"""
frequency_analysis.py
─────────────────────────────────────────────────────────────────────────────
CIDECODE 2026 — Multi-Accused Cross-Account Investigation Engine
Module: Transaction Frequency & Activity Analytics (Phase 3, Goals 2 & 5)

This is the LEAF utility module of the new Investigation Intelligence layer.
It owns the low-level transaction-shaping helpers that every other Phase 3
module (investigation_rules, reasoning_engine, investigation_queries) reuses,
so there is exactly ONE definition of "prepare the clean transactions with a
unified amount/direction and a heuristic counterparty column".

NO LLM is involved anywhere in this file — every number is computed in real
Python over the in-memory `case["clean"]` DataFrame. That is the whole point:
an investigator asking "which account is busiest" deserves an exact,
reproducible answer, not an estimate a language model read off a few chunks.

Reuses:
  - _with_amount()      from structured_queries  (unified _amount/_direction,
                        robust to Transaction_Type schema drift between runs)
  - extract_counterparty_hint() from counterparty (the SAME heuristic the
                        money-flow graph uses — never a second divergent copy)
"""

from __future__ import annotations

import re

import pandas as pd

from chatbot.counterparty import extract_counterparty_hint
from chatbot.structured_queries import _with_amount

# A day is considered a "spike" when its transaction count sits this many
# standard deviations above the account's mean daily activity. 2.0 is the
# conventional two-sigma threshold — high enough that ordinary busy days do
# not trip it, low enough to surface genuine bursts.
SPIKE_Z_THRESHOLD = 2.0

# An account whose most recent transaction predates the case's latest
# transaction by more than this many days is treated as dormant/inactive
# relative to the rest of the case.
DORMANT_GAP_DAYS = 90


# ─────────────────────────────────────────────────────────────────────────────
# SHARED TRANSACTION-SHAPING HELPERS (imported across the Phase 3 modules)
# ─────────────────────────────────────────────────────────────────────────────

def prepared_transactions(case: dict, account_id: str | None = None) -> pd.DataFrame:
    """
    Return the clean transactions with unified `_amount`/`_direction` columns,
    optionally scoped to one account and sorted chronologically.

    Every Phase 3 analytical handler starts from this so the amount/direction
    normalization (and its schema-drift handling) lives in one place.
    """
    df = case["clean"]
    if account_id and "account_number" in df.columns:
        df = df[df["account_number"].astype(str) == str(account_id)]
    df = _with_amount(df)
    if "Date" in df.columns:
        df = df.sort_values("Date", kind="stable")
    return df


def add_counterparty(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add a `_counterparty` column derived heuristically from each row's
    narration (same heuristic as the money-flow graph). Rows with no
    extractable counterparty get None. Approximate by design — callers must
    treat these as inferred external parties, never verified account matches.
    """
    df = df.copy()
    df["_counterparty"] = df.get("Narration", pd.Series(index=df.index, dtype=object)).apply(
        lambda n: extract_counterparty_hint(n)
    )
    return df


def daily_series(df: pd.DataFrame) -> pd.Series:
    """
    Transactions-per-calendar-day as a Series indexed by day, with the gaps
    between active days filled with zeros so mean/std/spike statistics reflect
    real inactivity rather than only the days that happened to have activity.
    """
    dates = df["Date"].dropna() if "Date" in df.columns else pd.Series([], dtype="datetime64[ns]")
    if dates.empty:
        return pd.Series(dtype=float)
    counts = dates.dt.normalize().value_counts().sort_index()
    full_range = pd.date_range(counts.index.min(), counts.index.max(), freq="D")
    return counts.reindex(full_range, fill_value=0)


def period_counts(df: pd.DataFrame, freq: str) -> pd.Series:
    """Transaction counts bucketed by pandas offset alias ('D', 'W', 'ME')."""
    dates = df["Date"].dropna() if "Date" in df.columns else pd.Series([], dtype="datetime64[ns]")
    if dates.empty:
        return pd.Series(dtype=float)
    return dates.dt.to_period(freq).value_counts().sort_index()


def period_amounts(df: pd.DataFrame, freq: str) -> pd.Series:
    """Total amount (debit+credit) bucketed by the same pandas offset alias
    period_counts() uses, for volume-over-time trending alongside count."""
    if "Date" not in df.columns or df.empty:
        return pd.Series(dtype=float)
    df = _with_amount(df).dropna(subset=["Date"])
    if df.empty:
        return pd.Series(dtype=float)
    return df.groupby(df["Date"].dt.to_period(freq))["_amount"].sum().sort_index()


def detect_spikes(series: pd.Series, z: float = SPIKE_Z_THRESHOLD) -> pd.Series:
    """
    Return the subset of a daily-count Series whose values are more than `z`
    standard deviations above the mean — i.e. abnormal bursts of activity.
    Empty Series when there is too little variation to judge.
    """
    if series.empty or series.std(ddof=0) == 0:
        return pd.Series(dtype=float)
    threshold = series.mean() + z * series.std(ddof=0)
    return series[series > threshold]


# ─────────────────────────────────────────────────────────────────────────────
# PER-ACCOUNT ACTIVITY TABLE — the backbone of frequency ranking questions
# ─────────────────────────────────────────────────────────────────────────────

def _holder_for(case: dict, account_id: str, df: pd.DataFrame) -> str:
    """Best-effort account-holder name from the case JSON, else the CSV rows."""
    acct_json = case.get("accounts", {}).get(str(account_id))
    if acct_json:
        holder = acct_json.get("account_details", {}).get("account_holder")
        if holder:
            return str(holder)
    if "account_holder" in df.columns and not df.empty:
        holder = df["account_holder"].dropna()
        if not holder.empty:
            return str(holder.iloc[0])
    return "(unidentified)"


def account_activity_table(case: dict) -> pd.DataFrame:
    """
    One row per account summarising its transaction activity:
    txn_count, active_days, span_days, avg_per_day, max_per_day, std_per_day,
    first_date, last_date, plus the holder name.

    Sorted by txn_count descending so the busiest account is row 0.
    """
    df = _with_amount(case["clean"])
    if "account_number" not in df.columns or df.empty:
        return pd.DataFrame()

    rows = []
    for account_id, group in df.groupby(df["account_number"].astype(str)):
        series = daily_series(group)
        dates = group["Date"].dropna() if "Date" in group.columns else pd.Series([], dtype="datetime64[ns]")
        first_date = dates.min() if not dates.empty else pd.NaT
        last_date = dates.max() if not dates.empty else pd.NaT
        span_days = int((last_date - first_date).days) + 1 if pd.notna(first_date) and pd.notna(last_date) else 0
        rows.append({
            "account": account_id,
            "holder": _holder_for(case, account_id, group),
            "txn_count": int(len(group)),
            "active_days": int((series > 0).sum()),
            "span_days": span_days,
            "avg_per_day": round(float(series.mean()), 3) if not series.empty else 0.0,
            "max_per_day": int(series.max()) if not series.empty else 0,
            "std_per_day": round(float(series.std(ddof=0)), 3) if not series.empty else 0.0,
            "first_date": first_date,
            "last_date": last_date,
        })

    table = pd.DataFrame(rows)
    if not table.empty:
        table = table.sort_values("txn_count", ascending=False).reset_index(drop=True)
    return table


def frequency_metrics(case: dict, account_id: str) -> dict | None:
    """Full frequency metric bundle for a single account (or None if absent)."""
    table = account_activity_table(case)
    if table.empty:
        return None
    match = table[table["account"] == str(account_id)]
    if match.empty:
        return None
    metrics = match.iloc[0].to_dict()

    df = prepared_transactions(case, account_id)
    series = daily_series(df)
    spikes = detect_spikes(series)
    metrics["weekly_counts"] = period_counts(df, "W")
    metrics["monthly_counts"] = period_counts(df, "M")
    metrics["spike_days"] = spikes
    return metrics


def dormant_accounts(case: dict) -> pd.DataFrame:
    """
    Accounts whose last transaction predates the case's most recent
    transaction by more than DORMANT_GAP_DAYS — i.e. inactive relative to the
    rest of the case. Returns the activity-table rows for those accounts.
    """
    table = account_activity_table(case)
    if table.empty or table["last_date"].isna().all():
        return pd.DataFrame()
    case_latest = table["last_date"].max()
    cutoff = case_latest - pd.Timedelta(days=DORMANT_GAP_DAYS)
    dormant = table[table["last_date"] < cutoff]
    return dormant.sort_values("last_date").reset_index(drop=True)


# ─────────────────────────────────────────────────────────────────────────────
# NATURAL-LANGUAGE HANDLER — recognises frequency/activity questions
# ─────────────────────────────────────────────────────────────────────────────

_FREQUENCY_RE = re.compile(
    r"\b(frequency|frequent|busiest|most active|most activity|activity|"
    r"transactions?\s+per\s+(day|week|month)|per\s+day|per\s+week|per\s+month|"
    r"dormant|inactive|spikes?|suddenly (became )?(very )?active|"
    r"unusually frequent|activity trend|frequency ranking|busiest day|busiest month)\b",
    re.IGNORECASE,
)


def matches_frequency_request(question: str) -> bool:
    """True when the question is about transaction frequency / activity levels."""
    return bool(_FREQUENCY_RE.search(question))


def _account_citation(case: dict, account_id: str) -> dict:
    bank = case.get("accounts", {}).get(str(account_id), {}).get("account_details", {}).get("bank_name") or ""
    return {"type": "account_context", "account": str(account_id), "bank_name": bank}


def try_frequency_answer(question: str, case: dict) -> dict | None:
    """
    Deterministic answers for frequency/activity questions (Goal 2 & 5).
    Returns an answer dict, or None to let the next handler try.
    """
    if not matches_frequency_request(question):
        return None

    q = question.lower()
    table = account_activity_table(case)
    if table.empty:
        return None

    # Dormant / inactive accounts ------------------------------------------
    if "dormant" in q or "inactive" in q:
        dormant = dormant_accounts(case)
        if dormant.empty:
            return _wrap(
                "No account is dormant relative to the rest of the case — every "
                f"account has transacted within {DORMANT_GAP_DAYS} days of the "
                "most recent transaction in the dataset.",
                [], "frequency_dormant",
            )
        lines = [
            f"  - {r['holder']} (account {r['account']}): last active "
            f"{r['last_date'].strftime('%d/%m/%Y') if pd.notna(r['last_date']) else '?'}, "
            f"{r['txn_count']} transaction(s) total"
            for _, r in dormant.iterrows()
        ]
        answer = (
            f"{len(dormant)} account(s) are dormant/inactive (no activity within "
            f"{DORMANT_GAP_DAYS} days of the case's latest transaction):\n" + "\n".join(lines)
        )
        citations = [_account_citation(case, r["account"]) for _, r in dormant.iterrows()]
        return _wrap(answer, citations, "frequency_dormant")

    # Busiest day (whole case) ---------------------------------------------
    if "busiest day" in q:
        series = daily_series(_with_amount(case["clean"]))
        if series.empty:
            return None
        peak_day = series.idxmax()
        answer = (
            f"The busiest day across the case was {peak_day.strftime('%d/%m/%Y')} "
            f"with {int(series.max())} transaction(s) recorded that day."
        )
        return _wrap(answer, [], "frequency_busiest_day")

    # Busiest month (whole case) -------------------------------------------
    if "busiest month" in q:
        counts = period_counts(_with_amount(case["clean"]), "M")
        if counts.empty:
            return None
        peak = counts.idxmax()
        answer = (
            f"The busiest month across the case was {peak.strftime('%B %Y')} "
            f"with {int(counts.max())} transaction(s)."
        )
        return _wrap(answer, [], "frequency_busiest_month")

    # Spikes / suddenly active ---------------------------------------------
    if "spike" in q or "suddenly" in q or "unusually frequent" in q:
        flagged = []
        citations = []
        for _, r in table.iterrows():
            metrics = frequency_metrics(case, r["account"])
            spikes = metrics["spike_days"] if metrics else pd.Series(dtype=float)
            if not spikes.empty:
                worst_day = spikes.idxmax()
                flagged.append(
                    f"  - {r['holder']} (account {r['account']}): {len(spikes)} spike day(s); "
                    f"peak {int(spikes.max())} transaction(s) on {worst_day.strftime('%d/%m/%Y')} "
                    f"(daily average {r['avg_per_day']})"
                )
                citations.append(_account_citation(case, r["account"]))
        if not flagged:
            return _wrap(
                "No account shows a statistically abnormal activity spike "
                f"(more than {SPIKE_Z_THRESHOLD:g} standard deviations above its "
                "own daily average).",
                [], "frequency_spikes",
            )
        answer = "Accounts with abnormal activity spikes (Z-score based):\n" + "\n".join(flagged)
        return _wrap(answer, citations, "frequency_spikes")

    # Frequency ranking / busiest account / most active --------------------
    if any(w in q for w in ["busiest", "most active", "most activity", "ranking", "frequency"]):
        top = table.head(10)
        lines = [
            f"  {i}. {r['holder']} (account {r['account']}): {r['txn_count']} transaction(s), "
            f"avg {r['avg_per_day']}/day, peak {r['max_per_day']}/day"
            for i, (_, r) in enumerate(top.iterrows(), start=1)
        ]
        leader = top.iloc[0]
        answer = (
            f"The busiest account is {leader['holder']} (account {leader['account']}) with "
            f"{leader['txn_count']} transaction(s). Frequency ranking:\n" + "\n".join(lines)
        )
        citations = [_account_citation(case, r["account"]) for _, r in top.iterrows()]
        return _wrap(answer, citations, "frequency_ranking")

    # Per-account per-day/week/month metrics -------------------------------
    from chatbot.structured_queries import _resolve_account

    account_id = _resolve_account(question, case)
    if account_id:
        metrics = frequency_metrics(case, account_id)
        if metrics:
            answer = (
                f"Transaction frequency for {metrics['holder']} (account {account_id}):\n"
                f"  - Total transactions: {metrics['txn_count']}\n"
                f"  - Active days: {metrics['active_days']} (over a {metrics['span_days']}-day span)\n"
                f"  - Average per active-to-active day: {metrics['avg_per_day']}\n"
                f"  - Busiest single day: {metrics['max_per_day']} transaction(s)\n"
                f"  - Standard deviation of daily activity: {metrics['std_per_day']}\n"
                f"  - Weeks with activity: {len(metrics['weekly_counts'])}, "
                f"months with activity: {len(metrics['monthly_counts'])}"
            )
            return _wrap(answer, [_account_citation(case, account_id)], "frequency_account")

    return None


def _wrap(answer: str, citations: list[dict], pattern: str) -> dict:
    """Standard frequency-handler result envelope."""
    return {"answer": answer, "citations": citations, "matched_pattern": pattern}
