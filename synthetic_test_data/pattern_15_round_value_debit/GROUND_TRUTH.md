# Pattern 15 — Round_value_debit

## Objective

Detects clusters of outward transfers in round rupee values (multiples of ₹5,000 or ₹10,000) occurring in the same period as non-round routine spending, inconsistent with normal behaviour.

## Dataset Files

| Role | Statement File | Bank | Account Number |
|------|---------------|------|----------------|
| Subject | `26544584572587-02-12-2024to08-05-2026.xlsx` | THE FEDERAL BANK LIMITED | 26544584572587 |
| Clean Control | `0404420836075563-01-12-2024to08-05-2026.csv` | BANK OF INDIA | 0404420836075563 |
| Clean Control | `812456323108126_statement.xlsx` | AXIS BANK LIMITED | 812456323108126 |

## Accounts Involved

### Subject — THE FEDERAL BANK LIMITED · 26544584572587
- **Statement:** `26544584572587-02-12-2024to08-05-2026.xlsx`
- **Full File Path:** `statements/26544584572587-02-12-2024to08-05-2026.xlsx`

### Clean Control — BANK OF INDIA · 0404420836075563
- **Statement:** `0404420836075563-01-12-2024to08-05-2026.csv`
- **Full File Path:** `statements/0404420836075563-01-12-2024to08-05-2026.csv`

### Clean Control — AXIS BANK LIMITED · 812456323108126
- **Statement:** `812456323108126_statement.xlsx`
- **Full File Path:** `statements/812456323108126_statement.xlsx`

## Expected Findings

### Pattern 15 — Round Value Debit

**Severity:** MEDIUM  
**Pattern ID:** 15  
**Amount Range:** ₹35,000.00 – ₹85,000.00  
**Reason:** Cluster of round-value outward transfers amid non-round routine spending.  

**Accounts Involved:**

- **Subject** — THE FEDERAL BANK LIMITED, Account `26544584572587` (`26544584572587-02-12-2024to08-05-2026.xlsx`)

## Supporting Transactions

Open the listed statement file and locate these transactions to verify this finding:

| Date | Type | Amount (₹) | Narration | Reference / UTR |
|------|------|------------|-----------|-----------------|
| 29-04-2025 | Debit | 35,000.00 | NEFT/N00892941220/Ajay Shah | `796750451798` |
| 01-05-2025 | Debit | 55,000.00 | NEFT/N73271293346/Ajay Shah | `009738249064` |
| 03-05-2025 | Debit | 75,000.00 | NEFT/N35816904304/Ajay Shah | `277557049823` |
| 05-05-2025 | Debit | 50,000.00 | NEFT/N53871149672/Ajay Shah | `351853494561` |
| 07-05-2025 | Debit | 50,000.00 | NEFT/N07491940442/Ajay Shah | `914801226817` |
| 09-05-2025 | Debit | 85,000.00 | NEFT/N48924913393/Ajay Shah | `582091455129` |
| 11-05-2025 | Debit | 55,000.00 | NEFT/N06071523247/Ajay Shah | `030400975567` |

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
