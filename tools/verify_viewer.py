"""
verify_viewer.py — LOCAL-ONLY verification viewer for the extraction phase.

⚠️  This is an internal demo aid. It is GIT-IGNORED (see .gitignore: `tools/`)
    and must NEVER be committed or pushed. Its only job is to make the extraction
    VISIBLE so the team and the judges can trust it.

WHAT IT DOES (Problem 4a):
    Point it at a folder of bank statements, click Run, and SEE on screen, per file:
      • which route the file took (CSV / digital PDF / scanned / image)
      • which OCR engine read it (Tesseract or Groq Vision) and at what confidence
      • the column map Groq returned — and whether it came from Groq, cache, or a fallback
      • the raw extracted text
      • the final clean transaction table
      • the rows flagged for manual review (never dropped silently)

HOW TO RUN (locally only):
    streamlit run tools/verify_viewer.py

Everything stays on this machine. Nothing is uploaded anywhere.

Team: Survey Corps | CIDECODE Hackathon 2026 | CID Karnataka
"""

import re
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

# Make the project importable when Streamlit runs this file directly.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from extraction.extraction_pipeline import run_extraction_pipeline
from extraction.router import route_file
from extraction.extractor_digital_pdf import extract_text_from_digital_pdf
from extraction.extractor_docx import extract_text_from_docx
from extraction.extractor_excel_csv import extract_dataframe_from_excel_csv
from extraction.extractor_ocr import extract_text_with_ocr_audit

DATASET = PROJECT_ROOT / "synthetic_dataset_full_mentoring"
SUPPORTED = (".pdf", ".xlsx", ".xls", ".csv", ".docx", ".jpg", ".jpeg", ".png")
# NOTE: the reference files in synthetic_dataset_full_mentoring/ (accounts_master,
# transactions_master, ground_truth, case_briefs) are for MANUAL verification only
# and are intentionally never read by this tool or the pipeline.


def file_ref_from_name(name: str) -> str:
    """
    A per-file traceback handle from the filename. This is NOT the account identity
    (that is read from the document content) — just a label so rows are traceable.
    """
    m = re.match(r"(ACC\d+)", Path(name).name)
    return m.group(1) if m else Path(name).stem


def raw_text_for_display(file_path: str, max_ocr_pages: int) -> str:
    """Re-extracts the raw text/preview for a single file, just for on-screen display."""
    route = route_file(file_path)
    if route == "pdf_digital":
        return extract_text_from_digital_pdf(file_path)
    if route in ("pdf_scanned", "image"):
        text, _ = extract_text_with_ocr_audit(file_path, max_pages=max_ocr_pages)
        return text
    if route == "docx":
        return extract_text_from_docx(file_path)
    if route == "excel_csv":
        df = extract_dataframe_from_excel_csv(file_path, "preview", "preview")
        return df.head(40).to_csv(index=False)
    return "(no preview available)"


# ─────────────────────────────────────────────────────────────────────────────
# UI
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Survey Corps — Extraction Verification", layout="wide")
st.title("🔍 Extraction Verification Viewer")
st.caption("Local-only demo tool. Nothing leaves this machine. Not committed to git.")

with st.sidebar:
    st.header("Run settings")
    # Two ways to feed the viewer: UPLOAD files (what you asked for) or point it
    # at a folder of statements already on disk.
    mode = st.radio("Input mode", ["Upload files", "Folder on disk"], index=0)
    if mode == "Upload files":
        uploaded = st.file_uploader(
            "Upload bank statements (PDF, JPG/PNG, DOCX, Excel, CSV)",
            type=["pdf", "jpg", "jpeg", "png", "docx", "xlsx", "xls", "csv"],
            accept_multiple_files=True,
        )
        folder = None
    else:
        uploaded = None
        folder = st.text_input("Folder of statements", value=str(DATASET / "statements" / "csv"))
    max_files = st.number_input("Max files (keep small / bounded)", 1, 50, 5)
    max_ocr_pages = st.number_input("Max OCR pages per scanned PDF", 1, 50, 3)
    run = st.button("▶ Run extraction", type="primary")

# A local folder to hold uploaded files for this run (git-ignored uploads/).
UPLOAD_DIR = PROJECT_ROOT / "uploads"

if run:
    chosen = []  # list of Path objects to process

    if mode == "Upload files":
        if not uploaded:
            st.warning("Upload at least one file in the sidebar first.")
            st.stop()
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        # Save each uploaded file to disk so the extractors can open it by path.
        for uf in uploaded[: int(max_files)]:
            dest = UPLOAD_DIR / uf.name
            dest.write_bytes(uf.getbuffer())
            chosen.append(dest)
    else:
        folder_path = Path(folder)
        if not folder_path.exists():
            st.error(f"Folder not found: {folder}")
            st.stop()
        all_files = sorted(p for p in folder_path.iterdir() if p.suffix.lower() in SUPPORTED)
        chosen = all_files[: int(max_files)]
        if not chosen:
            st.warning("No supported statement files found in that folder.")
            st.stop()

    # bank_name is just a hint; the real identity is read from each document.
    files = [{
        "file_path": str(p),
        "account_id": file_ref_from_name(p.name),
        "bank_name": "",
    } for p in chosen]

    st.info(f"Processing {len(files)} file(s): " + ", ".join(p.name for p in chosen))

    with st.spinner("Running extraction pipeline..."):
        result = run_extraction_pipeline(
            files, session_id="viewer_session",
            ingest_to_chromadb=False, max_ocr_pages=int(max_ocr_pages), persist=True,
        )

    # ── Run-level summary ─────────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Clean rows", result["clean_rows"])
    c2.metric("Flagged rows", result["flagged_rows"])
    c3.metric("Files processed", result["files_processed"])
    c4.metric("Files failed", len(result["files_failed"]))
    if result.get("storage_paths"):
        st.success(f"Saved to: {result['storage_paths']['folder']}")

    # ── Per-file visibility ───────────────────────────────────────────────────
    st.header("Per-file detail")
    for rec, fmeta in zip(result["per_file"], files):
        with st.expander(f"📄 {rec['file']}  —  route: {rec.get('route', rec.get('status'))}", expanded=True):
            # Real account identity read from the document content (Problems 2 & 4).
            st.subheader("Account details (read from the statement)")
            st.json(rec.get("account_details", {}))

            cols = st.columns(2)
            with cols[0]:
                st.subheader("Column map")
                st.json(rec.get("column_map", {"note": "vision model returned structured rows"}))
                src = rec.get("column_map_source", "n/a")
                badge = {"groq": "🟢 live Groq call", "cache": "🔵 cached Groq answer",
                         "fallback": "🔴 FALLBACK GUESS (Groq failed)", "empty": "⚪ no text"}.get(src, src)
                st.write(f"**Source:** {badge}")
                st.subheader("OCR engine")
                ocr = rec.get("ocr", "n/a")
                # st.json() chokes on a plain string like "n/a"; only use it for dicts.
                if isinstance(ocr, dict):
                    st.json(ocr)
                else:
                    st.write(f"`{ocr}` (text/table source — no OCR needed)")
            with cols[1]:
                st.subheader("Raw extracted text (preview)")
                txt = raw_text_for_display(fmeta["file_path"], int(max_ocr_pages))
                st.text_area("raw_text", value=txt[:4000], height=240, label_visibility="collapsed")

            # Rows are stamped with the REAL account number (Account_ID column),
            # so filter this statement's rows by the number we read from it.
            acc = (rec.get("account_details", {}) or {}).get("account_number", "")
            st.subheader("Clean transactions for this account")
            clean = result["clean_df"]
            if acc and "Account_ID" in clean.columns:
                st.dataframe(clean[clean["Account_ID"] == acc].head(200), use_container_width=True)
            else:
                st.dataframe(clean.head(200), use_container_width=True)

            flagged = result["flagged_df"]
            if not flagged.empty and "Account_ID" in flagged.columns and acc:
                acc_flagged = flagged[flagged["Account_ID"] == acc]
                if not acc_flagged.empty:
                    st.subheader("⚠️ Flagged for manual review")
                    st.dataframe(acc_flagged.head(200), use_container_width=True)
else:
    st.write("Set a folder in the sidebar and click **Run extraction**.")
