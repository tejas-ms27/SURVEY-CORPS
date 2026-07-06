# Pattern 09 — Credit_to_cash_out

## Objective

Detects a large inward credit (NEFT/IMPS/UPI) followed within a short window by one or more ATM withdrawals of a near-equivalent total amount, suggesting rapid cash-out of proceeds.

## Dataset Files

| Role | Statement File | Bank | Account Number |
|------|---------------|------|----------------|
| Subject | `97094247189329-01-12-2024to09-05-2026.xlsx` | THE FEDERAL BANK LIMITED | 97094247189329 |
| Clean Control | `6563986075289003-01-12-2024to09-05-2026.csv` | BANK OF INDIA | 6563986075289003 |
| Clean Control | `2930199412632830_statement.pdf` | PUNJAB NATIONAL BANK | 2930199412632830 |
| Clean Control | `81505882184559-01-12-2024to09-05-2026.pdf` | THE FEDERAL BANK LIMITED | 81505882184559 |
| Clean Control | `9174418126063678_statement.txt` | PUNJAB NATIONAL BANK | 9174418126063678 |

## Accounts Involved

### Subject — THE FEDERAL BANK LIMITED · 97094247189329
- **Statement:** `97094247189329-01-12-2024to09-05-2026.xlsx`
- **Full File Path:** `statements/97094247189329-01-12-2024to09-05-2026.xlsx`

### Clean Control — BANK OF INDIA · 6563986075289003
- **Statement:** `6563986075289003-01-12-2024to09-05-2026.csv`
- **Full File Path:** `statements/6563986075289003-01-12-2024to09-05-2026.csv`

### Clean Control — PUNJAB NATIONAL BANK · 2930199412632830
- **Statement:** `2930199412632830_statement.pdf`
- **Full File Path:** `statements/2930199412632830_statement.pdf`

### Clean Control — THE FEDERAL BANK LIMITED · 81505882184559
- **Statement:** `81505882184559-01-12-2024to09-05-2026.pdf`
- **Full File Path:** `statements/81505882184559-01-12-2024to09-05-2026.pdf`

### Clean Control — PUNJAB NATIONAL BANK · 9174418126063678
- **Statement:** `9174418126063678_statement.txt`
- **Full File Path:** `statements/9174418126063678_statement.txt`

## Expected Findings

### Pattern 9 — Credit To Cash Out

**Severity:** HIGH  
**Pattern ID:** 9  
**Amount Range:** ₹116,766.09 – ₹152,000.70  
**Reason:** Large inward credit followed promptly by near-equivalent ATM withdrawal.  

**Accounts Involved:**

- **Subject** — THE FEDERAL BANK LIMITED, Account `97094247189329` (`97094247189329-01-12-2024to09-05-2026.xlsx`)

## Supporting Transactions

Open the listed statement file and locate these transactions to verify this finding:

| Date | Type | Amount (₹) | Narration | Reference / UTR |
|------|------|------------|-----------|-----------------|
| 08-05-2025 | Credit | 152,000.70 | NEFT/N75255709921/Tarun Sethi | `583185988545` |
| 10-05-2025 | Debit | 116,766.09 | ATM CASH WITHDRAWAL/63038/DELHI | `405664219433` |

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
