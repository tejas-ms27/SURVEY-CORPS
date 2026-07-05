# Copied from: analysis phase cidecode hackathon/analysis phase cidecode hackathon/analysis_engine/detectors/round_value_debits.py
"""Pattern 15: repeated round-value debit pattern.

Flags accounts making numerous transfers using identical or rounded amounts
(e.g. ₹10,000, ₹20,000, ₹50,000 repeatedly), which can indicate structuring
or automated layering.
"""

from __future__ import annotations

import sqlite3
from collections import Counter

import pandas as pd

from ..config import AnalysisConfig
from ..database import fetch_transactions
from .common import make_finding


def _is_round_value(amount: float, divisor: float) -> bool:
    """Check if an amount is a round multiple of the divisor."""
    if amount <= 0 or divisor <= 0:
        return False
    return abs(amount % divisor) < 0.01


def detect_round_value_debits(
    connection: sqlite3.Connection,
    baseline: dict,
    config: AnalysisConfig,
) -> list:
    thresholds = baseline["thresholds"]
    frame = fetch_transactions(connection, "eligible_for_detection = 1 AND date IS NOT NULL")
    if frame.empty:
        return []

    # Focus on debits only
    debits = frame[frame["debit_amount"] > config.money_epsilon].copy()
    if debits.empty:
        return []

    amount_stats = baseline.get("transaction_amounts", {})
    high_round_floor = max(
        float(amount_stats.get("p90", 0.0) or 0.0),
        float(thresholds.get("high_value_amount", 0.0) or 0.0),
    )
    cluster_window_days = max(1, int(thresholds.get("round_trip_window_days", 1) or 1))
    account_metrics = []
    for account_id, group in debits.groupby("account_id", sort=False):
        round_mask = group["debit_amount"].apply(
            lambda a: _is_round_value(float(a), config.round_value_divisor)
        )
        round_debits = group[round_mask]
        total_debit = float(group["debit_amount"].sum())
        account_metrics.append(
            {
                "account_id": str(account_id),
                "round_count": int(len(round_debits)),
                "round_total": float(round_debits["debit_amount"].sum()),
                "round_amount_share": (
                    float(round_debits["debit_amount"].sum()) / max(total_debit, config.money_epsilon)
                ),
            }
        )
    metrics = pd.DataFrame(account_metrics)
    count_outlier_floor = 0.0
    total_outlier_floor = 0.0
    share_outlier_floor = 0.0
    if not metrics.empty:
        for column, target in [
            ("round_count", "count_outlier_floor"),
            ("round_total", "total_outlier_floor"),
            ("round_amount_share", "share_outlier_floor"),
        ]:
            values = pd.to_numeric(metrics[column], errors="coerce").dropna()
            if values.empty:
                continue
            q75 = float(values.quantile(0.75))
            q25 = float(values.quantile(0.25))
            floor = q75 + max(q75 - q25, 0.0)
            if target == "count_outlier_floor":
                count_outlier_floor = floor
            elif target == "total_outlier_floor":
                total_outlier_floor = floor
            else:
                share_outlier_floor = floor

    findings = []

    for account_id, group in debits.groupby("account_id", sort=False):
        # Find round-value amounts
        round_mask = group["debit_amount"].apply(
            lambda a: _is_round_value(float(a), config.round_value_divisor)
        )
        round_debits = group[round_mask]
        if len(round_debits) < config.round_value_min_repeats:
            continue

        high_round_debits = round_debits[
            round_debits["debit_amount"].astype(float) >= high_round_floor
        ].copy()
        high_cluster = None
        if len(high_round_debits) >= config.round_value_min_repeats:
            high_round_debits["parsed_date"] = pd.to_datetime(
                high_round_debits["date"], errors="coerce"
            )
            high_round_debits = high_round_debits.dropna(subset=["parsed_date"]).sort_values(
                ["parsed_date", "time", "source_order", "row_id"]
            )
            for start in high_round_debits.itertuples(index=False):
                cluster = high_round_debits[
                    (high_round_debits["parsed_date"] >= start.parsed_date)
                    & ((high_round_debits["parsed_date"] - start.parsed_date).dt.days <= cluster_window_days)
                ].copy()
                if len(cluster) < config.round_value_min_repeats:
                    continue
                candidate = {
                    "rows": cluster,
                    "count": int(len(cluster)),
                    "total": float(cluster["debit_amount"].sum()),
                    "start_date": str(cluster["date"].iloc[0]),
                    "end_date": str(cluster["date"].iloc[-1]),
                }
                if high_cluster is None or candidate["total"] > high_cluster["total"]:
                    high_cluster = candidate

        metric_row = metrics[metrics["account_id"] == str(account_id)]
        metric = metric_row.iloc[0].to_dict() if not metric_row.empty else {}
        aggregate_outlier = (
            float(metric.get("round_count", 0.0) or 0.0) > max(
                count_outlier_floor, config.round_value_min_repeats
            )
            and float(metric.get("round_total", 0.0) or 0.0) > max(
                total_outlier_floor, thresholds["round_value_collective_min"]
            )
            and float(metric.get("round_amount_share", 0.0) or 0.0) > share_outlier_floor
        )
        if not high_cluster and not aggregate_outlier:
            continue

        evidence_rows = high_cluster["rows"] if high_cluster else round_debits

        # Count repeated amounts
        amount_counts = Counter(float(a) for a in evidence_rows["debit_amount"])
        repeated_amounts = {
            amt: count for amt, count in amount_counts.items()
            if count >= config.round_value_min_repeats
        }

        if not repeated_amounts and not high_cluster:
            # Even without exact repeats, many round values together is suspicious
            total = float(evidence_rows["debit_amount"].sum())
            if total < thresholds["round_value_collective_min"]:
                continue
            if len(evidence_rows) < config.round_value_min_repeats * 2:
                continue

        # Collect txn_ids for all round-value debits
        ordered = evidence_rows.sort_values(["date", "time", "source_order", "row_id"])
        txn_ids = ordered["txn_id"].astype(str).tolist()
        amounts = ordered["debit_amount"].astype(float).tolist()
        total_round = float(ordered["debit_amount"].sum())

        explanation_parts = []
        if repeated_amounts:
            for amt, count in sorted(repeated_amounts.items(), key=lambda x: -x[1]):
                explanation_parts.append(f"₹{amt:,.0f} x{count}")
            explanation_detail = ", ".join(explanation_parts[:5])
            explanation = (
                f"Account {account_id} made {len(ordered)} suspicious round-value debits "
                f"totalling {total_round:.2f}, with repeated amounts: {explanation_detail}."
            )
        else:
            explanation = (
                f"Account {account_id} made {len(ordered)} suspicious round-value debits "
                f"(multiples of {config.round_value_divisor:.0f}) totalling {total_round:.2f}."
            )

        findings.append(
            make_finding(
                connection,
                15,
                [str(account_id)],
                txn_ids,
                explanation,
                {
                    "round_debit_count": len(ordered),
                    "total_round_debits": total_round,
                    "repeated_amounts": {str(k): v for k, v in repeated_amounts.items()},
                    "individual_amounts": amounts,
                    "divisor": config.round_value_divisor,
                    "round_value_evidence_type": "high_value_cluster" if high_cluster else "aggregate_outlier",
                    "account_round_value_metrics": {
                        "all_round_count": int(metric.get("round_count", 0) or 0),
                        "all_round_total": float(metric.get("round_total", 0.0) or 0.0),
                        "round_amount_share": float(metric.get("round_amount_share", 0.0) or 0.0),
                    },
                    "runtime_thresholds": {
                        "min_repeats": config.round_value_min_repeats,
                        "collective_min": thresholds["round_value_collective_min"],
                        "high_round_amount_floor": high_round_floor,
                        "cluster_window_days": cluster_window_days,
                        "count_outlier_floor": count_outlier_floor,
                        "total_outlier_floor": total_outlier_floor,
                        "share_outlier_floor": share_outlier_floor,
                    },
                },
            )
        )
        if len(findings) >= config.maximum_findings_per_pattern:
            break

    return findings
