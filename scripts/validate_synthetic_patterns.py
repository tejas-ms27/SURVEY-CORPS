#!/usr/bin/env python3
"""Run extraction + analysis for synthetic pattern folders and compare to truth.

The report is intentionally account-aware: it maps analysis account IDs
(`acct_001`, etc.) back to the fabricated account numbers in each
ground_truth.json so clean-control contamination is visible.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import time
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from analysis.analysis_engine.config import AnalysisConfig
from analysis.analysis_engine.pipeline import AnalysisPipeline
from extraction.extraction_pipeline import run_extraction_pipeline


IGNORE_EXTRA_PATTERNS = {6, 21, 22, 23}


def _norm_acct(value: Any) -> str:
    text = "" if value is None else str(value).strip()
    if text.endswith(".0") and text[:-2].isdigit():
        text = text[:-2]
    return text


def _load_truth(folder: Path) -> dict[str, Any]:
    return json.loads((folder / "ground_truth.json").read_text(encoding="utf-8"))


def _truth_maps(truth: dict[str, Any]) -> tuple[dict[str, str], dict[str, str], set[str]]:
    syn_to_number: dict[str, str] = {}
    syn_to_role: dict[str, str] = {}
    clean_numbers: set[str] = set()
    for account in truth.get("accounts", []):
        syn = str(account.get("synthetic_account_id", ""))
        number = _norm_acct(account.get("fabricated_account_number", ""))
        role = str(account.get("role", ""))
        if syn and number:
            syn_to_number[syn] = number
            syn_to_role[syn] = role
            if role == "clean_control":
                clean_numbers.add(number)
    return syn_to_number, syn_to_role, clean_numbers


def _files_for_extraction(folder: Path) -> list[dict[str, str]]:
    statements = folder / "statements"
    files = []
    for path in sorted(statements.iterdir()):
        if path.is_file():
            files.append(
                {
                    "file_path": str(path),
                    "account_id": path.stem,
                    "bank_name": "Unknown Bank",
                }
            )
    return files


def _run_extraction(folder: Path, session_id: str, force: bool) -> Path:
    out_dir = ROOT / "outputs" / "extractions" / session_id
    if force and out_dir.exists():
        shutil.rmtree(out_dir)
    if out_dir.exists() and (out_dir / "clean_transactions.csv").exists():
        return out_dir
    files = _files_for_extraction(folder)
    if not files:
        raise FileNotFoundError(f"No statements found in {folder / 'statements'}")
    run_extraction_pipeline(
        files=files,
        session_id=session_id,
        ingest_to_chromadb=False,
        max_ocr_pages=None,
        persist=True,
    )
    return out_dir


def _run_analysis(extraction_dir: Path, output_dir: Path, force: bool) -> Path:
    if force and output_dir.exists():
        shutil.rmtree(output_dir)
    result_path = output_dir / "analysis_results.json"
    if result_path.exists():
        return result_path
    config = AnalysisConfig(enable_llm_fallback=False)
    result = AnalysisPipeline(
        input_path=extraction_dir,
        output_dir=output_dir,
        config=config,
    ).run()
    return output_dir / "analysis_results.json"


def _load_account_map(extraction_dir: Path) -> dict[str, str]:
    clean_path = extraction_dir / "clean_transactions.csv"
    frame = pd.read_csv(clean_path, dtype=str).fillna("")
    mapping: dict[str, str] = {}
    if "source_account_id" not in frame.columns or "account_number" not in frame.columns:
        return mapping
    pairs = frame[["source_account_id", "account_number"]].drop_duplicates()
    for row in pairs.itertuples(index=False):
        mapping[str(row.source_account_id)] = _norm_acct(row.account_number)
    return mapping


def _finding_accounts_as_numbers(finding: dict[str, Any], account_map: dict[str, str]) -> set[str]:
    accounts = finding.get("accounts") or finding.get("account_ids") or []
    return {_norm_acct(account_map.get(str(account), str(account))) for account in accounts}


def _expected_by_pattern(truth: dict[str, Any], syn_to_number: dict[str, str]) -> list[dict[str, Any]]:
    expected = []
    for item in truth.get("expected_findings", []):
        pid = int(item.get("pattern_id"))
        syn_accounts = [str(value) for value in item.get("accounts_involved", [])]
        numbers = {syn_to_number[value] for value in syn_accounts if value in syn_to_number}
        expected.append(
            {
                "pattern_id": pid,
                "synthetic_accounts": syn_accounts,
                "account_numbers": numbers,
                "expected_tier": item.get("expected_tier", ""),
                "notes": item.get("notes", ""),
            }
        )
    return expected


def _analyze_result(
    truth: dict[str, Any],
    analysis: dict[str, Any],
    account_map: dict[str, str],
) -> dict[str, Any]:
    syn_to_number, _, clean_numbers = _truth_maps(truth)
    expected = _expected_by_pattern(truth, syn_to_number)
    findings = analysis.get("all_findings", [])
    suspicious = analysis.get("suspicious_accounts", [])

    pattern_counts: dict[str, int] = {}
    for finding in findings:
        pid = str(finding.get("pattern_id"))
        pattern_counts[pid] = pattern_counts.get(pid, 0) + 1

    misses = []
    for exp in expected:
        candidates = [f for f in findings if int(f.get("pattern_id", -1)) == exp["pattern_id"]]
        matched = False
        for finding in candidates:
            actual_numbers = _finding_accounts_as_numbers(finding, account_map)
            if exp["account_numbers"] and actual_numbers.intersection(exp["account_numbers"]):
                matched = True
                break
        if not matched:
            misses.append(
                {
                    **exp,
                    "account_numbers": sorted(exp["account_numbers"]),
                }
            )

    clean_contamination = []
    for finding in findings:
        pid = int(finding.get("pattern_id", -1))
        if pid in IGNORE_EXTRA_PATTERNS:
            continue
        actual_numbers = _finding_accounts_as_numbers(finding, account_map)
        clean_hit = sorted(actual_numbers.intersection(clean_numbers))
        if clean_hit:
            clean_contamination.append(
                {
                    "pattern_id": pid,
                    "pattern_name": finding.get("pattern_name", ""),
                    "clean_account_numbers": clean_hit,
                    "analysis_accounts": finding.get("accounts", []),
                    "confidence_tier": finding.get("confidence_tier", ""),
                    "evidence_strength": finding.get("evidence_strength", ""),
                    "explanation": finding.get("explanation", "")[:300],
                }
            )

    top_ranked = []
    for row in suspicious[:10]:
        account_id = str(row.get("account_id", ""))
        number = _norm_acct(account_map.get(account_id, account_id))
        top_ranked.append(
            {
                "account_id": account_id,
                "account_number": number,
                "role": "clean_control" if number in clean_numbers else "expected_or_subject",
                "total_score": row.get("total_score", 0),
                "distinct_pattern_count": row.get("distinct_pattern_count", 0),
            }
        )

    return {
        "folder": truth.get("folder"),
        "row_count": analysis.get("input_contract", {}).get("clean_row_count"),
        "pattern_counts": pattern_counts,
        "misses": misses,
        "clean_contamination": clean_contamination,
        "top_ranked": top_ranked,
        "passed": not misses and not clean_contamination,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-root", type=Path, default=ROOT / "synthetic_test_data")
    parser.add_argument("--session-prefix", default="synthetic_validation")
    parser.add_argument("--folders", nargs="*", help="Specific fixture folder names to run")
    parser.add_argument("--force", action="store_true", help="Regenerate extraction and analysis outputs")
    parser.add_argument("--skip-extraction", action="store_true", help="Only rerun/reuse analysis for existing extraction outputs")
    parser.add_argument("--report", type=Path, default=ROOT / "tmp" / "synthetic_pattern_validation_report.json")
    args = parser.parse_args()

    dataset_root = args.dataset_root.resolve()
    folders = [p for p in sorted(dataset_root.iterdir()) if (p / "ground_truth.json").exists()]
    if args.folders:
        wanted = set(args.folders)
        folders = [p for p in folders if p.name in wanted]

    report = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "dataset_root": str(dataset_root),
        "results": [],
    }

    failures = 0
    for folder in folders:
        session_id = f"{args.session_prefix}_{folder.name}"
        extraction_dir = ROOT / "outputs" / "extractions" / session_id
        if args.skip_extraction:
            if not (extraction_dir / "clean_transactions.csv").exists():
                print(f"SKIP {folder.name}: missing {extraction_dir}")
                failures += 1
                continue
        else:
            extraction_dir = _run_extraction(folder, session_id, args.force)

        analysis_dir = ROOT / "analysis" / "outputs" / session_id
        result_path = _run_analysis(extraction_dir, analysis_dir, args.force)
        truth = _load_truth(folder)
        analysis = json.loads(result_path.read_text(encoding="utf-8"))
        account_map = _load_account_map(extraction_dir)
        result = _analyze_result(truth, analysis, account_map)
        result["extraction_dir"] = str(extraction_dir)
        result["analysis_dir"] = str(analysis_dir)
        report["results"].append(result)

        status = "PASS" if result["passed"] else "FAIL"
        print(
            f"{status} {folder.name}: rows={result['row_count']} "
            f"misses={len(result['misses'])} clean_hits={len(result['clean_contamination'])} "
            f"patterns={result['pattern_counts']}"
        )
        if not result["passed"]:
            failures += 1

    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Report: {args.report}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
