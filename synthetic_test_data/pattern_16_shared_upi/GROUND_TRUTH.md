# Pattern 16 — Shared_upi

## Objective

Detects the same UPI handle or beneficiary identifier appearing across two or more separate account statements, linking accounts that are nominally unrelated.

## Dataset Files

| Role | Statement File | Bank | Account Number |
|------|---------------|------|----------------|
| Subject | `6752720432718688-03-12-2024to09-05-2026.csv` | UCO BANK | 6752720432718688 |
| Subject | `172372078937018_statement.pdf` | AXIS BANK LIMITED | 172372078937018 |
| Clean Control | `2818640871270954_statement.txt` | PUNJAB NATIONAL BANK | 2818640871270954 |
| Clean Control | `1885944132930321-01-12-2024to09-05-2026.pdf` | UCO BANK | 1885944132930321 |

## Accounts Involved

### Subject — UCO BANK · 6752720432718688
- **Statement:** `6752720432718688-03-12-2024to09-05-2026.csv`
- **Full File Path:** `statements/6752720432718688-03-12-2024to09-05-2026.csv`

### Subject — AXIS BANK LIMITED · 172372078937018
- **Statement:** `172372078937018_statement.pdf`
- **Full File Path:** `statements/172372078937018_statement.pdf`

### Clean Control — PUNJAB NATIONAL BANK · 2818640871270954
- **Statement:** `2818640871270954_statement.txt`
- **Full File Path:** `statements/2818640871270954_statement.txt`

### Clean Control — UCO BANK · 1885944132930321
- **Statement:** `1885944132930321-01-12-2024to09-05-2026.pdf`
- **Full File Path:** `statements/1885944132930321-01-12-2024to09-05-2026.pdf`

## Expected Findings

### Pattern 16 — Shared Upi

**Severity:** HIGH  
**Pattern ID:** 16  
**Amount Range:** ₹1,840.32 – ₹6,240.71  
**Reason:** Handle prashant71@kotak appears across separate account statements.  

**Accounts Involved:**

- **Subject** — UCO BANK, Account `6752720432718688` (`6752720432718688-03-12-2024to09-05-2026.csv`)
- **Subject** — AXIS BANK LIMITED, Account `172372078937018` (`172372078937018_statement.pdf`)

## Supporting Transactions

Open the listed statement file and locate these transactions to verify this finding:

| Date | Type | Amount (₹) | Narration | Reference / UTR |
|------|------|------------|-----------|-----------------|
| 18-04-2025 | Credit/Debit | UPI/DR/889430226747/Common/UCO/prashant71@kotak/UPI | UPI/DR/889430226747/Common/UCO/prashant71@kotak/UPI | `580122021174` |
| — | — | 1,840.32–6,240.71 | _(see statement)_ | `369710809810` |

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
