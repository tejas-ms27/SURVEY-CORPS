"""display_schema.py — capture each account's ORIGINAL statement column layout.

The extraction pipeline normalises every statement to one internal schema
(Date/Narration/Debit/Credit/…). For investigator-facing exports — e.g. the Money
Trail → Word download — we must instead reproduce the ORIGINAL statement's column
NAMES and ORDER. This module derives that "display schema" from what extraction
already holds in memory (the Excel/CSV header, or the digital-PDF text header line),
so it adds NO extra file reads and NO delay.

A display schema is an ordered list of columns:
    [{"name": "<original header text>", "field": "<internal field it maps to>"}]
`field` is the internal transaction field the exporter reads to fill each cell:
Date | Time | Date_Time | Narration | Debit | Credit | Balance | Cheque_Number |
Transaction_Reference | Amount | ref_or_cheque | "" (unknown → blank cell).

Fully generic and bank-agnostic: driven only by generic banking column vocabulary,
never a bank name or a per-format template.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

import pandas as pd

# Helper columns the pipeline appends to Excel/CSV frames — never part of the
# statement's own visible layout, so they are excluded from the display schema.
_NON_DISPLAY_COLUMNS = {"account_id", "bank_name", "source_account_id",
                        "account_number", "account_holder", "ifsc_code"}


def _classify_column_field(name: str) -> str:
    """Map an ORIGINAL column name to the internal field the exporter fills it from.

    Priority order matters: a "Value Date" / "Transaction Date" must resolve to a DATE
    (not to Narration via the word 'transaction'), so date is tested before narration."""
    s = (name or "").strip().lower()
    if not s:
        return ""
    if "balance" in s:
        return "Balance"
    has_cheque = "cheque" in s or "chq" in s
    has_ref = "ref" in s or "utr" in s
    if has_cheque and has_ref:
        return "ref_or_cheque"
    if has_cheque:
        return "Cheque_Number"
    if any(w in s for w in ("withdraw", "debit", "paid out")) or s == "dr":
        return "Debit"
    if any(w in s for w in ("deposit", "credit", "paid in")) or s == "cr":
        return "Credit"
    # A date column: the word "date" or the common abbreviation "dt" (txn dt / value dt).
    has_date = ("date" in s) or bool(re.search(r"\bdt\b", s))
    if has_date and "time" in s:
        return "Date_Time"
    if has_date:
        return "Date"
    if s == "time":
        return "Time"
    if any(w in s for w in ("narrat", "descript", "particular", "remark", "detail")):
        return "Narration"
    if has_ref or "transaction id" in s or "txn id" in s:
        return "Transaction_Reference"
    if "amount" in s or s == "amt":
        return "Amount"
    return ""


# Generic column-name phrases used to SEGMENT a single-space PDF header line into
# columns (longest first so multi-word names win). Generic banking vocabulary only.
_HEADER_PHRASES = sorted(
    [
        "trans date and time", "transaction date and time", "date and time",
        "transaction date", "value date", "posting date", "tran date", "txn date",
        "gl date", "date",
        "transaction details", "transaction remarks", "transaction particulars",
        "description", "narration", "particulars", "remarks", "details",
        "ref/cheque no", "ref / cheque no", "cheque no.", "cheque no",
        "cheque number", "chq no", "cheque", "reference no", "reference number",
        "ref no", "reference", "utr",
        "withdrawal amount", "withdrawal amt", "withdrawals", "withdrawal",
        "debit amount", "debit amt", "debit",
        "deposit amount", "deposit amt", "deposits", "deposit",
        "credit amount", "credit amt", "credit",
        "closing balance", "running balance", "balance", "amount", "time",
    ],
    key=len,
    reverse=True,
)
_HEADER_PHRASE_RE = re.compile("|".join(re.escape(p) for p in _HEADER_PHRASES), re.IGNORECASE)

# A header line: mentions a date AND at least one money/description column word, and
# carries no actual amount VALUE (so a data row is never mistaken for the header).
_DATE_WORD = re.compile(r"\bdate\b", re.IGNORECASE)
_MONEY_WORD = re.compile(
    r"debit|credit|withdraw|deposit|balance|narrat|descript|particular|amount",
    re.IGNORECASE)
_AMOUNT_VALUE = re.compile(r"\d[\d,]*\.\d{2}\b")


def _columns_from_names(names: List[str]) -> List[Dict[str, str]]:
    """Turn ordered original column names into schema entries, dropping empty ones."""
    out: List[Dict[str, str]] = []
    for nm in names:
        nm = (nm or "").strip()
        if not nm:
            continue
        out.append({"name": nm, "field": _classify_column_field(nm)})
    return out


def _schema_from_header_line(line: str) -> List[Dict[str, str]]:
    """Parse one header line into ordered columns. Tries a two-or-more-space split
    first (clean for table-extracted PDFs), then a generic phrase segmentation."""
    # Table-extracted headers separate cells with 2+ spaces → verbatim, best fidelity.
    parts = [p.strip() for p in re.split(r"\s{2,}", line.strip()) if p.strip()]
    if len(parts) >= 3:
        cols = _columns_from_names(parts)
        if sum(1 for c in cols if c["field"]) >= 3:
            return cols
    # Single-space flat header → segment by known column phrases (original text kept).
    matches = [m.group(0).strip() for m in _HEADER_PHRASE_RE.finditer(line)]
    cols = _columns_from_names(matches)
    if sum(1 for c in cols if c["field"]) >= 3:
        return cols
    return []


def _synthetic_schema(has_time: bool, has_balance: bool) -> List[Dict[str, str]]:
    """Last-resort generic layout when no header could be recovered. Uses neutral
    display names so the export is still usable on any statement."""
    cols = [{"name": "Date", "field": "Date"}]
    if has_time:
        cols.append({"name": "Time", "field": "Time"})
    cols.append({"name": "Narration", "field": "Narration"})
    cols.append({"name": "Debit", "field": "Debit"})
    cols.append({"name": "Credit", "field": "Credit"})
    if has_balance:
        cols.append({"name": "Balance", "field": "Balance"})
    return cols


def build_display_schema(
    route: str,
    raw_df: Optional[pd.DataFrame] = None,
    raw_text: str = "",
    has_time: bool = False,
    has_balance: bool = True,
) -> Dict[str, Any]:
    """Derive the account's display schema from in-memory extraction artefacts.

    Excel/CSV → the sheet's own header (verbatim). PDF/DOCX/text → the header line in
    the already-extracted text. Falls back to a generic synthetic layout so a schema
    is ALWAYS produced. Returns {"columns": [...], "source": "<how it was derived>"}.
    """
    # Excel / CSV: the frame's own column names ARE the original layout.
    if raw_df is not None and getattr(raw_df, "columns", None) is not None and len(raw_df.columns):
        names = [str(c) for c in raw_df.columns if str(c).strip().lower() not in _NON_DISPLAY_COLUMNS]
        cols = _columns_from_names(names)
        if sum(1 for c in cols if c["field"]) >= 2:
            return {"columns": cols, "source": "excel_header"}

    # Text sources (digital PDF / DOCX / txt): find the header line and parse it.
    for line in (raw_text or "").splitlines()[:60]:
        s = line.strip()
        if not s or not _DATE_WORD.search(s) or not _MONEY_WORD.search(s):
            continue
        if _AMOUNT_VALUE.search(s):
            continue  # a data row, not the header
        cols = _schema_from_header_line(s)
        if cols:
            return {"columns": cols, "source": "pdf_text_header"}

    return {"columns": _synthetic_schema(has_time, has_balance), "source": "synthetic"}
