"""CarbonLedger API. Server holds the register, the receipt chain and the signing key. Browsers hold nothing.
Units are SIMULATED pilot units until a verifier attests real ones. The API says so in every response.
No login yet (see DEBT.md): do not expose this to the public internet before it exists."""
import copy
import os
import threading
import time
from datetime import datetime, timezone
from typing import Callable, List, Literal, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field, model_validator

from carbonledger.chain import ChainClient, ChainError, DryRunChain, SolanaMemoChain
from carbonledger.mandate import Mandate, MandateError, authorize, consume, revoke
from carbonledger.receipts import ReceiptChain, digest, verify
from carbonledger.registry import Registry, RegistryError
from carbonledger.units import grams_to_clt

UNITS_STATUS = "Simulated pilot units. Not verified credits."
DEMO_PROJECT, DEMO_BATCH = "demo-pilot-1", "pilot-2026"
DEMO_ISSUED_G = 1_000_000_000          # 1,000 tonnes, simulated (ASSUMPTION for the demo)
MAX_RETIRE_G = 10**12                  # ASSUMPTION: a request above 1,000,000 tonnes is a mistake or an attack
STATUS_FOR = {"UNAUTHORISED": 403, "OVER_RETIREMENT": 409, "OVER_ISSUANCE": 409, "SUSPENDED": 409,
              "UNKNOWN_BATCH": 404, "UNKNOWN_PROJECT": 404, "BAD_AMOUNT": 422, "DUPLICATE_LINK": 409, "EXISTS": 409, "NOT_ATTESTED": 409}


class Line(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    name: str = Field(max_length=80)
    grams: int = Field(ge=0, le=MAX_RETIRE_G)


class RetireIn(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    account: Literal["personal", "business"]
    grams: int = Field(gt=0, le=MAX_RETIRE_G)
    kind: str = Field(max_length=24)
    label: str = Field(max_length=120)
    lines: List[Line] = Field(default_factory=list, max_length=200)
    target_iso3: Optional[str] = Field(default=None, pattern=r"^[A-Z]{3}$")
    idempotency_key: str = Field(min_length=8, max_length=64, pattern=r"^[A-Za-z0-9_-]+$")
    mandate_id: Optional[str] = Field(default=None, max_length=64)
    agent: Optional[str] = Field(default=None, max_length=64)

    @model_validator(mode="after")
    def lines_add_up(self):
        # A client cannot retire less than its own lines say (first step of D1).
        if self.lines and sum(l.grams for l in self.lines) != self.grams:
            raise ValueError("the line grams do not add up to the total; nothing was recorded")
        return self


class MandateIn(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    owner: str = Field(min_length=1, max_length=64)
    agent: str = Field(min_length=1, max_length=64)
    cap_g: int = Field(gt=0, le=MAX_RETIRE_G)
    ttl_seconds: int = Field(gt=0, le=31_536_000)
    allow_projects: Optional[List[str]] = Field(default=None, max_length=50)


class RevokeIn(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    owner: str = Field(min_length=1, max_length=64)


class State:
    def __init__(self, chain: ChainClient, now: Callable[[], float] = time.time):
        self.lock = threading.Lock()
        self.chain_client, self.now = chain, now
        self.registry = Registry(authority="trustee", verifiers={"verifier-1"})
        self.receipts = ReceiptChain()
        self.onchain = {}                       # receipt_id -> chain record (outside the hashed body)
        self.idem = {}                          # key -> (payload digest, response)
        self.mandates = {}
        r = self.registry
        r.register_project("trustee", DEMO_PROJECT, "GBR", "SIMULATED-PILOT")
        r.attest_project("verifier-1", DEMO_PROJECT, DEMO_ISSUED_G)
        r.issue_batch("trustee", DEMO_PROJECT, DEMO_BATCH, 2026, DEMO_ISSUED_G)


def chain_from_env() -> ChainClient:
    if os.environ.get("CHAIN_MODE", "dry-run") == "solana-devnet":
        return SolanaMemoChain(os.environ["SOLANA_RPC_URL"], os.environ["SOLANA_SECRET_KEY_B58"], "devnet")
    return DryRunChain()


def create_app(chain: Optional[ChainClient] = None, now: Callable[[], float] = time.time, web_origin: Optional[str] = None) -> FastAPI:
    st = State(chain or chain_from_env(), now)
    dev = os.environ.get("APP_ENV") == "dev"
    app = FastAPI(title="CarbonLedger API", docs_url="/docs" if dev else None, redoc_url=None, openapi_url="/openapi.json" if dev else None)
    app.state.st = st
    origin = web_origin or os.environ.get("WEB_ORIGIN")
    if origin:
        app.add_middleware(CORSMiddleware, allow_origins=[origin], allow_methods=["GET", "POST"], allow_headers=["content-type"])

    @app.middleware("http")
    async def security_headers(request, call_next):
        resp = await call_next(request)
        resp.headers["X-Content-Type-Options"] = "nosniff"
        resp.headers["X-Frame-Options"] = "DENY"
        resp.headers["Referrer-Policy"] = "no-referrer"
        resp.headers["Cache-Control"] = "no-store"
        resp.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
        resp.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"
        return resp

    @app.get("/health")
    def health():
        return {"status": "ok", "chain": getattr(st.chain_client, "cluster", "unknown"), "units": UNITS_STATUS}

    @app.get("/v1/registry/summary")
    def summary():
        b = st.registry.batches[DEMO_BATCH]
        return {"units": UNITS_STATUS, "issued_g": b.issued_g, "retired_g": b.retired_g, "remaining_g": b.issued_g - b.retired_g,
                "retirements": len(st.registry.retirements)}

    @app.post("/v1/mandates", status_code=201)
    def create_mandate(body: MandateIn):
        with st.lock:
            mid = "mnd-" + digest({"n": len(st.mandates), "o": body.owner, "a": body.agent})[:12]
            st.mandates[mid] = Mandate(mid, body.owner, body.agent, body.cap_g, int(st.now()) + body.ttl_seconds,
                                       tuple(body.allow_projects) if body.allow_projects is not None else None)
        return {"mandate_id": mid}

    @app.post("/v1/mandates/{mandate_id}/revoke")
    def revoke_mandate(mandate_id: str, body: RevokeIn):
        with st.lock:
            m = st.mandates.get(mandate_id)
            if m is None:
                raise HTTPException(404, "No such mandate.")
            try:
                revoke(m, body.owner)
            except MandateError as exc:
                raise HTTPException(403, str(exc))
        return {"revoked": True}

    @app.post("/v1/retire")
    def retire(body: RetireIn):
        payload_digest = digest(body.model_dump(exclude={"idempotency_key"}))
        with st.lock:
            prior = st.idem.get(body.idempotency_key)
            if prior is not None:
                if prior[0] != payload_digest:
                    raise HTTPException(409, "This idempotency key was already used for a different request.")
                return prior[1]
            now = int(st.now())
            mandate = None
            if body.mandate_id is not None:
                mandate = st.mandates.get(body.mandate_id)
                if mandate is None:
                    raise HTTPException(404, "No such mandate.")
                if not body.agent:
                    raise HTTPException(422, "An agent name is required when a mandate is used.")
                try:
                    authorize(mandate, body.agent, body.grams, DEMO_PROJECT, now)
                except MandateError as exc:
                    raise HTTPException(403, f"The mandate does not allow this: {exc.code}.")
            reg = copy.deepcopy(st.registry)            # work on a copy; commit only if everything succeeds
            retiree = f"{body.account}:{body.agent or 'self'}"
            lines_digest = digest({"lines": [l.model_dump() for l in body.lines]})
            try:
                ret = reg.retire(retiree, DEMO_BATCH, body.grams, body.target_iso3, lines_digest)
            except RegistryError as exc:
                raise HTTPException(STATUS_FOR.get(exc.code, 409), "Not enough pilot units left." if exc.code == "OVER_RETIREMENT" else str(exc))
            receipt_id = f"CL-{ret.receipt_no:08d}"
            receipt = {"receipt_id": receipt_id, "ts": datetime.fromtimestamp(now, timezone.utc).isoformat(), "account": body.account,
                       "grams": body.grams, "clt": grams_to_clt(body.grams), "kind": body.kind, "label": body.label,
                       "lines_digest": lines_digest, "target_iso3": body.target_iso3, "project_id": DEMO_PROJECT, "batch_id": DEMO_BATCH,
                       "serial_start": ret.serial_start, "serial_end": ret.serial_end, "units": UNITS_STATUS}
            preview = {"index": st.receipts.next_index(), "receipt": receipt, "prev_hash": st.receipts.head_hash()}
            receipt_hash = digest(preview)
            try:
                record = st.chain_client.record(receipt_id, receipt_hash)
            except ChainError:
                raise HTTPException(502, "The chain could not be reached. Nothing was recorded.")
            entry = st.receipts.append(receipt)
            assert entry["hash"] == receipt_hash
            st.registry = reg
            st.onchain[receipt_id] = {"signature": record.signature, "explorer_url": record.explorer_url, "cluster": record.cluster}
            if mandate is not None:
                consume(mandate, body.grams)
            resp = {"receipt_id": receipt_id, "ts": receipt["ts"], "receipt_hash": receipt_hash, "serial_start": ret.serial_start,
                    "serial_end": ret.serial_end, "signature": record.signature, "explorer_url": record.explorer_url or None,
                    "cluster": record.cluster, "units_status": UNITS_STATUS}
            st.idem[body.idempotency_key] = (payload_digest, resp)
            return resp

    @app.get("/v1/receipts/{receipt_id}")
    def get_receipt(receipt_id: str):
        e = st.receipts.find(receipt_id)
        if e is None:
            raise HTTPException(404, "No such receipt.")
        return {"entry": e, "chain": st.onchain.get(receipt_id)}

    @app.get("/v1/audit/verify")
    def audit_verify():
        bad = verify(st.receipts.entries())
        return {"intact": bad is None, "first_bad_index": bad, "count": len(st.receipts.entries()), "head_hash": st.receipts.head_hash()}

    return app


app = create_app() if os.environ.get("CARBONLEDGER_AUTOSTART") else None
