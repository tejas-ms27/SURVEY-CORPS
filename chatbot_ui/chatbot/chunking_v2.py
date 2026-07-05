"""
chunking_v2.py
─────────────────────────────────────────────────────────────────────────────
CIDECODE 2026 — Multi-Accused Cross-Account Investigation Engine
Module: Text Chunking for RAG Ingestion (v2 — real extraction schema)

Replaces chunking.py's transaction handling to match the ACTUAL extraction
pipeline output (clean_transactions.csv / flagged_transactions.csv /
duplicates.csv / per-account JSON), instead of the simplified mock schema.

Four chunk types are produced:
  1. clean transaction      -> chunk_type = "transaction"
  2. flagged transaction    -> chunk_type = "flagged_transaction"
                                (carries WHY it was flagged — flag_reason)
  3. duplicate transaction  -> chunk_type = "duplicate_transaction"
                                (carries WHY it was flagged as a dupe, and
                                 which original row it duplicates)
  4. account context        -> chunk_type = "account_context"
                                (one chunk per account: bank, branch,
                                 statement period, opening/closing balance —
                                 lets investigators ask account-level
                                 questions like "which bank is this account
                                 with" or "what period does this cover")

Fraud-pattern chunking (chunk_type = "fraud_pattern") is unchanged from the
original chunking.py — kept in pattern_to_chunk() below for continuity,
ready the moment the NetworkX module produces real output.
"""

import pandas as pd


def _is_missing(value) -> bool:
    if value is None:
        return True
    try:
        if pd.isna(value):
            return True
    except (TypeError, ValueError):
        pass
    return isinstance(value, str) and value.strip() == ""


def _fmt_field_value(value) -> str:
    if _is_missing(value):
        return "not extracted"
    if isinstance(value, pd.Timestamp):
        return value.strftime("%d/%m/%Y") if not pd.isna(value) else "not extracted"
    return str(value)


def _format_all_fields(fields: dict) -> str:
    return "; ".join(f"{key}: {_fmt_field_value(value)}" for key, value in fields.items())


def _fmt_amount(value) -> str:
    try:
        return f"₹{float(value):,.2f}"
    except (TypeError, ValueError):
        return "an unspecified amount"


def _fmt_date(value) -> str:
    if pd.isna(value):
        return "an unknown date"
    if isinstance(value, str):
        return value
    return value.strftime("%d/%m/%Y")


def _direction_and_amount(row: pd.Series) -> tuple[str, str, float]:
    """
    Return (direction phrase, transaction_type, amount).

    Older chatbot fixtures include Transaction_Type. Newer extraction outputs
    may only have Debit/Credit, so infer direction from whichever amount is
    non-zero.
    """
    txn_type = str(row.get("Transaction_Type") or "").strip().lower()
    debit = pd.to_numeric(row.get("Debit", 0), errors="coerce")
    credit = pd.to_numeric(row.get("Credit", 0), errors="coerce")
    debit = 0.0 if pd.isna(debit) else float(debit)
    credit = 0.0 if pd.isna(credit) else float(credit)

    if txn_type not in ("debit", "credit"):
        txn_type = "debit" if debit > 0 else "credit"

    if txn_type == "debit":
        return "debited from", "debit", debit
    return "credited to", "credit", credit


# ─────────────────────────────────────────────────────────────────────────────
# 1. CLEAN TRANSACTIONS  (from clean_transactions.csv)
# ─────────────────────────────────────────────────────────────────────────────

def clean_transaction_to_chunk(row: pd.Series) -> dict:
    """
    Converts one row of clean_transactions.csv into a chunk.
    Handles the real column names: account_number, Date, Narration, Debit,
    Credit, Balance, Transaction_Type, Bank_Name, txn_id, is_reversed.
    """
    direction, txn_type, amount = _direction_and_amount(row)
    date_str = _fmt_date(row["Date"])
    reversed_note = " This transaction was later reversed." if row.get("is_reversed") else ""

    all_fields = _format_all_fields(row.to_dict())
    text = (
        f"On {date_str}, {_fmt_amount(amount)} was {direction} account "
        f"{row['account_number']} at {row['Bank_Name']}. "
        f"Narration: {row['Narration']}. Resulting balance: {_fmt_amount(row['Balance'])}."
        f"{reversed_note} "
        f"All extracted transaction fields: {all_fields}."
    )

    metadata = {
        "chunk_type": "transaction",
        "txn_id": str(row["txn_id"]),
        "account_id": str(row["account_number"]),
        "bank_name": str(row["Bank_Name"]),
        "date": date_str,
        "amount": float(amount) if pd.notna(amount) else 0.0,
        "direction": txn_type,
        "is_reversed": bool(row.get("is_reversed", False)),
    }

    return {"id": f"txn-{row['txn_id']}", "text": text, "metadata": metadata}


def clean_transactions_to_chunks(df: pd.DataFrame) -> list[dict]:
    return [clean_transaction_to_chunk(row) for _, row in df.iterrows()]


# ─────────────────────────────────────────────────────────────────────────────
# 2. FLAGGED TRANSACTIONS  (from flagged_transactions.csv)
# ─────────────────────────────────────────────────────────────────────────────

def flagged_transaction_to_chunk(row: pd.Series) -> dict:
    """
    Converts one row of flagged_transactions.csv into a chunk.
    The flag_reason is the key piece of information here — investigators
    will directly ask "why was this transaction flagged?", so it must be
    prominent in the chunk TEXT, not just stored as metadata.
    """
    direction, txn_type, amount = _direction_and_amount(row)
    date_str = _fmt_date(row["Date"])

    all_fields = _format_all_fields(row.to_dict())
    text = (
        f"FLAGGED TRANSACTION (reason: {row['flag_reason']}). "
        f"On {date_str}, {_fmt_amount(amount)} was {direction} account "
        f"{row['Account_ID']} at {row['Bank_Name']}. "
        f"Narration: {row['Narration']}. Resulting balance: {_fmt_amount(row['Balance'])}. "
        f"This was flagged during extraction due to: {row['flag_reason']}. "
        f"All extracted flagged-transaction fields: {all_fields}."
    )

    metadata = {
        "chunk_type": "flagged_transaction",
        "account_id": str(row["Account_ID"]),
        "bank_name": str(row["Bank_Name"]),
        "date": date_str,
        "amount": float(amount) if pd.notna(amount) else 0.0,
        "direction": txn_type,
        "flag_reason": str(row["flag_reason"]),
    }

    # Use the row's position as a stable-enough id component since
    # flagged rows don't always carry a clean txn_id
    row_id = row.name if row.name is not None else id(row)
    return {"id": f"flagged-{row['Account_ID']}-{row_id}", "text": text, "metadata": metadata}


def flagged_transactions_to_chunks(df: pd.DataFrame) -> list[dict]:
    return [flagged_transaction_to_chunk(row) for _, row in df.iterrows()]


# ─────────────────────────────────────────────────────────────────────────────
# 3. DUPLICATE TRANSACTIONS  (from duplicates.csv)
# ─────────────────────────────────────────────────────────────────────────────

def duplicate_transaction_to_chunk(row: pd.Series) -> dict:
    """
    Converts one row of duplicates.csv into a chunk. Lets investigators
    ask things like "were any transactions removed as duplicates?" and
    get a grounded answer pointing at the specific rows involved.
    """
    date_str = _fmt_date(row["date"])

    all_fields = _format_all_fields(row.to_dict())
    text = (
        f"DUPLICATE TRANSACTION removed during extraction (reason: "
        f"{row['reason_flagged']}). On {date_str}, account {row['account_number']} "
        f"had a duplicate entry of {_fmt_amount(row['amount'])} "
        f"(narration: {row['narration']}). This duplicate (row "
        f"{row['duplicate_row_number']}) matches original row "
        f"{row['original_row_number']}. "
        f"All extracted duplicate-row fields: {all_fields}."
    )

    metadata = {
        "chunk_type": "duplicate_transaction",
        "account_id": str(row["account_number"]),
        "date": date_str,
        "amount": float(row["amount"]) if pd.notna(row["amount"]) else 0.0,
        "reason_flagged": str(row["reason_flagged"]),
        "duplicate_row_number": int(row["duplicate_row_number"]),
        "original_row_number": int(row["original_row_number"]),
    }

    return {
        "id": f"dup-{row['account_number']}-{row['duplicate_row_number']}",
        "text": text,
        "metadata": metadata,
    }


def duplicates_to_chunks(df: pd.DataFrame) -> list[dict]:
    return [duplicate_transaction_to_chunk(row) for _, row in df.iterrows()]


# ─────────────────────────────────────────────────────────────────────────────
# 4. ACCOUNT CONTEXT  (one chunk per account, from per-account JSON files)
# ─────────────────────────────────────────────────────────────────────────────

def account_to_chunk(account_json: dict) -> dict:
    """
    Converts one account's metadata (account_details block of a per-account
    JSON file) into a single context chunk. This lets investigators ask
    account-level questions ("what bank is ACC X with", "what period does
    this statement cover", "who is the nominee") without needing to dig
    through individual transactions.

    NOTE: across different banks, the multi-tier extraction (cheap_parse /
    schema_reparse / llm_full_read) does not always recover every field —
    some come back as an empty string rather than being absent entirely
    (e.g. opening_balance, bank_name, ifsc_code, account_holder). We
    distinguish "field not extracted" from "field is genuinely zero/empty"
    explicitly in the chunk text, so the chatbot never implies a balance of
    ₹0.00 when the real situation is "this bank's statement didn't expose
    that field to the parser."
    """
    d = account_json["account_details"]
    holder = d.get("account_holder") or "an unidentified account holder"
    nominee = d.get("nominee_name")
    nominee_clause = f" Nominee on record: {nominee}." if nominee else ""

    opening = d.get("opening_balance")
    opening_str = _fmt_amount(opening) if opening not in (None, "") else "not extracted"
    closing = d.get("closing_balance")
    closing_str = _fmt_amount(closing) if closing not in (None, "") else "not extracted"

    all_fields = _format_all_fields(d)
    text = (
        f"Account {d['account_number']} is held by {holder} at "
        f"{d.get('bank_name') or 'an unidentified bank'}"
        f"{', branch ' + d['branch'] if d.get('branch') else ''}. "
        f"Account type: {d.get('account_type') or 'not specified'}. "
        f"Statement period: {d.get('statement_period') or 'unknown'}. "
        f"Opening balance: {opening_str}, closing balance: {closing_str}."
        f"{nominee_clause} "
        f"This account has {account_json.get('transaction_count', 'an unknown number of')} "
        f"recorded transactions in this case. "
        f"All extracted account fields: {all_fields}."
    )

    metadata = {
        "chunk_type": "account_context",
        "account_id": str(d["account_number"]),
        "bank_name": str(d.get("bank_name") or "Unidentified Bank"),
        "account_holder": str(holder),
        "statement_period": str(d.get("statement_period") or ""),
    }

    return {"id": f"account-{d['account_number']}", "text": text, "metadata": metadata}


def accounts_to_chunks(accounts: dict[str, dict]) -> list[dict]:
    return [account_to_chunk(acct_json) for acct_json in accounts.values()]


# ─────────────────────────────────────────────────────────────────────────────
# 5. FRAUD PATTERNS  (unchanged contract — ready for when NetworkX output lands)
# ─────────────────────────────────────────────────────────────────────────────

def pattern_to_chunk(pattern: dict) -> dict:
    text = (
        f"FRAUD PATTERN [{pattern['pattern_type'].upper()}] "
        f"(severity: {pattern['severity']}). "
        f"Accounts involved: {', '.join(pattern['accused_accounts'])}. "
        f"Amount involved: {_fmt_amount(pattern['amount_involved'])}. "
        f"Date range: {pattern['date_range'][0]} to {pattern['date_range'][1]}. "
        f"Details: {pattern['summary']}"
    )
    metadata = {
        "chunk_type": "fraud_pattern",
        "pattern_id": pattern["pattern_id"],
        "pattern_type": pattern["pattern_type"],
        "severity": pattern["severity"],
        "amount_involved": float(pattern["amount_involved"]),
        "accused_accounts": ",".join(pattern["accused_accounts"]),
        "involved_transactions": ",".join(pattern["involved_transactions"]),
    }
    return {"id": f"pattern-{pattern['pattern_id']}", "text": text, "metadata": metadata}


def patterns_to_chunks(patterns: list[dict]) -> list[dict]:
    return [pattern_to_chunk(p) for p in patterns]


# ─────────────────────────────────────────────────────────────────────────────
# 6. CONVENIENCE — chunk an entire loaded case in one call
# ─────────────────────────────────────────────────────────────────────────────

def case_to_chunks(case: dict) -> list[dict]:
    """
    Takes the dict returned by data_loader.load_full_case() and returns
    every chunk across all four (or five, once fraud patterns exist) types,
    ready for ingest_chunks().
    """
    chunks = []
    chunks += clean_transactions_to_chunks(case["clean"])
    chunks += flagged_transactions_to_chunks(case["flagged"])
    chunks += duplicates_to_chunks(case["duplicates"])
    chunks += accounts_to_chunks(case["accounts"])
    chunks += patterns_to_chunks(case["fraud_patterns"])
    return chunks
