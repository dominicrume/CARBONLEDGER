"""Growth: what the business needs around the ledger, without touching the ledger.
  A  /v1/events and /v1/metrics: privacy-first usage counts (a day, a name, a number) and an operator dashboard.
  B  /v1/auth/*, /v1/accounts/me/profile, DELETE /v1/accounts/me: email sign-in, profiles, delete my data.
  C  /v1/accounts/me/statement: a business's retirement statement (CSV or JSON), every line checkable by receipt.
  D  /v1/league: weekly seasons ranked by XP (carbonledger_api/xp.py), never by grams, from server records only.
Personal data is the email and the display name, both deleted on request. Receipts carry only an owner id."""
import csv
import hashlib
import hmac
import io
import os
import re
import secrets
from datetime import date, datetime, timedelta, timezone
from typing import Callable, Dict, List, Literal, Optional, Set

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, Field

from carbonledger.auth import TokenBucket

from .models import UNITS_STATUS
from .seeker import NONCE_TTL_S, SeekerError, challenge, check_sign_in
from .xp import week_of, xp_of

# The only events the app may count. Retirements are not events: they are counted from the ledger itself.
EVENTS = {"site_view", "app_open", "scan_start", "estimate", "retire_open", "verify", "install", "signin_start", "statement"}
LINK_TTL_S = 15 * 60
EMAIL_RX = re.compile(r"^[^@\s]{1,64}@[^@\s]{1,190}\.[a-z]{2,24}$")
NAME_RX = re.compile(r"^[\w .'\-]{1,24}$", re.UNICODE)
RESERVED = ("carbonledger", "admin", "verifier", "trustee", "official", "support")
BLOCKED = ("fuck", "shit", "cunt", "nigg", "fag", "rape", "nazi", "hitler")   # a first filter; reports go to a person


class EventIn(BaseModel):
    name: str = Field(min_length=2, max_length=32)


class EmailIn(BaseModel):
    email: str = Field(min_length=3, max_length=254)


class TokenIn(BaseModel):
    token: str = Field(min_length=20, max_length=200)


class SeekerIn(BaseModel):
    address: str = Field(min_length=32, max_length=44)
    signed_message: str = Field(min_length=20, max_length=4000)
    signature: str = Field(min_length=40, max_length=200)


class ProfileIn(BaseModel):
    display_name: Optional[str] = Field(default=None, max_length=24)
    business_name: Optional[str] = Field(default=None, max_length=80)
    employees: Optional[int] = Field(default=None, ge=1, le=10_000_000)


def pseudonym(owner: str) -> str:
    """A stable public name that reveals nothing: Player 7F3A."""
    return "Player " + hashlib.sha256(owner.encode()).hexdigest()[:4].upper()


def clean_name(raw: str, field: str) -> Optional[str]:
    v = " ".join((raw or "").split())
    if not v:
        return None
    low = v.lower()
    if field == "display_name" and (not NAME_RX.match(v) or any(w in low for w in RESERVED)):
        raise HTTPException(422, "Choose a name of up to 24 letters, numbers, spaces, dots, dashes or apostrophes, not an official-sounding one. Nothing was saved.")
    if any(w in low.replace(" ", "") for w in BLOCKED):
        raise HTTPException(422, "That name is not allowed. Choose another. Nothing was saved.")
    return v


def growth_router(st, require_key: Callable, optional_key: Callable, mailer, people, public_url: str, sgt_lookup=None) -> APIRouter:
    g = APIRouter()
    event_bucket = TokenBucket(1, 120)
    event_bucket.rate = 120 / 3600.0                       # 120 events an hour per address, then quietly dropped
    email_bucket = TokenBucket(1, 5)
    email_bucket.rate = 5 / 3600.0                         # five sign-in emails an hour per address

    def client(request: Request) -> str:
        return request.headers.get("x-forwarded-for", "").split(",")[0].strip() or (request.client.host if request.client else "unknown")

    def today() -> str:
        return datetime.fromtimestamp(st.now(), timezone.utc).date().isoformat()

    def owners_for(owner: str) -> Set[str]:
        aid = people.account_of(owner)
        return people.owners_of(aid) if aid else {owner}

    def main_owner(owner: str) -> str:
        return people.account_of(owner) or owner

    def accepted(entries=None):
        for e in entries if entries is not None else st.receipts.entries():
            if e["receipt"].get("outcome") == "ACCEPTED":
                yield e

    # ---------------- A: usage counts and the operator dashboard ----------------
    @g.post("/v1/events", status_code=204)
    def event(body: EventIn, request: Request):
        """Counts one event for today. No id, no address, no device is stored. Unknown names and floods are dropped."""
        if body.name in EVENTS and event_bucket.take(client(request)):
            people.count_event(today(), body.name)
        return Response(status_code=204)

    @g.get("/v1/metrics")
    def metrics(request: Request, days: int = 30):
        """Operator only (METRICS_TOKEN). Usage counts plus what the ledger itself says: retirements, players, return rate."""
        token = os.environ.get("METRICS_TOKEN", "").strip()
        auth = request.headers.get("authorization", "")
        given = auth[7:].strip() if auth.lower().startswith("bearer ") else ""
        if not token or token.startswith("<") or not hmac.compare_digest(given, token):
            raise HTTPException(404, "Not found.")
        if not 1 <= days <= 366:
            raise HTTPException(422, "days must be between 1 and 366")
        since = (date.fromisoformat(today()) - timedelta(days=days - 1)).isoformat()
        per_day: Dict[str, dict] = {}
        first_seen: Dict[str, str] = {}
        weeks: Dict[str, Set[str]] = {}
        totals = {"retirements": 0, "refusals": 0, "grams": 0, "by_kind": {}, "by_account": {}}
        for e in st.receipts.entries():
            rc = e["receipt"]
            d = str(rc.get("ts", ""))[:10]
            o = main_owner(rc.get("owner", "?"))
            if rc.get("outcome") != "ACCEPTED":
                totals["refusals"] += 1
                if d >= since:
                    per_day.setdefault(d, {}).setdefault("refusals", 0)
                    per_day[d]["refusals"] += 1
                continue
            first_seen.setdefault(o, d)
            weeks.setdefault(o, set()).add(week_of(d))
            totals["retirements"] += 1
            totals["grams"] += rc["grams"]
            totals["by_kind"][rc["kind"]] = totals["by_kind"].get(rc["kind"], 0) + 1
            totals["by_account"][rc["account"]] = totals["by_account"].get(rc["account"], 0) + 1
            if d >= since:
                row = per_day.setdefault(d, {})
                row["retirements"] = row.get("retirements", 0) + 1
                row.setdefault("_players", set()).add(o)
        for d in first_seen.values():          # first_seen: player -> the day of their first retirement
            if d >= since:
                per_day.setdefault(d, {})["new_players"] = per_day.get(d, {}).get("new_players", 0) + 1
        for row in per_day.values():
            row["players"] = len(row.pop("_players", set()))
        for d, counts in people.event_counts(since).items():
            per_day.setdefault(d, {}).update(counts)
        players = len(first_seen)
        returning = sum(1 for w in weeks.values() if len(w) >= 2)
        window = [per_day.get(d, {}) for d in per_day if d >= since]
        funnel = {"site_view": sum(r.get("site_view", 0) for r in window), "app_open": sum(r.get("app_open", 0) for r in window),
                  "retire_open": sum(r.get("retire_open", 0) for r in window), "retirements": sum(r.get("retirements", 0) for r in window),
                  "new_players": sum(r.get("new_players", 0) for r in window)}
        return {"since": since, "units": UNITS_STATUS, "days": dict(sorted(per_day.items())), "funnel": funnel,
                "players": players, "returning_players": returning, "return_rate": round(returning / players, 3) if players else 0.0,
                "mandates": len(st.mandates), "anchors": st.outbox.counts(), **totals}

    # ---------------- B: sign-in, profile, delete my data ----------------
    @g.post("/v1/auth/email", status_code=202)
    def auth_email(body: EmailIn, request: Request):
        """Sends a one-time sign-in link. The same answer whether or not the address has an account."""
        if mailer is None:
            raise HTTPException(503, "Email sign-in is not set up on this server yet. Nothing was stored.")
        email = body.email.strip().lower()
        if not EMAIL_RX.match(email):
            raise HTTPException(422, "That does not look like an email address. Nothing was stored.")
        if not email_bucket.take(client(request)):
            raise HTTPException(429, "Too many sign-in emails from this address. Try again in an hour.", headers={"Retry-After": "3600"})
        token = secrets.token_urlsafe(32)
        people.put_link(hashlib.sha256(token.encode()).hexdigest(), email, st.now() + LINK_TTL_S)
        try:
            mailer(email, f"{public_url}/app#signin?t={token}")
        except Exception:
            raise HTTPException(502, "The email could not be sent just now. Try again in a minute.")
        return {"sent": True, "note": "If that address can receive email, a sign-in link is on its way. It works once, for 15 minutes."}

    @g.post("/v1/auth/verify")
    def auth_verify(body: TokenIn, caller=Depends(optional_key)):
        """Uses a sign-in link once. The login this browser already played with joins the account, so nothing is lost."""
        email = people.take_link(hashlib.sha256(body.token.encode()).hexdigest(), st.now())
        if not email:
            raise HTTPException(401, "This sign-in link has expired or was already used. Ask for a new one. Nothing changed.")
        aid = people.account_for_email(email)
        if caller is not None and caller.owner != aid:
            people.link_owner(caller.owner, aid)
        key, rec = st.keys.issue("personal", aid)
        st.store.insert_api_key(rec)
        return {"api_key": key, "owner": aid, "email": email, "units": UNITS_STATUS,
                "note": "Signed in. This browser keeps the login in Settings. Your earlier progress is part of your account now."}

    # ---------------- Sign in with Seeker: SIWS, then a read-only Genesis Token check ----------------
    domain = public_url.split("://", 1)[-1].split("/", 1)[0]
    iso = lambda t: datetime.fromtimestamp(t, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    @g.post("/v1/auth/seeker/challenge")
    def seeker_challenge(request: Request):
        """A one-time nonce for the wallet to sign. Signing moves nothing: no transaction, no payment."""
        if not email_bucket.take("siws:" + client(request)):
            raise HTTPException(429, "Too many sign-in attempts from this address. Try again later.", headers={"Retry-After": "3600"})
        nonce = secrets.token_hex(16)
        people.put_link(hashlib.sha256(f"siws:{nonce}".encode()).hexdigest(), "siws", st.now() + NONCE_TTL_S)
        return challenge(domain, public_url, nonce, iso(st.now()), iso(st.now() + NONCE_TTL_S))

    @g.post("/v1/auth/seeker/verify")
    def seeker_verify(body: SeekerIn, caller=Depends(optional_key)):
        try:
            nonce = check_sign_in(domain, body.address, body.signed_message, body.signature)
        except SeekerError as exc:
            raise HTTPException(401, f"Seeker sign-in refused: {exc}. Nothing changed.")
        if people.take_link(hashlib.sha256(f"siws:{nonce}".encode()).hexdigest(), st.now()) != "siws":
            raise HTTPException(401, "This sign-in has expired or was already used. Try again. Nothing changed.")
        aid = people.account_for_wallet(body.address)
        if caller is not None and caller.owner != aid:
            people.link_owner(caller.owner, aid)
        key, rec = st.keys.issue("personal", aid)
        st.store.insert_api_key(rec)
        seeker, note = False, "Signed in with your wallet. No Seeker Genesis Token was found on it."
        try:
            mint = sgt_lookup(body.address) if sgt_lookup else None
            if mint and people.set_seeker(aid, mint):
                seeker, note = True, "Signed in. Seeker Genesis Token verified: the Seeker badge is yours."
            elif mint:
                note = "Signed in. This phone's Seeker Genesis Token already belongs to another CarbonLedger account."
        except Exception:
            note = "Signed in with your wallet. The Seeker check could not reach Solana just now; sign in again later to add it."
        return {"api_key": key, "owner": aid, "wallet": body.address, "seeker": seeker, "note": note, "units": UNITS_STATUS}

    @g.get("/v1/accounts/me/profile")
    def get_profile(caller=Depends(require_key)):
        aid = people.account_of(caller.owner)
        return {"owner": main_owner(caller.owner), "signed_in": bool(aid), "email": people.email_of(aid) if aid else None,
                "seeker": bool(aid) and aid in people.seekers(),
                "public_name": people.get_profile(main_owner(caller.owner)).get("display_name") or pseudonym(main_owner(caller.owner)),
                **people.get_profile(main_owner(caller.owner))}

    @g.put("/v1/accounts/me/profile")
    def put_profile(body: ProfileIn, caller=Depends(require_key)):
        fields = {}
        if body.display_name is not None:
            fields["display_name"] = clean_name(body.display_name, "display_name")
        if body.business_name is not None:
            fields["business_name"] = clean_name(body.business_name, "business_name")
        if body.employees is not None:
            fields["employees"] = body.employees
        p = people.put_profile(main_owner(caller.owner), fields)
        return {"owner": main_owner(caller.owner), "public_name": p.get("display_name") or pseudonym(main_owner(caller.owner)), **p}

    @g.delete("/v1/accounts/me")
    def delete_me(caller=Depends(require_key)):
        """Deletes the email, the profile and the sign-in links, and switches off every login of this person.
        The ledger keeps its receipts: they hold only an owner id, which no longer leads to anyone."""
        aid = people.account_of(caller.owner)
        owners = owners_for(caller.owner) | {caller.owner}
        people.delete(owners, aid)
        for o in owners:
            for rec in st.keys.keys_of(o):
                st.keys.revoke(rec.key_id)
                st.store.revoke_api_key(rec.key_id)
        return {"deleted": True, "note": "Your email, name and sign-in links are deleted and your logins are switched off. "
                                         "Receipts stay on the public ledger with an id that no longer leads to you."}

    # ---------------- C: the business retirement statement ----------------
    @g.get("/v1/accounts/me/statement")
    def statement(account: Literal["business", "personal"] = "business", start: Optional[str] = None, end: Optional[str] = None,
                  format: Literal["csv", "json"] = "csv", caller=Depends(require_key)):
        try:
            lo = date.fromisoformat(start).isoformat() if start else "0000-01-01"
            hi = date.fromisoformat(end).isoformat() if end else "9999-12-31"
        except ValueError:
            raise HTTPException(422, "start and end are dates like 2026-10-01")
        mine = owners_for(caller.owner)
        prof = people.get_profile(main_owner(caller.owner))
        rows = []
        for e in accepted():
            rc = e["receipt"]
            d = str(rc["ts"])[:10]
            if rc.get("owner") not in mine or rc["account"] != account or not lo <= d <= hi:
                continue
            a = st.outbox.get(rc["receipt_id"])
            ap = a.public() if a else {"anchor_status": "pending"}
            s0, s1 = rc.get("serial_start"), rc.get("serial_end")
            rows.append({"date": d, "receipt_id": rc["receipt_id"], "kind": rc["kind"], "grams": rc["grams"], "clt": rc.get("clt"),
                         "target_iso3": rc.get("target_iso3") or "", "batch_id": rc.get("batch_id", ""),
                         "serial_first": s0 if s0 is not None else "", "serial_last": s1 - 1 if s1 is not None else "",
                         "pilot_tonne": s0 // 1_000_000 + 1 if s0 is not None else "", "receipt_hash": e["hash"],
                         "anchor_status": ap.get("anchor_status"), "explorer_url": ap.get("explorer_url") or ""})
        people.count_event(today(), "statement")
        head = {"statement_for": prof.get("business_name") or main_owner(caller.owner), "account": account, "from": lo if start else None,
                "to": hi if end else None, "retirements": len(rows), "total_grams": sum(r["grams"] for r in rows), "units": UNITS_STATUS,
                "verify": f"{public_url}/app#verify", "generated_at": datetime.fromtimestamp(st.now(), timezone.utc).isoformat(timespec="seconds")}
        if format == "json":
            return {**head, "rows": rows}
        buf = io.StringIO()
        buf.write(f"# CarbonLedger retirement statement for {head['statement_for']} ({account} account)\n")
        buf.write(f"# {head['retirements']} retirements, {head['total_grams']} g CO2e in total. {UNITS_STATUS}\n")
        buf.write(f"# Check any line: open {head['verify']} and paste its receipt_id. Generated {head['generated_at']}.\n")
        cols = ["date", "receipt_id", "kind", "grams", "clt", "target_iso3", "batch_id", "serial_first", "serial_last", "pilot_tonne",
                "receipt_hash", "anchor_status", "explorer_url"]
        w = csv.DictWriter(buf, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
        name = f"carbonledger-statement-{account}-{today()}.csv"
        return Response(buf.getvalue(), media_type="text/csv; charset=utf-8", headers={"content-disposition": f'attachment; filename="{name}"'})

    # ---------------- D: weekly leagues ----------------
    @g.get("/v1/league")
    def league(board: Literal["personal", "business"] = "personal", caller=Depends(optional_key)):
        """This week's season (Sunday to Saturday, UTC), ranked by XP from server records. Never by grams."""
        season = week_of(today())
        ends = (date.fromisoformat(season) + timedelta(days=7)).isoformat()
        by: Dict[str, List[dict]] = {}
        countries: Dict[str, dict] = {}
        for e in accepted():
            rc = e["receipt"]
            if week_of(str(rc["ts"])[:10]) != season:
                continue
            if rc["account"] == board:
                by.setdefault(main_owner(rc["owner"]), []).append({"id": rc["receipt_id"], "ts": rc["ts"], "grams": rc["grams"], "kind": rc["kind"]})
            iso = rc.get("target_iso3")
            if iso:
                c = countries.setdefault(iso, {"iso3": iso, "grams": 0, "players": set()})
                c["grams"] += rc["grams"]
                c["players"].add(main_owner(rc["owner"]))
        names, seekers = people.all_display_names(), people.seekers()
        table = sorted(({"owner": o, "xp": xp_of(rs)[0], "grams": sum(r["grams"] for r in rs), "retirements": len(rs)} for o, rs in by.items()),
                       key=lambda r: (-r["xp"], -r["retirements"], r["owner"]))
        me = main_owner(caller.owner) if caller is not None else None
        out = []
        for i, r in enumerate(table, 1):
            if i <= 20 or r["owner"] == me:
                out.append({"rank": i, "name": names.get(r["owner"]) or pseudonym(r["owner"]), "xp": r["xp"], "retirements": r["retirements"],
                            "grams": r["grams"], "you": r["owner"] == me, "seeker": r["owner"] in seekers})
        top_c = sorted(({"iso3": c["iso3"], "grams": c["grams"], "players": len(c["players"])} for c in countries.values()), key=lambda c: -c["grams"])[:10]
        return {"season": season, "ends": ends, "board": board, "players": len(table), "entries": out, "countries": top_c,
                "ranked_by": "XP: habits and actions, not the size of a footprint", "units": UNITS_STATUS}

    return g
