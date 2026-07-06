# Pattern 03 — Pass_through_routing

## Objective

Detects accounts that receive credits from multiple unrelated sources and rapidly forward the funds onward, retaining little residual balance. Characteristic of money mule or pass-through accounts.

## Dataset Files

| Role | Statement File | Bank | Account Number |
|------|---------------|------|----------------|
| Subject | `0144130624165626-01-12-2024to09-05-2026.csv` | UCO BANK | 0144130624165626 |
| Clean Control | `2423783239149708_statement.txt` | PUNJAB NATIONAL BANK | 2423783239149708 |
| Clean Control | `0288854422372621-01-12-2024to09-05-2026.xlsx` | BANK OF BARODA | 0288854422372621 |
| Clean Control | `97042978075723-01-12-2024to09-05-2026.pdf` | THE FEDERAL BANK LIMITED | 97042978075723 |
| Clean Control | `statement-67042020919.txt` | STATE BANK OF INDIA | 67042020919 |

## Accounts Involved

### Subject — UCO BANK · 0144130624165626
- **Statement:** `0144130624165626-01-12-2024to09-05-2026.csv`
- **Full File Path:** `statements/0144130624165626-01-12-2024to09-05-2026.csv`

### Clean Control — PUNJAB NATIONAL BANK · 2423783239149708
- **Statement:** `2423783239149708_statement.txt`
- **Full File Path:** `statements/2423783239149708_statement.txt`

### Clean Control — BANK OF BARODA · 0288854422372621
- **Statement:** `0288854422372621-01-12-2024to09-05-2026.xlsx`
- **Full File Path:** `statements/0288854422372621-01-12-2024to09-05-2026.xlsx`

### Clean Control — THE FEDERAL BANK LIMITED · 97042978075723
- **Statement:** `97042978075723-01-12-2024to09-05-2026.pdf`
- **Full File Path:** `statements/97042978075723-01-12-2024to09-05-2026.pdf`

### Clean Control — STATE BANK OF INDIA · 67042020919
- **Statement:** `statement-67042020919.txt`
- **Full File Path:** `statements/statement-67042020919.txt`

## Expected Findings

### Pattern 3 — Pass Through Routing

**Severity:** HIGH  
**Pattern ID:** 3  
**Amount Range:** ₹59,700.25 – ₹352,640.61  
**Reason:** Multiple unrelated inbound credits followed by rapid onward routing.  

**Accounts Involved:**

- **Subject** — UCO BANK, Account `0144130624165626` (`0144130624165626-01-12-2024to09-05-2026.csv`)

## Supporting Transactions

Open the listed statement file and locate these transactions to verify this finding:

| Date | Type | Amount (₹) | Narration | Reference / UTR |
|------|------|------------|-----------|-----------------|
| 25-06-2025 | Credit | NEFT/N51034045282/Mukesh Menon | NEFT/N51034045282/Mukesh Menon | `992541703789` |
| 25-06-2025 | Credit | UPI/CR/079445787975/Dinesh/BOB/8988021736@upi/UPI | UPI/CR/079445787975/Dinesh/BOB/8988021736@upi/UPI | `007662067498` |
| 25-06-2025 | Credit | UPI/CR/850933906868/Sangita/AXIS/7566349509@aubank/UPI | UPI/CR/850933906868/Sangita/AXIS/7566349509@aubank/UPI | `697146058195` |
| 25-06-2025 | Credit | NEFT/N09846936794/Ravi Verma | NEFT/N09846936794/Ravi Verma | `100535260194` |
| 25-06-2025 | Credit | NEFT/N18931870942/Mamta Roy | NEFT/N18931870942/Mamta Roy | `886248354463` |
| 27-06-2025 | Credit/Debit | RTGS/R07431638724/Mukesh Mehta/FDRL0262357 | RTGS/R07431638724/Mukesh Mehta/FDRL0262357 | `020524633375` |

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
