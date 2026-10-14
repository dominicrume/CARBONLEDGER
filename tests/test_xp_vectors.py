"""The server's XP rules and the browser's (apps/web/js/core/xp.js) pass the same vectors: a leaderboard and the
player's own screen can never disagree. XP pays for habits, never for emitting more."""
import json
from pathlib import Path

from carbonledger_api.xp import size_xp, xp_of

V = json.loads((Path(__file__).resolve().parents[1] / "conformance" / "xp_vectors.json").read_text(encoding="utf-8"))


def test_size_matches_the_shared_vectors():
    assert [size_xp(g) for g, _ in V["size"]] == [w for _, w in V["size"]]


def test_histories_match_the_shared_vectors():
    for h in V["histories"]:
        assert xp_of(h["records"])[0] == h["total"], h["name"]
