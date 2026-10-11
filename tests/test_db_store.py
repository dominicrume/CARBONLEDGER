"""The API on Postgres (D4, D9): receipts, idempotency, mandates and keys survive a restart, the database refuses
what the model refuses, and a broken stored chain stops the server. Needs DATABASE_URL_TEST; skipped otherwise."""
import os
import subprocess
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

URL = os.environ.get("DATABASE_URL_TEST", "")
pytestmark = pytest.mark.skipif(not URL, reason="DATABASE_URL_TEST not set")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
PEPPER = "store-test-pepper-" + "0" * 16


def _app(keys=None):
    from carbonledger.auth import ApiKeyStore
    from carbonledger.chain import DryRunChain
    from carbonledger_api.main import create_app
    from carbonledger_api.state import Limits
    from carbonledger_api.store import PostgresStore
    keys = keys or ApiKeyStore(PEPPER)
    app = create_app(DryRunChain(), now=lambda: 1_800_000_000, keys=keys, limits=Limits(), product_lookup=lambda c: None, store=PostgresStore(URL))
    c = TestClient(app)
    return app, c, keys


def _body(grams=1200, key="key-0000001", **kw):
    b = {"account": "personal", "grams": grams, "kind": "shop", "label": "Shopping basket", "lines": [], "target_iso3": "GBR",
         "idempotency_key": key, "items": [{"type": "products_sold", "gPerUnit": grams, "n": 1}]}
    b.update(kw)
    return b


@pytest.fixture(scope="module", autouse=True)
def fresh_db():
    from migrate import migrate
    migrate(URL, reset=True)


def test_state_survives_a_restart_and_idempotency_holds_across_it():
    app, c, keys = _app()
    key, rec = keys.issue("personal", "p1")
    app.state.st.store.insert_api_key(rec)
    c.headers["authorization"] = f"Bearer {key}"
    assert c.get("/health").json()["store"] == "postgres"
    a = c.post("/v1/retire", json=_body()).json()
    b = c.post("/v1/retire", json=_body(500, "key-0000002")).json()
    assert (b["serial_start"], b["serial_end"]) == (1200, 1700) and a["anchor_status"] == "anchored"
    # a second process on the same database
    from carbonledger.auth import ApiKeyStore
    app2, c2, _ = _app(ApiKeyStore(PEPPER))
    c2.headers["authorization"] = f"Bearer {key}"                   # the key came back from the database
    assert c2.get("/v1/registry/summary").json()["retired_g"] == 1700
    assert c2.get(f"/v1/receipts/{a['receipt_id']}").json()["chain"]["anchor_status"] == "anchored"
    assert c2.get("/v1/audit/verify").json() == c.get("/v1/audit/verify").json()
    again = c2.post("/v1/retire", json=_body()).json()
    assert again["receipt_id"] == a["receipt_id"] and c2.get("/v1/registry/summary").json()["retired_g"] == 1700
    assert c2.post("/v1/retire", json=_body(999)).status_code == 409           # same key, different request
    nxt = c2.post("/v1/retire", json=_body(10, "key-0000003")).json()
    assert (nxt["serial_start"], nxt["serial_end"]) == (1700, 1710)
    assert c2.get("/v1/accounts/me/totals").json()["personal"]["grams"] == 1710


def test_mandates_and_revocation_persist():
    from solders.keypair import Keypair
    from carbonledger.auth import ApiKeyStore
    app, c, keys = _app()
    key, rec = keys.issue("business", "acme"); app.state.st.store.insert_api_key(rec); c.headers["authorization"] = f"Bearer {key}"
    agent = Keypair()
    mid = c.post("/v1/mandates", json={"agent": str(agent.pubkey()), "cap_g": 1000, "ttl_seconds": 3600}).json()["mandate_id"]
    c.post(f"/v1/mandates/{mid}/revoke")
    _, c2, _ = _app(ApiKeyStore(PEPPER)); c2.headers["authorization"] = f"Bearer {key}"
    assert c2.app.state.st.mandates[mid].revoked and c2.app.state.st.mandates[mid].agent == str(agent.pubkey())


def test_the_database_refuses_what_the_model_refuses_and_memory_stays_clean():
    import psycopg
    app, c, keys = _app()
    key, rec = keys.issue("personal", "p9"); app.state.st.store.insert_api_key(rec); c.headers["authorization"] = f"Bearer {key}"
    before = c.get("/v1/registry/summary").json()["retired_g"]
    with psycopg.connect(URL, autocommit=True) as conn:        # an insider pre-books the next serial range directly
        conn.execute("INSERT INTO retirements (batch_id, retiree, grams, serial_start, serial_end, memo_hash) VALUES ('pilot-2026','insider',5,%s,%s,'m')", (before, before + 5))
    r = c.post("/v1/retire", json=_body(100, "key-0000009"))
    assert r.status_code == 409 and "database refused" in r.json()["detail"] and "Nothing was recorded" in r.json()["detail"]
    assert c.get("/v1/registry/summary").json()["retired_g"] == before
    assert c.get("/v1/audit/verify").json()["intact"]


def test_a_broken_stored_chain_refuses_to_start():
    import psycopg
    with psycopg.connect(URL, autocommit=True) as conn:
        conn.execute("ALTER TABLE receipts DISABLE TRIGGER receipts_append_only")          # only a superuser could; the test plays one
        conn.execute("UPDATE receipts SET receipt = receipt || '{\"grams\": 1}' WHERE idx = 0")
        conn.execute("ALTER TABLE receipts ENABLE TRIGGER receipts_append_only")
    with pytest.raises(ValueError, match="broken at index 0"):
        _app()
    env = {**os.environ, "DATABASE_URL": URL}
    out = subprocess.run([sys.executable, str(ROOT / "scripts" / "recheck.py")], env=env, capture_output=True, text=True)
    assert out.returncode == 1 and "RECEIPT CHAIN BROKEN at index 0" in out.stdout


def test_recheck_passes_on_a_clean_database():
    from migrate import migrate
    migrate(URL, reset=True)
    app, c, keys = _app()
    key, rec = keys.issue("personal", "p1"); app.state.st.store.insert_api_key(rec); c.headers["authorization"] = f"Bearer {key}"
    c.post("/v1/retire", json=_body())
    out = subprocess.run([sys.executable, str(ROOT / "scripts" / "recheck.py")], env={**os.environ, "DATABASE_URL": URL}, capture_output=True, text=True)
    assert out.returncode == 0 and "recheck: ok. 1 receipts, 1 retirements" in out.stdout, out.stdout + out.stderr
