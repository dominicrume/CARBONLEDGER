"""People and metrics on Postgres (db/migrations/0004_people_metrics.sql): counts hold no identity, a sign-in link
works once and expires, an account gathers its logins, and delete-my-data removes the person while the ledger stays.
Needs DATABASE_URL_TEST; skipped otherwise."""
import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

URL = os.environ.get("DATABASE_URL_TEST", "")
pytestmark = pytest.mark.skipif(not URL, reason="DATABASE_URL_TEST not set")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))


@pytest.fixture(scope="module", autouse=True)
def fresh_db():
    from migrate import migrate
    migrate(URL, reset=True)


def test_counts_links_accounts_profiles_and_deletion():
    import psycopg
    from carbonledger_api.people import PostgresPeople
    p = PostgresPeople(URL)
    p.count_event("2026-10-14", "app_open"); p.count_event("2026-10-14", "app_open"); p.count_event("2026-10-13", "site_view")
    assert p.event_counts("2026-10-14") == {"2026-10-14": {"app_open": 2}}
    with psycopg.connect(URL) as c:
        cols = [r[0] for r in c.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'event_counts'")]
    assert sorted(cols) == ["day", "n", "name"]                            # nothing about who

    p.put_link("a" * 64, "rume@example.com", 2_000_000_000)
    assert p.take_link("a" * 64, 1_900_000_000) == "rume@example.com"
    assert p.take_link("a" * 64, 1_900_000_000) is None                   # once only
    p.put_link("b" * 64, "rume@example.com", 1_000)
    assert p.take_link("b" * 64, 2_000) is None                            # expired

    aid = p.account_for_email("rume@example.com")
    assert p.account_for_email("rume@example.com") == aid
    p.link_owner("demo-personal-1234abcd", aid)
    assert p.owners_of(aid) == {aid, "demo-personal-1234abcd"} and p.account_of("demo-personal-1234abcd") == aid
    p.put_profile(aid, {"display_name": "Rume"}); p.put_profile(aid, {"business_name": "Ledger Labs"})
    assert p.get_profile(aid) == {"display_name": "Rume", "business_name": "Ledger Labs"} and p.all_display_names() == {aid: "Rume"}

    with pytest.raises(psycopg.errors.CheckViolation):
        with psycopg.connect(URL) as c:
            c.execute("INSERT INTO accounts (id, email) VALUES ('acct-000000000000', 'Upper@Example.com')")

    p.delete(p.owners_of(aid), aid)
    assert p.email_of(aid) is None and p.account_of("demo-personal-1234abcd") is None and p.get_profile(aid) == {}


def test_sign_in_and_delete_through_the_api_on_postgres():
    from carbonledger.auth import ApiKeyStore
    from carbonledger.chain import DryRunChain
    from carbonledger_api.main import create_app
    from carbonledger_api.people import PostgresPeople
    from carbonledger_api.state import Limits
    from carbonledger_api.store import PostgresStore
    sent = []
    keys = ApiKeyStore("people-test-pepper-" + "0" * 16)
    app = create_app(DryRunChain(), now=lambda: 1_800_000_000, keys=keys, limits=Limits(), product_lookup=lambda c: None,
                     store=PostgresStore(URL), anchor_interval_s=0.0, people=PostgresPeople(URL), mailer=lambda to, link: sent.append(link))
    c = TestClient(app)
    assert c.post("/v1/auth/email", json={"email": "db@example.com"}).status_code == 202
    r = c.post("/v1/auth/verify", json={"token": sent[0].split("t=")[1]})
    assert r.status_code == 200
    c.headers["authorization"] = f"Bearer {r.json()['api_key']}"
    assert c.put("/v1/accounts/me/profile", json={"display_name": "Db Person"}).json()["public_name"] == "Db Person"
    assert c.delete("/v1/accounts/me").status_code == 200
    assert c.get("/v1/accounts/me/profile").status_code == 401             # the login is switched off, in the database too
    with __import__("psycopg").connect(URL) as conn:
        assert conn.execute("SELECT count(*) FROM accounts WHERE email = 'db@example.com'").fetchone()[0] == 0
        assert conn.execute("SELECT bool_and(revoked) FROM api_keys WHERE owner LIKE 'acct-%'").fetchone()[0] is True
