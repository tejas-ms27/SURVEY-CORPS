# Clean Control — Negative Baseline

## Objective

Negative control dataset. No fraud patterns are deliberately planted. All findings from pattern detectors should be absent or limited to weak-tier noise.

## Dataset Files

| Role | Statement File | Bank | Account Number |
|------|---------------|------|----------------|
| Clean Control | `3012346509702773-02-12-2024to09-05-2026.pdf` | BANK OF INDIA | 3012346509702773 |
| Clean Control | `statement-36071249552.txt` | STATE BANK OF INDIA | 36071249552 |
| Clean Control | `9905651287101229_statement.pdf` | PUNJAB NATIONAL BANK | 9905651287101229 |
| Clean Control | `statement-26619050843.txt` | STATE BANK OF INDIA | 26619050843 |
| Clean Control | `0421212803246387_statement.txt` | PUNJAB NATIONAL BANK | 0421212803246387 |
| Clean Control | `97948931224243-01-12-2024to09-05-2026.csv` | THE FEDERAL BANK LIMITED | 97948931224243 |

## Accounts Involved

### Clean Control — BANK OF INDIA · 3012346509702773
- **Statement:** `3012346509702773-02-12-2024to09-05-2026.pdf`
- **Full File Path:** `statements/3012346509702773-02-12-2024to09-05-2026.pdf`

### Clean Control — STATE BANK OF INDIA · 36071249552
- **Statement:** `statement-36071249552.txt`
- **Full File Path:** `statements/statement-36071249552.txt`

### Clean Control — PUNJAB NATIONAL BANK · 9905651287101229
- **Statement:** `9905651287101229_statement.pdf`
- **Full File Path:** `statements/9905651287101229_statement.pdf`

### Clean Control — STATE BANK OF INDIA · 26619050843
- **Statement:** `statement-26619050843.txt`
- **Full File Path:** `statements/statement-26619050843.txt`

### Clean Control — PUNJAB NATIONAL BANK · 0421212803246387
- **Statement:** `0421212803246387_statement.txt`
- **Full File Path:** `statements/0421212803246387_statement.txt`

### Clean Control — THE FEDERAL BANK LIMITED · 97948931224243
- **Statement:** `97948931224243-01-12-2024to09-05-2026.csv`
- **Full File Path:** `statements/97948931224243-01-12-2024to09-05-2026.csv`

## Expected Findings

_No findings expected. This folder is a negative control._

## Expected Non-Findings

The following pattern detectors must NOT trigger on this dataset:

| Pattern ID | Pattern Name | Reason |
|-----------|--------------|--------|
| 1 | duplicate verification | No deliberately planted strong-tier behaviour. |
| 2 | failed reversed transaction | No deliberately planted strong-tier behaviour. |
| 3 | pass through routing | No deliberately planted strong-tier behaviour. |
| 4 | fund pooling | No deliberately planted strong-tier behaviour. |
| 5 | structuring smurfing | No deliberately planted strong-tier behaviour. |
| 7 | circular flow | No deliberately planted strong-tier behaviour. |
| 8 | money trail | No deliberately planted strong-tier behaviour. |
| 9 | credit to cash out | No deliberately planted strong-tier behaviour. |
| 10 | cross statement links | No deliberately planted strong-tier behaviour. |
| 11 | balance parking | No deliberately planted strong-tier behaviour. |
| 12 | hub ranking | No deliberately planted strong-tier behaviour. |
| 13 | low value testing | No deliberately planted strong-tier behaviour. |
| 14 | reversal clusters | No deliberately planted strong-tier behaviour. |
| 15 | round value debit | No deliberately planted strong-tier behaviour. |
| 16 | shared upi | No deliberately planted strong-tier behaviour. |
| 17 | round trip | No deliberately planted strong-tier behaviour. |
| 18 | dormant reactivation | No deliberately planted strong-tier behaviour. |
| 19 | first contact large transfer | No deliberately planted strong-tier behaviour. |

## Tier Expectations

- **Strong Findings:** 0
- **Weak Findings Allowed:** True
- **Ranking Expectation:** clean accounts must remain outside the suspicious top ranks

## Validation Notes

To manually verify this ground truth:

1. Open each statement file listed in **Dataset Files** above.
2. Search for each **Reference / UTR** value in the reference/narration columns.
3. Confirm the transaction date, amount, and type match the values above.
4. Confirm no other pattern detector fires on accounts listed as clean controls.
5. Dataset seed: `2025` — re-running the generator with this seed reproduces identical files.
