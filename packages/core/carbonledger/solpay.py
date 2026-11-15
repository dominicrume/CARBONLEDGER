"""Solana Pay, TEST MODE ONLY (docs/DECISIONS.md 2026-11-15, DEBT D29). A quote names the recipient, an amount in
lamports and a one-time reference key; the person's wallet pays it; the server finds the payment on chain by the
reference and checks it before anything is recorded. Money is integers (lamports) and Decimal for display, never float.
Spec: https://docs.solanapay.com/spec (transfer requests: solana:<recipient>?amount=&reference=&label=&message=)."""
from decimal import Decimal
from typing import Callable, Optional
from urllib.parse import quote

LAMPORTS_PER_SOL = 1_000_000_000
MIN_LAMPORTS = 1_000                       # never quote a zero payment
TEST_NOTE = "Test mode: paid with Solana devnet test tokens. No real money moves."


class PaymentError(ValueError):
    def __init__(self, code: str, message: str = ""):
        super().__init__(f"{code}: {message}" if message else code)
        self.code = code


def lamports_for(grams: int, lamports_per_tonne: int) -> int:
    """Price of a retirement, rounded up to the next lamport (1 tonne = 1,000,000 g). Integers only."""
    if not isinstance(grams, int) or isinstance(grams, bool) or grams <= 0:
        raise PaymentError("BAD_AMOUNT")
    return max(MIN_LAMPORTS, -(-grams * lamports_per_tonne // 1_000_000))


def sol_text(lamports: int) -> str:
    """Exact decimal SOL for the URL and the screen, with no trailing zeros (Decimal, never float)."""
    d = (Decimal(lamports) / Decimal(LAMPORTS_PER_SOL)).normalize()
    return format(d, "f")


def transfer_url(recipient: str, lamports: int, reference: str, label: str, message: str) -> str:
    return (f"solana:{recipient}?amount={sol_text(lamports)}&reference={reference}"
            f"&label={quote(label)}&message={quote(message)}")


def find_payment(rpc: Callable[[str, list], object], reference: str, recipient: str, min_lamports: int) -> Optional[str]:
    """Signature of a confirmed, successful transaction that carries `reference` and pays `recipient` at least
    `min_lamports`; None while nothing is on chain yet. A transaction that carries the reference but fails the
    checks raises PaymentError, so a short or misdirected payment is reported, never silently accepted."""
    sigs = rpc("getSignaturesForAddress", [reference, {"limit": 20, "commitment": "confirmed"}]) or []
    seen_bad = None
    for s in sigs:
        if s.get("err") is not None:
            seen_bad = "PAYMENT_FAILED"; continue
        tx = rpc("getTransaction", [s["signature"], {"encoding": "json", "commitment": "confirmed", "maxSupportedTransactionVersion": 0}])
        if not tx or (tx.get("meta") or {}).get("err") is not None:
            seen_bad = "PAYMENT_FAILED"; continue
        keys = [k if isinstance(k, str) else k.get("pubkey") for k in tx["transaction"]["message"]["accountKeys"]]
        if reference not in keys:
            continue
        if recipient not in keys:
            seen_bad = "WRONG_RECIPIENT"; continue
        i = keys.index(recipient); meta = tx["meta"]
        if meta["postBalances"][i] - meta["preBalances"][i] < min_lamports:
            seen_bad = "UNDERPAID"; continue
        return s["signature"]
    if seen_bad:
        raise PaymentError(seen_bad, "a transaction carries this reference but does not pay the quote")
    return None
