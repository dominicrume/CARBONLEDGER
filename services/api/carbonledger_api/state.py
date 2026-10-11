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
from carbonledger.mandate import Mandate
from carbonledger.registry import Batch, Project, Registry, Retirement

from .lookup import ProductLookup, lookup_from_env
from .store import MemoryStore, store_from_env

DEMO_PROJECT, DEMO_BATCH = "demo-pilot-1", "pilot-2026"
DEMO_ISSUED_G = 1_000_000_000          # 1,000 tonnes, simulated (ASSUMPTION for the demo)
HEALTH_CACHE_S = 10.0                  # how long one chain health answer is trusted before asking again


class Limits:
    """Edge limits, from the environment or a test."""
    def __init__(self, rate_per_minute: int = 60, burst: int = 20, max_request_bytes: int = 65536, request_timeout_s: float = 40.0,
                 agent_sig_max_age_s: int = 120):
        self.rate_per_minute, self.burst, self.max_request_bytes, self.request_timeout_s = rate_per_minute, burst, max_request_bytes, request_timeout_s
        self.agent_sig_max_age_s = agent_sig_max_age_s

    @classmethod
    def from_env(cls) -> "Limits":
        e = os.environ.get
        return cls(int(e("RATE_LIMIT_PER_MINUTE", "60")), int(e("RATE_LIMIT_BURST", "20")), int(e("MAX_REQUEST_BYTES", "65536")),
                   float(e("REQUEST_TIMEOUT_SECONDS", "40")), int(e("AGENT_SIGNATURE_MAX_AGE_SECONDS", "120")))


class State:
    def __init__(self, chain: ChainClient, now: Callable[[], float] = time.time, anchor_wait_s: float = 0.0,
                 keys: Optional[ApiKeyStore] = None, limits: Optional[Limits] = None, product_lookup: Optional[ProductLookup] = None,
                 store=None, anchor_interval_s: float = 0.0):
        self.lock = threading.Lock()
        self.product_lookup = product_lookup or lookup_from_env()
        self.chain_client, self.now, self.anchor_wait_s = chain, now, anchor_wait_s
        self.limits = limits or Limits()
        self.keys = keys or keys_from_env()
        self.bucket = TokenBucket(self.limits.rate_per_minute, self.limits.burst)
        self.store = store if store is not None else store_from_env(os.environ.get("DATABASE_URL"))
        self.registry = Registry(authority="trustee", verifiers={"verifier-1"})
        self.receipts = ReceiptChain()
        self.outbox = AnchorOutbox()
        self.outbox.on_change = self.store.update_outbox
        self.worker = AnchorWorker(chain, self.outbox, now=now, batch_window_s=anchor_interval_s)
        self.idem = {}                          # key -> (payload digest, receipt id)
        self.mandates = {}
        self._health: Optional[bool] = None
        self._health_at = 0.0
        saved = self.store.load()
        if saved is None:
            r = self.registry
            r.register_project("trustee", DEMO_PROJECT, "GBR", "SIMULATED-PILOT")
            r.attest_project("verifier-1", DEMO_PROJECT, DEMO_ISSUED_G)
            r.issue_batch("trustee", DEMO_PROJECT, DEMO_BATCH, 2026, DEMO_ISSUED_G)
            self.store.seed(r.projects.values(), r.batches.values())
        else:
            self._restore(saved)

    def _restore(self, s: dict) -> None:
        """Rebuild from storage. The receipt chain is verified first: a broken chain refuses to start."""
        self.receipts = ReceiptChain.from_entries(s["receipts"])
        r = self.registry
        r.projects = {row[0]: Project(*row) for row in s["projects"]}
        r.batches = {row[0]: Batch(*row) for row in s["batches"]}
        r.retirements = [Retirement(*row) for row in s["retirements"]]
        r.check_invariants()
        self.outbox.restore(s["outbox"])
        self.idem = {k: (d, rid) for k, d, rid in s["idem"]}
        for mid, owner, agent, cap, used, exp, allow, revoked in s["mandates"]:
            self.mandates[mid] = Mandate(mid, owner, agent, cap, int(exp), tuple(allow) if allow is not None else None, used, revoked)
        for key_id, role, owner, key_hash, revoked in s["api_keys"]:
            rec = self.keys.add_hashed(role, owner, key_hash, key_id)
            rec.revoked = revoked

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
        secret = _real(os.environ.get("SOLANA_SECRET_KEY_B58"))
        if not secret:
            raise RuntimeError("CHAIN_MODE is solana-devnet but SOLANA_SECRET_KEY_B58 is unset or still a placeholder")
        urls = [os.environ["SOLANA_RPC_URL"], os.environ.get("SOLANA_RPC_URL_FALLBACK", "")]
        return SolanaMemoChain(urls, secret, "devnet", timeout=float(os.environ.get("SOLANA_RPC_TIMEOUT_SECONDS", "15")))
    return DryRunChain()


def anchor_interval_from_env() -> float:
    return float(os.environ.get("ANCHOR_INTERVAL_SECONDS", "2"))


def anchor_wait_from_env() -> float:
    return float(os.environ.get("ANCHOR_WAIT_SECONDS", "20"))


def _real(v: Optional[str]) -> str:
    """A value still in its <placeholder> form from .env.example counts as unset."""
    v = (v or "").strip()
    return "" if v.startswith("<") else v


def keys_from_env() -> ApiKeyStore:
    """API_KEY_PEPPER is required outside dev and test. API_KEYS holds role:owner:hash entries made by
    scripts/make_api_key.py. In dev or test only, API_DEMO_KEY may supply one plaintext key for local tools."""
    env = os.environ.get("APP_ENV", "")
    pepper = _real(os.environ.get("API_KEY_PEPPER"))
    if not pepper:
        if env not in ("dev", "test"):
            raise RuntimeError("API_KEY_PEPPER is not set. The API refuses to start without it outside dev and test.")
        pepper = secrets.token_hex(32)
    store = ApiKeyStore(pepper)
    for item in filter(None, _real(os.environ.get("API_KEYS")).split(",")):
        role, owner, key_hash = item.strip().split(":", 2)
        store.add_hashed(role, owner, key_hash)
    demo = _real(os.environ.get("API_DEMO_KEY"))
    demo_biz = _real(os.environ.get("API_DEMO_BUSINESS_KEY"))
    if env in ("dev", "test") and (demo or demo_biz):
        from carbonledger.auth import hash_key
        if demo:
            store.add_hashed("personal", "demo", hash_key(pepper, demo), "key-demo")
        if demo_biz:
            store.add_hashed("business", "demo-business", hash_key(pepper, demo_biz), "key-demo-business")
    elif env == "dev" and store.count() == 0:
        key, _ = store.issue("personal", "demo")
        print(f"[dev] no API_KEYS configured; a demo key was minted for this process only: {key}", file=sys.stderr)
    return store
