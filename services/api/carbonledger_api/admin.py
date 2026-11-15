"""Operator levers (DEBT D24, paid 2026-11-15): authority keys only. Suspend a project whose evidence fails, and
re-queue a receipt whose anchor failed. An anchored receipt never moves; the database refuses it too."""
import copy
from typing import Callable

from fastapi import APIRouter, Depends, HTTPException

from carbonledger.auth import KeyRecord
from carbonledger.registry import RegistryError


def admin_router(st, require_key: Callable) -> APIRouter:
    r = APIRouter()
    # ---------------- Operator levers (D24): authority keys only ----------------
    def require_authority(caller: KeyRecord = Depends(require_key)) -> KeyRecord:
        if caller.role != "authority":
            raise HTTPException(403, "Only an authority key can do this. Nothing changed.")
        return caller

    @r.post("/v1/admin/projects/{project_id}/suspend")
    def suspend_project(project_id: str, caller: KeyRecord = Depends(require_authority)):
        """A project whose evidence fails is suspended: from this moment nothing more is issued or retired from it."""
        with st.lock:
            reg = copy.deepcopy(st.registry)
            try:
                reg.suspend_project("trustee", project_id)
            except RegistryError as exc:
                raise HTTPException(404 if exc.code == "UNKNOWN_PROJECT" else 409, f"{exc}. Nothing changed.")
            st.store.update_project_status(project_id, "suspended")
            st.registry = reg
        return {"project_id": project_id, "status": "suspended", "by": caller.owner}

    @r.post("/v1/admin/anchors/{receipt_id}/reanchor")
    def reanchor(receipt_id: str, caller: KeyRecord = Depends(require_authority)):
        """A receipt whose anchor failed goes back in the queue; the worker tries again. An anchored one never moves."""
        try:
            e = st.outbox.reanchor(receipt_id)
        except KeyError:
            raise HTTPException(404, "No such receipt in the anchor queue.")
        except ValueError as exc:
            raise HTTPException(409, f"{exc}. Nothing changed.")
        return {"receipt_id": receipt_id, "anchor_status": e.status, "by": caller.owner}

    return r
