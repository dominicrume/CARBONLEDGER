"""Hash-chained receipt log. Each receipt commits to the one before it. The head hash is what goes on Solana.
Only the hash is anchored, never the payload (no personal data on a public chain).
A chain alone cannot show that the newest receipts were cut off, so the anchored head is the second witness."""
import copy
import hashlib
import json
from typing import List, Optional

GENESIS = "0" * 64


def _canonical(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def digest(body: dict) -> str:
    return hashlib.sha256(_canonical(body).encode("utf-8")).hexdigest()


class ReceiptChain:
    def __init__(self) -> None:
        self._entries: List[dict] = []

    def next_index(self) -> int:
        return len(self._entries)

    def head_hash(self) -> str:
        return self._entries[-1]["hash"] if self._entries else GENESIS

    def append(self, receipt: dict) -> dict:
        body = {"index": len(self._entries), "receipt": receipt, "prev_hash": self.head_hash()}
        entry = {**body, "hash": digest(body)}
        self._entries.append(copy.deepcopy(entry))
        return copy.deepcopy(entry)

    def entries(self) -> List[dict]:
        return copy.deepcopy(self._entries)

    @classmethod
    def from_entries(cls, entries: List[dict]) -> "ReceiptChain":
        """Rebuild from stored rows. Raises ValueError naming the first bad index if the stored chain is broken."""
        bad = verify(entries)
        if bad is not None:
            raise ValueError(f"stored receipt chain is broken at index {bad}")
        c = cls()
        c._entries = copy.deepcopy(entries)
        return c

    def find(self, receipt_id: str) -> Optional[dict]:
        for e in self._entries:
            if e["receipt"].get("receipt_id") == receipt_id:
                return copy.deepcopy(e)
        return None


def verify(entries: List[dict]) -> Optional[int]:
    """None if intact, else the index of the first bad entry."""
    prev = GENESIS
    for i, e in enumerate(entries):
        body = {"index": e.get("index"), "receipt": e.get("receipt"), "prev_hash": e.get("prev_hash")}
        if e.get("index") != i or e.get("prev_hash") != prev or digest(body) != e.get("hash"):
            return i
        prev = e["hash"]
    return None
