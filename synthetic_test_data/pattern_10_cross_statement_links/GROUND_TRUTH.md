# Pattern 10 — Cross_statement_links

## Objective

Detects the same bank reference or UTR number appearing across two independent account statements from different account holders, confirming a cross-account money movement.

## Dataset Files

| Role | Statement File | Bank | Account Number |
|------|---------------|------|----------------|
| Originator | `6212049558977599_statement.pdf` | PUNJAB NATIONAL BANK | 6212049558977599 |
| Counterparty | `948472954416051_statement.xlsx` | AXIS BANK LIMITED | 948472954416051 |
| Clean Control | `statement-91190116136.pdf` | STATE BANK OF INDIA | 91190116136 |
| Clean Control | `62426182162468-01-12-2024to09-05-2026.csv` | THE FEDERAL BANK LIMITED | 62426182162468 |
| Clean Control | `statement-80913660582.xlsx` | STATE BANK OF INDIA | 80913660582 |
| Clean Control | `0984146900879825-02-12-2024to09-05-2026.pdf` | UCO BANK | 0984146900879825 |

## Accounts Involved

### Originator — PUNJAB NATIONAL BANK · 6212049558977599
- **Statement:** `6212049558977599_statement.pdf`
- **Full File Path:** `statements/6212049558977599_statement.pdf`

### Counterparty — AXIS BANK LIMITED · 948472954416051
- **Statement:** `948472954416051_statement.xlsx`
- **Full File Path:** `statements/948472954416051_statement.xlsx`

### Clean Control — STATE BANK OF INDIA · 91190116136
- **Statement:** `statement-91190116136.pdf`
- **Full File Path:** `statements/statement-91190116136.pdf`

### Clean Control — THE FEDERAL BANK LIMITED · 62426182162468
- **Statement:** `62426182162468-01-12-2024to09-05-2026.csv`
- **Full File Path:** `statements/62426182162468-01-12-2024to09-05-2026.csv`

### Clean Control — STATE BANK OF INDIA · 80913660582
- **Statement:** `statement-80913660582.xlsx`
- **Full File Path:** `statements/statement-80913660582.xlsx`

### Clean Control — UCO BANK · 0984146900879825
- **Statement:** `0984146900879825-02-12-2024to09-05-2026.pdf`
- **Full File Path:** `statements/0984146900879825-02-12-2024to09-05-2026.pdf`

## Expected Findings

### Pattern 10 — Cross Statement Links

**Severity:** HIGH  
**Pattern ID:** 10  
**Amount:** ₹240,000.36  
**Reason:** Same bank reference appears on two independent account statements.  

**Accounts Involved:**

- **Originator** — PUNJAB NATIONAL BANK, Account `6212049558977599` (`6212049558977599_statement.pdf`)
- **Counterparty** — AXIS BANK LIMITED, Account `948472954416051` (`948472954416051_statement.xlsx`)

## Supporting Transactions

Open the listed statement file and locate these transactions to verify this finding:

| Date | Type | Amount (₹) | Narration | Reference / UTR |
|------|------|------------|-----------|-----------------|
| 22-06-2025 | Credit | 240,000.36 | 22-06-2025 IMPS-I18033476443-SACHIN SEN | `I18033476443` |

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
