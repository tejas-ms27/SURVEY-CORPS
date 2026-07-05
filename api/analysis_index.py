"""
analysis_index.py — turn the REAL fraud-engine results into chatbot knowledge chunks.

The chatbot indexes the extraction data (transactions, flags, duplicates, account context)
plus its own light structuring rules. This adds chunks derived from the deep analysis engine
(analysis_results.json) and the court-ready report content — Case Narrative, suspicion scores,
prime suspects, per-account pattern findings — so the investigator can ask the chatbot about
the ANALYSIS and the REPORT, not just the raw statements.

It reuses reporting.report_data.build_report_context (same data the PDF shows) and emits chunks
in the exact {id, text, metadata} shape the chatbot's vector store already ingests, using the
existing chunk_type="fraud_pattern" so the current citation formatter renders them nicely.

No backend/detector logic is touched — this only READS analysis output and formats it.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


def _build_context(case_id: str) -> dict[str, Any] | None:
    analysis_dir = ROOT / "analysis" / "outputs" / case_id
    if not (analysis_dir / "analysis_results.json").exists():
        return None
    reporting_dir = str(ROOT / "reporting")
    if reporting_dir not in sys.path:
        sys.path.insert(0, reporting_dir)
    try:
        from report_data import build_report_context  # type: ignore

        return build_report_context(run_id=case_id, repo_root=ROOT)
    except Exception:
        return None


def analysis_chunks(case_id: str) -> list[dict[str, Any]]:
    """Return chatbot chunks describing the deep-analysis findings, or [] if not run yet."""
    ctx = _build_context(case_id)
    if not ctx:
        return []

    chunks: list[dict[str, Any]] = []

    def add(cid: str, text: str, account_id: str = "", pattern_type: str = "") -> None:
        chunks.append({
            "id": cid,
            "text": text,
            "metadata": {
                "chunk_type": "fraud_pattern",
                "source": "deep_analysis",
                "account_id": str(account_id or ""),
                "pattern_type": str(pattern_type or "fraud_analysis"),
                "severity": "high",
            },
        })

    # 1) Plain-language case narrative (the same story the report opens with).
    narrative = ctx.get("case_narrative", {}) or {}
    lines = narrative.get("lines", []) or []
    if lines:
        add(
            f"analysis-narrative-{case_id}",
            "CASE SUMMARY (deep fraud analysis). " + " ".join(str(l) for l in lines)
            + f" Total money moved: {narrative.get('total_moved_display', '')}."
            + f" Money into the suspect network: {narrative.get('money_into_network_display', '')}."
            + f" Account to investigate first: {narrative.get('first_target', '')}.",
        )

    # 2) Analysis summary (counts an investigator asks for).
    summ = ctx.get("analysis_summary", {}) or {}
    add(
        f"analysis-summary-{case_id}",
        "FRAUD ANALYSIS OVERVIEW. "
        f"{summ.get('accounts_flagged', 0)} account(s) were flagged as suspicious out of "
        f"{summ.get('accounts_analyzed', 0)} analysed. "
        f"{ctx.get('ranked_total', 0)} accounts are ranked by suspicion score. "
        f"Counterparty resolution rate: {summ.get('counterparty_resolution_rate', 0)}%. "
        f"Money-flow graph: {summ.get('graph_nodes', 0)} nodes and {summ.get('graph_edges', 0)} edges.",
    )

    # 3) One chunk per prime suspect (top of the priority list).
    for s in ctx.get("prime_suspects", []) or []:
        add(
            f"analysis-prime-{case_id}-{s.get('rank')}",
            f"PRIME SUSPECT rank {s.get('rank')} (investigate first): {s.get('holder', '')} "
            f"account {s.get('account_number', '')}. Suspicion score {s.get('score', 0)} ({s.get('band', '')}). "
            f"Key concern: {s.get('key_concern', '')}. {s.get('top_finding', '')}",
            account_id=s.get("account_number", ""),
            pattern_type=str(s.get("key_concern", "")),
        )

    # 4) One chunk per ranked suspect with its detected patterns + findings.
    for acc in ctx.get("ranked_accounts", []) or []:
        bullets = acc.get("bullets", []) or []
        pattern_names = ", ".join(b.get("pattern", "") for b in bullets[:6])
        finding_text = " ".join(f"[{b.get('pattern', '')}] {b.get('text', '')}" for b in bullets[:6])
        add(
            f"analysis-suspect-{case_id}-{acc.get('account_id')}",
            f"SUSPECT (fraud analysis): {acc.get('holder', '')} account {acc.get('account_number', '')} "
            f"at {acc.get('bank', '')}. Suspicion score {acc.get('score', 0)} "
            f"({acc.get('band', '')} risk), flagged by {acc.get('distinct_pattern_count', 0)} distinct "
            f"pattern(s) ({acc.get('strong_pattern_count', 0)} strong): {pattern_names}. "
            f"Findings: {finding_text}",
            account_id=acc.get("account_number", "") or acc.get("account_id", ""),
            pattern_type=str(acc.get("key_concern", "")),
        )

    # 5) Case reconstruction / clusters (who is connected to whom).
    recon = ctx.get("case_reconstruction", {}) or {}
    if recon.get("summary"):
        add(
            f"analysis-reconstruction-{case_id}",
            "CASE RECONSTRUCTION. " + str(recon.get("summary", ""))
            + f" The case has {recon.get('cluster_count', 0)} account cluster(s).",
        )

    return chunks
