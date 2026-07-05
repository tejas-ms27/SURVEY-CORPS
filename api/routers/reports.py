from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, HTMLResponse

from api.deps import load_case_resources
from chatbot.case_analytics import build_case_report_html

router = APIRouter(prefix="/api/cases/{case_id}/report", tags=["reports"])

_DOWNLOAD_FILES = {
    "clean": ("clean_transactions.csv", "text/csv"),
    "flagged": ("flagged_transactions.csv", "text/csv"),
    "duplicates": ("duplicates.csv", "text/csv"),
    "metadata": ("metadata.json", "application/json"),
}


def _resources(case_id: str):
    try:
        return load_case_resources(case_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("", response_class=HTMLResponse)
def get_report_html(case_id: str):
    resources = _resources(case_id)
    return HTMLResponse(build_case_report_html(case_id, resources))


@router.get("/downloads")
def list_downloads(case_id: str):
    resources = _resources(case_id)
    case_dir = Path(resources["case_dir"])
    available = {
        key: filename
        for key, (filename, _mime) in _DOWNLOAD_FILES.items()
        if (case_dir / filename).exists()
    }
    return {"available": available}


@router.get("/downloads/{file_key}")
def download_file(case_id: str, file_key: str):
    if file_key not in _DOWNLOAD_FILES:
        raise HTTPException(status_code=404, detail="Unknown file key.")
    resources = _resources(case_id)
    filename, mime = _DOWNLOAD_FILES[file_key]
    path = Path(resources["case_dir"]) / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"{filename} not found for this case.")
    return FileResponse(path, media_type=mime, filename=filename)
