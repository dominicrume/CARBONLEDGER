"""Growth around the ledger (carbonledger_api/growth.py): privacy-first counts, email sign-in that keeps earlier
progress, profiles with a name filter, delete-my-data, the business statement, and leagues ranked by XP, not grams."""
import csv
import io

from carbonledger_api.state import Limits
from test_api import CLOCK, body, make


def demo_limits():
    return Limits(demo_keys=True, demo_keys_per_hour=100)


def retire(c, n, **kw):
    r = c.post("/v1/retire", json=body(idempotency_key=f"key-{n:07d}", **kw))
    assert r.status_code == 200, r.text
    return r.json()["receipt_id"]


def with_mailer(**kw):
    sent = []
    c = make(mailer=lambda to, link: sent.append((to, link)), **kw)
    return c, sent


# ---------------- A: counts ----------------
def test_events_are_counts_only_and_unknown_names_are_dropped(monkeypatch):
    c = make()
    for name in ["app_open", "app_open", "site_view", "not_an_event", "x" * 30]:
        assert c.post("/v1/events", json={"name": name}).status_code in (204, 422)
    people = c.app.state.st.people
    assert set(people.events.values()) == {1, 2} and {k[1] for k in people.events} == {"app_open", "site_view"}
    assert all(len(k) == 2 for k in people.events)                         # (day, name): nothing about who
    assert c.anon().get("/v1/metrics").status_code == 404                    # no token configured: not even a hint
    monkeypatch.setenv("METRICS_TOKEN", "operator-only-token-123")
    assert c.anon().get("/v1/metrics", headers={"authorization": "Bearer wrong"}).status_code == 404
    retire(c, 1)
    m = c.anon().get("/v1/metrics", headers={"authorization": "Bearer operator-only-token-123"}).json()
    assert m["funnel"]["app_open"] == 2 and m["funnel"]["site_view"] == 1 and m["retirements"] == 1 and m["players"] == 1
    assert all(len(d) == 10 and d[4] == "-" for d in m["days"]), m["days"]          # every row is a date
    assert m["funnel"]["new_players"] == 1 and sum(r.get("new_players", 0) for r in m["days"].values()) == 1


# ---------------- B: sign-in, profile, delete ----------------
def test_sign_in_is_off_without_an_email_provider_and_stores_nothing():
    c = make(mailer=None)
    r = c.anon().post("/v1/auth/email", json={"email": "a@example.com"})
    assert r.status_code == 503 and "not set up" in r.json()["detail"]
    assert c.app.state.st.people.links == {}


def test_signing_in_keeps_the_progress_of_the_login_played_with_before():
    c, sent = with_mailer(limits=demo_limits())
    retire(c, 1, grams=500)                                                  # anonymous play first
    assert c.anon().post("/v1/auth/email", json={"email": "Rume@Example.com"}).status_code == 202
    to, link = sent[0]
    assert to == "rume@example.com" and "/app#signin?t=" in link
    token = link.split("t=")[1]
    r = c.post("/v1/auth/verify", json={"token": token})                     # from the same browser: its login joins
    assert r.status_code == 200 and r.json()["owner"].startswith("acct-")
    assert c.post("/v1/auth/verify", json={"token": token}).status_code == 401   # once only
    phone = c.anon()
    phone.headers["authorization"] = f"Bearer {r.json()['api_key']}"
    h = phone.get("/v1/accounts/me/history").json()["records"]
    assert [x["grams"] for x in h] == [500]                                  # the earlier progress, on a second device
    c.anon().post("/v1/auth/email", json={"email": "rume@example.com"})
    CLOCK["t"] += 16 * 60                                                    # a link lasts 15 minutes
    assert c.anon().post("/v1/auth/verify", json={"token": sent[1][1].split("t=")[1]}).status_code == 401   # expired


def test_profile_names_are_filtered_and_a_pseudonym_is_the_default():
    c = make()
    p = c.get("/v1/accounts/me/profile").json()
    assert p["public_name"].startswith("Player ") and p["signed_in"] is False
    assert c.put("/v1/accounts/me/profile", json={"display_name": "CarbonLedger Official"}).status_code == 422
    assert c.put("/v1/accounts/me/profile", json={"display_name": "<script>"}).status_code == 422
    r = c.put("/v1/accounts/me/profile", json={"display_name": "  Amara  O'Neil ", "business_name": "Leeds Bakery", "employees": 12})
    assert r.status_code == 200 and r.json()["public_name"] == "Amara O'Neil" and r.json()["employees"] == 12


def test_delete_my_data_removes_the_person_and_switches_off_every_login():
    c, sent = with_mailer(limits=demo_limits())
    retire(c, 1)
    c.anon().post("/v1/auth/email", json={"email": "gone@example.com"})
    key = c.post("/v1/auth/verify", json={"token": sent[0][1].split("t=")[1]}).json()["api_key"]
    c.put("/v1/accounts/me/profile", json={"display_name": "Soon Gone"})
    r = c.delete("/v1/accounts/me")
    assert r.status_code == 200 and "Receipts stay" in r.json()["note"]
    people = c.app.state.st.people
    assert people.accounts == {} and people.profiles == {} and people.links == {}
    assert c.get("/v1/accounts/me/history").status_code == 401
    other = c.anon(); other.headers["authorization"] = f"Bearer {key}"
    assert other.get("/v1/accounts/me/history").status_code == 401
    assert c.anon().get("/v1/audit/verify").json()["intact"] is True         # the ledger itself is untouched


# ---------------- C: statement ----------------
def test_business_statement_lists_each_retirement_with_its_proof():
    c = make(role="business", owner="acme")
    c.put("/v1/accounts/me/profile", json={"business_name": "Acme Foods"})
    ids = [retire(c, i, account="business", grams=g) for i, g in [(1, 1200), (2, 800)]]
    retire(c, 3, account="personal", grams=50)
    r = c.get("/v1/accounts/me/statement")
    assert r.status_code == 200 and r.headers["content-type"].startswith("text/csv") and "attachment" in r.headers["content-disposition"]
    lines = r.text.splitlines()
    assert lines[0].startswith("# CarbonLedger retirement statement for Acme Foods") and "not yet verified" in r.text.lower()
    rows = list(csv.DictReader(io.StringIO("\n".join(l for l in lines if not l.startswith("#")))))
    assert [x["receipt_id"] for x in rows] == ids and rows[0]["pilot_tonne"] == "1" and rows[0]["receipt_hash"]
    j = c.get("/v1/accounts/me/statement", params={"format": "json"}).json()
    assert j["total_grams"] == 2000 and j["retirements"] == 2
    assert c.get("/v1/accounts/me/statement", params={"start": "not-a-date"}).status_code == 422


# ---------------- D: league ----------------
def test_league_ranks_habits_above_one_big_footprint_and_never_shows_who():
    c = make(owner="flyer")
    retire(c, 1, grams=900_000, kind="travel", label="Journey")              # one big trip: 148 + week + kind
    careful = c.as_("personal", "careful")
    retire(careful, 2, grams=2_000)
    retire(careful, 3, grams=3_000, kind="travel", label="Journey")
    retire(careful, 4, grams=4_000, kind="daily", label="Everyday activities")
    careful.put("/v1/accounts/me/profile", json={"display_name": "Careful Cat"})
    board = careful.get("/v1/league").json()
    assert board["entries"][0]["name"] == "Careful Cat" and board["entries"][0]["you"] is True
    assert board["entries"][1]["name"].startswith("Player ") and board["entries"][1]["grams"] == 900_000
    assert board["entries"][0]["xp"] > board["entries"][1]["xp"] and "not the size" in board["ranked_by"]
    assert all("owner" not in e for e in board["entries"])
    assert c.anon().get("/v1/league").json()["players"] == 2                 # public, without anyone's key
