"""Merkle anchoring (D15, T22). Many receipts, one on-chain root per interval. Each receipt keeps a proof path, so
anyone can show that its hash is under the anchored root without the other receipts.

Leaves are receipt entry hashes (hex). Node = sha256(0x01 || left || right) over raw bytes; a leaf is hashed as
sha256(0x00 || leaf) first, so a leaf can never be passed off as a node (second-preimage guard). An odd node at any
level is paired with itself. The browser verifier (apps/web/js/core/merkle.js) implements the same rules."""
import hashlib
from typing import List, Tuple

LEAF, NODE = b"\x00", b"\x01"


def _h(prefix: bytes, *parts: bytes) -> bytes:
    return hashlib.sha256(prefix + b"".join(parts)).digest()


def leaf_hash(hex_hash: str) -> bytes:
    return _h(LEAF, bytes.fromhex(hex_hash))


def _levels(leaves: List[bytes]) -> List[List[bytes]]:
    if not leaves:
        raise ValueError("a Merkle tree needs at least one leaf")
    levels = [leaves]
    while len(levels[-1]) > 1:
        cur = levels[-1]
        nxt = [_h(NODE, cur[i], cur[i + 1] if i + 1 < len(cur) else cur[i]) for i in range(0, len(cur), 2)]
        levels.append(nxt)
    return levels


def root(hex_hashes: List[str]) -> str:
    return _levels([leaf_hash(h) for h in hex_hashes])[-1][0].hex()


def proof(hex_hashes: List[str], index: int) -> List[Tuple[str, str]]:
    """The sibling path for leaf `index`: a list of (side, hex) where side is 'L' if the sibling is on the left."""
    levels = _levels([leaf_hash(h) for h in hex_hashes])
    path, i = [], index
    for level in levels[:-1]:
        sib = i ^ 1
        sibling = level[sib] if sib < len(level) else level[i]
        path.append(("L" if sib < i else "R", sibling.hex()))
        i //= 2
    return path


def verify_proof(hex_hash: str, path: List[Tuple[str, str]], expected_root: str) -> bool:
    cur = leaf_hash(hex_hash)
    for side, sib_hex in path:
        sib = bytes.fromhex(sib_hex)
        cur = _h(NODE, sib, cur) if side == "L" else _h(NODE, cur, sib)
    return cur.hex() == expected_root
