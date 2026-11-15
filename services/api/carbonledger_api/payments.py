"""Payments, TEST MODE ONLY (docs/DECISIONS.md 2026-11-15, DEBT D29). Off unless PAYMENTS_MODE=solana-devnet-test.
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

MODES = ("solana-devnet-test",)
QUOTE_TTL_S = 900


class QuoteIn(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    grams: int = Field(gt=0, le=10**12)


class Payments:
    def __init__(self, mode: str = "", recipient: str = "", lamports_per_tonne: int = 100_000_000,
                 rpc: Optional[Callable[[str, list], object]] = None, now: Callable[[], float] = None):
        if mode and mode not in MODES:
            raise RuntimeError(f"PAYMENTS_MODE must be one of {MODES} or unset (got {mode}). Real money is not supported.")
        if mode and (not recipient or rpc is None):
            raise RuntimeError("PAYMENTS_MODE is set but there is no treasury address or chain RPC.")
        self.mode, self.recipient, self.lamports_per_tonne, self.rpc = mode, recipient, lamports_per_tonne, rpc
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
        lam = lamports_for(grams, self.lamports_per_tonne)
        ref = self.new_reference()
        exp = int(self.now()) + QUOTE_TTL_S
        with self.lock:
            self.quotes[ref] = {"owner": owner, "grams": grams, "lamports": lam, "expires": exp, "used": False, "signature": None}
        return {"reference": ref, "recipient": self.recipient, "lamports": lam, "amount": sol_text(lam), "currency": "SOL (devnet test)",
                "grams": grams, "expires_at": exp, "mode": self.mode, "note": TEST_NOTE,
                "url": transfer_url(self.recipient, lam, ref, "CarbonLedger (test)", f"Retire {grams} g of pilot units. Test mode, no real money.")}

    def status(self, ref: str) -> dict:
        q = self.quotes.get(ref)
        if q is None:
            raise HTTPException(404, "No such payment request. Ask for a new quote. Nothing was recorded.")
        if q["signature"] is None:
            try:
                q["signature"] = find_payment(self.rpc, ref, self.recipient, q["lamports"])
            except PaymentError as exc:
                return {"reference": ref, "status": "invalid", "code": exc.code, "note": TEST_NOTE}
        return {"reference": ref, "status": "paid" if q["signature"] else "pending", "signature": q["signature"],
                "used": q["used"], "note": TEST_NOTE}

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
