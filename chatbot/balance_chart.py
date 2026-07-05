"""
balance_chart.py
─────────────────────────────────────────────────────────────────────────────
CIDECODE 2026 — Multi-Accused Cross-Account Investigation Engine
Module: Balance-over-time chart per account

Uses the bank-stated `Balance` field from the per-account JSON transactions
(case["accounts"][id]["transactions"]) as the authoritative source, rather
than recomputing a cumulative debit/credit sum from the clean CSV — the CSV
is known to have schema drift across extraction runs (e.g. Transaction_Type
sometimes absent), and any gap in the row set would silently compound a
recomputed running total away from the real, bank-reported balance. The
cumulative-sum reconstruction is used only as a fallback when Balance is
missing for most of an account's rows.

flagged_transactions.csv has no txn_id column, so flagged points are joined
against the per-account transactions on (Date, Debit, Credit) instead.
"""

from __future__ import annotations

import re

import pandas as pd

_BALANCE_TREND_RE = re.compile(
    r"\bbalance\b.*\b(over time|trend|history|movement|timeline)\b"
    r"|\b(trend|history|movement|timeline)\b.*\bbalance\b",
    re.IGNORECASE,
)


def matches_balance_trend_request(question: str) -> bool:
    """True when the question is asking to see an account's balance trajectory."""
    return bool(_BALANCE_TREND_RE.search(question))


def _account_transactions_frame(case: dict, account_id: str) -> pd.DataFrame:
    txns = case.get("accounts", {}).get(str(account_id), {}).get("transactions", [])
    if not txns:
        return pd.DataFrame()
    df = pd.DataFrame(txns)
    df["_date"] = pd.to_datetime(df.get("Date"), format="%d/%m/%Y", errors="coerce")
    sort_cols = ["_date"] + (["Time"] if "Time" in df.columns else [])
    return df.sort_values(sort_cols).reset_index(drop=True)


def _resolve_balance_series(df: pd.DataFrame) -> pd.Series:
    """Real stated Balance where present; cumulative-sum fallback only if
    Balance is missing/'not extracted' for most rows of this account."""
    balance = pd.to_numeric(df.get("Balance"), errors="coerce")
    if len(df) and balance.isna().mean() <= 0.5:
        return balance.ffill()
    debit = pd.to_numeric(df.get("Debit"), errors="coerce").fillna(0.0)
    credit = pd.to_numeric(df.get("Credit"), errors="coerce").fillna(0.0)
    return (credit - debit).cumsum()


def _flagged_keys_for_account(case: dict, account_id: str) -> set[tuple]:
    """Join key is (Date, Debit, Credit) — flagged_transactions.csv has no txn_id."""
    flagged = case.get("flagged")
    if flagged is None or flagged.empty or "Account_ID" not in flagged.columns:
        return set()
    sub = flagged[flagged["Account_ID"].astype(str) == str(account_id)]
    keys = set()
    for _, row in sub.iterrows():
        date = row.get("Date")
        if pd.notna(date):
            date_str = date.strftime("%d/%m/%Y") if isinstance(date, pd.Timestamp) else str(date)
            keys.add((
                date_str,
                round(float(row.get("Debit") or 0), 2),
                round(float(row.get("Credit") or 0), 2),
            ))
    return keys


def build_balance_trend_figure(case: dict, account_id: str):
    """Line chart of an account's balance over time, with flagged transactions
    marked as red dots. Returns None if the account has no transaction history."""
    import plotly.graph_objects as go

    df = _account_transactions_frame(case, account_id)
    if df.empty:
        return None

    df["_balance"] = _resolve_balance_series(df)
    flagged_keys = _flagged_keys_for_account(case, account_id)
    df["_is_flagged"] = df.apply(
        lambda r: (
            str(r.get("Date")),
            round(float(r.get("Debit") or 0), 2),
            round(float(r.get("Credit") or 0), 2),
        ) in flagged_keys,
        axis=1,
    )

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["_date"], y=df["_balance"], mode="lines",
        name="Balance", line=dict(color="#291EC7"),
        hovertemplate="%{x|%d %b %Y}<br>₹%{y:,.2f}<extra></extra>",
    ))
    flagged_rows = df[df["_is_flagged"]]
    if not flagged_rows.empty:
        fig.add_trace(go.Scatter(
            x=flagged_rows["_date"], y=flagged_rows["_balance"], mode="markers",
            name="Flagged transaction", marker=dict(color="#C7401E", size=10),
            hovertemplate="%{x|%d %b %Y}<br>₹%{y:,.2f} (flagged)<extra></extra>",
        ))

    holder = case.get("accounts", {}).get(str(account_id), {}).get("account_details", {}).get("account_holder") or account_id
    fig.update_layout(
        title=f"Balance over time — {holder} ({account_id})",
        # Plain grouped ₹ figures on the axis and hover — never SI-abbreviated ("k"/"M").
        xaxis=dict(title="Date", rangeslider=dict(visible=True), type="date"),
        yaxis=dict(title="Balance (₹)", tickformat=",.0f", tickprefix="₹"),
        margin=dict(l=10, r=10, t=60, b=10),
        height=480,
    )
    return fig


def build_balance_trend_response(question: str, case: dict) -> dict | None:
    """Routing entry point: returns a chart response dict, or None to let the
    caller fall through to the next handler."""
    if not matches_balance_trend_request(question):
        return None

    from chatbot.structured_queries import _resolve_account

    account_id = _resolve_account(question, case)
    if not account_id:
        return {
            "answer": (
                "Which account's balance trend would you like? Name the account "
                "number or holder, e.g. 'balance trend for account 12668100018596'."
            ),
            "chart": None, "citations": [], "matched_pattern": "balance_trend_no_account",
        }

    fig = build_balance_trend_figure(case, account_id)
    if fig is None:
        return {
            "answer": f"No transaction history is available for account {account_id} to chart.",
            "chart": None, "citations": [], "matched_pattern": "balance_trend_empty",
        }

    holder = case.get("accounts", {}).get(str(account_id), {}).get("account_details", {}).get("account_holder") or "(unidentified)"
    return {
        "answer": f"Balance-over-time chart for {holder} (account {account_id}) is shown below.",
        "chart": fig, "citations": [], "matched_pattern": "balance_trend",
    }
