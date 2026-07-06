# Pattern 14 — Reversal_clusters

## Objective

Detects clusters of UPI debit transactions each followed by a matching reversal credit, repeating across multiple cycles, suggesting systematic reversal exploitation.

## Dataset Files

| Role | Statement File | Bank | Account Number |
|------|---------------|------|----------------|
| Subject | `85762776050010-01-12-2024to09-05-2026.csv` | THE FEDERAL BANK LIMITED | 85762776050010 |
| Clean Control | `596700606676173_statement.xlsx` | AXIS BANK LIMITED | 596700606676173 |
| Clean Control | `2796444213_statement.csv` | KOTAK MAHINDRA BANK LTD | 2796444213 |
| Clean Control | `4118260700258613-01-12-2024to09-05-2026.csv` | BANK OF INDIA | 4118260700258613 |
| Clean Control | `768835027156720_statement.pdf` | AXIS BANK LIMITED | 768835027156720 |

## Accounts Involved

### Subject — THE FEDERAL BANK LIMITED · 85762776050010
- **Statement:** `85762776050010-01-12-2024to09-05-2026.csv`
- **Full File Path:** `statements/85762776050010-01-12-2024to09-05-2026.csv`

### Clean Control — AXIS BANK LIMITED · 596700606676173
- **Statement:** `596700606676173_statement.xlsx`
- **Full File Path:** `statements/596700606676173_statement.xlsx`

### Clean Control — KOTAK MAHINDRA BANK LTD · 2796444213
- **Statement:** `2796444213_statement.csv`
- **Full File Path:** `statements/2796444213_statement.csv`

### Clean Control — BANK OF INDIA · 4118260700258613
- **Statement:** `4118260700258613-01-12-2024to09-05-2026.csv`
- **Full File Path:** `statements/4118260700258613-01-12-2024to09-05-2026.csv`

### Clean Control — AXIS BANK LIMITED · 768835027156720
- **Statement:** `768835027156720_statement.pdf`
- **Full File Path:** `statements/768835027156720_statement.pdf`

## Expected Findings

### Pattern 14 — Reversal Clusters

**Severity:** HIGH  
**Pattern ID:** 14  
**Amount Range:** ₹13,700.54 – ₹35,200.01  
**Reason:** Repeated debit-reversal pattern across multiple cycles.  

**Accounts Involved:**

- **Subject** — THE FEDERAL BANK LIMITED, Account `85762776050010` (`85762776050010-01-12-2024to09-05-2026.csv`)

## Supporting Transactions

Open the listed statement file and locate these transactions to verify this finding:

| Date | Type | Amount (₹) | Narration | Reference / UTR |
|------|------|------------|-----------|-----------------|
| 09-08-2025 | Credit/Debit | UPI/DR/375287537003/Yogesh/UCO/yogesh@paytm/UPI | UPI/DR/375287537003/Yogesh/UCO/yogesh@paytm/UPI | `U67873427788` |
| 10-08-2025 | Credit | RETURN/U67873427788/REVERSAL | RETURN/U67873427788/REVERSAL | `397250365985` |
| 12-08-2025 | Credit/Debit | UPI/DR/095099319270/Kunal/AXIS/kunal@paytm/UPI | UPI/DR/095099319270/Kunal/AXIS/kunal@paytm/UPI | `U56098340848` |
| 13-08-2025 | Credit | RETURN/U56098340848/REVERSAL | RETURN/U56098340848/REVERSAL | `199082295477` |
| 15-08-2025 | Credit/Debit | UPI/DR/591788217407/Priya/KOTAK/priya@paytm/UPI | UPI/DR/591788217407/Priya/KOTAK/priya@paytm/UPI | `U60604345626` |
| 16-08-2025 | Credit | RETURN/U60604345626/REVERSAL | RETURN/U60604345626/REVERSAL | `115607022123` |
| 18-08-2025 | Credit/Debit | UPI/DR/359537078933/Saurabh/PNB/saurabh@paytm/UPI | UPI/DR/359537078933/Saurabh/PNB/saurabh@paytm/UPI | `U25766913165` |
| 19-08-2025 | Credit | RETURN/U25766913165/REVERSAL | RETURN/U25766913165/REVERSAL | `299827599520` |

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
