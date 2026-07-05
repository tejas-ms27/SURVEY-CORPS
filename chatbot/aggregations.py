"""
aggregations.py
─────────────────────────────────────────────────────────────────────────────
CIDECODE 2026 — Multi-Accused Cross-Account Investigation Engine
Module: Exact Arithmetic via Pre-Vetted Parameterized Functions
        (advanced-features spec, Section 2)

READ SECTION 0.3 AND 2.3 OF THE SPEC BEFORE TOUCHING THIS — this is
deliberately NOT an "LLM writes and runs pandas code" feature.

The goal is exact arithmetic over many rows (totals, counts, averages),
computed in real Python — not estimated by an LLM reading a handful of
retrieved chunks. The mechanism is a FIXED registry of pre-vetted,
human-written aggregation functions. The LLM's ONLY job is to SELECT one
function from the registry and fill in its parameters; it never generates
code that gets executed.

HARD RULE (spec 2.3): the `_REGISTRY` dict below is the ONLY mechanism by
which the LLM's output causes Python to run, and every entry is a function a
human wrote and can read top to bottom. Nothing here may ever evolve toward
passing LLM-generated text into eval(), exec(), pd.eval(), or any similar
dynamic-execution mechanism. If a new question pattern needs a calculation
not covered here, ADD a new named function to the registry — never add a
generic code-execution escape hatch.
"""

from __future__ import annotations

import inspect
import json

import pandas as pd


# ─────────────────────────────────────────────────────────────────────────────
# THE FIXED FUNCTION REGISTRY — every entry is human-written and reviewable.
# ─────────────────────────────────────────────────────────────────────────────

def _normalize_direction(direction: str | None) -> str | None:
    if not direction:
        return None
    direction = str(direction).strip().lower().rstrip("s")
    return direction if direction in ("debit", "credit") else None


def _scope_to_account(df: pd.DataFrame, account_id: str | None) -> pd.DataFrame:
    if account_id and "account_number" in df.columns:
        return df[df["account_number"].astype(str) == str(account_id)]
    return df


def sum_by_direction_and_period(case: dict, account_id: str | None = None, direction: str | None = None,
                                start_date: str | None = None, end_date: str | None = None) -> dict:
    """Sum of Debit or Credit amounts, optionally filtered by account and date range."""
    direction = _normalize_direction(direction)
    if direction is None:
        raise ValueError("direction must be 'debit' or 'credit'")
    df = _scope_to_account(case["clean"], account_id)
    df = df[df["Transaction_Type"].astype(str).str.lower() == direction]
    if start_date:
        df = df[df["Date"] >= pd.to_datetime(start_date, errors="coerce")]
    if end_date:
        df = df[df["Date"] <= pd.to_datetime(end_date, errors="coerce")]
    col = "Debit" if direction == "debit" else "Credit"
    values = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
    return {"total": float(values.sum()), "count": len(df), "filtered_rows": df}


def sum_total_by_period(case: dict, account_id: str | None = None,
                         start_date: str | None = None, end_date: str | None = None) -> dict:
    """
    Sum of Debit + Credit combined (total money moved, regardless of
    direction), optionally scoped to an account and/or date range, with
    per-account attribution so "which account" is answered by this same
    call.
    """
    df = _scope_to_account(case["clean"], account_id)
    if start_date:
        df = df[df["Date"] >= pd.to_datetime(start_date, errors="coerce")]
    if end_date:
        df = df[df["Date"] <= pd.to_datetime(end_date, errors="coerce")]

    debit = pd.to_numeric(df["Debit"], errors="coerce").fillna(0.0)
    credit = pd.to_numeric(df["Credit"], errors="coerce").fillna(0.0)
    df = df.assign(_amount=debit + credit)
    total = float(df["_amount"].sum())

    by_account = []
    if "account_number" in df.columns:
        grouped = df.groupby("account_number")["_amount"].sum().sort_values(ascending=False)
        for acct_id, amt in grouped.items():
            holder = (case["accounts"].get(str(acct_id), {})
                          .get("account_details", {}).get("account_holder")) or "(unidentified)"
            by_account.append({"account_id": str(acct_id), "holder": holder, "total": float(amt)})

    return {"total": total, "count": len(df), "by_account": by_account, "filtered_rows": df}


def count_transactions_above_threshold(case: dict, account_id: str | None = None, amount: float | None = None) -> dict:
    """Count + list of transactions where Debit or Credit exceeds a threshold."""
    if amount is None:
        raise ValueError("amount threshold is required")
    amount = float(amount)
    df = _scope_to_account(case["clean"], account_id)
    debit = pd.to_numeric(df["Debit"], errors="coerce").fillna(0.0)
    credit = pd.to_numeric(df["Credit"], errors="coerce").fillna(0.0)
    mask = (debit > amount) | (credit > amount)
    return {"count": int(mask.sum()), "threshold": amount, "filtered_rows": df[mask]}


def average_transaction_amount(case: dict, account_id: str | None = None, direction: str | None = None) -> dict:
    """Average Debit/Credit amount, optionally scoped to one account/direction."""
    direction = _normalize_direction(direction)
    df = _scope_to_account(case["clean"], account_id)
    if direction:
        df = df[df["Transaction_Type"].astype(str).str.lower() == direction]
        col = "Debit" if direction == "debit" else "Credit"
        values = pd.to_numeric(df[col], errors="coerce")
    else:
        values = pd.concat([
            pd.to_numeric(df["Debit"], errors="coerce"),
            pd.to_numeric(df["Credit"], errors="coerce"),
        ])
    values = values[values > 0]
    return {"average": float(values.mean()) if len(values) else 0.0, "count": int(len(values))}


# Add more functions to this registry as real investigator question patterns
# are observed — keep each one narrow, named clearly, and independently
# testable. Do NOT add a generic "run_arbitrary_query(code)" escape hatch.
_REGISTRY = {
    "sum_by_direction_and_period": sum_by_direction_and_period,
    "sum_total_by_period": sum_total_by_period,
    "count_transactions_above_threshold": count_transactions_above_threshold,
    "average_transaction_amount": average_transaction_amount,
}


# ─────────────────────────────────────────────────────────────────────────────
# THE LLM'S ROLE — selection and parameter-filling ONLY, never code generation.
# ─────────────────────────────────────────────────────────────────────────────

_AGGREGATION_TOOL_SELECTION_PROMPT = """You are selecting which financial \
calculation to run for an investigator's question. You do NOT write code. \
You ONLY choose one function from this list and fill in its parameters:

- sum_by_direction_and_period(account_id, direction, start_date, end_date) — use \
ONLY when the question specifies a direction (debit/credit/"received"/"paid"/"withdrawn"/"deposited").
- sum_total_by_period(account_id, start_date, end_date) — use when the question asks \
for a combined/overall TOTAL amount moved or transferred WITHOUT specifying debit or \
credit, and/or asks which account(s) performed the transactions.
- count_transactions_above_threshold(account_id, amount)
- average_transaction_amount(account_id, direction)

Return ONLY a JSON object: {"function": "<name>", "params": {...}}.
If the question doesn't clearly match any of these, return
{"function": null, "params": {}} and it will fall back to a normal answer.
Use null for any parameter not specified in the question (e.g. account_id
is null if the question doesn't name a specific account). direction must be
"debit" or "credit". Dates must be ISO format (YYYY-MM-DD). amount must be a
plain number.

IMPORTANT: these functions return a single computed number, not a chart or a
pattern. If the question is asking whether activity/volume/transactions are
trending, increasing, decreasing, or changing OVER TIME (rather than asking
for one total/count/average figure), return {"function": null, "params": {}}
— that is handled by a dedicated trend-chart feature elsewhere, not by you."""


def _filter_params(func, params: dict) -> dict:
    """
    Keep only parameters the target function actually accepts (besides `case`),
    dropping nulls. This keeps an over-eager LLM (extra/unknown keys) from
    crashing the call — a defensive guard, not a code-generation path.
    """
    accepted = set(inspect.signature(func).parameters) - {"case"}
    return {k: v for k, v in (params or {}).items() if k in accepted and v is not None}


def try_aggregation_answer(question: str, case: dict) -> dict | None:
    """
    Ask the LLM to SELECT a pre-vetted function and PARAMETERS only (never
    code) for arithmetic-heavy questions, then execute that function directly.
    The LLM's output is a function name (checked against the fixed registry)
    plus a parameter dict — nothing is ever eval()'d or exec()'d.

    Returns an answer dict on a confident match, or None to fall through.
    """
    from chatbot.language import _strip_json_fences
    from chatbot.rag_chat import generate

    try:
        raw = generate([
            {"role": "system", "content": _AGGREGATION_TOOL_SELECTION_PROMPT},
            {"role": "user", "content": question},
        ], temperature=0.0)
    except Exception:
        return None  # provider/network issue — fall back to the normal flow

    try:
        selection = json.loads(_strip_json_fences(raw))
    except (json.JSONDecodeError, TypeError):
        return None

    func_name = selection.get("function")
    if func_name is None:
        return None

    func = _REGISTRY.get(func_name)
    if func is None:
        # LLM named a function that doesn't exist in the registry — treat as
        # no match, do not guess (checklist #5).
        return None

    params = _filter_params(func, selection.get("params", {}))
    try:
        result = func(case=case, **params)
    except (ValueError, TypeError, KeyError):
        return None  # bad/missing required parameter — fall through gracefully

    return build_aggregation_response(func_name, params, result)


# ─────────────────────────────────────────────────────────────────────────────
# RENDERING — the EXACT computed number, plus an optional Plotly chart.
# ─────────────────────────────────────────────────────────────────────────────

def format_aggregation_answer(func_name: str, params: dict, result: dict) -> str:
    """Plain-language summary of the EXACT number (never LLM-estimated)."""
    account = params.get("account_id")
    scope = f" for account {account}" if account else " across all accounts"

    if func_name == "sum_by_direction_and_period":
        direction = _normalize_direction(params.get("direction")) or "transaction"
        period_bits = []
        if params.get("start_date"):
            period_bits.append(f"from {params['start_date']}")
        if params.get("end_date"):
            period_bits.append(f"to {params['end_date']}")
        period = (" " + " ".join(period_bits)) if period_bits else ""
        return (
            f"The total of {direction} transactions{scope}{period} is "
            f"₹{result['total']:,.2f}, computed over {result['count']} transaction(s)."
        )

    if func_name == "sum_total_by_period":
        period_bits = []
        if params.get("start_date"):
            period_bits.append(f"from {params['start_date']}")
        if params.get("end_date"):
            period_bits.append(f"to {params['end_date']}")
        period = (" " + " ".join(period_bits)) if period_bits else ""
        lines = [
            f"The total amount transferred{scope}{period} is "
            f"₹{result['total']:,.2f}, computed over {result['count']} transaction(s)."
        ]
        by_account = result.get("by_account") or []
        if by_account and not account:
            lines.append("Breakdown by account:")
            lines += [
                f"  - {r['holder']} (account {r['account_id']}): ₹{r['total']:,.2f}"
                for r in by_account
            ]
        return "\n".join(lines)

    if func_name == "count_transactions_above_threshold":
        return (
            f"There are {result['count']} transaction(s){scope} where the debit "
            f"or credit amount exceeds ₹{result['threshold']:,.2f}."
        )

    if func_name == "average_transaction_amount":
        direction = _normalize_direction(params.get("direction"))
        direction_str = f" {direction}" if direction else ""
        return (
            f"The average{direction_str} transaction amount{scope} is "
            f"₹{result['average']:,.2f}, over {result['count']} transaction(s)."
        )

    return "Computed an exact result for this question."


def build_aggregation_response(func_name: str, params: dict, result: dict) -> dict:
    """
    Combine the exact computed number with an optional chart when the result
    includes filtered rows worth charting.
    """
    answer_text = format_aggregation_answer(func_name, params, result)

    chart = None
    rows = result.get("filtered_rows")
    if rows is not None and len(rows) > 1 and "Date" in rows.columns:
        try:
            import plotly.express as px

            chart = px.bar(
                rows, x="Date", y=["Debit", "Credit"],
                title="Transactions matching this query",
            )
        except Exception:
            chart = None

    citations = _citations_from_rows(rows)
    return {
        "answer": answer_text,
        "chart": chart,
        "citations": citations,
        "matched_pattern": f"aggregation:{func_name}",
    }


def _citations_from_rows(rows) -> list[dict]:
    if rows is None or len(rows) == 0:
        return []
    citations = []
    for _, row in rows.head(10).iterrows():
        date = row.get("Date")
        date_str = date.strftime("%d/%m/%Y") if isinstance(date, pd.Timestamp) and pd.notna(date) else str(date)
        citations.append({
            "type": "transaction",
            "ref": str(row.get("txn_id") or row.get("Transaction_ID") or "?"),
            "account": str(row.get("account_number") or "?"),
            "date": date_str,
        })
    return citations
