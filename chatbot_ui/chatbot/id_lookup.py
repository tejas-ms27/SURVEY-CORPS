"""
id_lookup.py
─────────────────────────────────────────────────────────────────────────────
CIDECODE 2026 — Multi-Accused Cross-Account Investigation Engine
Module: Exact-ID / Reference Lookup (advanced-features spec, Section 4)

WHY THIS EXISTS — read Section 0.1 of the spec before touching this.

There is NO structured tax-ID / PAN / GST / reference field anywhere in the
extraction schema. Any specific code/reference/ID an investigator asks about
lives ONLY inside free-text Narration, Reference_Number, or
Transaction_Reference. Neither the structured router (which matches question
SHAPES, not data values) nor semantic search (embedding similarity, not exact
substring matching) reliably finds a row by an exact alphanumeric code typed
into a question.

This module provides the one retrieval mechanism the other two fundamentally
cannot: a literal, case-insensitive substring search across the free-text
columns of every transaction source. It is the most deterministic question
shape there is, so it runs FIRST in the routing order (spec Section 4.3).

Honesty rule (spec 4.3): if a token looks ID-like but is genuinely not in the
data, we say so explicitly rather than letting the question fall through to a
probabilistic path that would return irrelevant chunks and let the LLM guess.
"""

from __future__ import annotations

import re

import pandas as pd

# Columns that can carry a free-text reference an investigator might ask about.
_REFERENCE_COLUMNS = ["Reference_Number", "Transaction_Reference", "Cheque_Number", "Transaction_ID"]


def _known_account_numbers(case: dict) -> set[str]:
    """Account numbers handled by the account-scoped paths, not this one."""
    return {str(acct_id) for acct_id in case.get("accounts", {})}


def looks_like_id_lookup(question: str, case: dict | None = None) -> str | None:
    """
    Detect whether the question contains something that looks like a specific
    ID/reference/code being asked about, and extract it. Returns the extracted
    token, or None if nothing ID-like is present.

    ASSUMPTIONS (stated per spec Section 6):
      1. A token that is exactly a known account number is NOT treated as an ID
         lookup. Account-scoped questions (including aggregation/structured
         questions that merely name an account) are handled more precisely by
         the downstream account-aware paths, so short-circuiting them here on a
         bare account number would route an aggregation question to the wrong
         handler (routing-order check #8).
      2. A candidate must contain at least one digit. Reference codes in this
         project's data are numeric or alphanumeric; this requirement rejects
         long ordinary English words ("transactions", "withdrawal") that would
         otherwise clear an alpha-only length bar and falsely hijack the route.
         Short purely-textual reference fragments are still handled downstream
         by the structured router's identifier_detail_lookup.
    """
    # Long alphanumeric tokens (8+ chars) — the kind of thing that is clearly
    # a reference code, not an ordinary word.
    candidates = re.findall(r"\b[A-Za-z0-9]{8,}\b", question)
    # Require at least one digit (assumption 2 above).
    candidates = [c for c in candidates if any(ch.isdigit() for ch in c)]

    if case is not None:
        known_accounts = _known_account_numbers(case)
        candidates = [c for c in candidates if c not in known_accounts]

    return candidates[0] if candidates else None


def exact_id_lookup(case: dict, token: str) -> dict | None:
    """
    Search Narration, Reference_Number, Transaction_Reference (and related
    free-text columns) across ALL transaction sources (clean, flagged,
    duplicates) for an EXACT case-insensitive substring match of `token`.

    This is a literal substring search — not semantic similarity, not
    question-shape regex matching. Returns None if nothing matches anywhere.
    """
    matches = []
    sources = [
        (case.get("clean"), "clean"),
        (case.get("flagged"), "flagged"),
        (case.get("duplicates"), "duplicate"),
    ]
    pattern = re.escape(token)

    for df, source_label in sources:
        if df is None or df.empty:
            continue
        narration_col = "Narration" if "Narration" in df.columns else "narration"
        mask = pd.Series(False, index=df.index)
        if narration_col in df.columns:
            mask = df[narration_col].astype(str).str.contains(pattern, case=False, na=False)
        for ref_col in _REFERENCE_COLUMNS:
            if ref_col in df.columns:
                mask = mask | df[ref_col].astype(str).str.contains(pattern, case=False, na=False)
        found = df[mask]
        if not found.empty:
            matches.append((source_label, found))

    if not matches:
        return None

    return {
        "token": token,
        "matches": matches,  # list of (source_label, DataFrame) pairs
        "total_count": sum(len(df) for _, df in matches),
    }


def _row_account(row: dict) -> str:
    return str(row.get("account_number") or row.get("Account_ID") or "?")


def _row_date(row: dict) -> str:
    value = row.get("Date", row.get("date"))
    if isinstance(value, pd.Timestamp):
        return value.strftime("%d/%m/%Y") if not pd.isna(value) else "?"
    return str(value) if value not in (None, "") else "?"


def _row_narration(row: dict) -> str:
    return str(row.get("Narration") or row.get("narration") or "")


def _citation_for_row(source_label: str, row: dict) -> dict:
    if source_label == "flagged":
        return {
            "type": "flagged_transaction",
            "account": _row_account(row),
            "date": _row_date(row),
            "flag_reason": str(row.get("flag_reason") or "?"),
        }
    if source_label == "duplicate":
        return {
            "type": "duplicate_transaction",
            "account": _row_account(row),
            "date": _row_date(row),
            "duplicate_row": int(row.get("duplicate_row_number") or 0),
            "original_row": int(row.get("original_row_number") or 0),
        }
    return {
        "type": "transaction",
        "ref": str(row.get("txn_id") or row.get("Transaction_ID") or "?"),
        "account": _row_account(row),
        "date": _row_date(row),
    }


def build_id_lookup_response(result: dict) -> dict:
    """
    Build a deterministic, citation-backed answer from exact_id_lookup output.
    No LLM is involved in the FINDING — the rows are reported directly.
    """
    token = result["token"]
    lines = [
        f"Found {result['total_count']} transaction(s) containing "
        f"'{token}' in a narration or reference field:"
    ]
    citations = []
    for source_label, df in result["matches"]:
        lines.append(f"\nIn {source_label} transactions ({len(df)} match(es)):")
        for _, row in df.head(10).iterrows():
            row_dict = row.to_dict()
            account = _row_account(row_dict)
            date = _row_date(row_dict)
            narration = _row_narration(row_dict)
            debit = pd.to_numeric(row_dict.get("Debit", row_dict.get("debit")), errors="coerce")
            credit = pd.to_numeric(row_dict.get("Credit", row_dict.get("credit")), errors="coerce")
            amount_bits = []
            if pd.notna(debit) and float(debit) > 0:
                amount_bits.append(f"debit ₹{float(debit):,.2f}")
            if pd.notna(credit) and float(credit) > 0:
                amount_bits.append(f"credit ₹{float(credit):,.2f}")
            amount_str = (", ".join(amount_bits) + " — ") if amount_bits else ""
            lines.append(
                f"  - account {account} on {date}: {amount_str}{narration}".rstrip()
            )
            citations.append(_citation_for_row(source_label, row_dict))
        if len(df) > 10:
            lines.append(f"  ... and {len(df) - 10} more match(es).")

    return {
        "answer": "\n".join(lines),
        "citations": citations,
        "matched_pattern": "exact_id_lookup",
    }


def try_id_lookup_answer(question: str, case: dict) -> dict | None:
    """
    Routing entry point for Section 4. Returns an answer dict when the question
    contains an ID-like token, or None when it contains nothing ID-like (so the
    caller proceeds to the next path).

    Crucially, when a token IS ID-like but is not found in the data, this
    returns an explicit "not found" answer rather than None — an honest
    "not found" beats letting a probabilistic fallback guess.
    """
    token = looks_like_id_lookup(question, case)
    if token is None:
        return None

    result = exact_id_lookup(case, token)
    if result is not None:
        return build_id_lookup_response(result)

    return {
        "answer": (
            f"No transaction found containing '{token}' in any narration or "
            f"reference field for this case."
        ),
        "citations": [],
        "matched_pattern": "exact_id_lookup_not_found",
    }
