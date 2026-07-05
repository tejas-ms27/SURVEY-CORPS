"""
reasoning_engine.py
─────────────────────────────────────────────────────────────────────────────
CIDECODE 2026 — Multi-Accused Cross-Account Investigation Engine
Module: Multi-Hop, Temporal & Chain-of-Evidence Reasoning (Phase 3, Goals 3/6/7)

The retrieval chatbot answers one-hop questions ("what is X"). This module
chains DETERMINISTIC operations to answer questions that need several linked
facts:

  * received-from-A-then-paid-B  (money passing through an intermediary)
  * highest-credit-then-moved-≥N% (a large inflow largely swept out)
  * "why is this account suspicious" (chain-of-evidence explanation)
  * "what happened before/after this transaction" (temporal ordering)

Every conclusion is built from real transaction rows — the reasoning is a
sequence of pandas filters, not an LLM narrative — so it satisfies Goal 7's
hard rule: never fabricate an explanation. When the deterministic chain finds
nothing, the handler returns None and the normal RAG fallback takes over.
"""

from __future__ import annotations

import re

import pandas as pd

from chatbot.frequency_analysis import (
    add_counterparty,
    frequency_metrics,
    prepared_transactions,
)
from chatbot.investigation_rules import run_all_rules

# "Later / immediately after" for the reasoning chains below.
CHAIN_WINDOW_DAYS = 3
HIGH_CREDIT_MOVE_RATIO = 0.80


def _rupees(v: float) -> str:
    return f"₹{v:,.2f}"


def _date(row: pd.Series) -> str:
    d = row.get("Date")
    return d.strftime("%d/%m/%Y") if isinstance(d, pd.Timestamp) and pd.notna(d) else "?"


def _citation(row: pd.Series, account_id: str) -> dict:
    return {
        "type": "transaction",
        "ref": str(row.get("txn_id") or row.get("Transaction_ID") or "?"),
        "account": str(account_id),
        "date": _date(row),
    }


def _holder(case: dict, account_id: str) -> str:
    holder = case.get("accounts", {}).get(str(account_id), {}).get("account_details", {}).get("account_holder")
    return str(holder) if holder else "(unidentified)"


def _accounts(case: dict) -> list[str]:
    df = case["clean"]
    if "account_number" not in df.columns:
        return []
    return [str(a) for a in df["account_number"].astype(str).unique()]


# ─────────────────────────────────────────────────────────────────────────────
# GOAL 3 — MULTI-HOP: received from A, later transferred to B
# ─────────────────────────────────────────────────────────────────────────────

_FROM_RE = re.compile(
    r"from\s+([a-z0-9 &.'-]+?)(?:\s+(?:and|then|later|who|which|transferred|sent|moved|paid)\b|$)",
    re.IGNORECASE,
)
_TO_RE = re.compile(r"to\s+([a-z0-9 &.'-]+?)\s*[?.!]?$", re.IGNORECASE)


def received_from_then_paid(case: dict, source: str, dest: str) -> dict | None:
    """
    Find accounts that received money from `source` and LATER paid `dest`
    (both matched heuristically against the counterparty inferred from
    narration). Returns an answer dict, or None if the chain finds nothing.
    """
    source_l, dest_l = source.strip().lower(), dest.strip().lower()
    hits, citations = [], []
    for account_id in _accounts(case):
        adf = add_counterparty(prepared_transactions(case, account_id))
        adf = adf[adf["_counterparty"].notna()]
        if adf.empty:
            continue
        inbound = adf[(adf["_direction"] == "credit")
                      & adf["_counterparty"].str.lower().str.contains(source_l, na=False)]
        if inbound.empty:
            continue
        earliest_in = inbound["Date"].min()
        outbound = adf[(adf["_direction"] == "debit")
                       & adf["_counterparty"].str.lower().str.contains(dest_l, na=False)]
        if pd.notna(earliest_in):
            outbound = outbound[outbound["Date"] >= earliest_in]
        if outbound.empty:
            continue
        received = float(inbound["_amount"].sum())
        paid = float(outbound["_amount"].sum())
        hits.append(
            f"  - {_holder(case, account_id)} (account {account_id}): received "
            f"{_rupees(received)} from '{source.strip()}', then paid {_rupees(paid)} to "
            f"'{dest.strip()}' (first inflow {earliest_in.strftime('%d/%m/%Y') if pd.notna(earliest_in) else '?'})"
        )
        citations += [_citation(r, account_id) for _, r in inbound.head(3).iterrows()]
        citations += [_citation(r, account_id) for _, r in outbound.head(3).iterrows()]

    if not hits:
        return {
            "answer": (f"No account in this case received money from '{source.strip()}' and "
                       f"later transferred to '{dest.strip()}' (based on counterparties inferred "
                       f"from narration)."),
            "citations": [], "matched_pattern": "reasoning_multi_hop_empty",
        }
    answer = (
        f"{len(hits)} intermediary account(s) received from '{source.strip()}' and later "
        f"paid '{dest.strip()}':\n" + "\n".join(hits)
    )
    return {"answer": answer, "citations": citations, "matched_pattern": "reasoning_multi_hop"}


# ─────────────────────────────────────────────────────────────────────────────
# GOAL 3 — highest credit then moved ≥ N% within a few days
# ─────────────────────────────────────────────────────────────────────────────

def highest_credit_then_moved(case: dict) -> dict | None:
    """
    Identify the single largest credit in the case, then check how much of it
    was debited back out within CHAIN_WINDOW_DAYS and compare against the ratio.
    """
    df = add_counterparty(prepared_transactions(case))
    credits = df[df["_direction"] == "credit"].dropna(subset=["Date"])
    if credits.empty:
        return None
    top = credits.loc[credits["_amount"].idxmax()]
    account_id = str(top.get("account_number"))
    c_date = top["Date"]
    window_end = c_date + pd.Timedelta(days=CHAIN_WINDOW_DAYS)

    adf = prepared_transactions(case, account_id)
    later_debits = adf[(adf["_direction"] == "debit")
                       & (adf["Date"] >= c_date) & (adf["Date"] <= window_end)]
    moved = float(later_debits["_amount"].sum())
    credit_amt = float(top["_amount"])
    pct = round(100 * moved / credit_amt) if credit_amt else 0
    crossed = moved >= HIGH_CREDIT_MOVE_RATIO * credit_amt

    reasoning = [
        f"1. Highest credit in the case: {_rupees(credit_amt)} into account {account_id} "
        f"({_holder(case, account_id)}) on {_date(top)}.",
        f"2. Outbound debits within {CHAIN_WINDOW_DAYS} day(s): {_rupees(moved)}.",
        f"3. That is {pct}% of the inbound amount "
        f"({'≥' if crossed else 'below'} the {round(HIGH_CREDIT_MOVE_RATIO * 100)}% threshold).",
    ]
    conclusion = (
        f"Account {account_id} received the highest credit and moved {pct}% of it straight "
        f"back out within {CHAIN_WINDOW_DAYS} days — consistent with pass-through / layering."
        if crossed else
        f"Account {account_id} received the highest credit but retained most of it "
        f"(only {pct}% moved out within {CHAIN_WINDOW_DAYS} days)."
    )
    answer = "Reasoning:\n" + "\n".join(reasoning) + f"\n\nConclusion:\n{conclusion}"
    citations = [_citation(top, account_id)] + [_citation(r, account_id) for _, r in later_debits.iterrows()]
    return {"answer": answer, "citations": citations, "matched_pattern": "reasoning_highest_credit_moved"}


# ─────────────────────────────────────────────────────────────────────────────
# GOAL 7 — CHAIN-OF-EVIDENCE: why is this account suspicious?
# ─────────────────────────────────────────────────────────────────────────────

def explain_account(case: dict, account_id: str) -> dict:
    """
    Assemble a numbered, evidence-backed explanation of why an account looks
    (or does not look) suspicious — drawn entirely from rule findings and
    frequency statistics, never from an LLM's imagination (Goal 7).
    """
    findings = run_all_rules(case, account_id=account_id)
    metrics = frequency_metrics(case, account_id)
    holder = _holder(case, account_id)

    reasoning, citations = [], []
    for i, f in enumerate(findings, start=1):
        reasoning.append(f"{i}. {f.rule}: {f.summary}")
        citations += f.citations

    if metrics and not metrics["spike_days"].empty:
        spikes = metrics["spike_days"]
        reasoning.append(
            f"{len(reasoning) + 1}. Activity spike: {int(spikes.max())} transaction(s) on "
            f"{spikes.idxmax().strftime('%d/%m/%Y')} versus a daily average of {metrics['avg_per_day']}."
        )

    if not reasoning:
        return {
            "answer": (f"No deterministic red flags were found for {holder} (account {account_id}). "
                       f"Nothing in the rule engine or frequency analysis marks this account as suspicious."),
            "citations": [], "matched_pattern": "reasoning_explain_clear",
        }

    high = sum(1 for f in findings if f.risk == "High")
    if high >= 2:
        conclusion = "High likelihood of layering activity."
    elif high == 1:
        conclusion = "Elevated risk — at least one high-severity pattern present."
    else:
        conclusion = "Some risk indicators present; warrants a closer manual review."

    answer = (
        f"Why account {account_id} ({holder}) is under scrutiny:\n\n"
        f"Reasoning:\n" + "\n".join(reasoning) + f"\n\nConclusion:\n{conclusion}"
    )
    return {"answer": answer, "citations": citations, "matched_pattern": "reasoning_explain"}


# ─────────────────────────────────────────────────────────────────────────────
# GOAL 6 — TEMPORAL: what happened before / after a reference transaction
# ─────────────────────────────────────────────────────────────────────────────

def _reference_transaction(question: str, adf: pd.DataFrame) -> pd.Series | None:
    """Pick the transaction a temporal question is anchored on."""
    # Explicit txn id in the question wins.
    for token in re.findall(r"[A-Za-z0-9_]+", question):
        match = adf[adf.get("txn_id").astype(str) == token] if "txn_id" in adf.columns else adf.iloc[0:0]
        if not match.empty:
            return match.iloc[0]
    q = question.lower()
    if any(w in q for w in ["salary", "payroll"]):
        sal = adf[adf["Narration"].astype(str).str.contains(r"salary|payroll", case=False, na=False)]
        if not sal.empty:
            return sal.sort_values("Date").iloc[0]
    if any(w in q for w in ["largest", "highest", "biggest"]):
        return adf.loc[adf["_amount"].idxmax()] if not adf.empty else None
    return None


def temporal_events(case: dict, question: str, account_id: str) -> dict | None:
    """List transactions immediately before/after a reference transaction."""
    adf = prepared_transactions(case, account_id).dropna(subset=["Date"])
    if adf.empty:
        return None
    ref = _reference_transaction(question, adf)
    if ref is None:
        return None

    q = question.lower()
    is_before = "before" in q
    ref_date = ref["Date"]
    window = adf[(adf["Date"] >= ref_date - pd.Timedelta(days=CHAIN_WINDOW_DAYS))
                 & (adf["Date"] <= ref_date + pd.Timedelta(days=CHAIN_WINDOW_DAYS))]
    window = window[window.index != ref.name]
    if is_before:
        window = window[window["Date"] <= ref_date]
        label = "before"
    else:
        window = window[window["Date"] >= ref_date]
        label = "after"

    if window.empty:
        return {
            "answer": f"No transactions found {label} the reference transaction on {_date(ref)}.",
            "citations": [], "matched_pattern": "reasoning_temporal_empty",
        }
    lines = [
        f"  - {_date(r)}: {_rupees(float(r['_amount']))} ({r['_direction']}) — "
        f"{str(r.get('Narration') or '').strip()[:60]}"
        for _, r in window.sort_values("Date").iterrows()
    ]
    answer = (
        f"Reference: {_rupees(float(ref['_amount']))} ({ref['_direction']}) on {_date(ref)} in "
        f"account {account_id}. Events {label} it (±{CHAIN_WINDOW_DAYS} days):\n" + "\n".join(lines)
    )
    citations = [_citation(r, account_id) for _, r in window.iterrows()]
    return {"answer": answer, "citations": citations, "matched_pattern": "reasoning_temporal"}


# ─────────────────────────────────────────────────────────────────────────────
# NATURAL-LANGUAGE HANDLER
# ─────────────────────────────────────────────────────────────────────────────

def try_reasoning_answer(question: str, case: dict) -> dict | None:
    """Dispatch multi-hop / temporal / chain-of-evidence reasoning questions."""
    from chatbot.structured_queries import _resolve_account

    q = question.lower()

    # Salary received then immediately transferred (Goal 3 example 3).
    if "salary" in q and any(w in q for w in ["transfer", "withdraw", "immediately", "then", "moved", "spent"]):
        from chatbot.investigation_rules import rule_salary_immediately_withdrawn

        findings = rule_salary_immediately_withdrawn(case)
        if not findings:
            return {
                "answer": ("No account shows a salary credit that was immediately transferred "
                           "back out (no narration-identified salary inflow met the rapid-outflow test)."),
                "citations": [], "matched_pattern": "reasoning_salary_transfer_empty",
            }
        blocks = [f.render() for f in findings[:8]]
        answer = (f"{len(findings)} account/salary event(s) where salary was received and quickly "
                  f"moved out:\n\n" + "\n\n".join(blocks))
        citations = [c for f in findings[:8] for c in f.citations]
        return {"answer": answer, "citations": citations, "matched_pattern": "reasoning_salary_transfer"}

    # Multi-hop: "... from X ... transferred ... to Y"
    if "from" in q and " to " in q and any(
        w in q for w in ["transfer", "sent", "moved", "paid", "later", "then", "received"]
    ):
        source_m = _FROM_RE.search(question)
        dest_m = _TO_RE.search(question)
        if source_m and dest_m:
            source, dest = source_m.group(1).strip(), dest_m.group(1).strip()
            if len(source) >= 2 and len(dest) >= 2 and source.lower() != dest.lower():
                return received_from_then_paid(case, source, dest)

    # Highest credit then moved out
    if ("highest" in q or "largest" in q or "biggest" in q) and "credit" in q and any(
        w in q for w in ["transfer", "moved", "moved out", "80%", "later", "%", "within"]
    ):
        result = highest_credit_then_moved(case)
        if result:
            return result

    # Chain-of-evidence explanation
    if any(w in q for w in ["why", "explain", "reasoning", "chain of evidence"]) and any(
        w in q for w in ["suspicious", "flag", "risky", "scrutin", "layering"]
    ):
        account_id = _resolve_account(question, case)
        if account_id:
            return explain_account(case, account_id)

    # Temporal before/after
    if ("before" in q or "after" in q) and any(
        w in q for w in ["transaction", "salary", "happened", "event", "activity"]
    ):
        account_id = _resolve_account(question, case)
        if account_id:
            return temporal_events(case, question, account_id)

    return None
