"""Post-run investigation graph generation.

This module is intentionally independent of detector logic and persistence.
It only reads the completed ``AnalysisResult`` plus the run SQLite connection
and writes optional PNG artifacts under ``<run_output>/graphs``.
"""

from __future__ import annotations

from collections import Counter, defaultdict
import json
import logging
import math
from pathlib import Path
from typing import Any, Iterable

import matplotlib

matplotlib.use("Agg")

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd

from .models import AnalysisResult, Finding, PATTERN_CATALOG

logger = logging.getLogger(__name__)

DPI = 300
LAYOUT_SEED = 42
MAX_VISIBLE_CLUSTER_NODES = 20
TOP_CLUSTER_GRAPH_COUNT = 3


def generate_investigation_graphs(
    result: AnalysisResult,
    output_dir: str | Path,
) -> dict[str, str]:
    """Generate post-analysis PNG graphs without affecting pipeline success.

    Individual graph failures are logged and skipped. No detector output,
    SQLite schema, JSON, or text summary is modified.
    """

    graphs_dir = Path(output_dir).expanduser().resolve() / "graphs"
    ui_dir = graphs_dir / "ui_graphs"
    report_dir = graphs_dir / "report_graphs"
    graphs_dir.mkdir(parents=True, exist_ok=True)
    ui_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)

    transactions = _load_transactions(result)
    generated: dict[str, str] = {}
    ui_tasks = [
        ("ui_graphs/money_flow_network_3d.json", _write_money_flow_network_ui),
        ("ui_graphs/balance_graph_all_accounts.json", _write_balance_graph_ui),
        ("ui_graphs/money_trail_all_accounts.json", _write_money_trail_ui),
        ("ui_graphs/sankey_flow.json", _write_sankey_ui),
    ]
    report_tasks = [
        ("report_graphs/case_overview_graph.png", _draw_case_overview_graph),
        ("report_graphs/suspicious_timeline.png", _draw_suspicious_timeline),
        ("report_graphs/fraud_pattern_summary.png", _draw_fraud_pattern_summary),
    ]

    for filename, writer in ui_tasks:
        path = graphs_dir / filename
        try:
            created = writer(result, transactions, path)
        except Exception:
            logger.exception("Skipping graph %s after generation failure", filename)
            created = False
        if created:
            generated[filename] = str(path)
            logger.info("Generated UI graph data: %s", path)
        else:
            logger.info("Skipped investigation graph due to insufficient data: %s", filename)

    for filename, drawer in report_tasks:
        path = graphs_dir / filename
        try:
            created = drawer(result, transactions, path)
        except Exception:
            logger.exception("Skipping graph %s after generation failure", filename)
            created = False
        if created:
            generated[filename] = str(path)
            logger.info("Generated report graph: %s", path)
        else:
            logger.info("Skipped report graph due to insufficient data: %s", filename)

    top_cluster_outputs = _draw_top_cluster_graphs(result, transactions, report_dir)
    generated.update(top_cluster_outputs)

    legacy_tasks = [
        ("money_flow_network.png", report_dir / "account_interconnection_graph.png"),
        ("case_overview_graph.png", report_dir / "case_overview_graph.png"),
        ("suspicious_timeline.png", report_dir / "suspicious_timeline.png"),
        ("fraud_pattern_summary.png", report_dir / "fraud_pattern_summary.png"),
    ]
    for filename, source in legacy_tasks:
        target = graphs_dir / filename
        if source.exists():
            target.write_bytes(source.read_bytes())
            generated[filename] = str(target)

    return generated


def _write_json(path: Path, payload: dict[str, Any]) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, default=str, sort_keys=True, indent=2), encoding="utf-8")
    return path.stat().st_size > 0


def _write_money_flow_network_ui(result: AnalysisResult, transactions: pd.DataFrame, path: Path) -> bool:
    payload = getattr(result, "network_graph_for_display", {}) or {}
    if not payload:
        payload = nx.node_link_data(result.graph, edges="edges") if result.graph is not None else {}
    if isinstance(payload, dict) and payload.get("edges"):
        payload = _ui_scoped_network_payload(result, payload)
    return _write_json(path, {"type": "money_flow_network_3d", "data": payload})


def _write_balance_graph_ui(result: AnalysisResult, transactions: pd.DataFrame, path: Path) -> bool:
    if transactions.empty or "account_id" not in transactions:
        return False
    frame = transactions.copy()
    frame["amount"] = frame["credit_amount"].astype(float) - frame["debit_amount"].astype(float)
    payload = []
    for account, group in frame.groupby("account_id", sort=True):
        payload.append(
            {
                "account_id": str(account),
                "points": [
                    {
                        "date": str(row.date or ""),
                        "txn_id": str(row.txn_id),
                        "balance": None if pd.isna(row.balance) else float(row.balance),
                        "net_amount": float(row.amount),
                    }
                    for row in group.itertuples(index=False)
                ],
            }
        )
    return _write_json(path, {"type": "balance_graph_all_accounts", "accounts": payload})


def _write_money_trail_ui(result: AnalysisResult, transactions: pd.DataFrame, path: Path) -> bool:
    trails = []
    for _, finding in _flatten_findings(result):
        if int(getattr(finding, "pattern_id", 0) or 0) != 8:
            continue
        details = _details(finding)
        trails.append(
            {
                "finding_id": getattr(finding, "finding_id", ""),
                "accounts": _accounts(finding),
                "source_credit_txn_id": details.get("source_credit_txn_id"),
                "credited_amount": details.get("credited_amount"),
                "trace_status": details.get("trace_status"),
                "allocations": details.get("allocations", []),
            }
        )
    return _write_json(path, {"type": "money_trail_all_accounts", "trails": trails})


def _write_sankey_ui(result: AnalysisResult, transactions: pd.DataFrame, path: Path) -> bool:
    clusters = getattr(result, "case_structure", {}).get("account_to_cluster", {}) if getattr(result, "case_structure", None) else {}
    flows: dict[tuple[str, str], float] = defaultdict(float)
    payload = _filtered_display_payload(getattr(result, "network_graph_for_display", {}) or {})
    for edge in payload.get("edges", []) or []:
        source = str(edge.get("source", ""))
        target = str(edge.get("target", ""))
        source_cluster = clusters.get(source, source)
        target_cluster = clusters.get(target, target)
        if not source_cluster or not target_cluster or source_cluster == target_cluster:
            continue
        flows[(source_cluster, target_cluster)] += _as_float(edge.get("amount"))
    payload = [
        {"source": source, "target": target, "amount": amount}
        for (source, target), amount in sorted(flows.items())
        if amount > 0
    ]
    return _write_json(path, {"type": "sankey_flow", "flows": payload})


def _load_transactions(result: AnalysisResult) -> pd.DataFrame:
    connection = getattr(result, "_connection", None)
    if connection is None:
        return pd.DataFrame()
    try:
        return pd.read_sql_query(
            """
            SELECT row_id, source_order, txn_id, account_id, source_account_id,
                   date, time, narration, narration_normalized, reference,
                   debit_amount, credit_amount, balance, counterparty_account,
                   counterparty_name_raw, counterparty_resolution_method,
                   counterparty_resolution_confidence, eligible_for_detection
            FROM transactions
            WHERE eligible_for_detection = 1
            ORDER BY date, time, source_order, row_id
            """,
            connection,
        )
    except Exception:
        logger.exception("Unable to read transactions for investigation graphs")
        return pd.DataFrame()


def _filtered_display_payload(payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return {"nodes": [], "edges": []}
    edges = [
        edge
        for edge in payload.get("edges", []) or []
        if isinstance(edge, dict) and bool(edge.get("included_in_case_reconstruction"))
    ]
    connected = {
        str(edge.get("source"))
        for edge in edges
        if str(edge.get("source", ""))
    }.union(
        str(edge.get("target"))
        for edge in edges
        if str(edge.get("target", ""))
    )
    nodes = [
        node
        for node in payload.get("nodes", []) or []
        if isinstance(node, dict) and str(node.get("id", "")) in connected
    ]
    return {"nodes": nodes, "edges": edges}


def _ui_scoped_network_payload(result: AnalysisResult, payload: dict[str, Any]) -> dict[str, Any]:
    filtered = _filtered_display_payload(payload)
    node_metadata = {
        str(node.get("id")): node
        for node in filtered.get("nodes", []) or []
        if str(node.get("id", ""))
    }
    selected_edges: list[dict[str, Any]] = []
    cluster_payloads = []
    for cluster in _cluster_rows(result)[:TOP_CLUSTER_GRAPH_COUNT]:
        cluster_id = str(cluster.get("cluster_id", ""))
        if not cluster_id:
            continue
        edge_totals: dict[tuple[str, str], dict[str, Any]] = {}
        edge_rows: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
        for edge in filtered.get("edges", []) or []:
            source = str(edge.get("source", ""))
            target = str(edge.get("target", ""))
            if (
                node_metadata.get(source, {}).get("cluster_id") != cluster_id
                and node_metadata.get(target, {}).get("cluster_id") != cluster_id
            ):
                continue
            pair = (source, target)
            bucket = edge_totals.setdefault(
                pair,
                {
                    "amount": 0.0,
                    "reconstruction_reason": edge.get("reconstruction_reason", ""),
                    "pattern_supported": bool(edge.get("pattern_supported")),
                },
            )
            bucket["amount"] += _as_float(edge.get("amount"))
            edge_rows[pair].append(edge)
        selected_pairs = _select_cluster_edges(edge_totals, node_metadata, MAX_VISIBLE_CLUSTER_NODES)
        selected_pair_set = {pair for pair, _ in selected_pairs}
        cluster_edges = [
            edge
            for pair in selected_pair_set
            for edge in edge_rows.get(pair, [])[:3]
        ]
        cluster_nodes = sorted({
            str(edge.get("source"))
            for edge in cluster_edges
        }.union(str(edge.get("target")) for edge in cluster_edges))
        selected_edges.extend(cluster_edges)
        cluster_payloads.append(
            {
                "cluster_id": cluster_id,
                "risk_label": _cluster_risk_label(cluster),
                "visible_node_count": len(cluster_nodes),
                "visible_edge_count": len(cluster_edges),
                "omitted_node_count": max(
                    0,
                    len(set(cluster.get("cluster_nodes", cluster.get("member_accounts", [])) or [])) - len(cluster_nodes),
                ),
            }
        )

    selected_ids = {
        str(edge.get("source"))
        for edge in selected_edges
    }.union(str(edge.get("target")) for edge in selected_edges)
    return {
        "nodes": [node for node_id, node in sorted(node_metadata.items()) if node_id in selected_ids],
        "edges": selected_edges,
        "clusters": cluster_payloads,
        "scope": "top_reconstruction_clusters_capped",
        "max_visible_nodes_per_cluster": MAX_VISIBLE_CLUSTER_NODES,
        "raw_filtered_node_count": len(filtered.get("nodes", []) or []),
        "raw_filtered_edge_count": len(filtered.get("edges", []) or []),
    }


def _cluster_rows(result: AnalysisResult) -> list[dict[str, Any]]:
    clusters = (getattr(result, "case_structure", {}) or {}).get("clusters", []) or []
    return sorted(
        [cluster for cluster in clusters if not cluster.get("is_isolated")],
        key=lambda item: (-_as_float(item.get("total_score")), -int(item.get("edge_count", 0) or 0), str(item.get("cluster_id", ""))),
    )


def _cluster_risk_label(cluster: dict[str, Any]) -> str:
    score = _as_float(cluster.get("total_score"))
    pattern_count = len(cluster.get("pattern_ids", []) or [])
    if score >= 600 or pattern_count >= 3:
        return "High risk"
    if score >= 300 or pattern_count >= 2:
        return "Medium risk"
    return "Watchlist"


def _draw_top_cluster_graphs(
    result: AnalysisResult,
    transactions: pd.DataFrame,
    report_dir: Path,
) -> dict[str, str]:
    generated: dict[str, str] = {}
    top_clusters = _cluster_rows(result)[:TOP_CLUSTER_GRAPH_COUNT]
    for index, cluster in enumerate(top_clusters):
        cluster_id = str(cluster.get("cluster_id") or f"cluster_{index + 1:03d}")
        cluster_dir = report_dir / "clusters" / cluster_id
        cluster_dir.mkdir(parents=True, exist_ok=True)
        tasks = [
            ("account_interconnection_graph.png", _draw_money_flow_network),
            ("balance_cashflow_trend.png", _draw_balance_cashflow_trend),
            ("money_trail_flow.png", _draw_money_trail_flow),
            ("money_trail_sankey.png", _draw_money_trail_sankey),
        ]
        for filename, drawer in tasks:
            path = cluster_dir / filename
            try:
                created = drawer(result, transactions, path, cluster)
            except Exception:
                logger.exception("Skipping cluster graph %s/%s after generation failure", cluster_id, filename)
                created = False
            if created:
                rel = f"report_graphs/clusters/{cluster_id}/{filename}"
                generated[rel] = str(path)
                if index == 0:
                    compatibility_path = report_dir / filename
                    compatibility_path.write_bytes(path.read_bytes())
                    generated[f"report_graphs/{filename}"] = str(compatibility_path)
        if index == 0 and not (report_dir / "account_interconnection_graph.png").exists():
            fallback = cluster_dir / "account_interconnection_graph.png"
            if fallback.exists():
                (report_dir / "account_interconnection_graph.png").write_bytes(fallback.read_bytes())
    return generated


def _draw_case_overview_graph(
    result: AnalysisResult,
    transactions: pd.DataFrame,
    path: Path,
) -> bool:
    del transactions
    clusters = _cluster_rows(result)
    if not clusters:
        return False

    overview = nx.Graph()
    for cluster in clusters:
        cluster_id = str(cluster.get("cluster_id", ""))
        if not cluster_id:
            continue
        overview.add_node(
            cluster_id,
            score=_as_float(cluster.get("total_score")),
            account_count=int(cluster.get("account_count", 0) or 0),
            edge_count=int(cluster.get("edge_count", 0) or 0),
            risk_label=_cluster_risk_label(cluster),
        )
    if overview.number_of_nodes() == 0:
        return False

    display = _filtered_display_payload(getattr(result, "network_graph_for_display", {}) or {})
    node_cluster = {
        str(node.get("id")): str(node.get("cluster_id"))
        for node in display.get("nodes", []) or []
        if str(node.get("id", "")) and str(node.get("cluster_id", ""))
    }
    cluster_flows: Counter[tuple[str, str]] = Counter()
    for edge in display.get("edges", []) or []:
        source_cluster = node_cluster.get(str(edge.get("source", "")), "")
        target_cluster = node_cluster.get(str(edge.get("target", "")), "")
        if source_cluster and target_cluster and source_cluster != target_cluster:
            pair = tuple(sorted((source_cluster, target_cluster)))
            cluster_flows[pair] += _as_float(edge.get("amount"))
    for (source, target), amount in cluster_flows.items():
        if overview.has_node(source) and overview.has_node(target):
            overview.add_edge(source, target, amount=float(amount))

    fig, ax = plt.subplots(figsize=(12, 8), facecolor="white")
    ax.set_facecolor("white")
    if overview.number_of_nodes() == 1:
        pos = {next(iter(overview.nodes())): (0.0, 0.0)}
    else:
        pos = nx.spring_layout(overview, seed=LAYOUT_SEED, k=1.8)

    max_score = max((_as_float(data.get("score")) for _, data in overview.nodes(data=True)), default=1.0)
    sizes = [
        1600 + 2600 * (_as_float(data.get("score")) / max(max_score, 1.0))
        for _, data in overview.nodes(data=True)
    ]
    colors = [
        "#d73027" if data.get("risk_label") == "High risk" else "#fdae61" if data.get("risk_label") == "Medium risk" else "#fee08b"
        for _, data in overview.nodes(data=True)
    ]
    widths = [
        1.0 + 4.0 * math.log1p(_as_float(data.get("amount"))) / max(math.log1p(max((_as_float(v.get("amount")) for _, _, v in overview.edges(data=True)), default=1.0)), 1.0)
        for _, _, data in overview.edges(data=True)
    ]
    if overview.number_of_edges() > 0:
        nx.draw_networkx_edges(
            overview,
            pos,
            ax=ax,
            width=widths,
            edge_color="#868e96",
            alpha=0.6,
        )
    nx.draw_networkx_nodes(
        overview,
        pos,
        ax=ax,
        node_size=sizes,
        node_color=colors,
        edgecolors="#343a40",
        linewidths=1.2,
    )
    labels = {
        node: f"{node}\n{data.get('risk_label')}\n{data.get('account_count')} acct / {data.get('edge_count')} edge"
        for node, data in overview.nodes(data=True)
    }
    nx.draw_networkx_labels(overview, pos, labels=labels, ax=ax, font_size=8, font_weight="bold")
    ax.set_title("Case Overview Graph", fontsize=18, fontweight="bold", pad=14)
    ax.text(
        0.5,
        -0.04,
        "Each node is a reconstructed case cluster. Detailed account-level graphs are generated only for the highest-risk clusters.",
        transform=ax.transAxes,
        ha="center",
        fontsize=9,
        color="#495057",
    )
    ax.axis("off")
    _save_figure(fig, path)
    return True


def _draw_money_flow_network(
    result: AnalysisResult,
    transactions: pd.DataFrame,
    path: Path,
    cluster: dict[str, Any] | None = None,
) -> bool:
    del transactions
    display_graph = getattr(result, "network_graph_for_display", {}) or {}
    display_graph = _filtered_display_payload(display_graph)
    node_metadata = {
        _clean_text(node.get("id")): node
        for node in display_graph.get("nodes", [])
        if isinstance(node, dict) and _clean_text(node.get("id"))
    }
    display_edges = display_graph.get("edges", [])

    if display_edges:
        raw_edges = [
            (edge.get("source"), edge.get("target"), edge)
            for edge in display_edges
            if isinstance(edge, dict)
        ]
    else:
        graph = result.graph
        if graph is None or graph.number_of_edges() == 0:
            return False
        raw_edges = list(graph.edges(data=True))
        if not node_metadata:
            node_metadata = {
                _clean_text(node): {"id": _clean_text(node), "cluster_id": "cluster_unknown"}
                for node in graph.nodes()
                if _clean_text(node)
            }

    cluster_id = str(cluster.get("cluster_id", "")) if cluster else ""
    cluster_members = set(
        str(item)
        for item in (cluster or {}).get("cluster_nodes", (cluster or {}).get("member_accounts", []))
        if str(item)
    )
    edge_totals: dict[tuple[str, str], dict[str, Any]] = {}
    for source, target, data in raw_edges:
        amount = _as_float(data.get("amount"))
        if amount <= 0:
            continue
        clean_source = _clean_text(source)
        clean_target = _clean_text(target)
        if not clean_source or not clean_target:
            continue
        if cluster_id:
            source_cluster = node_metadata.get(clean_source, {}).get("cluster_id", "")
            target_cluster = node_metadata.get(clean_target, {}).get("cluster_id", "")
            if source_cluster != cluster_id and target_cluster != cluster_id:
                continue
            if cluster_members and clean_source not in cluster_members and clean_target not in cluster_members:
                continue
        pair = (clean_source, clean_target)
        bucket = edge_totals.setdefault(
            pair,
            {
                "amount": 0.0,
                "count": 0,
                "txn_ids": [],
                "dates": [],
                "source_cluster": node_metadata.get(clean_source, {}).get("cluster_id", "cluster_unknown"),
                "target_cluster": node_metadata.get(clean_target, {}).get("cluster_id", "cluster_unknown"),
                "reconstruction_reason": data.get("reconstruction_reason", ""),
                "pattern_supported": bool(data.get("pattern_supported")),
                "confidence_score": _as_float(data.get("confidence_score")),
            },
        )
        bucket["amount"] += amount
        bucket["count"] += 1
        if data.get("txn_id"):
            bucket["txn_ids"].append(str(data["txn_id"]))
        for txn_id in data.get("txn_ids", []) or []:
            bucket["txn_ids"].append(str(txn_id))
        if data.get("date"):
            bucket["dates"].append(str(data["date"]))

    if not edge_totals:
        return False

    selected = _select_cluster_edges(edge_totals, node_metadata, MAX_VISIBLE_CLUSTER_NODES)
    flow_graph = nx.DiGraph()
    for (source, target), data in selected:
        flow_graph.add_node(source, **node_metadata.get(source, {}))
        flow_graph.add_node(target, **node_metadata.get(target, {}))
        flow_graph.add_edge(source, target, **data)

    if flow_graph.number_of_edges() == 0:
        return False

    suspicious = _suspicious_account_ids(result)
    cycle_accounts = _cycle_account_ids(result)

    plt.style.use("default")
    fig, ax = plt.subplots(figsize=(14, 10), facecolor="white")
    ax.set_facecolor("white")

    pos = _stable_network_positions(flow_graph)
    max_amount = max(data["amount"] for _, _, data in flow_graph.edges(data=True))
    widths = [
        0.8 + 5.2 * math.log1p(data["amount"]) / max(math.log1p(max_amount), 1.0)
        for _, _, data in flow_graph.edges(data=True)
    ]

    node_colors = []
    node_sizes = []
    edge_colors = []
    for node in flow_graph.nodes():
        metadata = node_metadata.get(str(node), {})
        score = _as_float(metadata.get("total_score"))
        tiers = {int(tier) for tier in metadata.get("suspicion_tiers", []) if str(tier).isdigit()}
        node_sizes.append(360 + min(score, 800.0) * 0.55)
        if node in suspicious or 1 in tiers:
            node_colors.append("#d7191c")
        elif 2 in tiers:
            node_colors.append("#fdae61")
        elif 3 in tiers:
            node_colors.append("#fee08b")
        else:
            node_colors.append("#e9ecef")
        edge_colors.append("#7b1e3b" if node in cycle_accounts else "#495057")

    edge_colors_by_reason = [_edge_style(data.get("reconstruction_reason", ""), bool(data.get("pattern_supported")))[0] for _, _, data in flow_graph.edges(data=True)]
    edge_styles = [_edge_style(data.get("reconstruction_reason", ""), bool(data.get("pattern_supported")))[1] for _, _, data in flow_graph.edges(data=True)]
    for style in sorted(set(edge_styles)):
        styled_edges = [
            (source, target)
            for source, target, data in flow_graph.edges(data=True)
            if _edge_style(data.get("reconstruction_reason", ""), bool(data.get("pattern_supported")))[1] == style
        ]
        styled_widths = [
            widths[idx]
            for idx, (_, _, data) in enumerate(flow_graph.edges(data=True))
            if _edge_style(data.get("reconstruction_reason", ""), bool(data.get("pattern_supported")))[1] == style
        ]
        styled_colors = [
            edge_colors_by_reason[idx]
            for idx, (_, _, data) in enumerate(flow_graph.edges(data=True))
            if _edge_style(data.get("reconstruction_reason", ""), bool(data.get("pattern_supported")))[1] == style
        ]
        nx.draw_networkx_edges(
            flow_graph,
            pos,
            edgelist=styled_edges,
            ax=ax,
            width=styled_widths,
            edge_color=styled_colors,
            arrows=True,
            arrowsize=16,
            alpha=0.76,
            style=style,
            connectionstyle="arc3,rad=0.08",
        )
    nx.draw_networkx_nodes(
        flow_graph,
        pos,
        ax=ax,
        node_size=node_sizes,
        node_color=node_colors,
        edgecolors=edge_colors,
        linewidths=1.5,
    )
    _draw_offset_labels(ax, pos, _top_label_nodes(flow_graph, limit=5), limit=18, font_size=8)
    edge_label_thresholds = _cluster_edge_label_thresholds(flow_graph)
    labeled_edges = dict(
        sorted(
            {
                (source, target): _format_amount(data["amount"])
                for source, target, data in flow_graph.edges(data=True)
                if data["amount"] >= edge_label_thresholds.get(data.get("source_cluster"), 0.0)
            }.items(),
            key=lambda item: (-flow_graph.edges[item[0]]["amount"], item[0][0], item[0][1]),
        )[:16]
    )
    nx.draw_networkx_edge_labels(
        flow_graph,
        pos,
        edge_labels=labeled_edges,
        ax=ax,
        font_size=6,
        font_color="#343a40",
        rotate=False,
    )

    _add_legend(
        ax,
        [
            ("Tier 1 / suspicious account", "#d7191c"),
            ("Tier 2 evidence", "#fdae61"),
            ("Tier 3 weak signal", "#fee08b"),
            ("Other node", "#e9ecef"),
            ("Cycle/round-trip outline", "#7b1e3b"),
        ],
    )
    title = "Account Interconnection Graph"
    if cluster:
        title = f"Account Interconnection Graph - {cluster_id} ({_cluster_risk_label(cluster)})"
    ax.set_title(title, fontsize=18, fontweight="bold", pad=16)
    omitted = _omitted_node_count(edge_totals, flow_graph)
    if omitted > 0:
        ax.text(
            0.99,
            0.02,
            f"+{omitted} more account(s) in raw data",
            transform=ax.transAxes,
            ha="right",
            va="bottom",
            fontsize=9,
            color="#495057",
            bbox={"boxstyle": "round,pad=0.35", "facecolor": "white", "edgecolor": "#ced4da"},
        )
    ax.text(
        0.5,
        -0.035,
        "Only reconstruction-included evidence edges are drawn. Edge width follows amount; color/style follows reconstruction reason.",
        transform=ax.transAxes,
        ha="center",
        fontsize=9,
        color="#495057",
    )
    ax.axis("off")
    _save_figure(fig, path)
    return True


def _draw_money_trail_sankey(
    result: AnalysisResult,
    transactions: pd.DataFrame,
    path: Path,
    cluster: dict[str, Any] | None = None,
) -> bool:
    trail = _highest_risk_money_trail(result, cluster)
    if trail is None:
        return False
    details = _details(trail)
    credited_amount = _as_float(details.get("credited_amount"))
    allocations = [item for item in details.get("allocations", []) if _as_float(item.get("allocated_from_credit")) > 0]
    if credited_amount <= 0 or not allocations:
        return False

    try:
        import plotly.graph_objects as go
    except Exception:
        logger.info("Plotly is not installed; money_trail_sankey.png cannot be exported")
        return False

    lookup = _transaction_lookup(transactions)
    account = _first_account(trail)
    source = _source_label(details, lookup)
    destination_totals = _allocation_destination_totals(allocations, lookup)
    if not destination_totals:
        return False

    labels = [source, account]
    label_index = {source: 0, account: 1}
    link_sources = [0]
    link_targets = [1]
    link_values = [credited_amount]

    for destination, amount in sorted(destination_totals.items(), key=lambda item: (-item[1], item[0]))[:20]:
        if destination not in label_index:
            label_index[destination] = len(labels)
            labels.append(destination)
        link_sources.append(label_index[account])
        link_targets.append(label_index[destination])
        link_values.append(amount)

    fig = go.Figure(
        data=[
            go.Sankey(
                arrangement="fixed",
                node={
                    "pad": 18,
                    "thickness": 18,
                    "line": {"color": "#343a40", "width": 0.5},
                    "label": [_short_label(label, limit=26) for label in labels],
                    "color": ["#6c757d", "#d7191c"] + ["#2c7bb6"] * (len(labels) - 2),
                },
                link={
                    "source": link_sources,
                    "target": link_targets,
                    "value": link_values,
                    "color": "rgba(116, 125, 140, 0.45)",
                },
            )
        ]
    )
    fig.update_layout(
        title_text=_cluster_title("Money Trail Sankey", cluster),
        font_size=12,
        paper_bgcolor="white",
        plot_bgcolor="white",
        width=1400,
        height=850,
        margin={"l": 40, "r": 40, "t": 80, "b": 40},
    )
    try:
        fig.write_image(str(path), scale=2)
    except Exception:
        logger.exception("Plotly image export failed for %s", path.name)
        return False
    return path.exists()


def _draw_suspicious_timeline(
    result: AnalysisResult,
    transactions: pd.DataFrame,
    path: Path,
) -> bool:
    if transactions.empty:
        return False
    txn_patterns = _txn_pattern_map(result)
    if not txn_patterns:
        return False

    frame = transactions[transactions["txn_id"].astype(str).isin(txn_patterns)].copy()
    if frame.empty:
        return False
    frame["date_dt"] = pd.to_datetime(frame["date"], errors="coerce")
    frame = frame.dropna(subset=["date_dt"])
    if frame.empty:
        return False

    frame["amount"] = frame[["debit_amount", "credit_amount"]].apply(
        lambda row: max(_as_float(row["debit_amount"]), _as_float(row["credit_amount"])),
        axis=1,
    )
    frame = frame[frame["amount"] > 0]
    if frame.empty:
        return False
    frame["category"] = frame.apply(lambda row: _timeline_category(row, txn_patterns), axis=1)

    categories = [
        "Large credit",
        "Large debit",
        "Round trip",
        "Layering",
        "Cash withdrawal",
        "Structuring",
        "Money trail",
        "Other suspicious",
    ]
    colors = {
        "Large credit": "#1a9850",
        "Large debit": "#d73027",
        "Round trip": "#7b3294",
        "Layering": "#fdae61",
        "Cash withdrawal": "#2c7bb6",
        "Structuring": "#e66101",
        "Money trail": "#313695",
        "Other suspicious": "#6c757d",
    }

    fig, ax = plt.subplots(figsize=(14, 7), facecolor="white")
    ax.set_facecolor("white")
    for category in categories:
        subset = frame[frame["category"] == category]
        if subset.empty:
            continue
        ax.scatter(
            subset["date_dt"],
            subset["amount"],
            label=category,
            s=42,
            color=colors[category],
            alpha=0.82,
            edgecolors="white",
            linewidths=0.5,
        )

    top_rows = frame.sort_values(["amount", "txn_id"], ascending=[False, True]).head(12)
    for _, row in top_rows.iterrows():
        ax.annotate(
            _short_label(str(row["txn_id"]), limit=16),
            (row["date_dt"], row["amount"]),
            xytext=(4, 6),
            textcoords="offset points",
            fontsize=6,
            color="#343a40",
        )

    ax.set_title("Suspicious Transaction Timeline", fontsize=18, fontweight="bold", pad=14)
    ax.set_xlabel("Date")
    ax.set_ylabel("Transaction amount")
    ax.yaxis.set_major_formatter(lambda value, _: _format_amount(value))
    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter(ax.xaxis.get_major_locator()))
    ax.grid(True, axis="y", color="#dee2e6", linewidth=0.7)
    ax.legend(loc="upper left", ncols=2, frameon=True, facecolor="white")
    fig.autofmt_xdate()
    _save_figure(fig, path)
    return True


def _draw_fraud_pattern_summary(
    result: AnalysisResult,
    transactions: pd.DataFrame,
    path: Path,
) -> bool:
    counts: list[tuple[str, int]] = []
    for key, findings in result.findings_by_pattern.items():
        pattern_id = _pattern_id_from_key(key)
        if pattern_id == 6:
            continue
        count = len(findings or [])
        if count <= 0:
            continue
        label = PATTERN_CATALOG.get(pattern_id, key)
        counts.append((_title_label(label), count))

    if not counts:
        return False

    counts = sorted(counts, key=lambda item: (item[1], item[0]))
    labels = [item[0] for item in counts]
    values = [item[1] for item in counts]

    height = max(5.0, 0.42 * len(labels) + 1.8)
    fig, ax = plt.subplots(figsize=(12, height), facecolor="white")
    ax.set_facecolor("white")
    bars = ax.barh(labels, values, color="#2c7bb6", edgecolor="#1b4f72")
    ax.set_title("Fraud Pattern Summary", fontsize=18, fontweight="bold", pad=14)
    ax.set_xlabel("Detection count")
    ax.grid(True, axis="x", color="#dee2e6", linewidth=0.7)
    for bar, value in zip(bars, values):
        ax.text(
            bar.get_width() + max(values) * 0.015,
            bar.get_y() + bar.get_height() / 2,
            str(value),
            va="center",
            fontsize=9,
            color="#212529",
        )
    ax.set_xlim(0, max(values) * 1.15 + 1)
    _save_figure(fig, path)
    return True


def _draw_balance_cashflow_trend(
    result: AnalysisResult,
    transactions: pd.DataFrame,
    path: Path,
    cluster: dict[str, Any] | None = None,
) -> bool:
    if transactions.empty:
        return False
    account_id = _preferred_account(result, transactions, cluster)
    if not account_id:
        return False

    frame = transactions[transactions["account_id"].astype(str) == str(account_id)].copy()
    if frame.empty:
        return False
    frame["date_dt"] = pd.to_datetime(frame["date"], errors="coerce")
    frame = frame.dropna(subset=["date_dt"]).sort_values(["date_dt", "source_order", "row_id"])
    if frame.empty:
        return False

    frame["balance_num"] = pd.to_numeric(frame["balance"], errors="coerce")
    if frame["balance_num"].notna().sum() < 2:
        return False
    frame["debit_num"] = pd.to_numeric(frame["debit_amount"], errors="coerce").fillna(0.0)
    frame["credit_num"] = pd.to_numeric(frame["credit_amount"], errors="coerce").fillna(0.0)
    frame["balance_delta"] = frame["balance_num"].diff()

    fig, ax = plt.subplots(figsize=(14, 7), facecolor="white")
    ax.set_facecolor("white")
    ax.plot(
        frame["date_dt"],
        frame["balance_num"],
        color="#2c7bb6",
        linewidth=2.0,
        marker="o",
        markersize=3,
        label="Running balance",
    )

    positive = frame[frame["balance_delta"] > 0]
    negative = frame[frame["balance_delta"] < 0]
    pos_cut = positive["balance_delta"].quantile(0.90) if len(positive) >= 3 else None
    neg_cut = negative["balance_delta"].quantile(0.10) if len(negative) >= 3 else None
    sudden_increase = positive[positive["balance_delta"] >= pos_cut] if pos_cut is not None else positive.head(0)
    sudden_withdrawal = negative[negative["balance_delta"] <= neg_cut] if neg_cut is not None else negative.head(0)

    if not sudden_increase.empty:
        ax.scatter(
            sudden_increase["date_dt"],
            sudden_increase["balance_num"],
            s=72,
            color="#1a9850",
            edgecolors="white",
            linewidths=0.8,
            label="Sudden balance increase",
            zorder=3,
        )
    if not sudden_withdrawal.empty:
        ax.scatter(
            sudden_withdrawal["date_dt"],
            sudden_withdrawal["balance_num"],
            s=72,
            color="#d73027",
            edgecolors="white",
            linewidths=0.8,
            label="Sudden withdrawal / cash-out",
            zorder=3,
        )

    pattern_txns = _account_highlight_txns(result, account_id, {8, 9, 18})
    if pattern_txns:
        highlighted = frame[frame["txn_id"].astype(str).isin(pattern_txns)]
        if not highlighted.empty:
            ax.scatter(
                highlighted["date_dt"],
                highlighted["balance_num"],
                s=88,
                facecolors="none",
                edgecolors="#7b3294",
                linewidths=1.4,
                label="Money trail / dormant / cash-out evidence",
                zorder=4,
            )

    ax.set_title(
        f"{_cluster_title('Balance / Cash Flow Trend', cluster)} - {_short_label(account_id, limit=24)}",
        fontsize=18,
        fontweight="bold",
        pad=14,
    )
    ax.set_xlabel("Date")
    ax.set_ylabel("Running balance")
    ax.yaxis.set_major_formatter(lambda value, _: _format_amount(value))
    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter(ax.xaxis.get_major_locator()))
    ax.grid(True, axis="y", color="#dee2e6", linewidth=0.7)
    ax.legend(loc="best", frameon=True, facecolor="white")
    fig.autofmt_xdate()
    _save_figure(fig, path)
    return True


def _draw_money_trail_flow(
    result: AnalysisResult,
    transactions: pd.DataFrame,
    path: Path,
    cluster: dict[str, Any] | None = None,
) -> bool:
    trail = _highest_risk_money_trail(result, cluster)
    if trail is None:
        return False
    details = _details(trail)
    allocations = [item for item in details.get("allocations", []) if _as_float(item.get("allocated_from_credit")) > 0]
    if not allocations:
        return False

    lookup = _transaction_lookup(transactions)
    account = _first_account(trail)
    source = _source_label(details, lookup)
    credited_amount = _as_float(details.get("credited_amount"))

    trail_graph = nx.DiGraph()
    trail_graph.add_edge(source, account, amount=credited_amount, label=_format_amount(credited_amount))

    destination_totals = _allocation_destination_totals(allocations, lookup)
    if not destination_totals:
        return False
    for destination, amount in sorted(destination_totals.items(), key=lambda item: (-item[1], item[0]))[:18]:
        trail_graph.add_edge(account, destination, amount=amount, label=_format_amount(amount))

    fig, ax = plt.subplots(figsize=(13, 8), facecolor="white")
    ax.set_facecolor("white")
    pos = _layered_flow_positions(trail_graph, source, account)
    max_amount = max(data["amount"] for _, _, data in trail_graph.edges(data=True))
    widths = [
        1.0 + 5.0 * math.log1p(data["amount"]) / max(math.log1p(max_amount), 1.0)
        for _, _, data in trail_graph.edges(data=True)
    ]
    node_colors = [
        "#6c757d" if node == source else "#d7191c" if node == account else "#2c7bb6"
        for node in trail_graph.nodes()
    ]

    nx.draw_networkx_edges(
        trail_graph,
        pos,
        ax=ax,
        width=widths,
        edge_color="#747d8c",
        arrows=True,
        arrowsize=18,
        alpha=0.75,
        connectionstyle="arc3,rad=0.06",
    )
    nx.draw_networkx_nodes(
        trail_graph,
        pos,
        ax=ax,
        node_size=1200,
        node_color=node_colors,
        edgecolors="#343a40",
        linewidths=1.0,
    )
    nx.draw_networkx_labels(
        trail_graph,
        pos,
        labels={node: _short_label(node, limit=22) for node in trail_graph.nodes()},
        ax=ax,
        font_size=8,
        font_color="#111111",
    )
    nx.draw_networkx_edge_labels(
        trail_graph,
        pos,
        edge_labels={(u, v): data["label"] for u, v, data in trail_graph.edges(data=True)},
        ax=ax,
        font_size=8,
        font_color="#343a40",
        rotate=False,
    )
    ax.set_title(_cluster_title("Money Trail Flow Diagram", cluster), fontsize=18, fontweight="bold", pad=14)
    ax.text(
        0.5,
        -0.04,
        f"Trail starts at credit transaction {details.get('source_credit_txn_id', '')}",
        transform=ax.transAxes,
        ha="center",
        fontsize=9,
        color="#495057",
    )
    ax.axis("off")
    _save_figure(fig, path)
    return True


def _flatten_findings(result: AnalysisResult) -> Iterable[tuple[str, Finding]]:
    for key, findings in result.findings_by_pattern.items():
        for finding in findings or []:
            yield key, finding


def _details(finding: Finding | dict[str, Any]) -> dict[str, Any]:
    if isinstance(finding, dict):
        return finding.get("details", {}) or {}
    return finding.details or {}


def _accounts(finding: Finding | dict[str, Any]) -> list[str]:
    values = finding.get("accounts", []) if isinstance(finding, dict) else finding.accounts
    return [str(value) for value in values or [] if str(value)]


def _txn_ids(finding: Finding | dict[str, Any]) -> list[str]:
    values = finding.get("txn_ids", []) if isinstance(finding, dict) else finding.txn_ids
    return [str(value) for value in values or [] if str(value)]


def _pattern_id_from_key(key: str) -> int:
    try:
        return int(str(key).split("_", 1)[0])
    except Exception:
        return 0


def _first_account(finding: Finding | dict[str, Any]) -> str:
    accounts = _accounts(finding)
    return accounts[0] if accounts else "Observed account"


def _suspicious_account_ids(result: AnalysisResult) -> set[str]:
    accounts = {
        str(item.get("account_id"))
        for item in result.suspicious_accounts or []
        if item.get("account_id")
    }
    for key, finding in _flatten_findings(result):
        if _pattern_id_from_key(key) in {5, 7, 8, 10, 13, 16, 17, 18, 19, 21}:
            accounts.update(_accounts(finding))
    return accounts


def _hub_account_ids(result: AnalysisResult, graph: nx.Graph) -> set[str]:
    hubs = set()
    for key, finding in _flatten_findings(result):
        if _pattern_id_from_key(key) == 12:
            hubs.update(_accounts(finding))
    ranked = sorted(graph.degree, key=lambda item: (-item[1], str(item[0])))[:5]
    hubs.update(str(node) for node, _ in ranked)
    return hubs


def _cycle_account_ids(result: AnalysisResult) -> set[str]:
    accounts = set()
    for key, finding in _flatten_findings(result):
        if _pattern_id_from_key(key) in {7, 17}:
            accounts.update(_accounts(finding))
    return accounts


def _highest_risk_money_trail(result: AnalysisResult, cluster: dict[str, Any] | None = None) -> Finding | None:
    trails = list(result.findings_by_pattern.get("8_money_trail_tracing", []) or [])
    if cluster:
        members = set(str(item) for item in cluster.get("member_accounts", []) if str(item))
        trails = [trail for trail in trails if members.intersection(_accounts(trail))]
    if not trails:
        return None

    def score(finding: Finding) -> tuple[float, int, str]:
        details = _details(finding)
        amount = max(_as_float(details.get("credited_amount")), _as_float(details.get("traced_amount")))
        allocation_count = len(details.get("allocations", []) or [])
        return (amount, allocation_count, getattr(finding, "finding_id", ""))

    return sorted(trails, key=score, reverse=True)[0]


def _txn_pattern_map(result: AnalysisResult) -> dict[str, set[int]]:
    mapping: dict[str, set[int]] = defaultdict(set)
    for key, finding in _flatten_findings(result):
        pattern_id = _pattern_id_from_key(key)
        if pattern_id == 6:
            continue
        for txn_id in _txn_ids(finding):
            mapping[txn_id].add(pattern_id)
    return mapping


def _timeline_category(row: pd.Series, txn_patterns: dict[str, set[int]]) -> str:
    patterns = txn_patterns.get(str(row["txn_id"]), set())
    narration = str(row.get("narration", "") or "").lower()
    if patterns.intersection({7, 17}):
        return "Round trip"
    if patterns.intersection({3, 4, 10}):
        return "Layering"
    if 5 in patterns:
        return "Structuring"
    if 9 in patterns or "atm" in narration or "cash" in narration:
        return "Cash withdrawal"
    if 8 in patterns:
        return "Money trail"
    if _as_float(row.get("credit_amount")) >= _as_float(row.get("debit_amount")):
        return "Large credit"
    if _as_float(row.get("debit_amount")) > 0:
        return "Large debit"
    return "Other suspicious"


def _preferred_account(
    result: AnalysisResult,
    transactions: pd.DataFrame,
    cluster: dict[str, Any] | None = None,
) -> str:
    allowed = set(str(item) for item in (cluster or {}).get("member_accounts", []) if str(item))
    if result.suspicious_accounts:
        ranked = sorted(
            [
                item for item in result.suspicious_accounts
                if not allowed or str(item.get("account_id", "")) in allowed
            ],
            key=lambda item: (-_as_float(item.get("total_score")), str(item.get("account_id", ""))),
        )
        for item in ranked:
            account = str(item.get("account_id") or "")
            if account:
                return account
    if "account_id" not in transactions:
        return ""
    frame = transactions
    if allowed:
        frame = transactions[transactions["account_id"].astype(str).isin(allowed)]
    totals = (
        frame.assign(
            volume=pd.to_numeric(frame["debit_amount"], errors="coerce").fillna(0)
            + pd.to_numeric(frame["credit_amount"], errors="coerce").fillna(0)
        )
        .groupby("account_id")["volume"]
        .sum()
        .sort_values(ascending=False)
    )
    return str(totals.index[0]) if not totals.empty else ""


def _account_highlight_txns(result: AnalysisResult, account_id: str, pattern_ids: set[int]) -> set[str]:
    txns = set()
    for key, finding in _flatten_findings(result):
        if _pattern_id_from_key(key) not in pattern_ids:
            continue
        if str(account_id) in _accounts(finding):
            txns.update(_txn_ids(finding))
    return txns


def _transaction_lookup(transactions: pd.DataFrame) -> dict[str, dict[str, Any]]:
    if transactions.empty or "txn_id" not in transactions:
        return {}
    return {
        str(row["txn_id"]): row.to_dict()
        for _, row in transactions.iterrows()
    }


def _source_label(details: dict[str, Any], lookup: dict[str, dict[str, Any]]) -> str:
    context = details.get("source_credit_context", {}) or {}
    txn_id = str(details.get("source_credit_txn_id") or "")
    row = lookup.get(txn_id, {})
    for candidate in (
        context.get("counterparty_account"),
        row.get("counterparty_account"),
        context.get("counterparty_name_raw"),
        row.get("counterparty_name_raw"),
    ):
        cleaned = _clean_text(candidate)
        if cleaned:
            return cleaned
    return "Suspicious credit source"


def _allocation_destination_totals(
    allocations: list[dict[str, Any]],
    lookup: dict[str, dict[str, Any]],
) -> dict[str, float]:
    totals: Counter[str] = Counter()
    for allocation in allocations:
        amount = _as_float(allocation.get("allocated_from_credit"))
        if amount <= 0:
            continue
        txn_id = str(allocation.get("debit_txn_id") or "")
        row = lookup.get(txn_id, {})
        destination = _destination_label(allocation, row)
        totals[destination] += amount
    return dict(totals)


def _destination_label(allocation: dict[str, Any], row: dict[str, Any]) -> str:
    for candidate in (
        allocation.get("counterparty_account"),
        row.get("counterparty_account"),
        allocation.get("counterparty_name_raw"),
        row.get("counterparty_name_raw"),
    ):
        cleaned = _clean_text(candidate)
        if cleaned:
            return cleaned
    narration = str(row.get("narration") or allocation.get("narration") or "").strip()
    if narration:
        lower = narration.lower()
        if "atm" in lower or "cash" in lower or "withdraw" in lower:
            return "Cash / ATM withdrawal"
        return narration[:40]
    txn_id = _clean_text(allocation.get("debit_txn_id")) or _clean_text(row.get("txn_id"))
    return txn_id or "Unresolved destination"


def _select_cluster_edges(
    edge_totals: dict[tuple[str, str], dict[str, Any]],
    node_metadata: dict[str, dict[str, Any]],
    node_limit: int,
) -> list[tuple[tuple[str, str], dict[str, Any]]]:
    if not edge_totals:
        return []

    node_amounts: Counter[str] = Counter()
    node_degrees: Counter[str] = Counter()
    for (source, target), data in edge_totals.items():
        amount = _as_float(data.get("amount"))
        node_amounts[source] += amount
        node_amounts[target] += amount
        node_degrees[source] += 1
        node_degrees[target] += 1

    def node_rank(node: str) -> tuple[float, float, float, str]:
        metadata = node_metadata.get(node, {})
        return (
            _as_float(metadata.get("total_score")),
            float(node_degrees.get(node, 0)),
            float(node_amounts.get(node, 0.0)),
            node,
        )

    ranked_nodes = sorted(node_amounts, key=lambda node: node_rank(node), reverse=True)
    selected_nodes = set(ranked_nodes[:node_limit])
    selected = [
        (pair, data)
        for pair, data in edge_totals.items()
        if pair[0] in selected_nodes and pair[1] in selected_nodes
    ]
    if selected:
        return sorted(selected, key=lambda item: (-_as_float(item[1].get("amount")), item[0][0], item[0][1]))

    fallback: list[tuple[tuple[str, str], dict[str, Any]]] = []
    fallback_nodes: set[str] = set()
    for pair, data in sorted(edge_totals.items(), key=lambda item: (-_as_float(item[1].get("amount")), item[0][0], item[0][1])):
        if len(fallback_nodes.union(pair)) > node_limit:
            continue
        fallback.append((pair, data))
        fallback_nodes.update(pair)
    return fallback


def _stable_network_positions(graph: nx.DiGraph) -> dict[Any, tuple[float, float]]:
    if graph.number_of_nodes() <= 1:
        return {node: (0.0, 0.0) for node in graph.nodes()}
    try:
        return nx.kamada_kawai_layout(graph)
    except Exception:
        return nx.spring_layout(graph, seed=LAYOUT_SEED, k=1.2)


def _edge_style(reason: str, pattern_supported: bool) -> tuple[str, str]:
    if pattern_supported or reason == "pattern_supported":
        return "#d73027", "solid"
    if reason == "strong_confidence":
        return "#2c7bb6", "solid"
    if reason == "reference_or_ledger_corroborated":
        return "#1a9850", "dashed"
    if reason == "low_degree_endpoint":
        return "#6c757d", "dotted"
    return "#868e96", "solid"


def _top_label_nodes(graph: nx.DiGraph, limit: int = 5) -> list[Any]:
    return [
        node
        for node, _ in sorted(
            graph.degree,
            key=lambda item: (
                -_as_float(graph.nodes[item[0]].get("total_score")),
                -int(item[1]),
                str(item[0]),
            ),
        )[:limit]
    ]


def _omitted_node_count(
    edge_totals: dict[tuple[str, str], dict[str, Any]],
    graph: nx.DiGraph,
) -> int:
    all_nodes = set()
    for source, target in edge_totals:
        all_nodes.add(source)
        all_nodes.add(target)
    return max(0, len(all_nodes) - graph.number_of_nodes())


def _cluster_title(base: str, cluster: dict[str, Any] | None) -> str:
    if not cluster:
        return base
    cluster_id = str(cluster.get("cluster_id", "cluster"))
    return f"{base} - {cluster_id} ({_cluster_risk_label(cluster)})"


def _radial_money_flow_positions(
    graph: nx.DiGraph,
    suspicious: set[str],
    hubs: set[str],
) -> dict[str, tuple[float, float]]:
    ranked_nodes = sorted(graph.degree, key=lambda item: (-item[1], str(item[0])))
    core = [
        str(node)
        for node, degree in ranked_nodes
        if str(node) in suspicious or str(node) in hubs or degree >= 3
    ][:14]
    core_set = set(core)
    outer = sorted(str(node) for node in graph.nodes() if str(node) not in core_set)
    pos: dict[str, tuple[float, float]] = {}

    if len(core) == 1:
        pos[core[0]] = (0.0, 0.0)
    elif core:
        for idx, node in enumerate(core):
            angle = 2 * math.pi * idx / len(core)
            pos[node] = (0.55 * math.cos(angle), 0.55 * math.sin(angle))

    if outer:
        for idx, node in enumerate(outer):
            angle = 2 * math.pi * idx / len(outer)
            radius = 1.42 + 0.08 * (idx % 2)
            pos[node] = (radius * math.cos(angle), radius * math.sin(angle))

    missing = [node for node in graph.nodes() if node not in pos]
    if missing:
        fallback = nx.spring_layout(graph.subgraph(missing), seed=LAYOUT_SEED)
        pos.update({node: tuple(value) for node, value in fallback.items()})
    return pos


def _layered_flow_positions(graph: nx.DiGraph, source: str, account: str) -> dict[str, tuple[float, float]]:
    destinations = sorted(node for node in graph.nodes() if node not in {source, account})
    pos: dict[str, tuple[float, float]] = {source: (0.0, 0.0), account: (1.0, 0.0)}
    if not destinations:
        return nx.spring_layout(graph, seed=LAYOUT_SEED)
    if len(destinations) == 1:
        pos[destinations[0]] = (2.0, 0.0)
        return pos
    y_values = np.linspace(1.0, -1.0, len(destinations))
    for destination, y_value in zip(destinations, y_values):
        pos[destination] = (2.0, float(y_value))
    return pos


def _clustered_money_flow_positions(graph: nx.DiGraph) -> dict[str, tuple[float, float]]:
    clusters: dict[str, list[str]] = defaultdict(list)
    for node, data in graph.nodes(data=True):
        cluster_id = str(data.get("cluster_id") or "cluster_unknown")
        clusters[cluster_id].append(str(node))

    ordered_clusters = sorted(clusters.items(), key=lambda item: (-len(item[1]), item[0]))
    if not ordered_clusters:
        return {}

    pos: dict[str, tuple[float, float]] = {}
    cluster_count = len(ordered_clusters)
    for cluster_idx, (_, nodes) in enumerate(ordered_clusters):
        if cluster_count == 1:
            center_x, center_y = 0.0, 0.0
        else:
            angle = 2 * math.pi * cluster_idx / cluster_count
            ring_radius = 2.1 + 0.12 * cluster_count
            center_x = ring_radius * math.cos(angle)
            center_y = ring_radius * math.sin(angle)

        nodes = sorted(
            nodes,
            key=lambda node: (
                -_as_float(graph.nodes[node].get("total_score")),
                -graph.degree(node),
                node,
            ),
        )
        local_radius = 0.35 + min(1.4, 0.08 * len(nodes))
        for node_idx, node in enumerate(nodes):
            if len(nodes) == 1:
                pos[node] = (center_x, center_y)
                continue
            node_angle = 2 * math.pi * node_idx / len(nodes)
            radius = local_radius * (0.75 + 0.25 * (node_idx % 3))
            pos[node] = (
                center_x + radius * math.cos(node_angle),
                center_y + radius * math.sin(node_angle),
            )

    return pos


def _filter_interconnection_edges(
    edge_totals: dict[tuple[str, str], dict[str, Any]],
    observed_nodes: set[str],
) -> dict[tuple[str, str], dict[str, Any]]:
    kept: dict[tuple[str, str], dict[str, Any]] = {}
    external_best: dict[str, tuple[tuple[str, str], dict[str, Any]]] = {}

    for pair, data in edge_totals.items():
        source, target = pair
        source_observed = source in observed_nodes
        target_observed = target in observed_nodes
        if source_observed and target_observed:
            kept[pair] = data
            continue
        if not (source_observed or target_observed):
            continue
        observed = source if source_observed else target
        existing = external_best.get(observed)
        if existing is None or data["amount"] > existing[1]["amount"]:
            external_best[observed] = (pair, data)

    for pair, data in external_best.values():
        kept.setdefault(pair, data)
    return kept


def _interconnection_edge_limit(edge_totals: dict[tuple[str, str], dict[str, Any]]) -> int:
    cluster_counts = Counter(str(data.get("source_cluster") or "cluster_unknown") for data in edge_totals.values())
    if not cluster_counts:
        return 0
    dense_threshold = max(8, int(np.sqrt(max(cluster_counts.values())) * 3))
    return sum(min(count, dense_threshold) for count in cluster_counts.values())


def _cluster_edge_label_thresholds(graph: nx.DiGraph) -> dict[str, float]:
    amounts_by_cluster: dict[str, list[float]] = defaultdict(list)
    for _, _, data in graph.edges(data=True):
        cluster_id = str(data.get("source_cluster") or "cluster_unknown")
        amounts_by_cluster[cluster_id].append(_as_float(data.get("amount")))
    thresholds = {}
    for cluster_id, amounts in amounts_by_cluster.items():
        positive = [amount for amount in amounts if amount > 0]
        if not positive:
            thresholds[cluster_id] = 0.0
        else:
            thresholds[cluster_id] = float(np.quantile(positive, 0.70))
    return thresholds


def _add_legend(ax: plt.Axes, items: list[tuple[str, str]]) -> None:
    handles = [
        plt.Line2D(
            [0],
            [0],
            marker="o",
            color="white",
            label=label,
            markerfacecolor=color,
            markeredgecolor="#343a40",
            markersize=9,
        )
        for label, color in items
    ]
    ax.legend(handles=handles, loc="upper left", frameon=True, facecolor="white")


def _draw_offset_labels(
    ax: plt.Axes,
    pos: dict[Any, tuple[float, float]],
    nodes: Iterable[Any],
    limit: int,
    font_size: int,
) -> None:
    for node in nodes:
        x, y = pos[node]
        distance = math.hypot(float(x), float(y))
        if distance <= 0.001:
            dx, dy = 0.0, 0.07
        else:
            dx = 0.045 * float(x) / distance
            dy = 0.045 * float(y) / distance
        ax.text(
            float(x) + dx,
            float(y) + dy,
            _short_label(node, limit=limit),
            ha="center",
            va="center",
            fontsize=font_size,
            color="#111111",
            bbox={
                "boxstyle": "round,pad=0.18",
                "facecolor": "white",
                "edgecolor": "none",
                "alpha": 0.78,
            },
            zorder=5,
        )


def _title_label(value: str) -> str:
    return str(value).replace("_", " ").title()


def _short_label(value: Any, limit: int = 18) -> str:
    text = _clean_text(value) or "Unknown"
    if len(text) <= limit:
        return text
    if limit <= 8:
        return text[:limit]
    return f"{text[: max(4, limit // 2 - 1)]}...{text[-max(4, limit // 2 - 2):]}"


def _clean_text(value: Any) -> str:
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass
    text = str(value).strip()
    if text.lower() in {"", "nan", "none", "null", "<na>"}:
        return ""
    return text


def _format_amount(value: Any) -> str:
    amount = _as_float(value)
    sign = "-" if amount < 0 else ""
    amount = abs(amount)
    if amount >= 10_000_000:
        return f"{sign}INR {amount / 10_000_000:.2f}Cr"
    if amount >= 100_000:
        return f"{sign}INR {amount / 100_000:.2f}L"
    if amount >= 1_000:
        return f"{sign}INR {amount / 1_000:.1f}K"
    return f"{sign}INR {amount:.0f}"


def _as_float(value: Any) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return 0.0
    if math.isnan(number) or math.isinf(number):
        return 0.0
    return number


def _save_figure(fig: plt.Figure, path: Path) -> None:
    fig.tight_layout()
    fig.savefig(path, dpi=DPI, facecolor="white", bbox_inches="tight")
    plt.close(fig)
