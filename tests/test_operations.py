"""Go-live operations (2026-11-15): operator levers (D24) and the clean count of real users."""
from carbonledger.chain import ChainError
from carbonledger_api.main import DEMO_PROJECT
from test_api import body, make


class FailingChain:
    cluster = "devnet"

    def health(self):
        return True

    def record(self, receipt_id, receipt_hash):
        raise ChainError("devnet unreachable")

    def confirm(self, rec):
        return rec


def test_only_an_authority_suspends_and_a_suspended_project_retires_nothing():
    c = make()
    assert c.post(f"/v1/admin/projects/{DEMO_PROJECT}/suspend").status_code == 403          # a personal key cannot
    boss = c.as_("authority", "operator-1")
    r = boss.post(f"/v1/admin/projects/{DEMO_PROJECT}/suspend")
    assert r.status_code == 200 and r.json()["status"] == "suspended"
    refused = c.post("/v1/retire", json=body(idempotency_key="key-o000001"))
    assert refused.status_code >= 400 and "SUSPENDED" in refused.json()["detail"]
    assert boss.post("/v1/admin/projects/nope/suspend").status_code == 404


def test_only_a_failed_anchor_can_be_requeued():
    c = make(chain=FailingChain(), anchor_wait_s=3.0)
    rid = c.post("/v1/retire", json=body(idempotency_key="key-o000011")).json()["receipt_id"]
    boss = c.as_("authority", "operator-1")
    e = c.app.state.st.outbox.get(rid)
    if e.status != "failed":                       # force the failed state the worker reaches after its attempts
        c.app.state.st.outbox._set(e, status="failed")
    assert c.post(f"/v1/admin/anchors/{rid}/reanchor").status_code == 403
    r = boss.post(f"/v1/admin/anchors/{rid}/reanchor")
    assert r.status_code == 200 and r.json()["anchor_status"] in ("pending", "failed", "anchored")
    c.app.state.st.outbox._set(e, status="anchored")
    assert boss.post(f"/v1/admin/anchors/{rid}/reanchor").status_code == 409           # anchored never moves
    assert boss.post("/v1/admin/anchors/CL-NOPE/reanchor").status_code == 404


def test_the_clean_count_leaves_out_internal_logins_and_the_time_before_launch(monkeypatch):
    from test_api import CLOCK
    c = make()
    c.post("/v1/retire", json=body(idempotency_key="key-o000021"))                        # p1, before launch
    CLOCK["t"] += 86_400 * 3
    import datetime as dt
    launch = dt.datetime.fromtimestamp(CLOCK["t"], dt.timezone.utc).date().isoformat()
    c.as_("personal", "staff-7").post("/v1/retire", json=body(idempotency_key="key-o000022"))   # internal
    c.as_("personal", "visitor-1").post("/v1/retire", json=body(idempotency_key="key-o000023"))  # real
    monkeypatch.setenv("METRICS_TOKEN", "operator-only-token-123")
    monkeypatch.setenv("INTERNAL_OWNERS", "staff-7")
    monkeypatch.setenv("METRICS_SINCE", launch)
    m = c.anon().get("/v1/metrics", headers={"authorization": "Bearer operator-only-token-123"}).json()
    assert m["retirements"] == 3                                                          # the raw count is unchanged
    assert m["real"]["retirements"] == 1 and m["real"]["players"] == 1 and m["real"]["since"] == launch
