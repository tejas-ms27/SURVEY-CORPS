"""
verify_batch.py — Post-batch verification (final-fix prompt Sections 4.1 + 5).

Given a batch output folder, prints the Section-5 12-point checklist with REAL
numbers and applies the Section 4.1 balance_mismatch gate. Targets are passed in
per scope (Secondary / Primary / Full-162) so nothing is hardcoded to a file.

Usage:
    python3 tools/verify_batch.py outputs/extractions/batch_secondary --scope secondary
"""
import argparse
import json
import sys
from pathlib import Path

# GT targets per scope (from ground_truth.md / source_inventory.json — counts only).
TARGETS = {
    "secondary": {"rows": 190691, "acct": (142, 144), "holder": (139, 144), "ifsc": (106, 144),
                  "true_zero": 2, "files": 144},
    "primary":   {"rows": None,   "acct": None, "holder": None, "ifsc": None, "files": 18},
    "full":      {"rows": 205455, "acct": (142, 162), "holder": (139, 162), "ifsc": (106, 162),
                  "files": 162},
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("folder")
    ap.add_argument("--scope", choices=list(TARGETS), required=True)
    args = ap.parse_args()
    folder = Path(args.folder)
    rep = json.loads((folder / "extraction_summary_report.json").read_text())
    led = json.loads((folder / "extraction_ledger.json").read_text())
    tgt = TARGETS[args.scope]

    t = rep["totals"]
    clean, flagged = t["transactions_clean"], t["transactions_flagged"]
    total = clean + flagged
    fb = rep.get("flag_breakdown", {})
    bm = fb.get("balance_mismatch", 0)
    mq = rep["metadata_quality"]
    rec = rep["reconciliation"]

    zr = [l for l in led if l["rows_extracted"] == 0]
    zr_true = [l for l in zr if l["zero_row_status"] == "true_zero"]
    zr_func = [l for l in zr if l["zero_row_status"] in ("functional_failure", "technical_failure")]
    fallbacks = {}
    for l in led:
        m = l.get("fallback_method_used") or l.get("parser_tier") or "?"
        if "fallback" in str(m) or "repair" in str(m):
            fallbacks[m] = fallbacks.get(m, 0) + 1

    def line(ok, label, got, want=""):
        mark = "PASS" if ok else "FAIL" if ok is False else "----"
        w = f"  (target {want})" if want != "" else ""
        print(f"  [{mark}] {label:34s} {got}{w}")

    print(f"\n{'='*64}\nSECTION 5 — 12-POINT CHECKLIST   scope={args.scope}  folder={folder.name}\n{'='*64}")
    line(t["files_processed"] == tgt["files"], "1. files processed", t["files_processed"], tgt["files"])
    rows_ok = (abs(total - tgt["rows"]) / tgt["rows"] < 0.02) if tgt["rows"] else None
    line(rows_ok, "2. total rows", f"{total:,}", f"~{tgt['rows']:,}" if tgt["rows"] else "n/a")
    line(None, "3. clean / flagged", f"{clean:,} / {flagged:,}")
    a, h, i = mq["with_account_number"], mq["with_holder_name"], mq["with_ifsc"]
    line(tgt["acct"] and a >= tgt["acct"][0], "4. account_number found", f"{a}/{mq['graded_files']}",
         f"{tgt['acct'][0]}/{tgt['acct'][1]}" if tgt["acct"] else "")
    line(tgt["holder"] and h >= tgt["holder"][0], "5. holder found", f"{h}/{mq['graded_files']}",
         f"{tgt['holder'][0]}/{tgt['holder'][1]}" if tgt["holder"] else "")
    line(tgt["ifsc"] and i >= tgt["ifsc"][0], "6. IFSC found", f"{i}/{mq['graded_files']}",
         f"{tgt['ifsc'][0]}/{tgt['ifsc'][1]}" if tgt["ifsc"] else "")
    line(None, "7. avg reconciliation", rec["average"])
    line(None, "8. files below 0.90", len(rec["files_below_0.90"]))
    line(None, "9. zero-row files", f"{len(zr)} ({len(zr_true)} true / {len(zr_func)} functional)")
    line(len(zr_func) == 0, "10. NO functional zero-rows", len(zr_func), 0)
    line(None, "11. fallbacks fired", dict(fallbacks))
    print(f"\n{'='*64}\nSECTION 4.1 — balance_mismatch GATE\n{'='*64}")
    line(bm == 0, "12. balance_mismatch == 0", bm, 0)
    if bm:
        md = rep.get("mismatch_diagnosis", {})
        print(f"        diagnosis: {md}")
    print(f"\n  flag_breakdown: {fb}")
    print(f"  GATE {'OPEN (balance_mismatch=0)' if bm == 0 else f'BLOCKED ({bm} balance_mismatch flags)'}\n")
    return 0 if bm == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
