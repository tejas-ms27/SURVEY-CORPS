# Pattern 07 — Circular_flow

## Objective

Detects a closed-loop flow where funds originate from Account A, pass through one or more intermediaries, and eventually return to Account A, indicating layering or wash transactions.

## Dataset Files

| Role | Statement File | Bank | Account Number |
|------|---------------|------|----------------|
| Originator | `statement-44000827893.txt` | STATE BANK OF INDIA | 44000827893 |
| Intermediary | `48880432099033-01-12-2024to09-05-2026.pdf` | THE FEDERAL BANK LIMITED | 48880432099033 |
| Intermediary | `statement-96465802265.pdf` | STATE BANK OF INDIA | 96465802265 |
| Intermediary | `68699629400471 statement.csv` | HDFC BANK LTD | 68699629400471 |
| Recipient | `6332927949015177-01-12-2024to09-05-2026.pdf` | UCO BANK | 6332927949015177 |
| Clean Control | `statement-37853420993.txt` | STATE BANK OF INDIA | 37853420993 |
| Clean Control | `84975745891270 statement.pdf` | HDFC BANK LTD | 84975745891270 |

## Accounts Involved

### Originator — STATE BANK OF INDIA · 44000827893
- **Statement:** `statement-44000827893.txt`
- **Full File Path:** `statements/statement-44000827893.txt`

### Intermediary — THE FEDERAL BANK LIMITED · 48880432099033
- **Statement:** `48880432099033-01-12-2024to09-05-2026.pdf`
- **Full File Path:** `statements/48880432099033-01-12-2024to09-05-2026.pdf`

### Intermediary — STATE BANK OF INDIA · 96465802265
- **Statement:** `statement-96465802265.pdf`
- **Full File Path:** `statements/statement-96465802265.pdf`

### Intermediary — HDFC BANK LTD · 68699629400471
- **Statement:** `68699629400471 statement.csv`
- **Full File Path:** `statements/68699629400471 statement.csv`

### Recipient — UCO BANK · 6332927949015177
- **Statement:** `6332927949015177-01-12-2024to09-05-2026.pdf`
- **Full File Path:** `statements/6332927949015177-01-12-2024to09-05-2026.pdf`

### Clean Control — STATE BANK OF INDIA · 37853420993
- **Statement:** `statement-37853420993.txt`
- **Full File Path:** `statements/statement-37853420993.txt`

### Clean Control — HDFC BANK LTD · 84975745891270
- **Statement:** `84975745891270 statement.pdf`
- **Full File Path:** `statements/84975745891270 statement.pdf`

## Expected Findings

### Pattern 7 — Circular Flow

**Severity:** HIGH  
**Pattern ID:** 7  
**Amount Range:** ₹276,578.67 – ₹294,000.24  
**Reason:** Closed-loop circular flow; every hop corroborated by both statements.  

**Accounts Involved:**

- **Originator** — STATE BANK OF INDIA, Account `44000827893` (`statement-44000827893.txt`)
- **Intermediary** — THE FEDERAL BANK LIMITED, Account `48880432099033` (`48880432099033-01-12-2024to09-05-2026.pdf`)
- **Intermediary** — STATE BANK OF INDIA, Account `96465802265` (`statement-96465802265.pdf`)
- **Intermediary** — HDFC BANK LTD, Account `68699629400471` (`68699629400471 statement.csv`)
- **Recipient** — UCO BANK, Account `6332927949015177` (`6332927949015177-01-12-2024to09-05-2026.pdf`)

## Supporting Transactions

Open the listed statement file and locate these transactions to verify this finding:

| Date | Type | Amount (₹) | Narration | Reference / UTR |
|------|------|------------|-----------|-----------------|
| 07-08-2025 | Debit | 294,000.24 | INB NEFT-N21158961706/PREETI AHUJA/FDRL/DR | `N21158961706` |
| 08-08-2025 | Credit | 283,360.15 | NEFT/N49652837781/GOPAL SRIVASTAVA | `N49652837781` |
| 09-08-2025 | Credit | 284,358.16 | 09-08-2025 INB IMPS/I82260658072/GAURAV KHANNA/HDFC | `I82260658072` |
| 10/08/25 | Credit/Debit | RTGS-R76603974582-MANOJ JOSHI/UCBA0230918 | RTGS-R76603974582-MANOJ JOSHI/UCBA0230918 | `R76603974582` |
| 11-08-2025 | Credit | 289,258.71 | INB IMPS/I07572363242/MANOJ JOSHI/UCBA | `I07572363242` |

## Expected Non-Findings

The following pattern detectors must NOT trigger on this dataset:

| Pattern ID | Pattern Name | Reason |
|-----------|--------------|--------|
| 5 | structuring smurfing | No unrelated fixture planted for this pattern. |

## Validation Notes

To manually verify this ground truth:

1. Open each statement file listed in **Dataset Files** above.
2. Search for each **Reference / UTR** value in the reference/narration columns.
3. Confirm the transaction date, amount, and type match the values above.
4. Confirm no other pattern detector fires on accounts listed as clean controls.
5. Dataset seed: `2025` — re-running the generator with this seed reproduces identical files.
