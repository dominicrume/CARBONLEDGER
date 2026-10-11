#!/usr/bin/env python3
"""ROOTS gate. Exit 0 only if all 13 checks are scored, every ROOTED check has
a pointer, and every HV check that is not ROOTED carries a dated waiver."""
import pathlib
import re
import sys

HV = {4, 7, 8, 11, 12, 13}


def main(ws: str) -> int:
    f = pathlib.Path(ws) / "ROOTS-SCORE.md"
    if not f.exists():
        print("BLOCKED: no ROOTS-SCORE.md")
        return 1
    rows = re.findall(r"^\|\s*(\d{1,2})\s*\|([^|]*)\|([^|]*)\|([^|]*)\|([^|]*)\|", f.read_text(), re.M)
    seen, problems = set(), []
    for n, _name, state, pointer, waiver in rows:
        n = int(n)
        seen.add(n)
        state = state.strip().upper()
        if state not in {"ROOTED", "SEEDLING", "ABSENT"}:
            problems.append(f"check {n}: state must be ROOTED, SEEDLING or ABSENT")
        elif state == "ROOTED" and not pointer.strip():
            problems.append(f"check {n}: ROOTED needs a pointer")
        elif state != "ROOTED" and n in HV and not re.search(r"20\d\d-\d\d-\d\d", waiver):
            problems.append(f"check {n}: HV check needs a dated waiver")
    missing = sorted(set(range(1, 14)) - seen)
    if missing:
        problems.append(f"unscored checks: {missing}")
    for p in problems:
        print("BLOCKED:", p)
    if problems:
        return 1
    print("CLEARED: all thirteen checks scored, waivers dated.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "."))
