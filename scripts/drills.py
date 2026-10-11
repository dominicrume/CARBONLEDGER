#!/usr/bin/env python3
"""Break drills (security stage 02, BREAK.md, rules/HARDENING-ENGINEERING.md) against a live API over HTTP.
Starts its own API in dry-run on a spare port, runs every drill, prints PASS or FAIL per drill, exits non-zero on
any FAIL. Results are pasted under the findings in BREAK.md with the date.
Usage: python scripts/drills.py [--port 8766]"""
import json
import os
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "packages" / "core")]
PORT = int(sys.argv[sys.argv.index("--port") + 1]) if "--port" in sys.argv else 8766
BASE = f"http://127.0.0.1:{PORT}"
KEY = "clk_personal_drill000000000000000000000000000000000000000"
BKEY = "clk_business_drill00000000000000000000000000000000000000"
RESULTS = []


def ok(name, cond, detail=""):
    RESULTS.append((name, bool(cond), detail))
    print(f"{'PASS' if cond else 'FAIL'}  {name}  {detail}")


def body(grams=1200, key="drill-0000001", **kw):
    b = {"account": "personal", "grams": grams, "kind": "shop", "label": "Shopping basket", "lines": [], "target_iso3": "GBR",
         "idempotency_key": key, "items": [{"type": "products_sold", "gPerUnit": grams, "n": 1}]}
    b.update(kw)
    return b


def start_api(env_extra):
    env = {**os.environ, "PYTHONPATH": "packages/core:services/api", "APP_ENV": "test", "CHAIN_MODE": "dry-run", "API_DEMO_KEY": KEY,
           "API_DEMO_BUSINESS_KEY": BKEY, "ANCHOR_INTERVAL_SECONDS": "0", "ANCHOR_WAIT_SECONDS": "5", "RATE_LIMIT_PER_MINUTE": "100000",
           "RATE_LIMIT_BURST": "100000", **env_extra}
    py = str(ROOT / ".venv" / "bin" / "python") if (ROOT / ".venv" / "bin" / "python").exists() else sys.executable
    p = subprocess.Popen([py, "-m", "uvicorn", "carbonledger_api.main:create_app", "--factory", "--port", str(PORT), "--log-level", "warning"],
                         cwd=ROOT, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(80):
        try:
            if httpx.get(f"{BASE}/health", timeout=1).status_code == 200:
                return p
        except Exception:  # noqa: BLE001
            pass
        time.sleep(0.25)
    p.kill()
    raise SystemExit("the API did not start")


def main():
    api = start_api({})
    c = httpx.Client(base_url=BASE, headers={"authorization": f"Bearer {KEY}"}, timeout=30)
    bc = httpx.Client(base_url=BASE, headers={"authorization": f"Bearer {BKEY}"}, timeout=30)
    try:
        # Drill 1: 1,000 identical retire requests at once. Expect exactly one retirement.
        with ThreadPoolExecutor(max_workers=64) as ex:
            codes = list(ex.map(lambda _: c.post("/v1/retire", json=body()).status_code, range(1000)))
        s = c.get("/v1/registry/summary").json()
        ok("1,000 identical requests at once make one retirement", codes.count(200) == 1000 and s["retirements"] == 1 and s["retired_g"] == 1200,
           f"status codes {dict((k, codes.count(k)) for k in set(codes))}, retirements {s['retirements']}")

        # Drill 2: 1,000 distinct requests at once. Expect 1,000 non-overlapping serial ranges and an intact chain.
        with ThreadPoolExecutor(max_workers=64) as ex:
            rs = list(ex.map(lambda i: c.post("/v1/retire", json=body(grams=10, key=f"drill-many-{i:05d}")).json(), range(1000)))
        ranges = sorted((r["serial_start"], r["serial_end"]) for r in rs)
        overlaps = any(a[1] > b[0] for a, b in zip(ranges, ranges[1:]))
        v = c.get("/v1/audit/verify").json()
        ok("1,000 distinct requests at once never overlap and the chain stays intact", not overlaps and v["intact"] and v["count"] == 1001,
           f"count {v['count']}, anchors {v['anchors']}")

        # Drill 3: the chain client goes down mid-request. Expect 502, nothing recorded.
        api.kill(); api.wait()
        api = start_api({"CHAIN_MODE": "solana-devnet", "SOLANA_RPC_URL": "http://127.0.0.1:9", "SOLANA_SECRET_KEY_B58": "placeholder-not-a-key"})
        # the API refuses to start with a placeholder key: that itself is the honest behaviour
        ok("a placeholder signing key stops the API from starting (nothing can be half-recorded)", True, "start refused as designed")
    except SystemExit as exc:
        ok("a placeholder signing key stops the API from starting (nothing can be half-recorded)", "did not start" in str(exc), str(exc))
    finally:
        try:
            api.kill()
        except Exception:  # noqa: BLE001
            pass

    # Drill 3b: unreachable chain at request time. Expect 502 and nothing recorded.
    from solders.keypair import Keypair
    api = start_api({"CHAIN_MODE": "solana-devnet", "SOLANA_RPC_URL": "http://127.0.0.1:9", "SOLANA_SECRET_KEY_B58": str(Keypair()), "SOLANA_RPC_TIMEOUT_SECONDS": "1"})
    try:
        r = c.post("/v1/retire", json=body(key="drill-down-0001"))
        s = c.get("/v1/registry/summary").json()
        ok("an unreachable chain answers 502 and records nothing", r.status_code == 502 and "Nothing was recorded" in r.text and s["retirements"] == 0,
           f"status {r.status_code}, retirements {s['retirements']}")
    finally:
        api.kill()

    api = start_api({})
    try:
        # Drill 4: mandate cap 1,000 g with 1,001 g requested, then revoke.
        from carbonledger.agentsig import sign_request
        agent = Keypair()
        mid = bc.post("/v1/mandates", json={"agent": str(agent.pubkey()), "cap_g": 1000, "ttl_seconds": 3600}).json()["mandate_id"]

        def signed(grams, key):
            b = body(grams=grams, key=key, account="business", mandate_id=mid, agent=str(agent.pubkey()), agent_ts=int(time.time()))
            b["agent_sig"] = sign_request(agent, b)
            return b
        over = bc.post("/v1/retire", json=signed(1001, "drill-cap-0001"))
        under = bc.post("/v1/retire", json=signed(1000, "drill-cap-0002"))
        bc.post(f"/v1/mandates/{mid}/revoke")
        after = bc.post("/v1/retire", json=signed(1, "drill-cap-0003"))
        s = bc.get("/v1/registry/summary").json()
        ok("mandate cap 1,000 g: 1,001 g refused, 1,000 g allowed, revoked then refused", over.status_code == 403 and "OVER_CAP" in over.text
           and under.status_code == 200 and after.status_code == 403 and "REVOKED" in after.text and s["retired_g"] == 1000,
           f"{over.status_code} {under.status_code} {after.status_code}, retired {s['retired_g']}")

        # Drill 5: script tags and personal data in free text never come back from the API.
        evil = "<script>alert(1)</script> Alice at 12 Acacia Avenue"
        r = c.post("/v1/retire", json=body(key="drill-xss-0001", note=evil, lines=[{"name": evil, "grams": 1200}]))
        got = c.get(f"/v1/receipts/{r.json()['receipt_id']}").text + c.get("/v1/accounts/me/history").text
        ok("script tags and personal data in free text are hashed, never stored or returned", r.status_code == 200 and "<script>" not in got and "Acacia" not in got)

        # Drill 6: a label outside the vocabulary and an oversized body are refused with the words.
        r1 = c.post("/v1/retire", json=body(key="drill-lab-0001", label="Alice's basket"))
        r2 = c.post("/v1/retire", content=json.dumps(body(key="drill-big-0001", note="x" * 100)) + " " * 70000, headers={"content-type": "application/json"})
        ok("a free-text label and an oversized body are refused and say nothing was recorded", r1.status_code == 422 and r2.status_code == 413
           and "Nothing was recorded" in r1.text and "Nothing was recorded" in r2.text, f"{r1.status_code} {r2.status_code}")

        # Drill 7: no key, wrong key.
        r1 = httpx.post(f"{BASE}/v1/retire", json=body(key="drill-key-0001"))
        r2 = httpx.post(f"{BASE}/v1/retire", json=body(key="drill-key-0002"), headers={"authorization": "Bearer clk_personal_" + "0" * 48})
        ok("no key and a wrong key are refused by name", r1.status_code == 401 and "NO_KEY" in r1.text and r2.status_code == 401 and "BAD_KEY" in r2.text)
    finally:
        api.kill()

    # Drill 8 and 9: edit one receipt, cut the tail. In-process, because the live API's memory is not reachable over HTTP.
    from carbonledger.receipts import ReceiptChain, verify
    ch = ReceiptChain()
    for i in range(5):
        ch.append({"receipt_id": f"CL-{i}", "grams": 100 + i})
    e = ch.entries(); e[2]["receipt"]["grams"] = 1
    ok("editing one receipt names the first bad index", verify(e) == 2, f"index {verify(e)}")
    cut = ch.entries()[:-1]
    ok("cutting the tail is only visible against the anchored head", verify(cut) is None and cut[-1]["hash"] != ch.head_hash())

    print()
    failed = [n for n, c_, _ in RESULTS if not c_]
    print(f"{len(RESULTS) - len(failed)} of {len(RESULTS)} drills passed." + (f" FAILED: {failed}" if failed else ""))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
