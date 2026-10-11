import pytest
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.transaction import Transaction
from carbonledger.chain import ChainError, DryRunChain, MEMO_PROGRAM_ID, SolanaMemoChain, memo_text
from carbonledger.receipts import GENESIS, ReceiptChain, verify


def test_the_memo_transaction_builds_and_signs_offline():
    kp = Keypair()
    chain = SolanaMemoChain("http://unused.invalid", str(kp))
    text = memo_text("CL-00000001", "ab" * 32)
    raw = chain.build_signed_tx("11111111111111111111111111111111", text)
    tx = Transaction.from_bytes(raw)
    msg = tx.message
    keys = [str(k) for k in msg.account_keys]
    assert str(kp.pubkey()) in keys and MEMO_PROGRAM_ID in keys
    assert msg.instructions[0].data == text.encode()
    assert len(tx.signatures) == 1 and str(tx.signatures[0]) != "1" * 64
    tx.verify()                                   # raises if the signature does not match the message


def test_the_memo_carries_only_ids_and_a_hash():
    t = memo_text("CL-00000001", "cd" * 32)
    assert t == "carbonledger:v1:CL-00000001:" + "cd" * 32 and "@" not in t


def test_an_oversized_memo_is_refused():
    chain = SolanaMemoChain("http://unused.invalid", str(Keypair()))
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
        c.append({"receipt_id": f"CL-{i}", "grams": 100 + i})
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
