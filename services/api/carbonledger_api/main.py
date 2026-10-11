"""CarbonLedger API. Server holds the register, the receipt chain and the signing key. Browsers hold nothing.
Units are SIMULATED pilot units until a verifier attests real ones. The API says so in every response.
No login yet (see DEBT.md): do not expose this to the public internet before it exists.

The retire flow (rule 6 as refined on 2026-10-11):
  1. Check the request, the mandate, and that the chain is reachable. If it is not, nothing is recorded.
  2. Under the lock: retire on a copy of the register, append the receipt, commit, enqueue the anchor.
  3. Outside the lock: the anchor worker submits and confirms. The response waits up to ANCHOR_WAIT_SECONDS for it.
  4. Nothing is called "recorded on Solana" until the chain confirmed it. A failed anchor is shown as failed."""
import asyncio
import copy
import os
import time
from datetime import datetime, timezone
from typing import Callable, Optional

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from carbonledger.agentsig import AgentSigError, check_timestamp, verify_agent
from carbonledger.auth import ApiKeyStore, AuthError, KeyRecord
from carbonledger.chain import ChainClient
from carbonledger.merkle import verify_proof
from carbonledger.mandate import Mandate, MandateError, authorize, consume, revoke
from carbonledger.receipts import digest, verify
from carbonledger.registry import RegistryError
from carbonledger.units import grams_to_clt

from .accounts import account_router
from .lookup import ProductLookup
from .models import STATUS_FOR, UNITS_STATUS, MandateIn, RetireIn
from .recompute import RecomputeError, compute
from .state import DEMO_BATCH, DEMO_ISSUED_G, DEMO_PROJECT, Limits, State, anchor_interval_from_env, anchor_wait_from_env, chain_from_env
from .store import StoreError

__all__ = ["create_app", "public_receipt_id", "DEMO_BATCH", "DEMO_ISSUED_G", "DEMO_PROJECT", "UNITS_STATUS"]


def public_receipt_id(receipt_body: dict) -> str:
    """CL- plus 12 hex characters of the receipt's content digest. Not sequential: the explorer learns no volume."""
    return "CL-" + digest(receipt_body)[:12].upper()


def create_app(chain: Optional[ChainClient] = None, now: Callable[[], float] = time.time, web_origin: Optional[str] = None,
               anchor_wait_s: Optional[float] = None, start_worker: bool = True, keys: Optional[ApiKeyStore] = None,
               limits: Optional[Limits] = None, product_lookup: Optional[ProductLookup] = None, store=None,
               anchor_interval_s: Optional[float] = None) -> FastAPI:
    st = State(chain or chain_from_env(), now, anchor_wait_from_env() if anchor_wait_s is None else anchor_wait_s,
               keys=keys, limits=limits or Limits.from_env(), product_lookup=product_lookup, store=store,
               anchor_interval_s=anchor_interval_from_env() if anchor_interval_s is None else anchor_interval_s)
    dev = os.environ.get("APP_ENV") == "dev"
    app = FastAPI(title="CarbonLedger API", docs_url="/docs" if dev else None, redoc_url=None, openapi_url="/openapi.json" if dev else None)
    app.state.st = st
    origin = web_origin or os.environ.get("WEB_ORIGIN")
    if origin:
        app.add_middleware(CORSMiddleware, allow_origins=[origin], allow_methods=["GET", "POST"], allow_headers=["content-type", "authorization"])
    if start_worker:
        st.worker.start()

    @app.exception_handler(RequestValidationError)
    async def plain_422(request: Request, exc: RequestValidationError):
        """Rule 4: an error says what happened in words, and that nothing was recorded. One line, no stack of objects."""
        parts = []
        for e in exc.errors()[:5]:
            loc = ".".join(str(x) for x in e.get("loc", []) if x not in ("body",))
            parts.append(f"{loc}: {e.get('msg', 'invalid')}" if loc else e.get("msg", "invalid"))
        errors = [{"loc": [str(x) for x in e.get("loc", [])], "msg": e.get("msg", ""), "type": e.get("type", "")} for e in exc.errors()[:5]]
        return JSONResponse({"detail": "Invalid request. " + "; ".join(parts) + ". Nothing was recorded.", "errors": errors}, status_code=422)

    def require_key(request: Request) -> KeyRecord:
        """Every write needs a key (D2). Then the key's bucket must have a token (rate limit)."""
        auth = request.headers.get("authorization", "")
        token = auth[7:].strip() if auth.lower().startswith("bearer ") else ""
        try:
            rec = st.keys.check(token)
        except AuthError as exc:
            raise HTTPException(401, f"Not allowed: {exc.code}. Nothing was recorded.", headers={"WWW-Authenticate": "Bearer"})
        if not st.bucket.take(rec.key_id):
            raise HTTPException(429, "Too many requests for this key. Wait a minute. Nothing was recorded.", headers={"Retry-After": "60"})
        return rec

    @app.middleware("http")
    async def edge_limits(request: Request, call_next):
        """Request size and a server-side deadline. A timed-out request answers 504 and says to check history."""
        length = request.headers.get("content-length")
        if length and length.isdigit() and int(length) > st.limits.max_request_bytes:
            return JSONResponse({"detail": "Request too large. Nothing was recorded."}, status_code=413)
        try:
            return await asyncio.wait_for(call_next(request), timeout=st.limits.request_timeout_s)
        except asyncio.TimeoutError:
            return JSONResponse({"detail": "The server took too long. The outcome is unconfirmed: check your history before retrying."}, status_code=504)

    @app.middleware("http")
    async def security_headers(request, call_next):
        resp = await call_next(request)
        resp.headers["X-Content-Type-Options"] = "nosniff"
        resp.headers["X-Frame-Options"] = "DENY"
        resp.headers["Referrer-Policy"] = "no-referrer"
        resp.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
        if request.url.path.startswith(("/v1/", "/health", "/docs", "/openapi.json")):
            resp.headers["Cache-Control"] = "no-store"
            resp.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"
        else:                                    # the app's own pages carry their policy in a meta tag (apps/web/index.html)
            resp.headers["Content-Security-Policy"] = "frame-ancestors 'none'"
        return resp

    @app.get("/health")
    def health():
        return {"status": "ok", "chain": getattr(st.chain_client, "cluster", "unknown"), "units": UNITS_STATUS,
                "anchors": st.outbox.counts(), "store": st.store.kind}

    @app.get("/v1/registry/summary")
    def summary():
        b = st.registry.batches[DEMO_BATCH]
        return {"units": UNITS_STATUS, "issued_g": b.issued_g, "retired_g": b.retired_g, "remaining_g": b.issued_g - b.retired_g,
                "retirements": len(st.registry.retirements)}

    @app.post("/v1/mandates", status_code=201)
    def create_mandate(body: MandateIn, caller: KeyRecord = Depends(require_key)):
        if caller.role not in ("business", "authority"):
            raise HTTPException(403, "Only a business key can write a mandate. Nothing was recorded.")
        with st.lock:
            mid = "mnd-" + digest({"n": len(st.mandates), "o": caller.owner, "a": body.agent})[:12]
            st.mandates[mid] = Mandate(mid, caller.owner, body.agent, body.cap_g, int(st.now()) + body.ttl_seconds,
                                       tuple(body.allow_projects) if body.allow_projects is not None else None)
            st.store.upsert_mandate(st.mandates[mid])
        return {"mandate_id": mid, "owner": caller.owner}

    @app.post("/v1/mandates/{mandate_id}/revoke")
    def revoke_mandate(mandate_id: str, caller: KeyRecord = Depends(require_key)):
        with st.lock:
            m = st.mandates.get(mandate_id)
            if m is None:
                raise HTTPException(404, "No such mandate.")
            try:
                revoke(m, caller.owner)
            except MandateError as exc:
                raise HTTPException(403, str(exc))
            st.store.upsert_mandate(m)
        return {"revoked": True}

    def _response(receipt: dict, receipt_hash: str, anchor: dict) -> dict:
        return {"receipt_id": receipt["receipt_id"], "ts": receipt["ts"], "receipt_hash": receipt_hash,
                "serial_start": receipt["serial_start"], "serial_end": receipt["serial_end"], "units_status": UNITS_STATUS, **anchor}

    @app.post("/v1/retire")
    def retire(body: RetireIn, caller: KeyRecord = Depends(require_key)):
        if body.account == "business" and caller.role not in ("business", "agent", "authority"):
            raise HTTPException(403, "This key cannot retire for a business. Nothing was recorded.")
        payload_digest = digest({**body.model_dump(exclude={"idempotency_key"}), "caller": caller.owner})
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
                    receipt_id = _commit(body, payload_digest, caller)
        entry = st.outbox.wait_settled(receipt_id, st.anchor_wait_s)
        e = st.receipts.find(receipt_id)
        return _response(e["receipt"], e["hash"], entry.public())

    def _commit(body: RetireIn, payload_digest: str, caller: KeyRecord) -> str:
        """Called under the lock. Retires on a copy, commits, enqueues the anchor. Returns the receipt id."""
        now = int(st.now())
        mandate = None
        if body.mandate_id is not None:
            mandate = st.mandates.get(body.mandate_id)
            if mandate is None:
                raise HTTPException(404, "No such mandate.")
            if not body.agent:
                raise HTTPException(422, "An agent key is required when a mandate is used.")
            try:
                check_timestamp(body.agent_ts, now, st.limits.agent_sig_max_age_s)
                verify_agent(body.agent, body.agent_sig, body.model_dump(exclude={"agent_sig"}))
            except AgentSigError as exc:
                raise HTTPException(403, f"The agent signature was refused: {exc.code}. Nothing was recorded.")
            try:
                authorize(mandate, body.agent, body.grams, DEMO_PROJECT, now)
            except MandateError as exc:
                raise HTTPException(403, f"The mandate does not allow this: {exc.code}.")
        # The server prices the items itself (D1). A total below that is refused. Above it is allowed: estimates err high.
        try:
            computed_g, _breakdown = compute(body.items, st.product_lookup)
        except RecomputeError as exc:
            raise HTTPException(422, f"Cannot price this request: {exc}. Nothing was recorded.")
        if body.grams < computed_g:
            raise HTTPException(422, f"The total ({body.grams} g) is below what the server computes for these items ({computed_g} g). Nothing was recorded.")
        reg = copy.deepcopy(st.registry)            # work on a copy; commit only if everything succeeds
        retiree = f"{body.account}:{caller.owner}:{body.agent or 'self'}"
        lines_digest = digest({"lines": [l.model_dump() for l in body.lines]})
        note_digest = digest({"note": body.note}) if body.note else None
        items_digest = digest({"items": [i.model_dump(by_alias=True) for i in body.items]})
        try:
            ret = reg.retire(retiree, DEMO_BATCH, body.grams, body.target_iso3, lines_digest)
        except RegistryError as exc:
            raise HTTPException(STATUS_FOR.get(exc.code, 409), "Not enough pilot units left." if exc.code == "OVER_RETIREMENT" else str(exc))
        receipt = {"ts": datetime.fromtimestamp(now, timezone.utc).isoformat(), "account": body.account, "owner": caller.owner,
                   "grams": body.grams, "clt": grams_to_clt(body.grams), "kind": body.kind, "label": body.label,
                   "lines_digest": lines_digest, "note_digest": note_digest, "items_digest": items_digest, "computed_g": computed_g,
                   "target_iso3": body.target_iso3, "project_id": DEMO_PROJECT, "batch_id": DEMO_BATCH,
                   "serial_start": ret.serial_start, "serial_end": ret.serial_end, "units": UNITS_STATUS}
        # The public id comes from the receipt's own content, so the memo never exposes a running count (F14).
        receipt_id = public_receipt_id(receipt)
        receipt["receipt_id"] = receipt_id
        preview = {"index": st.receipts.next_index(), "receipt": receipt, "prev_hash": st.receipts.head_hash()}
        preview["hash"] = digest(preview)
        try:                                     # the database first (its constraints are the second guard), then memory
            st.store.write_retirement(preview, ret, reg.batches[DEMO_BATCH], body.idempotency_key, payload_digest)
        except StoreError as exc:
            raise HTTPException(409, f"{exc}. Nothing was recorded.")
        entry = st.receipts.append(receipt)
        assert entry["hash"] == preview["hash"]
        st.registry = reg
        if mandate is not None:
            consume(mandate, body.grams)
            st.store.upsert_mandate(mandate)
        st.outbox.enqueue(receipt_id, entry["hash"], entry["index"])
        st.idem[body.idempotency_key] = (payload_digest, receipt_id)
        return receipt_id

    app.include_router(account_router(st, require_key))

    @app.get("/v1/receipts/{receipt_id}")
    def get_receipt(receipt_id: str):
        e = st.receipts.find(receipt_id)
        if e is None:
            raise HTTPException(404, "No such receipt.")
        a = st.outbox.get(receipt_id)
        return {"entry": e, "chain": a.public() if a else None}

    @app.get("/v1/receipts/{receipt_id}/proof")
    def get_proof(receipt_id: str):
        """The Merkle path from this receipt's hash to the anchored root. Anyone can recompute it (verify screen)."""
        e = st.receipts.find(receipt_id)
        if e is None:
            raise HTTPException(404, "No such receipt.")
        a = st.outbox.get(receipt_id)
        ok = bool(a and a.status == "anchored" and a.proof is not None and verify_proof(e["hash"], [tuple(p) for p in a.proof], a.anchor_root))
        return {"receipt_id": receipt_id, "receipt_hash": e["hash"], "index": e["index"], **(a.public() if a else {"anchor_status": "pending"}),
                "proof": a.proof if a else None, "proof_checks": ok,
                "memo": f"carbonledger:v2:{a.anchor_id}:{a.anchor_root}" if a and a.anchor_root else None}

    @app.get("/v1/audit/verify")
    def audit_verify():
        bad = verify(st.receipts.entries())
        return {"intact": bad is None, "first_bad_index": bad, "count": len(st.receipts.entries()), "head_hash": st.receipts.head_hash(),
                "anchors": st.outbox.counts()}

    web_dir = Path(os.environ.get("WEB_DIR", "")) if os.environ.get("WEB_DIR") else None
    if web_dir and web_dir.is_dir():          # one origin for app and API (deploy): no CORS, the page's CSP 'self' covers the API
        app.mount("/", StaticFiles(directory=str(web_dir), html=True), name="web")
    return app


app = create_app() if os.environ.get("CARBONLEDGER_AUTOSTART") else None
