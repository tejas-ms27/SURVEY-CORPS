#!/usr/bin/env python3
"""Compare pipeline analysis_results.json with a synthetic folder's ground truth."""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any


NAME_TO_ID = {
    "duplicate_verification": 1, "failed_reversed_transaction": 2, "pass_through_routing": 3,
    "fund_pooling": 4, "structuring_smurfing": 5, "circular_flow": 7, "money_trail": 8,
    "credit_to_cash_out": 9, "cross_statement_links": 10, "balance_parking": 11,
    "hub_ranking": 12, "low_value_testing": 13, "reversal_clusters": 14,
    "round_value_debit": 15, "shared_upi": 16, "round_trip": 17,
    "dormant_reactivation": 18, "first_contact_large_transfer": 19,
    "llm_lead_unknown_shape": 22, "ml_ensemble_unknown_shape": 23,
}


def pattern_id(value: Any) -> int | None:
    if isinstance(value, int): return value
    if isinstance(value, str):
        if value.casefold() in NAME_TO_ID: return NAME_TO_ID[value.casefold()]
        match = re.search(r"(?i)(?:pattern[_ -]?)?(\d{1,2})", value)
        if match: return int(match.group(1))
    return None


def strings(value: Any) -> set[str]:
    if value is None: return set()
    if isinstance(value, (str, int)):
        raw = str(value)
        return {raw, *re.findall(r"\bSYN\d{4}\b", raw)}
    if isinstance(value, list):
        return set().union(*(strings(x) for x in value))
    if isinstance(value, dict):
        result = set()
        for key in ("synthetic_account_id", "source_account_id", "account_id", "id", "file", "filename", "ref", "reference"):
            if key in value: result |= strings(value[key])
        return result
    return set()


def normalize_finding(item: dict[str, Any], inherited_pid: int | None = None) -> dict[str, Any] | None:
    pid = pattern_id(item.get("pattern_id")) or pattern_id(item.get("pattern")) or pattern_id(item.get("pattern_name")) or inherited_pid
    if pid is None: return None
    accounts = set()
    for key in ("accounts_involved", "account_ids", "accounts", "source_account_id", "account_id", "entities", "source_files", "files"):
        accounts |= strings(item.get(key))
    refs = set()
    for key in ("expected_txn_refs", "txn_refs", "transaction_refs", "references", "ref", "bank_ref", "transaction_ids"):
        refs |= strings(item.get(key))
    tier = str(item.get("tier", item.get("expected_tier", item.get("severity", "unknown")))).casefold()
    return {"pattern_id": pid, "accounts": accounts, "refs": refs, "tier": tier, "raw": item}


def extract_findings(data: Any) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    seen: set[int] = set()
    def walk(value: Any, inherited_pid: int | None = None) -> None:
        if isinstance(value, list):
            for child in value: walk(child, inherited_pid)
        elif isinstance(value, dict):
            normalized = normalize_finding(value, inherited_pid)
            # Only count finding-like objects, not containers such as {pattern_id: [...]}.
            finding_keys = {"tier", "severity", "accounts_involved", "accounts", "account_ids", "account_id", "source_account_id",
                            "txn_refs", "transaction_refs", "evidence", "amount", "score", "finding_id"}
            if normalized and (finding_keys & set(value)) and id(value) not in seen:
                found.append(normalized); seen.add(id(value))
            for key, child in value.items():
                child_pid = pattern_id(key) if re.search(r"(?i)pattern|^\d{1,2}$", str(key)) else inherited_pid
                walk(child, child_pid)
    walk(data)
    return found


def validate_truth(truth: dict[str, Any]) -> list[str]:
    errors = []
    for key in ("folder", "description", "accounts", "expected_findings", "expected_non_findings"):
        if key not in truth: errors.append(f"missing key: {key}")
    ids = {x.get("synthetic_account_id") for x in truth.get("accounts", [])}
    if None in ids: errors.append("account missing synthetic_account_id")
    for finding in truth.get("expected_findings", []):
        if pattern_id(finding.get("pattern_id")) is None: errors.append("finding missing valid pattern_id")
        unknown = set(finding.get("accounts_involved", [])) - ids
        if unknown: errors.append(f"finding references unknown accounts: {sorted(unknown)}")
    return errors


def compare(truth: dict[str, Any], analysis: Any, strict_accounts: bool) -> dict[str, Any]:
    actual = extract_findings(analysis)
    expected = []
    for item in truth.get("expected_findings", []):
        expected.append({"pattern_id": pattern_id(item.get("pattern_id")),
                         "accounts": set(map(str, item.get("accounts_involved", []))),
                         "refs": set(map(str, item.get("expected_txn_refs", []))), "raw": item})
    used: set[int] = set(); matches = []; misses = []
    for exp in expected:
        choices = [(i, act) for i, act in enumerate(actual) if i not in used and act["pattern_id"] == exp["pattern_id"]]
        scored = []
        for i, act in choices:
            account_overlap = exp["accounts"] & act["accounts"]
            ref_overlap = exp["refs"] & act["refs"]
            if strict_accounts and exp["accounts"] and not account_overlap: continue
            scored.append((len(account_overlap) * 10 + len(ref_overlap) * 5 + (1 if act["tier"] != "unknown" else 0), i, act,
                           account_overlap, ref_overlap))
        if not scored:
            misses.append({"pattern_id": exp["pattern_id"], "accounts": sorted(exp["accounts"])})
            continue
        _, i, act, account_overlap, ref_overlap = max(scored, key=lambda x: x[0])
        used.add(i)
        matches.append({"pattern_id": exp["pattern_id"], "expected_accounts": sorted(exp["accounts"]),
                        "account_overlap": sorted(account_overlap), "reference_overlap": sorted(ref_overlap),
                        "actual_tier": act["tier"]})
    extras = [{"pattern_id": act["pattern_id"], "accounts": sorted(act["accounts"]), "tier": act["tier"]}
              for i, act in enumerate(actual) if i not in used]
    allow_weak = bool(truth.get("tier_expectations", {}).get("weak_findings_allowed"))
    failing_extras = [x for x in extras if not (allow_weak and x["tier"] in {"weak", "low", "informational", "info"})]
    by_pattern: dict[int, dict[str, int]] = defaultdict(lambda: {"matched": 0, "missed": 0, "unexpected_extra": 0})
    for x in matches: by_pattern[x["pattern_id"]]["matched"] += 1
    for x in misses: by_pattern[x["pattern_id"]]["missed"] += 1
    for x in extras: by_pattern[x["pattern_id"]]["unexpected_extra"] += 1
    return {"folder": truth.get("folder"), "passed": not misses and not failing_extras,
            "summary": {"matched": len(matches), "missed": len(misses), "unexpected_extra": len(extras),
                        "failing_unexpected_extra": len(failing_extras)},
            "by_pattern": {str(k): v for k, v in sorted(by_pattern.items())},
            "matches": matches, "misses": misses, "unexpected_extras": extras,
            "notes": ["Pattern-only matching is used when pipeline output does not expose synthetic IDs or bank references."]}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("ground_truth", type=Path, help="ground_truth.json or its containing fixture folder")
    parser.add_argument("analysis_results", type=Path)
    parser.add_argument("--strict-accounts", action="store_true", help="Require at least one expected account ID overlap.")
    parser.add_argument("--json-report", type=Path)
    args = parser.parse_args()
    truth_path = args.ground_truth / "ground_truth.json" if args.ground_truth.is_dir() else args.ground_truth
    truth = json.loads(truth_path.read_text(encoding="utf-8"))
    errors = validate_truth(truth)
    if errors:
        print("Invalid ground truth: " + "; ".join(errors), file=sys.stderr); return 2
    analysis = json.loads(args.analysis_results.read_text(encoding="utf-8"))
    report = compare(truth, analysis, args.strict_accounts)
    print(f"Folder: {report['folder']}")
    for pid, result in report["by_pattern"].items():
        print(f"Pattern {pid}: matched={result['matched']} missed={result['missed']} unexpected-extra={result['unexpected_extra']}")
    summary = report["summary"]
    print(f"{'PASS' if report['passed'] else 'FAIL'}: matched={summary['matched']} missed={summary['missed']} "
          f"unexpected-extra={summary['unexpected_extra']}")
    if args.json_report:
        args.json_report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
