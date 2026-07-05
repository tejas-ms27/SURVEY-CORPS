"""Compare produced findings against ground truth and compute honest metrics.

Definitions (documented so the numbers are defensible):
  TP  — an expected finding whose pattern fired on an expected account
        (matched by real account number, UTR-recovered account, or, only when the
        expected account cannot be resolved to a number, by the pattern firing at all).
  FN  — an expected finding with no matching produced finding (a miss).
  FP  — a *scored* pattern (excluding structural id 6, meta id 21, and lead ids 22/23)
        firing on a clean_control account, or firing on a pattern listed in the folder's
        expected_non_findings.
  not_evaluable — an expected finding that the dataset cannot faithfully exercise using
        only production behaviour (e.g. population-scale leads 22/23 on a 2-3 account
        fixture). Never counted as TP/FP/FN; reported with its reason.

No dataset value is hardcoded: everything is read from each folder's ground_truth.json.
"""

from __future__ import annotations

from typing import Any

# Structural (6), meta-ranking (21), and the two lead detectors (22, 23) are never counted
# as scored false positives — 6/21 are not account-accusatory, and 22/23 are explicitly
# low-confidence leads by design (a lead on a clean account is reported separately, not as FP).
FP_EXCLUDED_PATTERNS = {6, 21, 22, 23}

# Population-scale lead detectors. The unsupervised ML ensemble needs >= 5 accounts
# (analysis/analysis_engine/detectors/ml_ensemble.py) and the Pattern-22 anomaly percentile
# is degenerate on a handful of accounts. This threshold is derived from production
# behaviour, not tuned to any folder.
POPULATION_LEAD_PATTERNS = {22, 23}
MIN_ACCOUNTS_FOR_POPULATION_LEAD = 5

PATTERN_NAMES = {
    1: "duplicate_verification", 2: "failed_reversed_transaction", 3: "pass_through_routing",
    4: "fund_pooling", 5: "structuring_smurfing", 6: "money_flow_graph", 7: "circular_flow",
    8: "money_trail", 9: "credit_to_cash_out", 10: "cross_statement_links", 11: "balance_parking",
    12: "hub_ranking", 13: "low_value_testing", 14: "reversal_clusters", 15: "round_value_debit",
    16: "shared_upi", 17: "round_trip", 18: "dormant_reactivation", 19: "first_contact_large_transfer",
    21: "suspicious_account_ranking", 22: "llm_lead_unknown_shape", 23: "ml_ensemble_unknown_shape",
}


def _norm(value: Any) -> str:
    text = "" if value is None else str(value).strip()
    if text.endswith(".0") and text[:-2].isdigit():
        text = text[:-2]
    return text


def _truth_maps(truth: dict[str, Any]) -> tuple[dict[str, str], set[str], int]:
    syn_to_number: dict[str, str] = {}
    clean_numbers: set[str] = set()
    for account in truth.get("accounts", []):
        syn = str(account.get("synthetic_account_id", ""))
        number = _norm(account.get("fabricated_account_number", ""))
        if syn and number:
            syn_to_number[syn] = number
            if str(account.get("role", "")) == "clean_control":
                clean_numbers.add(number)
    return syn_to_number, clean_numbers, len(truth.get("accounts", []))


def _finding_numbers(finding: dict[str, Any], account_map: dict[str, str]) -> set[str]:
    accounts = finding.get("accounts") or finding.get("account_ids") or []
    return {_norm(account_map.get(str(a), str(a))) for a in accounts if _norm(a)}


def _expected_numbers(item: dict[str, Any], syn_to_number: dict[str, str],
                      utr_map: dict[str, set[str]]) -> set[str]:
    numbers: set[str] = set()
    for syn in item.get("accounts_involved", []) or []:
        number = syn_to_number.get(str(syn))
        if number:
            numbers.add(number)
    for ref in item.get("expected_txn_refs", []) or []:
        numbers |= {_norm(n) for n in utr_map.get(str(ref), set())}
    return {n for n in numbers if n}


def score_fixture(bundle: dict[str, Any]) -> dict[str, Any]:
    folder = bundle["folder"].name
    truth = bundle["truth"]
    analysis = bundle["analysis"]
    account_map = bundle["account_number_map"]
    utr_map = bundle["utr_account_map"]

    syn_to_number, clean_numbers, account_count = _truth_maps(truth)
    # Only ACCUSATORY findings count. Detectors emit negative/status rows with an empty
    # account list ("No duplicates detected", "No money-trail triggered", "not_triggered")
    # to prove they ran and found nothing — those are never a true or false positive on any
    # dataset, so they are excluded from both TP matching and FP counting.
    findings = [
        f for f in (analysis.get("all_findings", []) or [])
        if (f.get("accounts") or f.get("account_ids"))
    ]
    expected_non_finding_ids = {int(n.get("pattern_id")) for n in truth.get("expected_non_findings", []) or []}

    tp: list[dict[str, Any]] = []
    fn: list[dict[str, Any]] = []
    not_evaluable: list[dict[str, Any]] = []

    for item in truth.get("expected_findings", []) or []:
        pid = int(item.get("pattern_id"))
        if pid in POPULATION_LEAD_PATTERNS and account_count < MIN_ACCOUNTS_FOR_POPULATION_LEAD:
            not_evaluable.append({
                "pattern_id": pid,
                "reason": (
                    f"Pattern {pid} is a population-scale lead; the fixture has only "
                    f"{account_count} account(s) (< {MIN_ACCOUNTS_FOR_POPULATION_LEAD}). "
                    "Not faithfully exercisable in isolation — measured on combined_all_patterns."
                ),
            })
            continue
        expected_nums = _expected_numbers(item, syn_to_number, utr_map)
        candidates = [f for f in findings if int(f.get("pattern_id", -1)) == pid]
        match = None
        for f in candidates:
            if expected_nums and _finding_numbers(f, account_map) & expected_nums:
                match = {"basis": "account_or_utr", "finding_id": f.get("finding_id", "")}
                break
        if match is None and not expected_nums and candidates:
            # Expected accounts could not be resolved to real numbers (identity gap);
            # fall back to "pattern fired" and flag the weaker basis transparently.
            match = {"basis": "pattern_only_account_unresolved", "finding_id": candidates[0].get("finding_id", "")}
        record = {"pattern_id": pid, "expected_numbers": sorted(expected_nums), **(match or {})}
        (tp if match else fn).append(record)

    # False positives: scored patterns hitting clean accounts or expected-non-finding patterns.
    fp_pairs: set[tuple[int, str]] = set()
    lead_on_clean: list[dict[str, Any]] = []
    for f in findings:
        pid = int(f.get("pattern_id", -1))
        nums = _finding_numbers(f, account_map)
        clean_hit = nums & clean_numbers
        if pid in FP_EXCLUDED_PATTERNS:
            if pid in POPULATION_LEAD_PATTERNS and clean_hit:
                lead_on_clean.append({"pattern_id": pid, "accounts": sorted(clean_hit)})
            continue
        for number in clean_hit:
            fp_pairs.add((pid, number))
        if pid in expected_non_finding_ids:
            for number in (nums or {""}):
                fp_pairs.add((pid, number))

    return {
        "folder": folder,
        "account_count": account_count,
        "row_count": (analysis.get("input_contract", {}) or {}).get("clean_row_count"),
        "tp": tp,
        "fn": fn,
        "fp": [{"pattern_id": p, "account_number": a} for p, a in sorted(fp_pairs)],
        "not_evaluable": not_evaluable,
        "lead_on_clean": lead_on_clean,
        "counts": {"tp": len(tp), "fn": len(fn), "fp": len(fp_pairs), "not_evaluable": len(not_evaluable)},
        "extraction_dir": bundle.get("extraction_dir"),
        "analysis_dir": bundle.get("analysis_dir"),
    }


def _prf(tp: int, fp: int, fn: int) -> dict[str, float]:
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    return {"precision": round(precision, 4), "recall": round(recall, 4), "f1": round(f1, 4)}


def aggregate(fixture_scores: list[dict[str, Any]]) -> dict[str, Any]:
    total_tp = sum(s["counts"]["tp"] for s in fixture_scores)
    total_fp = sum(s["counts"]["fp"] for s in fixture_scores)
    total_fn = sum(s["counts"]["fn"] for s in fixture_scores)
    total_ne = sum(s["counts"]["not_evaluable"] for s in fixture_scores)

    per_pattern: dict[int, dict[str, int]] = {}
    for s in fixture_scores:
        for rec in s["tp"]:
            per_pattern.setdefault(rec["pattern_id"], {"expected": 0, "detected": 0, "missed": 0, "fp": 0})
            per_pattern[rec["pattern_id"]]["expected"] += 1
            per_pattern[rec["pattern_id"]]["detected"] += 1
        for rec in s["fn"]:
            per_pattern.setdefault(rec["pattern_id"], {"expected": 0, "detected": 0, "missed": 0, "fp": 0})
            per_pattern[rec["pattern_id"]]["expected"] += 1
            per_pattern[rec["pattern_id"]]["missed"] += 1
        for rec in s["fp"]:
            per_pattern.setdefault(rec["pattern_id"], {"expected": 0, "detected": 0, "missed": 0, "fp": 0})
            per_pattern[rec["pattern_id"]]["fp"] += 1

    pattern_breakdown = []
    for pid in sorted(per_pattern):
        row = per_pattern[pid]
        recall = row["detected"] / row["expected"] if row["expected"] else None
        pattern_breakdown.append({
            "pattern_id": pid,
            "pattern_name": PATTERN_NAMES.get(pid, str(pid)),
            "expected": row["expected"],
            "detected": row["detected"],
            "missed": row["missed"],
            "false_positives": row["fp"],
            "recall": round(recall, 4) if recall is not None else None,
        })

    return {
        "overall": {
            "patterns_present": total_tp + total_fn,
            "detected": total_tp,
            "missed": total_fn,
            "false_positives": total_fp,
            "not_evaluable": total_ne,
            **_prf(total_tp, total_fp, total_fn),
        },
        "pattern_breakdown": pattern_breakdown,
        "fixtures": fixture_scores,
    }
