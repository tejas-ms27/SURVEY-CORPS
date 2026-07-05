"""
structured_queries.py
─────────────────────────────────────────────────────────────────────────────
CIDECODE 2026 — Multi-Accused Cross-Account Investigation Engine
Module: Structured Query Router

WHY THIS EXISTS — read before touching the regex patterns below.

Pure semantic (vector) search is the wrong tool for an entire class of
investigator questions: "list every X", "how many Y are there", "what is
field Z for account W". These questions have ONE correct, fully-determined
answer that already exists in the loaded data — there is nothing for an
LLM to "find" via similarity, because similarity search ranks chunks by how
close their TEXT is to the question's wording, not by whether they contain
the complete, correct answer.

This was observed directly: asking "list all account holder names" against
a 6-account case retrieved five near-irrelevant transaction chunks (all
with NEGATIVE relevance scores, meaning none of them were good matches) and
the LLM picked one stray name it noticed in narration text — presenting it
as the only account holder, when 6 real, correct names were sitting in
account-context data the whole time. Same failure mode hit "why was this
flagged" (real flag_reason text was never retrieved) and "closing balance
of all accounts" (mixed correct account-level data with incorrect
transaction-level Balance fields for the same account in one answer).

THE FIX: before calling ask() / doing any embedding-based retrieval, check
if the question matches a known STRUCTURED pattern below. If it does,
answer it directly from the in-memory `case` dict (the same dict returned
by data_loader.load_full_case()) — deterministic, zero hallucination risk,
and complete by construction. Semantic search remains the fallback for
genuinely open-ended/exploratory questions where no single structured
answer exists.

This module does NOT call the LLM at all for matched patterns — answers
are built with plain Python string formatting from real data. This is a
deliberate choice: a deterministic answer needs no LLM in the loop, and
skipping that loop also means matched questions answer instantly.
"""

import re

import pandas as pd


_IDENTIFIER_WORD_RE = re.compile(
    r"\b("
    r"id|identifier|details?|full|complete|everything|a\s*to\s*z|"
    r"tax|taxation|gst|gstin|pan|tin|ifsc|ckyc|customer|account|"
    r"transaction|txn|reference|ref|cheque"
    r")\b",
    re.IGNORECASE,
)
_IDENTIFIER_TOKEN_RE = re.compile(r"\b[A-Za-z0-9][A-Za-z0-9_@./:-]{4,}[A-Za-z0-9]\b")
_DATE_TOKEN_RE = re.compile(r"\d{1,2}[/-]\d{1,2}[/-]\d{2,4}")
_COMMON_NON_IDENTIFIER_TOKENS = {
    "about",
    "account",
    "branch",
    "cheque",
    "complete",
    "customer",
    "dataset",
    "detail",
    "details",
    "everything",
    "identifier",
    "reference",
    "taxation",
    "transaction",
}
_TAX_IDENTIFIER_FIELDS = {
    "branch_gstin",
    "gstin",
    "gst_number",
    "pan",
    "pan_number",
    "tin",
    "tax_id",
    "taxation_id",
}


def _is_missing(value) -> bool:
    if value is None:
        return True
    try:
        if pd.isna(value):
            return True
    except (TypeError, ValueError):
        pass
    return isinstance(value, str) and value.strip() == ""


def _format_value(value) -> str:
    if _is_missing(value):
        return "not extracted"
    if isinstance(value, pd.Timestamp):
        return value.strftime("%d/%m/%Y") if not pd.isna(value) else "not extracted"
    return str(value)


def _format_field_block(fields: dict, indent: str = "  - ") -> str:
    if not fields:
        return f"{indent}(no fields present)"
    return "\n".join(f"{indent}{key}: {_format_value(value)}" for key, value in fields.items())


def _flatten_mapping(value, prefix: str = "") -> dict:
    if isinstance(value, dict):
        flattened = {}
        for key, child in value.items():
            child_prefix = f"{prefix}.{key}" if prefix else str(key)
            flattened.update(_flatten_mapping(child, child_prefix))
        return flattened
    if isinstance(value, list):
        return {prefix: f"{len(value)} item(s)"}
    return {prefix: value}


def _contains_identifier(value, candidate: str) -> bool:
    if _is_missing(value):
        return False
    return candidate.lower() in str(value).lower()


def _row_matches_candidate(row: pd.Series, candidate: str) -> bool:
    return any(_contains_identifier(value, candidate) for value in row.to_dict().values())


def _mapping_matches_candidate(mapping: dict, candidate: str) -> bool:
    return any(_contains_identifier(value, candidate) for value in _flatten_mapping(mapping).values())


def _extract_identifier_candidates(question: str) -> list[str]:
    candidates = []
    for raw in _IDENTIFIER_TOKEN_RE.findall(question):
        token = raw.strip(".,;:()[]{}<>\"'")
        if _DATE_TOKEN_RE.fullmatch(token):
            continue  # a bare date is never an identifier/reference code
        token_lower = token.lower()
        if token_lower in _COMMON_NON_IDENTIFIER_TOKENS:
            continue
        if not any(ch.isdigit() for ch in token) and not any(ch in token for ch in "_@/:-"):
            continue
        if token not in candidates:
            candidates.append(token)
    return candidates


def _account_file_metadata(case: dict, account_id: str) -> dict | None:
    for file_record in case.get("run_metadata", {}).get("files", []):
        account_details = file_record.get("account_details", {})
        account_ref = str(file_record.get("account_ref") or "")
        account_number = str(account_details.get("account_number") or "")
        if account_id in {account_ref, account_number}:
            return _flatten_mapping({
                key: value
                for key, value in file_record.items()
                if key != "account_details"
            })
    return None


def _tax_identifier_answer(case: dict) -> dict | None:
    rows = []
    citations = []
    for acct_id, acct_json in case["accounts"].items():
        details = acct_json.get("account_details", {})
        holder = details.get("account_holder") or "(unidentified)"
        bank = details.get("bank_name") or "(unidentified bank)"
        tax_fields = {
            key: details.get(key)
            for key in details
            if key.lower() in _TAX_IDENTIFIER_FIELDS or "gstin" in key.lower() or key.lower() == "pan"
        }
        if not tax_fields:
            tax_fields = {"branch_gstin": details.get("branch_gstin")}
        rendered = ", ".join(f"{key}: {_format_value(value)}" for key, value in tax_fields.items())
        rows.append(f"  - {holder} (account {acct_id}, {bank}): {rendered}")
        citations.append({"type": "account_context", "account": acct_id, "bank_name": bank})

    if not rows:
        return None
    answer = "Tax identifier fields found in the dataset:\n" + "\n".join(rows)
    return {"answer": answer, "citations": citations, "matched_pattern": "tax_identifier_catalog"}


_SCAN_MONTHS = (
    "january", "february", "march", "april", "may", "june",
    "july", "august", "september", "october", "november", "december",
)


def _looks_like_transaction_scan(q_lower: str) -> bool:
    """
    True when the question is really a full-transaction-scan request
    (highest/lowest, top-N, above/below threshold, or a date range) rather than
    a single-identifier lookup. Used so the greedy identifier handler defers to
    the dedicated scan handlers when a question happens to also name an account.
    """
    txn_ctx = any(w in q_lower for w in [
        "transaction", "transfer", "payment", "debit", "credit",
        "amount", "withdrawal", "deposit",
    ])
    has_digit = bool(re.search(r"\d", q_lower))
    threshold = has_digit and any(w in q_lower for w in [
        "above", "below", "over", "under", "more than",
        "less than", "greater than", "exceeding", "exceed",
    ])
    extremum = txn_ctx and any(w in q_lower for w in [
        "highest", "lowest", "largest", "smallest", "biggest",
        "maximum", "minimum", "top",
    ])
    date_range = txn_ctx and (
        any(m in q_lower for m in _SCAN_MONTHS)
        or len(_DATE_TOKEN_RE.findall(q_lower)) >= 2
        or "between" in q_lower
    )
    balance_rank = "balance" in q_lower and any(w in q_lower for w in [
        "highest", "lowest", "largest", "smallest", "biggest",
        "maximum", "minimum", "top", "peak", "most", "least",
    ])
    return threshold or extremum or date_range or balance_rank


def _handle_identifier_detail_lookup(question: str, case: dict) -> dict | None:
    """
    Matches exact identifier lookups and returns every field available for the
    matched record(s), instead of asking semantic search to summarize a chunk.
    """
    q_lower = question.lower()
    # A scan-shaped question ("above 10k for account X", "highest debit for X")
    # names an account but wants a computed answer over ALL its rows — let the
    # dedicated scan handlers below take it instead of dumping the account.
    if _looks_like_transaction_scan(q_lower):
        return None
    if not _IDENTIFIER_WORD_RE.search(question):
        return None

    candidates = _extract_identifier_candidates(question)
    if not candidates and re.search(r"\b(tax|taxation|gst|gstin|pan|tin)\b", q_lower):
        return _tax_identifier_answer(case)
    if not candidates:
        return None

    # If every identifier is just a known account number, this is really an
    # "account details" question — defer to the crisp account-profile handler
    # rather than echoing every single transaction row for that account (which
    # produced thousands of lines of unreadable output).
    if all(c in case["accounts"] for c in candidates):
        return None

    answer_sections = []
    citations = []
    seen_citations = set()

    def add_citation(citation: dict) -> None:
        key = tuple(sorted((k, str(v)) for k, v in citation.items()))
        if key not in seen_citations:
            seen_citations.add(key)
            citations.append(citation)

    for candidate in candidates:
        candidate_sections = []

        for acct_id, acct_json in case["accounts"].items():
            details = acct_json.get("account_details", {})
            account_matches = _mapping_matches_candidate(details, candidate)
            transaction_matches = [
                txn
                for txn in acct_json.get("transactions", [])
                if _mapping_matches_candidate(txn, candidate)
            ]

            if account_matches:
                bank = details.get("bank_name") or "(unidentified bank)"
                clean_count = (
                    len(case["clean"][case["clean"]["account_number"].astype(str) == str(acct_id)])
                    if "account_number" in case["clean"].columns else 0
                )
                flagged_count = (
                    len(case["flagged"][case["flagged"]["Account_ID"].astype(str) == str(acct_id)])
                    if "Account_ID" in case["flagged"].columns else 0
                )
                duplicate_count = (
                    len(case["duplicates"][case["duplicates"]["account_number"].astype(str) == str(acct_id)])
                    if "account_number" in case["duplicates"].columns else 0
                )
                candidate_sections.append(
                    f"Account record ({acct_id}) - every account_details field:\n"
                    f"{_format_field_block(details)}"
                )
                file_metadata = _account_file_metadata(case, acct_id)
                if file_metadata:
                    candidate_sections.append(
                        f"Extraction metadata for account {acct_id}:\n"
                        f"{_format_field_block(file_metadata)}"
                    )
                candidate_sections.append(
                    f"Account {acct_id} linked-row counts:\n"
                    f"  - per-account JSON transactions: {len(acct_json.get('transactions', []))}\n"
                    f"  - clean transaction rows: {clean_count}\n"
                    f"  - flagged transaction rows: {flagged_count}\n"
                    f"  - duplicate rows: {duplicate_count}"
                )
                add_citation({"type": "account_context", "account": acct_id, "bank_name": bank})

            for txn in transaction_matches:
                candidate_sections.append(
                    f"Per-account JSON transaction ({txn.get('txn_id') or txn.get('Transaction_ID') or 'unlabelled'}) - every field:\n"
                    f"{_format_field_block(txn)}"
                )
                add_citation({
                    "type": "transaction",
                    "ref": str(txn.get("txn_id") or txn.get("Transaction_ID") or candidate),
                    "account": str(txn.get("Account_ID") or acct_id),
                    "date": str(txn.get("Date") or "?"),
                })

        table_specs = [
            ("clean_transactions.csv", case["clean"], "transaction"),
            ("flagged_transactions.csv", case["flagged"], "flagged_transaction"),
            ("duplicates.csv", case["duplicates"], "duplicate_transaction"),
        ]
        for table_name, df, citation_type in table_specs:
            if df.empty:
                continue
            matches = df[df.apply(lambda row: _row_matches_candidate(row, candidate), axis=1)]
            for _, row in matches.iterrows():
                row_dict = row.to_dict()
                candidate_sections.append(
                    f"{table_name} row - every column:\n{_format_field_block(row_dict)}"
                )
                if citation_type == "flagged_transaction":
                    add_citation({
                        "type": "flagged_transaction",
                        "account": str(row_dict.get("Account_ID") or "?"),
                        "date": _format_value(row_dict.get("Date")),
                        "flag_reason": str(row_dict.get("flag_reason") or "?"),
                    })
                elif citation_type == "duplicate_transaction":
                    add_citation({
                        "type": "duplicate_transaction",
                        "account": str(row_dict.get("account_number") or "?"),
                        "date": _format_value(row_dict.get("date")),
                        "duplicate_row": int(row_dict.get("duplicate_row_number") or 0),
                        "original_row": int(row_dict.get("original_row_number") or 0),
                    })
                else:
                    add_citation({
                        "type": "transaction",
                        "ref": str(row_dict.get("txn_id") or row_dict.get("Transaction_ID") or candidate),
                        "account": str(row_dict.get("account_number") or row_dict.get("Account_ID") or "?"),
                        "date": _format_value(row_dict.get("Date")),
                    })

        if candidate_sections:
            answer_sections.append(
                f"Complete dataset details for identifier '{candidate}':\n"
                + "\n\n".join(candidate_sections)
            )

    if not answer_sections:
        return None

    answer = "\n\n".join(answer_sections)
    return {"answer": answer, "citations": citations, "matched_pattern": "identifier_detail_lookup"}


# ─────────────────────────────────────────────────────────────────────────────
# SHARED HELPERS for the transaction-scan handlers below
# ─────────────────────────────────────────────────────────────────────────────

def _resolve_account(question: str, case: dict) -> str | None:
    """
    Returns the account_id if the question names a specific account number or
    account holder. Single shared resolver used by every scan handler below —
    mirrors resolve_account_filter() in rag_chat.py so scoping is consistent.
    """
    q_lower = question.lower()
    for acct_id, acct_json in case["accounts"].items():
        if acct_id in question:
            return acct_id
        holder = acct_json["account_details"].get("account_holder", "")
        if holder and holder.lower() in q_lower:
            return acct_id
    return None


def _with_amount(df: pd.DataFrame) -> pd.DataFrame:
    """
    Return a copy of the transactions DataFrame with a unified numeric
    `_amount` column and a normalized `_direction` ("debit"/"credit") column.

    Robust to schema drift between extraction runs: some runs emit a
    Transaction_Type column, others don't. When the label is absent or blank,
    direction is inferred from whichever of Debit/Credit is populated.
    """
    df = df.copy()
    debit = pd.to_numeric(df.get("Debit"), errors="coerce").fillna(0.0)
    credit = pd.to_numeric(df.get("Credit"), errors="coerce").fillna(0.0)

    if "Transaction_Type" in df.columns:
        direction = df["Transaction_Type"].astype(str).str.strip().str.lower()
        blank = ~direction.isin(["debit", "credit"])
        direction = direction.mask(blank & (debit > 0), "debit")
        direction = direction.mask(blank & (debit <= 0) & (credit > 0), "credit")
    else:
        direction = pd.Series(
            ["debit" if d > 0 else "credit" for d, c in zip(debit, credit)],
            index=df.index,
        )

    df["_direction"] = direction
    df["_amount"] = debit.where(direction == "debit", credit)
    return df


def _extract_count(question: str, target_acct: str | None, default: int) -> int:
    """
    Pull an explicit small count ("top 5", "3 highest") from the question,
    ignoring any account number so its long digit string isn't mistaken for N.
    """
    q = question.replace(target_acct, " ") if target_acct else question
    for tok in re.findall(r"\b(\d+)\b", q):
        val = int(tok)
        if 1 <= val <= 50:
            return val
    return default


def _txn_line(row: pd.Series) -> str:
    """One-line rendering of a transaction row for list answers."""
    date_str = row["Date"].strftime("%d/%m/%Y") if pd.notna(row.get("Date")) else "?"
    narration = str(row.get("Narration") or "").strip()
    return f"  - {date_str}: ₹{row['_amount']:,.2f} ({row['_direction']}) — {narration[:60]}"


def _txn_citation(row: pd.Series) -> dict:
    return {
        "type": "transaction",
        "ref": str(row.get("txn_id") or row.get("Transaction_ID") or "?"),
        "account": str(row.get("account_number") or "?"),
        "date": row["Date"].strftime("%d/%m/%Y") if pd.notna(row.get("Date")) else "?",
    }


# ─────────────────────────────────────────────────────────────────────────────
# PATTERN HANDLERS
# Each handler takes (question, case) and returns an answer dict, or None if
# it doesn't actually apply once it looks closer (lets a coarse regex match
# defer to the next handler / fall through to semantic search).
# ─────────────────────────────────────────────────────────────────────────────

def _handle_account_details(question: str, case: dict) -> dict | None:
    """
    Full profile for ONE named account: every account_details field, statement
    period, balances, and clean/flagged transaction counts. Returns None when
    no specific account is named (so all-account handlers can take over).
    """
    q_lower = question.lower()
    if not any(w in q_lower for w in [
        "detail", "information", "info", "profile", "tell me about",
        "about account", "account details",
    ]):
        return None

    target_acct = _resolve_account(question, case)
    if not target_acct:
        return None

    acct_json = case["accounts"].get(target_acct)
    if not acct_json:
        return None

    d = acct_json["account_details"]
    clean_count = len(case["clean"][case["clean"]["account_number"].astype(str) == str(target_acct)])
    flagged_count = (
        len(case["flagged"][case["flagged"]["Account_ID"].astype(str) == str(target_acct)])
        if "Account_ID" in case["flagged"].columns else 0
    )

    def _bal(key: str) -> str:
        v = d.get(key)
        if v in (None, "") or _is_missing(v):
            return "not extracted"
        try:
            return f"₹{float(v):,.2f}"
        except (TypeError, ValueError):
            return str(v)

    lines = [
        f"Account number: {d.get('account_number')}",
        f"Account holder: {_format_value(d.get('account_holder'))}",
        f"Bank: {_format_value(d.get('bank_name'))}  |  Branch: {_format_value(d.get('branch'))}",
        f"IFSC: {_format_value(d.get('ifsc_code'))}  |  MICR: {_format_value(d.get('micr_code'))}",
        f"Account type: {_format_value(d.get('account_type'))}",
        f"Statement period: {_format_value(d.get('statement_period'))}",
        f"Opening balance: {_bal('opening_balance')}",
        f"Closing balance: {_bal('closing_balance')}",
        f"Nominee: {_format_value(d.get('nominee_name'))}",
        f"Customer ID: {_format_value(d.get('customer_id'))}",
        f"GSTIN: {_format_value(d.get('branch_gstin'))}  |  CKYC: {_format_value(d.get('ckyc_number'))}",
        f"Currency: {_format_value(d.get('currency'))}",
        f"Address: {_format_value(d.get('customer_address'))}",
        f"Total transactions: {clean_count} clean, {flagged_count} flagged",
    ]
    answer = f"Full details for account {target_acct}:\n" + "\n".join(lines)
    citations = [{"type": "account_context", "account": target_acct,
                  "bank_name": d.get("bank_name") or ""}]
    return {"answer": answer, "citations": citations, "matched_pattern": "account_details"}


def _handle_all_accounts_summary(question: str, case: dict) -> dict | None:
    """Full per-account overview for the whole case (names + balances + counts)."""
    q_lower = question.lower()
    if not any(w in q_lower for w in [
        "summary", "overview", "all account", "all the account", "every account",
    ]):
        return None
    if any(w in q_lower for w in ["transaction", "transfer", "payment"]):
        return None  # too specific — let the scan handlers take it

    lines = []
    citations = []
    for acct_id, acct_json in case["accounts"].items():
        d = acct_json["account_details"]
        clean_count = len(case["clean"][case["clean"]["account_number"].astype(str) == str(acct_id)])
        flagged_count = (
            len(case["flagged"][case["flagged"]["Account_ID"].astype(str) == str(acct_id)])
            if "Account_ID" in case["flagged"].columns else 0
        )
        closing = d.get("closing_balance")
        try:
            closing_str = f"₹{float(closing):,.2f}" if closing not in (None, "") else "not extracted"
        except (TypeError, ValueError):
            closing_str = str(closing)
        lines.append(
            f"\n• {d.get('account_holder') or '(unidentified)'} — {acct_id} at "
            f"{d.get('bank_name') or 'unknown bank'}\n"
            f"  Period: {d.get('statement_period') or 'unknown'}  |  Closing balance: {closing_str}\n"
            f"  Transactions: {clean_count} clean, {flagged_count} flagged"
        )
        citations.append({"type": "account_context", "account": acct_id,
                          "bank_name": d.get("bank_name") or ""})

    answer = f"Summary of all {len(case['accounts'])} accounts in this case:" + "".join(lines)
    return {"answer": answer, "citations": citations, "matched_pattern": "all_accounts_summary"}


def _handle_top_n_transactions(question: str, case: dict) -> dict | None:
    """Top N transactions by amount. Handles 'top 5', 'largest 3 transfers', etc."""
    q_lower = question.lower()
    if not any(w in q_lower for w in ["top", "largest", "biggest", "highest"]):
        return None
    if not any(w in q_lower for w in ["transaction", "transfer", "payment", "debit", "credit"]):
        return None

    target_acct = _resolve_account(question, case)
    n = _extract_count(question, target_acct, default=0)
    # Only treat this as a "top N" (list) request when a count is explicit or
    # the word "top" is present; otherwise defer to the singular highest/lowest
    # handler ("the highest debit" should return ONE row, not a list of five).
    if n == 0 and "top" not in q_lower:
        return None
    if n == 0:
        n = 5

    prefer_debit = "debit" in q_lower or "withdrawal" in q_lower
    prefer_credit = "credit" in q_lower or "received" in q_lower or "deposit" in q_lower

    df = case["clean"]
    if target_acct:
        df = df[df["account_number"].astype(str) == str(target_acct)]
    df = _with_amount(df)
    if prefer_debit:
        df = df[df["_direction"] == "debit"]
    elif prefer_credit:
        df = df[df["_direction"] == "credit"]

    if df.empty:
        return {"answer": "No matching transactions found for that filter.",
                "citations": [], "matched_pattern": "top_n_transactions"}

    top = df.nlargest(n, "_amount")
    answer = (
        f"Top {len(top)} transaction(s) by amount"
        f"{' for account ' + target_acct if target_acct else ' across all accounts'}:\n"
        + "\n".join(_txn_line(r) for _, r in top.iterrows())
    )
    citations = [_txn_citation(r) for _, r in top.iterrows()]
    return {"answer": answer, "citations": citations, "matched_pattern": "top_n_transactions"}


def _handle_highest_lowest_transaction(question: str, case: dict) -> dict | None:
    """Single highest/lowest transaction, optionally scoped to account/direction."""
    q_lower = question.lower()
    is_highest = any(w in q_lower for w in ["highest", "largest", "biggest", "maximum", "most", "top"])
    is_lowest = any(w in q_lower for w in ["lowest", "smallest", "minimum", "least"])
    if not (is_highest or is_lowest):
        return None
    if not any(w in q_lower for w in ["transaction", "amount", "debit", "credit", "transfer", "payment"]):
        return None

    prefer_debit = "debit" in q_lower or "withdrawal" in q_lower or "sent" in q_lower or "paid" in q_lower
    prefer_credit = "credit" in q_lower or "received" in q_lower or "deposit" in q_lower

    df = case["clean"]
    target_acct = _resolve_account(question, case)
    if target_acct:
        df = df[df["account_number"].astype(str) == str(target_acct)]
    df = _with_amount(df)
    if prefer_debit:
        df = df[df["_direction"] == "debit"]
    elif prefer_credit:
        df = df[df["_direction"] == "credit"]

    if df.empty:
        return {"answer": "No matching transactions found for that filter.",
                "citations": [], "matched_pattern": "highest_lowest_transaction"}

    row = df.nlargest(1, "_amount").iloc[0] if is_highest else df.nsmallest(1, "_amount").iloc[0]
    date_str = row["Date"].strftime("%d/%m/%Y") if pd.notna(row.get("Date")) else "unknown date"
    narration = str(row.get("Narration") or "").strip()
    answer = (
        f"The {'highest' if is_highest else 'lowest'} {row['_direction']} transaction"
        f"{' for account ' + target_acct if target_acct else ' across all accounts'} "
        f"is ₹{row['_amount']:,.2f} on {date_str}. "
        f"Narration: {narration}. "
        f"Reference: {row.get('txn_id') or row.get('Transaction_ID') or '?'}."
    )
    return {"answer": answer, "citations": [_txn_citation(row)],
            "matched_pattern": "highest_lowest_transaction"}


def _handle_transactions_above_below_threshold(question: str, case: dict) -> dict | None:
    """Lists transactions above/below a rupee threshold named in the question."""
    q_lower = question.lower()
    is_above = any(w in q_lower for w in ["above", "over", "more than", "greater than", "exceeding", "exceed"])
    is_below = any(w in q_lower for w in ["below", "under", "less than", "smaller than"])
    if not (is_above or is_below):
        return None

    amounts = re.findall(r"[\d,]+(?:\.\d+)?", question.replace(",", ""))
    known_accounts = {str(a) for a in case.get("accounts", {})}
    amounts = [a for a in amounts if a not in known_accounts]  # e.g. "over time for account 12668100018596" — the account number is not a threshold
    if not amounts:
        return None
    try:
        threshold = float(max(amounts, key=lambda x: float(x)))
    except ValueError:
        return None

    df = case["clean"]
    target_acct = _resolve_account(question, case)
    if target_acct:
        df = df[df["account_number"].astype(str) == str(target_acct)]
    df = _with_amount(df)
    mask = (df["_amount"] > threshold) if is_above else ((df["_amount"] < threshold) & (df["_amount"] > 0))
    matched = df[mask].sort_values("_amount", ascending=not is_above)

    if matched.empty:
        return {
            "answer": f"No transactions {'above' if is_above else 'below'} ₹{threshold:,.2f} found"
                      + (f" for account {target_acct}" if target_acct else "") + ".",
            "citations": [], "matched_pattern": "threshold_list",
        }

    lines = [_txn_line(r) for _, r in matched.head(20).iterrows()]
    more = f"\n  (and {len(matched) - 20} more)" if len(matched) > 20 else ""
    answer = (
        f"Found {len(matched)} transaction(s) {'above' if is_above else 'below'} ₹{threshold:,.2f}"
        f"{' for account ' + target_acct if target_acct else ''}:\n"
        + "\n".join(lines) + more
    )
    citations = [_txn_citation(r) for _, r in matched.head(20).iterrows()]
    return {"answer": answer, "citations": citations, "matched_pattern": "threshold_list"}


def _handle_date_range_transactions(question: str, case: dict) -> dict | None:
    """Transactions within a named month or an explicit date range."""
    q_lower = question.lower()
    MONTHS = {"january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
              "july": 7, "august": 8, "september": 9, "october": 10, "november": 11, "december": 12}

    month_match = next((m for m in MONTHS if m in q_lower), None)
    if not month_match and "between" not in q_lower and "from" not in q_lower and " on " not in q_lower:
        return None

    df = case["clean"]
    target_acct = _resolve_account(question, case)
    if target_acct:
        df = df[df["account_number"].astype(str) == str(target_acct)]
    df = _with_amount(df)

    if month_match:
        month_num = MONTHS[month_match]
        years = re.findall(r"\b(20\d{2})\b", question)
        if years:
            year = int(years[0])
        else:
            valid_years = df["Date"].dt.year.dropna()
            if valid_years.empty:
                return None
            year = int(valid_years.mode().iloc[0])
        matched = df[(df["Date"].dt.month == month_num) & (df["Date"].dt.year == year)]
        period_str = f"{month_match.capitalize()} {year}"
    else:
        date_strs = _DATE_TOKEN_RE.findall(question)
        if len(date_strs) < 2:
            return None
        try:
            start = pd.to_datetime(date_strs[0], dayfirst=True)
            end = pd.to_datetime(date_strs[1], dayfirst=True)
        except Exception:
            return None
        matched = df[(df["Date"] >= start) & (df["Date"] <= end)]
        period_str = f"{date_strs[0]} to {date_strs[1]}"

    if matched.empty:
        return {"answer": f"No transactions found for {period_str}"
                          + (f" in account {target_acct}" if target_acct else "") + ".",
                "citations": [], "matched_pattern": "date_range"}

    total_debit = matched[matched["_direction"] == "debit"]["_amount"].sum()
    total_credit = matched[matched["_direction"] == "credit"]["_amount"].sum()
    matched_sorted = matched.sort_values("Date")
    max_lines = 20
    lines = [_txn_line(r) for _, r in matched_sorted.head(max_lines).iterrows()]
    remaining = len(matched) - len(lines)
    if remaining > 0:
        lines.append(f"  (+{remaining} more transaction(s) not shown)")
    answer = (
        f"{len(matched)} transaction(s) in {period_str}"
        f"{' for account ' + target_acct if target_acct else ''}. "
        f"Total debits: ₹{total_debit:,.2f}, Total credits: ₹{total_credit:,.2f}.\n"
        + "\n".join(lines)
    )
    citations = [_txn_citation(r) for _, r in matched_sorted.head(max_lines).iterrows()]
    return {"answer": answer, "citations": citations, "matched_pattern": "date_range"}


def _handle_balance_ranking(question: str, case: dict) -> dict | None:
    """Highest/lowest (running) account Balance — e.g. 'top 3 highest balance'."""
    q_lower = question.lower()
    if "balance" not in q_lower or "closing" in q_lower or "final" in q_lower:
        return None  # closing/final balance is handled by _handle_closing_balance
    is_high = any(w in q_lower for w in ["highest", "largest", "biggest", "maximum", "top", "most", "peak"])
    is_low = any(w in q_lower for w in ["lowest", "smallest", "minimum", "least"])
    if not (is_high or is_low):
        return None

    df = case["clean"]
    if "Balance" not in df.columns:
        return None
    target_acct = _resolve_account(question, case)
    if target_acct:
        df = df[df["account_number"].astype(str) == str(target_acct)]
    df = df.copy()
    df["_bal"] = pd.to_numeric(df["Balance"], errors="coerce")
    df = df.dropna(subset=["_bal"])
    if df.empty:
        return {"answer": "No balance figures are available for that filter.",
                "citations": [], "matched_pattern": "balance_ranking"}

    # "top"/plural ("balances") implies a short list; a bare "highest balance"
    # implies a single figure.
    plural = "top" in q_lower or "balances" in q_lower
    n = _extract_count(question, target_acct, default=3 if plural else 1)
    ranked = df.nlargest(n, "_bal") if is_high else df.nsmallest(n, "_bal")

    word = "highest" if is_high else "lowest"
    lines = []
    for _, r in ranked.iterrows():
        date_str = r["Date"].strftime("%d/%m/%Y") if pd.notna(r.get("Date")) else "?"
        narration = str(r.get("Narration") or "").strip()
        lines.append(f"  - ₹{r['_bal']:,.2f} on {date_str} — {narration[:50]}")

    scope = f" for account {target_acct}" if target_acct else " across all accounts"
    if n == 1:
        answer = f"The {word} balance{scope} was ₹{ranked.iloc[0]['_bal']:,.2f}.\n" + lines[0].strip()
    else:
        answer = f"The {len(ranked)} {word} balance points{scope}:\n" + "\n".join(lines)
    citations = [_txn_citation(r) for _, r in ranked.iterrows()]
    return {"answer": answer, "citations": citations, "matched_pattern": "balance_ranking"}

def _handle_list_account_holders(question: str, case: dict) -> dict | None:
    """Matches: "list/show/who are the account holders/accused [persons]"."""
    if not re.search(r"\b(list|show|who are|name)\b.*\b(account holder|accused|holder)", question, re.IGNORECASE):
        return None

    rows = []
    for acct_id, acct_json in case["accounts"].items():
        d = acct_json["account_details"]
        holder = d.get("account_holder") or "(not extracted)"
        bank = d.get("bank_name") or "(not extracted)"
        rows.append(f"  - {holder} — account {acct_id} at {bank}")

    answer = (
        f"There are {len(case['accounts'])} accounts in this case:\n"
        + "\n".join(rows)
    )
    citations = [
        {"type": "account_context", "account": acct_id, "bank_name": j["account_details"].get("bank_name") or "(not extracted)"}
        for acct_id, j in case["accounts"].items()
    ]
    return {"answer": answer, "citations": citations, "matched_pattern": "list_account_holders"}


def _handle_closing_balance(question: str, case: dict) -> dict | None:
    """Matches: "closing balance" mentioned, for one account or all accounts."""
    if "closing balance" not in question.lower() and "final balance" not in question.lower():
        return None

    # Does the question name one specific account/person, or ask for all?
    target_account = None
    q_lower = question.lower()
    for acct_id, acct_json in case["accounts"].items():
        holder = acct_json["account_details"].get("account_holder", "")
        if acct_id in question or (holder and holder.lower() in q_lower):
            target_account = acct_id
            break

    accounts_to_report = (
        {target_account: case["accounts"][target_account]}
        if target_account
        else case["accounts"]
    )

    rows = []
    citations = []
    for acct_id, acct_json in accounts_to_report.items():
        d = acct_json["account_details"]
        closing = d.get("closing_balance")
        closing_str = f"₹{float(closing):,.2f}" if closing not in (None, "") else "not extracted"
        holder = d.get("account_holder") or "(unidentified)"
        bank = d.get("bank_name") or "(unidentified bank)"
        rows.append(f"  - {holder} (account {acct_id}, {bank}): {closing_str}")
        citations.append({"type": "account_context", "account": acct_id, "bank_name": bank})

    answer = "Closing balance" + ("s" if len(rows) > 1 else "") + ":\n" + "\n".join(rows)
    return {"answer": answer, "citations": citations, "matched_pattern": "closing_balance"}


def _handle_flag_reason_lookup(question: str, case: dict) -> dict | None:
    """
    Matches: "why was [a/this] transaction flagged", "what flag reasons exist",
    "how many transactions were flagged".
    """
    q_lower = question.lower()
    if "flag" not in q_lower:
        return None
    if not re.search(r"\b(why|what|how many|reason)\b", q_lower):
        return None

    flagged_df = case["flagged"]
    if flagged_df.empty:
        return {
            "answer": "No transactions were flagged during extraction for this case.",
            "citations": [],
            "matched_pattern": "flag_reason_lookup",
        }

    reason_counts = flagged_df["flag_reason"].value_counts()
    summary_lines = [f"  - {reason}: {count} transaction(s)" for reason, count in reason_counts.items()]

    # If the question asks "why", include a couple of concrete examples per reason
    examples = []
    if "why" in q_lower:
        for reason in reason_counts.index:
            example_row = flagged_df[flagged_df["flag_reason"] == reason].iloc[0]
            examples.append(
                f"  Example ({reason}): account {example_row['Account_ID']} on "
                f"{example_row['Date'].strftime('%d/%m/%Y') if pd.notna(example_row['Date']) else 'unknown date'} — "
                f"narration: {example_row['Narration']}"
            )

    answer = (
        f"{len(flagged_df)} transaction(s) were flagged during extraction, "
        f"across {len(reason_counts)} distinct reason(s):\n"
        + "\n".join(summary_lines)
    )
    if examples:
        answer += "\n\n" + "\n".join(examples)

    citations = [
        {"type": "flagged_transaction", "account": str(row["Account_ID"]), "flag_reason": row["flag_reason"]}
        for _, row in flagged_df.head(10).iterrows()
    ]
    return {"answer": answer, "citations": citations, "matched_pattern": "flag_reason_lookup"}


def _handle_transaction_count(question: str, case: dict) -> dict | None:
    """Matches: "how many transactions" for one account or the whole case."""
    q_lower = question.lower()
    if not re.search(r"how many (transactions|entries|records)", q_lower):
        return None

    target_account = None
    for acct_id, acct_json in case["accounts"].items():
        holder = acct_json["account_details"].get("account_holder", "")
        if acct_id in question or (holder and holder.lower() in q_lower):
            target_account = acct_id
            break

    clean_df = case["clean"]
    if target_account:
        count = len(clean_df[clean_df["account_number"] == target_account])
        flagged_count = len(case["flagged"][case["flagged"]["Account_ID"] == target_account])
        holder = case["accounts"][target_account]["account_details"].get("account_holder") or "(unidentified)"
        answer = (
            f"{holder} (account {target_account}) has {count} clean transaction(s)"
            + (f" and {flagged_count} flagged transaction(s)" if flagged_count else "")
            + " recorded in this case."
        )
        citations = [{"type": "account_context", "account": target_account, "bank_name": case["accounts"][target_account]["account_details"].get("bank_name") or ""}]
    else:
        per_account = clean_df.groupby("account_number").size()
        lines = [f"  - account {acct}: {n} transaction(s)" for acct, n in per_account.items()]
        answer = (
            f"This case has {len(clean_df)} total clean transactions across "
            f"{len(per_account)} accounts:\n" + "\n".join(lines)
        )
        citations = [{"type": "account_context", "account": a, "bank_name": ""} for a in per_account.index]

    return {"answer": answer, "citations": citations, "matched_pattern": "transaction_count"}


def _handle_duplicate_summary(question: str, case: dict) -> dict | None:
    """Matches: "were any duplicates", "how many duplicate transactions"."""
    q_lower = question.lower()
    if "duplicate" not in q_lower:
        return None

    dup_df = case["duplicates"]
    if dup_df.empty:
        return {
            "answer": "No duplicate transactions were identified during extraction for this case.",
            "citations": [],
            "matched_pattern": "duplicate_summary",
        }

    per_account = dup_df.groupby("account_number").size()
    lines = [f"  - account {acct}: {n} duplicate(s)" for acct, n in per_account.items()]
    answer = (
        f"{len(dup_df)} duplicate transaction(s) were identified and removed "
        f"during extraction, across {len(per_account)} account(s):\n" + "\n".join(lines)
    )
    citations = [
        {"type": "duplicate_transaction", "account": str(row["account_number"]),
         "duplicate_row": int(row["duplicate_row_number"]), "original_row": int(row["original_row_number"])}
        for _, row in dup_df.head(10).iterrows()
    ]
    return {"answer": answer, "citations": citations, "matched_pattern": "duplicate_summary"}


def _handle_list_banks(question: str, case: dict) -> dict | None:
    """Matches: "which banks", "list all banks", "what banks are involved"."""
    if not re.search(r"\b(which|list|what)\b.*\bbank", question, re.IGNORECASE):
        return None

    banks = {}
    for acct_id, acct_json in case["accounts"].items():
        bank = acct_json["account_details"].get("bank_name") or "(unidentified bank)"
        banks.setdefault(bank, []).append(acct_id)

    lines = [f"  - {bank}: {len(accts)} account(s) — {', '.join(accts)}" for bank, accts in banks.items()]
    answer = f"This case involves {len(banks)} distinct bank(s):\n" + "\n".join(lines)
    citations = [{"type": "account_context", "account": acct_id, "bank_name": bank} for bank, accts in banks.items() for acct_id in accts]
    return {"answer": answer, "citations": citations, "matched_pattern": "list_banks"}


# ─────────────────────────────────────────────────────────────────────────────
# ROUTER — tries each handler in order, returns the first match (or None)
# ─────────────────────────────────────────────────────────────────────────────

_HANDLERS = [
    _handle_identifier_detail_lookup,   # existing — exact identifier dumps
    _handle_account_details,            # full profile for one named account
    _handle_list_account_holders,       # existing — names only (before summary)
    _handle_list_banks,                 # existing
    _handle_all_accounts_summary,       # whole-case account overview
    _handle_top_n_transactions,         # "top 5" list — before highest/lowest
    _handle_highest_lowest_transaction, # single highest/lowest row
    _handle_transactions_above_below_threshold,
    _handle_date_range_transactions,
    _handle_balance_ranking,            # highest/lowest running balance
    _handle_closing_balance,            # existing
    _handle_flag_reason_lookup,         # existing
    _handle_transaction_count,          # existing
    _handle_duplicate_summary,          # existing
]


# Investigation-Intelligence cues (Phase 3). A question carrying one of these
# is analytical/multi-hop/frequency-shaped — NOT a simple structured lookup —
# even when it also contains scan words like "highest" or "credit" that the
# transaction-scan handlers would otherwise greedily claim (e.g. "highest
# transaction FREQUENCY", "highest credit and LATER TRANSFERRED 80%"). We defer
# those to the dedicated Investigation Intelligence layer that runs next.
_INVESTIGATION_CUE_RE = re.compile(
    r"\b(transaction\s+)?frequency\b|\bbusiest\b|\bmost active\b|\bmost activity\b|"
    r"\bdormant\b|\binactive\b|\bspikes?\b|\bfrequency ranking\b|"
    r"\blater\s+(transferred|sent|moved|paid)\b|\bthen\s+(transferred|sent|moved|paid)\b|"
    r"\bimmediately\s+(after|transferred|withdrew|withdrawn)\b|"
    r"\bwithin\s+(two|three|four|\d+)\s+(day|hour|minute)|"
    r"\bmostly\s+(send|sends|receive|receives|perform)\b|\brather than receive\b|"
    r"\brarely\s+(spend|send)\b|\bone beneficiary\b|\bsingle beneficiary\b|"
    r"\bonly transact\b|\bcommon (counterpart|beneficiar)|\bshared (counterpart|beneficiar)\b|"
    r"\bwhy\b.*\b(suspicious|layering|scrutin)\b",
    re.IGNORECASE,
)


def try_structured_answer(question: str, case: dict) -> dict | None:
    """
    Attempts to answer the question using a structured handler. Returns
    {"answer": str, "citations": list[dict], "matched_pattern": str} on a
    match, or None if no structured pattern applies (caller should then
    fall back to the Investigation Intelligence layer / semantic search).

    Defers up front when the question is Investigation-Intelligence-shaped
    (frequency/multi-hop/analytics) so a coarse scan handler doesn't hijack an
    analytical question that merely happens to share a keyword like "highest".
    """
    if _INVESTIGATION_CUE_RE.search(question):
        return None

    for handler in _HANDLERS:
        result = handler(question, case)
        if result is not None:
            return result
    return None
