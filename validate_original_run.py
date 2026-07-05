#!/usr/bin/env python3
"""
validate_original_run.py — Full end-to-end PRODUCTION run over the original bank-statement
dataset, for later manual validation.

This is an EXECUTION / VALIDATION driver only. It calls the exact same production entry
points the end-user app (app.py) triggers, in the exact production order:

    Original statements → run_extraction_pipeline → AnalysisPipeline → build_report → outputs

It does NOT modify any threshold, detector, scoring, reconstruction, or output. Each phase is
wrapped so a recoverable error is logged and the run continues. It emits a complete execution
summary + error summary + statistics for validation.

Usage:
    python validate_original_run.py                 # default dataset + report on
    python validate_original_run.py --no-report
    python validate_original_run.py --dataset "DATASET FOLDER/original bank statements"

Team: Survey Corps | CIDECODE Hackathon 2026 | CID Karnataka
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

SUPPORTED = {".pdf", ".xlsx", ".xls", ".csv", ".txt", ".docx", ".jpg", ".jpeg", ".png"}
# Case-insensitive filesystems make "Secondary" and "secondary" the same dir; discover_files
# de-dups by resolved path, so listing both is harmless.
SUBFOLDERS = ["primary", "Secondary", "secondary"]


def _default_dataset() -> Path:
    """Locate '<something>/original bank statements' robustly (the top folder name has a
    trailing space on disk: 'DATASET FOLDER '). Falls back to a fixed guess."""
    for d in sorted(ROOT.iterdir()):
        if d.is_dir() and (d / "original bank statements").is_dir():
            return (d / "original bank statements").resolve()
    return (ROOT / "DATASET FOLDER " / "original bank statements")


DEFAULT_DATASET = _default_dataset()


def discover_files(dataset: Path) -> tuple[list[dict], list[dict]]:
    """Return (files_to_process, skipped) across the dataset subfolders."""
    files: list[dict] = []
    skipped: list[dict] = []
    seen: set[str] = set()
    seen_dirs: set[str] = set()
    for sub in SUBFOLDERS:
        d = dataset / sub
        if not d.is_dir():
            continue
        # On a case-insensitive filesystem "Secondary" and "secondary" are the SAME physical
        # directory; skip re-scanning it (path.resolve() preserves case on macOS, so compare
        # case-folded) to avoid processing every file twice.
        dir_key = str(d.resolve()).casefold()
        if dir_key in seen_dirs:
            continue
        seen_dirs.add(dir_key)
        for p in sorted(d.iterdir()):
            if not p.is_file():
                continue
            name = p.name
            if name.startswith(".") or name.startswith("._") or "__MACOSX" in str(p):
                skipped.append({"file": name, "reason": "hidden/system file"})
                continue
            if p.suffix.lower() not in SUPPORTED:
                skipped.append({"file": name, "reason": f"unsupported extension {p.suffix}"})
                continue
            try:
                if p.stat().st_size == 0:
                    skipped.append({"file": name, "reason": "empty file (0 bytes)"})
                    continue
            except OSError as e:
                skipped.append({"file": name, "reason": f"unreadable: {e}"})
                continue
            key = str(p.resolve())
            if key in seen:
                continue
            seen.add(key)
            files.append({"file_path": str(p), "account_id": p.stem, "bank_name": "Unknown Bank",
                          "subfolder": sub})
    return files, skipped


def classify_failure(record: dict) -> str:
    """Best-effort root cause for a per-file extraction failure/under-extraction."""
    err = str(record.get("error", "")).lower()
    if "preflight" in err or "not_found" in err or "empty" in err:
        return "file missing/empty on disk"
    if "password" in err or "encrypt" in err:
        return "password-protected / encrypted file"
    if "unsupported" in err:
        return "unsupported/unknown route"
    if record.get("zero_row_status") == "functional_failure":
        return "readable but under-extracted (parser/LLM fallback produced no rows)"
    if record.get("status") == "FAILED":
        return "extraction exception (see exception text)"
    return "n/a"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", default=str(DEFAULT_DATASET))
    ap.add_argument("--no-report", action="store_true")
    ap.add_argument("--languages", nargs="*", default=["en"])
    ap.add_argument("--session", default=None)
    args = ap.parse_args()

    dataset = Path(args.dataset).expanduser().resolve()
    session_id = args.session or datetime.now().strftime("validation_original_%Y%m%d_%H%M%S")
    out_dir = ROOT / "outputs" / "validation_runs" / session_id
    out_dir.mkdir(parents=True, exist_ok=True)
    log_lines: list[str] = []

    def log(msg: str) -> None:
        line = f"[{time.strftime('%H:%M:%S')}] {msg}"
        print(line, flush=True)
        log_lines.append(line)

    summary: dict = {
        "session_id": session_id,
        "dataset": str(dataset),
        "started_at": datetime.now().isoformat(),
        "phases": {},
        "failures": [],
        "overall_status": "started",
    }

    run_start = time.perf_counter()
    log(f"VALIDATION RUN {session_id}")
    log(f"Dataset: {dataset}")

    # ── Discovery ─────────────────────────────────────────────────────────────
    files, skipped = discover_files(dataset)
    summary["files_discovered"] = len(files) + len(skipped)
    summary["files_to_process"] = len(files)
    summary["files_skipped"] = skipped
    by_fmt: dict[str, int] = {}
    for f in files:
        by_fmt[Path(f["file_path"]).suffix.lower()] = by_fmt.get(Path(f["file_path"]).suffix.lower(), 0) + 1
    summary["format_breakdown"] = by_fmt
    log(f"Discovered {summary['files_discovered']} files "
        f"({len(files)} to process, {len(skipped)} skipped). Formats: {by_fmt}")

    # ── PHASE 1: EXTRACTION ───────────────────────────────────────────────────
    log("PHASE 1/3 — EXTRACTION starting ...")
    p1 = time.perf_counter()
    extraction_dir = ROOT / "outputs" / "extractions" / session_id
    ext_result = None
    try:
        from extraction.extraction_pipeline import run_extraction_pipeline
        ext_result = run_extraction_pipeline(
            files=[{k: f[k] for k in ("file_path", "account_id", "bank_name")} for f in files],
            session_id=session_id, ingest_to_chromadb=False, max_ocr_pages=None, persist=True)
    except Exception as e:
        summary["phases"]["extraction"] = {"status": "FAILED", "exception": repr(e),
                                            "traceback": traceback.format_exc()[-2000:]}
        summary["failures"].append({"filename": "(whole extraction phase)", "phase": "extraction",
                                    "exception": repr(e), "root_cause": "extraction phase crashed"})
        log(f"EXTRACTION PHASE CRASHED: {e}")
        summary["overall_status"] = "extraction_failed"
        _write(out_dir, summary, log_lines)
        return 1

    per_file = ext_result.get("per_file", []) or []
    failed = [r for r in per_file if r.get("status") == "FAILED"]
    functional_failures = [r for r in per_file if r.get("zero_row_status") == "functional_failure"]
    succeeded = [r for r in per_file if r.get("status") not in ("FAILED",)]
    for r in failed + functional_failures:
        summary["failures"].append({
            "filename": r.get("file"), "phase": "extraction",
            "exception": r.get("error", r.get("zero_row_reason", "under-extracted")),
            "root_cause": classify_failure(r)})
    summary["phases"]["extraction"] = {
        "status": "OK",
        "elapsed_seconds": round(time.perf_counter() - p1, 1),
        "files_processed": ext_result.get("files_processed", 0),
        "files_failed_count": len(ext_result.get("files_failed", []) or []),
        "files_failed": ext_result.get("files_failed", []),
        "files_functional_failure_count": len(functional_failures),
        "clean_rows": ext_result.get("clean_rows", 0),
        "flagged_rows": ext_result.get("flagged_rows", 0),
        "total_rows": ext_result.get("total_rows", 0),
        "total_llm_calls": sum(r.get("llm_calls", 0) for r in per_file),
        "missing_key_warnings": ext_result.get("missing_key_warnings", []),
        "tier_by_file": {r.get("file"): r.get("tier") for r in per_file if r.get("tier")},
        "reconciliation_by_file": {r.get("file"): r.get("reconciliation_rate")
                                   for r in per_file if "reconciliation_rate" in r},
        "extraction_output_dir": str(extraction_dir),
    }
    log(f"EXTRACTION done in {summary['phases']['extraction']['elapsed_seconds']}s: "
        f"{ext_result.get('files_processed',0)} processed, {len(failed)} failed, "
        f"{len(functional_failures)} under-extracted, {ext_result.get('clean_rows',0)} clean rows, "
        f"{summary['phases']['extraction']['total_llm_calls']} LLM calls.")

    # ── PHASE 2: ANALYSIS ─────────────────────────────────────────────────────
    log("PHASE 2/3 — ANALYSIS starting ...")
    p2 = time.perf_counter()
    analysis_dir = ROOT / "analysis" / "outputs" / session_id
    analysis_payload = None
    try:
        from analysis.analysis_engine.config import AnalysisConfig
        from analysis.analysis_engine.pipeline import AnalysisPipeline
        # Same config the end-user app triggers (LLM fallback enabled, run-budget capped).
        result = AnalysisPipeline(input_path=extraction_dir, output_dir=analysis_dir,
                                  config=AnalysisConfig()).run()
        analysis_payload = result.to_dict()
    except Exception as e:
        summary["phases"]["analysis"] = {"status": "FAILED", "exception": repr(e),
                                         "elapsed_seconds": round(time.perf_counter() - p2, 1),
                                         "traceback": traceback.format_exc()[-2000:]}
        summary["failures"].append({"filename": "(whole analysis phase)", "phase": "analysis",
                                    "exception": repr(e), "root_cause": "analysis phase crashed"})
        log(f"ANALYSIS PHASE CRASHED: {e}")
        summary["overall_status"] = "analysis_failed"
        _write(out_dir, summary, log_lines)
        return 1

    fbp = analysis_payload.get("findings_by_pattern", {}) or {}
    finding_counts = {k: len(v) for k, v in fbp.items()}
    baseline = analysis_payload.get("baseline_summary", {}) or {}
    case_structure = analysis_payload.get("case_structure", {}) or {}
    summary["phases"]["analysis"] = {
        "status": "OK",
        "elapsed_seconds": round(time.perf_counter() - p2, 1),
        "accounts": baseline.get("account_count", 0),
        "eligible_rows": baseline.get("row_counts", {}).get("eligible", 0),
        "excluded_rows": baseline.get("row_counts", {}).get("excluded", 0),
        "graph_nodes": analysis_payload.get("graph_summary", {}).get("node_count", 0),
        "graph_edges": analysis_payload.get("graph_summary", {}).get("edge_count", 0),
        "total_findings": sum(finding_counts.values()),
        "finding_counts_by_pattern": finding_counts,
        "suspicious_accounts": len(analysis_payload.get("suspicious_accounts", []) or []),
        "weak_signal_accounts": len(analysis_payload.get("weak_signal_accounts", []) or []),
        "clusters": case_structure.get("cluster_count", 0),
        "counterparty_resolution_rate": (analysis_payload.get("counterparty_resolution", {}) or {}).get("resolution_rate_percent", 0),
        "llm_status": analysis_payload.get("run_metadata", {}).get("llm_status", ""),
        "llm_call_count": analysis_payload.get("run_metadata", {}).get("llm_call_count", 0),
        "analysis_output_dir": str(analysis_dir),
    }
    log(f"ANALYSIS done in {summary['phases']['analysis']['elapsed_seconds']}s: "
        f"{summary['phases']['analysis']['accounts']} accounts, "
        f"{summary['phases']['analysis']['total_findings']} findings, "
        f"{summary['phases']['analysis']['suspicious_accounts']} suspicious, "
        f"{summary['phases']['analysis']['clusters']} clusters, "
        f"graph {summary['phases']['analysis']['graph_nodes']}n/{summary['phases']['analysis']['graph_edges']}e.")

    # ── PHASE 3: REPORT ───────────────────────────────────────────────────────
    reports: list[dict] = []
    if not args.no_report:
        venv_py = ROOT / ".report_venv" / "bin" / "python"
        for lang in args.languages:
            log(f"PHASE 3/3 — REPORT ({lang}) starting ...")
            p3 = time.perf_counter()
            name = "investigation_report_kn.pdf" if lang == "kn" else "investigation_report.pdf"
            out_pdf = analysis_dir / name
            entry = {"language": lang, "pdf": str(out_pdf)}
            if not venv_py.exists():
                entry.update({"status": "SKIPPED", "reason": ".report_venv missing (see setup in DELIVERABLES.md)"})
                log("REPORT skipped: .report_venv not installed.")
            else:
                try:
                    proc = subprocess.run(
                        [str(venv_py), str(ROOT / "reporting" / "build_report.py"),
                         "--run-id", session_id, "--ai", "--out", str(out_pdf), "--language", lang, "--save-html"],
                        cwd=str(ROOT), capture_output=True, text=True, timeout=600)
                    html = out_pdf.with_suffix(".html")
                    if proc.returncode == 0 and out_pdf.exists():
                        entry["status"] = "OK_PDF"
                    elif html.exists():
                        entry["status"] = "OK_HTML_FALLBACK"
                        entry["html"] = str(html)
                    else:
                        entry["status"] = "FAILED"
                        entry["error"] = (proc.stderr or proc.stdout or "")[-600:]
                        summary["failures"].append({"filename": name, "phase": "report",
                                                    "exception": entry["error"], "root_cause": "report render failed"})
                    entry["stdout_tail"] = (proc.stdout or "")[-400:]
                except Exception as e:
                    entry.update({"status": "FAILED", "error": repr(e)})
                    summary["failures"].append({"filename": name, "phase": "report",
                                                "exception": repr(e), "root_cause": "report subprocess crashed"})
            entry["elapsed_seconds"] = round(time.perf_counter() - p3, 1)
            reports.append(entry)
            log(f"REPORT ({lang}) -> {entry.get('status')} ({entry['elapsed_seconds']}s)")
    summary["phases"]["report"] = {"status": "OK" if reports else "SKIPPED", "reports": reports}

    # ── Artifact inventory ────────────────────────────────────────────────────
    def _inventory(d: Path) -> list[str]:
        return sorted(str(p.relative_to(ROOT)) for p in d.rglob("*") if p.is_file()) if d.exists() else []
    summary["artifacts"] = {
        "extraction": _inventory(extraction_dir),
        "analysis": _inventory(analysis_dir),
    }

    summary["total_elapsed_seconds"] = round(time.perf_counter() - run_start, 1)
    summary["finished_at"] = datetime.now().isoformat()
    summary["overall_status"] = "COMPLETED"
    log(f"VALIDATION RUN COMPLETE in {summary['total_elapsed_seconds']}s. Status: COMPLETED.")
    _write(out_dir, summary, log_lines)
    log(f"Deliverables written under: {out_dir}")
    return 0


def _write(out_dir: Path, summary: dict, log_lines: list[str]) -> None:
    (out_dir / "execution_summary.json").write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    (out_dir / "error_summary.json").write_text(
        json.dumps(summary.get("failures", []), indent=2, default=str), encoding="utf-8")
    (out_dir / "execution_log.txt").write_text("\n".join(log_lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
