"""The anchor worker: one transaction per batch, a proof for every receipt, honest failure (D5, D15)."""
from carbonledger.chain import ChainError, DryRunChain
from carbonledger.merkle import verify_proof
from carbonledger.outbox import AnchorOutbox, AnchorWorker, MAX_ATTEMPTS


class Counting(DryRunChain):
    def __init__(self):
        self.records = []
    def record(self, anchor_id, root):
        self.records.append((anchor_id, root))
        return super().record(anchor_id, root)


def _fill(ob, n, start=0):
    for i in range(n):
        ob.enqueue(f"CL-{i}", f"{i:064x}", start + i)


def test_many_receipts_share_one_transaction_and_each_keeps_a_proof():
    ob, ch = AnchorOutbox(), Counting()
    _fill(ob, 7, start=12)
    assert AnchorWorker(ch, ob).run_once() == 7
    assert len(ch.records) == 1 and ch.records[0][0] == "A-00000012-00000018"
    root = ch.records[0][1]
    for e in ob.entries.values():
        assert e.status == "anchored" and e.anchor_root == root and e.signature == ob.entries["CL-0"].signature
        assert verify_proof(e.receipt_hash, [tuple(p) for p in e.proof], root)
    assert ob.counts() == {"pending": 0, "anchored": 7, "failed": 0}


def test_a_batch_that_never_confirms_fails_loudly_after_retries():
    class Dropping(Counting):
        def confirm(self, rec):
            raise ChainError("blockhash expired")
    ob, ch = AnchorOutbox(), Dropping()
    _fill(ob, 3)
    w = AnchorWorker(ch, ob)
    for _ in range(MAX_ATTEMPTS):
        w.run_once()
    assert ob.counts() == {"pending": 0, "anchored": 0, "failed": 3} and len(ch.records) == MAX_ATTEMPTS
    e = ob.entries["CL-1"]
    assert e.signature is None and e.proof is None and "expired" in e.last_error
    assert w.run_once() == 0


def test_later_receipts_form_the_next_batch_and_batches_never_overlap():
    ob, ch = AnchorOutbox(), Counting()
    _fill(ob, 2)
    w = AnchorWorker(ch, ob)
    w.run_once()
    ob.enqueue("CL-9", "9" * 64, 2)
    w.run_once()
    assert [r[0] for r in ch.records] == ["A-00000000-00000001", "A-00000002-00000002"]
    assert ob.entries["CL-9"].anchor_root != ob.entries["CL-0"].anchor_root


def test_max_batch_splits_a_large_backlog():
    ob, ch = AnchorOutbox(), Counting()
    _fill(ob, 10)
    w = AnchorWorker(ch, ob, max_batch=4)
    assert [w.run_once() for _ in range(4)] == [4, 4, 2, 0]
    assert len(ch.records) == 3
