from __future__ import annotations

from fastapi import APIRouter, HTTPException

from api.deps import delete_case, invalidate_case, latest_case_id, load_case_resources
from chatbot.case_registry import list_available_cases

router = APIRouter(prefix="/api/cases", tags=["cases"])


@router.get("")
def get_cases():
    cases = list_available_cases()
    return {"cases": cases, "latest": latest_case_id()}


@router.get("/{case_id}/summary")
def get_case_summary(case_id: str):
    try:
        resources = load_case_resources(case_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    case = resources["case"]
    return {
        "case_id": case_id,
        "case_dir": str(resources["case_dir"]),
        "accounts": len(case["accounts"]),
        "clean_rows": len(case["clean"]),
        "flagged_rows": len(case["flagged"]),
        "indexed_chunks": resources["indexed_count"],
    }


@router.post("/{case_id}/reindex")
def reindex_case(case_id: str):
    try:
        resources = load_case_resources(case_id, force_reindex=True)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"case_id": case_id, "indexed_chunks": resources["indexed_count"]}


@router.delete("/{case_id}")
def remove_case(case_id: str):
    ok, message = delete_case(case_id)
    if not ok:
        raise HTTPException(status_code=400, detail=message)
    return {"ok": True, "message": message, "next_active": latest_case_id()}
