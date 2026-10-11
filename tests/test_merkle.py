import hashlib
import random
import pytest
from carbonledger.merkle import leaf_hash, proof, root, verify_proof


def _hashes(n):
    return [hashlib.sha256(f"r{i}".encode()).hexdigest() for i in range(n)]


@pytest.mark.parametrize("n", [1, 2, 3, 4, 5, 7, 8, 9, 64, 65, 256])
def test_every_leaf_proves_against_the_root(n):
    hs = _hashes(n)
    r = root(hs)
    for i in range(n):
        p = proof(hs, i)
        assert verify_proof(hs[i], p, r), (n, i)
        assert len(p) == (n - 1).bit_length() if n > 1 else len(p) == 0


def test_a_changed_leaf_or_a_wrong_proof_fails():
    hs = _hashes(6)
    r = root(hs)
    p = proof(hs, 2)
    other = hashlib.sha256(b"not in the tree").hexdigest()
    assert not verify_proof(other, p, r)
    assert not verify_proof(hs[2], proof(hs, 3), r)
    assert not verify_proof(hs[2], p, root(hs[:5]))
    flipped = [("R" if s == "L" else "L", h) for s, h in p]
    assert not verify_proof(hs[2], flipped, r)


def test_root_depends_on_order_and_a_leaf_cannot_pose_as_a_node():
    hs = _hashes(4)
    assert root(hs) != root(list(reversed(hs)))
    assert leaf_hash(hs[0]) != bytes.fromhex(hs[0])
    assert root([hs[0]]) == leaf_hash(hs[0]).hex()          # a single leaf: the root is the leaf hash


def test_random_trees_hold():
    rnd = random.Random(7)
    for _ in range(50):
        n = rnd.randint(1, 40)
        hs = _hashes(n)
        r = root(hs)
        i = rnd.randrange(n)
        assert verify_proof(hs[i], proof(hs, i), r)
