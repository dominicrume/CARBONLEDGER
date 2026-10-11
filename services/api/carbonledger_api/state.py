"""Server state: the register, the receipt chain, the anchor outbox, idempotency and mandates. In memory today (D9).
The chain client comes from the environment. Keys come from the secret store, never from the repo."""
import os
import secrets
import sys
import threading
import time
from typing import Callable, Optional

from carbonledger.auth import ApiKeyStore, TokenBucket
from carbonledger.chain import ChainClient, DryRunChain, SolanaMemoChain
from carbonledger.outbox import AnchorOutbox, AnchorWorker
from carbonledger.receipts import ReceiptChain
from carbonledger.registry import Registry

DEMO_PROJECT, DEMO_BATCH = "demo-pilot-1", "pilot-2026"
DEMO_ISSUED_G = 1_000_000_000          # 1,000 tonnes, simulated (ASSUMPTION for the demo)
HEALTH_CACHE_S = 10.0                  # how long one chain health answer is trusted before asking again


class Limits:
    """Edge limits, from the environment or a test."""
    def __init__(self, rate_per_minute: int = 60, burst: int = 20, max_request_bytes: int = 65536, request_timeout_s: float = 40.0):
        self.rate_per_minute, self.burst, self.max_request_bytes, self.request_timeout_s = rate_per_minute, burst, max_request_bytes, request_timeout_s

    @classmethod
    def from_env(cls) -> "Limits":
        e = os.environ.get
        return cls(int(e("RATE_LIMIT_PER_MINUTE", "60")), int(e("RATE_LIMIT_BURST", "20")), int(e("MAX_REQUEST_BYTES", "65536")),
                   float(e("REQUEST_TIMEOUT_SECONDS", "40")))


class State:
    def __init__(self, chain: ChainClient, now: Callable[[], float] = time.time, anchor_wait_s: float = 0.0,
                 keys: Optional[ApiKeyStore] = None, limits: Optional[Limits] = None):
        self.lock = threading.Lock()
        self.chain_client, self.now, self.anchor_wait_s = chain, now, anchor_wait_s
        self.limits = limits or Limits()
        self.keys = keys or keys_from_env()
        self.bucket = TokenBucket(self.limits.rate_per_minute, self.limits.burst)
        self.registry = Registry(authority="trustee", verifiers={"verifier-1"})
        self.receipts = ReceiptChain()
        self.outbox = AnchorOutbox()
        self.worker = AnchorWorker(chain, self.outbox, now=now)
        self.idem = {}                          # key -> (payload digest, response)
        self.mandates = {}
        self._health: Optional[bool] = None
        self._health_at = 0.0
        r = self.registry
        r.register_project("trustee", DEMO_PROJECT, "GBR", "SIMULATED-PILOT")
        r.attest_project("verifier-1", DEMO_PROJECT, DEMO_ISSUED_G)
        r.issue_batch("trustee", DEMO_PROJECT, DEMO_BATCH, 2026, DEMO_ISSUED_G)

    def chain_healthy(self) -> bool:
        """Asked before committing a retirement. If the chain is known to be down, nothing is recorded."""
        t = time.monotonic()
        if self._health is None or t - self._health_at > HEALTH_CACHE_S:
            self._health, self._health_at = bool(self.chain_client.health()), t
        return self._health

    def forget_health(self) -> None:
        self._health = None


def chain_from_env() -> ChainClient:
    if os.environ.get("CHAIN_MODE", "dry-run") == "solana-devnet":
        urls = [os.environ["SOLANA_RPC_URL"], os.environ.get("SOLANA_RPC_URL_FALLBACK", "")]
        return SolanaMemoChain(urls, os.environ["SOLANA_SECRET_KEY_B58"], "devnet",
                               timeout=float(os.environ.get("SOLANA_RPC_TIMEOUT_SECONDS", "15")))
    return DryRunChain()


def anchor_wait_from_env() -> float:
    return float(os.environ.get("ANCHOR_WAIT_SECONDS", "20"))


def keys_from_env() -> ApiKeyStore:
    """API_KEY_PEPPER is required outside dev and test. API_KEYS holds role:owner:hash entries made by
    scripts/make_api_key.py. In dev or test only, API_DEMO_KEY may supply one plaintext key for local tools."""
    env = os.environ.get("APP_ENV", "")
    pepper = os.environ.get("API_KEY_PEPPER", "")
    if not pepper:
        if env not in ("dev", "test"):
            raise RuntimeError("API_KEY_PEPPER is not set. The API refuses to start without it outside dev and test.")
        pepper = secrets.token_hex(32)
    store = ApiKeyStore(pepper)
    for item in filter(None, os.environ.get("API_KEYS", "").split(",")):
        role, owner, key_hash = item.strip().split(":", 2)
        store.add_hashed(role, owner, key_hash)
    demo = os.environ.get("API_DEMO_KEY", "")
    if demo and env in ("dev", "test"):
        from carbonledger.auth import hash_key
        store.add_hashed("personal", "demo", hash_key(pepper, demo), "key-demo")
    elif env == "dev" and store.count() == 0:
        key, _ = store.issue("personal", "demo")
        print(f"[dev] no API_KEYS configured; a demo key was minted for this process only: {key}", file=sys.stderr)
    return store
