"""Writes conformance/merkle_vectors.json from the Python tree and checks it is unchanged, so the browser verifier
(apps/web/test/merkle.test.mjs) proves the same vectors."""
import hashlib
import json
from pathlib import Path

from carbonledger.merkle import proof, root

PATH = Path(__file__).resolve().parents[1] / "conformance" / "merkle_vectors.json"


def _vectors():
    out = []
    for n in (1, 2, 3, 5, 8, 13):
        hs = [hashlib.sha256(f"merkle-{n}-{i}".encode()).hexdigest() for i in range(n)]
        r = root(hs)
        for i in sorted({0, n // 2, n - 1}):
            out.append({"name": f"n{n}-leaf{i}", "leaf": hs[i], "path": proof(hs, i), "root": r})
    return out


def test_vectors_file_matches_the_python_tree():
    want = _vectors()
    if not PATH.exists():
        PATH.write_text(json.dumps(want, indent=1) + "\n", encoding="utf-8")
    got = json.loads(PATH.read_text(encoding="utf-8"))
    assert [[list(p) for p in v["path"]] for v in want] == [v["path"] for v in got]
    assert [v["root"] for v in want] == [v["root"] for v in got]
