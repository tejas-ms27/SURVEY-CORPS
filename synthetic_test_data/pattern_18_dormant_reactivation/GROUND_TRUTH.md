# Pattern 18 — Dormant_reactivation

## Objective

Detects a long period of dormancy (no transactions) followed by a sudden burst of high-value activity, consistent with account reactivation for fraud use.

## Dataset Files

| Role | Statement File | Bank | Account Number |
|------|---------------|------|----------------|
| Subject | `1351667800484732-26-12-2024to19-10-2025.xlsx` | BANK OF BARODA | 1351667800484732 |
| Clean Control | `64062840118450_SOA.csv` | BANDHAN BANK LIMITED | 64062840118450 |
| Clean Control | `15530197371184 statement.xlsx` | HDFC BANK LTD | 15530197371184 |
| Clean Control | `50637967294429 statement.pdf` | HDFC BANK LTD | 50637967294429 |
| Clean Control | `8061995370719974-01-12-2024to09-05-2026.csv` | UCO BANK | 8061995370719974 |
| Clean Control | `0678492539681463-02-12-2024to09-05-2026.csv` | BANK OF BARODA | 0678492539681463 |

## Accounts Involved

### Subject — BANK OF BARODA · 1351667800484732
- **Statement:** `1351667800484732-26-12-2024to19-10-2025.xlsx`
- **Full File Path:** `statements/1351667800484732-26-12-2024to19-10-2025.xlsx`

### Clean Control — BANDHAN BANK LIMITED · 64062840118450
- **Statement:** `64062840118450_SOA.csv`
- **Full File Path:** `statements/64062840118450_SOA.csv`

### Clean Control — HDFC BANK LTD · 15530197371184
- **Statement:** `15530197371184 statement.xlsx`
- **Full File Path:** `statements/15530197371184 statement.xlsx`

### Clean Control — HDFC BANK LTD · 50637967294429
- **Statement:** `50637967294429 statement.pdf`
- **Full File Path:** `statements/50637967294429 statement.pdf`

### Clean Control — UCO BANK · 8061995370719974
- **Statement:** `8061995370719974-01-12-2024to09-05-2026.csv`
- **Full File Path:** `statements/8061995370719974-01-12-2024to09-05-2026.csv`

### Clean Control — BANK OF BARODA · 0678492539681463
- **Statement:** `0678492539681463-02-12-2024to09-05-2026.csv`
- **Full File Path:** `statements/0678492539681463-02-12-2024to09-05-2026.csv`

## Expected Findings

### Pattern 18 — Dormant Reactivation

**Severity:** HIGH  
**Pattern ID:** 18  
**Amount Range:** ₹2,430.39 – ₹308,000.38  
**Reason:** Long dormancy followed by a material reactivation burst.  

**Accounts Involved:**

- **Subject** — BANK OF BARODA, Account `1351667800484732` (`1351667800484732-26-12-2024to19-10-2025.xlsx`)

## Supporting Transactions

Open the listed statement file and locate these transactions to verify this finding:

| Date | Type | Amount (₹) | Narration | Reference / UTR |
|------|------|------------|-----------|-----------------|
| 26-12-2024 | Credit | 2,430.39 | INTEREST CREDIT | `935736232497` |
| 27-09-2025 | Credit | 308,000.38 | NEFT/N07969471466/Pooja Kapoor | `507586823202` |
| 28-09-2025 | Debit | 73,000.97 | IMPS-164946057382-Manoj Kapoor | `331273106093` |

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
