"""Batch 1 hardening (2026-11-15): one request or one login cannot empty the pilot pool, per-address limits use the
address our proxy saw, agents retire only under a mandate, a mandate's use is written with its retirement, and the
server will not start on a silent dry run."""
import pytest
from solders.keypair import Keypair
from starlette.requests import Request

from carbonledger_api.net import client_address
from carbonledger_api.state import Limits, chain_from_env
from carbonledger_api.store import MemoryStore, StoreError
from carbonledger.chain import DryRunChain
from test_api import CLOCK, body, make, signed


def items(g):
    return [{"type": "products_sold", "gPerUnit": g, "n": 1}]


# ---- 1. a claim far above what the server computes is refused ----
def test_a_total_far_above_the_computed_amount_is_refused():
    c = make()
    ok = c.post("/v1/retire", json=body(grams=2000, items=items(1000), idempotency_key="key-h000001"))
    assert ok.status_code == 200                                     # 1,000 g computed: up to 1,000 g extra is allowed
    big = c.post("/v1/retire", json=body(grams=2001, items=items(1000), idempotency_key="key-h000002"))
    assert big.status_code == 422 and "ABOVE_COMPUTED" in big.json()["detail"] and "No units were retired" in big.json()["detail"]
    pct = c.post("/v1/retire", json=body(grams=110_001, items=items(100_000), idempotency_key="key-h000003"))
    assert pct.status_code == 422                                    # above 10 % of a large computed amount
    assert c.post("/v1/retire", json=body(grams=110_000, items=items(100_000), idempotency_key="key-h000004")).status_code == 200


def test_the_daily_limit_per_login_and_for_the_pool():
    c = make(limits=Limits(daily_key_cap_g=1500, daily_total_cap_g=2500))
    assert c.post("/v1/retire", json=body(grams=1000, idempotency_key="key-h000011")).status_code == 200
    mine = c.post("/v1/retire", json=body(grams=600, idempotency_key="key-h000012"))
    assert mine.status_code == 429 and "DAILY_LIMIT" in mine.json()["detail"]
    other = c.as_("personal", "p2")
    assert other.post("/v1/retire", json=body(grams=1400, idempotency_key="key-h000013")).status_code == 200
    pool = c.as_("personal", "p3").post("/v1/retire", json=body(grams=200, idempotency_key="key-h000014"))
    assert pool.status_code == 429 and "POOL_DAILY_LIMIT" in pool.json()["detail"]
    assert c.get("/v1/registry/summary").json()["retired_g"] == 2400  # the refused ones moved nothing
    CLOCK["t"] += 86_400                                             # a new UTC day
    assert c.post("/v1/retire", json=body(grams=600, idempotency_key="key-h000015")).status_code == 200


def test_the_environment_turns_the_ceilings_on_and_zero_turns_one_off(monkeypatch):
    for k in ("DAILY_RETIRE_CAP_PER_LOGIN_G", "DAILY_RETIRE_CAP_TOTAL_G", "TRUSTED_PROXY_HOPS"):
        monkeypatch.delenv(k, raising=False)
    lim = Limits.from_env()
    assert lim.daily_key_cap_g == 10_000_000 and lim.daily_total_cap_g == 50_000_000 and lim.trusted_proxy_hops == 1
    monkeypatch.setenv("DAILY_RETIRE_CAP_TOTAL_G", "0")
    assert Limits.from_env().daily_total_cap_g is None


# ---- 2. the client's address is the one our proxy appended, not what the client wrote ----
def _req(xff=None, host="10.0.0.1"):
    headers = [(b"x-forwarded-for", xff.encode())] if xff is not None else []
    return Request({"type": "http", "headers": headers, "client": (host, 1234)})


def test_a_forged_forwarded_for_entry_does_not_change_the_address():
    assert client_address(_req("1.1.1.1, 203.0.113.7"), 1) == "203.0.113.7"       # the client wrote 1.1.1.1
    assert client_address(_req("9.9.9.9, 8.8.8.8, 203.0.113.7"), 1) == "203.0.113.7"
    assert client_address(_req("9.9.9.9, 203.0.113.7, 10.1.1.1"), 2) == "203.0.113.7"
    assert client_address(_req(None), 1) == "10.0.0.1"
    assert client_address(_req("1.1.1.1"), 0) == "10.0.0.1"                       # 0 ignores the header


def test_demo_logins_cannot_be_multiplied_by_writing_a_new_address():
    c = make(limits=Limits(demo_keys=True, demo_keys_per_hour=1))
    a = c.anon()
    a.headers["x-forwarded-for"] = "1.1.1.1, 203.0.113.9"
    assert a.post("/v1/demo/key").status_code == 201
    a.headers["x-forwarded-for"] = "2.2.2.2, 203.0.113.9"                         # same real address, new forged prefix
    assert a.post("/v1/demo/key").status_code == 429


# ---- 3. an agent key retires only under a mandate, booked to the mandate's owner ----
def test_an_agent_key_needs_a_mandate_and_an_agent_needs_one_too():
    c = make()
    bot = c.as_("agent", "bot-1")
    r = bot.post("/v1/retire", json=body(idempotency_key="key-h000021"))
    assert r.status_code == 403 and "MANDATE_REQUIRED" in r.json()["detail"]
    r = c.post("/v1/retire", json=body(agent="someone", idempotency_key="key-h000022"))
    assert r.status_code == 422 and "under a mandate" in r.json()["detail"]
    assert c.get("/v1/registry/summary").json()["retirements"] == 0


def test_a_mandate_retirement_is_the_mandate_owners():
    agent = Keypair()
    biz = make(role="business", owner="acme")
    mid = biz.post("/v1/mandates", json={"agent": str(agent.pubkey()), "cap_g": 1000, "ttl_seconds": 3600}).json()["mandate_id"]
    bot = biz.as_("agent", "bot-7")
    r = bot.post("/v1/retire", json=signed(agent, grams=300, idempotency_key="key-h000031", mandate_id=mid, account="business"))
    assert r.status_code == 200
    rec = biz.get(f"/v1/receipts/{r.json()['receipt_id']}").json()["entry"]["receipt"]
    assert rec["owner"] == "acme" and rec["approved_by"].startswith(f"mandate {mid}")


# ---- 4. the mandate's use is written in the retirement's own transaction ----
class FailOnce(MemoryStore):
    def __init__(self):
        self.calls, self.seen = 0, []

    def write_retirement(self, entry, ret, batch, idem_key, payload_digest, mandate=None, grams=0):
        self.calls += 1
        self.seen.append((mandate.id if mandate else None, grams))
        if self.calls == 1:
            raise StoreError("the database refused the retirement: injected")


def test_a_failed_write_moves_nothing_and_the_same_request_can_be_retried():
    agent, store = Keypair(), FailOnce()
    c = make(role="business", owner="acme", store=store)
    mid = c.post("/v1/mandates", json={"agent": str(agent.pubkey()), "cap_g": 1000, "ttl_seconds": 3600}).json()["mandate_id"]
    req = signed(agent, grams=400, idempotency_key="key-h000041", mandate_id=mid, account="business")
    first = c.post("/v1/retire", json=req)
    assert first.status_code == 409 and "Nothing was recorded" in first.json()["detail"]
    st = c.app.state.st
    assert st.mandates[mid].used_g == 0 and "key-h000041" not in st.idem and st.registry.batches["pilot-2026"].retired_g == 0
    again = c.post("/v1/retire", json=req)
    assert again.status_code == 200 and st.mandates[mid].used_g == 400
    assert store.seen == [(mid, 400), (mid, 400)]                    # the mandate travels with the retirement write


# ---- 5. no silent dry run outside dev and test ----
def test_the_server_refuses_to_start_without_an_explicit_chain_mode(monkeypatch):
    monkeypatch.setenv("APP_ENV", "demo")
    monkeypatch.delenv("CHAIN_MODE", raising=False)
    with pytest.raises(RuntimeError, match="CHAIN_MODE"):
        chain_from_env()
    monkeypatch.setenv("CHAIN_MODE", "solana_devnet")                              # a typo used to mean dry run
    with pytest.raises(RuntimeError, match="CHAIN_MODE"):
        chain_from_env()
    monkeypatch.setenv("CHAIN_MODE", "dry-run")                                    # chosen on purpose: allowed
    assert isinstance(chain_from_env(), DryRunChain)
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.delenv("CHAIN_MODE")
    assert isinstance(chain_from_env(), DryRunChain)
