#!/usr/bin/env python3
"""
run_case.py — One-command, end-to-end run for a COMPLETELY UNSEEN case.

    python run_case.py <folder-with-statements>
    python run_case.py <folder>/statements
    python run_case.py file1.pdf file2.csv file3.xlsx
    python run_case.py <folder> --report            # also build the PDF/HTML report
    python run_case.py <folder> --report --language kn
    python run_case.py <folder> --no-llm            # fully deterministic analysis

This is the live-demo path: extraction -> fraud detection -> (optional) report, on any
folder of bank statements, with NO dependency on the synthetic dataset or any ground truth.
It reads account identity only from the statements themselves and never hardcodes anything.

Team: Survey Corps | CIDECODE Hackathon 2026 | CID Karnataka
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

STATEMENT_EXTS = {".pdf", ".xlsx", ".xls", ".csv", ".txt", ".docx", ".jpg", ".jpeg", ".png"}


def _collect_files(inputs: list[str]) -> list[dict[str, str]]:
    """Resolve the CLI inputs into a flat list of statement files.

    Accepts: a folder (uses its `statements/` subfolder if present, else the folder
    itself), or an explicit list of files. Only known statement extensions are kept.
    """
    files: list[Path] = []
    for raw in inputs:
        p = Path(raw).expanduser()
        if p.is_dir():
            base = p / "statements" if (p / "statements").is_dir() else p
            files.extend(sorted(c for c in base.iterdir() if c.is_file() and c.suffix.lower() in STATEMENT_EXTS))
        elif p.is_file() and p.suffix.lower() in STATEMENT_EXTS:
            files.append(p)
    # de-dup, preserve order
    seen: set[str] = set()
    out: list[dict[str, str]] = []
    for p in files:
        key = str(p.resolve())
        if key in seen:
            continue
        seen.add(key)
        out.append({"file_path": str(p), "account_id": p.stem, "bank_name": "Unknown Bank"})
    return out


def _build_report(session_id: str, analysis_dir: Path, language: str) -> tuple[Path | None, str]:
    """Generate the investigation report via the reporting venv, with graceful fallback."""
    venv_py = ROOT / ".report_venv" / "bin" / "python"
    if not venv_py.exists():
        return None, ("Report renderer venv missing. One-time setup:\n"
                      "  python3 -m venv .report_venv && .report_venv/bin/pip install "
                      "playwright jinja2 groq && .report_venv/bin/python -m playwright install chromium")
    out_pdf = analysis_dir / ("investigation_report_kn.pdf" if language == "kn" else "investigation_report.pdf")
    cmd = [str(venv_py), str(ROOT / "reporting" / "build_report.py"),
           "--run-id", session_id, "--ai", "--out", str(out_pdf), "--language", language]
    try:
        proc = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True, timeout=300)
    except subprocess.TimeoutExpired:
        return None, "Report generation timed out."
    # build_report writes HTML alongside on PDF failure (Phase 5), so check both.
    html = out_pdf.with_suffix(".html")
    if out_pdf.exists():
        return out_pdf, "PDF report generated."
    if html.exists():
        return html, "PDF unavailable — HTML report preserved instead."
    return None, (proc.stderr or proc.stdout or "unknown error")[-800:]


def main() -> int:
    ap = argparse.ArgumentParser(description="End-to-end run for an unseen case.")
    ap.add_argument("inputs", nargs="+", help="A folder of statements, a statements/ dir, or explicit files.")
    ap.add_argument("--session", default=None, help="Session id (default: run_<timestamp>).")
    ap.add_argument("--report", action="store_true", help="Also build the investigation report.")
    ap.add_argument("--language", choices=["en", "kn"], default="en")
    ap.add_argument("--no-llm", action="store_true", help="Deterministic analysis (no LLM narration/assist).")
    args = ap.parse_args()

    files = _collect_files(args.inputs)
    if not files:
        print("No statement files found in the given input(s).", file=sys.stderr)
        return 2

    session_id = args.session or datetime.now().strftime("run_%Y%m%d_%H%M%S")
    print(f"[run_case] session={session_id}  files={len(files)}")

    from extraction.extraction_pipeline import run_extraction_pipeline
    from analysis.analysis_engine.config import AnalysisConfig
    from analysis.analysis_engine.pipeline import AnalysisPipeline

    t0 = time.perf_counter()
    ext = run_extraction_pipeline(files=files, session_id=session_id, ingest_to_chromadb=False,
                                  max_ocr_pages=None, persist=True)
    extraction_dir = Path(ext.get("storage_paths", {}).get("folder", ROOT / "outputs" / "extractions" / session_id))
    print(f"[run_case] extraction: {ext.get('clean_rows',0)} clean / {ext.get('flagged_rows',0)} flagged "
          f"/ {len(ext.get('files_failed',[]))} failed  ({time.perf_counter()-t0:.1f}s)")
    if ext.get("missing_key_warnings"):
        for w in ext["missing_key_warnings"]:
            print(f"[run_case] WARN: {w}")
    if ext.get("files_failed"):
        print(f"[run_case] WARN: files failed extraction: {ext['files_failed']}")

    analysis_dir = ROOT / "analysis" / "outputs" / session_id
    t1 = time.perf_counter()
    result = AnalysisPipeline(
        input_path=extraction_dir,
        output_dir=analysis_dir,
        config=AnalysisConfig(enable_llm_fallback=not args.no_llm),
    ).run()
    payload = result.to_dict()
    print(f"[run_case] analysis: {len(payload.get('suspicious_accounts',[]))} suspicious account(s), "
          f"{payload.get('graph_summary',{}).get('edge_count',0)} money-flow edges  ({time.perf_counter()-t1:.1f}s)")
    if payload.get("case_summary"):
        print(f"[run_case] case: {payload['case_summary']}")
    for acc in payload.get("suspicious_accounts", [])[:5]:
        print(f"          - {acc.get('account_id')}: score={acc.get('total_score')} "
              f"patterns={acc.get('distinct_pattern_count')}")

    if args.report:
        pdf, msg = _build_report(session_id, analysis_dir, args.language)
        print(f"[run_case] report: {msg}" + (f"  -> {pdf}" if pdf else ""))

    print(f"[run_case] outputs:\n  extraction: {extraction_dir}\n  analysis:   {analysis_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
