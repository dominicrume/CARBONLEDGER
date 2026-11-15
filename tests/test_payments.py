"""Test-mode payments (docs/DECISIONS.md 2026-11-15, DEBT D29): Solana Pay on devnet. Nothing is recorded without a
paid quote that belongs to the caller and matches the grams; one payment pays for one retirement; money is integers.
The chain is a stub here; the real RPC path is the same calls (getSignaturesForAddress, getTransaction)."""
import pytest

from carbonledger.solpay import PaymentError, find_payment, lamports_for, sol_text, transfer_url
from carbonledger_api.payments import Payments
from test_api import body, make

TREASURY = "7DQZmWuTomLpBSHD44D3whxjPUja2Rt7Mm3LNGNewiyh"


class StubChain:
    """Plays devnet: pay(reference, lamports, to=...) puts a transaction on 'chain'."""
    def __init__(self):
        self.txs = {}

    def pay(self, ref, lamports, to=TREASURY, err=None):
        sig = f"sig{len(self.txs) + 1}"
        self.txs[sig] = {"ref": ref, "to": to, "lamports": lamports, "err": err}
        return sig

    def __call__(self, method, params):
        if method == "getSignaturesForAddress":
            return [{"signature": s, "err": t["err"]} for s, t in self.txs.items() if t["ref"] == params[0]]
        if method == "getTransaction":
            t = self.txs[params[0]]
            return {"meta": {"err": t["err"], "preBalances": [10**10, 0, 0], "postBalances": [10**10 - t["lamports"], t["lamports"], 0]},
                    "transaction": {"message": {"accountKeys": ["payer111", t["to"], t["ref"]]}}}
        raise AssertionError(method)


def app_with_payments():
    chain = StubChain()
    c = make(payments=Payments("solana-devnet-test", TREASURY, 100_000_000, chain))
    return c, chain


# ---- the money maths: integers and Decimal, never float ----
def test_price_is_whole_lamports_rounded_up_with_a_floor():
    assert lamports_for(1_000_000, 100_000_000) == 100_000_000          # one tonne at 0.1 SOL a tonne
    assert lamports_for(57_808, 100_000_000) == 5_780_800
    assert lamports_for(1, 100_000_000) == 1_000                        # floor: never a zero payment
    assert lamports_for(3, 333_333_333) == 1_000
    assert sol_text(5_780_800) == "0.0057808" and sol_text(10**9) == "1"
    with pytest.raises(PaymentError):
        lamports_for(0, 100_000_000)
    u = transfer_url(TREASURY, 5_780_800, "Ref111", "CarbonLedger (test)", "Retire 57808 g. Test mode")
    assert u.startswith(f"solana:{TREASURY}?amount=0.0057808&reference=Ref111&label=CarbonLedger%20%28test%29")


def test_find_payment_checks_recipient_amount_and_failure():
    ch = StubChain()
    assert find_payment(ch, "R1", TREASURY, 5000) is None               # nothing on chain yet
    ch.pay("R1", 4999)
    with pytest.raises(PaymentError, match="UNDERPAID"):
        find_payment(ch, "R1", TREASURY, 5000)
    ch2 = StubChain(); ch2.pay("R2", 9000, to="SomeoneElse111")
    with pytest.raises(PaymentError, match="WRONG_RECIPIENT"):
        find_payment(ch2, "R2", TREASURY, 5000)
    ch3 = StubChain(); ch3.pay("R3", 9000, err={"InstructionError": 1})
    with pytest.raises(PaymentError, match="PAYMENT_FAILED"):
        find_payment(ch3, "R3", TREASURY, 5000)
    ch4 = StubChain(); sig = ch4.pay("R4", 5000)
    assert find_payment(ch4, "R4", TREASURY, 5000) == sig


# ---- the API: off by default, test mode only when switched on ----
def test_payments_are_off_by_default_and_retire_is_unchanged():
    c = make()
    assert c.get("/health").json()["payments"] == "off"
    assert c.post("/v1/pay/quote", json={"grams": 100}).status_code == 404
    assert c.post("/v1/retire", json=body(idempotency_key="key-p000001")).status_code == 200


def test_only_test_modes_exist():
    with pytest.raises(RuntimeError, match="Real money is not supported"):
        Payments("solana-mainnet", TREASURY, 1, lambda m, p: None)


def test_no_retirement_without_a_paid_quote_that_matches():
    c, chain = app_with_payments()
    assert c.get("/health").json()["payments"] == "solana-devnet-test"
    r = c.post("/v1/retire", json=body(grams=1200, idempotency_key="key-p000011"))
    assert r.status_code == 402 and "PAYMENT_REQUIRED" in r.json()["detail"]
    q = c.post("/v1/pay/quote", json={"grams": 1200}).json()
    assert q["lamports"] == 120_000 and q["amount"] == "0.00012" and "No real money" in q["note"] and q["url"].startswith("solana:")
    pending = c.post("/v1/retire", json=body(grams=1200, idempotency_key="key-p000012", payment_reference=q["reference"]))
    assert pending.status_code == 402 and "PAYMENT_PENDING" in pending.json()["detail"]
    assert c.get(f"/v1/pay/{q['reference']}").json()["status"] == "pending"
    wrong = c.post("/v1/retire", json=body(grams=1300, idempotency_key="key-p000013", payment_reference=q["reference"]))
    assert wrong.status_code == 402 and "PAYMENT_MISMATCH" in wrong.json()["detail"]
    theirs = c.as_("personal", "p9").post("/v1/retire", json=body(grams=1200, idempotency_key="key-p000014", payment_reference=q["reference"]))
    assert theirs.status_code == 402 and "PAYMENT_NOT_FOUND" in theirs.json()["detail"]
    assert c.get("/v1/registry/summary").json()["retirements"] == 0          # nothing recorded by any refusal


def test_a_paid_quote_retires_once_and_the_receipt_carries_the_payment():
    c, chain = app_with_payments()
    q = c.post("/v1/pay/quote", json={"grams": 1200}).json()
    sig = chain.pay(q["reference"], q["lamports"])
    assert c.get(f"/v1/pay/{q['reference']}").json() == {"reference": q["reference"], "status": "paid", "signature": sig, "used": False,
                                                       "note": q["note"]}
    ok = c.post("/v1/retire", json=body(grams=1200, idempotency_key="key-p000021", payment_reference=q["reference"]))
    assert ok.status_code == 200
    rec = c.get(f"/v1/receipts/{ok.json()['receipt_id']}").json()["entry"]["receipt"]
    assert rec["payment_signature"] == sig and rec["payment_amount"] == 120_000 and rec["payment_unit"] == "lamports" and rec["payment_mode"] == "solana-devnet-test"
    again = c.post("/v1/retire", json=body(grams=1200, idempotency_key="key-p000022", payment_reference=q["reference"]))
    assert again.status_code == 409 and "PAYMENT_USED" in again.json()["detail"]
    same = c.post("/v1/retire", json=body(grams=1200, idempotency_key="key-p000021", payment_reference=q["reference"]))
    assert same.status_code == 200 and same.json()["receipt_id"] == ok.json()["receipt_id"]   # an idempotent replay is not a second payment
    assert c.get("/v1/registry/summary").json()["retirements"] == 1


def test_an_underpaid_quote_is_reported_and_records_nothing():
    c, chain = app_with_payments()
    q = c.post("/v1/pay/quote", json={"grams": 1200}).json()
    chain.pay(q["reference"], q["lamports"] - 1)
    assert c.get(f"/v1/pay/{q['reference']}").json()["status"] == "invalid"
    r = c.post("/v1/retire", json=body(grams=1200, idempotency_key="key-p000031", payment_reference=q["reference"]))
    assert r.status_code == 402 and "UNDERPAID" in r.json()["detail"]
    assert c.get("/v1/registry/summary").json()["retirements"] == 0


# ---- Stripe test mode: cards, Apple Pay, Google Pay, bank; test keys only ----
class StubStripe:
    def __init__(self):
        self.sessions = {}

    def __call__(self, method, path, data):
        if method == "POST":
            sid = f"cs_test_{len(self.sessions) + 1}"
            self.sessions[sid] = {"id": sid, "url": f"https://checkout.stripe.com/c/pay/{sid}", "payment_status": "unpaid",
                                  "amount": data["line_items[0][price_data][unit_amount]"], "payment_intent": None}
            return self.sessions[sid]
        return self.sessions[path.rsplit("/", 1)[1]]

    def pay(self, sid):
        self.sessions[sid].update(payment_status="paid", payment_intent="pi_test_" + sid[-1])


def test_stripe_test_mode_quotes_in_pence_and_retires_only_when_paid():
    from carbonledger_api.payments import pence_for
    assert pence_for(1_000_000, 10_000) == 10_000 and pence_for(57_808, 10_000) == 579 and pence_for(1, 10_000) == 30
    st = StubStripe()
    c = make(payments=Payments("stripe-test", stripe=st, pence_per_tonne=10_000, public_url="https://example.test"))
    q = c.post("/v1/pay/quote", json={"grams": 57_808}).json()
    assert q["amount"] == "5.79" and q["pence"] == 579 and q["url"].startswith("https://checkout.stripe.com/") and "No real money" in q["note"]
    r = c.post("/v1/retire", json=body(grams=57_808, idempotency_key="key-s000001", payment_reference=q["reference"]))
    assert r.status_code == 402 and "PAYMENT_PENDING" in r.json()["detail"]
    st.pay(q["reference"])
    ok = c.post("/v1/retire", json=body(grams=57_808, idempotency_key="key-s000002", payment_reference=q["reference"]))
    assert ok.status_code == 200
    rec = c.get(f"/v1/receipts/{ok.json()['receipt_id']}").json()["entry"]["receipt"]
    assert rec["payment_mode"] == "stripe-test" and rec["payment_amount"] == 579 and rec["payment_unit"] == "pence" and rec["payment_signature"] == "pi_test_1"


def test_a_live_stripe_key_is_refused(monkeypatch):
    from carbonledger_api.payments import payments_from_env
    monkeypatch.setenv("PAYMENTS_MODE", "stripe-test"); monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_live_abc")
    with pytest.raises(RuntimeError, match="Live keys are refused"):
        payments_from_env()
