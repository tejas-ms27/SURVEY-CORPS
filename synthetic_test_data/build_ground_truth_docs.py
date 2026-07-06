"""
Build human-readable ground truth documentation.

Task 1: Generate GROUND_TRUTH.md in every pattern/clean_control folder.
Task 2: Create ground_truth/investigations/ with 6 investigation case files.

Does NOT touch any statement files or generation logic.
"""

import json
import csv
import pathlib
import textwrap
from datetime import date

try:
    import openpyxl
    HAS_OPENPYXL = True
except ImportError:
    HAS_OPENPYXL = False

try:
    import pdfplumber
    HAS_PDFPLUMBER = True
except ImportError:
    HAS_PDFPLUMBER = False

BASE = pathlib.Path(__file__).parent

# ──────────────────────────────────────────────────────────────────────────────
# Statement reader – returns list of dicts with keys:
#   date, narration, ref, debit, credit, balance
# ──────────────────────────────────────────────────────────────────────────────

def _parse_date(s: str) -> str:
    for fmt in ("%d-%m-%Y", "%d/%m/%Y", "%Y-%m-%d", "%d-%b-%Y", "%d %b %Y"):
        try:
            from datetime import datetime
            return datetime.strptime(s.strip(), fmt).strftime("%d-%m-%Y")
        except ValueError:
            pass
    return s.strip()


def _money(s: str) -> str:
    v = str(s).strip().replace(",", "")
    if not v or v in ("-", "nil", ""):
        return ""
    try:
        return f"{float(v):,.2f}"
    except ValueError:
        return s.strip()


def read_csv(path: pathlib.Path) -> list[dict]:
    rows = []
    with path.open(encoding="utf-8-sig", newline="") as fh:
        all_lines = fh.readlines()

    # Skip metadata header block (Bank Name / Account Number / etc.) and find
    # the first line that looks like actual transaction column headers.
    _META_KEYS = {"bank name", "account number", "account holder name",
                  "branch", "ifsc code", "statement period"}
    skip = 0
    for i, line in enumerate(all_lines):
        first_cell = line.split(",")[0].strip().lower().strip('"')
        if first_cell in _META_KEYS or first_cell == "":
            skip = i + 1
        else:
            break

    import io
    reader = csv.DictReader(io.StringIO("".join(all_lines[skip:])))
    for r in reader:
        keys = [k for k in r.keys() if k is not None]
        # Detect column positions heuristically
        date_col = next((k for k in keys if "date" in k.lower() or "dt" in k.lower()), keys[0] if keys else "")
        narr_col = next((k for k in keys if any(x in k.lower() for x in ["narr", "particular", "description", "detail", "transact"])), keys[1] if len(keys) > 1 else "")
        ref_col  = next((k for k in keys if any(x in k.lower() for x in ["chq", "ref", "cheque", "tran id", "transn id", "utr", "ins"])), "")
        dr_col   = next((k for k in keys if any(x in k.lower() for x in ["debit", "withdrawal", "dr", "debit amount"])), "")
        cr_col   = next((k for k in keys if any(x in k.lower() for x in ["credit", "deposit", "cr", "credit amount"])), "")
        bal_col  = next((k for k in keys if "balance" in k.lower() or "bal" in k.lower()), "")
        rows.append({
            "date":     _parse_date(r.get(date_col, "")),
            "narration": r.get(narr_col, "").strip(),
            "ref":      r.get(ref_col, "").strip() if ref_col else "",
            "debit":    _money(r.get(dr_col, "")) if dr_col else "",
            "credit":   _money(r.get(cr_col, "")) if cr_col else "",
            "balance":  _money(r.get(bal_col, "")) if bal_col else "",
        })
    return rows


def read_xlsx(path: pathlib.Path) -> list[dict]:
    if not HAS_OPENPYXL:
        return []
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb.active
    rows_raw = list(ws.iter_rows(values_only=True))
    if not rows_raw:
        return []
    # Find header row
    hdr_idx = 0
    for i, row in enumerate(rows_raw[:10]):
        cells = [str(c).lower() if c else "" for c in row]
        if any("date" in c or "narr" in c or "particular" in c for c in cells):
            hdr_idx = i
            break
    headers = [str(c).lower().strip() if c else f"col{j}" for j, c in enumerate(rows_raw[hdr_idx])]

    def col(keys):
        for k in keys:
            for j, h in enumerate(headers):
                if k in h:
                    return j
        return -1

    di = col(["date", "tran date", "tran_date"])
    ni = col(["narr", "particular", "description", "tran particular"])
    ri = col(["chq", "ref", "tran id", "transn id", "utr", "ins", "cheque"])
    dri = col(["debit", "withdrawal", "dr"])
    cri = col(["credit", "deposit", "cr"])
    bi = col(["balance", "bal"])

    result = []
    for row in rows_raw[hdr_idx + 1:]:
        if not any(row):
            continue
        def gc(i):
            return str(row[i]).strip() if i >= 0 and i < len(row) and row[i] is not None else ""
        result.append({
            "date":      _parse_date(gc(di)) if di >= 0 else "",
            "narration": gc(ni),
            "ref":       gc(ri),
            "debit":     _money(gc(dri)) if dri >= 0 else "",
            "credit":    _money(gc(cri)) if cri >= 0 else "",
            "balance":   _money(gc(bi)) if bi >= 0 else "",
        })
    wb.close()
    return result


def read_txt(path: pathlib.Path) -> list[dict]:
    rows = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line.startswith("|") or "Trans Dt" in line or "---" in line:
                continue
            parts = [p.strip() for p in line.strip("|").split("|")]
            if len(parts) < 7:
                continue
            rows.append({
                "date":      _parse_date(parts[0]),
                "narration": parts[3],
                "ref":       parts[2],
                "debit":     parts[5],
                "credit":    parts[6],
                "balance":   parts[7] if len(parts) > 7 else "",
            })
    return rows


def read_pdf(path: pathlib.Path) -> list[dict]:
    if not HAS_PDFPLUMBER:
        return []
    rows = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            for line in text.split("\n"):
                parts = line.split()
                if len(parts) < 4:
                    continue
                # Heuristic: first token looks like DD-MM-YYYY
                import re
                if re.match(r"\d{2}[-/]\d{2}[-/]\d{4}", parts[0]):
                    rows.append({
                        "date":      _parse_date(parts[0]),
                        "narration": " ".join(parts[1:-3]),
                        "ref":       "",
                        "debit":     parts[-3] if parts[-3].replace(",","").replace(".","").isdigit() else "",
                        "credit":    parts[-2] if parts[-2].replace(",","").replace(".","").isdigit() else "",
                        "balance":   parts[-1] if parts[-1].replace(",","").replace(".","").isdigit() else "",
                    })
    return rows


def read_statement(path: pathlib.Path) -> list[dict]:
    ext = path.suffix.lower()
    if ext == ".csv":
        return read_csv(path)
    elif ext == ".xlsx":
        return read_xlsx(path)
    elif ext == ".txt":
        return read_txt(path)
    elif ext == ".pdf":
        return read_pdf(path)
    return []


def find_tx(rows: list[dict], ref: str) -> dict | None:
    ref = ref.strip()
    for r in rows:
        if ref and ref in r.get("ref", ""):
            return r
        if ref and ref in r.get("narration", ""):
            return r
    return None


# ──────────────────────────────────────────────────────────────────────────────
# TASK 1 – GROUND_TRUTH.md per pattern folder
# ──────────────────────────────────────────────────────────────────────────────

PATTERN_DESCRIPTIONS = {
    1:  "Detects when the exact same transaction row appears twice in a statement. Both rows share the same reference number, amount, and narration — evidence of a processing error or deliberate manipulation.",
    2:  "Detects a debit transaction that is subsequently reversed by a matching credit of the same amount. Often seen in fraudulent transfer attempts that are caught and reversed, or in fee exploitation schemes.",
    3:  "Detects accounts that receive credits from multiple unrelated sources and rapidly forward the funds onward, retaining little residual balance. Characteristic of money mule or pass-through accounts.",
    4:  "Detects rapid accumulation of funds from multiple senders within a short window, consistent with a pooling account aggregating proceeds before onward disbursement.",
    5:  "Detects a pattern of cash deposits each staying just below the ₹50,000 reporting threshold. Consistent with deliberate structuring to evade currency transaction reporting obligations.",
    7:  "Detects a closed-loop flow where funds originate from Account A, pass through one or more intermediaries, and eventually return to Account A, indicating layering or wash transactions.",
    8:  "Detects a corroborated multi-hop fund movement where the same UTR/reference number appears as a debit in the sender's statement and a credit in the receiver's statement.",
    9:  "Detects a large inward credit (NEFT/IMPS/UPI) followed within a short window by one or more ATM withdrawals of a near-equivalent total amount, suggesting rapid cash-out of proceeds.",
    10: "Detects the same bank reference or UTR number appearing across two independent account statements from different account holders, confirming a cross-account money movement.",
    11: "Detects a large credit that remains substantially unspent in an account for an extended period, suggesting the account is being used as a parking vehicle rather than for normal commerce.",
    12: "Detects a central hub account that receives funds from an unusually large number of distinct sender accounts within the analysis window, a hallmark of mule network aggregation.",
    13: "Detects reciprocal micro-transfers (₹1–₹50) flowing in both directions between two accounts, a classic account validation or channel-testing technique used before large fraud transfers.",
    14: "Detects clusters of UPI debit transactions each followed by a matching reversal credit, repeating across multiple cycles, suggesting systematic reversal exploitation.",
    15: "Detects clusters of outward transfers in round rupee values (multiples of ₹5,000 or ₹10,000) occurring in the same period as non-round routine spending, inconsistent with normal behaviour.",
    16: "Detects the same UPI handle or beneficiary identifier appearing across two or more separate account statements, linking accounts that are nominally unrelated.",
    17: "Detects a round-trip pattern where funds sent from Account A reach Account B via an intermediary and are subsequently returned to Account A through a different channel.",
    18: "Detects a long period of dormancy (no transactions) followed by a sudden burst of high-value activity, consistent with account reactivation for fraud use.",
    19: "Detects a large-value transfer (RTGS/IMPS/NEFT) where the two parties have no prior transaction history, indicating a first-ever contact that is immediately high value.",
    22: "Safety-net trigger for anomalous spending patterns that evade rule-based detectors. LLM analysis surfaces these via semantic understanding of narration sequences.",
    23: "Safety-net trigger using ensemble ML signals (isolation forest, auto-encoder) to surface statistical anomalies that match no named rule pattern.",
}

SEVERITY_MAP = {
    "strong":     "HIGH",
    "weak":       "MEDIUM",
    "safety_net": "LOW (Safety Net — no named rule match)",
}

NON_FINDING_PATTERN_NAMES = {
    1: "duplicate_verification", 2: "failed_reversed_transaction",
    3: "pass_through_routing", 4: "fund_pooling", 5: "structuring_smurfing",
    7: "circular_flow", 8: "money_trail", 9: "credit_to_cash_out",
    10: "cross_statement_links", 11: "balance_parking", 12: "hub_ranking",
    13: "low_value_testing", 14: "reversal_clusters", 15: "round_value_debit",
    16: "shared_upi", 17: "round_trip", 18: "dormant_reactivation",
    19: "first_contact_large_transfer", 22: "llm_lead_unknown_shape",
    23: "ml_ensemble_unknown_shape",
}


def build_ground_truth_md(folder_path: pathlib.Path) -> str:
    gt_path = folder_path / "ground_truth.json"
    if not gt_path.exists():
        return ""
    with gt_path.open() as f:
        gt = json.load(f)

    folder_name = gt["folder"]
    description = gt.get("description", "")
    findings = gt.get("expected_findings", [])
    non_findings = gt.get("expected_non_findings", [])
    accounts = gt.get("accounts", [])

    # Build synthetic_id → account mapping
    acct_by_id = {a["synthetic_account_id"]: a for a in accounts}

    # Pre-load statement rows for every account
    stmt_rows: dict[str, list[dict]] = {}
    for acct in accounts:
        file_rel = acct.get("file", "")
        p = folder_path / file_rel
        # Also try without 'statements/' prefix
        if not p.exists():
            p = folder_path / "statements" / pathlib.Path(file_rel).name
        if p.exists():
            stmt_rows[acct["synthetic_account_id"]] = read_statement(p)
        else:
            stmt_rows[acct["synthetic_account_id"]] = []

    lines = []

    # Title
    # Derive pattern number and name from folder
    if folder_name.startswith("pattern_"):
        parts = folder_name.split("_", 2)
        pat_num = parts[1]
        pat_label = " ".join(w.capitalize() for w in parts[2:])
        lines.append(f"# Pattern {pat_num} — {pat_label}")
    elif folder_name == "clean_control":
        lines.append("# Clean Control — Negative Baseline")
    elif folder_name == "combined_all_patterns":
        lines.append("# Combined All Patterns — Full Regression Set")
    else:
        lines.append(f"# {folder_name.replace('_', ' ').title()}")

    lines.append("")
    lines.append("## Objective")
    lines.append("")
    if findings:
        pid = findings[0]["pattern_id"]
        lines.append(PATTERN_DESCRIPTIONS.get(pid, description))
    else:
        lines.append("Negative control dataset. No fraud patterns are deliberately planted. "
                     "All findings from pattern detectors should be absent or limited to weak-tier noise.")
    lines.append("")

    # Dataset files
    lines.append("## Dataset Files")
    lines.append("")
    lines.append("| Role | Statement File | Bank | Account Number |")
    lines.append("|------|---------------|------|----------------|")
    for acct in accounts:
        role = acct.get("role", "unknown").replace("_", " ").title()
        fname = pathlib.Path(acct.get("file", "")).name
        bank = acct.get("bank", "")
        acct_no = acct.get("fabricated_account_number", "")
        lines.append(f"| {role} | `{fname}` | {bank} | {acct_no} |")
    lines.append("")

    # Accounts Involved section
    lines.append("## Accounts Involved")
    lines.append("")
    for acct in accounts:
        role = acct.get("role", "unknown").replace("_", " ").title()
        fname = pathlib.Path(acct.get("file", "")).name
        bank = acct.get("bank", "")
        acct_no = acct.get("fabricated_account_number", "")
        lines.append(f"### {role} — {bank} · {acct_no}")
        lines.append(f"- **Statement:** `{fname}`")
        lines.append(f"- **Full File Path:** `{acct.get('file', '')}`")
        lines.append("")

    # Expected Findings
    lines.append("## Expected Findings")
    lines.append("")
    if not findings:
        lines.append("_No findings expected. This folder is a negative control._")
        lines.append("")
    else:
        for finding in findings:
            pid = finding["pattern_id"]
            pname = finding.get("pattern_name", NON_FINDING_PATTERN_NAMES.get(pid, ""))
            tier = finding.get("expected_tier", "strong")
            severity = SEVERITY_MAP.get(tier, tier.upper())
            amt_range = finding.get("expected_amount_range", [])
            notes = finding.get("notes", "")
            accts_inv = finding.get("accounts_involved", [])
            refs = finding.get("expected_txn_refs", [])

            lines.append(f"### Pattern {pid} — {pname.replace('_', ' ').title()}")
            lines.append("")
            lines.append(f"**Severity:** {severity}  ")
            lines.append(f"**Pattern ID:** {pid}  ")
            if amt_range:
                if amt_range[0] == amt_range[1]:
                    lines.append(f"**Amount:** ₹{amt_range[0]:,.2f}  ")
                else:
                    lines.append(f"**Amount Range:** ₹{amt_range[0]:,.2f} – ₹{amt_range[1]:,.2f}  ")
            lines.append(f"**Reason:** {notes}  ")
            lines.append("")

            # Accounts involved (resolved to real details)
            if accts_inv:
                lines.append("**Accounts Involved:**")
                lines.append("")
                for sid in accts_inv:
                    a = acct_by_id.get(sid, {})
                    if a:
                        role = a.get("role", "").replace("_", " ").title()
                        bank = a.get("bank", "")
                        acct_no = a.get("fabricated_account_number", "")
                        fname = pathlib.Path(a.get("file", "")).name
                        lines.append(f"- **{role}** — {bank}, Account `{acct_no}` (`{fname}`)")
                lines.append("")

            # Supporting transactions
            lines.append("## Supporting Transactions")
            lines.append("")
            lines.append("Open the listed statement file and locate these transactions to verify this finding:")
            lines.append("")
            lines.append("| Date | Type | Amount (₹) | Narration | Reference / UTR |")
            lines.append("|------|------|------------|-----------|-----------------|")

            seen_refs = set()
            for idx, ref in enumerate(refs):
                if ref in seen_refs:
                    continue
                seen_refs.add(ref)

                # Try to find the transaction in accounts_involved first, then all accounts
                tx = None
                search_order = [acct_by_id.get(s, {}) for s in accts_inv]
                search_order += [a for a in accounts if a.get("synthetic_account_id") not in accts_inv]
                for a in search_order:
                    sid = a.get("synthetic_account_id", "")
                    tx = find_tx(stmt_rows.get(sid, []), ref)
                    if tx:
                        break

                if tx:
                    txtype = "Credit" if tx.get("credit") and not tx.get("debit") else \
                             "Debit"  if tx.get("debit")  and not tx.get("credit") else \
                             "Credit/Debit"
                    amt = tx.get("credit") or tx.get("debit") or "—"
                    narr = tx.get("narration", "")[:80]
                    lines.append(f"| {tx.get('date','—')} | {txtype} | {amt} | {narr} | `{ref}` |")
                else:
                    # Provide ref + amount range as fallback
                    if amt_range:
                        amt_str = f"~{amt_range[0]:,.2f}" if amt_range[0] == amt_range[1] else \
                                  f"{amt_range[0]:,.2f}–{amt_range[1]:,.2f}"
                    else:
                        amt_str = "—"
                    lines.append(f"| — | — | {amt_str} | _(see statement)_ | `{ref}` |")

            lines.append("")

    # Expected Non-Findings
    lines.append("## Expected Non-Findings")
    lines.append("")
    lines.append("The following pattern detectors must NOT trigger on this dataset:")
    lines.append("")
    lines.append("| Pattern ID | Pattern Name | Reason |")
    lines.append("|-----------|--------------|--------|")
    for nf in non_findings:
        pid = nf["pattern_id"]
        pname = NON_FINDING_PATTERN_NAMES.get(pid, "")
        reason = nf.get("reason", "")
        lines.append(f"| {pid} | {pname.replace('_', ' ')} | {reason} |")
    lines.append("")

    # Tier expectations (clean control only)
    tier_exp = gt.get("tier_expectations", {})
    if tier_exp:
        lines.append("## Tier Expectations")
        lines.append("")
        for k, v in tier_exp.items():
            lines.append(f"- **{k.replace('_', ' ').title()}:** {v}")
        lines.append("")

    # Safety net (patterns 22/23)
    sn = gt.get("safety_net_expectation", "")
    if sn:
        lines.append("## Safety Net Expectation")
        lines.append("")
        lines.append(sn)
        lines.append("")

    lines.append("## Validation Notes")
    lines.append("")
    lines.append("To manually verify this ground truth:")
    lines.append("")
    lines.append("1. Open each statement file listed in **Dataset Files** above.")
    lines.append("2. Search for each **Reference / UTR** value in the reference/narration columns.")
    lines.append("3. Confirm the transaction date, amount, and type match the values above.")
    lines.append("4. Confirm no other pattern detector fires on accounts listed as clean controls.")
    lines.append(f"5. Dataset seed: `2025` — re-running the generator with this seed reproduces identical files.")
    lines.append("")

    return "\n".join(lines)


# ──────────────────────────────────────────────────────────────────────────────
# TASK 2 – Investigation case framework
# ──────────────────────────────────────────────────────────────────────────────

INVESTIGATIONS = [
    {
        "id": "INV_001",
        "title": "UPI Investment Scam — Victim Defrauded via Fake Mutual Fund Scheme",
        "fraud_type": "UPI Investment Scam",
        "folder": "inv_001_upi_investment_scam",
        "background": textwrap.dedent("""\
            A private individual was approached via WhatsApp with an offer to invest in a
            "guaranteed return" mutual fund scheme. The victim was instructed to transfer
            funds via UPI/RTGS to a seemingly legitimate account. The account turned out to
            be a mule routing account. Funds were immediately forwarded through two more
            intermediary accounts and ultimately withdrawn as cash.
        """),
        "accounts": [
            {"acct_no": "1974187568",      "bank": "KOTAK MAHINDRA BANK LTD", "file": "pattern_19_first_contact_large_transfer/statements/1974187568_statement.csv",          "role": "Victim / Originator",         "pattern_folder": "pattern_19"},
            {"acct_no": "83871366032735",  "bank": "HDFC BANK LTD",           "file": "pattern_19_first_contact_large_transfer/statements/83871366032735 statement.pdf",       "role": "First Receiver (Mule Layer 1)","pattern_folder": "pattern_19"},
            {"acct_no": "73056887297587",  "bank": "BANDHAN BANK LIMITED",    "file": "pattern_03_pass_through_routing/statements/73056887297587_SOA.xlsx",                    "role": "Routing / Pass-Through (Layer 2)", "pattern_folder": "pattern_03"},
            {"acct_no": "1185080153",      "bank": "KOTAK MAHINDRA BANK LTD", "file": "pattern_04_fund_pooling/statements/1185080153_statement.csv",                           "role": "Pooling Account (Layer 3)",   "pattern_folder": "pattern_04"},
            {"acct_no": "30654527754078",  "bank": "THE FEDERAL BANK LIMITED","file": "pattern_09_credit_to_cash_out/statements/30654527754078-01-12-2024to08-05-2026.pdf",    "role": "Cash-Out Account (Final Layer)","pattern_folder": "pattern_09"},
        ],
        "money_approx": "₹6,42,000 initial transfer; total proceeds pooled ~₹3,00,000–₹8,50,000",
        "patterns": ["first_contact_large_transfer", "pass_through_routing", "fund_pooling", "credit_to_cash_out"],
        "key_refs": {
            "Initial RTGS": "R95720579226",
            "Pass-through credits": ["051698095623", "508863857173", "445482069527"],
            "Pooling inflows": ["389922137580", "384915118541", "200216494773"],
            "Cash-out ATM": "867662226469",
        },
        "reconstruction": textwrap.dedent("""\
            ## Step-by-Step Money Movement

            ### Step 1 — Victim Transfer (First Contact Large Transfer)
            - **Date:** Located in `1974187568_statement.csv` under reference `R95720579226`
            - **Action:** Victim (Kotak account 1974187568) sends ₹6,42,000 via RTGS to
              HDFC account 83871366032735.
            - **Signal:** This is the first-ever transaction between these two parties —
              no prior history exists in either statement.
            - **Receiving statement:** The same ref `R95720579226` appears as a credit in
              `83871366032735 statement.pdf` (HDFC Bank).

            ### Step 2 — First Receiver Routes Funds (Pass-Through)
            - **Date:** Within 24–48 hours of receipt
            - **Action:** HDFC account 83871366032735 forwards funds onward via UPI/IMPS.
            - **Receiving account:** Bandhan Bank account 73056887297587 (`73056887297587_SOA.xlsx`)
            - **Signal:** The Bandhan account shows multiple unrelated inbound credits
              (refs: 051698095623, 508863857173, 445482069527, 810040308391, 745952975950)
              followed by rapid onward routing — a classic pass-through pattern.

            ### Step 3 — Funds Pooled (Fund Pooling)
            - **Date:** Within 2–5 days of initial transfer
            - **Action:** Kotak account 1185080153 receives funds from multiple sources
              (including the Bandhan routing account) in a short window.
            - **Supporting refs in `1185080153_statement.csv`:**
              389922137580, 384915118541, 200216494773, 162947856305, 915009796170
            - **Signal:** Multiple unrelated senders, tight time window, no outward
              retail spend — consistent with a pooling mule.

            ### Step 4 — Cash Withdrawal (Credit to Cash Out)
            - **Date:** Within 1–3 days of pooling
            - **Action:** Federal Bank account 30654527754078 receives a large inward
              credit (ref 563801007073) and within hours makes ATM withdrawals (ref 867662226469)
              equivalent to the credited amount.
            - **Statement:** `30654527754078-01-12-2024to08-05-2026.pdf`
            - **Signal:** Rapid credit-to-ATM pattern eliminates any legitimate commercial purpose.

            ## Reconstruction Summary

            | Step | From | To | Amount (Approx) | Method | Reference |
            |------|------|----|-----------------|--------|-----------|
            | 1 | Victim (Kotak 1974187568) | HDFC 83871366032735 | ₹6,42,000 | RTGS | R95720579226 |
            | 2 | HDFC 83871366032735 | Bandhan 73056887297587 | ₹4,00,000–₹6,00,000 | UPI/IMPS | Multiple |
            | 3 | Bandhan + others → Kotak 1185080153 | (pooled) | ₹3,00,000–₹8,50,000 | UPI/NEFT | Multiple |
            | 4 | Kotak 1185080153 → Federal 30654527754078 | ATM Cash | ₹1,45,000–₹1,86,000 | ATM | 867662226469 |

            **Conclusion:** Funds originating from the victim's UPI payment were layered
            through three mule accounts and withdrawn as cash within 3–5 banking days,
            consistent with a organised UPI investment scam network.
        """),
        "non_findings": [
            ("circular_flow", "Funds do not return to originator — the chain terminates at cash withdrawal."),
            ("duplicate_verification", "No duplicate transaction rows detected in any statement."),
            ("structuring_smurfing", "Deposits are not kept below ₹50,000 threshold; this is a single large transfer."),
            ("dormant_reactivation", "None of these accounts show prior dormancy before the fraud window."),
            ("shared_upi", "Different UPI handles are used at each hop; no shared handle across accounts."),
        ],
    },
    {
        "id": "INV_002",
        "title": "Mule Network — Hub-and-Spoke Aggregation for Organised Cyber Fraud",
        "fraud_type": "Mule Network / Hub-and-Spoke",
        "folder": "inv_002_mule_network_hub_spoke",
        "background": textwrap.dedent("""\
            A central mule account (the hub) is controlled by an organised cyber-fraud group.
            Multiple peripheral accounts (spokes) — each operated by a recruited money mule —
            receive small amounts from fraud victims and transfer them to the hub. The hub then
            aggregates the proceeds and routes them for layering. This structure makes individual
            spoke accounts appear to have limited suspicious activity, while the hub shows
            the full scale of the operation.
        """),
        "accounts": [
            {"acct_no": "2583442857",          "bank": "KOTAK MAHINDRA BANK LTD", "file": "pattern_12_hub_ranking/statements/2583442857_statement.xlsx",               "role": "Hub (Aggregator)",    "pattern_folder": "pattern_12"},
            {"acct_no": "2871288856142199",     "bank": "PUNJAB NATIONAL BANK",    "file": "pattern_12_hub_ranking/statements/2871288856142199_statement.pdf",           "role": "Spoke Account 1",     "pattern_folder": "pattern_12"},
            {"acct_no": "12691319567650",       "bank": "THE FEDERAL BANK LIMITED","file": "pattern_12_hub_ranking/statements/12691319567650-01-12-2024to08-05-2026.xlsx","role": "Spoke Account 2",     "pattern_folder": "pattern_12"},
            {"acct_no": "5089515621605975",     "bank": "UCO BANK",                "file": "pattern_12_hub_ranking/statements/5089515621605975-02-12-2024to08-05-2026.xlsx","role": "Spoke Account 3",   "pattern_folder": "pattern_12"},
            {"acct_no": "59347392058238",       "bank": "HDFC BANK LTD",           "file": "pattern_12_hub_ranking/statements/59347392058238 statement.csv",             "role": "Spoke Account 4",     "pattern_folder": "pattern_12"},
            {"acct_no": "81206073174626",       "bank": "THE FEDERAL BANK LIMITED","file": "pattern_12_hub_ranking/statements/81206073174626-02-12-2024to08-05-2026.xlsx","role": "Spoke Account 5",     "pattern_folder": "pattern_12"},
            {"acct_no": "99628833989",          "bank": "STATE BANK OF INDIA",     "file": "pattern_12_hub_ranking/statements/statement-99628833989.xlsx",               "role": "Spoke Account 6",     "pattern_folder": "pattern_12"},
            {"acct_no": "5226559152743878",     "bank": "PUNJAB NATIONAL BANK",    "file": "pattern_12_hub_ranking/statements/5226559152743878_statement.txt",           "role": "Spoke Account 7",     "pattern_folder": "pattern_12"},
        ],
        "money_approx": "₹31,200–₹63,400 per spoke transfer; total aggregated at hub from 7 spokes",
        "patterns": ["hub_ranking", "fund_pooling"],
        "key_refs": {
            "Spoke 1 → Hub": ["N39558289002"],
            "Spoke 2 → Hub": ["I43243339199"],
            "Spoke 3 → Hub": ["I71359001100"],
            "Spoke 4 → Hub": ["I75823920825"],
            "Spoke 5 → Hub": ["I18986330736"],
            "Spoke 6 → Hub": ["U72411748544"],
            "Spoke 7 → Hub": ["N65830057946"],
        },
        "reconstruction": textwrap.dedent("""\
            ## Step-by-Step Money Movement

            All transfers flow from individual spoke accounts into the central hub
            (Kotak account 2583442857). Every spoke-to-hub transfer is corroborated
            by matching entries on both the spoke's statement and the hub's statement.

            ### Spoke-to-Hub Transfer Map

            | Spoke | Bank | Account | Transfer Ref | Direction |
            |-------|------|---------|-------------|-----------|
            | Spoke 1 | PUNJAB NATIONAL BANK | 2871288856142199 | N39558289002 | Spoke → Hub |
            | Spoke 2 | THE FEDERAL BANK LIMITED | 12691319567650 | I43243339199 | Spoke → Hub |
            | Spoke 3 | UCO BANK | 5089515621605975 | I71359001100 | Spoke → Hub |
            | Spoke 4 | HDFC BANK LTD | 59347392058238 | I75823920825 | Spoke → Hub |
            | Spoke 5 | THE FEDERAL BANK LIMITED | 81206073174626 | I18986330736 | Spoke → Hub |
            | Spoke 6 | STATE BANK OF INDIA | 99628833989 | U72411748544 | Spoke → Hub |
            | Spoke 7 | PUNJAB NATIONAL BANK | 5226559152743878 | N65830057946 | Spoke → Hub |

            ### Corroboration Method
            For each ref above:
            1. Open the spoke's statement file and locate the debit entry with that ref.
            2. Open `2583442857_statement.xlsx` (hub) and locate the matching credit entry with the same ref.
            3. Amounts must match exactly — this is the cross-statement corroboration requirement.

            ### Hub Behaviour
            - The hub account (Kotak 2583442857) receives from 7 distinct accounts across
              5 different banks within the analysis window.
            - This concentration of inflows from multiple unrelated sources, combined with
              the hub's own outward routing behaviour, is the core hub_ranking signal.

            ## Reconstruction Summary

            Seven spoke accounts, each at a different bank and in different cities,
            funnel proceeds into a single Kotak hub account. The hub account shows
            no corresponding retail expenditure — all inflows are received and held
            or forwarded. This is the structural signature of a professional money
            mule network operating across multiple banking relationships simultaneously.
        """),
        "non_findings": [
            ("circular_flow",   "Funds do not return to any spoke — the flow is unidirectional into the hub."),
            ("round_trip",      "No return leg detected in any spoke statement."),
            ("dormant_reactivation", "None of the spoke or hub accounts was dormant before this activity."),
            ("duplicate_verification", "No duplicate rows detected."),
            ("structuring_smurfing", "Individual transfer amounts are not calibrated below reporting thresholds."),
        ],
    },
    {
        "id": "INV_003",
        "title": "Circular Money Laundering — Layered Round-Trip via Multi-Bank Chain",
        "fraud_type": "Layered Money Laundering / Circular Flow",
        "folder": "inv_003_circular_money_laundering",
        "background": textwrap.dedent("""\
            A criminal group launders proceeds by moving funds through a chain of accounts
            at different banks, eventually returning the funds to the originating account.
            This circular flow creates an appearance of legitimate commercial activity
            (payments between businesses) while obscuring the illicit origin. Simultaneously,
            a parallel money trail confirms cross-bank fund movement corroborated by
            matching UTR numbers on both sides of each transfer.
        """),
        "accounts": [
            {"acct_no": "16965968123",    "bank": "STATE BANK OF INDIA", "file": "pattern_07_circular_flow/statements/statement-16965968123.txt",          "role": "Originator (Loop Start/End)",   "pattern_folder": "pattern_07"},
            {"acct_no": "25347399309",    "bank": "STATE BANK OF INDIA", "file": "pattern_07_circular_flow/statements/statement-25347399309.csv",          "role": "Intermediary 1",               "pattern_folder": "pattern_07"},
            {"acct_no": "23088623376",    "bank": "STATE BANK OF INDIA", "file": "pattern_07_circular_flow/statements/statement-23088623376.txt",          "role": "Intermediary 2",               "pattern_folder": "pattern_07"},
            {"acct_no": "2561038363701767","bank":"UCO BANK",            "file": "pattern_07_circular_flow/statements/2561038363701767-01-12-2024to07-05-2026.pdf", "role": "Final Hop (Returns to Originator)", "pattern_folder": "pattern_07"},
            {"acct_no": "7966944653",     "bank": "KOTAK MAHINDRA BANK LTD","file":"pattern_08_money_trail/statements/7966944653_statement.xlsx",           "role": "Money Trail — Sender",         "pattern_folder": "pattern_08"},
            {"acct_no": "48420599781",    "bank": "STATE BANK OF INDIA", "file": "pattern_08_money_trail/statements/statement-48420599781.txt",             "role": "Money Trail — Receiver",       "pattern_folder": "pattern_08"},
        ],
        "money_approx": "Circular loop: ₹1,83,465–₹1,94,000; Parallel trail: ₹1,75,149",
        "patterns": ["circular_flow", "money_trail", "round_trip"],
        "key_refs": {
            "Hop 1 (Originator → Intermediary 1)": "N64528068915",
            "Hop 2 (Intermediary 1 → Intermediary 2)": "I72988444765",
            "Hop 3 (Intermediary 2 → Final Hop)": "N93051572449",
            "Hop 4 (Final Hop → Originator, completes loop)": "N50221616826",
            "Parallel trail debit/credit": "I55274060571",
        },
        "reconstruction": textwrap.dedent("""\
            ## Circular Flow — Step-by-Step

            ### Hop 1 — Originator sends to Intermediary 1
            - **From:** SBI account 16965968123 (`statement-16965968123.txt`)
            - **To:** SBI account 25347399309 (`statement-25347399309.csv`)
            - **Reference:** `N64528068915`
            - **Corroboration:** Debit in originator's statement; Credit in Intermediary 1's statement.
            - **Amount:** ~₹1,83,465–₹1,94,000

            ### Hop 2 — Intermediary 1 → Intermediary 2
            - **From:** SBI account 25347399309
            - **To:** SBI account 23088623376 (`statement-23088623376.txt`)
            - **Reference:** `I72988444765`
            - **Corroboration:** Debit in Intermediary 1; Credit in Intermediary 2.

            ### Hop 3 — Intermediary 2 → UCO Bank (Final Hop)
            - **From:** SBI account 23088623376
            - **To:** UCO Bank account 2561038363701767 (`2561038363701767-*.pdf`)
            - **Reference:** `N93051572449`
            - **Corroboration:** Debit in Intermediary 2; Credit in UCO statement.

            ### Hop 4 — UCO Bank returns funds to Originator (Loop Closed)
            - **From:** UCO Bank account 2561038363701767
            - **To:** SBI account 16965968123 (same as Hop 1 sender)
            - **Reference:** `N50221616826`
            - **Corroboration:** Debit in UCO statement; Credit in SBI originator statement.
            - **This closes the loop.** Funds return to their starting point.

            ## Parallel Money Trail

            Simultaneously, a separate corroborated transfer occurs:
            - **Sender:** Kotak account 7966944653 (`7966944653_statement.xlsx`)
            - **Receiver:** SBI account 48420599781 (`statement-48420599781.txt`)
            - **Reference:** `I55274060571`
            - **Amount:** ₹1,75,149.55
            - **Corroboration:** Debit in Kotak statement; Credit in SBI statement with identical ref.

            ## Reconstruction Summary

            | Hop | From Account | To Account | Bank(s) | Reference | Signal |
            |-----|-------------|-----------|---------|-----------|--------|
            | 1 | SBI 16965968123 | SBI 25347399309 | SBI→SBI | N64528068915 | Circular Start |
            | 2 | SBI 25347399309 | SBI 23088623376 | SBI→SBI | I72988444765 | Intermediary |
            | 3 | SBI 23088623376 | UCO 2561038363701767 | SBI→UCO | N93051572449 | Cross-Bank |
            | 4 | UCO 2561038363701767 | SBI 16965968123 | UCO→SBI | N50221616826 | Loop Closed |
            | P1 | Kotak 7966944653 | SBI 48420599781 | Kotak→SBI | I55274060571 | Parallel Trail |

            The circular loop and the parallel money trail collectively demonstrate a
            coordinated layering operation using four accounts across two banks.
        """),
        "non_findings": [
            ("structuring_smurfing", "No pattern of sub-threshold deposits is present."),
            ("hub_ranking",         "No single account receives from more than two others in this chain."),
            ("dormant_reactivation","None of these accounts was dormant before the circular activity."),
            ("first_contact_large_transfer", "The parties have prior transaction history within the dataset."),
            ("low_value_testing",   "No micro-transfer probing is present."),
        ],
    },
    {
        "id": "INV_004",
        "title": "Dormant Account Takeover + Large First-Contact Fraud Transfer",
        "fraud_type": "Account Takeover / Dormant Account Exploitation",
        "folder": "inv_004_dormant_account_takeover",
        "background": textwrap.dedent("""\
            A UCO Bank account that had been dormant for an extended period was suddenly
            reactivated and used to receive and forward a large transfer. In parallel, a
            Kotak Bank account with no prior transaction history received a first-time
            large RTGS transfer. Together these incidents suggest a coordinated account
            takeover scheme where dormant accounts and freshly opened mule accounts are
            activated simultaneously for a fraud event.
        """),
        "accounts": [
            {"acct_no": "5699090930288949","bank": "UCO BANK",            "file": "pattern_18_dormant_reactivation/statements/5699090930288949-26-12-2024to28-10-2025.pdf",   "role": "Dormant Account (Reactivated)", "pattern_folder": "pattern_18"},
            {"acct_no": "1974187568",       "bank": "KOTAK MAHINDRA BANK LTD","file": "pattern_19_first_contact_large_transfer/statements/1974187568_statement.csv",          "role": "First-Contact Originator",     "pattern_folder": "pattern_19"},
            {"acct_no": "83871366032735",   "bank": "HDFC BANK LTD",      "file": "pattern_19_first_contact_large_transfer/statements/83871366032735 statement.pdf",           "role": "First-Contact Receiver",       "pattern_folder": "pattern_19"},
        ],
        "money_approx": "Dormant reactivation: ₹1,170–₹1,44,000; First-contact RTGS: ₹6,42,000",
        "patterns": ["dormant_reactivation", "first_contact_large_transfer"],
        "key_refs": {
            "Dormant account — first transaction after dormancy": "122531129346",
            "Dormant account — reactivation burst tx 2": "885307217643",
            "Dormant account — reactivation burst tx 3": "891723038808",
            "First-contact RTGS (originator debit)": "R95720579226",
            "First-contact RTGS (receiver credit)": "R95720579226",
        },
        "reconstruction": textwrap.dedent("""\
            ## UCO Bank Dormant Account Reactivation

            ### Dormancy Evidence
            - **Account:** UCO Bank 5699090930288949
            - **Statement file:** `5699090930288949-26-12-2024to28-10-2025.pdf`
            - **Observation:** The statement shows a prolonged gap with zero transactions,
              followed by a sudden burst of three transactions:
              1. Ref `122531129346` — First transaction post-dormancy
              2. Ref `885307217643` — Rapid follow-up transaction
              3. Ref `891723038808` — Third transaction within the burst window
            - **Amount range:** ₹1,170 to ₹1,44,000 (escalating from small test to large amount)
            - **Signal:** Dormant accounts reactivated for fraud typically begin with a
              small test transaction, then escalate — this account follows that exact pattern.

            ## First-Contact Large Transfer (Kotak → HDFC)

            ### Transfer Evidence
            - **Originator:** Kotak account 1974187568 (`1974187568_statement.csv`)
            - **Receiver:** HDFC account 83871366032735 (`83871366032735 statement.pdf`)
            - **Reference:** `R95720579226` (RTGS)
            - **Amount:** ₹6,42,000
            - **Signal:** Searching `1974187568_statement.csv` for ref `R95720579226`
              shows this is the first-ever transaction between these parties — no prior
              credit or debit involving the HDFC account number or UPI handle appears
              anywhere in the Kotak statement history.

            ## Investigation Hypothesis

            The reactivated UCO dormant account and the freshly utilised Kotak account
            appear to be part of the same fraud activation wave. The dormant UCO account
            may have been taken over (credentials compromised), while the Kotak account
            may be a newly recruited mule account. Both were activated in close proximity
            to receive or forward fraud proceeds.

            ## Reconstruction Summary

            | Event | Account | Bank | Amount | Reference | Signal |
            |-------|---------|------|--------|-----------|--------|
            | Dormant burst tx 1 | 5699090930288949 | UCO | ~₹1,170 | 122531129346 | First post-dormancy tx |
            | Dormant burst tx 2 | 5699090930288949 | UCO | ~₹50,000 | 885307217643 | Escalation |
            | Dormant burst tx 3 | 5699090930288949 | UCO | ~₹1,44,000 | 891723038808 | Large reactivation |
            | First-contact RTGS | 1974187568 (sender) | Kotak | ₹6,42,000 | R95720579226 | No prior relationship |
            | First-contact receipt | 83871366032735 (receiver) | HDFC | ₹6,42,000 | R95720579226 | First inflow from Kotak |
        """),
        "non_findings": [
            ("circular_flow",    "Funds do not loop back to originator."),
            ("hub_ranking",      "Only 1–2 accounts involved; no hub aggregation pattern."),
            ("structuring_smurfing", "Amounts do not follow sub-threshold structuring."),
            ("reversal_clusters","No debit-reversal pairs detected."),
            ("shared_upi",       "No shared UPI handle across accounts."),
        ],
    },
    {
        "id": "INV_005",
        "title": "Smurfing + Structured Cash Placement via Multiple Channels",
        "fraud_type": "Structured Cash Placement / Smurfing",
        "folder": "inv_005_smurfing_structured_placement",
        "background": textwrap.dedent("""\
            A suspect account at Axis Bank receives a series of cash deposits, each
            carefully kept below ₹50,000 to avoid Currency Transaction Report (CTR)
            obligations. Simultaneously, a linked HDFC account shows a cluster of
            round-value outward transfers — a hallmark of layering after successful
            placement. A Federal Bank account is used as the final cash-out vehicle
            via ATM withdrawals after receiving a large aggregated credit.
        """),
        "accounts": [
            {"acct_no": "750850479834326",  "bank": "AXIS BANK LIMITED",    "file": "pattern_05_structuring_smurfing/statements/750850479834326_statement.xlsx",       "role": "Placement Account (Structuring)","pattern_folder": "pattern_05"},
            {"acct_no": "85315254644320",   "bank": "HDFC BANK LTD",        "file": "pattern_15_round_value_debit/statements/85315254644320 statement.pdf",            "role": "Layering Account (Round Values)", "pattern_folder": "pattern_15"},
            {"acct_no": "30654527754078",   "bank": "THE FEDERAL BANK LIMITED","file":"pattern_09_credit_to_cash_out/statements/30654527754078-01-12-2024to08-05-2026.pdf","role": "Integration / Cash-Out Account","pattern_folder": "pattern_09"},
        ],
        "money_approx": "Structuring deposits: ₹44,900–₹49,900 × 8 events; Round-value transfers: ₹25,000–₹85,000 × 7; Cash-out: ₹1,45,000–₹1,86,000",
        "patterns": ["structuring_smurfing", "round_value_debit", "credit_to_cash_out"],
        "key_refs": {
            "Structuring deposits (Axis)": ["014782139565", "396821238320", "125229000046", "669291167555", "270281220048", "735929287799", "544113730778", "469609805690"],
            "Round-value transfers (HDFC)": ["219871512217", "899751038969", "246372423033", "099577519299", "984982294808", "425877947807", "872406510315"],
            "Cash-out credit inflow": "563801007073",
            "Cash-out ATM withdrawal": "867662226469",
        },
        "reconstruction": textwrap.dedent("""\
            ## Stage 1 — Placement (Structuring / Smurfing)

            **Account:** Axis Bank 750850479834326
            **Statement:** `750850479834326_statement.xlsx`

            Eight separate cash deposits, each below ₹50,000, are deposited into the
            Axis Bank account over the fraud window. The structuring is evident from
            the tight amount band (₹44,900–₹49,900) and the cadence of deposits.

            | # | Reference | Amount Range |
            |---|-----------|-------------|
            | 1 | 014782139565 | ₹44,900–₹49,900 |
            | 2 | 396821238320 | ₹44,900–₹49,900 |
            | 3 | 125229000046 | ₹44,900–₹49,900 |
            | 4 | 669291167555 | ₹44,900–₹49,900 |
            | 5 | 270281220048 | ₹44,900–₹49,900 |
            | 6 | 735929287799 | ₹44,900–₹49,900 |
            | 7 | 544113730778 | ₹44,900–₹49,900 |
            | 8 | 469609805690 | ₹44,900–₹49,900 |

            **To verify:** Open `750850479834326_statement.xlsx`, search for each ref above,
            confirm each is a credit entry with amount in the ₹44,900–₹49,900 band.

            ## Stage 2 — Layering (Round-Value Debits)

            **Account:** HDFC Bank 85315254644320
            **Statement:** `85315254644320 statement.pdf`

            Seven outward transfers in conspicuously round rupee amounts
            (₹25,000–₹85,000) occur in the same period, interspersed with
            normal non-round retail spending (groceries, utilities, UPI).

            | # | Reference | Amount Range |
            |---|-----------|-------------|
            | 1 | 219871512217 | ₹25,000–₹85,000 |
            | 2 | 899751038969 | ₹25,000–₹85,000 |
            | 3 | 246372423033 | ₹25,000–₹85,000 |
            | 4 | 099577519299 | ₹25,000–₹85,000 |
            | 5 | 984982294808 | ₹25,000–₹85,000 |
            | 6 | 425877947807 | ₹25,000–₹85,000 |
            | 7 | 872406510315 | ₹25,000–₹85,000 |

            ## Stage 3 — Integration / Cash Out

            **Account:** Federal Bank 30654527754078
            **Statement:** `30654527754078-01-12-2024to08-05-2026.pdf`

            A large inward credit (ref `563801007073`, ₹1,45,000–₹1,86,000) is
            followed within hours to days by ATM withdrawals (ref `867662226469`)
            consuming the equivalent amount. No legitimate retail expenditure
            pattern follows the credit — the funds are extracted as cash directly.

            ## Reconstruction Summary

            | Stage | Account | Bank | Activity | References |
            |-------|---------|------|----------|-----------|
            | Placement | 750850479834326 | Axis Bank | 8 × sub-₹50K cash deposits | 014782139565 … 469609805690 |
            | Layering | 85315254644320 | HDFC | 7 × round-value outward transfers | 219871512217 … 872406510315 |
            | Integration | 30654527754078 | Federal Bank | Large credit → immediate ATM cash | 563801007073 → 867662226469 |
        """),
        "non_findings": [
            ("circular_flow",   "Funds do not return to originator at any stage."),
            ("hub_ranking",     "Only three accounts; no spoke-to-hub aggregation pattern."),
            ("money_trail",     "No corroborated cross-statement UTR link between these three accounts."),
            ("low_value_testing","No micro-transfer probing detected in any statement."),
            ("duplicate_verification", "No duplicate transaction rows detected."),
        ],
    },
    {
        "id": "INV_006",
        "title": "Business Email Fraud — Fake Supplier Payment with Shared UPI Handle",
        "fraud_type": "Business Email Fraud / Shared Credential Abuse",
        "folder": "inv_006_business_email_fraud_shared_upi",
        "background": textwrap.dedent("""\
            A fraudster impersonated a supplier and diverted invoice payments to two
            separate mule accounts. Both mule accounts received payments to the same
            fraudulent UPI handle, linking them as controlled by the same individual
            or group. Additionally, a low-value test transfer was used to validate
            account details before the main payment was executed — a common BEC technique.
            A reversal cluster was also detected on the victim-side account, suggesting
            the victim attempted to reverse the payment after discovering the fraud.
        """),
        "accounts": [
            {"acct_no": "99138197699213",  "bank": "THE FEDERAL BANK LIMITED", "file": "pattern_16_shared_upi/statements/99138197699213-02-12-2024to08-05-2026.csv", "role": "Mule Account 1 (Shared UPI)", "pattern_folder": "pattern_16"},
            {"acct_no": "35398829268638",  "bank": "BANDHAN BANK LIMITED",     "file": "pattern_16_shared_upi/statements/35398829268638_SOA.csv",                    "role": "Mule Account 2 (Shared UPI)", "pattern_folder": "pattern_16"},
            {"acct_no": "0165684919172270","bank": "PUNJAB NATIONAL BANK",     "file": "pattern_13_low_value_testing/statements/0165684919172270_statement.pdf",      "role": "Test-Transfer Originator",    "pattern_folder": "pattern_13"},
            {"acct_no": "9456806565",      "bank": "KOTAK MAHINDRA BANK LTD",  "file": "pattern_13_low_value_testing/statements/9456806565_statement.xlsx",           "role": "Test-Transfer Counterparty",  "pattern_folder": "pattern_13"},
            {"acct_no": "5029518734468697","bank": "UCO BANK",                 "file": "pattern_14_reversal_clusters/statements/5029518734468697-01-12-2024to08-05-2026.pdf", "role": "Victim Account (Reversal Attempts)", "pattern_folder": "pattern_14"},
        ],
        "money_approx": "Shared UPI payments: ₹3,250–₹7,490 per transaction; Test transfers: ₹2–₹27; Reversal attempts: ₹11,400–₹28,700",
        "patterns": ["shared_upi", "low_value_testing", "reversal_clusters"],
        "key_refs": {
            "Shared UPI tx in Mule 1 (Federal)": "454765872505",
            "Shared UPI tx in Mule 2 (Bandhan)": "001614410230",
            "Test transfer 1 (both sides)": "U40014894936",
            "Test transfer 2 (both sides)": "U22264596871",
            "Test transfer 3 (both sides)": "U44532517544",
            "Reversal cluster debit 1": "U31538669531",
            "Reversal cluster credit 1": "740682745330",
            "Reversal cluster debit 2": "U71434768704",
            "Reversal cluster credit 2": "241754535853",
            "Reversal cluster debit 3": "U61130734906",
            "Reversal cluster credit 3": "510631731294",
        },
        "reconstruction": textwrap.dedent("""\
            ## Step 1 — Account Validation via Low-Value Test Transfers

            Before the main fraud payment, the fraudster sent micro-amounts between
            PNB account 0165684919172270 and Kotak account 9456806565 to confirm
            account validity and UPI routing.

            | Test | Reference | Confirmation |
            |------|-----------|-------------|
            | Test 1 | U40014894936 | Both `0165684919172270_statement.pdf` (PNB) and `9456806565_statement.xlsx` (Kotak) contain this ref — cross-validated |
            | Test 2 | U22264596871 | Same cross-validation — debit in one, credit in other |
            | Test 3 | U44532517544 | Third probe confirming bidirectional channel |

            **To verify:** Open both statements and search for each ref — it must appear
            in both statements as complementary debit/credit entries.

            ## Step 2 — Main Fraud Payments via Shared UPI Handle

            The fraudster's UPI handle (`akash37@okaxis`) appears in both:
            - Federal Bank account 99138197699213 (`99138197699213-*.csv`), ref `454765872505`
            - Bandhan Bank account 35398829268638 (`35398829268638_SOA.csv`), ref `001614410230`

            **Amount range:** ₹3,250–₹7,490 per transaction
            **Signal:** The same UPI handle receiving payments in two nominally unrelated
            accounts proves the same individual controls both accounts.

            ## Step 3 — Victim Reversal Attempts

            After discovering the fraud, the victim (UCO Bank account 5029518734468697)
            attempted to reverse payments. These appear as debit-reversal clusters:

            | Cycle | Debit Ref | Reversal Ref | Amount Range |
            |-------|-----------|-------------|-------------|
            | 1 | U31538669531 | 740682745330 | ₹11,400–₹28,700 |
            | 2 | U71434768704 | 241754535853 | ₹11,400–₹28,700 |
            | 3 | U61130734906 | 510631731294 | ₹11,400–₹28,700 |

            **Statement:** `5029518734468697-01-12-2024to08-05-2026.pdf`
            **To verify:** Each cycle should show a UPI debit followed closely (within
            hours or days) by a matching reversal credit of the exact same amount.

            ## Reconstruction Summary

            | Phase | Account | Bank | Event | Key Reference |
            |-------|---------|------|-------|--------------|
            | Validation | PNB 0165684919172270 ↔ Kotak 9456806565 | PNB / Kotak | 3× micro-probe transfers | U40014894936, U22264596871, U44532517544 |
            | Fraud payment 1 | Federal 99138197699213 | Federal | UPI receipt via akash37@okaxis | 454765872505 |
            | Fraud payment 2 | Bandhan 35398829268638 | Bandhan | UPI receipt via same handle | 001614410230 |
            | Victim reversal | UCO 5029518734468697 | UCO | 3× debit-reversal attempts | U31538669531 … 510631731294 |
        """),
        "non_findings": [
            ("fund_pooling",   "Amounts pooled are not from multiple unrelated senders at scale."),
            ("hub_ranking",    "No hub-spoke aggregation; only two mule accounts linked by UPI handle."),
            ("circular_flow",  "Funds do not return to any originator."),
            ("balance_parking","No large credit left unspent; amounts are small."),
            ("structuring_smurfing", "No sub-threshold cash deposit structuring detected."),
        ],
    },
]


def write_investigation(inv: dict, inv_dir: pathlib.Path):
    inv_dir.mkdir(parents=True, exist_ok=True)

    # ── CASE_DESCRIPTION.md ─────────────────────────────────────────────────
    lines = []
    lines.append(f"# Case: {inv['title']}")
    lines.append("")
    lines.append(f"**Investigation ID:** {inv['id']}  ")
    lines.append(f"**Fraud Type:** {inv['fraud_type']}  ")
    lines.append(f"**Number of Accounts:** {len(inv['accounts'])}  ")
    lines.append(f"**Approximate Money Involved:** {inv['money_approx']}  ")
    lines.append("")
    lines.append("## Background")
    lines.append("")
    lines.append(inv["background"].strip())
    lines.append("")
    lines.append("## Investigation Objective")
    lines.append("")
    lines.append("Verify that the Case Reconstruction Engine can:")
    lines.append("")
    lines.append("1. Identify all accounts involved in this case from the provided statements.")
    lines.append("2. Reconstruct the complete chronological money movement.")
    lines.append("3. Correctly assign roles (victim, mule, routing, pooling, cash-out) to each account.")
    lines.append("4. Generate an investigation narrative that a CID officer could use directly.")
    lines.append("5. Surface the correct pattern detectors and suppress false positives.")
    lines.append("")
    lines.append("## Dataset Files for This Case")
    lines.append("")
    lines.append("| Role | Statement File | Bank | Account Number |")
    lines.append("|------|--------------|------|----------------|")
    for acct in inv["accounts"]:
        fname = pathlib.Path(acct["file"]).name
        lines.append(f"| {acct['role']} | `{fname}` | {acct['bank']} | {acct['acct_no']} |")
    lines.append("")
    lines.append("## Source Pattern Folders")
    lines.append("")
    pat_folders = sorted(set(a["pattern_folder"] for a in inv["accounts"]))
    for pf in pat_folders:
        lines.append(f"- `{pf}/statements/`")
    lines.append("")
    (inv_dir / "CASE_DESCRIPTION.md").write_text("\n".join(lines), encoding="utf-8")

    # ── EXPECTED_PATTERNS.md ────────────────────────────────────────────────
    lines = []
    lines.append(f"# Expected Patterns — {inv['title']}")
    lines.append("")
    lines.append("The following pattern detectors are expected to fire on this case:")
    lines.append("")
    for p in inv["patterns"]:
        pid = {v: k for k, v in NON_FINDING_PATTERN_NAMES.items()}.get(p, "?")
        lines.append(f"✓ **Pattern {pid} — {p.replace('_', ' ').title()}**")
        lines.append(f"  - {PATTERN_DESCRIPTIONS.get(pid, '')}")
        lines.append("")
    (inv_dir / "EXPECTED_PATTERNS.md").write_text("\n".join(lines), encoding="utf-8")

    # ── EXPECTED_RECONSTRUCTION.md ──────────────────────────────────────────
    lines = []
    lines.append(f"# Expected Case Reconstruction — {inv['title']}")
    lines.append("")
    lines.append(inv["reconstruction"].strip())
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Key Reference Numbers for Manual Verification")
    lines.append("")
    for label, ref in inv["key_refs"].items():
        if isinstance(ref, list):
            lines.append(f"- **{label}:** " + ", ".join(f"`{r}`" for r in ref))
        else:
            lines.append(f"- **{label}:** `{ref}`")
    lines.append("")
    (inv_dir / "EXPECTED_RECONSTRUCTION.md").write_text("\n".join(lines), encoding="utf-8")

    # ── EXPECTED_FINDINGS.md ────────────────────────────────────────────────
    lines = []
    lines.append(f"# Expected Findings — {inv['title']}")
    lines.append("")
    for p in inv["patterns"]:
        pid = {v: k for k, v in NON_FINDING_PATTERN_NAMES.items()}.get(p, "?")
        lines.append(f"## Pattern {pid} — {p.replace('_', ' ').title()}")
        lines.append("")
        lines.append(f"**Pattern Name:** {p}  ")
        lines.append(f"**Pattern ID:** {pid}  ")
        lines.append(f"**Expected Confidence:** High  ")
        lines.append(f"**Why It Should Trigger:**  ")
        lines.append(f"{PATTERN_DESCRIPTIONS.get(pid, '')}  ")
        lines.append("")
        lines.append("**Accounts Involved:**")
        for acct in inv["accounts"]:
            fname = pathlib.Path(acct["file"]).name
            lines.append(f"- `{fname}` — {acct['bank']} {acct['acct_no']} ({acct['role']})")
        lines.append("")
        lines.append("**Supporting References:**")
        for label, ref in inv["key_refs"].items():
            if isinstance(ref, list):
                lines.append(f"- {label}: " + ", ".join(f"`{r}`" for r in ref))
            else:
                lines.append(f"- {label}: `{ref}`")
        lines.append("")
    (inv_dir / "EXPECTED_FINDINGS.md").write_text("\n".join(lines), encoding="utf-8")

    # ── EXPECTED_NON_FINDINGS.md ────────────────────────────────────────────
    lines = []
    lines.append(f"# Expected Non-Findings — {inv['title']}")
    lines.append("")
    lines.append("The following patterns must NOT be reported as findings for this case.  ")
    lines.append("Triggering any of these would constitute a false positive.")
    lines.append("")
    lines.append("| Pattern | Pattern Name | Reason Must Not Fire |")
    lines.append("|---------|-------------|----------------------|")
    for pname, reason in inv["non_findings"]:
        pid = {v: k for k, v in NON_FINDING_PATTERN_NAMES.items()}.get(pname, "?")
        lines.append(f"| {pid} | {pname.replace('_', ' ')} | {reason} |")
    lines.append("")
    (inv_dir / "EXPECTED_NON_FINDINGS.md").write_text("\n".join(lines), encoding="utf-8")

    print(f"  Written: {inv_dir.name}/")


# ──────────────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────────────

def main():
    # Task 1: GROUND_TRUTH.md for each pattern folder
    folders = sorted(BASE.iterdir())
    processed = 0
    for folder in folders:
        if not folder.is_dir():
            continue
        name = folder.name
        if name.startswith("_") or name == "ground_truth":
            continue
        gt_path = folder / "ground_truth.json"
        if not gt_path.exists():
            continue
        print(f"Building GROUND_TRUTH.md for {name} ...")
        md = build_ground_truth_md(folder)
        if md:
            (folder / "GROUND_TRUTH.md").write_text(md, encoding="utf-8")
            processed += 1

    print(f"\nTask 1 complete: {processed} GROUND_TRUTH.md files written.\n")

    # Task 2: Investigation framework
    inv_root = BASE / "ground_truth" / "investigations"
    inv_root.mkdir(parents=True, exist_ok=True)

    print("Building investigation case files ...")
    for inv in INVESTIGATIONS:
        inv_dir = inv_root / inv["folder"]
        write_investigation(inv, inv_dir)

    # Write index
    idx_lines = [
        "# Investigation Cases Index",
        "",
        "Each sub-folder is a complete cybercrime investigation case for testing the Case Reconstruction Engine.",
        "",
        "| ID | Title | Fraud Type | Patterns |",
        "|----|-------|-----------|---------|",
    ]
    for inv in INVESTIGATIONS:
        pats = ", ".join(p.replace("_", " ") for p in inv["patterns"])
        idx_lines.append(f"| {inv['id']} | [{inv['title']}]({inv['folder']}/CASE_DESCRIPTION.md) | {inv['fraud_type']} | {pats} |")
    idx_lines += [
        "",
        "## How to Use",
        "",
        "1. Open the `CASE_DESCRIPTION.md` to understand the investigation scenario.",
        "2. Open the statement files listed in each case (from the source pattern folders).",
        "3. Run the Case Reconstruction Engine on those statements.",
        "4. Compare the engine output against `EXPECTED_RECONSTRUCTION.md`.",
        "5. Verify all patterns in `EXPECTED_PATTERNS.md` fired.",
        "6. Verify no patterns in `EXPECTED_NON_FINDINGS.md` fired.",
        "7. Check the narrative quality against `EXPECTED_FINDINGS.md`.",
        "",
    ]
    (inv_root / "INDEX.md").write_text("\n".join(idx_lines), encoding="utf-8")

    print(f"\nTask 2 complete: {len(INVESTIGATIONS)} investigation cases written to ground_truth/investigations/")


if __name__ == "__main__":
    main()
