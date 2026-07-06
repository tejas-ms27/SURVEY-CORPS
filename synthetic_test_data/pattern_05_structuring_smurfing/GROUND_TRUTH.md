# Pattern 05 — Structuring_smurfing

## Objective

Detects a pattern of cash deposits each staying just below the ₹50,000 reporting threshold. Consistent with deliberate structuring to evade currency transaction reporting obligations.

## Dataset Files

| Role | Statement File | Bank | Account Number |
|------|---------------|------|----------------|
| Subject | `01441964801494 statement.pdf` | HDFC BANK LTD | 01441964801494 |
| Clean Control | `59731337686839-01-12-2024to09-05-2026.csv` | THE FEDERAL BANK LIMITED | 59731337686839 |
| Clean Control | `2577033909619367-01-12-2024to09-05-2026.xlsx` | BANK OF BARODA | 2577033909619367 |
| Clean Control | `371676562339215_statement.xlsx` | AXIS BANK LIMITED | 371676562339215 |

## Accounts Involved

### Subject — HDFC BANK LTD · 01441964801494
- **Statement:** `01441964801494 statement.pdf`
- **Full File Path:** `statements/01441964801494 statement.pdf`

### Clean Control — THE FEDERAL BANK LIMITED · 59731337686839
- **Statement:** `59731337686839-01-12-2024to09-05-2026.csv`
- **Full File Path:** `statements/59731337686839-01-12-2024to09-05-2026.csv`

### Clean Control — BANK OF BARODA · 2577033909619367
- **Statement:** `2577033909619367-01-12-2024to09-05-2026.xlsx`
- **Full File Path:** `statements/2577033909619367-01-12-2024to09-05-2026.xlsx`

### Clean Control — AXIS BANK LIMITED · 371676562339215
- **Statement:** `371676562339215_statement.xlsx`
- **Full File Path:** `statements/371676562339215_statement.xlsx`

## Expected Findings

### Pattern 5 — Structuring Smurfing

**Severity:** HIGH  
**Pattern ID:** 5  
**Amount Range:** ₹42,200.00 – ₹49,900.00  
**Reason:** Repeated cash deposits just below a common reporting threshold.  

**Accounts Involved:**

- **Subject** — HDFC BANK LTD, Account `01441964801494` (`01441964801494 statement.pdf`)

## Supporting Transactions

Open the listed statement file and locate these transactions to verify this finding:

| Date | Type | Amount (₹) | Narration | Reference / UTR |
|------|------|------------|-----------|-----------------|
| — | — | 42,200.00–49,900.00 | _(see statement)_ | `526241052483` |
| — | — | 42,200.00–49,900.00 | _(see statement)_ | `532521735031` |
| — | — | 42,200.00–49,900.00 | _(see statement)_ | `871401609943` |
| — | — | 42,200.00–49,900.00 | _(see statement)_ | `838468610909` |
| — | — | 42,200.00–49,900.00 | _(see statement)_ | `857019413251` |
| — | — | 42,200.00–49,900.00 | _(see statement)_ | `138970001673` |

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
