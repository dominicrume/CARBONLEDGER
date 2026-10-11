"""Anchor outbox. A receipt commits first, with anchor_status pending. A worker submits and confirms it on the chain,
then marks it anchored with the signature and slot. A dropped transaction is resubmitted. After MAX_ATTEMPTS it is
marked failed and shown as failed: never silently claimed (D5, rule 6 as refined on 2026-10-11)."""
import threading
import time
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

from .chain import ChainClient, ChainError, ChainRecord

PENDING, ANCHORED, FAILED = "pending", "anchored", "failed"
MAX_ATTEMPTS = 5


@dataclass
class AnchorEntry:
    receipt_id: str
    receipt_hash: str
    status: str = PENDING
    signature: Optional[str] = None
    explorer_url: Optional[str] = None
    cluster: Optional[str] = None
    slot: Optional[int] = None
    attempts: int = 0
    last_error: str = ""
    anchored_at: Optional[float] = None

    def public(self) -> dict:
        return {"anchor_status": self.status, "signature": self.signature, "explorer_url": self.explorer_url or None,
                "cluster": self.cluster, "slot": self.slot, "attempts": self.attempts, "error": self.last_error or None}


@dataclass
class AnchorOutbox:
    entries: Dict[str, AnchorEntry] = field(default_factory=dict)
    order: List[str] = field(default_factory=list)
    lock: threading.Lock = field(default_factory=threading.Lock)
    changed: threading.Condition = field(default_factory=threading.Condition)
    kick: threading.Event = field(default_factory=threading.Event)      # wakes the worker on enqueue
    on_change: Optional[Callable[["AnchorEntry"], None]] = None          # persistence hook, called after each change

    def enqueue(self, receipt_id: str, receipt_hash: str) -> AnchorEntry:
        with self.lock:
            e = AnchorEntry(receipt_id, receipt_hash)
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
        """Load entries from storage rows (receipt_id, receipt_hash, status, signature, explorer_url, cluster, slot, attempts, last_error, anchored_at)."""
        with self.lock:
            for r in rows:
                e = AnchorEntry(r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[8] or "", r[9])
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
    """Processes the outbox. `run_once` is synchronous for tests. `start` runs it on a daemon thread."""
    def __init__(self, chain: ChainClient, outbox: AnchorOutbox, interval: float = 1.0, now: Callable[[], float] = time.time,
                 on_failed: Optional[Callable[[AnchorEntry], None]] = None):
        self.chain, self.outbox, self.interval, self.now, self.on_failed = chain, outbox, interval, now, on_failed
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def process(self, e: AnchorEntry) -> None:
        self.outbox._set(e, attempts=e.attempts + 1)
        try:
            rec: ChainRecord = self.chain.record(e.receipt_id, e.receipt_hash)
            self.outbox._set(e, signature=rec.signature, explorer_url=rec.explorer_url, cluster=rec.cluster)
            rec = self.chain.confirm(rec)
            if not rec.confirmed:
                raise ChainError("not confirmed")
            self.outbox._set(e, status=ANCHORED, slot=rec.slot, anchored_at=self.now(), last_error="")
        except ChainError as exc:
            if e.attempts >= MAX_ATTEMPTS:
                self.outbox._set(e, status=FAILED, last_error=str(exc))
                if self.on_failed:
                    self.on_failed(e)
            else:
                self.outbox._set(e, last_error=str(exc))

    def run_once(self) -> int:
        todo = self.outbox.pending()
        for e in todo:
            self.process(e)
        return len(todo)

    def start(self) -> None:
        def loop():
            while not self._stop.is_set():
                try:
                    self.outbox.kick.clear()
                    if self.run_once() == 0:
                        self.outbox.kick.wait(self.interval)
                except Exception:  # noqa: BLE001  the worker must never die quietly
                    self._stop.wait(self.interval)
        self._thread = threading.Thread(target=loop, name="anchor-worker", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=5)
