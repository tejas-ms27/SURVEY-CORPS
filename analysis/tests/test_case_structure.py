"""Case reconstruction should cluster evidence, not raw payment noise."""

import sys
from pathlib import Path

import networkx as nx

PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))

from analysis_engine.case_structure import build_case_structure
from analysis_engine.models import Finding


def _graph() -> nx.MultiDiGraph:
    graph = nx.MultiDiGraph()
    for account in ["A", "B", "C", "D"]:
        graph.add_node(account, observed_account=True)
    graph.add_node("common@upi", observed_account=False)
    graph.add_node("fraud@upi", observed_account=False)

    for account in ["A", "B", "C", "D"]:
        graph.add_edge(
            account,
            "common@upi",
            key=f"{account}_common",
            txn_id=f"{account}_common",
            txn_ids=[f"{account}_common"],
            amount=100.0,
            confidence_score=0.40,
            counterparty_resolution_confidence=0.40,
            reference="",
            ledger_pair_id="",
        )

    graph.add_edge(
        "A",
        "fraud@upi",
        key="A_fraud",
        txn_id="A_fraud",
        txn_ids=["A_fraud"],
        amount=50000.0,
        confidence_score=0.40,
        counterparty_resolution_confidence=0.40,
        reference="",
        ledger_pair_id="",
    )
    graph.add_edge(
        "A",
        "B",
        key="A_B_weak",
        txn_id="A_B_weak",
        txn_ids=["A_B_weak"],
        amount=2500.0,
        confidence_score=0.40,
        counterparty_resolution_confidence=0.40,
        reference="",
        ledger_pair_id="",
    )
    graph.add_edge(
        "C",
        "D",
        key="C_D_pattern",
        txn_id="C_D_pattern",
        txn_ids=["C_D_pattern"],
        amount=90000.0,
        confidence_score=0.40,
        counterparty_resolution_confidence=0.40,
        reference="",
        ledger_pair_id="",
    )
    graph.add_edge(
        "B",
        "common@upi",
        key="B_common_strong",
        txn_id="B_common_strong",
        txn_ids=["B_common_strong"],
        amount=75000.0,
        confidence_score=0.90,
        counterparty_resolution_confidence=0.90,
        reference="",
        ledger_pair_id="",
    )
    graph.add_edge(
        "B",
        "C",
        key="B_C_strong",
        txn_id="B_C_strong",
        txn_ids=["B_C_strong"],
        amount=75000.0,
        confidence_score=0.90,
        counterparty_resolution_confidence=0.90,
        reference="",
        ledger_pair_id="",
    )
    return graph


def test_case_reconstruction_filters_public_noise_but_keeps_evidence_edges():
    findings = {
        "8_money_trail_tracing": [
            Finding(
                8,
                "money_trail_tracing",
                ["C", "D"],
                ["C_D_pattern"],
                "pattern-supported edge",
                "",
            )
        ]
    }
    suspicious_accounts = [
        {"account_id": "A", "total_score": 10},
        {"account_id": "B", "total_score": 8},
        {"account_id": "C", "total_score": 7},
        {"account_id": "D", "total_score": 6},
    ]

    case_structure, _, _, display = build_case_structure(_graph(), findings, suspicious_accounts)
    edge_by_txn = {
        edge["txn_ids"][0]: edge
        for edge in display["edges"]
        if edge.get("txn_ids")
    }

    assert edge_by_txn["A_common"]["included_in_case_reconstruction"] is False
    assert edge_by_txn["A_common"]["reconstruction_reason"] == "filtered_high_degree_public_endpoint"
    assert edge_by_txn["A_fraud"]["included_in_case_reconstruction"] is True
    assert edge_by_txn["A_fraud"]["reconstruction_reason"] == "low_degree_endpoint"
    assert edge_by_txn["A_B_weak"]["included_in_case_reconstruction"] is False
    assert edge_by_txn["A_B_weak"]["reconstruction_reason"] == "filtered_weak_observed_observed"
    assert edge_by_txn["C_D_pattern"]["included_in_case_reconstruction"] is True
    assert edge_by_txn["C_D_pattern"]["reconstruction_reason"] == "pattern_supported"
    assert edge_by_txn["B_common_strong"]["included_in_case_reconstruction"] is False
    assert edge_by_txn["B_common_strong"]["reconstruction_reason"] == "filtered_high_degree_public_endpoint"
    assert edge_by_txn["B_C_strong"]["included_in_case_reconstruction"] is True
    assert edge_by_txn["B_C_strong"]["reconstruction_reason"] == "strong_observed_account_edge"

    assert case_structure["cluster_method"] == "evidence_protected_strong_edge_components"
    assert case_structure["reconstruction_graph"]["filtered_edge_count"] >= 2


def test_case_reconstruction_deduplicates_repeated_finding_groups_for_display():
    findings = {
        "17_round_trip_detection": [
            Finding(17, "round_trip_detection", ["A", "B"], ["A_B_weak"], "round trip one", ""),
            Finding(17, "round_trip_detection", ["B", "A"], ["rt2"], "round trip two", ""),
        ]
    }
    suspicious_accounts = [
        {"account_id": "A", "total_score": 10},
        {"account_id": "B", "total_score": 8},
    ]

    case_structure, _, _, _ = build_case_structure(_graph(), findings, suspicious_accounts)
    clusters = case_structure["clusters"]
    group = next(
        evidence_group
        for cluster in clusters
        for evidence_group in cluster["evidence_groups"]
        if evidence_group["pattern_id"] == 17 and evidence_group["accounts"] == ["A", "B"]
    )

    assert group["finding_count"] == 2
    assert group["txn_id_count"] == 2
