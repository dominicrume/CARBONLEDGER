"""The receipt chain, in the KYA receipt format (knowyouragenticai-receipts 1.1.0, SPEC.md v1.3).

Every attempt that reaches the decision layer is a receipt, ACCEPTED or REFUSED, sealed to the one before it:
seal = sha256(canonical(body) + prev). The seal is the hash this system anchors (one Merkle root per interval)
and stores. The wire format is the package's, with CarbonLedger's own fields added (the spec allows added fields
when both ends are controlled; the package's verify() and the verifier page check the seals regardless).

What the format does not do, in the package's own words: it is not signed and it does not prove a rule was
enforced. Origin comes from the anchored root on Solana; enforcement comes from registry.py and the database.
The `ledger` field names the decider and says when the chain is simulated, as the spec requires."""
import copy
import hashlib
import json
from typing import List, Optional

from knowyouragenticai_receipts import GENESIS, assert_ascii, canonical, seal
from knowyouragenticai_receipts import verify as kya_verify

RECEIPT_FIELDS = ("n", "what", "amount", "payee", "currency", "instrument", "rule", "outcome", "approved_by", "ledger", "at", "prev", "seal")
CURRENCY = "gCO2e"            # grams of CO2 equivalent, as a string, never a JSON number (spec section 4)


def digest(body: dict) -> str:
    """sha256 of the canonical JSON. Used for ids, idempotency and note digests, the same bytes the seal uses."""
    return hashlib.sha256(canonical(body).encode("utf-8")).hexdigest()


class ReceiptChain:
    """An append-only list of KYA receipts. Entries are returned in the shape the API and the app already use:
    {"index", "receipt", "prev_hash", "hash"} where receipt is the full wire-format receipt (with its seal),
    prev_hash is its `prev` and hash is its `seal`."""

    def __init__(self) -> None:
        self._receipts: List[dict] = []

    def next_index(self) -> int:
        return len(self._receipts)

    def head_hash(self) -> str:
        return self._receipts[-1]["seal"] if self._receipts else GENESIS

    def append(self, fields: dict, *, what: str, amount: str, payee: str, rule: str, outcome: str, approved_by: str,
               ledger: str, at: str, instrument: str = "", currency: str = CURRENCY) -> dict:
        """Seal one attempt. `fields` are CarbonLedger's own additions (receipt_id, grams, serial range, digests).
        Raises NonAsciiInReceipt before sealing if any field is not ASCII (spec section 5), ValueError if `fields`
        would overwrite a spec field."""
        return self.commit(self.prepare(fields, what=what, amount=amount, payee=payee, rule=rule, outcome=outcome, approved_by=approved_by,
                                        ledger=ledger, at=at, instrument=instrument, currency=currency))

    def prepare(self, fields: dict, *, what: str, amount: str, payee: str, rule: str, outcome: str, approved_by: str,
                ledger: str, at: str, instrument: str = "", currency: str = CURRENCY) -> dict:
        """Seal the next receipt WITHOUT appending it, so a store can write it first and refuse it (its constraints
        are the second guard). `commit` then appends exactly that entry."""
        clash = sorted(set(fields) & set(RECEIPT_FIELDS))
        if clash:
            raise ValueError(f"fields would overwrite spec fields: {clash}")
        if not isinstance(amount, str):
            raise TypeError("amount must be a string")
        r = {"n": len(self._receipts) + 1, "what": what, "amount": amount, "payee": payee, "currency": currency, "instrument": instrument,
             "rule": rule, "outcome": outcome, "approved_by": approved_by, "ledger": ledger, "at": at, "prev": self.head_hash(), **fields}
        assert_ascii(r)                                   # before sealing, never after
        r["seal"] = seal(r, r["prev"])
        return self._entry(r)

    def commit(self, entry: dict) -> dict:
        """Append a prepared entry. Refuses one that no longer follows the head (something else was appended)."""
        r = entry["receipt"]
        if r["prev"] != self.head_hash() or r["n"] != len(self._receipts) + 1:
            raise ValueError("prepared receipt no longer follows the head of the chain")
        self._receipts.append(copy.deepcopy(r))
        return self._entry(r)

    @staticmethod
    def _entry(r: dict) -> dict:
        return {"index": r["n"] - 1, "receipt": copy.deepcopy(r), "prev_hash": r["prev"], "hash": r["seal"]}

    def entries(self) -> List[dict]:
        return [self._entry(r) for r in self._receipts]

    def receipts(self) -> List[dict]:
        """The bare chain in the package's wire format: what `python -m knowyouragenticai_receipts verify` reads."""
        return copy.deepcopy(self._receipts)

    def find(self, receipt_id: str) -> Optional[dict]:
        for r in self._receipts:
            if r.get("receipt_id") == receipt_id:
                return self._entry(r)
        return None

    @classmethod
    def from_entries(cls, entries: List[dict]) -> "ReceiptChain":
        """Rebuild from stored rows. Raises ValueError naming the first bad index if the stored chain is broken."""
        bad = verify(entries)
        if bad is not None:
            raise ValueError(f"stored receipt chain is broken at index {bad}")
        c = cls()
        c._receipts = [copy.deepcopy(e["receipt"]) for e in entries]
        return c


def verify(entries: List[dict]) -> Optional[int]:
    """None if intact, else the 0-based index of the first bad entry. Checks the seals exactly as the package does
    (same bytes, same rule) and the wrapper's index, prev_hash and hash columns against them."""
    prev = GENESIS
    for i, e in enumerate(entries):
        r = e.get("receipt") if isinstance(e, dict) else None
        if not isinstance(r, dict) or "seal" not in r:
            return i
        body = {k: v for k, v in r.items() if k != "seal"}
        try:
            expected = seal(body, prev)
        except (TypeError, ValueError):
            return i
        if r.get("n") != i + 1 or r.get("prev") != prev or r["seal"] != expected or e.get("index") != i or e.get("prev_hash") != prev or e.get("hash") != r["seal"]:
            return i
        prev = r["seal"]
    return None


def verify_wire(receipts: List[dict]) -> tuple:
    """The package's own verdict on a bare chain: (True, 0) or (False, 1-based position)."""
    return kya_verify(receipts)


def to_json(receipts: List[dict]) -> str:
    return json.dumps(receipts, indent=2) + "\n"
