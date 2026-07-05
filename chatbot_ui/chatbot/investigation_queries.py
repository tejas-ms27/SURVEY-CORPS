"""
investigation_queries.py
─────────────────────────────────────────────────────────────────────────────
CIDECODE 2026 — Multi-Accused Cross-Account Investigation Engine
Module: Investigation Intelligence Router + Analytical Handlers
        (Phase 3, Goals 1, 8, 10)

This is the single entry point the routing pipeline calls for the new
"Investigation Intelligence" layer (spec: sits AFTER structured queries,
BEFORE graph + RAG). It:

  1. dispatches to the deterministic sub-engines — reasoning_engine,
     investigation_rules, frequency_analysis — in a fixed, most-specific-first
     order, and
  2. hosts the investigator ANALYTICAL handlers that don't belong to any of
     those sub-engines: "which account receives the most deposits", "which
     accounts mostly send rather than receive", "which accounts only transact
     with one beneficiary", cross-account counterparty overlap, etc.

Every answer returned from here carries a confidence/explainability footer
(Goal 10): Analysis Type, Handler, Evidence, Confidence. Because every handler
computes from real rows with zero LLM involvement, deterministic answers are
reported at 100% confidence by construction.
"""

from __future__ import annotations

import re

import pandas as pd

from chatbot.frequency_analysis import add_counterparty, prepared_transactions, try_frequency_answer
from chatbot.investigation_rules import CASH_NARRATION_RE, try_rules_answer
from chatbot.reasoning_engine import try_reasoning_answer
from chatbot.structured_queries import _resolve_account

# Human-readable analysis-type labels keyed by matched_pattern prefix, used for
# the Goal 10 explainability footer.
_ANALYSIS_LABELS = {
    "frequency": "Transaction Frequency Analysis",
    "investigation_rules": "Investigation Rule Engine",
    "reasoning": "Multi-Hop / Chain-of-Evidence Reasoning",
    "investigation_query": "Investigator Query Engine",
    "cross_account": "Cross-Account Investigation",
}


def _rupees(v: float) -> str:
    return f"₹{v:,.2f}"


def _holder(case: dict, account_id: str, df: pd.DataFrame | None = None) -> str:
    holder = case.get("accounts", {}).get(str(account_id), {}).get("account_details", {}).get("account_holder")
    if holder:
        return str(holder)
    if df is not None and "account_holder" in df.columns and not df.empty:
        names = df["account_holder"].dropna()
        if not names.empty:
            return str(names.iloc[0])
    return "(unidentified)"


def _account_citation(case: dict, account_id: str) -> dict:
    bank = case.get("accounts", {}).get(str(account_id), {}).get("account_details", {}).get("bank_name") or ""
    return {"type": "account_context", "account": str(account_id), "bank_name": bank}


# ─────────────────────────────────────────────────────────────────────────────
# PER-ACCOUNT FLOW SUMMARY — backbone of the analytical handlers below
# ─────────────────────────────────────────────────────────────────────────────

def account_flow_summary(case: dict) -> pd.DataFrame:
    """
    One row per account: credit/debit counts and sums, distinct inferred
    beneficiaries, and cash-withdrawal count. Computed once, reused by every
    analytical handler in this module.
    """
    df = case["clean"]
    if "account_number" not in df.columns or df.empty:
        return pd.DataFrame()

    rows = []
    for account_id in df["account_number"].astype(str).unique():
        adf = add_counterparty(prepared_transactions(case, account_id))
        credits = adf[adf["_direction"] == "credit"]
        debits = adf[adf["_direction"] == "debit"]
        cash_debits = debits[debits["Narration"].astype(str).str.contains(CASH_NARRATION_RE, na=False)]
        beneficiaries = adf.loc[adf["_direction"] == "debit", "_counterparty"].dropna().unique()
        rows.append({
            "account": account_id,
            "holder": _holder(case, account_id, adf),
            "n": int(len(adf)),
            "credit_count": int(len(credits)),
            "debit_count": int(len(debits)),
            "credit_sum": float(credits["_amount"].sum()),
            "debit_sum": float(debits["_amount"].sum()),
            "distinct_beneficiaries": int(len(beneficiaries)),
            "cash_debit_count": int(len(cash_debits)),
        })
    return pd.DataFrame(rows)


# ─────────────────────────────────────────────────────────────────────────────
# ANALYTICAL HANDLERS (Goal 1) — deterministic investigator questions
# ─────────────────────────────────────────────────────────────────────────────

def _handle_most_deposits(question: str, case: dict) -> dict | None:
    q = question.lower()
    if not (("most" in q or "highest" in q) and any(w in q for w in ["deposit", "credit", "receive", "incoming"])):
        return None
    table = account_flow_summary(case)
    if table.empty:
        return None
    ranked = table.sort_values("credit_count", ascending=False).head(5)
    leader = ranked.iloc[0]
    lines = [
        f"  {i}. {r['holder']} (account {r['account']}): {r['credit_count']} deposit(s) "
        f"totalling {_rupees(r['credit_sum'])}"
        for i, (_, r) in enumerate(ranked.iterrows(), start=1)
    ]
    answer = (
        f"{leader['holder']} (account {leader['account']}) receives the most deposits — "
        f"{leader['credit_count']} credit transaction(s) totalling {_rupees(leader['credit_sum'])}.\n"
        + "\n".join(lines)
    )
    citations = [_account_citation(case, r["account"]) for _, r in ranked.iterrows()]
    return {"answer": answer, "citations": citations, "matched_pattern": "investigation_query_most_deposits"}


def _handle_send_vs_receive(question: str, case: dict) -> dict | None:
    q = question.lower()
    mostly_send = (
        (("send" in q or "sends" in q or "outgoing" in q or "spend" in q) and "rather than" in q)
        or ("mostly send" in q or "mostly sends" in q or "send money" in q)
    )
    mostly_receive = "mostly receive" in q or "receive but" in q or "rarely spend" in q or "rarely send" in q
    if not (mostly_send or mostly_receive):
        return None
    table = account_flow_summary(case)
    if table.empty:
        return None

    table = table.copy()
    # net flow ratio: >0 means net receiver, <0 means net sender
    table["net"] = table["credit_sum"] - table["debit_sum"]
    if mostly_receive:
        subset = table[table["credit_sum"] > table["debit_sum"] * 1.5].sort_values("net", ascending=False)
        verb = "receive far more than they spend"
    else:
        subset = table[table["debit_sum"] > table["credit_sum"] * 1.5].sort_values("net")
        verb = "send out far more than they receive"

    if subset.empty:
        return {"answer": f"No account clearly {verb} in this case.",
                "citations": [], "matched_pattern": "investigation_query_send_receive"}
    lines = [
        f"  - {r['holder']} (account {r['account']}): in {_rupees(r['credit_sum'])} / "
        f"out {_rupees(r['debit_sum'])}"
        for _, r in subset.head(5).iterrows()
    ]
    answer = f"Account(s) that {verb}:\n" + "\n".join(lines)
    citations = [_account_citation(case, r["account"]) for _, r in subset.head(5).iterrows()]
    return {"answer": answer, "citations": citations, "matched_pattern": "investigation_query_send_receive"}


def _handle_single_beneficiary(question: str, case: dict) -> dict | None:
    q = question.lower()
    if not (("one beneficiary" in q or "single beneficiary" in q or "only transact" in q
             or "one counterparty" in q or "same beneficiary" in q)):
        return None
    table = account_flow_summary(case)
    if table.empty:
        return None
    subset = table[(table["distinct_beneficiaries"] == 1) & (table["debit_count"] >= 2)]
    if subset.empty:
        return {"answer": "No account transacts with only a single inferred beneficiary.",
                "citations": [], "matched_pattern": "investigation_query_single_beneficiary"}
    lines = [
        f"  - {r['holder']} (account {r['account']}): {r['debit_count']} outgoing transfer(s), "
        f"all to one inferred beneficiary"
        for _, r in subset.iterrows()
    ]
    answer = (
        "Account(s) transacting with only one inferred beneficiary (counterparties are heuristic, "
        "derived from narration):\n" + "\n".join(lines)
    )
    citations = [_account_citation(case, r["account"]) for _, r in subset.iterrows()]
    return {"answer": answer, "citations": citations, "matched_pattern": "investigation_query_single_beneficiary"}


def _handle_cash_heavy(question: str, case: dict) -> dict | None:
    q = question.lower()
    if not ("cash" in q and any(w in q for w in ["withdrawal", "withdraw", "mostly", "perform"])):
        return None
    table = account_flow_summary(case)
    if table.empty:
        return None
    table = table.copy()
    table["cash_share"] = table.apply(
        lambda r: r["cash_debit_count"] / r["debit_count"] if r["debit_count"] else 0.0, axis=1
    )
    subset = table[(table["cash_debit_count"] >= 2) & (table["cash_share"] >= 0.5)].sort_values(
        "cash_share", ascending=False
    )
    if subset.empty:
        return {"answer": "No account is dominated by cash withdrawals in this case.",
                "citations": [], "matched_pattern": "investigation_query_cash_heavy"}
    lines = [
        f"  - {r['holder']} (account {r['account']}): {r['cash_debit_count']} cash debit(s) "
        f"= {round(r['cash_share'] * 100)}% of its outgoing transactions"
        for _, r in subset.head(5).iterrows()
    ]
    answer = "Account(s) mostly performing cash withdrawals:\n" + "\n".join(lines)
    citations = [_account_citation(case, r["account"]) for _, r in subset.head(5).iterrows()]
    return {"answer": answer, "citations": citations, "matched_pattern": "investigation_query_cash_heavy"}


# ─────────────────────────────────────────────────────────────────────────────
# CROSS-ACCOUNT INVESTIGATION (Goal 8) — shared counterparties / connections
# ─────────────────────────────────────────────────────────────────────────────

def _handle_common_counterparties(question: str, case: dict) -> dict | None:
    q = question.lower()
    if not any(p in q for p in [
        "common counterpart", "common beneficiar", "shared counterpart", "shared beneficiar",
        "same source", "same beneficiar", "connected account", "accounts connected",
        "shared pattern", "same counterpart", "receiving money from the same",
    ]):
        return None

    # Map each inferred counterparty -> set of accounts touching it.
    counterparty_accounts: dict[str, set[str]] = {}
    for account_id in (str(a) for a in case["clean"]["account_number"].astype(str).unique()):
        adf = add_counterparty(prepared_transactions(case, account_id))
        for cp in adf["_counterparty"].dropna().unique():
            counterparty_accounts.setdefault(cp, set()).add(account_id)

    shared = {cp: accts for cp, accts in counterparty_accounts.items() if len(accts) >= 2}
    if not shared:
        return {
            "answer": ("No inferred counterparty is shared between two or more accounts in this case "
                       "(counterparties are heuristic, derived from narration text)."),
            "citations": [], "matched_pattern": "cross_account_common_empty",
        }
    lines = [
        f"  - '{cp}' is shared by {len(accts)} accounts: {', '.join(sorted(accts))}"
        for cp, accts in sorted(shared.items(), key=lambda kv: len(kv[1]), reverse=True)[:10]
    ]
    answer = (
        f"{len(shared)} inferred counterpart(y/ies) are shared across multiple accounts — "
        f"possible links between accused (heuristic, narration-derived):\n" + "\n".join(lines)
    )
    accts_seen = {a for accts in shared.values() for a in accts}
    citations = [_account_citation(case, a) for a in sorted(accts_seen)][:15]
    return {"answer": answer, "citations": citations, "matched_pattern": "cross_account_common"}


_ANALYTICAL_HANDLERS = [
    # send-vs-receive before most-deposits: "mostly send/receive money" both
    # contain the substring "most", which the deposits handler would otherwise
    # greedily claim.
    _handle_send_vs_receive,
    _handle_most_deposits,
    _handle_single_beneficiary,
    _handle_cash_heavy,
    _handle_common_counterparties,
]


# ─────────────────────────────────────────────────────────────────────────────
# GOAL 10 — confidence / explainability footer
# ─────────────────────────────────────────────────────────────────────────────

def _analysis_label(pattern: str) -> str:
    for prefix, label in _ANALYSIS_LABELS.items():
        if pattern.startswith(prefix):
            return label
    return "Investigation Intelligence"


def _with_explainability(result: dict) -> dict:
    """Append the Goal 10 footer (Analysis Type / Handler / Evidence / Confidence)."""
    pattern = result.get("matched_pattern") or "investigation"
    footer = (
        "\n\n———\n"
        f"Analysis Type: {_analysis_label(pattern)}\n"
        f"Handler: {pattern}()\n"
        f"Evidence: clean_transactions.csv\n"
        f"Confidence: 100% (deterministic)"
    )
    result["answer"] = result["answer"] + footer
    return result


# ─────────────────────────────────────────────────────────────────────────────
# TOP-LEVEL ROUTER — the pipeline's "Investigation Intelligence" layer
# ─────────────────────────────────────────────────────────────────────────────

def try_investigation_answer(question: str, case: dict) -> dict | None:
    """
    Attempt to answer with the Investigation Intelligence layer.

    Order (most specific first): reasoning chains → rule engine → frequency
    analysis → analytical investigator queries. Returns an answer dict with the
    Goal 10 explainability footer attached, or None so the caller falls through
    to graph/RAG.
    """
    for sub_engine in (try_reasoning_answer, try_rules_answer, try_frequency_answer):
        result = sub_engine(question, case)
        if result is not None:
            return _with_explainability(result)

    for handler in _ANALYTICAL_HANDLERS:
        result = handler(question, case)
        if result is not None:
            return _with_explainability(result)

    return None
