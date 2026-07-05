# Copied from: analysis phase cidecode hackathon/analysis phase cidecode hackathon/analysis_engine/detectors/high_throughput.py
"""Pattern 3: high-volume pass-through/routing account variant.

Unlike Pattern 5 (transit) which uses aggregate throughput ratio, this pattern
examines temporal proximity — credits followed by near-equal debits within a
short window — to identify high-throughput pass-through behaviour.
"""

from __future__ import annotations

import sqlite3

import networkx as nx
import numpy as np
import pandas as pd

from ..config import AnalysisConfig
from ..database import fetch_transactions
from ..utils import safe_ratio
from ..utils import normalize_text
from .common import make_finding


ORDINARY_PASS_THROUGH_CREDIT_TOKENS = {
    "SALARY",
    "INTEREST",
    "REFUND",
    "REVERSAL",
    "CASHBACK",
    "DIVIDEND",
    "PENSION",
}

ORDINARY_PASS_THROUGH_DEBIT_TOKENS = {
    "ATM",
    "CASH",
    "POS",
    "BILL",
    "RECHARGE",
    "CHARGES",
    "GST",
    "FUEL",
    "MAINTENANCE",
    "INTEREST",
}


def _contains_any_token(value: object, tokens: set[str]) -> bool:
    normalized = normalize_text(value or "")
    return any(token in normalized for token in tokens)


def _pass_through_burst_evidence(
    connection: sqlite3.Connection,
    account_id: str,
    baseline: dict,
    config: AnalysisConfig,
) -> dict | None:
    """Return localized pass-through evidence for an account, if present.

    Aggregate inflow/outflow similarity is not enough: ordinary retail accounts
    can have high throughput across many payment endpoints. This gate requires a
    burst of multiple material credits followed quickly by transfer-like debits
    clearing most of that burst.
    """

    frame = fetch_transactions(
        connection,
        "eligible_for_detection = 1 AND date IS NOT NULL AND account_id = ?",
        parameters=(account_id,),
    )
    if frame.empty:
        return None
    frame["parsed_date"] = pd.to_datetime(frame["date"], errors="coerce")
    frame = frame.dropna(subset=["parsed_date"]).sort_values(
        ["parsed_date", "time", "source_order", "row_id"]
    )
    if frame.empty:
        return None

    thresholds = baseline["thresholds"]
    amounts = baseline.get("transaction_amounts", {})
    window_days = max(1, int(thresholds.get("reversal_window_days", 1) or 1))
    min_credit_count = max(2, int(config.high_throughput_min_counterparties))
    material_credit_floor = max(
        float(amounts.get("p75", 0.0) or 0.0),
        float(thresholds.get("high_value_amount", 0.0) or 0.0),
    )
    burst_total_floor = max(
        float(amounts.get("p90", 0.0) or 0.0) * min_credit_count,
        float(amounts.get("p99", 0.0) or 0.0),
    )

    credits = frame[
        (frame["credit_amount"] >= material_credit_floor)
        & ~frame["narration"].fillna("").apply(
            lambda value: _contains_any_token(value, ORDINARY_PASS_THROUGH_CREDIT_TOKENS)
        )
    ].copy()
    debits = frame[
        (frame["debit_amount"] > config.money_epsilon)
        & ~frame["narration"].fillna("").apply(
            lambda value: _contains_any_token(value, ORDINARY_PASS_THROUGH_DEBIT_TOKENS)
        )
    ].copy()
    if len(credits) < min_credit_count or debits.empty:
        return None

    best: dict | None = None
    for start in credits.itertuples(index=False):
        start_date = start.parsed_date
        cluster = credits[
            (credits["parsed_date"] >= start_date)
            & ((credits["parsed_date"] - start_date).dt.days <= window_days)
        ].copy()
        if len(cluster) < min_credit_count:
            continue
        cluster_total = float(cluster["credit_amount"].sum())
        if cluster_total <= config.money_epsilon:
            continue
        if cluster_total < burst_total_floor:
            continue
        last_credit_order = int(cluster["source_order"].max())
        last_credit_date = cluster["parsed_date"].max()
        following_debits = debits[
            (debits["parsed_date"] >= start_date)
            & ((debits["parsed_date"] - last_credit_date).dt.days <= window_days)
            & (debits["source_order"] > last_credit_order)
        ].copy()
        if following_debits.empty:
            continue
        debit_total = float(following_debits["debit_amount"].sum())
        clearance_ratio = safe_ratio(debit_total, cluster_total)
        if clearance_ratio < (1.0 - config.high_throughput_retention_max):
            continue
        txn_ids = (
            cluster["txn_id"].astype(str).tolist()
            + following_debits["txn_id"].astype(str).tolist()
        )
        evidence = {
            "credit_burst_count": int(len(cluster)),
            "credit_burst_total": cluster_total,
            "following_debit_count": int(len(following_debits)),
            "following_debit_total": debit_total,
            "clearance_ratio": clearance_ratio,
            "window_days": window_days,
            "material_credit_floor": material_credit_floor,
            "burst_total_floor": burst_total_floor,
            "credit_txn_ids": cluster["txn_id"].astype(str).tolist(),
            "debit_txn_ids": following_debits["txn_id"].astype(str).tolist(),
            "txn_ids": list(dict.fromkeys(txn_ids)),
        }
        if best is None or evidence["credit_burst_total"] > best["credit_burst_total"]:
            best = evidence
    return best


def detect_high_throughput_pass_through(
    connection: sqlite3.Connection,
    baseline: dict,
    graph: nx.MultiDiGraph,
    config: AnalysisConfig,
) -> list:
    thresholds = baseline["thresholds"]
    accounts = pd.read_sql_query("SELECT * FROM accounts", connection)
    findings = []

    for row in accounts.itertuples(index=False):
        total_credit = float(row.total_credit)
        total_debit = float(row.total_debit)
        total_volume = float(row.total_volume)

        if total_volume < thresholds["high_throughput_volume_min"]:
            continue

        # Retention is how much stays; pass-through means very little stays
        if total_credit < config.money_epsilon:
            continue
        retention = safe_ratio(abs(total_credit - total_debit), total_credit)
        if retention > config.high_throughput_retention_max:
            continue

        # Must have multiple counterparties on both sides
        node = str(row.account_id)
        in_edges = list(graph.in_edges(node, data=True))
        out_edges = list(graph.out_edges(node, data=True))
        in_sources = {src for src, _, _ in in_edges if src != node}
        out_targets = {tgt for _, tgt, _ in out_edges if tgt != node}

        if len(in_sources) < config.high_throughput_min_counterparties:
            continue
        if len(out_targets) < 1:
            continue

        burst_evidence = _pass_through_burst_evidence(
            connection, str(row.account_id), baseline, config
        )
        if not burst_evidence:
            continue

        # Gather transaction IDs from all incident edges
        txn_ids = list(burst_evidence["txn_ids"])
        for edges in (in_edges, out_edges):
            for edge_tuple in edges:
                edge_data = edge_tuple[2] if len(edge_tuple) > 2 else {}
                txn_ids.extend(edge_data.get("txn_ids", [edge_data.get("txn_id", "")]))
        txn_ids = [tid for tid in txn_ids if tid]

        findings.append(
            make_finding(
                connection,
                3,
                [node],
                txn_ids,
                f"Account {node} received {total_credit:.2f} from {len(in_sources)} sources "
                f"and disbursed {total_debit:.2f} to {len(out_targets)} targets, "
                f"retaining only {retention:.1%} of inflow — consistent with high-throughput pass-through.",
                {
                    "total_credit": total_credit,
                    "total_debit": total_debit,
                    "retention_ratio": retention,
                    "inbound_source_count": len(in_sources),
                    "outbound_target_count": len(out_targets),
                    "localized_pass_through_evidence": burst_evidence,
                    "runtime_thresholds": {
                        "volume_min": thresholds["high_throughput_volume_min"],
                        "retention_max": config.high_throughput_retention_max,
                        "min_counterparties": config.high_throughput_min_counterparties,
                        "localized_window_days": burst_evidence["window_days"],
                        "material_credit_floor": burst_evidence["material_credit_floor"],
                        "burst_total_floor": burst_evidence["burst_total_floor"],
                    },
                },
            )
        )
        if len(findings) >= config.maximum_findings_per_pattern:
            break

    return findings
