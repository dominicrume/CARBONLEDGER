"""The receipt chain IS the KYA receipt format: the package verifies what we seal, its CLI accepts our export,
refusals are first-class, and the spec's rules (ASCII, string amounts, seal = sha256(canonical + prev)) hold."""
import hashlib
import json
import subprocess
import sys

import pytest
from knowyouragenticai_receipts import GENESIS, Chain, NonAsciiInReceipt, canonical, verify as kya_verify
from carbonledger.receipts import CURRENCY, ReceiptChain, to_json, verify, verify_wire

AT = "2027-01-02T03:04:05Z"
LEDGER = "CarbonLedger API, chain dry-run (simulated pilot units)"


def _stamp(c, i, outcome="ACCEPTED", grams=100):
    return c.append({"receipt_id": f"CL-{i:012X}", "grams": grams, "serial_start": 0, "serial_end": grams}, what=f"retire {grams} g for a basket",
                    amount=str(grams), payee="demo-pilot-1", rule="within the cap" if outcome == "ACCEPTED" else "OVER_CAP: the request would pass the cap",
                    outcome=outcome, approved_by="api key owner p1", ledger=LEDGER, at=AT, instrument=f"serial range 0-{grams}")


def test_seal_is_exactly_the_specs_rule_and_the_package_verifies_it():
    c = ReceiptChain()
    e = _stamp(c, 1)
    r = e["receipt"]
    body = {k: v for k, v in r.items() if k != "seal"}
    assert r["seal"] == hashlib.sha256((canonical(body) + GENESIS).encode()).hexdigest()
    assert r["prev"] == GENESIS and r["n"] == 1 and r["amount"] == "100" and r["currency"] == CURRENCY
    _stamp(c, 2, "REFUSED", 5000)
    assert verify_wire(c.receipts()) == (True, 0) and verify(c.entries()) is None
    assert c.head_hash() == c.receipts()[-1]["seal"]


def test_a_refusal_is_a_receipt_with_equal_weight():
    c = ReceiptChain()
    _stamp(c, 1); r = _stamp(c, 2, "REFUSED", 9000)["receipt"]
    assert r["outcome"] == "REFUSED" and r["rule"].startswith("OVER_CAP") and r["n"] == 2
    assert [x["outcome"] for x in c.receipts()] == ["ACCEPTED", "REFUSED"]


def test_tampering_breaks_every_seal_after_it_in_both_verifiers():
    c = ReceiptChain()
    for i in range(1, 5):
        _stamp(c, i)
    wire = c.receipts(); wire[1]["amount"] = "9999"
    assert kya_verify(wire) == (False, 2)                       # the package: 1-based position
    ents = c.entries(); ents[1]["receipt"]["amount"] = "9999"
    assert verify(ents) == 1                                     # ours: 0-based index, same entry
    ents = c.entries(); del ents[1]
    assert verify(ents) == 1
    ents = c.entries(); ents[1], ents[2] = ents[2], ents[1]
    assert verify(ents) is not None
    cut = c.entries()[:-1]
    assert verify(cut) is None and cut[-1]["hash"] != c.head_hash()   # deletion of the tail needs the anchored head


def test_non_ascii_and_numeric_amounts_are_refused_before_sealing():
    c = ReceiptChain()
    with pytest.raises(NonAsciiInReceipt):
        c.append({"receipt_id": "CL-1", "note": "Pay ₦500"}, what="x", amount="1", payee="p", rule="r", outcome="ACCEPTED", approved_by="a", ledger="l", at=AT)
    with pytest.raises(TypeError):
        c.append({"receipt_id": "CL-1"}, what="x", amount=1, payee="p", rule="r", outcome="ACCEPTED", approved_by="a", ledger="l", at=AT)
    with pytest.raises(ValueError, match="spec fields"):
        c.append({"outcome": "ACCEPTED"}, what="x", amount="1", payee="p", rule="r", outcome="ACCEPTED", approved_by="a", ledger="l", at=AT)
    assert len(c.receipts()) == 0                                 # nothing half-sealed


def test_the_packages_own_chain_and_ours_agree_on_the_bytes():
    """Stamp the same body through the package's Chain and through ours: identical seals."""
    theirs = Chain(approved_by="api key owner p1", ledger=LEDGER)
    t = theirs.stamp(what="retire 100 g for a basket", amount="100", currency=CURRENCY, payee="demo-pilot-1", rule="within the cap",
                     outcome="ACCEPTED", instrument="serial range 0-100", at=AT)
    ours = ReceiptChain().append({}, what="retire 100 g for a basket", amount="100", payee="demo-pilot-1", rule="within the cap",
                                 outcome="ACCEPTED", approved_by="api key owner p1", ledger=LEDGER, at=AT, instrument="serial range 0-100")["receipt"]
    assert ours == t


def test_the_package_cli_verifies_our_export_and_catches_an_edit(tmp_path):
    c = ReceiptChain()
    for i in range(1, 4):
        _stamp(c, i, "REFUSED" if i == 2 else "ACCEPTED")
    f = tmp_path / "receipts.json"; f.write_text(to_json(c.receipts()))
    ok = subprocess.run([sys.executable, "-m", "knowyouragenticai_receipts", "verify", str(f)], capture_output=True, text=True)
    assert ok.returncode == 0, ok.stdout + ok.stderr
    wire = c.receipts(); wire[0]["rule"] = "edited later"; f.write_text(to_json(wire))
    bad = subprocess.run([sys.executable, "-m", "knowyouragenticai_receipts", "verify", str(f)], capture_output=True, text=True)
    assert bad.returncode == 1, bad.stdout + bad.stderr
    f.write_text(json.dumps({"not": "a chain"}))
    other = subprocess.run([sys.executable, "-m", "knowyouragenticai_receipts", "verify", str(f)], capture_output=True, text=True)
    assert other.returncode == 2                                  # a different file is not an accusation


def test_rebuild_from_rows_refuses_a_broken_chain():
    c = ReceiptChain(); _stamp(c, 1); _stamp(c, 2)
    rows = c.entries()
    assert ReceiptChain.from_entries(rows).head_hash() == c.head_hash()
    rows[0]["receipt"]["grams"] = 1
    with pytest.raises(ValueError, match="broken at index 0"):
        ReceiptChain.from_entries(rows)
