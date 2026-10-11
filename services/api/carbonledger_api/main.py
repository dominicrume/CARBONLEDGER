"""CarbonLedger API. Server holds the register, the receipt chain and the signing key. Browsers hold nothing.
Units are SIMULATED pilot units until a verifier attests real ones. The API says so in every response.
No login yet (see DEBT.md): do not expose this to the public internet before it exists.

The retire flow (rule 6 as refined on 2026-10-11):
  1. Check the request, the mandate, and that the chain is reachable. If it is not, nothing is recorded.
  2. Under the lock: retire on a copy of the register, append the receipt, commit, enqueue the anchor.
  3. Outside the lock: the anchor worker submits and confirms. The response waits up to ANCHOR_WAIT_SECONDS for it.
  4. Nothing is called "recorded on Solana" until the chain confirmed it. A failed anchor is shown as failed."""
import copy
import os
import time
from datetime import datetime, timezone
from typing import Callable, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from carbonledger.chain import ChainClient
from carbonledger.mandate import Mandate, MandateError, authorize, consume, revoke
from carbonledger.receipts import digest, verify
from carbonledger.registry import RegistryError
from carbonledger.units import grams_to_clt

from .models import STATUS_FOR, UNITS_STATUS, MandateIn, RetireIn, RevokeIn
from .state import DEMO_BATCH, DEMO_ISSUED_G, DEMO_PROJECT, State, anchor_wait_from_env, chain_from_env

__all__ = ["create_app", "public_receipt_id", "DEMO_BATCH", "DEMO_ISSUED_G", "DEMO_PROJECT", "UNITS_STATUS"]


def public_receipt_id(receipt_body: dict) -> str:
    """CL- plus 12 hex characters of the receipt's content digest. Not sequential: the explorer learns no volume."""
    return "CL-" + digest(receipt_body)[:12].upper()


def create_app(chain: Optional[ChainClient] = None, now: Callable[[], float] = time.time, web_origin: Optional[str] = None,
               anchor_wait_s: Optional[float] = None, start_worker: bool = True) -> FastAPI:
    st = State(chain or chain_from_env(), now, anchor_wait_from_env() if anchor_wait_s is None else anchor_wait_s)
    dev = os.environ.get("APP_ENV") == "dev"
    app = FastAPI(title="CarbonLedger API", docs_url="/docs" if dev else None, redoc_url=None, openapi_url="/openapi.json" if dev else None)
    app.state.st = st
    origin = web_origin or os.environ.get("WEB_ORIGIN")
    if origin:
        app.add_middleware(CORSMiddleware, allow_origins=[origin], allow_methods=["GET", "POST"], allow_headers=["content-type"])
    if start_worker:
        st.worker.start()

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
        return {"status": "ok", "chain": getattr(st.chain_client, "cluster", "unknown"), "units": UNITS_STATUS,
                "anchors": st.outbox.counts()}

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

    def _response(receipt: dict, receipt_hash: str, anchor: dict) -> dict:
        return {"receipt_id": receipt["receipt_id"], "ts": receipt["ts"], "receipt_hash": receipt_hash,
                "serial_start": receipt["serial_start"], "serial_end": receipt["serial_end"], "units_status": UNITS_STATUS, **anchor}

    @app.post("/v1/retire")
    def retire(body: RetireIn):
        payload_digest = digest(body.model_dump(exclude={"idempotency_key"}))
        with st.lock:
            prior = st.idem.get(body.idempotency_key)
            if prior is not None:
                if prior[0] != payload_digest:
                    raise HTTPException(409, "This idempotency key was already used for a different request.")
                receipt_id = prior[1]
            else:
                receipt_id = None
        if receipt_id is None:
            if not st.chain_healthy():
                raise HTTPException(502, "The chain could not be reached. Nothing was recorded.")
            with st.lock:
                prior = st.idem.get(body.idempotency_key)        # re-check: another thread may have won the race
                if prior is not None:
                    receipt_id = prior[1]
                else:
                    receipt_id = _commit(body, payload_digest)
        entry = st.outbox.wait_settled(receipt_id, st.anchor_wait_s)
        e = st.receipts.find(receipt_id)
        return _response(e["receipt"], e["hash"], entry.public())

    def _commit(body: RetireIn, payload_digest: str) -> str:
        """Called under the lock. Retires on a copy, commits, enqueues the anchor. Returns the receipt id."""
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
        receipt = {"ts": datetime.fromtimestamp(now, timezone.utc).isoformat(), "account": body.account,
                   "grams": body.grams, "clt": grams_to_clt(body.grams), "kind": body.kind, "label": body.label,
                   "lines_digest": lines_digest, "target_iso3": body.target_iso3, "project_id": DEMO_PROJECT, "batch_id": DEMO_BATCH,
                   "serial_start": ret.serial_start, "serial_end": ret.serial_end, "units": UNITS_STATUS}
        # The public id comes from the receipt's own content, so the memo never exposes a running count (F14).
        receipt_id = public_receipt_id(receipt)
        receipt["receipt_id"] = receipt_id
        entry = st.receipts.append(receipt)
        st.registry = reg
        if mandate is not None:
            consume(mandate, body.grams)
        st.outbox.enqueue(receipt_id, entry["hash"])
        st.idem[body.idempotency_key] = (payload_digest, receipt_id)
        return receipt_id

    @app.get("/v1/receipts/{receipt_id}")
    def get_receipt(receipt_id: str):
        e = st.receipts.find(receipt_id)
        if e is None:
            raise HTTPException(404, "No such receipt.")
        a = st.outbox.get(receipt_id)
        return {"entry": e, "chain": a.public() if a else None}

    @app.get("/v1/audit/verify")
    def audit_verify():
        bad = verify(st.receipts.entries())
        return {"intact": bad is None, "first_bad_index": bad, "count": len(st.receipts.entries()), "head_hash": st.receipts.head_hash(),
                "anchors": st.outbox.counts()}

    return app


app = create_app() if os.environ.get("CARBONLEDGER_AUTOSTART") else None
