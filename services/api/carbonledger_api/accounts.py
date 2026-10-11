"""An owner's own totals and history, from server records (T20). A browser total is never a score.
These reads need the owner's key: history is personal data. Receipts and the audit stay public by id."""
from typing import Dict, Literal

from fastapi import APIRouter, Depends, HTTPException

from .models import UNITS_STATUS


def account_router(st, require_key) -> APIRouter:
    r = APIRouter(prefix="/v1/accounts/me")

    def _mine():
        return [e for e in st.receipts.entries()]

    @r.get("/totals")
    def totals(caller=Depends(require_key)):
        out: Dict[str, dict] = {a: {"grams": 0, "count": 0, "by_kind": {}} for a in ("personal", "business")}
        for e in _mine():
            rc = e["receipt"]
            if rc.get("owner") != caller.owner:
                continue
            t = out[rc["account"]]
            t["grams"] += rc["grams"]
            t["count"] += 1
            t["by_kind"][rc["kind"]] = t["by_kind"].get(rc["kind"], 0) + rc["grams"]
        return {"owner": caller.owner, "units": UNITS_STATUS, "source": "ledger", **out}

    @r.get("/history")
    def history(account: Literal["personal", "business", "all"] = "all", limit: int = 200, caller=Depends(require_key)):
        if not 1 <= limit <= 1000:
            raise HTTPException(422, "limit must be between 1 and 1000")
        rows = []
        for e in reversed(_mine()):
            rc = e["receipt"]
            if rc.get("owner") != caller.owner or (account != "all" and rc["account"] != account):
                continue
            a = st.outbox.get(rc["receipt_id"])
            rows.append({"id": rc["receipt_id"], "ts": rc["ts"], "account": rc["account"], "grams": rc["grams"], "clt": rc["clt"], "kind": rc["kind"],
                         "label": rc["label"], "target_iso3": rc["target_iso3"], "serial_start": rc["serial_start"], "serial_end": rc["serial_end"],
                         "receipt_hash": e["hash"], **(a.public() if a else {"anchor_status": "pending"})})
            if len(rows) >= limit:
                break
        return {"owner": caller.owner, "units": UNITS_STATUS, "source": "ledger", "records": rows}

    @r.get("/mandates")
    def mandates(caller=Depends(require_key)):
        """The caller's own mandates: cap, used, expiry, agent key, revoked. Owners see theirs; an agent key sees the ones naming it."""
        out = []
        with st.lock:
            for m in st.mandates.values():
                if m.owner == caller.owner or (caller.role == "agent" and m.agent == caller.owner):
                    out.append({"mandate_id": m.id, "owner": m.owner, "agent": m.agent, "cap_g": m.cap_g, "used_g": m.used_g,
                                "expires_at": m.expires_at, "allow_projects": list(m.allow_projects) if m.allow_projects is not None else None,
                                "revoked": m.revoked, "active": not m.revoked and int(st.now()) < m.expires_at})
        return {"owner": caller.owner, "mandates": out}

    return r
