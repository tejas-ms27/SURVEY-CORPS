# Pattern 17 — Round_trip

## Objective

Detects a round-trip pattern where funds sent from Account A reach Account B via an intermediary and are subsequently returned to Account A through a different channel.

## Dataset Files

| Role | Statement File | Bank | Account Number |
|------|---------------|------|----------------|
| Originator | `98036543420467_SOA.xlsx` | BANDHAN BANK LIMITED | 98036543420467 |
| Recipient | `4258497598930953-01-12-2024to09-05-2026.pdf` | BANK OF INDIA | 4258497598930953 |
| Clean Control | `1494217892566411-01-12-2024to09-05-2026.csv` | BANK OF BARODA | 1494217892566411 |
| Clean Control | `5944733842_statement.csv` | KOTAK MAHINDRA BANK LTD | 5944733842 |
| Clean Control | `statement-58418814459.txt` | STATE BANK OF INDIA | 58418814459 |

## Accounts Involved

### Originator — BANDHAN BANK LIMITED · 98036543420467
- **Statement:** `98036543420467_SOA.xlsx`
- **Full File Path:** `statements/98036543420467_SOA.xlsx`

### Recipient — BANK OF INDIA · 4258497598930953
- **Statement:** `4258497598930953-01-12-2024to09-05-2026.pdf`
- **Full File Path:** `statements/4258497598930953-01-12-2024to09-05-2026.pdf`

### Clean Control — BANK OF BARODA · 1494217892566411
- **Statement:** `1494217892566411-01-12-2024to09-05-2026.csv`
- **Full File Path:** `statements/1494217892566411-01-12-2024to09-05-2026.csv`

### Clean Control — KOTAK MAHINDRA BANK LTD · 5944733842
- **Statement:** `5944733842_statement.csv`
- **Full File Path:** `statements/5944733842_statement.csv`

### Clean Control — STATE BANK OF INDIA · 58418814459
- **Statement:** `statement-58418814459.txt`
- **Full File Path:** `statements/statement-58418814459.txt`

## Expected Findings

### Pattern 17 — Round Trip

**Severity:** HIGH  
**Pattern ID:** 17  
**Amount Range:** ₹354,676.31 – ₹400,000.25  
**Reason:** Out-and-back round-trip via different channels; all sides have statements.  

**Accounts Involved:**

- **Originator** — BANDHAN BANK LIMITED, Account `98036543420467` (`98036543420467_SOA.xlsx`)
- **Recipient** — BANK OF INDIA, Account `4258497598930953` (`4258497598930953-01-12-2024to09-05-2026.pdf`)

## Supporting Transactions

Open the listed statement file and locate these transactions to verify this finding:

| Date | Type | Amount (₹) | Narration | Reference / UTR |
|------|------|------------|-----------|-----------------|
| 19-05-2025 | Debit | 400,000.25 | NEFT/N94773093765/REKHA KHANNA | `N94773093765` |
| 21-05-2025 | Credit | 354,676.31 | IMPS-I00293152286-REKHA KHANNA | `I00293152286` |

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
