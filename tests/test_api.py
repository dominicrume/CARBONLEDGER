import pytest
from fastapi.testclient import TestClient
from carbonledger.chain import ChainError, DryRunChain
from carbonledger_api.main import DEMO_BATCH, DEMO_ISSUED_G, create_app

CLOCK = {"t": 1_800_000_000}


def make(chain=None, **kw):
    return TestClient(create_app(chain or DryRunChain(), now=lambda: CLOCK["t"], **kw))


def body(**kw):
    b = {"account": "personal", "grams": 1200, "kind": "shop", "label": "Basket",
         "target_iso3": "GBR", "idempotency_key": "key-0000001"}
    b.update(kw)
    b.setdefault("lines", [{"name": "Beef", "grams": b["grams"]}] if isinstance(b["grams"], int) else [])
    return b


def test_health_headers_and_docs_off():
    c = make()
    r = c.get("/health")
    assert r.status_code == 200 and "Simulated" in r.json()["units"]
    assert r.headers["x-content-type-options"] == "nosniff" and r.headers["cache-control"] == "no-store"
    assert c.get("/docs").status_code == 404 and c.get("/openapi.json").status_code == 404


def test_retire_gives_a_receipt_with_a_fresh_serial_range():
    c = make()
    a = c.post("/v1/retire", json=body()).json()
    b = c.post("/v1/retire", json=body(idempotency_key="key-0000002", grams=500)).json()
    assert (a["serial_start"], a["serial_end"]) == (0, 1200)
    assert (b["serial_start"], b["serial_end"]) == (1200, 1700)         # a gram is never retired twice
    assert a["signature"].startswith("dryrun-") and "Simulated" in a["units_status"]
    s = c.get("/v1/registry/summary").json()
    assert s["retired_g"] == 1700 and s["remaining_g"] == DEMO_ISSUED_G - 1700


def test_replaying_a_request_does_not_retire_twice():
    c = make()
    first = c.post("/v1/retire", json=body()).json()
    again = c.post("/v1/retire", json=body()).json()
    assert first == again and c.get("/v1/registry/summary").json()["retired_g"] == 1200


def test_same_key_with_a_different_request_is_refused():
    c = make()
    c.post("/v1/retire", json=body())
    assert c.post("/v1/retire", json=body(grams=999)).status_code == 409


def test_cannot_retire_more_than_exists():
    c = make()
    r = c.post("/v1/retire", json=body(grams=DEMO_ISSUED_G + 1))
    assert r.status_code == 409 and "Not enough" in r.json()["detail"]
    assert c.get("/v1/registry/summary").json()["retired_g"] == 0


def test_a_failed_chain_write_leaves_nothing_behind():
    class Down:
        cluster = "down"
        def record(self, rid, h):
            raise ChainError("down")
    c = make(Down())
    r = c.post("/v1/retire", json=body())
    assert r.status_code == 502 and "Nothing was recorded" in r.json()["detail"]
    assert c.get("/v1/registry/summary").json()["retired_g"] == 0
    assert c.get("/v1/audit/verify").json()["count"] == 0


@pytest.mark.parametrize("bad", [
    {"grams": "1200"}, {"grams": 0}, {"grams": -5}, {"grams": 10**13}, {"grams": 1.5}, {"extra": "x"},
    {"target_iso3": "gb"}, {"idempotency_key": "short"}, {"idempotency_key": "has space!!"}, {"account": "admin"}, {"label": "x" * 500},
])
def test_hostile_input_is_rejected_loudly(bad):
    assert make().post("/v1/retire", json=body(**bad)).status_code == 422


@pytest.mark.parametrize("lines,grams", [([{"name": "Beef", "grams": 1199}], 1200), ([{"name": "a", "grams": 700}, {"name": "b", "grams": 700}], 1200)])
def test_lines_that_do_not_add_up_are_refused(lines, grams):
    c = make()
    r = c.post("/v1/retire", json=body(lines=lines, grams=grams))
    assert r.status_code == 422 and "add up" in r.text
    assert c.get("/v1/registry/summary").json()["retired_g"] == 0


def test_lines_that_add_up_or_no_lines_are_accepted():
    c = make()
    assert c.post("/v1/retire", json=body(lines=[{"name": "a", "grams": 500}, {"name": "b", "grams": 700}])).status_code == 200
    assert c.post("/v1/retire", json=body(lines=[], idempotency_key="key-0000009")).status_code == 200


def test_audit_chain_is_intact_then_detects_tampering():
    app = create_app(DryRunChain(), now=lambda: CLOCK["t"])
    c = TestClient(app)
    for i in range(3):
        c.post("/v1/retire", json=body(idempotency_key=f"key-000000{i}"))
    v = c.get("/v1/audit/verify").json()
    assert v["intact"] and v["count"] == 3
    app.state.st.receipts._entries[1]["receipt"]["grams"] = 1      # an insider edits history
    v = c.get("/v1/audit/verify").json()
    assert not v["intact"] and v["first_bad_index"] == 1


def test_receipts_can_be_looked_up():
    c = make()
    r = c.post("/v1/retire", json=body()).json()
    got = c.get(f"/v1/receipts/{r['receipt_id']}").json()
    assert got["entry"]["hash"] == r["receipt_hash"] and got["chain"]["signature"] == r["signature"]
    assert c.get("/v1/receipts/CL-99999999").status_code == 404


def test_mandate_caps_expiry_revocation_and_agent():
    c = make()
    mid = c.post("/v1/mandates", json={"owner": "acme", "agent": "agent-1", "cap_g": 1000, "ttl_seconds": 3600}).json()["mandate_id"]
    ok = c.post("/v1/retire", json=body(grams=600, idempotency_key="key-1000001", mandate_id=mid, agent="agent-1", account="business"))
    assert ok.status_code == 200
    over = c.post("/v1/retire", json=body(grams=401, idempotency_key="key-1000002", mandate_id=mid, agent="agent-1", account="business"))
    assert over.status_code == 403 and "OVER_CAP" in over.json()["detail"]
    wrong = c.post("/v1/retire", json=body(grams=1, idempotency_key="key-1000003", mandate_id=mid, agent="agent-2", account="business"))
    assert wrong.status_code == 403 and "WRONG_AGENT" in wrong.json()["detail"]
    assert c.post(f"/v1/mandates/{mid}/revoke", json={"owner": "mallory"}).status_code == 403
    assert c.post(f"/v1/mandates/{mid}/revoke", json={"owner": "acme"}).status_code == 200
    gone = c.post("/v1/retire", json=body(grams=1, idempotency_key="key-1000004", mandate_id=mid, agent="agent-1", account="business"))
    assert gone.status_code == 403 and "REVOKED" in gone.json()["detail"]
    assert c.get("/v1/registry/summary").json()["retired_g"] == 600       # the refused ones changed nothing
    CLOCK["t"] += 10_000
    mid2 = c.post("/v1/mandates", json={"owner": "acme", "agent": "agent-1", "cap_g": 10, "ttl_seconds": 5}).json()["mandate_id"]
    CLOCK["t"] += 6
    late = c.post("/v1/retire", json=body(grams=1, idempotency_key="key-1000005", mandate_id=mid2, agent="agent-1", account="business"))
    assert late.status_code == 403 and "EXPIRED" in late.json()["detail"]


def test_a_mandate_needs_a_named_agent():
    c = make()
    mid = c.post("/v1/mandates", json={"owner": "acme", "agent": "agent-1", "cap_g": 1000, "ttl_seconds": 3600}).json()["mandate_id"]
    assert c.post("/v1/retire", json=body(mandate_id=mid)).status_code == 422
    assert c.post("/v1/retire", json=body(mandate_id="mnd-nope", agent="a")).status_code == 404


def test_cors_is_closed_unless_an_origin_is_named():
    closed = make().options("/v1/retire", headers={"origin": "https://evil.example", "access-control-request-method": "POST"})
    assert "access-control-allow-origin" not in closed.headers
    opened = make(web_origin="http://127.0.0.1:8080")
    ok = opened.options("/v1/retire", headers={"origin": "http://127.0.0.1:8080", "access-control-request-method": "POST"})
    assert ok.headers.get("access-control-allow-origin") == "http://127.0.0.1:8080"
    bad = opened.options("/v1/retire", headers={"origin": "https://evil.example", "access-control-request-method": "POST"})
    assert "access-control-allow-origin" not in bad.headers
