# Pattern 13 — Low_value_testing

## Objective

Detects reciprocal micro-transfers (₹1–₹50) flowing in both directions between two accounts, a classic account validation or channel-testing technique used before large fraud transfers.

## Dataset Files

| Role | Statement File | Bank | Account Number |
|------|---------------|------|----------------|
| Originator | `78878611072845 statement.xlsx` | HDFC BANK LTD | 78878611072845 |
| Counterparty | `76722295363979 statement.xlsx` | HDFC BANK LTD | 76722295363979 |
| Clean Control | `4461116152003187-02-12-2024to09-05-2026.xlsx` | BANK OF BARODA | 4461116152003187 |
| Clean Control | `971912244714012_statement.pdf` | AXIS BANK LIMITED | 971912244714012 |
| Clean Control | `statement-94316247379.csv` | STATE BANK OF INDIA | 94316247379 |

## Accounts Involved

### Originator — HDFC BANK LTD · 78878611072845
- **Statement:** `78878611072845 statement.xlsx`
- **Full File Path:** `statements/78878611072845 statement.xlsx`

### Counterparty — HDFC BANK LTD · 76722295363979
- **Statement:** `76722295363979 statement.xlsx`
- **Full File Path:** `statements/76722295363979 statement.xlsx`

### Clean Control — BANK OF BARODA · 4461116152003187
- **Statement:** `4461116152003187-02-12-2024to09-05-2026.xlsx`
- **Full File Path:** `statements/4461116152003187-02-12-2024to09-05-2026.xlsx`

### Clean Control — AXIS BANK LIMITED · 971912244714012
- **Statement:** `971912244714012_statement.pdf`
- **Full File Path:** `statements/971912244714012_statement.pdf`

### Clean Control — STATE BANK OF INDIA · 94316247379
- **Statement:** `statement-94316247379.csv`
- **Full File Path:** `statements/statement-94316247379.csv`

## Expected Findings

### Pattern 13 — Low Value Testing

**Severity:** HIGH  
**Pattern ID:** 13  
**Amount Range:** ₹2.18 – ₹23.80  
**Reason:** Reciprocal low-value probes on both real account sides.  

**Accounts Involved:**

- **Originator** — HDFC BANK LTD, Account `78878611072845` (`78878611072845 statement.xlsx`)
- **Counterparty** — HDFC BANK LTD, Account `76722295363979` (`76722295363979 statement.xlsx`)

## Supporting Transactions

Open the listed statement file and locate these transactions to verify this finding:

| Date | Type | Amount (₹) | Narration | Reference / UTR |
|------|------|------------|-----------|-----------------|
| 04-09-2025 | Debit | 23.80 | UPI-SEEMA ROY-seema849@okicici-909929827484-DR VIA UPI | `U81817581718` |
| 05-09-2025 | Credit | 15.72 | UPI-SEEMA ROY-seema849@okicici-850467826097-CR VIA UPI | `U12498477381` |
| 06-09-2025 | Debit | 19.69 | UPI-SEEMA ROY-seema849@okicici-180603853622-DR VIA UPI | `U55476301778` |
| 07-09-2025 | Credit | 2.18 | UPI-SEEMA ROY-seema849@okicici-563176009283-CR VIA UPI | `U61100377626` |
| 08-09-2025 | Debit | 11.40 | UPI-SEEMA ROY-seema849@okicici-612744639382-DR VIA UPI | `U66835788905` |

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
