"""CarbonLedger API. Server holds the register, the receipt chain and the signing key. Browsers hold nothing.
Units are pilot units, not yet verified credits, until a verifier attests a real project. The API says so in every response.
No login yet (see DEBT.md): do not expose this to the public internet before it exists.

The retire flow (rule 6 as refined on 2026-10-11):
  1. Check the request, the mandate, and that the chain is reachable. If it is not, nothing is recorded.
  2. Under the lock: retire on a copy of the register, append the receipt, commit, enqueue the anchor.
  3. Outside the lock: the anchor worker submits and confirms. The response waits up to ANCHOR_WAIT_SECONDS for it.
  4. Nothing is called "recorded on Solana" until the chain confirmed it. A failed anchor is shown as failed."""
import asyncio
import mimetypes
import copy
import os
import secrets
import time
from datetime import datetime, timezone
from typing import Callable, Optional

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

mimetypes.add_type("application/manifest+json", ".webmanifest")   # the installable app's manifest

from carbonledger.agentsig import AgentSigError, check_timestamp, verify_agent
from carbonledger.auth import ApiKeyStore, AuthError, KeyRecord
from carbonledger.chain import ChainClient
from carbonledger.merkle import verify_proof
from carbonledger.mandate import Mandate, MandateError, authorize, consume, revoke
from carbonledger.receipts import digest, to_json, verify
from carbonledger.registry import RegistryError
from carbonledger.units import grams_to_clt

from .accounts import account_router, world_router
from .growth import growth_router
from .studio import studio_router
from .mailer import mailer_from_env
from .people import people_from_env
from .seeker import sgt_lookup_from_env
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
               anchor_interval_s: Optional[float] = None, people=None, mailer="env", sgt_lookup="env") -> FastAPI:
    st = State(chain or chain_from_env(), now, anchor_wait_from_env() if anchor_wait_s is None else anchor_wait_s,
               keys=keys, limits=limits or Limits.from_env(), product_lookup=product_lookup, store=store,
               anchor_interval_s=anchor_interval_from_env() if anchor_interval_s is None else anchor_interval_s)
    dev = os.environ.get("APP_ENV") == "dev"
    app = FastAPI(title="CarbonLedger API", docs_url="/docs" if dev else None, redoc_url=None, openapi_url="/openapi.json" if dev else None)
    app.state.st = st
    st.people = people if people is not None else people_from_env(os.environ.get("DATABASE_URL"))
    mailer = mailer_from_env() if mailer == "env" else mailer
    sgt_lookup = sgt_lookup_from_env() if sgt_lookup == "env" else sgt_lookup
    origin = web_origin or os.environ.get("WEB_ORIGIN")
    if origin:
        app.add_middleware(CORSMiddleware, allow_origins=[origin], allow_methods=["GET", "POST", "PUT", "DELETE"], allow_headers=["content-type", "authorization"], expose_headers=["content-disposition"])
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

    def acts_for_business(caller: KeyRecord) -> bool:
        """Business, agent and authority keys act for a business. On a demo server every demo login does too:
        a visitor plays both leagues with one login, from the first tap (D28). Never true outside demo mode."""
        return caller.role in ("business", "agent", "authority") or (st.limits.demo_keys and caller.owner.startswith(("demo-", "acct-")))

    def require_key(request: Request) -> KeyRecord:
        """Every write needs a key (D2). Then the key's bucket must have a token (rate limit)."""
        auth = request.headers.get("authorization", "")
        token = auth[7:].strip() if auth.lower().startswith("bearer ") else ""
        try:
            rec = st.keys.check(token)
        except AuthError as exc:
            how = "Get a demo login below, or open Settings and add your API key." if st.limits.demo_keys else "Open Settings (the gear icon) and add your API key."
            raise HTTPException(401, f"Not allowed: {exc.code}. This needs a login. {how} Nothing was recorded.", headers={"WWW-Authenticate": "Bearer"})
        if not st.bucket.take(rec.key_id):
            raise HTTPException(429, "Too many requests for this key. Wait a minute. Nothing was recorded.", headers={"Retry-After": "60"})
        return rec

    def optional_key(request: Request) -> Optional[KeyRecord]:
        """A key if one was sent and is good, else None (public reads that can also say "you")."""
        return require_key(request) if request.headers.get("authorization") else None

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
            resp.headers.setdefault("Cache-Control", "no-cache")   # revalidate by ETag, so a deploy shows at once
        return resp

    @app.get("/health")
    def health():
        return {"status": "ok", "chain": getattr(st.chain_client, "cluster", "unknown"), "units": UNITS_STATUS,
                "anchors": st.outbox.counts(), "store": st.store.kind, "demo_keys": st.limits.demo_keys}

    @app.post("/v1/demo/key", status_code=201)
    def demo_key(request: Request, role: str = "personal"):
        """A self-serve login for the demo (pilot units only). Off unless DEMO_LOGINS=1 and APP_ENV=demo: then
        a few per hour per client address, personal or business, stored like any other key. The plaintext is
        shown once, to the caller, and never logged."""
        if not st.limits.demo_keys:
            raise HTTPException(404, "Demo logins are not available here. Ask whoever runs the API for a key.")
        if role not in ("personal", "business"):
            raise HTTPException(422, "role must be personal or business. Nothing was recorded.")
        client = request.headers.get("x-forwarded-for", "").split(",")[0].strip() or (request.client.host if request.client else "unknown")
        if not st.demo_bucket.take(client):
            raise HTTPException(429, "Too many demo logins from this address. Try again in an hour.", headers={"Retry-After": "3600"})
        owner = f"demo-{role}-{secrets.token_hex(4)}"
        key, rec = st.keys.issue(role, owner)
        st.store.insert_api_key(rec)
        return {"api_key": key, "role": role, "owner": owner, "units": UNITS_STATUS,
                "note": "A demo login for pilot units. It signs nothing. Keep it in this browser's Settings."}

    @app.get("/v1/registry/summary")
    def summary():
        b = st.registry.batches[DEMO_BATCH]
        return {"units": UNITS_STATUS, "issued_g": b.issued_g, "retired_g": b.retired_g, "remaining_g": b.issued_g - b.retired_g,
                "retirements": len(st.registry.retirements)}

    @app.post("/v1/mandates", status_code=201)
    def create_mandate(body: MandateIn, caller: KeyRecord = Depends(require_key)):
        if not acts_for_business(caller) or caller.role == "agent":
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
        if body.account == "business" and not acts_for_business(caller):
            raise HTTPException(403, "This key cannot retire for a business. Use a business login. Nothing was recorded.")
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
        """Called under the lock. Every attempt that reaches a decision becomes a sealed receipt (KYA format):
        ACCEPTED with its serial range, or REFUSED with the rule that stopped it. Returns the accepted receipt id."""
        now = int(st.now())
        at = datetime.fromtimestamp(now, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        cluster = getattr(st.chain_client, 'cluster', 'unknown')
        ledger = f"CarbonLedger API, {'dry run' if cluster == 'dry-run' else 'Solana ' + cluster} (pilot units, not yet verified)"
        lines_digest = digest({"lines": [l.model_dump() for l in body.lines]})
        note_digest = digest({"note": body.note}) if body.note else None
        items_digest = digest({"items": [i.model_dump(by_alias=True) for i in body.items]})
        base = {"ts": datetime.fromtimestamp(now, timezone.utc).isoformat(), "account": body.account, "owner": caller.owner,
                "grams": body.grams, "kind": body.kind, "label": body.label, "lines_digest": lines_digest, "note_digest": note_digest,
                "items_digest": items_digest, "target_iso3": body.target_iso3, "project_id": DEMO_PROJECT, "batch_id": DEMO_BATCH, "units": UNITS_STATUS}
        what = f"retire {body.grams} g of pilot units: {body.label}"
        mandate = st.mandates.get(body.mandate_id) if body.mandate_id is not None else None
        if body.mandate_id is not None and mandate is None:
            raise HTTPException(404, "No such mandate.")
        if mandate is not None and not body.agent:
            raise HTTPException(422, "An agent key is required when a mandate is used.")
        approved_by = f"mandate {mandate.id} of {mandate.owner}" if mandate else f"api key owner {caller.owner}"

        def refuse(status: int, code: str, message: str, computed_g=None) -> None:
            """Record the refusal as a receipt (it is anchored like any other), then answer. No units move."""
            fields = {**base, "computed_g": computed_g, "refusal_code": code}
            fields["receipt_id"] = public_receipt_id(fields)
            entry = st.receipts.prepare(fields, what=what, amount=str(body.grams), payee=DEMO_PROJECT, rule=f"{code}: {message}", outcome="REFUSED",
                                        approved_by=approved_by, ledger=ledger, at=at, instrument="nothing moved")
            try:
                st.store.write_refusal(entry)
                entry = st.receipts.commit(entry)
                st.outbox.enqueue(fields["receipt_id"], entry["hash"], entry["index"])
                noted = f" The refusal is on the record as {fields['receipt_id']}."
            except StoreError:
                noted = " The refusal could not be recorded."
            raise HTTPException(status, f"{message} No units were retired.{noted}")

        if mandate is not None:
            try:
                check_timestamp(body.agent_ts, now, st.limits.agent_sig_max_age_s)
                verify_agent(body.agent, body.agent_sig, body.model_dump(exclude={"agent_sig"}))
            except AgentSigError as exc:
                refuse(403, exc.code, f"The agent signature was refused: {exc.code}.")
            try:
                authorize(mandate, body.agent, body.grams, DEMO_PROJECT, now)
            except MandateError as exc:
                refuse(403, exc.code, f"The mandate does not allow this: {exc.code}.")
        # The server prices the items itself (D1). A total below that is refused. Above it is allowed: estimates err high.
        try:
            computed_g, _breakdown = compute(body.items, st.product_lookup)
        except RecomputeError as exc:
            refuse(422, exc.code, f"Cannot price this request: {exc}.")
        if body.grams < computed_g:
            refuse(422, "BELOW_COMPUTED", f"The total ({body.grams} g) is below what the server computes for these items ({computed_g} g).", computed_g)
        reg = copy.deepcopy(st.registry)            # work on a copy; commit only if everything succeeds
        retiree = f"{body.account}:{caller.owner}:{body.agent or 'self'}"
        try:
            ret = reg.retire(retiree, DEMO_BATCH, body.grams, body.target_iso3, lines_digest)
        except RegistryError as exc:
            refuse(STATUS_FOR.get(exc.code, 409), exc.code, "Not enough pilot units left." if exc.code == "OVER_RETIREMENT" else str(exc), computed_g)
        fields = {**base, "clt": grams_to_clt(body.grams), "computed_g": computed_g, "serial_start": ret.serial_start, "serial_end": ret.serial_end}
        # The public id comes from the receipt's own content, so the memo never exposes a running count (F14).
        receipt_id = public_receipt_id(fields)
        fields["receipt_id"] = receipt_id
        rule = "within the mandate cap, allow-list and expiry; priced by the server" if mandate else "priced by the server from the typed items; pilot units available"
        preview = st.receipts.prepare(fields, what=what, amount=str(body.grams), payee=DEMO_PROJECT, rule=rule, outcome="ACCEPTED", approved_by=approved_by,
                                      ledger=ledger, at=at, instrument=f"serial range {ret.serial_start}-{ret.serial_end} of batch {DEMO_BATCH}")
        try:                                     # the database first (its constraints are the second guard), then memory
            st.store.write_retirement(preview, ret, reg.batches[DEMO_BATCH], body.idempotency_key, payload_digest)
        except StoreError as exc:
            raise HTTPException(409, f"{exc}. Nothing was recorded.")
        entry = st.receipts.commit(preview)
        st.registry = reg
        if mandate is not None:
            consume(mandate, body.grams)
            st.store.upsert_mandate(mandate)
        st.outbox.enqueue(receipt_id, entry["hash"], entry["index"])
        st.idem[body.idempotency_key] = (payload_digest, receipt_id)
        return receipt_id

    app.include_router(account_router(st, require_key))
    app.include_router(growth_router(st, require_key, optional_key, mailer, st.people, os.environ.get("PUBLIC_URL", "https://carbonledger.world").rstrip("/"), sgt_lookup))
    app.include_router(world_router(st))
    app.include_router(studio_router())

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

    @app.get("/v1/audit/receipts.json")
    def audit_export():
        """The whole chain in the KYA receipt wire format, for `python -m knowyouragenticai_receipts verify` and the
        verifier page. Ids and hashes only: no names, baskets or notes are in it."""
        from fastapi.responses import Response
        return Response(to_json(st.receipts.receipts()), media_type="application/json",
                        headers={"content-disposition": 'attachment; filename="carbonledger-receipts.json"'})

    @app.get("/v1/audit/verify")
    def audit_verify():
        bad = verify(st.receipts.entries())
        rs = st.receipts.receipts()
        return {"intact": bad is None, "first_bad_index": bad, "count": len(rs), "accepted": sum(r["outcome"] == "ACCEPTED" for r in rs),
                "refused": sum(r["outcome"] == "REFUSED" for r in rs), "head_hash": st.receipts.head_hash(), "format": "knowyouragenticai-receipts 1.1.0",
                "anchors": st.outbox.counts()}

    web_dir = Path(os.environ.get("WEB_DIR", "")) if os.environ.get("WEB_DIR") else None
    if web_dir and web_dir.is_dir():          # one origin for app and API (deploy): no CORS, the page's CSP 'self' covers the API
        from fastapi.responses import FileResponse
        landing, shell, studio = web_dir / "landing.html", web_dir / "index.html", web_dir / "studio.html"

        @app.get("/", include_in_schema=False)
        def home(request: Request):           # the public landing page; the app lives at /app, VOREM Studio at studio.<domain>
            if request.headers.get("host", "").split(":")[0].startswith("studio.") and studio.is_file():
                return FileResponse(studio)
            return FileResponse(landing if landing.is_file() else shell)

        @app.get("/studio", include_in_schema=False)
        def studio_page():
            return FileResponse(studio)

        @app.get("/app", include_in_schema=False)
        def app_shell():                      # /app has no trailing slash, so the app's relative asset paths still resolve from /
            return FileResponse(shell)
        app.mount("/", StaticFiles(directory=str(web_dir), html=True), name="web")
    return app


app = create_app() if os.environ.get("CARBONLEDGER_AUTOSTART") else None
