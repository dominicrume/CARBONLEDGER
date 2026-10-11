"""Chain clients. The API talks to a ChainClient and never knows which. DryRunChain is the default.
SolanaMemoChain writes a short memo (receipt id and hash only) with a server-held key.
Browsers never hold a signing key. Keys come from the secret store, never from the repo."""
import base64
import hashlib
from dataclasses import dataclass
from typing import Protocol

MEMO_PROGRAM_ID = "MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr"   # SPL Memo v2


class ChainError(RuntimeError):
    pass


@dataclass(frozen=True)
class ChainRecord:
    signature: str
    explorer_url: str
    cluster: str


class ChainClient(Protocol):
    def record(self, receipt_id: str, receipt_hash: str) -> ChainRecord: ...


class DryRunChain:
    """Records nothing anywhere. The signature is clearly fake so nobody mistakes it for a transaction."""
    cluster = "dry-run"

    def record(self, receipt_id: str, receipt_hash: str) -> ChainRecord:
        sig = "dryrun-" + hashlib.sha256(f"{receipt_id}{receipt_hash}".encode()).hexdigest()[:32]
        return ChainRecord(sig, "", self.cluster)


def memo_text(receipt_id: str, receipt_hash: str) -> str:
    return f"carbonledger:v1:{receipt_id}:{receipt_hash}"


class SolanaMemoChain:
    """Needs `pip install solders httpx`. Network part is NOT exercised by the offline tests."""
    def __init__(self, rpc_url: str, secret_key_b58: str, cluster: str = "devnet", timeout: float = 15.0):
        from solders.keypair import Keypair
        self.rpc_url, self.cluster, self.timeout = rpc_url, cluster, timeout
        self.payer = Keypair.from_base58_string(secret_key_b58)

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

    def _rpc(self, method: str, params: list):
        import httpx
        try:
            r = httpx.post(self.rpc_url, json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params}, timeout=self.timeout)
            r.raise_for_status()
            data = r.json()
        except Exception as exc:  # noqa: BLE001
            raise ChainError(f"RPC {method} failed: {exc}") from exc
        if "error" in data:
            raise ChainError(f"RPC {method} error: {data['error']}")
        return data["result"]

    def record(self, receipt_id: str, receipt_hash: str) -> ChainRecord:
        bh = self._rpc("getLatestBlockhash", [{"commitment": "finalized"}])["value"]["blockhash"]
        raw = self.build_signed_tx(bh, memo_text(receipt_id, receipt_hash))
        sig = self._rpc("sendTransaction", [base64.b64encode(raw).decode(), {"encoding": "base64", "preflightCommitment": "confirmed"}])
        return ChainRecord(sig, f"https://explorer.solana.com/tx/{sig}?cluster={self.cluster}", self.cluster)
