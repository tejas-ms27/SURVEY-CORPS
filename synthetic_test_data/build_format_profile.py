#!/usr/bin/env python3
"""Build a PII-safe structural profile of every CID statement source file."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


SUPPORTED = {".pdf", ".csv", ".xlsx", ".xls", ".txt"}
HEADER_WORDS = re.compile(
    r"(?i)\b(date|dt|narration|description|particulars?|withdrawals?|deposits?|"
    r"debits?|credits?|balance|amount|value|cheque|chq|reference|ref|txn|tran|transaction)\b"
)
SAFE_HEADER_LABELS = [
    "Account Name", "Account No", "Account Number", "ACCOUNT NO", "Customer Name",
    "Branch", "Branch Name", "IFSC", "IFSC Code", "Statement Period", "From Date",
    "To Date", "Date of Statement", "Account Opening Date", "Currency", "Product",
    "Available Balance", "Opening Balance", "Closing Balance", "Account Status",
]
SAFE_FOOTER_MARKERS = [
    "computer generated", "end of statement", "page", "registered office",
    "this is a system generated", "disclaimer", "closing balance",
]
PREFIX_PATTERNS = {
    "UPI/": r"\bUPI/", "UPI-": r"\bUPI-", "NEFT/": r"\bNEFT/", "NEFT-": r"\bNEFT-",
    "NEFT*": r"\bNEFT\*", "IMPS/": r"\bIMPS/", "IMPS-": r"\bIMPS-", "RTGS/": r"\bRTGS/",
    "RTGS-": r"\bRTGS-", "ATM/": r"\bATM/", "ATM-CASH": r"\bATM[- ]CASH",
    "CHQ": r"\bCHQ\b", "CASH DEPOSIT": r"\bCASH DEPOSIT\b", "POS/": r"\bPOS/",
    "ACH/": r"\bACH/", "NACH": r"\bNACH\b", "SALARY": r"\bSALARY\b",
}
DATE_PATTERNS = {
    "DD/MM/YYYY": r"\b(?:0?[1-9]|[12]\d|3[01])/(?:0?[1-9]|1[0-2])/\d{4}\b",
    "DD-MM-YYYY": r"\b(?:0?[1-9]|[12]\d|3[01])-(?:0?[1-9]|1[0-2])-\d{4}\b",
    "DD-Mon-YYYY": r"\b(?:0?[1-9]|[12]\d|3[01])-[A-Za-z]{3}-\d{4}\b",
    "DD-Mon-YY": r"\b(?:0?[1-9]|[12]\d|3[01])-[A-Za-z]{3}-\d{2}\b",
    "YYYY-MM-DD": r"\b\d{4}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12]\d|3[01])\b",
    "DD/MM/YY": r"\b(?:0?[1-9]|[12]\d|3[01])/(?:0?[1-9]|1[0-2])/\d{2}\b",
    "DD-MM-YY": r"\b(?:0?[1-9]|[12]\d|3[01])-(?:0?[1-9]|1[0-2])-\d{2}\b",
}


def source_id(path: Path, root: Path) -> str:
    rel = str(path.relative_to(root)).replace("\\", "/")
    return hashlib.sha256(rel.encode("utf-8")).hexdigest()[:16]


def safe_labels(text: str) -> list[str]:
    found = []
    for label in SAFE_HEADER_LABELS:
        if re.search(rf"(?i)(?<![A-Za-z]){re.escape(label)}(?![A-Za-z])", text):
            found.append(label)
    return sorted(set(found), key=str.lower)


def split_pdf_header(line: str) -> list[str]:
    parts = [x.strip(" :-") for x in re.split(r"\s{2,}|\t+|\|", line) if x.strip(" :-")]
    return [x for x in parts if len(x) <= 45 and HEADER_WORDS.search(x)]


def read_pdf(path: Path) -> dict[str, Any]:
    cp = subprocess.run(
        ["pdftotext", "-layout", str(path), "-"], capture_output=True, text=True,
        errors="replace", timeout=90, check=False,
    )
    text = cp.stdout
    pages = max(1, text.count("\f"))
    lines = [x.rstrip() for x in text.splitlines()]
    candidates = [(len(HEADER_WORDS.findall(x)), x) for x in lines if len(HEADER_WORDS.findall(x)) >= 3]
    columns = split_pdf_header(max(candidates, default=(0, ""), key=lambda x: (x[0], -len(x[1])))[1])
    normalized_header = " | ".join(columns)
    repeated = sum(1 for _, line in candidates if split_pdf_header(line) == columns) if columns else 0
    return {
        "text": text,
        "columns": columns,
        "pages": pages,
        "text_layer": len(re.sub(r"\s", "", text)) >= 100,
        "page_header_repeated": repeated > 1,
        "header_signature": normalized_header,
    }


def sniff_delimiter(path: Path) -> str:
    sample = path.read_bytes()[:8192].decode("utf-8-sig", errors="replace")
    try:
        return csv.Sniffer().sniff(sample, delimiters=",\t;|").delimiter
    except csv.Error:
        return "\t" if sample.count("\t") > sample.count(",") else ","


def read_tabular(path: Path) -> dict[str, Any]:
    ext = path.suffix.lower()
    delimiter = None
    if ext == ".csv":
        delimiter = sniff_delimiter(path)
        for encoding in ("utf-8-sig", "cp1252", "latin1"):
            try:
                frame = pd.read_csv(path, header=None, sep=delimiter, dtype=str, encoding=encoding,
                                    on_bad_lines="skip", nrows=80)
                break
            except Exception:
                frame = None
        if frame is None:
            raise ValueError("unable to parse CSV")
    else:
        frame = pd.read_excel(path, header=None, dtype=str, nrows=80)
    best: tuple[int, list[str]] = (0, [])
    all_text = []
    for row in frame.itertuples(index=False, name=None):
        cells = [str(x).strip() for x in row if pd.notna(x) and str(x).strip() not in {"", "nan"}]
        all_text.extend(cells)
        score = sum(bool(HEADER_WORDS.search(x.replace("_", " ").replace("-", " "))) and len(x) <= 60 for x in cells)
        if score > best[0]:
            best = (score, cells)
    columns = [x for x in best[1] if len(x) <= 60] if best[0] >= 3 else []
    return {"text": "\n".join(all_text), "columns": columns, "delimiter": delimiter}


def read_txt(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="replace")
    candidates = [(len(HEADER_WORDS.findall(x)), x) for x in text.splitlines() if len(HEADER_WORDS.findall(x)) >= 3]
    line = max(candidates, default=(0, ""), key=lambda x: x[0])[1]
    return {"text": text, "columns": split_pdf_header(line), "fixed_width": bool(re.search(r"\s{3,}", line))}


def format_details(path: Path) -> dict[str, Any]:
    if path.suffix.lower() == ".pdf":
        return read_pdf(path)
    if path.suffix.lower() in {".csv", ".xlsx", ".xls"}:
        return read_tabular(path)
    return read_txt(path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path, default=Path(__file__).with_name("format_profile.json"))
    args = parser.parse_args()
    root = args.root.resolve()
    files = sorted(p for folder in (root / "primary", root / "Secondary")
                   for p in folder.iterdir() if p.is_file() and p.suffix.lower() in SUPPORTED)
    scans: list[dict[str, Any]] = []
    errors = []
    for path in files:
        sid = source_id(path, root)
        try:
            details = format_details(path)
            text = details.pop("text")
            date_formats = [name for name, regex in DATE_PATTERNS.items() if re.search(regex, text)]
            prefixes = [name for name, regex in PREFIX_PATTERNS.items() if re.search(regex, text, re.I)]
            footers = [x for x in SAFE_FOOTER_MARKERS if x in text.lower()]
            scans.append({
                "source_id": sid, "source_set": path.parent.name.lower(), "format": path.suffix.lower()[1:],
                "columns": details.pop("columns", []), "header_labels": safe_labels(text),
                "date_formats": date_formats, "narration_prefixes": prefixes,
                "footer_markers": footers, **details,
            })
        except Exception as exc:
            errors.append({"source_id": sid, "format": path.suffix.lower()[1:], "error": type(exc).__name__})

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for scan in scans:
        key_material = json.dumps({
            "format": scan["format"], "columns": scan["columns"],
            "delimiter": scan.get("delimiter"), "fixed_width": scan.get("fixed_width"),
            "text_layer": scan.get("text_layer"),
        }, sort_keys=True)
        grouped[hashlib.sha256(key_material.encode()).hexdigest()[:12]].append(scan)

    templates = []
    for n, (fingerprint, members) in enumerate(sorted(grouped.items()), 1):
        representative = members[0]
        template = {
            "template_id": f"OBS_{representative['format'].upper()}_{n:03d}",
            "fingerprint": fingerprint,
            "format": representative["format"],
            "source_count": len(members),
            "source_ids": [x["source_id"] for x in members],
            "columns_in_observed_order": representative["columns"],
            "header_labels_observed": sorted(set(y for x in members for y in x["header_labels"])),
            "date_formats_observed": sorted(set(y for x in members for y in x["date_formats"])),
            "narration_prefixes_observed": sorted(set(y for x in members for y in x["narration_prefixes"])),
            "balance_behavior": "separate_debit_credit_with_running_balance"
                if any(re.search(r"(?i)(debit|withdraw)", c) for c in representative["columns"])
                and any(re.search(r"(?i)(credit|deposit)", c) for c in representative["columns"])
                and any(re.search(r"(?i)balance", c) for c in representative["columns"])
                else "not_determined_from_header",
            "footer_markers_observed": sorted(set(y for x in members for y in x["footer_markers"])),
        }
        for key in ("delimiter", "fixed_width", "text_layer", "page_header_repeated"):
            if key in representative:
                template[key] = representative[key]
        if representative["format"] == "pdf":
            template["pdf_page_counts"] = sorted(set(x["pages"] for x in members))
            template["pdf_extraction_mode"] = "text_layer" if representative["text_layer"] else "ocr_required_or_low_text"
        templates.append(template)
        for member in members:
            member["template_id"] = template["template_id"]

    generated_templates: dict[str, str | None] = {}
    desired_headers = {
        "pdf": ["Date", "Narration", "Chq/Ref No", "Withdrawal (Dr)", "Deposit(Cr)", "Balance"],
        "csv": ["TRAN-DATE", "TRAN_PARTICULAR", "CHQ-NUM", "WITHDRAWAL", "DEPOSIT", "BALANCE"],
        "xlsx": ["Ac_No", "AC_Name", "Tran_ID", "Tran_Date", "Tran_Type", "Sub_Type", "Inst_Type",
                 "Inst_Num", "Dr_Amt", "Cr_Amt", "Balance", "Rmks", "Narration", "pstd_dt", "Crncy",
                 "value_dt", "mkr_emp_id", "chk_emp_id"],
        "txt": ["Trans Dt Value Dt Transn ID", "Transaction Particulars", "Debit", "Credit", "Balance"],
    }
    for fmt, wanted in desired_headers.items():
        generated_templates[fmt] = next(
            (x["template_id"] for x in templates if x["format"] == fmt
             and [c.casefold() for c in x["columns_in_observed_order"]] == [c.casefold() for c in wanted]),
            None,
        )
    profile = {
        "schema_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "privacy": "PII-safe: source filenames and field values are excluded; source_id is SHA-256(path) prefix.",
        "scan_scope": {"folders": ["primary", "Secondary"], "supported_formats": sorted(SUPPORTED),
                       "files_discovered": len(files), "files_profiled": len(scans), "errors": errors,
                       "format_counts": dict(sorted(Counter(x["format"] for x in scans).items()))},
        "templates": templates,
        "source_coverage": [{k: x[k] for k in ("source_id", "source_set", "format", "template_id")} for x in scans],
        "generator_template_selection": generated_templates,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(profile, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Profiled {len(scans)}/{len(files)} files into {len(templates)} templates; errors={len(errors)}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
