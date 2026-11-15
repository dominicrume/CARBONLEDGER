"""Payments, TEST MODE ONLY (docs/DECISIONS.md 2026-11-15, DEBT D29). Off unless PAYMENTS_MODE is solana-devnet-test
or stripe-test (cards, Apple Pay, Google Pay, bank, through Stripe Checkout with a TEST key; a live key is refused).
A person asks for a quote, their wallet pays devnet test tokens to the treasury with the quote's reference key, and
/v1/retire is accepted only with a paid, unused reference that belongs to the caller and matches the grams.
Quotes live in memory: a restart forgets unpaid quotes, which is acceptable while no real money moves."""
import os
import secrets
import threading
from typing import Callable, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from carbonledger.solpay import TEST_NOTE, PaymentError, find_payment, lamports_for, sol_text, transfer_url

MODES = ("solana-devnet-test", "stripe-test")
STRIPE_NOTE = "Test mode: Stripe test card payment. No real money moves."


def pence_for(grams: int, pence_per_tonne: int) -> int:
    """Card price in whole pence, rounded up, at least Stripe's 30p minimum. Integers only."""
    if not isinstance(grams, int) or isinstance(grams, bool) or grams <= 0:
        raise PaymentError("BAD_AMOUNT")
    return max(30, -(-grams * pence_per_tonne // 1_000_000))
QUOTE_TTL_S = 900


class QuoteIn(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    grams: int = Field(gt=0, le=10**12)


class Payments:
    def __init__(self, mode: str = "", recipient: str = "", lamports_per_tonne: int = 100_000_000,
                 rpc: Optional[Callable[[str, list], object]] = None, now: Callable[[], float] = None,
                 stripe: Optional[Callable[[str, str, dict], dict]] = None, pence_per_tonne: int = 10_000, public_url: str = ""):
        if mode and mode not in MODES:
            raise RuntimeError(f"PAYMENTS_MODE must be one of {MODES} or unset (got {mode}). Real money is not supported.")
        if mode == "solana-devnet-test" and (not recipient or rpc is None):
            raise RuntimeError("PAYMENTS_MODE is set but there is no treasury address or chain RPC.")
        if mode == "stripe-test" and stripe is None:
            raise RuntimeError("PAYMENTS_MODE=stripe-test needs a Stripe TEST key (sk_test_...).")
        self.mode, self.recipient, self.lamports_per_tonne, self.rpc = mode, recipient, lamports_per_tonne, rpc
        self.stripe, self.pence_per_tonne, self.public_url = stripe, pence_per_tonne, public_url.rstrip("/")
        self.now = now or __import__("time").time
        self.quotes: Dict[str, dict] = {}
        self.lock = threading.Lock()

    @property
    def on(self) -> bool:
        return bool(self.mode)

    def new_reference(self) -> str:
        from solders.keypair import Keypair     # a fresh public key nobody holds: only a payment will ever mention it
        return str(Keypair().pubkey())

    def quote(self, owner: str, grams: int) -> dict:
        if self.mode == "stripe-test":
            return self._stripe_quote(owner, grams)
        lam = lamports_for(grams, self.lamports_per_tonne)
        ref = self.new_reference()
        exp = int(self.now()) + QUOTE_TTL_S
        with self.lock:
            self.quotes[ref] = {"owner": owner, "grams": grams, "amount": lam, "unit": "lamports", "expires": exp, "used": False, "signature": None}
        return {"reference": ref, "recipient": self.recipient, "lamports": lam, "amount": sol_text(lam), "currency": "SOL (devnet test)",
                "grams": grams, "expires_at": exp, "mode": self.mode, "note": TEST_NOTE,
                "url": transfer_url(self.recipient, lam, ref, "CarbonLedger (test)", f"Retire {grams} g of pilot units. Test mode, no real money.")}

    def _stripe_quote(self, owner: str, grams: int) -> dict:
        pence = pence_for(grams, self.pence_per_tonne)
        back = f"{self.public_url}/app#shop"
        sess = self.stripe("POST", "/v1/checkout/sessions", {
            "mode": "payment", "success_url": back, "cancel_url": back,
            "line_items[0][quantity]": 1, "line_items[0][price_data][currency]": "gbp",
            "line_items[0][price_data][unit_amount]": pence,
            "line_items[0][price_data][product_data][name]": f"Retire {grams} g of pilot units (test mode, not yet verified credits)",
            "metadata[grams]": grams})
        ref = sess["id"]; exp = int(self.now()) + QUOTE_TTL_S
        with self.lock:
            self.quotes[ref] = {"owner": owner, "grams": grams, "amount": pence, "unit": "pence", "expires": exp, "used": False, "signature": None}
        return {"reference": ref, "url": sess["url"], "amount": f"{pence // 100}.{pence % 100:02d}", "currency": "GBP (Stripe test)",
                "pence": pence, "grams": grams, "expires_at": exp, "mode": self.mode, "note": STRIPE_NOTE}

    def _found(self, ref: str, q: dict) -> Optional[str]:
        if self.mode == "stripe-test":
            sess = self.stripe("GET", f"/v1/checkout/sessions/{ref}", {})
            return (sess.get("payment_intent") or sess["id"]) if sess.get("payment_status") == "paid" else None
        return find_payment(self.rpc, ref, self.recipient, q["amount"])

    def status(self, ref: str) -> dict:
        q = self.quotes.get(ref)
        if q is None:
            raise HTTPException(404, "No such payment request. Ask for a new quote. Nothing was recorded.")
        if q["signature"] is None:
            try:
                q["signature"] = self._found(ref, q)
            except PaymentError as exc:
                return {"reference": ref, "status": "invalid", "code": exc.code, "note": self.note}
        return {"reference": ref, "status": "paid" if q["signature"] else "pending", "signature": q["signature"],
                "used": q["used"], "note": self.note}

    @property
    def note(self) -> str:
        return STRIPE_NOTE if self.mode == "stripe-test" else TEST_NOTE

    def check_for_retire(self, ref: Optional[str], owner: str, grams: int) -> dict:
        """Outside the lock (it may ask the chain). Raises HTTPException 402 with a code, before anything is recorded."""
        if not ref:
            raise HTTPException(402, "PAYMENT_REQUIRED: ask for a quote and pay it first (test mode, no real money). Nothing was recorded.")
        q = self.quotes.get(ref)
        if q is None or q["owner"] != owner:
            raise HTTPException(402, "PAYMENT_NOT_FOUND: this payment request is not yours or does not exist. Nothing was recorded.")
        if q["grams"] != grams:
            raise HTTPException(402, f"PAYMENT_MISMATCH: the quote was for {q['grams']} g, this retirement is {grams} g. Nothing was recorded.")
        st = self.status(ref)
        if st["status"] != "paid":
            code = st.get("code", "PAYMENT_PENDING")
            raise HTTPException(402, f"{code}: the payment is not confirmed on chain yet. Nothing was recorded.")
        if q["used"]:
            raise HTTPException(409, "PAYMENT_USED: this payment already paid for a retirement. Nothing was recorded.")
        return q

    def mark_used(self, ref: str) -> None:
        with self.lock:
            self.quotes[ref]["used"] = True


def payments_from_env() -> Payments:
    mode = os.environ.get("PAYMENTS_MODE", "").strip()
    if not mode:
        return Payments()
    if mode == "stripe-test":
        key = os.environ.get("STRIPE_SECRET_KEY", "").strip()
        if not key.startswith("sk_test_"):
            raise RuntimeError("PAYMENTS_MODE=stripe-test needs STRIPE_SECRET_KEY to be a TEST key (sk_test_...). Live keys are refused.")

        def stripe(method: str, path: str, data: dict) -> dict:
            import httpx
            r = httpx.request(method, "https://api.stripe.com" + path, data=data if method == "POST" else None, auth=(key, ""), timeout=20)
            body = r.json()
            if r.status_code >= 400:
                raise PaymentError("STRIPE_ERROR", str(body.get("error", {}).get("message", ""))[:120])
            return body
        return Payments(mode, stripe=stripe, pence_per_tonne=int(os.environ.get("PRICE_PENCE_PER_TONNE", "10000")),
                        public_url=os.environ.get("PUBLIC_URL", "https://carbonledger.world"))
    url = os.environ.get("SOLANA_RPC_URL", "").strip()
    recipient = os.environ.get("PAYMENT_RECIPIENT", "").strip()
    if not recipient:
        secret = os.environ.get("SOLANA_SECRET_KEY_B58", "").strip()
        if secret and not secret.startswith("<"):
            from solders.keypair import Keypair
            recipient = str(Keypair.from_base58_string(secret).pubkey())
    if not url:
        raise RuntimeError("PAYMENTS_MODE is set but SOLANA_RPC_URL is not.")

    def rpc(method: str, params: list):
        import httpx
        r = httpx.post(url, json={"jsonrpc": "2.0", "id": secrets.token_hex(4), "method": method, "params": params}, timeout=15)
        r.raise_for_status(); body = r.json()
        if "error" in body:
            raise PaymentError("RPC_ERROR", str(body["error"])[:120])
        return body.get("result")
    return Payments(mode, recipient, int(os.environ.get("PRICE_LAMPORTS_PER_TONNE", "100000000")), rpc)


def payments_router(pay: Payments, require_key: Callable) -> APIRouter:
    r = APIRouter()

    @r.post("/v1/pay/quote", status_code=201)
    def quote(body: QuoteIn, caller=Depends(require_key)):
        if not pay.on:
            raise HTTPException(404, "Payments are not switched on here. Nothing was recorded.")
        return pay.quote(caller.owner, body.grams)

    @r.get("/v1/pay/{reference}")
    def status(reference: str):
        if not pay.on:
            raise HTTPException(404, "Payments are not switched on here.")
        return pay.status(reference)

    return r
