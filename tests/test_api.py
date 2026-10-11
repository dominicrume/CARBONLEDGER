import time

import pytest
from fastapi.testclient import TestClient
from carbonledger.auth import ApiKeyStore
from carbonledger.chain import ChainError, DryRunChain
from carbonledger_api.main import DEMO_BATCH, DEMO_ISSUED_G, create_app
from carbonledger_api.state import Limits

CLOCK = {"t": 1_800_000_000}
PEPPER = "test-pepper-" + "0" * 24


class Client(TestClient):
    """A test client that carries a key. `as_(role, owner)` issues another key and returns a client for it."""
    def __init__(self, app, keys, role="personal", owner="p1"):
        super().__init__(app)
        self.keys = keys
        self.key, self.rec = keys.issue(role, owner)
        self.headers["authorization"] = f"Bearer {self.key}"

    def as_(self, role, owner):
        return Client(self.app, self.keys, role, owner)

    def anon(self):
        c = TestClient(self.app)
        return c


def make(chain=None, role="personal", owner="p1", limits=None, **kw):
    keys = ApiKeyStore(PEPPER)
    return Client(create_app(chain or DryRunChain(), now=lambda: CLOCK["t"], keys=keys, limits=limits or Limits(), **kw), keys, role, owner)


def body(**kw):
    b = {"account": "personal", "grams": 1200, "kind": "shop", "label": "Shopping basket",
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
    assert a["signature"].startswith("dryrun-") and "Simulated" in a["units_status"] and a["anchor_status"] == "anchored"
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


class Down:
    cluster = "down"
    def health(self):
        return False
    def record(self, rid, h):
        raise ChainError("down")
    def confirm(self, rec):
        raise ChainError("down")


class HealthyButDropping(DryRunChain):
    """Says it is up, accepts the submission, never confirms it. The outbox must show the truth."""
    def confirm(self, rec):
        raise ChainError("blockhash expired before the transaction was confirmed")


class FlakyThenFine(DryRunChain):
    """Fails the first two submissions, then works. The worker must retry and end anchored."""
    def __init__(self):
        self.calls = 0
    def record(self, rid, h):
        self.calls += 1
        if self.calls <= 2:
            raise ChainError("transient")
        return super().record(rid, h)


def test_a_chain_that_is_down_records_nothing():
    c = make(Down())
    r = c.post("/v1/retire", json=body())
    assert r.status_code == 502 and "Nothing was recorded" in r.json()["detail"]
    assert c.get("/v1/registry/summary").json()["retired_g"] == 0
    assert c.get("/v1/audit/verify").json()["count"] == 0


def test_nothing_claims_recorded_on_solana_until_confirmed():
    c = make(HealthyButDropping())
    r = c.post("/v1/retire", json=body()).json()
    assert r["anchor_status"] == "failed" and r["attempts"] == 5 and "expired" in r["error"]
    got = c.get(f"/v1/receipts/{r['receipt_id']}").json()
    assert got["chain"]["anchor_status"] == "failed"
    assert c.get("/health").json()["anchors"] == {"pending": 0, "anchored": 0, "failed": 1}
    assert c.get("/v1/audit/verify").json()["intact"]         # the receipt itself is intact and visible as unanchored


def test_a_dropped_submission_is_retried_until_anchored():
    c = make(FlakyThenFine())
    r = c.post("/v1/retire", json=body()).json()
    assert r["anchor_status"] == "anchored" and r["attempts"] == 3 and r["signature"].startswith("dryrun-") and r["slot"] == 0


def test_the_response_does_not_wait_forever_for_an_anchor():
    class Slow(DryRunChain):
        def confirm(self, rec):
            time.sleep(0.5)
            return super().confirm(rec)
    c = make(Slow(), anchor_wait_s=0.05)
    r = c.post("/v1/retire", json=body()).json()
    assert r["anchor_status"] == "pending" and r["slot"] is None     # submitted, not yet confirmed: no slot, no claim
    time.sleep(0.8)
    assert c.get(f"/v1/receipts/{r['receipt_id']}").json()["chain"]["anchor_status"] == "anchored"


@pytest.mark.parametrize("bad", [
    {"grams": "1200"}, {"grams": 0}, {"grams": -5}, {"grams": 10**13}, {"grams": 1.5}, {"extra": "x"},
    {"target_iso3": "gb"}, {"idempotency_key": "short"}, {"idempotency_key": "has space!!"}, {"account": "admin"}, {"label": "x" * 500},
    {"label": "Alice's weekly shop at 12 Acacia Avenue"}, {"kind": "anything"}, {"note": "n" * 121},
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
    c = make()
    app = c.app
    for i in range(3):
        c.post("/v1/retire", json=body(idempotency_key=f"key-000000{i}"))
    v = c.get("/v1/audit/verify").json()
    assert v["intact"] and v["count"] == 3
    app.state.st.receipts._entries[1]["receipt"]["grams"] = 1      # an insider edits history
    v = c.get("/v1/audit/verify").json()
    assert not v["intact"] and v["first_bad_index"] == 1


def test_receipt_ids_are_not_sequential_and_come_from_content():
    c = make()
    a = c.post("/v1/retire", json=body()).json()
    b = c.post("/v1/retire", json=body(idempotency_key="key-0000002")).json()
    import re
    assert re.fullmatch(r"CL-[0-9A-F]{12}", a["receipt_id"]) and re.fullmatch(r"CL-[0-9A-F]{12}", b["receipt_id"])
    assert a["receipt_id"] != b["receipt_id"]
    assert not any(a["receipt_id"].endswith(s) for s in ("0001", "0000001"))   # no counter leaks into the public id
    entry = c.get(f"/v1/receipts/{a['receipt_id']}").json()["entry"]
    from carbonledger_api.main import public_receipt_id
    assert public_receipt_id({k: v for k, v in entry["receipt"].items() if k != "receipt_id"}) == a["receipt_id"]


def test_receipts_can_be_looked_up():
    c = make()
    r = c.post("/v1/retire", json=body()).json()
    got = c.get(f"/v1/receipts/{r['receipt_id']}").json()
    assert got["entry"]["hash"] == r["receipt_hash"] and got["chain"]["signature"] == r["signature"]
    assert c.get("/v1/receipts/CL-99999999").status_code == 404


def test_mandate_caps_expiry_revocation_and_agent():
    c = make(role="business", owner="acme")
    mid = c.post("/v1/mandates", json={"agent": "agent-1", "cap_g": 1000, "ttl_seconds": 3600}).json()["mandate_id"]
    ok = c.post("/v1/retire", json=body(grams=600, idempotency_key="key-1000001", mandate_id=mid, agent="agent-1", account="business"))
    assert ok.status_code == 200
    over = c.post("/v1/retire", json=body(grams=401, idempotency_key="key-1000002", mandate_id=mid, agent="agent-1", account="business"))
    assert over.status_code == 403 and "OVER_CAP" in over.json()["detail"]
    wrong = c.post("/v1/retire", json=body(grams=1, idempotency_key="key-1000003", mandate_id=mid, agent="agent-2", account="business"))
    assert wrong.status_code == 403 and "WRONG_AGENT" in wrong.json()["detail"]
    assert c.as_("business", "mallory").post(f"/v1/mandates/{mid}/revoke").status_code == 403
    assert c.post(f"/v1/mandates/{mid}/revoke").status_code == 200
    gone = c.post("/v1/retire", json=body(grams=1, idempotency_key="key-1000004", mandate_id=mid, agent="agent-1", account="business"))
    assert gone.status_code == 403 and "REVOKED" in gone.json()["detail"]
    assert c.get("/v1/registry/summary").json()["retired_g"] == 600       # the refused ones changed nothing
    CLOCK["t"] += 10_000
    mid2 = c.post("/v1/mandates", json={"agent": "agent-1", "cap_g": 10, "ttl_seconds": 5}).json()["mandate_id"]
    CLOCK["t"] += 6
    late = c.post("/v1/retire", json=body(grams=1, idempotency_key="key-1000005", mandate_id=mid2, agent="agent-1", account="business"))
    assert late.status_code == 403 and "EXPIRED" in late.json()["detail"]


def test_a_mandate_needs_a_named_agent():
    c = make(role="business", owner="acme")
    mid = c.post("/v1/mandates", json={"agent": "agent-1", "cap_g": 1000, "ttl_seconds": 3600}).json()["mandate_id"]
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


# ---- login and limits (D2, T12) ----
def test_every_write_needs_a_key_and_reads_stay_public():
    c = make()
    a = c.anon()
    r = a.post("/v1/retire", json=body())
    assert r.status_code == 401 and "NO_KEY" in r.json()["detail"] and "Nothing was recorded" in r.json()["detail"]
    assert a.post("/v1/mandates", json={"agent": "x", "cap_g": 1, "ttl_seconds": 1}).status_code == 401
    assert a.get("/health").status_code == 200 and a.get("/v1/audit/verify").status_code == 200
    assert c.get("/v1/registry/summary").json()["retired_g"] == 0


def test_wrong_and_revoked_keys_are_refused_by_name():
    c = make()
    bad = c.anon(); bad.headers["authorization"] = "Bearer clk_personal_" + "f" * 48
    assert "BAD_KEY" in bad.post("/v1/retire", json=body()).json()["detail"]
    c.keys.revoke(c.rec.key_id)
    r = c.post("/v1/retire", json=body())
    assert r.status_code == 401 and "REVOKED_KEY" in r.json()["detail"]


def test_a_personal_key_cannot_write_a_mandate_or_retire_for_a_business():
    c = make()
    assert c.post("/v1/mandates", json={"agent": "x", "cap_g": 1, "ttl_seconds": 1}).status_code == 403
    assert c.post("/v1/retire", json=body(account="business")).status_code == 403


def test_rate_limit_is_per_key_and_says_so():
    c = make(limits=Limits(rate_per_minute=60, burst=2))
    assert c.post("/v1/retire", json=body(idempotency_key="key-0000001")).status_code == 200
    assert c.post("/v1/retire", json=body(idempotency_key="key-0000002")).status_code == 200
    r = c.post("/v1/retire", json=body(idempotency_key="key-0000003"))
    assert r.status_code == 429 and r.headers["retry-after"] == "60" and "Nothing was recorded" in r.json()["detail"]
    assert c.as_("personal", "p2").post("/v1/retire", json=body(idempotency_key="key-0000004")).status_code == 200
    assert c.get("/v1/registry/summary").json()["retirements"] == 3


def test_oversized_requests_are_refused_before_parsing():
    c = make(limits=Limits(max_request_bytes=200))
    r = c.post("/v1/retire", json=body(label="x" * 100))
    assert r.status_code == 413 and "Nothing was recorded" in r.json()["detail"]


def test_a_slow_request_answers_504_with_an_unconfirmed_outcome():
    class Slow(DryRunChain):
        def health(self):
            time.sleep(0.3); return True
    c = make(Slow(), limits=Limits(request_timeout_s=0.05))
    r = c.post("/v1/retire", json=body())
    assert r.status_code == 504 and "unconfirmed" in r.json()["detail"]


def test_free_text_goes_in_the_note_and_only_its_hash_is_kept():
    c = make()
    r = c.post("/v1/retire", json=body(label="Journey", kind="travel", note="Heathrow to Barcelona, Alice and Bob")).json()
    e = c.get(f"/v1/receipts/{r['receipt_id']}").json()["entry"]
    assert e["receipt"]["label"] == "Journey" and e["receipt"]["note_digest"] and "note" not in e["receipt"]
    assert "Heathrow" not in c.get(f"/v1/receipts/{r['receipt_id']}").text
    plain = c.post("/v1/retire", json=body(idempotency_key="key-0000002")).json()
    assert c.get(f"/v1/receipts/{plain['receipt_id']}").json()["entry"]["receipt"]["note_digest"] is None
