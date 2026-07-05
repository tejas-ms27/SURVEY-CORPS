"""
timeseries_chart.py
─────────────────────────────────────────────────────────────────────────────
CIDECODE 2026 — Multi-Accused Cross-Account Investigation Engine
Module: Transaction-volume time-series chart (count + amount over time)

Shows whether transaction activity is increasing or decreasing over the
statement period, for the whole case or one account. Reuses period_counts()/
period_amounts() from frequency_analysis.py (the same bucketing already
proven behind "busiest day/month") rather than re-deriving date bucketing.

Granularity auto-scales to the date span (day / week / month) so a
multi-year case doesn't render as thousands of noisy daily points.
"""

from __future__ import annotations

import re

import pandas as pd

from chatbot.frequency_analysis import period_counts, period_amounts

_TIMESERIES_RE = re.compile(
    r"\b(transactions?|volume|txn)\b.{0,40}\b(over time|trend|trending|increasing|"
    r"decreasing|increase|decrease|growth|declin\w*|timeline|rising|falling)\b"
    r"|\b(over time|trend|trending|increasing|decreasing|increase|decrease|growth|"
    r"declin\w*|timeline|rising|falling)\b.{0,40}\b(transactions?|volume|txn)\b",
    re.IGNORECASE,
)

_GRANULARITY_LABEL = {"D": "day", "W": "week", "M": "month"}


def matches_timeseries_request(question: str) -> bool:
    """True when the question asks whether transaction volume is trending up/down."""
    return bool(_TIMESERIES_RE.search(question))


def _auto_granularity(dates: pd.Series) -> str:
    """Day for short spans, week for medium spans, month for multi-year cases."""
    if dates.empty:
        return "D"
    span_days = (dates.max() - dates.min()).days
    if span_days <= 60:
        return "D"
    if span_days <= 730:
        return "W"
    return "M"


def _scope_to_account(case: dict, account_id: str | None) -> pd.DataFrame:
    df = case["clean"]
    if account_id and "account_number" in df.columns:
        df = df[df["account_number"].astype(str) == str(account_id)]
    return df


def build_timeseries_figure(case: dict, account_id: str | None = None):
    """Dual-axis line chart: transaction count (left axis) and total amount
    moved (right axis), bucketed at an auto-selected granularity. Returns
    None when there are no dated transactions in scope."""
    import plotly.graph_objects as go

    df = _scope_to_account(case, account_id)
    dates = df["Date"].dropna() if "Date" in df.columns else pd.Series([], dtype="datetime64[ns]")
    if dates.empty:
        return None

    freq = _auto_granularity(dates)
    counts = period_counts(df, freq)
    amounts = period_amounts(df, freq)
    if counts.empty:
        return None

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=counts.index.to_timestamp(), y=counts.values, mode="lines+markers",
        name="Transaction count", line=dict(color="#291EC7"),
        hovertemplate="%{x|%d %b %Y}<br>Transactions: %{y:,}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=amounts.index.to_timestamp(), y=amounts.values, mode="lines+markers",
        name="Total amount (₹)", yaxis="y2", line=dict(color="#C7401E"),
        hovertemplate="%{x|%d %b %Y}<br>₹%{y:,.2f}<extra></extra>",
    ))

    granularity_label = _GRANULARITY_LABEL[freq]
    scope = f"account {account_id}" if account_id else "whole case"
    fig.update_layout(
        # Title pinned to the very top of the figure (container coords); the
        # legend sits just above the plot area (paper coords) so the two never
        # share the same band. Earlier the legend at y=1.12 rode up into the
        # title and the two overlapped once the chat squeezed the top margin.
        title=dict(
            text=f"Transaction volume over time (per {granularity_label}) — {scope}",
            y=0.98, yanchor="top", x=0.5, xanchor="center",
        ),
        # Plain grouped numbers, never SI-abbreviated ("k"/"M") — full ₹ figures throughout.
        xaxis=dict(title="Date", rangeslider=dict(visible=True), type="date"),
        yaxis=dict(title="Transaction count", side="left", tickformat=","),
        yaxis2=dict(title="Total amount (₹)", side="right", overlaying="y",
                     tickformat=",.0f", tickprefix="₹"),
        legend=dict(orientation="h", y=1.02, yanchor="bottom", x=0, xanchor="left"),
        # Roomy top margin so the title band and legend band both breathe.
        margin=dict(l=10, r=10, t=96, b=10),
        height=520,
    )
    return fig


def _summarize_trend(counts: pd.Series) -> str:
    """Compares the mean of the first half of the period series against the
    second half — a simple, explainable increasing/decreasing/stable call."""
    if len(counts) < 2:
        return "not enough data points to determine a trend"
    midpoint = len(counts) // 2
    first_half = counts.iloc[:midpoint].mean()
    second_half = counts.iloc[midpoint:].mean()
    if second_half > first_half * 1.1:
        return "increasing"
    if second_half < first_half * 0.9:
        return "decreasing"
    return "roughly stable"


def build_timeseries_response(question: str, case: dict) -> dict | None:
    """Routing entry point: returns a chart response dict, or None to let the
    caller fall through to the next handler."""
    if not matches_timeseries_request(question):
        return None

    from chatbot.structured_queries import _resolve_account

    account_id = _resolve_account(question, case)
    df = _scope_to_account(case, account_id)
    dates = df["Date"].dropna() if "Date" in df.columns else pd.Series([], dtype="datetime64[ns]")
    if dates.empty:
        scope = f"account {account_id}" if account_id else "this case"
        return {
            "answer": f"No dated transactions are available for {scope} to chart.",
            "chart": None, "citations": [], "matched_pattern": "timeseries_empty",
        }

    freq = _auto_granularity(dates)
    counts = period_counts(df, freq)
    fig = build_timeseries_figure(case, account_id)
    trend = _summarize_trend(counts)
    granularity_label = _GRANULARITY_LABEL[freq]

    holder = None
    if account_id:
        holder = case.get("accounts", {}).get(str(account_id), {}).get("account_details", {}).get("account_holder")
    label = f"{holder} (account {account_id})" if holder else (f"account {account_id}" if account_id else "the whole case")

    answer = (
        f"Transaction volume for {label}, bucketed by {granularity_label}: "
        f"{trend} over the observed period. Chart shown below."
    )
    return {"answer": answer, "chart": fig, "citations": [], "matched_pattern": "timeseries_trend"}
