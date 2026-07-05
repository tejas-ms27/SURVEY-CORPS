"""
data_loader.py
─────────────────────────────────────────────────────────────────────────────
CIDECODE 2026 — Multi-Accused Cross-Account Investigation Engine
Module: Real Extraction Output Loader

Replaces mock_data.py. Loads the ACTUAL output of the extraction pipeline:
  - clean_transactions.csv      (the bulk of transactions, validated)
  - flagged_transactions.csv    (transactions with a flag_reason —
                                  balance_mismatch, invalid_date, etc.)
  - duplicates.csv              (transactions identified as duplicates,
                                  with a reason_flagged)
  - metadata.json               (run-level summary: per-file reconciliation
                                  rate, extraction tier used, account details)
  - per-account JSON files      (e.g. unknown_763010062770.json) — richer
                                  account-level metadata (branch, nominee,
                                  statement period, opening/closing balance)
                                  than the flat CSVs carry alone

NOTE: No fraud-pattern file exists yet (the NetworkX module's output).
get_flagged_patterns() below returns an empty list as a safe placeholder —
swap it for the real loader the moment that module produces output,
matching the schema agreed with the fraud-detection teammate.
"""

import json
from pathlib import Path

import pandas as pd


def load_clean_transactions(path: str | Path = "clean_transactions.csv") -> pd.DataFrame:
    """
    Loads clean_transactions.csv. Adds a `source` column so downstream
    chunking can distinguish "clean" rows from flagged/duplicate rows
    if all three are ever merged into one DataFrame.
    """
    df = pd.read_csv(path, dtype={"account_number": str})
    df["Date"] = pd.to_datetime(df["Date"], format="%d/%m/%Y", errors="coerce")
    df["source"] = "clean"
    return df


def load_flagged_transactions(path: str | Path = "flagged_transactions.csv") -> pd.DataFrame:
    """
    Loads flagged_transactions.csv. These rows have a `flag_reason`
    (e.g. "balance_mismatch", "invalid_date") which is valuable context
    for the chatbot — investigators will directly ask "why was this
    transaction flagged?"
    """
    df = pd.read_csv(path, dtype={"Account_ID": str})
    df["Date"] = pd.to_datetime(df["Date"], format="%d/%m/%Y", errors="coerce")
    df["source"] = "flagged"
    return df


def load_duplicates(path: str | Path = "duplicates.csv") -> pd.DataFrame:
    """
    Loads duplicates.csv. Each row records a duplicate transaction and
    which original row it duplicates, plus why it was flagged as a dupe.
    """
    df = pd.read_csv(path, dtype={"account_number": str})
    df["date"] = pd.to_datetime(df["date"], format="%d/%m/%Y", errors="coerce")
    df["source"] = "duplicate"
    return df


def load_run_metadata(path: str | Path = "metadata.json") -> dict:
    """
    Loads metadata.json — the run-level summary. Useful for building
    account-level context chunks (bank name, statement period, opening/
    closing balance, reconciliation rate) that aren't in the flat CSVs.
    """
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_account_json(path: str | Path) -> dict:
    """
    Loads a single per-account JSON file (e.g. unknown_763010062770.json).
    Contains account_details + the full transaction list for that account.
    Richer than the CSV rows alone — has branch, nominee_name,
    statement_period, opening/closing balance.
    """
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_all_account_jsons(directory: str | Path = ".") -> dict[str, dict]:
    """
    Loads every per-account JSON file in a directory, keyed by account
    number. Skips metadata.json and any CSV files automatically.

    Returns
    -------
    dict mapping account_number (str) -> account JSON dict
    """
    directory = Path(directory)
    accounts = {}

    # Run-level files that live alongside the per-account JSONs but are NOT
    # account JSONs. extraction_ledger.json is a LIST and extraction_summary_
    # report.json is a summary dict without account_details — calling .get(
    # "account_details") on them blows up, so they are skipped by name. Any
    # other non-account-shaped JSON is skipped by the shape guard below.
    _NON_ACCOUNT_JSONS = {
        "metadata.json",
        "extraction_ledger.json",
        "extraction_summary_report.json",
    }

    def _maybe_add(json_path: Path) -> None:
        if json_path.name in _NON_ACCOUNT_JSONS:
            return
        data = load_account_json(json_path)
        # Only per-account JSON dicts carry an "account_details" block; skip
        # anything else (lists, report dicts, future run-level files) instead
        # of assuming every *.json in the folder is an account file.
        if not isinstance(data, dict) or "account_details" not in data:
            return
        details = data.get("account_details") or {}
        if not isinstance(details, dict):
            return
        acct_number = str(details.get("account_number", ""))
        if acct_number:
            accounts[acct_number] = data

    for json_path in directory.glob("*.json"):
        _maybe_add(json_path)

    statements_dir = directory / "statements"
    if statements_dir.exists():
        for json_path in statements_dir.glob("*.json"):
            _maybe_add(json_path)
    return accounts


def get_flagged_patterns() -> list[dict]:
    """
    PLACEHOLDER — the NetworkX fraud-detection module has not produced
    output yet. Returns an empty list so the rest of the RAG pipeline
    runs end-to-end without erroring.

    Once the teammate's module is ready, replace this with a real loader,
    e.g.:
        def get_flagged_patterns(path="fraud_patterns.json") -> list[dict]:
            with open(path) as f:
                return json.load(f)

    The dicts it returns must match the schema agreed earlier:
    pattern_id, pattern_type, severity, accused_accounts,
    involved_transactions, amount_involved, date_range, summary, graph_path.
    """
    return []


def load_full_case(data_dir: str | Path = ".") -> dict:
    """
    Convenience loader — pulls together everything available for a case
    in one call.

    Returns
    -------
    dict with keys:
        "clean"            -> DataFrame
        "flagged"          -> DataFrame
        "duplicates"       -> DataFrame
        "run_metadata"     -> dict (from metadata.json)
        "accounts"         -> dict[account_number -> account JSON]
        "fraud_patterns"   -> list[dict] (empty until fraud detection is ready)
    """
    data_dir = Path(data_dir)
    return {
        "clean": load_clean_transactions(data_dir / "clean_transactions.csv"),
        "flagged": load_flagged_transactions(data_dir / "flagged_transactions.csv"),
        "duplicates": load_duplicates(data_dir / "duplicates.csv"),
        "run_metadata": load_run_metadata(data_dir / "metadata.json"),
        "accounts": load_all_account_jsons(data_dir),
        "fraud_patterns": get_flagged_patterns(),
    }
