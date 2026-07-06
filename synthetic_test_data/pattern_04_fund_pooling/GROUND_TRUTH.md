# Pattern 04 — Fund_pooling

## Objective

Detects rapid accumulation of funds from multiple senders within a short window, consistent with a pooling account aggregating proceeds before onward disbursement.

## Dataset Files

| Role | Statement File | Bank | Account Number |
|------|---------------|------|----------------|
| Subject | `39557477253057 statement.csv` | HDFC BANK LTD | 39557477253057 |
| Clean Control | `9611224309_statement.xlsx` | KOTAK MAHINDRA BANK LTD | 9611224309 |
| Clean Control | `2749784479808556-01-12-2024to09-05-2026.csv` | BANK OF BARODA | 2749784479808556 |
| Clean Control | `statement-30063705300.pdf` | STATE BANK OF INDIA | 30063705300 |

## Accounts Involved

### Subject — HDFC BANK LTD · 39557477253057
- **Statement:** `39557477253057 statement.csv`
- **Full File Path:** `statements/39557477253057 statement.csv`

### Clean Control — KOTAK MAHINDRA BANK LTD · 9611224309
- **Statement:** `9611224309_statement.xlsx`
- **Full File Path:** `statements/9611224309_statement.xlsx`

### Clean Control — BANK OF BARODA · 2749784479808556
- **Statement:** `2749784479808556-01-12-2024to09-05-2026.csv`
- **Full File Path:** `statements/2749784479808556-01-12-2024to09-05-2026.csv`

### Clean Control — STATE BANK OF INDIA · 30063705300
- **Statement:** `statement-30063705300.pdf`
- **Full File Path:** `statements/statement-30063705300.pdf`

## Expected Findings

### Pattern 4 — Fund Pooling

**Severity:** HIGH  
**Pattern ID:** 4  
**Amount Range:** ₹18,100.99 – ₹69,600.90  
**Reason:** Fund pooling from multiple unrelated senders within a short window.  

**Accounts Involved:**

- **Subject** — HDFC BANK LTD, Account `39557477253057` (`39557477253057 statement.csv`)

## Supporting Transactions

Open the listed statement file and locate these transactions to verify this finding:

| Date | Type | Amount (₹) | Narration | Reference / UTR |
|------|------|------------|-----------|-----------------|
| 28/04/25 | Credit | UPI-Kamal Naik-2410792575@paytm-016147460181-CR VIA UPI | UPI-Kamal Naik-2410792575@paytm-016147460181-CR VIA UPI | `067273453130` |
| 29/04/25 | Credit | UPI-Yogesh Nair-3312574435@oksbi-273628585722-CR VIA UPI | UPI-Yogesh Nair-3312574435@oksbi-273628585722-CR VIA UPI | `356388427384` |
| 26/04/25 | Credit | UPI-Tarun Menon-tarun.menon@okhdfcbank-696469851865-CR VIA UPI | UPI-Tarun Menon-tarun.menon@okhdfcbank-696469851865-CR VIA UPI | `634304489068` |
| 28/04/25 | Credit | UPI-Ashish Kulkarni-6484489431@okhdfcbank-344297117385-CR VIA UPI | UPI-Ashish Kulkarni-6484489431@okhdfcbank-344297117385-CR VIA UPI | `683870942331` |
| 29/04/25 | Credit | UPI-Neha Patel-neha976@ptsbi-552124658383-CR VIA UPI | UPI-Neha Patel-neha976@ptsbi-552124658383-CR VIA UPI | `534965595598` |
| 27/04/25 | Credit | UPI-Ravi Pandey-5809094888@upi-038028177825-CR VIA UPI | UPI-Ravi Pandey-5809094888@upi-038028177825-CR VIA UPI | `718241825047` |
| 27/04/25 | Credit | UPI-Anjali Bose-0979827143@ibl-285453417097-CR VIA UPI | UPI-Anjali Bose-0979827143@ibl-285453417097-CR VIA UPI | `287101406851` |
| 25/04/25 | Credit | UPI-Rekha Iyer-rekha145@ptyes-185653037644-CR VIA UPI | UPI-Rekha Iyer-rekha145@ptyes-185653037644-CR VIA UPI | `118298163839` |

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
