# Pattern 08 — Money_trail

## Objective

Detects a corroborated multi-hop fund movement where the same UTR/reference number appears as a debit in the sender's statement and a credit in the receiver's statement.

## Dataset Files

| Role | Statement File | Bank | Account Number |
|------|---------------|------|----------------|
| Originator | `6551703125468816-01-12-2024to09-05-2026.pdf` | BANK OF INDIA | 6551703125468816 |
| Recipient | `078469715959585_statement.pdf` | AXIS BANK LIMITED | 078469715959585 |
| Clean Control | `2440602554009646_statement.xlsx` | PUNJAB NATIONAL BANK | 2440602554009646 |
| Clean Control | `00057753678707 statement.csv` | HDFC BANK LTD | 00057753678707 |
| Clean Control | `052367692850118_statement.pdf` | AXIS BANK LIMITED | 052367692850118 |
| Clean Control | `34131720302851_SOA.xlsx` | BANDHAN BANK LIMITED | 34131720302851 |
| Clean Control | `statement-90520229751.csv` | STATE BANK OF INDIA | 90520229751 |

## Accounts Involved

### Originator — BANK OF INDIA · 6551703125468816
- **Statement:** `6551703125468816-01-12-2024to09-05-2026.pdf`
- **Full File Path:** `statements/6551703125468816-01-12-2024to09-05-2026.pdf`

### Recipient — AXIS BANK LIMITED · 078469715959585
- **Statement:** `078469715959585_statement.pdf`
- **Full File Path:** `statements/078469715959585_statement.pdf`

### Clean Control — PUNJAB NATIONAL BANK · 2440602554009646
- **Statement:** `2440602554009646_statement.xlsx`
- **Full File Path:** `statements/2440602554009646_statement.xlsx`

### Clean Control — HDFC BANK LTD · 00057753678707
- **Statement:** `00057753678707 statement.csv`
- **Full File Path:** `statements/00057753678707 statement.csv`

### Clean Control — AXIS BANK LIMITED · 052367692850118
- **Statement:** `052367692850118_statement.pdf`
- **Full File Path:** `statements/052367692850118_statement.pdf`

### Clean Control — BANDHAN BANK LIMITED · 34131720302851
- **Statement:** `34131720302851_SOA.xlsx`
- **Full File Path:** `statements/34131720302851_SOA.xlsx`

### Clean Control — STATE BANK OF INDIA · 90520229751
- **Statement:** `statement-90520229751.csv`
- **Full File Path:** `statements/statement-90520229751.csv`

## Expected Findings

### Pattern 8 — Money Trail

**Severity:** HIGH  
**Pattern ID:** 8  
**Amount:** ₹152,856.12  
**Reason:** Multi-hop trail; real entries on both sides of every transfer.  

**Accounts Involved:**

- **Originator** — BANK OF INDIA, Account `6551703125468816` (`6551703125468816-01-12-2024to09-05-2026.pdf`)
- **Recipient** — AXIS BANK LIMITED, Account `078469715959585` (`078469715959585_statement.pdf`)

## Supporting Transactions

Open the listed statement file and locate these transactions to verify this finding:

| Date | Type | Amount (₹) | Narration | Reference / UTR |
|------|------|------------|-----------|-----------------|
| 16-05-2025 | Credit | 152,856.12 | 16-05-2025 NEFT/N29095242018/RENU KUMAR | `N29095242018` |

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
