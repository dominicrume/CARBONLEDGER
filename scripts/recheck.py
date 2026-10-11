#!/usr/bin/env python3
"""Nightly recheck (security stage 01). Re-runs every registry invariant on the stored rows, verifies the receipt
chain, and checks that every anchored receipt's stored hash equals the hash that was anchored. Exit 0 when all hold.
Exit 1 and print the first bad index otherwise. Needs DATABASE_URL. Without one, asks a running API instead."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "packages", "core"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "services", "api"))


def recheck_db(url: str) -> int:
    from carbonledger.receipts import verify
    from carbonledger.registry import Batch, Project, Registry, Retirement
    from carbonledger_api.store import PostgresStore
    s = PostgresStore(url).load()
    if s is None:
        print("recheck: empty database, nothing to check")
        return 0
    r = Registry("trustee", {"verifier-1"}, {row[0]: Project(*row) for row in s["projects"]}, {row[0]: Batch(*row) for row in s["batches"]},
                 set(), [Retirement(*row) for row in s["retirements"]])
    try:
        r.check_invariants()
    except AssertionError as exc:
        print(f"recheck: REGISTRY INVARIANT BROKEN: {exc}")
        return 1
    bad = verify(s["receipts"])
    if bad is not None:
        print(f"recheck: RECEIPT CHAIN BROKEN at index {bad}")
        return 1
    by_id = {e["receipt"]["receipt_id"]: e for e in s["receipts"]}
    for row in s["outbox"]:
        rid, anchored_hash, status = row[0], row[1], row[2]
        e = by_id.get(rid)
        if e is None:
            print(f"recheck: OUTBOX ROW WITHOUT RECEIPT {rid}")
            return 1
        if status == "anchored" and e["hash"] != anchored_hash:
            print(f"recheck: ANCHORED HASH DISAGREES at index {e['index']} ({rid})")
            return 1
    counts = {}
    for row in s["outbox"]:
        counts[row[2]] = counts.get(row[2], 0) + 1
    print(f"recheck: ok. {len(s['receipts'])} receipts, {len(s['retirements'])} retirements, anchors {counts}, head {s['receipts'][-1]['hash'][:16] if s['receipts'] else 'genesis'}")
    if counts.get("failed"):
        print(f"recheck: WARNING {counts['failed']} failed anchor(s) need attention")
        return 2
    return 0


def recheck_api(base: str) -> int:
    import httpx
    v = httpx.get(f"{base}/v1/audit/verify", timeout=10).json()
    print("recheck (api):", v)
    return 0 if v["intact"] and not v["anchors"].get("failed") else 1


if __name__ == "__main__":
    url = os.environ.get("DATABASE_URL")
    sys.exit(recheck_db(url) if url else recheck_api(os.environ.get("API_URL", "http://127.0.0.1:8000")))
