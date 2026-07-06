"""
run_batch.py — Run the extraction pipeline over a folder (or explicit file list) as
ONE independent invocation, per the final-fix prompt Section 4 (Secondary / Primary /
Full-162 are each their own run, never combined into a single pass unless asked).

Usage:
    python3 tools/run_batch.py --scope secondary
    python3 tools/run_batch.py --scope primary
    python3 tools/run_batch.py --scope full
    python3 tools/run_batch.py --files "a.pdf" "b.txt" --session validation
"""
import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from extraction.extraction_pipeline import run_extraction_pipeline  # noqa: E402

BASE = REPO / "original bank statements"
EXTS = {".pdf", ".xlsx", ".xls", ".csv", ".txt", ".docx", ".jpg", ".jpeg", ".png"}


def collect(folder: Path):
    return sorted(p for p in folder.rglob("*") if p.is_file() and p.suffix.lower() in EXTS)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scope", choices=["secondary", "primary", "full"])
    ap.add_argument("--files", nargs="*", help="explicit file paths (overrides --scope)")
    ap.add_argument("--session", default=None)
    ap.add_argument("--max-ocr-pages", type=int, default=None)
    args = ap.parse_args()

    if args.files:
        paths = []
        for f in args.files:
            m = list(BASE.rglob(Path(f).name))
            paths.append(m[0] if m else Path(f))
        session = args.session or "validation"
        folders = ["explicit"]
    else:
        if args.scope == "secondary":
            paths = collect(BASE / "Secondary"); folders = ["Secondary"]
        elif args.scope == "primary":
            paths = collect(BASE / "primary"); folders = ["primary"]
        else:
            paths = collect(BASE / "Secondary") + collect(BASE / "primary")
            folders = ["Secondary", "primary"]
        session = args.session or f"batch_{args.scope}"

    files = [{"file_path": str(p), "account_id": p.stem, "bank_name": ""} for p in paths]
    print(f"[run_batch] scope={folders} files={len(files)} session={session}", flush=True)

    result = run_extraction_pipeline(
        files=files, session_id=session, ingest_to_chromadb=False,
        max_ocr_pages=args.max_ocr_pages, persist=True,
    )
    sp = result.get("storage_paths", {}) or {}
    folder = sp.get("folder", "")
    # Tag the report with explicit scope so the three batches are never confused.
    if folder:
        rp = Path(folder) / "extraction_summary_report.json"
        if rp.exists():
            rep = json.loads(rp.read_text())
            rep["scope_manifest"] = {"scope": session, "folders": folders, "file_count": len(files)}
            rp.write_text(json.dumps(rep, indent=2))
    print(f"\n[run_batch] DONE: clean={result['clean_rows']} flagged={result['flagged_rows']} "
          f"files_processed={result['files_processed']} failed={len(result['files_failed'])}", flush=True)
    print(f"[run_batch] output folder: {folder}", flush=True)


if __name__ == "__main__":
    main()
