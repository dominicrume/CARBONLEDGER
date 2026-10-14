"""XP on the server, for leaderboards (a browser total is never a score). The same rules as apps/web/js/core/xp.js,
and both pass conformance/xp_vectors.json: XP pays for actions and habits, never for emitting more.
  size 5..150 on log10(grams), only the first 5 retirements of a UTC day score,
  +100 for the first retirement of a week (weeks start Sunday, UTC), +40 per new kind of action that week."""
import math
from datetime import date, timedelta
from typing import Dict, Iterable, Tuple

DAILY_COUNTED, WEEK_XP, KIND_XP = 5, 100, 40


def size_xp(grams: int) -> int:
    if not grams or grams <= 0:
        return 0
    return max(5, min(150, math.floor(25 * math.log10(grams) + 0.5)))    # half up, like JavaScript's Math.round


def week_of(ts: str) -> str:
    d = date.fromisoformat(str(ts)[:10])
    return (d - timedelta(days=(d.weekday() + 1) % 7)).isoformat()


def xp_of(records: Iterable[dict]) -> Tuple[int, Dict[str, int]]:
    """records: dicts with id, ts (ISO), grams, kind, mode. Returns (total, xp per record id)."""
    per_day: Dict[str, int] = {}
    weeks: Dict[str, set] = {}
    each: Dict[str, int] = {}
    total = 0
    for r in sorted(records, key=lambda r: str(r["ts"])):
        d, w = str(r["ts"])[:10], week_of(r["ts"])
        per_day[d] = per_day.get(d, 0) + 1
        x = size_xp(r["grams"]) if per_day[d] <= DAILY_COUNTED else 0
        if w not in weeks:
            weeks[w] = set()
            x += WEEK_XP
        if r.get("kind") and r["kind"] not in weeks[w]:
            weeks[w].add(r["kind"])
            x += KIND_XP
        each[r["id"]] = x
        total += x
    return total, each
