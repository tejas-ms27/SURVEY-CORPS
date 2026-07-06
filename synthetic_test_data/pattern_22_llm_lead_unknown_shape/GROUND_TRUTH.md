# Pattern 22 — Llm_lead_unknown_shape

## Objective

Safety-net trigger for anomalous spending patterns that evade rule-based detectors. LLM analysis surfaces these via semantic understanding of narration sequences.

## Dataset Files

| Role | Statement File | Bank | Account Number |
|------|---------------|------|----------------|
| Subject | `9194437102_statement.xlsx` | KOTAK MAHINDRA BANK LTD | 9194437102 |
| Subject | `38299997813349_SOA.pdf` | BANDHAN BANK LIMITED | 38299997813349 |

## Accounts Involved

### Subject — KOTAK MAHINDRA BANK LTD · 9194437102
- **Statement:** `9194437102_statement.xlsx`
- **Full File Path:** `statements/9194437102_statement.xlsx`

### Subject — BANDHAN BANK LIMITED · 38299997813349
- **Statement:** `38299997813349_SOA.pdf`
- **Full File Path:** `statements/38299997813349_SOA.pdf`

## Expected Findings

### Pattern 22 — Llm Lead Unknown Shape

**Severity:** LOW (Safety Net — no named rule match)  
**Pattern ID:** 22  
**Amount Range:** ₹970.39 – ₹8,411.93  
**Reason:** Expected zero strong/weak findings from Patterns 1-19; surface only via Pattern 22/23 safety-net trigger.  

**Accounts Involved:**

- **Subject** — KOTAK MAHINDRA BANK LTD, Account `9194437102` (`9194437102_statement.xlsx`)
- **Subject** — BANDHAN BANK LIMITED, Account `38299997813349` (`38299997813349_SOA.pdf`)

## Supporting Transactions

Open the listed statement file and locate these transactions to verify this finding:

| Date | Type | Amount (₹) | Narration | Reference / UTR |
|------|------|------------|-----------|-----------------|
| 18-07-2025 | Credit | 1,754.05 | UPI/CR/304413445110/Vikram/PUNB/vikram647@okhdfcbank/UPI | `040066189490` |
| 19-07-2025 | Debit | 7,515.08 | UPI/DR/392132969815/Arun/HDFC/arun588@okhdfcbank/UPI | `820852434285` |
| 31-08-2025 | Debit | 5,261.62 | UPI/DR/429588518580/Sarita/KKBK/8734452045@pthdfc/UPI | `188268667979` |
| 09-09-2025 | Credit | 2,139.37 | UPI/CR/809311869652/Babita/KKBK/babita711@ptsbi/UPI | `650812741187` |
| 10-10-2025 | Debit | 6,787.60 | UPI/DR/590410884565/Pankaj/PUNB/pankaj520@ybl/UPI | `063261520403` |
| 10-11-2025 | Debit | 7,914.36 | UPI/DR/001965032578/Saurabh/PUNB/saurabh.mishra@ptaxis/UPI | `311691215207` |
| 23-12-2025 | Credit | 3,042.30 | UPI/CR/642885489033/Ankit/UCBA/ankit350@kotak/UPI | `915713412730` |
| — | — | 970.39–8,411.93 | _(see statement)_ | `238959090807` |
| — | — | 970.39–8,411.93 | _(see statement)_ | `845686800976` |
| — | — | 970.39–8,411.93 | _(see statement)_ | `664530268103` |
| — | — | 970.39–8,411.93 | _(see statement)_ | `374058271024` |
| — | — | 970.39–8,411.93 | _(see statement)_ | `460094039221` |
| — | — | 970.39–8,411.93 | _(see statement)_ | `505401960263` |
| — | — | 970.39–8,411.93 | _(see statement)_ | `488404679946` |

## Expected Non-Findings

The following pattern detectors must NOT trigger on this dataset:

| Pattern ID | Pattern Name | Reason |
|-----------|--------------|--------|
| 1 | duplicate verification | Unknown-shape fixture avoids written rule thresholds. |
| 2 | failed reversed transaction | Unknown-shape fixture avoids written rule thresholds. |
| 3 | pass through routing | Unknown-shape fixture avoids written rule thresholds. |
| 4 | fund pooling | Unknown-shape fixture avoids written rule thresholds. |
| 5 | structuring smurfing | Unknown-shape fixture avoids written rule thresholds. |
| 7 | circular flow | Unknown-shape fixture avoids written rule thresholds. |
| 8 | money trail | Unknown-shape fixture avoids written rule thresholds. |
| 9 | credit to cash out | Unknown-shape fixture avoids written rule thresholds. |
| 10 | cross statement links | Unknown-shape fixture avoids written rule thresholds. |
| 11 | balance parking | Unknown-shape fixture avoids written rule thresholds. |
| 12 | hub ranking | Unknown-shape fixture avoids written rule thresholds. |
| 13 | low value testing | Unknown-shape fixture avoids written rule thresholds. |
| 14 | reversal clusters | Unknown-shape fixture avoids written rule thresholds. |
| 15 | round value debit | Unknown-shape fixture avoids written rule thresholds. |
| 16 | shared upi | Unknown-shape fixture avoids written rule thresholds. |
| 17 | round trip | Unknown-shape fixture avoids written rule thresholds. |
| 18 | dormant reactivation | Unknown-shape fixture avoids written rule thresholds. |
| 19 | first contact large transfer | Unknown-shape fixture avoids written rule thresholds. |

## Safety Net Expectation

Expected zero strong/weak findings from Patterns 1-19; surface only via Pattern 22/23 safety-net trigger.

## Validation Notes

To manually verify this ground truth:

1. Open each statement file listed in **Dataset Files** above.
2. Search for each **Reference / UTR** value in the reference/narration columns.
3. Confirm the transaction date, amount, and type match the values above.
4. Confirm no other pattern detector fires on accounts listed as clean controls.
5. Dataset seed: `2025` — re-running the generator with this seed reproduces identical files.
