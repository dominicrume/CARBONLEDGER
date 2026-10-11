import pytest
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.transaction import Transaction
from carbonledger.chain import ChainError, DryRunChain, MEMO_PROGRAM_ID, SolanaMemoChain, memo_text
from carbonledger.receipts import GENESIS, ReceiptChain, verify


def test_the_memo_transaction_builds_and_signs_offline():
    kp = Keypair()
    chain = SolanaMemoChain(["http://unused.invalid"], str(kp))
    text = memo_text("A-00000000-00000000", "ab" * 32)
    raw = chain.build_signed_tx("11111111111111111111111111111111", text)
    tx = Transaction.from_bytes(raw)
    msg = tx.message
    keys = [str(k) for k in msg.account_keys]
    assert str(kp.pubkey()) in keys and MEMO_PROGRAM_ID in keys
    assert msg.instructions[0].data == text.encode()
    assert len(tx.signatures) == 1 and str(tx.signatures[0]) != "1" * 64
    tx.verify()                                   # raises if the signature does not match the message


def test_the_memo_carries_only_an_anchor_id_and_a_root():
    t = memo_text("A-00000000-00000041", "cd" * 32)
    assert t == "carbonledger:v2:A-00000000-00000041:" + "cd" * 32 and "@" not in t


def test_an_oversized_memo_is_refused():
    chain = SolanaMemoChain(["http://unused.invalid"], str(Keypair()))
    with pytest.raises(ChainError):
        chain.build_signed_tx("11111111111111111111111111111111", "x" * 600)


def test_the_memo_program_id_is_a_valid_address():
    assert len(bytes(Pubkey.from_string(MEMO_PROGRAM_ID))) == 32


def test_dry_run_signatures_cannot_be_mistaken_for_real_ones():
    r = DryRunChain().record("CL-1", "00" * 32)
    assert r.signature.startswith("dryrun-") and r.explorer_url == ""


def _chain():
    c = ReceiptChain()
    for i in range(3):
        c.append({"receipt_id": f"CL-{i}", "grams": 100 + i}, what="retire", amount=str(100 + i), payee="p1", rule="test", outcome="ACCEPTED",
                 approved_by="test", ledger="test chain (simulated)", at="2027-01-01T00:00:00Z")
    return c


def test_receipt_chain_verifies_and_detects_edit_removal_and_reorder():
    c = _chain()
    assert verify(c.entries()) is None and c.entries()[0]["prev_hash"] == GENESIS
    e = c.entries(); e[1]["receipt"]["grams"] = 1
    assert verify(e) == 1
    e = c.entries(); del e[1]
    assert verify(e) == 1
    e = c.entries(); e[1], e[2] = e[2], e[1]
    assert verify(e) is not None


def test_a_cut_tail_is_only_visible_against_the_anchored_head():
    c = _chain()
    anchored = c.head_hash()
    cut = c.entries()[:-1]
    assert verify(cut) is None and cut[-1]["hash"] != anchored


def test_memo_program_id_matches_the_published_spl_memo_v2_address():
    """Checked against docs.rs, pkg.go.dev and the solana-program/memo repository on 2026-10-11."""
    assert MEMO_PROGRAM_ID == "MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr"


# ---- SolanaMemoChain against a fake RPC transport: confirmation, expiry, fallback, failure rate (D5, T21) ----
class FakeRpc:
    def __init__(self, confirm_after=1, down=(), fail_tx=False, expire=False):
        self.confirm_after, self.down, self.fail_tx, self.expire = confirm_after, set(down), fail_tx, expire
        self.calls, self.status_polls = [], 0

    def __call__(self, url, payload):
        self.calls.append((url, payload["method"]))
        if url in self.down:
            raise ChainError("connection refused")
        m = payload["method"]
        if m == "getHealth":
            return {"result": "ok"}
        if m == "getLatestBlockhash":
            return {"result": {"value": {"blockhash": "11111111111111111111111111111111", "lastValidBlockHeight": 100}}}
        if m == "sendTransaction":
            return {"result": "5" * 87}
        if m == "getBlockHeight":
            return {"result": 101 if self.expire else 50}
        if m == "getSignatureStatuses":
            self.status_polls += 1
            if self.fail_tx:
                return {"result": {"value": [{"err": {"InstructionError": [0, "Custom"]}, "slot": 7}]}}
            if self.status_polls >= self.confirm_after:
                return {"result": {"value": [{"confirmationStatus": "confirmed", "slot": 1234, "err": None}]}}
            return {"result": {"value": [None]}}
        raise AssertionError(m)


def _chain_with(rpc, urls=("http://primary.invalid",)):
    return SolanaMemoChain(list(urls), str(Keypair()), transport=rpc, sleep=lambda s: None, confirm_timeout=5)


def test_record_then_confirm_returns_slot_and_confirmed():
    rpc = FakeRpc(confirm_after=3)
    ch = _chain_with(rpc)
    rec = ch.record("CL-1", "ab" * 32)
    assert not rec.confirmed and rec.explorer_url.endswith("cluster=devnet")
    done = ch.confirm(rec)
    assert done.confirmed and done.slot == 1234 and rpc.status_polls == 3


def test_an_expired_blockhash_raises_instead_of_claiming_success():
    ch = _chain_with(FakeRpc(confirm_after=99, expire=True))
    with pytest.raises(ChainError, match="expired"):
        ch.confirm(ch.record("CL-1", "ab" * 32))


def test_a_transaction_that_failed_on_chain_is_an_error():
    ch = _chain_with(FakeRpc(fail_tx=True))
    with pytest.raises(ChainError, match="failed on chain"):
        ch.confirm(ch.record("CL-1", "ab" * 32))


def test_fallback_endpoint_is_used_when_the_primary_is_down():
    rpc = FakeRpc(down={"http://primary.invalid"})
    ch = _chain_with(rpc, urls=("http://primary.invalid", "http://fallback.invalid"))
    assert ch.health()
    assert ("http://fallback.invalid", "getHealth") in rpc.calls
    assert 0 < ch.stats.failure_rate() < 1


def test_every_endpoint_down_is_a_plain_error_after_retries():
    rpc = FakeRpc(down={"http://a.invalid", "http://b.invalid"})
    ch = _chain_with(rpc, urls=("http://a.invalid", "http://b.invalid"))
    assert ch.health() is False
    with pytest.raises(ChainError, match="every endpoint"):
        ch.record("CL-1", "ab" * 32)
    assert ch.stats.failure_rate() == 1.0
    assert len([c for c in rpc.calls if c[1] == "getLatestBlockhash"]) == 6      # 2 urls x (1 + 2 retries)
