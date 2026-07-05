from __future__ import annotations

import json
import time
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from api.deps import invalidate_case, load_case_resources
from api.utils import df_to_records
from chatbot.case_analytics import build_case_id, fmt_duration
from config.settings import SUPPORTED_EXTENSIONS, UPLOAD_DIR
from extraction.extraction_pipeline import run_extraction_pipeline

router = APIRouter(prefix="/api/extraction", tags=["extraction"])


@router.get("/supported-extensions")
def get_supported_extensions():
    return {"extensions": [ext.lstrip(".") for ext in SUPPORTED_EXTENSIONS]}


@router.post("/run")
async def run_extraction(
    files: list[UploadFile] = File(...),
    account_hints: str = Form("[]"),
    bank_hints: str = Form("[]"),
    case_name: str = Form(""),
    max_ocr_pages: int = Form(3),
):
    """
    Upload one or more bank statement files and run the extraction pipeline.
    `account_hints` / `bank_hints` are JSON-encoded arrays parallel to `files`
    (sent as JSON strings because standard multipart form fields don't carry
    arrays cleanly across all HTTP clients).
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded.")

    try:
        account_hint_list = json.loads(account_hints)
        bank_hint_list = json.loads(bank_hints)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid hints payload: {exc}") from exc

    session_id = build_case_id(case_name)
    session_upload_dir = Path(UPLOAD_DIR) / session_id
    session_upload_dir.mkdir(parents=True, exist_ok=True)

    pipeline_files = []
    for index, upload in enumerate(files):
        dest = session_upload_dir / upload.filename
        contents = await upload.read()
        dest.write_bytes(contents)
        account_hint = (account_hint_list[index] if index < len(account_hint_list) else "") or Path(upload.filename).stem
        bank_hint = (bank_hint_list[index] if index < len(bank_hint_list) else "") or "Unknown Bank"
        pipeline_files.append({
            "file_path": str(dest),
            "account_id": account_hint,
            "bank_name": bank_hint,
        })

    start = time.perf_counter()
    try:
        result = run_extraction_pipeline(
            files=pipeline_files,
            session_id=session_id,
            ingest_to_chromadb=False,
            max_ocr_pages=int(max_ocr_pages),
            persist=True,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Extraction failed after {fmt_duration(time.perf_counter() - start)}: {exc}",
        ) from exc
    elapsed = time.perf_counter() - start

    invalidate_case(session_id)
    resources = load_case_resources(session_id)

    storage_paths = result.get("storage_paths", {}) or {}
    # Keys match api/routers/reports.py's _DOWNLOAD_FILES so the frontend can
    # hit the same /api/cases/{id}/report/downloads/{key} endpoint either way.
    downloads = {
        key: storage_key
        for key, storage_key in [
            ("clean", "clean_csv"),
            ("flagged", "flagged_csv"),
            ("duplicates", "duplicates_csv"),
            ("metadata", "metadata_json"),
        ]
        if storage_paths.get(storage_key) and Path(storage_paths[storage_key]).exists()
    }

    return {
        "session_id": session_id,
        "elapsed_seconds": elapsed,
        "elapsed_label": fmt_duration(elapsed),
        "clean_rows": result.get("clean_rows", 0),
        "flagged_rows": result.get("flagged_rows", 0),
        "files_processed": result.get("files_processed", 0),
        "files_failed": result.get("files_failed", []),
        "per_file": result.get("per_file", []),
        "clean_preview": df_to_records(result.get("clean_df"))[:200],
        "flagged_preview": df_to_records(result.get("flagged_df"))[:200],
        "downloads_available": list(downloads.keys()),
        "indexed_chunks": resources["indexed_count"],
    }
