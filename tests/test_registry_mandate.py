"""Conformance vectors plus random attack sequences. The Anchor program must pass the same vectors."""
import json
import random
from pathlib import Path
import pytest
from carbonledger.agentsig import AgentSigError, check_timestamp, verify_agent
from carbonledger.mandate import Mandate, MandateError, authorize, consume, revoke
from carbonledger.registry import Registry, RegistryError

ROOT = Path(__file__).resolve().parents[1] / "conformance"
REG = json.loads((ROOT / "registry_vectors.json").read_text())
ALL_MAN = json.loads((ROOT / "mandate_vectors.json").read_text())
MAN = [v for v in ALL_MAN if v.get("kind") != "signature"]
SIG = [v for v in ALL_MAN if v.get("kind") == "signature"]


@pytest.mark.parametrize("v", REG, ids=[v["name"] for v in REG])
def test_registry_vector(v):
    r = Registry("auth", {"ver"})
    for step in v["steps"]:
        fn = getattr(r, step["op"])
        if step["expect"] == "ok":
            fn(*step["args"])
        else:
            with pytest.raises(RegistryError) as e:
                fn(*step["args"])
            assert e.value.code == step["expect"], step
        r.check_invariants()


@pytest.mark.parametrize("v", MAN, ids=[v["name"] for v in MAN])
def test_mandate_vector(v):
    m = Mandate(**{**v["mandate"], "allow_projects": tuple(v["mandate"]["allow_projects"]) if v["mandate"]["allow_projects"] is not None else None})
    q = v["request"]
    if v["expect"] == "ok":
        authorize(m, q["agent"], q["grams"], q["project_id"], q["now"])
    else:
        with pytest.raises(MandateError) as e:
            authorize(m, q["agent"], q["grams"], q["project_id"], q["now"])
        assert e.value.code == v["expect"]


def test_only_the_owner_revokes():
    m = Mandate("m", "acme", "agent-1", 10, 99)
    with pytest.raises(MandateError):
        revoke(m, "mallory")
    revoke(m, "acme")
    assert m.revoked


def test_random_attack_never_breaks_the_invariants():
    """Hammer the registry with 20,000 random, often hostile, calls. The rules must hold every time."""
    rnd = random.Random(2026)
    r = Registry("auth", {"ver"})
    signers = ["auth", "ver", "mallory", "alice"]
    for step in range(20_000):
        op = rnd.choice(["register", "attest", "issue", "retire", "link", "suspend"])
        pid, bid = f"p{rnd.randint(1, 3)}", f"b{rnd.randint(1, 5)}"
        n = rnd.choice([-5, 0, 1, 7, 100, 10_000, 10**12])
        try:
            if op == "register":
                r.register_project(rnd.choice(signers), pid, "GBR", "x")
            elif op == "attest":
                r.attest_project(rnd.choice(signers), pid, n)
            elif op == "issue":
                r.issue_batch(rnd.choice(signers), pid, bid, 2026, n)
            elif op == "retire":
                r.retire(rnd.choice(signers), bid, n, None, "h")
            elif op == "link":
                r.link_external(rnd.choice(signers), "RegX", f"S{rnd.randint(1, 8)}", bid)
            else:
                if rnd.random() < 0.05:
                    r.suspend_project(rnd.choice(signers), pid)
        except RegistryError:
            pass
        r.check_invariants()
    assert len(r.retirements) > 0, "the attack never got a retirement through, so the test proved little"


def _agent_gate(v):
    """The order the API uses: timestamp window, then the signature, then the mandate's agent key."""
    check_timestamp(v["request"]["agent_ts"], v["now"], v["max_age"])
    verify_agent(v["request"]["agent"], v["agent_sig"], v["request"])
    m = Mandate("m1", "acme", v["mandate_agent"], 10**9, 10**9)
    authorize(m, v["request"]["agent"], v["request"]["grams"], "p1", v["now"])


@pytest.mark.parametrize("v", SIG, ids=[v["name"] for v in SIG])
def test_agent_signature_vector(v):
    """Only public keys and signatures live in the vectors. No private key is in the repo."""
    if v["expect"] == "ok":
        _agent_gate(v)
    else:
        with pytest.raises((AgentSigError, MandateError)) as e:
            _agent_gate(v)
        assert e.value.code == v["expect"], v["name"]


def test_signature_vectors_cover_every_refusal():
    assert {v["expect"] for v in SIG} >= {"ok", "WRONG_AGENT", "BAD_SIGNATURE", "EXPIRED_SIGNATURE", "FUTURE_TIMESTAMP", "NO_SIGNATURE", "BAD_AGENT_KEY"}
