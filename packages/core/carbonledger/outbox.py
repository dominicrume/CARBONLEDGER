"""Anchor outbox (D5, D15, T22). A receipt commits first, with anchor_status pending. The worker gathers the pending
receipts, builds one Merkle root over their hashes, submits ONE transaction, confirms it, then marks every receipt
in that batch anchored with the signature, the root and its own proof path. A dropped transaction is resubmitted.
After MAX_ATTEMPTS a receipt is marked failed and shown as failed: never silently claimed."""
import threading
import time
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

from .chain import ChainClient, ChainError, ChainRecord
from .merkle import proof as merkle_proof, root as merkle_root

PENDING, ANCHORED, FAILED = "pending", "anchored", "failed"
MAX_ATTEMPTS = 5
MAX_BATCH = 1024


@dataclass
class AnchorEntry:
    receipt_id: str
    receipt_hash: str
    index: int = 0                              # position in the receipt chain
    status: str = PENDING
    signature: Optional[str] = None
    explorer_url: Optional[str] = None
    cluster: Optional[str] = None
    slot: Optional[int] = None
    attempts: int = 0
    last_error: str = ""
    anchored_at: Optional[float] = None
    anchor_id: Optional[str] = None             # the batch, e.g. A-00000012-00000057 (first and last chain index)
    anchor_root: Optional[str] = None
    proof: Optional[list] = None                # [[side, hex], ...] from this leaf up to the root

    def public(self) -> dict:
        return {"anchor_status": self.status, "signature": self.signature, "explorer_url": self.explorer_url or None,
                "cluster": self.cluster, "slot": self.slot, "attempts": self.attempts, "error": self.last_error or None,
                "anchor_id": self.anchor_id, "anchor_root": self.anchor_root}


def anchor_id_for(first_index: int, last_index: int) -> str:
    return f"A-{first_index:08d}-{last_index:08d}"


@dataclass
class AnchorOutbox:
    entries: Dict[str, AnchorEntry] = field(default_factory=dict)
    order: List[str] = field(default_factory=list)
    lock: threading.Lock = field(default_factory=threading.Lock)
    changed: threading.Condition = field(default_factory=threading.Condition)
    kick: threading.Event = field(default_factory=threading.Event)      # wakes the worker on enqueue
    on_change: Optional[Callable[["AnchorEntry"], None]] = None          # persistence hook, called after each change

    def enqueue(self, receipt_id: str, receipt_hash: str, index: int = 0) -> AnchorEntry:
        with self.lock:
            e = AnchorEntry(receipt_id, receipt_hash, index)
            self.entries[receipt_id] = e
            self.order.append(receipt_id)
        self.kick.set()
        return e

    def get(self, receipt_id: str) -> Optional[AnchorEntry]:
        with self.lock:
            return self.entries.get(receipt_id)

    def pending(self) -> List[AnchorEntry]:
        with self.lock:
            return [self.entries[r] for r in self.order if self.entries[r].status == PENDING]

    def counts(self) -> dict:
        with self.lock:
            out = {PENDING: 0, ANCHORED: 0, FAILED: 0}
            for e in self.entries.values():
                out[e.status] += 1
            return out

    def _set(self, e: AnchorEntry, **kw) -> None:
        with self.lock:
            for k, v in kw.items():
                setattr(e, k, v)
        if self.on_change:
            self.on_change(e)
        with self.changed:
            self.changed.notify_all()

    def restore(self, rows) -> None:
        """Load entries from storage rows: (receipt_id, receipt_hash, status, signature, explorer_url, cluster, slot,
        attempts, last_error, anchored_at, index, anchor_id, anchor_root, proof)."""
        with self.lock:
            for r in rows:
                e = AnchorEntry(r[0], r[1], r[10] or 0, r[2], r[3], r[4], r[5], r[6], r[7], r[8] or "", r[9], r[11], r[12], r[13])
                self.entries[e.receipt_id] = e
                self.order.append(e.receipt_id)

    def wait_settled(self, receipt_id: str, timeout: float) -> AnchorEntry:
        """Block up to `timeout` seconds for the entry to leave pending. Returns the entry either way."""
        deadline = time.monotonic() + timeout
        with self.changed:
            while True:
                e = self.entries.get(receipt_id)
                if e is None or e.status != PENDING:
                    return e
                left = deadline - time.monotonic()
                if left <= 0:
                    return e
                self.changed.wait(left)


class AnchorWorker:
    """Processes the outbox in batches. `run_once` is synchronous for tests. `start` runs it on a daemon thread.
    batch_window_s: after a receipt arrives, wait this long so more receipts can share one root."""
    def __init__(self, chain: ChainClient, outbox: AnchorOutbox, interval: float = 1.0, now: Callable[[], float] = time.time,
                 on_failed: Optional[Callable[[AnchorEntry], None]] = None, batch_window_s: float = 0.0, max_batch: int = MAX_BATCH):
        self.chain, self.outbox, self.interval, self.now, self.on_failed = chain, outbox, interval, now, on_failed
        self.batch_window_s, self.max_batch = batch_window_s, max_batch
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def process(self, batch: List[AnchorEntry]) -> None:
        batch = sorted(batch, key=lambda e: e.index)
        hashes = [e.receipt_hash for e in batch]
        root = merkle_root(hashes)
        aid = anchor_id_for(batch[0].index, batch[-1].index)
        for e in batch:
            self.outbox._set(e, attempts=e.attempts + 1)
        try:
            rec: ChainRecord = self.chain.record(aid, root)
            for e in batch:
                self.outbox._set(e, signature=rec.signature, explorer_url=rec.explorer_url, cluster=rec.cluster)
            rec = self.chain.confirm(rec)
            if not rec.confirmed:
                raise ChainError("not confirmed")
            when = self.now()
            for i, e in enumerate(batch):
                self.outbox._set(e, status=ANCHORED, slot=rec.slot, anchored_at=when, last_error="", anchor_id=aid, anchor_root=root,
                                 proof=[list(p) for p in merkle_proof(hashes, i)])
        except ChainError as exc:
            for e in batch:
                if e.attempts >= MAX_ATTEMPTS:
                    self.outbox._set(e, status=FAILED, last_error=str(exc), signature=None, explorer_url=None)
                    if self.on_failed:
                        self.on_failed(e)
                else:
                    self.outbox._set(e, last_error=str(exc), signature=None, explorer_url=None)

    def run_once(self) -> int:
        todo = self.outbox.pending()[: self.max_batch]
        if todo:
            self.process(todo)
        return len(todo)

    def start(self) -> None:
        def loop():
            while not self._stop.is_set():
                try:
                    self.outbox.kick.clear()
                    if self.outbox.pending():
                        if self.batch_window_s:
                            self._stop.wait(self.batch_window_s)
                        self.run_once()
                    else:
                        self.outbox.kick.wait(self.interval)
                except Exception:  # noqa: BLE001  the worker must never die quietly
                    self._stop.wait(self.interval)
        self._thread = threading.Thread(target=loop, name="anchor-worker", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=5)
