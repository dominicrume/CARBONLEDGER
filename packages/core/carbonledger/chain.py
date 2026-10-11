"""Chain clients. The API talks to a ChainClient and never knows which. DryRunChain is the default.
SolanaMemoChain writes a short memo (receipt id and hash only) with a server-held key, then confirms it.
Browsers never hold a signing key. Keys come from the secret store, never from the repo.

Two steps, on purpose (D5): `record` submits and returns a signature. `confirm` waits until the cluster confirms
the signature or the blockhash expires. Nothing is called "recorded on Solana" until `confirm` returns."""
import base64
import hashlib
import threading
import time
from dataclasses import dataclass, replace
from typing import List, Optional, Protocol, Sequence

MEMO_PROGRAM_ID = "MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr"   # SPL Memo v2
TRANSIENT_HTTP = {408, 425, 429, 500, 502, 503, 504}


class ChainError(RuntimeError):
    pass


@dataclass(frozen=True)
class ChainRecord:
    signature: str
    explorer_url: str
    cluster: str
    slot: Optional[int] = None          # set once confirmed
    confirmed: bool = False


class ChainClient(Protocol):
    cluster: str
    def health(self) -> bool: ...
    def record(self, receipt_id: str, receipt_hash: str) -> ChainRecord: ...
    def confirm(self, rec: ChainRecord) -> ChainRecord: ...


class DryRunChain:
    """Records nothing anywhere. The signature is clearly fake so nobody mistakes it for a transaction."""
    cluster = "dry-run"

    def health(self) -> bool:
        return True

    def record(self, receipt_id: str, receipt_hash: str) -> ChainRecord:
        sig = "dryrun-" + hashlib.sha256(f"{receipt_id}{receipt_hash}".encode()).hexdigest()[:32]
        return ChainRecord(sig, "", self.cluster)

    def confirm(self, rec: ChainRecord) -> ChainRecord:
        return replace(rec, confirmed=True, slot=0)


def memo_text(receipt_id: str, receipt_hash: str) -> str:
    return f"carbonledger:v1:{receipt_id}:{receipt_hash}"


class RpcStats:
    """Counts calls and failures over a sliding minute, so an alert can fire when the rate passes a threshold (T21)."""
    def __init__(self, window_s: int = 60):
        self.window_s, self._events, self._lock = window_s, [], threading.Lock()

    def add(self, ok: bool, now: Optional[float] = None) -> None:
        t = now if now is not None else time.time()
        with self._lock:
            self._events.append((t, ok))
            self._events = [(ts, k) for ts, k in self._events if ts > t - self.window_s]

    def failure_rate(self, now: Optional[float] = None) -> float:
        t = now if now is not None else time.time()
        with self._lock:
            live = [k for ts, k in self._events if ts > t - self.window_s]
        return 0.0 if not live else live.count(False) / len(live)


class SolanaMemoChain:
    """Needs `pip install solders httpx`. Network calls are NOT exercised by the offline tests.
    rpc_urls: the first is primary, the rest are fallbacks tried in order on transient failure (T21)."""
    def __init__(self, rpc_urls: Sequence[str], secret_key_b58: str, cluster: str = "devnet", timeout: float = 15.0,
                 retries: int = 2, confirm_timeout: float = 60.0, poll_interval: float = 1.0, sleep=time.sleep, transport=None):
        from solders.keypair import Keypair
        urls = [u for u in rpc_urls if u]
        if not urls:
            raise ChainError("no RPC URL configured")
        self.rpc_urls, self.cluster, self.timeout, self.retries = list(urls), cluster, timeout, retries
        self.confirm_timeout, self.poll_interval, self._sleep = confirm_timeout, poll_interval, sleep
        self.payer = Keypair.from_base58_string(secret_key_b58)
        self.stats = RpcStats()
        self._transport = transport          # tests inject a callable(url, payload) -> dict

    def build_signed_tx(self, blockhash: str, text: str) -> bytes:
        from solders.hash import Hash
        from solders.instruction import AccountMeta, Instruction
        from solders.pubkey import Pubkey
        from solders.transaction import Transaction
        if len(text.encode()) > 500:
            raise ChainError("memo too long")
        ix = Instruction(Pubkey.from_string(MEMO_PROGRAM_ID), text.encode(),
                         [AccountMeta(self.payer.pubkey(), is_signer=True, is_writable=False)])
        tx = Transaction.new_signed_with_payer([ix], self.payer.pubkey(), [self.payer], Hash.from_string(blockhash))
        return bytes(tx)

    def _post(self, url: str, payload: dict) -> dict:
        if self._transport is not None:
            return self._transport(url, payload)
        import httpx
        r = httpx.post(url, json=payload, timeout=self.timeout)
        if r.status_code in TRANSIENT_HTTP:
            raise ChainError(f"transient HTTP {r.status_code}")
        r.raise_for_status()
        return r.json()

    def _rpc(self, method: str, params: list):
        payload = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
        last: Optional[Exception] = None
        for attempt in range(self.retries + 1):
            for url in self.rpc_urls:
                try:
                    data = self._post(url, payload)
                except Exception as exc:  # noqa: BLE001  network, timeout, transient status
                    self.stats.add(False)
                    last = exc
                    continue
                if "error" in data:
                    self.stats.add(False)
                    raise ChainError(f"RPC {method} error: {data['error']}")
                self.stats.add(True)
                return data["result"]
            if attempt < self.retries:
                self._sleep(0.5 * (2 ** attempt))
        raise ChainError(f"RPC {method} failed on every endpoint: {last}")

    def health(self) -> bool:
        try:
            return self._rpc("getHealth", []) == "ok"
        except ChainError:
            return False

    def record(self, receipt_id: str, receipt_hash: str) -> ChainRecord:
        bh = self._rpc("getLatestBlockhash", [{"commitment": "finalized"}])["value"]
        raw = self.build_signed_tx(bh["blockhash"], memo_text(receipt_id, receipt_hash))
        sig = self._rpc("sendTransaction", [base64.b64encode(raw).decode(), {"encoding": "base64", "preflightCommitment": "confirmed"}])
        self._last_valid_height = bh.get("lastValidBlockHeight")
        return ChainRecord(sig, f"https://explorer.solana.com/tx/{sig}?cluster={self.cluster}", self.cluster)

    def confirm(self, rec: ChainRecord) -> ChainRecord:
        """Poll until the cluster confirms the signature. Raise ChainError if it never lands before the deadline
        or the blockhash expires. The caller may then resubmit the same memo with a fresh blockhash."""
        deadline = time.monotonic() + self.confirm_timeout
        while True:
            st = self._rpc("getSignatureStatuses", [[rec.signature], {"searchTransactionHistory": True}])["value"][0]
            if st and st.get("err"):
                raise ChainError(f"transaction failed on chain: {st['err']}")
            if st and st.get("confirmationStatus") in ("confirmed", "finalized"):
                return replace(rec, confirmed=True, slot=st.get("slot"))
            last_valid = getattr(self, "_last_valid_height", None)
            if last_valid is not None and self._rpc("getBlockHeight", [{"commitment": "confirmed"}]) > last_valid:
                raise ChainError("blockhash expired before the transaction was confirmed")
            if time.monotonic() > deadline:
                raise ChainError("confirmation timed out")
            self._sleep(self.poll_interval)
