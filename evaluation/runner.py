"""Run the real pipeline (extraction + analysis) over a fixture folder.

Self-contained and dataset-agnostic: given any folder that has a `statements/`
subfolder, it runs extraction then analysis and returns the loaded outputs plus the
identity maps the scorer needs. Reuses the same public entry points the app uses, so
the evaluation measures exactly the production path.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

# Analysis is run deterministically (no LLM) so the numbers are stable and free.
from analysis.analysis_engine.config import AnalysisConfig  # noqa: E402
from analysis.analysis_engine.pipeline import AnalysisPipeline  # noqa: E402
from extraction.extraction_pipeline import run_extraction_pipeline  # noqa: E402

STATEMENT_EXTS = {".pdf", ".xlsx", ".xls", ".csv", ".txt", ".docx", ".jpg", ".jpeg", ".png"}


def norm_acct(value: Any) -> str:
    """Normalize an account-number-like value (drops a trailing '.0' from float coercion)."""
    text = "" if value is None else str(value).strip()
    if text.endswith(".0") and text[:-2].isdigit():
        text = text[:-2]
    return text


def load_truth(folder: Path) -> dict[str, Any]:
    path = folder / "ground_truth.json"
    if not path.exists():
        raise FileNotFoundError(f"No ground_truth.json in {folder}")
    return json.loads(path.read_text(encoding="utf-8"))


def statement_files(folder: Path) -> list[dict[str, str]]:
    statements = folder / "statements"
    files: list[dict[str, str]] = []
    if not statements.is_dir():
        return files
    for path in sorted(statements.iterdir()):
        if path.is_file() and path.suffix.lower() in STATEMENT_EXTS:
            files.append(
                {"file_path": str(path), "account_id": path.stem, "bank_name": "Unknown Bank"}
            )
    return files


def run_extraction(folder: Path, session_id: str, force: bool) -> Path:
    out_dir = ROOT / "outputs" / "extractions" / session_id
    if force and out_dir.exists():
        shutil.rmtree(out_dir)
    if (out_dir / "clean_transactions.csv").exists():
        return out_dir  # reuse cached extraction
    files = statement_files(folder)
    if not files:
        raise FileNotFoundError(f"No statement files in {folder / 'statements'}")
    run_extraction_pipeline(
        files=files,
        session_id=session_id,
        ingest_to_chromadb=False,
        max_ocr_pages=None,
        persist=True,
    )
    return out_dir


def run_analysis(extraction_dir: Path, output_dir: Path, force: bool) -> Path:
    if force and output_dir.exists():
        shutil.rmtree(output_dir)
    result_path = output_dir / "analysis_results.json"
    if result_path.exists():
        return result_path  # reuse cached analysis
    # Deterministic: no LLM fallback, so evaluation numbers are reproducible and free.
    AnalysisPipeline(
        input_path=extraction_dir,
        output_dir=output_dir,
        config=AnalysisConfig(enable_llm_fallback=False),
    ).run()
    return result_path


def load_account_number_map(extraction_dir: Path) -> dict[str, str]:
    """Map the pipeline's analysis account id (source_account_id) -> real account number."""
    clean_path = extraction_dir / "clean_transactions.csv"
    mapping: dict[str, str] = {}
    if not clean_path.exists():
        return mapping
    frame = pd.read_csv(clean_path, dtype=str).fillna("")
    if "source_account_id" not in frame.columns or "account_number" not in frame.columns:
        return mapping
    for row in frame[["source_account_id", "account_number"]].drop_duplicates().itertuples(index=False):
        mapping[str(row.source_account_id)] = norm_acct(row.account_number)
    return mapping


def load_utr_account_map(extraction_dir: Path) -> dict[str, set[str]]:
    """Map each reference/UTR string seen in the statements -> the real account numbers
    whose rows carry it. Lets the scorer recover expected accounts even when a TXT/PDF
    statement did not print a parseable account number (identity gap)."""
    clean_path = extraction_dir / "clean_transactions.csv"
    utr_map: dict[str, set[str]] = {}
    if not clean_path.exists():
        return utr_map
    frame = pd.read_csv(clean_path, dtype=str).fillna("")
    number_col = "account_number" if "account_number" in frame.columns else "Account_ID"
    text_cols = [
        c for c in ("Reference_Number", "Transaction_Reference", "Transaction_ID", "Narration", "reference")
        if c in frame.columns
    ]
    if number_col not in frame.columns or not text_cols:
        return utr_map
    for row in frame.itertuples(index=False):
        number = norm_acct(getattr(row, number_col, ""))
        if not number:
            continue
        blob = " ".join(str(getattr(row, c, "")) for c in text_cols)
        # index the whole-token references so the scorer can look up an exact UTR quickly
        for token in blob.replace("/", " ").replace("-", " ").split():
            if len(token) >= 6 and any(ch.isdigit() for ch in token):
                utr_map.setdefault(token, set()).add(number)
    return utr_map


def run_fixture(folder: Path, session_prefix: str, force: bool) -> dict[str, Any]:
    """Run extraction + analysis for one fixture folder and return everything the scorer needs."""
    session_id = f"{session_prefix}_{folder.name}"
    extraction_dir = run_extraction(folder, session_id, force)
    analysis_dir = ROOT / "analysis" / "outputs" / session_id
    result_path = run_analysis(extraction_dir, analysis_dir, force)
    return {
        "folder": folder,
        "truth": load_truth(folder),
        "analysis": json.loads(result_path.read_text(encoding="utf-8")),
        "account_number_map": load_account_number_map(extraction_dir),
        "utr_account_map": load_utr_account_map(extraction_dir),
        "extraction_dir": str(extraction_dir),
        "analysis_dir": str(analysis_dir),
    }
