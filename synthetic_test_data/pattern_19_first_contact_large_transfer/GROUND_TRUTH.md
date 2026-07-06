# Pattern 19 — First_contact_large_transfer

## Objective

Detects a large-value transfer (RTGS/IMPS/NEFT) where the two parties have no prior transaction history, indicating a first-ever contact that is immediately high value.

## Dataset Files

| Role | Statement File | Bank | Account Number |
|------|---------------|------|----------------|
| Originator | `3646678344002840-02-12-2024to09-05-2026.csv` | UCO BANK | 3646678344002840 |
| Counterparty | `7937753974154053_statement.txt` | PUNJAB NATIONAL BANK | 7937753974154053 |
| Clean Control | `1573834194604305-01-12-2024to09-05-2026.pdf` | BANK OF BARODA | 1573834194604305 |
| Clean Control | `2265730243390069_statement.txt` | PUNJAB NATIONAL BANK | 2265730243390069 |
| Clean Control | `0012685434741507-02-12-2024to09-05-2026.xlsx` | BANK OF BARODA | 0012685434741507 |
| Clean Control | `589052956261933_statement.xlsx` | AXIS BANK LIMITED | 589052956261933 |

## Accounts Involved

### Originator — UCO BANK · 3646678344002840
- **Statement:** `3646678344002840-02-12-2024to09-05-2026.csv`
- **Full File Path:** `statements/3646678344002840-02-12-2024to09-05-2026.csv`

### Counterparty — PUNJAB NATIONAL BANK · 7937753974154053
- **Statement:** `7937753974154053_statement.txt`
- **Full File Path:** `statements/7937753974154053_statement.txt`

### Clean Control — BANK OF BARODA · 1573834194604305
- **Statement:** `1573834194604305-01-12-2024to09-05-2026.pdf`
- **Full File Path:** `statements/1573834194604305-01-12-2024to09-05-2026.pdf`

### Clean Control — PUNJAB NATIONAL BANK · 2265730243390069
- **Statement:** `2265730243390069_statement.txt`
- **Full File Path:** `statements/2265730243390069_statement.txt`

### Clean Control — BANK OF BARODA · 0012685434741507
- **Statement:** `0012685434741507-02-12-2024to09-05-2026.xlsx`
- **Full File Path:** `statements/0012685434741507-02-12-2024to09-05-2026.xlsx`

### Clean Control — AXIS BANK LIMITED · 589052956261933
- **Statement:** `589052956261933_statement.xlsx`
- **Full File Path:** `statements/589052956261933_statement.xlsx`

## Expected Findings

### Pattern 19 — First Contact Large Transfer

**Severity:** HIGH  
**Pattern ID:** 19  
**Amount:** ₹352,000.22  
**Reason:** No prior relationship; first-ever contact is a large RTGS transfer.  

**Accounts Involved:**

- **Originator** — UCO BANK, Account `3646678344002840` (`3646678344002840-02-12-2024to09-05-2026.csv`)
- **Counterparty** — PUNJAB NATIONAL BANK, Account `7937753974154053` (`7937753974154053_statement.txt`)

## Supporting Transactions

Open the listed statement file and locate these transactions to verify this finding:

| Date | Type | Amount (₹) | Narration | Reference / UTR |
|------|------|------------|-----------|-----------------|
| 16-06-2025 | Credit/Debit | RTGS/R09200230076/KIRAN KULKARNI/PUNB0497941 | RTGS/R09200230076/KIRAN KULKARNI/PUNB0497941 | `R09200230076` |

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
