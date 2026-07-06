# Pattern 01 — Duplicate_verification

## Objective

Detects when the exact same transaction row appears twice in a statement. Both rows share the same reference number, amount, and narration — evidence of a processing error or deliberate manipulation.

## Dataset Files

| Role | Statement File | Bank | Account Number |
|------|---------------|------|----------------|
| Subject | `statement-01317032607.xlsx` | STATE BANK OF INDIA | 01317032607 |
| Clean Control | `39198147025911_SOA.pdf` | BANDHAN BANK LIMITED | 39198147025911 |
| Clean Control | `0709015866_statement.csv` | KOTAK MAHINDRA BANK LTD | 0709015866 |

## Accounts Involved

### Subject — STATE BANK OF INDIA · 01317032607
- **Statement:** `statement-01317032607.xlsx`
- **Full File Path:** `statements/statement-01317032607.xlsx`

### Clean Control — BANDHAN BANK LIMITED · 39198147025911
- **Statement:** `39198147025911_SOA.pdf`
- **Full File Path:** `statements/39198147025911_SOA.pdf`

### Clean Control — KOTAK MAHINDRA BANK LTD · 0709015866
- **Statement:** `0709015866_statement.csv`
- **Full File Path:** `statements/0709015866_statement.csv`

## Expected Findings

### Pattern 1 — Duplicate Verification

**Severity:** HIGH  
**Pattern ID:** 1  
**Amount:** ₹21,800.66  
**Reason:** Exact duplicate row embedded in realistic surrounding activity.  

**Accounts Involved:**

- **Subject** — STATE BANK OF INDIA, Account `01317032607` (`statement-01317032607.xlsx`)

## Supporting Transactions

Open the listed statement file and locate these transactions to verify this finding:

| Date | Type | Amount (₹) | Narration | Reference / UTR |
|------|------|------------|-----------|-----------------|
| 10-08-2025 | Debit | 21,800.66 | INB IMPS/I11395059790/Mina Sethi/HDFC | `I11395059790` |

## Expected Non-Findings

The following pattern detectors must NOT trigger on this dataset:

| Pattern ID | Pattern Name | Reason |
|-----------|--------------|--------|
| 7 | circular flow | No unrelated fixture planted for this pattern. |

## Validation Notes

To manually verify this ground truth:

1. Open each statement file listed in **Dataset Files** above.
2. Search for each **Reference / UTR** value in the reference/narration columns.
3. Confirm the transaction date, amount, and type match the values above.
4. Confirm no other pattern detector fires on accounts listed as clean controls.
5. Dataset seed: `2025` — re-running the generator with this seed reproduces identical files.
