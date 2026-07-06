# Pattern 11 — Balance_parking

## Objective

Detects a large credit that remains substantially unspent in an account for an extended period, suggesting the account is being used as a parking vehicle rather than for normal commerce.

## Dataset Files

| Role | Statement File | Bank | Account Number |
|------|---------------|------|----------------|
| Subject | `statement-08959469915.xlsx` | STATE BANK OF INDIA | 08959469915 |
| Clean Control | `3851062425_statement.xlsx` | KOTAK MAHINDRA BANK LTD | 3851062425 |
| Clean Control | `97556000042808-01-12-2024to08-05-2026.csv` | THE FEDERAL BANK LIMITED | 97556000042808 |
| Clean Control | `85173206686139 statement.xlsx` | HDFC BANK LTD | 85173206686139 |
| Clean Control | `8008270503_statement.csv` | KOTAK MAHINDRA BANK LTD | 8008270503 |

## Accounts Involved

### Subject — STATE BANK OF INDIA · 08959469915
- **Statement:** `statement-08959469915.xlsx`
- **Full File Path:** `statements/statement-08959469915.xlsx`

### Clean Control — KOTAK MAHINDRA BANK LTD · 3851062425
- **Statement:** `3851062425_statement.xlsx`
- **Full File Path:** `statements/3851062425_statement.xlsx`

### Clean Control — THE FEDERAL BANK LIMITED · 97556000042808
- **Statement:** `97556000042808-01-12-2024to08-05-2026.csv`
- **Full File Path:** `statements/97556000042808-01-12-2024to08-05-2026.csv`

### Clean Control — HDFC BANK LTD · 85173206686139
- **Statement:** `85173206686139 statement.xlsx`
- **Full File Path:** `statements/85173206686139 statement.xlsx`

### Clean Control — KOTAK MAHINDRA BANK LTD · 8008270503
- **Statement:** `8008270503_statement.csv`
- **Full File Path:** `statements/8008270503_statement.csv`

## Expected Findings

### Pattern 11 — Balance Parking

**Severity:** HIGH  
**Pattern ID:** 11  
**Amount:** ₹464,000.95  
**Reason:** Large credit remains parked; subsequent activity is minor.  

**Accounts Involved:**

- **Subject** — STATE BANK OF INDIA, Account `08959469915` (`statement-08959469915.xlsx`)

## Supporting Transactions

Open the listed statement file and locate these transactions to verify this finding:

| Date | Type | Amount (₹) | Narration | Reference / UTR |
|------|------|------------|-----------|-----------------|
| — | — | ~464,000.95 | _(see statement)_ | `845965912536` |

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
