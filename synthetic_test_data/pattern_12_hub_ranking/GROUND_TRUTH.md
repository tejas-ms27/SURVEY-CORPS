# Pattern 12 — Hub_ranking

## Objective

Detects a central hub account that receives funds from an unusually large number of distinct sender accounts within the analysis window, a hallmark of mule network aggregation.

## Dataset Files

| Role | Statement File | Bank | Account Number |
|------|---------------|------|----------------|
| Hub | `94079742466285_SOA.pdf` | BANDHAN BANK LIMITED | 94079742466285 |
| Spoke | `5112945020_statement.xlsx` | KOTAK MAHINDRA BANK LTD | 5112945020 |
| Spoke | `3982799780574773-01-12-2024to09-05-2026.xlsx` | BANK OF BARODA | 3982799780574773 |
| Spoke | `5007288473965366-01-12-2024to09-05-2026.xlsx` | UCO BANK | 5007288473965366 |
| Spoke | `9233632350372247-01-12-2024to09-05-2026.csv` | BANK OF INDIA | 9233632350372247 |
| Spoke | `35986543405557-01-12-2024to09-05-2026.csv` | THE FEDERAL BANK LIMITED | 35986543405557 |
| Spoke | `8687279450866072_statement.pdf` | PUNJAB NATIONAL BANK | 8687279450866072 |
| Spoke | `9517122164_statement.pdf` | KOTAK MAHINDRA BANK LTD | 9517122164 |
| Clean Control | `6325120086_statement.xlsx` | KOTAK MAHINDRA BANK LTD | 6325120086 |
| Clean Control | `6263452588_statement.csv` | KOTAK MAHINDRA BANK LTD | 6263452588 |
| Clean Control | `3656963468_statement.pdf` | KOTAK MAHINDRA BANK LTD | 3656963468 |

## Accounts Involved

### Hub — BANDHAN BANK LIMITED · 94079742466285
- **Statement:** `94079742466285_SOA.pdf`
- **Full File Path:** `statements/94079742466285_SOA.pdf`

### Spoke — KOTAK MAHINDRA BANK LTD · 5112945020
- **Statement:** `5112945020_statement.xlsx`
- **Full File Path:** `statements/5112945020_statement.xlsx`

### Spoke — BANK OF BARODA · 3982799780574773
- **Statement:** `3982799780574773-01-12-2024to09-05-2026.xlsx`
- **Full File Path:** `statements/3982799780574773-01-12-2024to09-05-2026.xlsx`

### Spoke — UCO BANK · 5007288473965366
- **Statement:** `5007288473965366-01-12-2024to09-05-2026.xlsx`
- **Full File Path:** `statements/5007288473965366-01-12-2024to09-05-2026.xlsx`

### Spoke — BANK OF INDIA · 9233632350372247
- **Statement:** `9233632350372247-01-12-2024to09-05-2026.csv`
- **Full File Path:** `statements/9233632350372247-01-12-2024to09-05-2026.csv`

### Spoke — THE FEDERAL BANK LIMITED · 35986543405557
- **Statement:** `35986543405557-01-12-2024to09-05-2026.csv`
- **Full File Path:** `statements/35986543405557-01-12-2024to09-05-2026.csv`

### Spoke — PUNJAB NATIONAL BANK · 8687279450866072
- **Statement:** `8687279450866072_statement.pdf`
- **Full File Path:** `statements/8687279450866072_statement.pdf`

### Spoke — KOTAK MAHINDRA BANK LTD · 9517122164
- **Statement:** `9517122164_statement.pdf`
- **Full File Path:** `statements/9517122164_statement.pdf`

### Clean Control — KOTAK MAHINDRA BANK LTD · 6325120086
- **Statement:** `6325120086_statement.xlsx`
- **Full File Path:** `statements/6325120086_statement.xlsx`

### Clean Control — KOTAK MAHINDRA BANK LTD · 6263452588
- **Statement:** `6263452588_statement.csv`
- **Full File Path:** `statements/6263452588_statement.csv`

### Clean Control — KOTAK MAHINDRA BANK LTD · 3656963468
- **Statement:** `3656963468_statement.pdf`
- **Full File Path:** `statements/3656963468_statement.pdf`

## Expected Findings

### Pattern 12 — Hub Ranking

**Severity:** HIGH  
**Pattern ID:** 12  
**Amount Range:** ₹15,900.07 – ₹67,600.57  
**Reason:** Hub receives from 6-8 spoke accounts with corroborating statements.  

**Accounts Involved:**

- **Hub** — BANDHAN BANK LIMITED, Account `94079742466285` (`94079742466285_SOA.pdf`)
- **Spoke** — KOTAK MAHINDRA BANK LTD, Account `5112945020` (`5112945020_statement.xlsx`)
- **Spoke** — BANK OF BARODA, Account `3982799780574773` (`3982799780574773-01-12-2024to09-05-2026.xlsx`)
- **Spoke** — UCO BANK, Account `5007288473965366` (`5007288473965366-01-12-2024to09-05-2026.xlsx`)
- **Spoke** — BANK OF INDIA, Account `9233632350372247` (`9233632350372247-01-12-2024to09-05-2026.csv`)
- **Spoke** — THE FEDERAL BANK LIMITED, Account `35986543405557` (`35986543405557-01-12-2024to09-05-2026.csv`)
- **Spoke** — PUNJAB NATIONAL BANK, Account `8687279450866072` (`8687279450866072_statement.pdf`)
- **Spoke** — KOTAK MAHINDRA BANK LTD, Account `9517122164` (`9517122164_statement.pdf`)

## Supporting Transactions

Open the listed statement file and locate these transactions to verify this finding:

| Date | Type | Amount (₹) | Narration | Reference / UTR |
|------|------|------------|-----------|-----------------|
| 20-08-2025 | Debit | 43,600.78 | UPI/DR/527600328756/MOHIT/BDBL/4426519181@apl/UPI | `U20407131625` |
| 21-08-2025 | Debit | 49,700.48 | IMPS-I54731840427-MOHIT SHAH | `I54731840427` |
| 22-08-2025 | Debit | 20,600.67 | NEFT/N82261038226/MOHIT SHAH | `N82261038226` |
| 23-08-2025 | Credit/Debit | NEFT/N60819842972/MOHIT SHAH | NEFT/N60819842972/MOHIT SHAH | `N60819842972` |
| 20-08-2025 | Credit/Debit | NEFT/N46803727233/MOHIT SHAH | NEFT/N46803727233/MOHIT SHAH | `N46803727233` |
| 21-08-2025 | Credit | 67,600.57 | 21-08-2025 IMPS-I82173013339-MOHIT SHAH | `I82173013339` |
| 22-08-2025 | Credit | 53,800.96 | IMPS-I22511245968-MOHIT SHAH | `I22511245968` |

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
