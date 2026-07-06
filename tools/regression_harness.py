"""
regression_harness.py — Offline, deterministic regression harness (Issue 6).

WHY THIS EXISTS
    Rule 2 of the engineering contract forbids any change that makes even one
    previously-working statement worse. To enforce that we need a repeatable,
    side-effect-free measurement of the extraction engine over the WHOLE corpus,
    captured BEFORE a change and compared AFTER it.

WHAT IT MEASURES (per the contract's required report)
    Total Statements, Passed, Failed, Missing Holder, Missing Account,
    Missing IFSC, Balance Mismatches, Flagged Rows, Extracted Rows, Lost Rows,
    and — when a saved baseline exists — New Regressions.

WHY IT IS OFFLINE / DETERMINISTIC
    It exercises only the cheap deterministic Tier-2 text path
    (digital-PDF / DOCX / TXT) and the deterministic Excel/CSV column path —
    exactly the layers the page-break, metadata and balance issues live in.
    It makes NO LLM calls, so it costs zero API quota and produces identical
    numbers on every run. Scanned PDFs / images (which require the vision model)
    are routed-and-skipped, never silently dropped from the report.

USAGE
    python3 tools/regression_harness.py                 # run + compare to baseline
    python3 tools/regression_harness.py --save-baseline # run + overwrite baseline
    python3 tools/regression_harness.py --json out.json  # also dump raw per-file JSON

    Exit code is non-zero if a NEW REGRESSION is detected (CI-friendly).

Team: Survey Corps | CIDECODE Hackathon 2026 | CID Karnataka
"""

import argparse
import hashlib
import json
import sys
import traceback
from pathlib import Path

# Make the repo root importable when run as a script.
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import logging
logging.disable(logging.CRITICAL)  # keep the harness output clean

import pandas as pd  # noqa: E402

from extraction.router import route_file  # noqa: E402
from extraction.extractor_digital_pdf import extract_text_from_digital_pdf  # noqa: E402
from extraction.account_extractor import extract_account_details_from_text  # noqa: E402
from extraction.standardiser import (  # noqa: E402
    standardise_digital_pdf_transactions,
    standardise_dataframe_direct,
    count_transaction_like_lines,
)
from extraction.validator import grade_parse, validate_and_clean  # noqa: E402

try:
    from extraction.extractor_docx import extract_text_from_docx, extract_text_from_txt
except Exception:  # pragma: no cover - optional deps
    extract_text_from_docx = extract_text_from_txt = None

try:
    from extraction.extractor_excel_csv import extract_dataframe_from_excel_csv
except Exception:  # pragma: no cover - optional deps
    extract_dataframe_from_excel_csv = None

# Corpora that make up the regression set. Anything matching these roots is graded.
CORPUS_DIRS = [
    REPO_ROOT / "original bank statements",
    REPO_ROOT / "synthetic_dataset_full",
    REPO_ROOT / "synthetic_dataset_full_mentoring",
]
BASELINE_PATH = REPO_ROOT / "tools" / "regression_baselines" / "baseline.json"
# Extracted-text cache: pdfplumber is slow (10-46s on the largest PDFs), and text
# extraction is pure input (it never changes when the PARSER changes), so caching it
# keyed by path+mtime+size makes every rerun after a parser edit near-instant. The
# cache is keyed on file identity, so editing a statement file invalidates its entry.
_TEXTCACHE_DIR = REPO_ROOT / "tools" / "regression_baselines" / ".textcache"

# Routes the OFFLINE harness can grade deterministically (no LLM / no vision).
_TEXT_ROUTES = {"pdf_digital", "docx", "text"}


def _cached_text(path: Path, extract_fn):
    """Returns extracted text for `path`, caching it on disk keyed by path+mtime+size."""
    st = path.stat()
    key = hashlib.md5(f"{path}|{st.st_mtime_ns}|{st.st_size}".encode()).hexdigest()
    cache_file = _TEXTCACHE_DIR / f"{key}.txt"
    if cache_file.exists():
        return cache_file.read_text(encoding="utf-8", errors="replace")
    text = extract_fn(str(path)) or ""
    _TEXTCACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file.write_text(text, encoding="utf-8", errors="replace")
    return text


# Reference / answer-key artifacts shipped alongside the statements that the real
# pipeline NEVER processes (phase1.md is explicit about this). Grading them pollutes
# the metrics (e.g. transactions_master.csv is a 275k-row ledger, not a statement).
# Matched on the lowercased filename stem — generic artifact names, not bank-specific.
_NON_STATEMENT_NAMES = (
    "transactions_master", "accounts_master", "case_briefs",
    "generation_summary", "ground_truth", "readme", "notes",
)


def _is_statement_file(p: Path) -> bool:
    name = p.name.lower()
    return not any(tok in name for tok in _NON_STATEMENT_NAMES)


def _collect_files():
    """Every gradeable statement file under the corpus dirs, sorted for stability."""
    exts = {".pdf", ".docx", ".txt", ".xlsx", ".xls", ".csv"}
    files = []
    for root in CORPUS_DIRS:
        if not root.exists():
            continue
        for p in sorted(root.rglob("*")):
            if p.is_file() and p.suffix.lower() in exts and _is_statement_file(p):
                files.append(p)
    return files


def _grade_text(raw_text, name):
    """Deterministic Tier-2 parse + grade for a text source. Returns a metrics dict."""
    details = extract_account_details_from_text(raw_text or "")
    expected = count_transaction_like_lines(raw_text or "")
    df = standardise_digital_pdf_transactions(raw_text or "", "ACC", details.get("bank_name") or "Bank",
                                              details.get("opening_balance", "") or "", {})
    return _finish_grade(df, details, expected)


def _grade_excel(path, name):
    """Deterministic Excel/CSV column-path parse + grade (no LLM). Metrics dict."""
    if extract_dataframe_from_excel_csv is None:
        return None
    raw_df = extract_dataframe_from_excel_csv(str(path), "ACC", "Bank")
    details = (raw_df.attrs.get("statement_metadata", {}) or {}) if raw_df is not None else {}
    inferred = (raw_df.attrs.get("inferred_column_map", {}) or {}) if raw_df is not None else {}
    core = {k: v for k, v in inferred.items()
            if k in ("date", "narration", "debit", "credit", "balance")}
    if raw_df is None or raw_df.empty or not core:
        # No deterministic map → the real pipeline would call the LLM here; the
        # offline harness records it as not-deterministically-gradeable.
        return None
    df = standardise_dataframe_direct(raw_df, core, "ACC", details.get("bank_name") or "Bank")
    return _finish_grade(df, details, len(raw_df))


def _finish_grade(df, details, expected):
    """Shared tail: grade the parse and run validation; return a metrics dict."""
    grade = grade_parse(df, expected_rows=expected or None)
    # Flip a detected newest-first parse before validation (mirrors the pipeline).
    val_df = df.iloc[::-1].reset_index(drop=True) if grade.get("ordering") == "newest_first" else df
    if val_df is not None and not val_df.empty:
        val_df = val_df.copy()
        val_df["Account_ID"] = details.get("account_number") or "ACC"
    clean_df, flagged_df = validate_and_clean(val_df)
    balance_mismatch = int((flagged_df.get("flag_reason") == "balance_mismatch").sum()) \
        if not flagged_df.empty else 0
    # Rows the narration-bloat SAFETY NET surfaced. These were silently "clean" before
    # the net existed despite holding multiple swallowed transactions, so moving them
    # to flagged is a CORRECTION (a pre-existing defect made visible), not lost data —
    # the diff counts (clean + bloat_flagged) so it is never read as a regression.
    bloat_flagged = int((flagged_df.get("flag_reason")
                         == "narration_contains_multiple_transactions").sum()) \
        if not flagged_df.empty else 0
    # Issue 7: capture the validator's per-cause diagnosis breakdown for the report.
    diagnosis = {}
    if not flagged_df.empty and "mismatch_diagnosis" in flagged_df.columns:
        mism = flagged_df[flagged_df["flag_reason"] == "balance_mismatch"]
        diagnosis_series = mism["mismatch_diagnosis"].replace("", "unclassified")
        diagnosis = {str(k): int(v) for k, v in diagnosis_series.value_counts().items()}
    return {
        "mismatch_diagnosis": diagnosis,
        "expected_txn_lines": int(expected or 0),
        "parsed_rows": int(len(df)),
        "reconciliation_rate": round(float(grade["reconciliation_rate"]), 4),
        "completeness_ratio": round(float(grade["completeness_ratio"]), 4),
        "ordering": grade["ordering"],
        "has_balance_column": bool(grade["has_balance_column"]),
        "verdict": grade["verdict"],
        "clean_rows": int(len(clean_df)),
        "flagged_rows": int(len(flagged_df)),
        "balance_mismatch_rows": balance_mismatch,
        "bloat_flagged_rows": bloat_flagged,
        "missing_holder": not bool((details or {}).get("account_holder")),
        "missing_account": not bool((details or {}).get("account_number")),
        "missing_ifsc": not bool((details or {}).get("ifsc_code")),
    }


def run():
    """Grades every gradeable file and returns {per_file: {...}, summary: {...}}."""
    per_file = {}
    for path in _collect_files():
        rel = str(path.relative_to(REPO_ROOT))
        try:
            route = route_file(str(path))
        except Exception as e:
            per_file[rel] = {"route": "ERROR", "status": "route_failed", "error": str(e)}
            continue

        try:
            if route in _TEXT_ROUTES:
                if route == "pdf_digital":
                    text = _cached_text(path, extract_text_from_digital_pdf)
                elif route == "docx" and extract_text_from_docx:
                    text = _cached_text(path, extract_text_from_docx)
                elif route == "text" and extract_text_from_txt:
                    text = _cached_text(path, extract_text_from_txt)
                else:
                    per_file[rel] = {"route": route, "status": "skipped_no_extractor"}
                    continue
                metrics = _grade_text(text, path.name)
            elif route == "excel_csv":
                metrics = _grade_excel(path, path.name)
                if metrics is None:
                    per_file[rel] = {"route": route, "status": "skipped_needs_llm"}
                    continue
            else:
                # pdf_scanned / image → needs the vision model; not offline-gradeable.
                per_file[rel] = {"route": route, "status": "skipped_needs_vision"}
                continue
            metrics["route"] = route
            metrics["status"] = "graded"
            per_file[rel] = metrics
        except Exception as e:
            per_file[rel] = {"route": route, "status": "error",
                             "error": f"{e}", "trace": traceback.format_exc(limit=3)}

    graded = {k: v for k, v in per_file.items() if v.get("status") == "graded"}
    summary = {
        "total_files": len(per_file),
        "graded": len(graded),
        "skipped": sum(1 for v in per_file.values() if str(v.get("status", "")).startswith("skipped")),
        "errored": sum(1 for v in per_file.values() if v.get("status") in ("error", "route_failed")),
        "passed": sum(1 for v in graded.values() if v["verdict"] == "PASS"),
        "failed": sum(1 for v in graded.values() if v["verdict"] == "FAIL"),
        "missing_holder": sum(1 for v in graded.values() if v["missing_holder"]),
        "missing_account": sum(1 for v in graded.values() if v["missing_account"]),
        "missing_ifsc": sum(1 for v in graded.values() if v["missing_ifsc"]),
        "balance_mismatch_rows": sum(v["balance_mismatch_rows"] for v in graded.values()),
        "flagged_rows": sum(v["flagged_rows"] for v in graded.values()),
        "extracted_rows": sum(v["parsed_rows"] for v in graded.values()),
        "clean_rows": sum(v["clean_rows"] for v in graded.values()),
    }
    # Aggregate the validator's mismatch-cause diagnosis across the corpus (Issue 7).
    diag_totals = {}
    for v in graded.values():
        for cause, cnt in (v.get("mismatch_diagnosis") or {}).items():
            diag_totals[cause] = diag_totals.get(cause, 0) + cnt
    summary["mismatch_diagnosis_breakdown"] = dict(
        sorted(diag_totals.items(), key=lambda kv: -kv[1]))
    return {"per_file": per_file, "summary": summary}


def _diff_against_baseline(current, baseline):
    """
    Returns (regressions, improvements) comparing per-file metrics. A regression is
    any graded file that gets STRICTLY worse on a monitored axis: fewer parsed rows,
    a lower reconciliation rate (beyond rounding), a PASS→FAIL flip, more flagged
    rows, or an identity field that was present before and is now missing.
    """
    regressions, improvements = [], []
    base_files = baseline.get("per_file", {})
    for rel, cur in current["per_file"].items():
        old = base_files.get(rel)
        if not old or old.get("status") != "graded" or cur.get("status") != "graded":
            continue
        reasons = []
        if cur["parsed_rows"] < old["parsed_rows"]:
            reasons.append(f"parsed_rows {old['parsed_rows']}→{cur['parsed_rows']}")
        if cur["reconciliation_rate"] < old["reconciliation_rate"] - 1e-4:
            reasons.append(f"reconcile {old['reconciliation_rate']}→{cur['reconciliation_rate']}")
        if old["verdict"] == "PASS" and cur["verdict"] == "FAIL":
            reasons.append("verdict PASS→FAIL")
        # A flagged-rows increase is only a REGRESSION if we LOST data. We compare
        # (clean + narration-bloat-flagged), because a row moved from silently-clean to
        # bloat-flagged is a correction, not a loss (the row is still present, now
        # honestly flagged). A file extracting MORE rows also is not a regression.
        old_accounted = old["clean_rows"] + old.get("bloat_flagged_rows", 0)
        cur_accounted = cur["clean_rows"] + cur.get("bloat_flagged_rows", 0)
        if cur_accounted < old_accounted:
            reasons.append(f"accounted_rows {old_accounted}→{cur_accounted}")
        for fld in ("missing_holder", "missing_account", "missing_ifsc"):
            if cur[fld] and not old[fld]:
                reasons.append(fld.replace("missing_", "lost_"))
        if reasons:
            regressions.append((rel, reasons))

        gains = []
        if cur["parsed_rows"] > old["parsed_rows"]:
            gains.append(f"parsed_rows {old['parsed_rows']}→{cur['parsed_rows']}")
        if cur["reconciliation_rate"] > old["reconciliation_rate"] + 1e-4:
            gains.append(f"reconcile {old['reconciliation_rate']}→{cur['reconciliation_rate']}")
        if old["verdict"] == "FAIL" and cur["verdict"] == "PASS":
            gains.append("verdict FAIL→PASS")
        if cur["flagged_rows"] < old["flagged_rows"]:
            gains.append(f"flagged {old['flagged_rows']}→{cur['flagged_rows']}")
        for fld in ("missing_holder", "missing_account", "missing_ifsc"):
            if old[fld] and not cur[fld]:
                gains.append(fld.replace("missing_", "gained_"))
        if gains:
            improvements.append((rel, gains))
    return regressions, improvements


def _print_summary(s):
    print("\n=== REGRESSION SUMMARY (offline, deterministic) ===")
    print(f"  Total files          : {s['total_files']}")
    print(f"  Graded               : {s['graded']}   "
          f"(skipped: {s['skipped']}  errored: {s['errored']})")
    print(f"  Passed / Failed      : {s['passed']} / {s['failed']}")
    print(f"  Missing Holder       : {s['missing_holder']}")
    print(f"  Missing Account      : {s['missing_account']}")
    print(f"  Missing IFSC         : {s['missing_ifsc']}")
    print(f"  Balance Mismatch rows: {s['balance_mismatch_rows']}")
    print(f"  Flagged rows         : {s['flagged_rows']}")
    print(f"  Extracted rows       : {s['extracted_rows']}  (clean: {s['clean_rows']})")
    diag = s.get("mismatch_diagnosis_breakdown") or {}
    if diag:
        print("  Mismatch diagnosis   : " + ", ".join(f"{k}={v}" for k, v in diag.items()))


def main():
    ap = argparse.ArgumentParser(description="Offline deterministic regression harness")
    ap.add_argument("--save-baseline", action="store_true",
                    help="overwrite the saved baseline with this run")
    ap.add_argument("--json", metavar="PATH", help="also write the raw per-file JSON here")
    args = ap.parse_args()

    current = run()
    _print_summary(current["summary"])

    if args.json:
        Path(args.json).write_text(json.dumps(current, indent=2))
        print(f"\n  wrote raw JSON → {args.json}")

    exit_code = 0
    if args.save_baseline:
        BASELINE_PATH.parent.mkdir(parents=True, exist_ok=True)
        BASELINE_PATH.write_text(json.dumps(current, indent=2))
        print(f"\n  SAVED baseline → {BASELINE_PATH.relative_to(REPO_ROOT)}")
    elif BASELINE_PATH.exists():
        baseline = json.loads(BASELINE_PATH.read_text())
        regressions, improvements = _diff_against_baseline(current, baseline)
        print("\n=== DIFF vs BASELINE ===")
        if not regressions:
            print("  New Regressions: 0  ✓")
        else:
            exit_code = 1
            print(f"  New Regressions: {len(regressions)}  ✗")
            for rel, reasons in regressions:
                print(f"    - {rel}: {'; '.join(reasons)}")
        print(f"  Improvements   : {len(improvements)}")
        for rel, gains in improvements:
            print(f"    + {rel}: {'; '.join(gains)}")
    else:
        print("\n  (no baseline saved yet — run with --save-baseline to create one)")

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
