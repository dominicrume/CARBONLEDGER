"""Sign in with Seeker: Sign in with Solana (SIWS) on a Seeker's wallet, then a read-only check on Solana mainnet for a
Seeker Genesis Token (SGT). Nothing is ever sent to the chain and no transaction is signed.

SIWS: the server issues a one-time nonce; the wallet signs a SIWS message that names our domain, the wallet address
and that nonce. We check the signature (ed25519), the domain, the address and the nonce (used once, 10 minutes).

SGT (docs.solanamobile.com, "Seeker Genesis Token"; mint-authority check removed upstream, PR #49, Sep 2026): a
Token-2022 mint whose Token Group Member extension points at the Seeker group, held with a balance above zero."""
import base64
import os
from typing import Callable, Optional

import httpx

SGT_GROUP = "GT22s89nU4iWFkNXj1Bw6uYhJJWDRPpShHt4Bk8f99Te"
TOKEN_2022 = "TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb"
NONCE_TTL_S = 10 * 60
STATEMENT = "Sign in to CarbonLedger. This signs a message only: no transaction, no payment, nothing moves."


class SeekerError(ValueError):
    pass


def challenge(domain: str, uri: str, nonce: str, issued_at: str, expires_at: str) -> dict:
    """The SIWS input the wallet turns into the message it signs (Wallet Standard solana:signIn)."""
    return {"domain": domain, "statement": STATEMENT, "uri": uri, "version": "1", "nonce": nonce,
            "issuedAt": issued_at, "expirationTime": expires_at}


def check_sign_in(domain: str, address: str, signed_message_b64: str, signature_b64: str) -> str:
    """Verifies a SIWS result. Returns the nonce it carries; raises SeekerError otherwise."""
    from solders.pubkey import Pubkey
    from solders.signature import Signature
    try:
        msg = base64.b64decode(signed_message_b64, validate=True)
        sig = Signature.from_bytes(base64.b64decode(signature_b64, validate=True))
        key = Pubkey.from_string(address)
    except Exception:
        raise SeekerError("the sign-in result is not well formed")
    if not sig.verify(key, msg):
        raise SeekerError("the signature does not match this wallet")
    lines = msg.decode("utf-8", "replace").split("\n")
    if len(lines) < 2 or lines[0] != f"{domain} wants you to sign in with your Solana account:" or lines[1] != address:
        raise SeekerError(f"the message is not a sign-in to {domain} for this wallet")
    nonce = next((l[len("Nonce: "):] for l in lines if l.startswith("Nonce: ")), "")
    if not nonce:
        raise SeekerError("the message carries no nonce")
    return nonce


def sgt_lookup_rpc(url: str, timeout: float = 10.0) -> Callable[[str], Optional[str]]:
    """Returns a function: wallet address -> the mint of a Seeker Genesis Token it holds, or None. Read-only RPC."""
    def rpc(method: str, params: list) -> dict:
        r = httpx.post(url, json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params}, timeout=timeout)
        r.raise_for_status()
        body = r.json()
        if "error" in body:
            raise SeekerError(f"the Solana RPC refused {method}")
        return body["result"]

    def lookup(wallet: str) -> Optional[str]:
        accts = rpc("getTokenAccountsByOwner", [wallet, {"programId": TOKEN_2022}, {"encoding": "jsonParsed"}])["value"]
        mints = [a["account"]["data"]["parsed"]["info"]["mint"] for a in accts
                 if int(a["account"]["data"]["parsed"]["info"]["tokenAmount"]["amount"]) > 0]          # empty accounts are not ownership
        for i in range(0, len(mints), 100):
            for mint, acc in zip(mints[i:i + 100], rpc("getMultipleAccounts", [mints[i:i + 100], {"encoding": "jsonParsed"}])["value"]):
                if sgt_mint_ok(acc):
                    return mint
        return None
    return lookup


def sgt_mint_ok(acc: Optional[dict]) -> bool:
    """A Token-2022 mint that is a member of the Seeker Genesis group."""
    if not acc or acc.get("owner") != TOKEN_2022:
        return False
    info = (acc.get("data") or {}).get("parsed", {}).get("info", {})
    for ext in info.get("extensions", []) or []:
        if ext.get("extension") == "tokenGroupMember" and (ext.get("state") or {}).get("group") == SGT_GROUP:
            return True
    return False


def sgt_lookup_from_env() -> Callable[[str], Optional[str]]:
    return sgt_lookup_rpc(os.environ.get("SOLANA_MAINNET_RPC_URL", "https://api.mainnet-beta.solana.com"))
