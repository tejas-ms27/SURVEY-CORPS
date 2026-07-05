"""
counterparty.py
─────────────────────────────────────────────────────────────────────────────
CIDECODE 2026 — Multi-Accused Cross-Account Investigation Engine
Module: Shared counterparty / direction heuristics

WHY THIS MODULE EXISTS — single source of truth for two heuristics.

`extract_counterparty_hint()` and `infer_direction_amount()` were originally
defined inside app.py (the Streamlit dashboard). The in-chat transaction
network graph (Section 1 of the advanced-features spec) needs the EXACT same
counterparty heuristic — the spec is explicit that it must be REUSED, not
re-implemented as a second, slightly-divergent version, so that the same
data limitation and the same honesty/labeling discipline apply in both
places.

app.py cannot be imported from the chatbot package without side effects
(it calls st.set_page_config() at import time), so the shared logic lives
here instead. Both app.py and chatbot.graph_viz import from this module —
there is only ever one definition of each heuristic.
"""

from __future__ import annotations

import re

import pandas as pd


def infer_direction_amount(row: pd.Series) -> tuple[str, float]:
    """
    Resolve a transaction row to (direction, amount).

    Prefers the explicit Transaction_Type column when it is "debit"/"credit";
    otherwise infers direction from whichever of Debit/Credit is populated.
    """
    txn_type = str(row.get("Transaction_Type") or "").strip().lower()
    debit = pd.to_numeric(row.get("Debit", 0), errors="coerce")
    credit = pd.to_numeric(row.get("Credit", 0), errors="coerce")
    debit = 0.0 if pd.isna(debit) else float(debit)
    credit = 0.0 if pd.isna(credit) else float(credit)
    if txn_type not in ("debit", "credit"):
        txn_type = "debit" if debit > 0 else "credit"
    return txn_type, debit if txn_type == "debit" else credit


def extract_counterparty_hint(narration: str) -> str | None:
    """
    Heuristically pull a likely counterparty name out of free-text narration.

    APPROXIMATE BY DESIGN — there is no structured counterparty/account column
    in the extraction schema, so this strips bank/transfer/reference tokens
    and keeps what looks like a name. Returns None when nothing name-like
    survives. Callers MUST label nodes/edges derived from this as heuristic,
    never as verified counterparties.
    """
    text = str(narration or "").upper()
    if not text or text == "NAN":
        return None
    text = re.sub(r"\b(NEFT|RTGS|IMPS|UPI|NACH|ACH|INB|MB|ATM|POS|TRANSFER|TRF)\b", " ", text)
    text = re.sub(r"\b[A-Z]{4}0[A-Z0-9]{6}\b", " ", text)
    text = re.sub(r"\b[A-Z]{2,}\d{5,}\b", " ", text)
    text = re.sub(r"\b\d{4,}\b", " ", text)
    text = re.sub(r"\b(DR|CR|REF|TXN|ID|NO|CELL|BANK|PAYMENT|CHARGE|GST|EMI|CASH|WITHDRAWAL|DEPOSIT)\b", " ", text)
    text = re.sub(r"[^A-Z .&-]", " ", text)
    text = re.sub(r"\s+", " ", text).strip(" .-&")
    bad_tokens = {"IPAY", "ESHP", "SBIEPAY", "CNRB", "HDFC", "ICICI", "IDIB", "BARB", "MAHB"}
    parts = [part for part in text.split() if part not in bad_tokens and len(part) > 1]
    cleaned = " ".join(parts[:5]).strip()
    alpha_count = sum(char.isalpha() for char in cleaned)
    if "/" in cleaned or alpha_count < 3:
        return None
    if alpha_count < max(3, len(cleaned.replace(" ", "")) * 0.45):
        return None
    return cleaned.title()
