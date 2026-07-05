"""Case relationship structure built from finalized graph and findings."""

from __future__ import annotations

import json
from collections import defaultdict
from typing import Any

import networkx as nx

from .llm_client import GroqKeyRotatingClient
from .models import Finding
from .scoring import finding_tier


def build_case_structure(
    graph: nx.MultiDiGraph,
    findings_by_pattern: dict[str, list[Finding]],
    suspicious_accounts: list[dict[str, Any]],
    llm_client: GroqKeyRotatingClient | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]], str, dict[str, Any]]:
    account_scores = {str(item.get("account_id")): item for item in suspicious_accounts}
    account_findings = _account_findings(findings_by_pattern)
    evidence_txn_ids = _evidence_txn_ids(findings_by_pattern)
    reconstruction_graph, edge_policy = _reconstruction_graph(graph, evidence_txn_ids)
    _add_scored_or_finding_accounts(reconstruction_graph, graph, account_scores, account_findings)
    edge_policy["reconstruction_graph"]["node_count"] = reconstruction_graph.number_of_nodes()
    components = _components(reconstruction_graph)
    node_cluster: dict[str, str] = {}
    clusters: list[dict[str, Any]] = []

    for idx, members in enumerate(components, start=1):
        cluster_id = f"cluster_{idx:03d}"
        cluster_nodes = sorted(str(member) for member in members)
        member_list = [
            member
            for member in cluster_nodes
            if _is_observed_case_account(reconstruction_graph, member, account_scores, account_findings)
        ]
        external_counterparties = [member for member in cluster_nodes if member not in set(member_list)]
        for member in cluster_nodes:
            node_cluster[member] = cluster_id
        edge_count = sum(
            1
            for source, target in reconstruction_graph.edges()
            if str(source) in members and str(target) in members
        )
        total_score = sum(float(account_scores.get(member, {}).get("total_score", 0) or 0) for member in member_list)
        pattern_ids = sorted({
            int(finding.pattern_id)
            for member in member_list
            for finding in account_findings.get(member, [])
        })
        evidence_groups = _cluster_evidence_groups(member_list, account_findings)
        subcases = _subcases(evidence_groups)
        bridge_accounts = _bridge_accounts(evidence_groups)
        clusters.append(
            {
                "cluster_id": cluster_id,
                "member_accounts": member_list,
                "cluster_nodes": cluster_nodes,
                "account_count": len(member_list),
                "node_count": len(cluster_nodes),
                "external_counterparty_count": len(external_counterparties),
                "sample_external_counterparties": external_counterparties[:25],
                "edge_count": edge_count,
                "is_isolated": edge_count == 0,
                "total_score": round(total_score, 4),
                "pattern_ids": pattern_ids,
                "evidence_group_count": len(evidence_groups),
                "evidence_groups": evidence_groups,
                "subcase_count": len(subcases),
                "subcases": subcases,
                "bridge_accounts": bridge_accounts,
                "highest_priority_account": max(
                    member_list,
                    key=lambda member: (float(account_scores.get(member, {}).get("total_score", 0) or 0), member),
                ) if member_list else "",
            }
        )

    case_structure = {
        "cluster_count": len(clusters),
        "clusters": clusters,
        "account_to_cluster": node_cluster,
        "cluster_method": "evidence_protected_strong_edge_components",
        "edge_policy": edge_policy["summary"],
        "raw_graph": edge_policy["raw_graph"],
        "reconstruction_graph": edge_policy["reconstruction_graph"],
    }
    network_graph_for_display = _network_graph_for_display(
        graph,
        node_cluster,
        account_scores,
        account_findings,
        edge_policy,
    )
    cluster_summaries = [
        _summarize_cluster(cluster, reconstruction_graph, account_findings, account_scores, llm_client)
        for cluster in clusters
    ]
    case_summary = _case_summary(clusters, suspicious_accounts)
    return case_structure, cluster_summaries, case_summary, network_graph_for_display


def _components(graph: nx.MultiDiGraph) -> list[set[str]]:
    if graph is None or graph.number_of_nodes() == 0:
        return []
    undirected = graph.to_undirected()
    components = [set(str(node) for node in component) for component in nx.connected_components(undirected)]
    return sorted(components, key=lambda members: (-len(members), sorted(members)))


def _account_findings(findings_by_pattern: dict[str, list[Finding]]) -> dict[str, list[Finding]]:
    mapping: dict[str, list[Finding]] = defaultdict(list)
    for findings in findings_by_pattern.values():
        for finding in findings:
            if finding.pattern_id in {6, 21, 22, 23}:
                continue
            for account in finding.accounts:
                mapping[str(account)].append(finding)
    return mapping


def _evidence_txn_ids(findings_by_pattern: dict[str, list[Finding]]) -> set[str]:
    txn_ids: set[str] = set()
    for findings in findings_by_pattern.values():
        for finding in findings:
            if finding.pattern_id in {6, 21, 22, 23}:
                continue
            txn_ids.update(str(value) for value in finding.txn_ids if str(value))
            txn_ids.update(_txn_ids_from_details(finding.details))
    return txn_ids


def _txn_ids_from_details(value: Any) -> set[str]:
    txn_ids: set[str] = set()
    if isinstance(value, dict):
        for key, nested in value.items():
            normalized_key = str(key).lower()
            if normalized_key.endswith("txn_id") and str(nested):
                txn_ids.add(str(nested))
            elif normalized_key.endswith("txn_ids") and isinstance(nested, (list, tuple, set)):
                txn_ids.update(str(item) for item in nested if str(item))
            else:
                txn_ids.update(_txn_ids_from_details(nested))
    elif isinstance(value, list):
        for item in value:
            txn_ids.update(_txn_ids_from_details(item))
    return txn_ids


def _reconstruction_graph(
    graph: nx.MultiDiGraph,
    evidence_txn_ids: set[str],
) -> tuple[nx.MultiDiGraph, dict[str, Any]]:
    reconstruction = nx.MultiDiGraph()
    if graph is None:
        return reconstruction, _empty_edge_policy()

    node_degrees = _node_observed_degrees(graph)
    degree_values = [degree for degree in node_degrees.values() if degree > 0]
    low_degree_threshold = _percentile(degree_values, 50)
    high_degree_threshold = _percentile(degree_values, 95)
    edge_decisions: dict[str, dict[str, Any]] = {}
    reason_counts: dict[str, int] = defaultdict(int)
    included_edges = 0

    for source, target, key, data in graph.edges(keys=True, data=True):
        edge_id = _edge_id(source, target, key)
        decision = _edge_decision(
            graph,
            source,
            target,
            data,
            evidence_txn_ids,
            node_degrees,
            low_degree_threshold,
            high_degree_threshold,
        )
        edge_decisions[edge_id] = decision
        reason_counts[str(decision["reason"])] += 1
        if decision["included_in_case_reconstruction"]:
            if source not in reconstruction:
                reconstruction.add_node(source, **dict(graph.nodes[source]))
            if target not in reconstruction:
                reconstruction.add_node(target, **dict(graph.nodes[target]))
            reconstruction.add_edge(source, target, key=key, **data)
            included_edges += 1

    return reconstruction, {
        "summary": {
            "description": (
                "Clusters are built from an evidence-protected reconstruction graph. "
                "Raw graph edges remain available for audit, but weak public-infrastructure "
                "or boundary edges do not merge accounts into one case cluster."
            ),
            "rules": [
                "Always keep edges that support a fired detector finding.",
                "Keep observed-account edges with confidence_score >= 0.85.",
                "Keep ledger-pair corroborated observed-account edges.",
                "Keep low-degree non-account endpoints so mule UPI/cash-out destinations are not dropped.",
                "Do not let high-degree public endpoints merge case clusters unless a fired detector already uses that edge.",
            ],
            "low_degree_percentile": 50,
            "low_degree_threshold": low_degree_threshold,
            "high_degree_percentile": 95,
            "high_degree_threshold": high_degree_threshold,
            "reason_counts": dict(sorted(reason_counts.items())),
        },
        "raw_graph": {
            "node_count": graph.number_of_nodes(),
            "edge_count": graph.number_of_edges(),
        },
        "reconstruction_graph": {
            "node_count": reconstruction.number_of_nodes(),
            "edge_count": included_edges,
            "filtered_edge_count": max(0, graph.number_of_edges() - included_edges),
        },
        "node_degrees": node_degrees,
        "edge_decisions": edge_decisions,
    }


def _add_scored_or_finding_accounts(
    reconstruction_graph: nx.MultiDiGraph,
    raw_graph: nx.MultiDiGraph,
    account_scores: dict[str, dict[str, Any]],
    account_findings: dict[str, list[Finding]],
) -> None:
    for account in sorted(set(account_scores).union(account_findings)):
        if not account or account in reconstruction_graph:
            continue
        if raw_graph is not None and account in raw_graph:
            reconstruction_graph.add_node(account, **dict(raw_graph.nodes[account]))
        else:
            reconstruction_graph.add_node(account, observed_account=True)


def _is_observed_case_account(
    graph: nx.MultiDiGraph,
    node: str,
    account_scores: dict[str, dict[str, Any]],
    account_findings: dict[str, list[Finding]],
) -> bool:
    data = graph.nodes[node] if graph is not None and node in graph else {}
    return bool(data.get("observed_account") or node in account_scores or node in account_findings)


def _empty_edge_policy() -> dict[str, Any]:
    return {
        "summary": {
            "description": "No money-flow graph was available for case reconstruction.",
            "rules": [],
            "low_degree_percentile": 50,
            "low_degree_threshold": 0,
            "high_degree_percentile": 95,
            "high_degree_threshold": 0,
            "reason_counts": {},
        },
        "raw_graph": {"node_count": 0, "edge_count": 0},
        "reconstruction_graph": {"node_count": 0, "edge_count": 0, "filtered_edge_count": 0},
        "node_degrees": {},
        "edge_decisions": {},
    }


def _edge_decision(
    graph: nx.MultiDiGraph,
    source: Any,
    target: Any,
    data: dict[str, Any],
    evidence_txn_ids: set[str],
    node_degrees: dict[str, int],
    low_degree_threshold: float,
    high_degree_threshold: float,
) -> dict[str, Any]:
    source_id = str(source)
    target_id = str(target)
    source_data = graph.nodes[source] if source in graph else {}
    target_data = graph.nodes[target] if target in graph else {}
    source_observed = bool(source_data.get("observed_account"))
    target_observed = bool(target_data.get("observed_account"))
    confidence = _edge_confidence(data)
    edge_txn_ids = _edge_txn_ids(data)
    pattern_supported = bool(edge_txn_ids.intersection(evidence_txn_ids))
    method = str(data.get("counterparty_resolution_method", "") or "")
    corroborated = bool(
        str(data.get("ledger_pair_id", "") or "")
        or method in {"exact_reference_or_upi_match", "ledger_pair_match", "mirrored_ledger_pair"}
    )
    strong_confidence = confidence >= 0.85
    source_degree = node_degrees.get(source_id, 0)
    target_degree = node_degrees.get(target_id, 0)
    source_public = (not source_observed) and source_degree > high_degree_threshold
    target_public = (not target_observed) and target_degree > high_degree_threshold
    low_degree_endpoint = min(source_degree or 0, target_degree or 0) <= low_degree_threshold
    observed_pair = source_observed and target_observed
    ledger_corroborated = bool(
        str(data.get("ledger_pair_id", "") or "")
        or method in {"ledger_pair_match", "mirrored_ledger_pair"}
    )

    if pattern_supported:
        included = True
        reason = "pattern_supported"
    elif source_public or target_public:
        included = False
        reason = "filtered_high_degree_public_endpoint"
    elif observed_pair and (strong_confidence or ledger_corroborated):
        included = True
        reason = "strong_observed_account_edge" if strong_confidence else "ledger_corroborated_observed_edge"
    elif corroborated:
        included = True
        reason = "reference_or_ledger_corroborated"
    elif observed_pair:
        included = False
        reason = "filtered_weak_observed_observed"
    elif low_degree_endpoint:
        included = True
        reason = "low_degree_endpoint"
    else:
        included = False
        reason = "filtered_boundary_medium_confidence"

    return {
        "included_in_case_reconstruction": included,
        "reason": reason,
        "confidence_score": confidence,
        "pattern_supported": pattern_supported,
        "reference_or_ledger_corroborated": corroborated,
        "source_degree": source_degree,
        "target_degree": target_degree,
        "source_observed_account": source_observed,
        "target_observed_account": target_observed,
        "high_degree_public_endpoint": bool(source_public or target_public),
    }


def _node_observed_degrees(graph: nx.MultiDiGraph) -> dict[str, int]:
    observed_nodes = {
        str(node)
        for node, data in graph.nodes(data=True)
        if data.get("observed_account")
    }
    neighbor_map: dict[str, set[str]] = defaultdict(set)
    raw_neighbor_map: dict[str, set[str]] = defaultdict(set)
    for source, target in graph.edges():
        source_id = str(source)
        target_id = str(target)
        raw_neighbor_map[source_id].add(target_id)
        raw_neighbor_map[target_id].add(source_id)
        if target_id in observed_nodes:
            neighbor_map[source_id].add(target_id)
        if source_id in observed_nodes:
            neighbor_map[target_id].add(source_id)
    degrees = {}
    for node in graph.nodes():
        node_id = str(node)
        observed_degree = len(neighbor_map.get(node_id, set()))
        degrees[node_id] = observed_degree if observed_degree > 0 else len(raw_neighbor_map.get(node_id, set()))
    return degrees


def _percentile(values: list[int], percentile: int) -> float:
    if not values:
        return 0.0
    ordered = sorted(float(value) for value in values)
    if len(ordered) == 1:
        return ordered[0]
    rank = (len(ordered) - 1) * (percentile / 100)
    lower = int(rank)
    upper = min(lower + 1, len(ordered) - 1)
    weight = rank - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def _edge_confidence(data: dict[str, Any]) -> float:
    for key in ("confidence_score", "counterparty_resolution_confidence"):
        try:
            value = data.get(key)
            if value is not None and float(value) > 0:
                return max(0.0, min(1.0, float(value)))
        except (TypeError, ValueError):
            continue
    return 1.0


def _edge_txn_ids(data: dict[str, Any]) -> set[str]:
    txn_ids = {str(value) for value in data.get("txn_ids", []) if str(value)}
    txn_id = str(data.get("txn_id", "") or "")
    if txn_id:
        txn_ids.add(txn_id)
    return txn_ids


def _edge_id(source: Any, target: Any, key: Any) -> str:
    return f"{source}->{target}::{key}"


def _cluster_evidence_groups(
    members: list[str],
    account_findings: dict[str, list[Finding]],
) -> list[dict[str, Any]]:
    member_set = set(members)
    grouped: dict[tuple[int, tuple[str, ...]], dict[str, Any]] = {}
    for member in members:
        for finding in account_findings.get(member, []):
            accounts = tuple(sorted(set(finding.accounts).intersection(member_set)))
            if not accounts:
                continue
            key = (int(finding.pattern_id), accounts)
            bucket = grouped.setdefault(
                key,
                {
                    "pattern_id": int(finding.pattern_id),
                    "pattern_name": finding.pattern_name,
                    "accounts": list(accounts),
                    "finding_count": 0,
                    "txn_ids": set(),
                    "finding_ids": [],
                    "seen_finding_ids": set(),
                    "confidence_tiers": set(),
                },
            )
            if finding.finding_id in bucket["seen_finding_ids"]:
                continue
            bucket["seen_finding_ids"].add(finding.finding_id)
            bucket["finding_count"] += 1
            bucket["txn_ids"].update(finding.txn_ids)
            bucket["finding_ids"].append(finding.finding_id)
            bucket["confidence_tiers"].add(finding_tier(finding))

    rows = []
    for bucket in grouped.values():
        rows.append(
            {
                "pattern_id": bucket["pattern_id"],
                "pattern_name": bucket["pattern_name"],
                "accounts": bucket["accounts"],
                "finding_count": bucket["finding_count"],
                "txn_id_count": len(bucket["txn_ids"]),
                "representative_finding_ids": bucket["finding_ids"][:5],
                "confidence_tiers": sorted(bucket["confidence_tiers"]),
            }
        )
    return sorted(rows, key=lambda item: (-int(item["finding_count"]), int(item["pattern_id"]), item["accounts"]))


def _subcases(evidence_groups: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for idx, group in enumerate(evidence_groups, start=1):
        rows.append(
            {
                "subcase_id": f"subcase_{idx:03d}",
                "pattern_id": group["pattern_id"],
                "pattern_name": group["pattern_name"],
                "accounts": group["accounts"],
                "finding_count": group["finding_count"],
                "txn_id_count": group["txn_id_count"],
            }
        )
    return rows


def _bridge_accounts(evidence_groups: list[dict[str, Any]]) -> list[dict[str, Any]]:
    account_groups: dict[str, list[str]] = defaultdict(list)
    account_patterns: dict[str, set[int]] = defaultdict(set)
    for idx, group in enumerate(evidence_groups, start=1):
        subcase_id = f"subcase_{idx:03d}"
        for account in group.get("accounts", []):
            account_groups[str(account)].append(subcase_id)
            account_patterns[str(account)].add(int(group.get("pattern_id", 0) or 0))
    rows = [
        {
            "account_id": account,
            "subcase_ids": subcases,
            "distinct_pattern_ids": sorted(account_patterns[account]),
            "subcase_count": len(subcases),
        }
        for account, subcases in account_groups.items()
        if len(subcases) > 1
    ]
    return sorted(rows, key=lambda item: (-int(item["subcase_count"]), item["account_id"]))


def _network_graph_for_display(
    graph: nx.MultiDiGraph,
    node_cluster: dict[str, str],
    account_scores: dict[str, dict[str, Any]],
    account_findings: dict[str, list[Finding]],
    edge_policy: dict[str, Any],
) -> dict[str, Any]:
    node_degrees = edge_policy.get("node_degrees", {})
    nodes = []
    for node, data in graph.nodes(data=True):
        account = str(node)
        score = account_scores.get(account, {})
        tiers = sorted({finding_tier(finding) for finding in account_findings.get(account, [])})
        nodes.append(
            {
                "id": account,
                "cluster_id": node_cluster.get(account, ""),
                "observed_account": bool(data.get("observed_account")),
                "total_score": float(score.get("total_score", 0) or 0),
                "suspicion_tiers": tiers,
                "pattern_count": len(account_findings.get(account, [])),
                "reconstruction_degree": int(node_degrees.get(account, 0) or 0),
            }
        )
    edges = []
    for source, target, key, data in graph.edges(keys=True, data=True):
        decision = edge_policy.get("edge_decisions", {}).get(_edge_id(source, target, key), {})
        edges.append(
            {
                "id": f"{source}->{target}::{key}",
                "source": str(source),
                "target": str(target),
                "amount": float(data.get("amount", 0) or 0),
                "date": str(data.get("date", "") or ""),
                "txn_ids": [str(value) for value in data.get("txn_ids", []) if str(value)],
                "confidence_score": float(data.get("confidence_score", 1.0) or 1.0),
                "included_in_case_reconstruction": bool(decision.get("included_in_case_reconstruction", False)),
                "reconstruction_reason": str(decision.get("reason", "")),
                "pattern_supported": bool(decision.get("pattern_supported", False)),
                "high_degree_public_endpoint": bool(decision.get("high_degree_public_endpoint", False)),
            }
        )
    return {"nodes": nodes, "edges": edges}


def _summarize_cluster(
    cluster: dict[str, Any],
    graph: nx.MultiDiGraph,
    account_findings: dict[str, list[Finding]],
    account_scores: dict[str, dict[str, Any]],
    llm_client: GroqKeyRotatingClient | None,
) -> dict[str, Any]:
    members = [str(value) for value in cluster.get("member_accounts", [])]
    pattern_names = sorted({
        finding.pattern_name
        for member in members
        for finding in account_findings.get(member, [])
    })
    template = _template_cluster_summary(cluster, pattern_names)
    summary = template
    source = "template"
    errors: list[str] = []
    if len(members) > 1 and llm_client is not None and llm_client.available and llm_client.has_active_key():
        payload = _cluster_llm_payload(cluster, members, graph, account_findings, account_scores)
        result = llm_client.chat_json(
            [
                {
                    "role": "system",
                    "content": (
                        "Given connected bank accounts, relationships, and finalized pattern evidence, "
                        "write a 4-6 sentence plain-English case summary. State only what the data shows. "
                        "Do not speculate about intent or guilt. Return JSON with key summary."
                    ),
                },
                {"role": "user", "content": json.dumps(payload, default=str, sort_keys=True)},
            ],
            call_context="cluster_summary",
        )
        if result.ok:
            try:
                candidate = str(json.loads(result.content).get("summary", "")).strip()
            except json.JSONDecodeError:
                candidate = ""
                errors.append("template_fallback:invalid_json_response")
            if candidate:
                summary = candidate
                source = "groq"
            else:
                errors.append("template_fallback:empty_summary_response")
        else:
            errors.append(f"template_fallback:{result.error}")
    row = {
        "cluster_id": cluster.get("cluster_id"),
        "summary": summary,
        "explanation_source": source,
    }
    if errors:
        row["llm_errors"] = errors
    return row


def _cluster_llm_payload(
    cluster: dict[str, Any],
    members: list[str],
    graph: nx.MultiDiGraph,
    account_findings: dict[str, list[Finding]],
    account_scores: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    member_set = set(members)
    ranked_members = sorted(
        members,
        key=lambda member: (
            -float(account_scores.get(member, {}).get("total_score", 0) or 0),
            -len(account_findings.get(member, [])),
            member,
        ),
    )
    top_members = ranked_members[:12]
    edge_rows = [
        {
            "source": str(source_node),
            "target": str(target_node),
            "amount": float(data.get("amount", 0) or 0),
            "date": str(data.get("date", "") or ""),
        }
        for source_node, target_node, data in graph.edges(data=True)
        if str(source_node) in member_set and str(target_node) in member_set
    ]
    edge_rows = sorted(edge_rows, key=lambda item: (-float(item.get("amount", 0) or 0), item["source"], item["target"]))[:30]
    return {
        "cluster": {
            "cluster_id": cluster.get("cluster_id"),
            "account_count": cluster.get("account_count"),
            "edge_count": cluster.get("edge_count"),
            "total_score": cluster.get("total_score"),
            "pattern_ids": cluster.get("pattern_ids", []),
            "evidence_group_count": cluster.get("evidence_group_count"),
            "subcase_count": cluster.get("subcase_count"),
            "highest_priority_account": cluster.get("highest_priority_account"),
            "omitted_member_count": max(0, len(members) - len(top_members)),
        },
        "top_accounts": [
            {
                "account_id": member,
                "score": {
                    "total_score": account_scores.get(member, {}).get("total_score", 0),
                    "distinct_pattern_count": account_scores.get(member, {}).get("distinct_pattern_count", 0),
                    "strong_pattern_count": account_scores.get(member, {}).get("strong_pattern_count", 0),
                    "total_findings": account_scores.get(member, {}).get("total_findings", 0),
                },
                "patterns": [
                    {
                        "pattern_id": finding.pattern_id,
                        "pattern_name": finding.pattern_name,
                        "tier": finding_tier(finding),
                        "txn_ids": finding.txn_ids[:8],
                    }
                    for finding in account_findings.get(member, [])[:8]
                ],
            }
            for member in top_members
        ],
        "evidence_groups": (cluster.get("evidence_groups", []) or [])[:12],
        "bridge_accounts": (cluster.get("bridge_accounts", []) or [])[:8],
        "top_edges": edge_rows,
    }


def _template_cluster_summary(cluster: dict[str, Any], pattern_names: list[str]) -> str:
    members = cluster.get("member_accounts", [])
    if cluster.get("is_isolated"):
        account = members[0] if members else "unknown"
        patterns = ", ".join(pattern_names) if pattern_names else "no scored pattern"
        return f"Account {account} was evaluated as an isolated account with no established transactional link to other accounts in this case. It was associated with {patterns}."
    patterns = ", ".join(pattern_names[:8]) if pattern_names else "no scored pattern"
    return (
        f"{cluster.get('cluster_id')} contains {cluster.get('account_count')} connected account(s) "
        f"and {cluster.get('edge_count')} transaction edge(s). The cluster evidence includes {patterns}."
    )


def _case_summary(clusters: list[dict[str, Any]], suspicious_accounts: list[dict[str, Any]]) -> str:
    if not clusters:
        return "No transactional account clusters were available in this run."
    top = max(clusters, key=lambda item: (float(item.get("total_score", 0) or 0), str(item.get("cluster_id", ""))))
    return (
        f"The case contains {len(clusters)} account cluster(s), with {len(suspicious_accounts)} account(s) ranked for suspicious activity. "
        f"The highest-priority cluster is {top.get('cluster_id')} with total score {float(top.get('total_score', 0) or 0):.2f}."
    )
