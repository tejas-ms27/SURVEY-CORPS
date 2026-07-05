"""
structuring.py
─────────────────────────────────────────────────────────────────────────────
CIDECODE 2026 — Multi-Accused Cross-Account Investigation Engine
Module: Structuring / Smurfing Detection (advanced-features spec, Section 3)

WHAT THIS DETECTS: launderers sometimes split a large transfer into several
smaller transactions each just under a reporting threshold (e.g. repeatedly
moving amounts just below ₹50,000), often in quick succession. This is a
temporal/amount heuristic that runs directly against clean_transactions.csv —
no dependency on the not-yet-built NetworkX fraud module.

TIME-PRECISION HONESTY (spec 3.2): real bank data does not reliably carry a
Time field. When Time is missing for any transaction in a candidate cluster,
we fall back to same-DAY grouping and mark time_precision="day" so the UI can
present day-level matches with less certainty than minute-level matches.

HONESTY CAVEAT IS MANDATORY (spec 3.3): the alert text must state plainly that
this is a heuristic flag, not a confirmed finding. Same principle as the
heuristic graph nodes — a pattern surfaces something worth investigating, it
is not itself proof, and the UI language must not overstate that.
"""

from __future__ import annotations

import pandas as pd


def _row_timestamp(date_value, time_value):
    """Combine a Date and an "HH:MM" Time string into a Timestamp, or NaT."""
    if pd.isna(date_value):
        return pd.NaT
    time_str = str(time_value).strip()
    if not time_str or time_str.lower() == "nan":
        return pd.Timestamp(date_value)
    parsed = pd.to_datetime(f"{pd.Timestamp(date_value).date()} {time_str}", errors="coerce")
    return parsed if pd.notna(parsed) else pd.Timestamp(date_value)


def _cluster_by_proximity(near_threshold: pd.DataFrame, time_window_minutes: int) -> list[pd.DataFrame]:
    """
    Group near-threshold rows into proximity clusters.

    If EVERY row in the candidate set carries a usable Time, cluster by a true
    rolling time window (consecutive rows within `time_window_minutes`).
    Otherwise fall back to same-Date grouping — minute-level precision is not
    trustworthy when any Time is missing.
    """
    if near_threshold.empty:
        return []

    rows = near_threshold.copy()
    all_have_time = bool(rows["has_time"].all())

    if all_have_time:
        rows["_ts"] = [
            _row_timestamp(d, t) for d, t in zip(rows["Date"], rows["Time"])
        ]
        rows = rows.sort_values("_ts")
        clusters = []
        current = [rows.iloc[0]]
        for i in range(1, len(rows)):
            gap = rows.iloc[i]["_ts"] - current[-1]["_ts"]
            if gap <= pd.Timedelta(minutes=time_window_minutes):
                current.append(rows.iloc[i])
            else:
                clusters.append(pd.DataFrame(current))
                current = [rows.iloc[i]]
        clusters.append(pd.DataFrame(current))
        return [c.drop(columns=["_ts"], errors="ignore") for c in clusters]

    # Day-level fallback — one cluster per calendar day.
    rows = rows.sort_values("Date")
    return [group for _, group in rows.groupby(rows["Date"].dt.date)]


def detect_structuring_patterns(case: dict, threshold: float = 50000,
                                proximity_tolerance: float = 0.1,
                                time_window_minutes: int = 30,
                                min_transactions: int = 3) -> list[dict]:
    """
    Flag clusters of same-account transactions, close in time, each
    individually just under `threshold`, that collectively suggest deliberate
    structuring to avoid a reporting threshold.

    proximity_tolerance: how close to the threshold counts as suspicious
    (0.1 = within 10% below threshold, i.e. ₹45,000-₹49,999 for ₹50,000).
    """
    clean = case.get("clean")
    if clean is None or clean.empty or "account_number" not in clean.columns:
        return []

    df = clean.copy()
    if "Time" in df.columns:
        df["has_time"] = df["Time"].notna() & (df["Time"].astype(str).str.strip() != "")
    else:
        df["has_time"] = False

    debit = pd.to_numeric(df.get("Debit"), errors="coerce").fillna(0.0)
    credit = pd.to_numeric(df.get("Credit"), errors="coerce").fillna(0.0)
    df["_debit"] = debit
    df["_credit"] = credit

    lower = threshold * (1 - proximity_tolerance)
    flagged_clusters = []

    for account_id, group in df.groupby("account_number"):
        near_threshold = group[
            ((group["_debit"] >= lower) & (group["_debit"] < threshold)) |
            ((group["_credit"] >= lower) & (group["_credit"] < threshold))
        ].sort_values("Date")

        if len(near_threshold) < min_transactions:
            continue

        for cluster in _cluster_by_proximity(near_threshold, time_window_minutes):
            if len(cluster) < min_transactions:
                continue
            txns = []
            for _, row in cluster.iterrows():
                date = row.get("Date")
                txns.append({
                    "txn_id": row.get("txn_id"),
                    "Date": date.strftime("%d/%m/%Y") if isinstance(date, pd.Timestamp) and pd.notna(date) else str(date),
                    "Narration": row.get("Narration"),
                    "Debit": float(row.get("_debit", 0.0)),
                    "Credit": float(row.get("_credit", 0.0)),
                })
            flagged_clusters.append({
                "account_id": str(account_id),
                "transaction_count": len(cluster),
                "total_amount": float(cluster["_debit"].sum() + cluster["_credit"].sum()),
                "threshold_used": threshold,
                "time_precision": "minute" if bool(cluster["has_time"].all()) else "day",
                "transactions": txns,
            })

    return flagged_clusters


def structuring_results_by_account(case: dict, **kwargs) -> dict[str, list[dict]]:
    """
    Run detection once and index the clusters by account_id, for the
    case-load-time caching described in spec 3.3.
    """
    by_account: dict[str, list[dict]] = {}
    for cluster in detect_structuring_patterns(case, **kwargs):
        by_account.setdefault(cluster["account_id"], []).append(cluster)
    return by_account


def format_structuring_alert(cluster: dict) -> str:
    """
    Mandatory-caveat alert text (spec 3.3). Do NOT strip the honesty caveat —
    a heuristic flag is not a confirmed finding.
    """
    when = "within the same hour" if cluster["time_precision"] == "minute" else "on the same day"
    return (
        f"⚠️ **Possible structuring detected** — account {cluster['account_id']} has "
        f"{cluster['transaction_count']} transactions totaling "
        f"₹{cluster['total_amount']:,.2f}, each individually just under the "
        f"₹{cluster['threshold_used']:,.0f} threshold, clustered {when}. "
        f"This pattern is consistent with deliberate structuring to avoid "
        f"reporting requirements, but is a heuristic flag, not a confirmed finding — "
        f"investigate the underlying transactions before treating this as conclusive."
    )
