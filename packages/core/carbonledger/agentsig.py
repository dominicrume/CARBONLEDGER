"""Agent identity (KYA). A mandate names the agent's ed25519 public key. An agent request carries a timestamp and a
signature over the request digest. The server verifies the signature, checks the timestamp window, then checks the
mandate. A name is not an identity; a key is. The same shape maps to the Solana agent registry later.

Message signed: sha256 of the canonical request body with `agent_sig` removed and every null field dropped, so a
client that omits a field and one that sends it as null sign the same bytes. The body includes agent, agent_ts
and the idempotency key, so a replay with a new key fails and a replay with the same key is just idempotent."""
from typing import Optional

from .receipts import digest

MAX_FUTURE_SKEW_S = 30
PREFIX = b"carbonledger:agent:v1:"


class AgentSigError(ValueError):
    def __init__(self, code: str, message: str = ""):
        super().__init__(f"{code}: {message}" if message else code)
        self.code = code


def canonical(request_without_sig: dict) -> dict:
    return {k: v for k, v in request_without_sig.items() if v is not None and k != "agent_sig"}


def agent_message(request_without_sig: dict) -> bytes:
    return PREFIX + digest(canonical(request_without_sig)).encode("ascii")


def is_pubkey(b58: Optional[str]) -> bool:
    try:
        from solders.pubkey import Pubkey
        return b58 is not None and len(bytes(Pubkey.from_string(b58))) == 32
    except Exception:  # noqa: BLE001
        return False


def check_timestamp(agent_ts: Optional[int], now: int, max_age_s: int) -> None:
    if agent_ts is None:
        raise AgentSigError("NO_TIMESTAMP")
    if agent_ts > now + MAX_FUTURE_SKEW_S:
        raise AgentSigError("FUTURE_TIMESTAMP", "the request is dated in the future")
    if now - agent_ts > max_age_s:
        raise AgentSigError("EXPIRED_SIGNATURE", f"older than {max_age_s} seconds; a replay or a slow clock")


def verify_agent(pubkey_b58: Optional[str], sig_b58: Optional[str], request_without_sig: dict) -> None:
    """Raise AgentSigError unless `sig_b58` is a valid ed25519 signature by `pubkey_b58` over the request."""
    from solders.pubkey import Pubkey
    from solders.signature import Signature
    if not is_pubkey(pubkey_b58):
        raise AgentSigError("BAD_AGENT_KEY", "agent must be a base58 ed25519 public key")
    if not sig_b58:
        raise AgentSigError("NO_SIGNATURE")
    try:
        sig = Signature.from_string(sig_b58)
    except Exception:  # noqa: BLE001
        raise AgentSigError("BAD_SIGNATURE", "not a base58 signature")
    if not sig.verify(Pubkey.from_string(pubkey_b58), agent_message(request_without_sig)):
        raise AgentSigError("BAD_SIGNATURE", "the signature does not match the agent key and the request")


def sign_request(keypair, request_without_sig: dict) -> str:
    """For agents and tests: sign a request with a solders Keypair. Returns the base58 signature."""
    return str(keypair.sign_message(agent_message(request_without_sig)))
