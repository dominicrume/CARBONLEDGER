"""Server state: the register, the receipt chain, the anchor outbox, idempotency and mandates. In memory today (D9).
The chain client comes from the environment. Keys come from the secret store, never from the repo."""
import os
import threading
import time
from typing import Callable, Optional

from carbonledger.chain import ChainClient, DryRunChain, SolanaMemoChain
from carbonledger.outbox import AnchorOutbox, AnchorWorker
from carbonledger.receipts import ReceiptChain
from carbonledger.registry import Registry

DEMO_PROJECT, DEMO_BATCH = "demo-pilot-1", "pilot-2026"
DEMO_ISSUED_G = 1_000_000_000          # 1,000 tonnes, simulated (ASSUMPTION for the demo)
HEALTH_CACHE_S = 10.0                  # how long one chain health answer is trusted before asking again


class State:
    def __init__(self, chain: ChainClient, now: Callable[[], float] = time.time, anchor_wait_s: float = 0.0):
        self.lock = threading.Lock()
        self.chain_client, self.now, self.anchor_wait_s = chain, now, anchor_wait_s
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
