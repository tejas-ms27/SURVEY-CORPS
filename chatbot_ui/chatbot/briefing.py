"""
briefing.py
─────────────────────────────────────────────────────────────────────────────
CIDECODE 2026 — Multi-Accused Cross-Account Investigation Engine
Module: Investigator Briefing (case-level narrative summary)

Same discipline as aggregations.py (see that module's docstring): the LLM
never computes or invents a number. assemble_case_facts() is pure Python and
does all the counting; generate_case_briefing() makes exactly ONE LLM call
whose only job is to phrase the given facts into a paragraph, under a system
prompt that forbids adding any number not present in the input.
"""

from __future__ import annotations

from chatbot.investigation_rules import run_all_rules
from chatbot.structuring import structuring_results_by_account


def assemble_case_facts(case: dict, structuring_by_account: dict | None = None) -> dict:
    """Pure-Python facts assembly — no LLM involved."""
    findings = run_all_rules(case)
    risk_counts = {"High": 0, "Medium": 0, "Low": 0}
    rule_counts: dict[str, int] = {}
    for f in findings:
        risk_counts[f.risk] = risk_counts.get(f.risk, 0) + 1
        rule_counts[f.rule] = rule_counts.get(f.rule, 0) + 1
    top_rules = sorted(rule_counts.items(), key=lambda kv: -kv[1])[:3]

    if structuring_by_account is None:
        structuring_by_account = structuring_results_by_account(case)
    clusters = [c for cl in structuring_by_account.values() for c in cl]

    clean = case["clean"]
    dates = clean["Date"].dropna() if "Date" in clean.columns else None
    date_range = (
        f"{dates.min().strftime('%d/%m/%Y')} to {dates.max().strftime('%d/%m/%Y')}"
        if dates is not None and not dates.empty else "unknown"
    )

    return {
        "case_account_count": len(case["accounts"]),
        "total_clean_transactions": len(clean),
        "total_flagged_transactions": len(case["flagged"]),
        "total_findings": len(findings),
        "high_risk_findings": risk_counts.get("High", 0),
        "medium_risk_findings": risk_counts.get("Medium", 0),
        "low_risk_findings": risk_counts.get("Low", 0),
        "top_finding_types": ", ".join(f"{name} ({count})" for name, count in top_rules) or "none",
        "structuring_alert_count": len(clusters),
        "structuring_alert_total_amount": f"₹{sum(c['total_amount'] for c in clusters):,.2f}",
        "case_date_range": date_range,
    }


_BRIEFING_SYSTEM_PROMPT = """You are drafting a one-paragraph investigator briefing \
for a forensic financial-crime case. You are given a fixed set of facts as key:value \
lines. Write a concise, professional paragraph (4-6 sentences) for an investigator.

HARD RULES:
- Use ONLY the numbers given below. Do NOT invent, estimate, or add any number, \
account name, or date not present in the facts.
- Do NOT make legal conclusions or claims of guilt — describe patterns/counts only, \
using cautious language ("may warrant review", "flagged for").
- No title/heading — just the paragraph."""


def generate_case_briefing(case: dict, structuring_by_account: dict | None = None) -> str:
    """Computes every number in pure Python; makes exactly ONE generate() call
    to phrase prose from a fixed facts dict the LLM cannot add numbers to."""
    from chatbot.rag_chat import generate

    facts = assemble_case_facts(case, structuring_by_account)
    facts_text = "\n".join(f"{k}: {v}" for k, v in facts.items())
    return generate([
        {"role": "system", "content": _BRIEFING_SYSTEM_PROMPT},
        {"role": "user", "content": facts_text},
    ], temperature=0.2)
