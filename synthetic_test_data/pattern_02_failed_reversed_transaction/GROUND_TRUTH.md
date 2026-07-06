# Pattern 02 — Failed_reversed_transaction

## Objective

Detects a debit transaction that is subsequently reversed by a matching credit of the same amount. Often seen in fraudulent transfer attempts that are caught and reversed, or in fee exploitation schemes.

## Dataset Files

| Role | Statement File | Bank | Account Number |
|------|---------------|------|----------------|
| Subject | `610050431188751_statement.csv` | AXIS BANK LIMITED | 610050431188751 |
| Clean Control | `77849479467322 statement.csv` | HDFC BANK LTD | 77849479467322 |
| Clean Control | `51051343030311_SOA.xlsx` | BANDHAN BANK LIMITED | 51051343030311 |
| Clean Control | `4580064736_statement.xlsx` | KOTAK MAHINDRA BANK LTD | 4580064736 |

## Accounts Involved

### Subject — AXIS BANK LIMITED · 610050431188751
- **Statement:** `610050431188751_statement.csv`
- **Full File Path:** `statements/610050431188751_statement.csv`

### Clean Control — HDFC BANK LTD · 77849479467322
- **Statement:** `77849479467322 statement.csv`
- **Full File Path:** `statements/77849479467322 statement.csv`

### Clean Control — BANDHAN BANK LIMITED · 51051343030311
- **Statement:** `51051343030311_SOA.xlsx`
- **Full File Path:** `statements/51051343030311_SOA.xlsx`

### Clean Control — KOTAK MAHINDRA BANK LTD · 4580064736
- **Statement:** `4580064736_statement.xlsx`
- **Full File Path:** `statements/4580064736_statement.xlsx`

## Expected Findings

### Pattern 2 — Failed Reversed Transaction

**Severity:** HIGH  
**Pattern ID:** 2  
**Amount:** ₹20,000.97  
**Reason:** Debit followed by credit reversal for the exact same amount.  

**Accounts Involved:**

- **Subject** — AXIS BANK LIMITED, Account `610050431188751` (`610050431188751_statement.csv`)

## Supporting Transactions

Open the listed statement file and locate these transactions to verify this finding:

| Date | Type | Amount (₹) | Narration | Reference / UTR |
|------|------|------------|-----------|-----------------|
| 02-04-2025 | Credit/Debit | NEFT/I78322984623/Harish Rao/BKID0608861 | NEFT/I78322984623/Harish Rao/BKID0608861 | `I78322984623` |
| 04-04-2025 | Credit | RETURN/I78322984623/TRANSACTION FAILED | RETURN/I78322984623/TRANSACTION FAILED | `457389211895` |

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
