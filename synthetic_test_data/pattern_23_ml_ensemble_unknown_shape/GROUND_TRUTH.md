# Pattern 23 — Ml_ensemble_unknown_shape

## Objective

Safety-net trigger using ensemble ML signals (isolation forest, auto-encoder) to surface statistical anomalies that match no named rule pattern.

## Dataset Files

| Role | Statement File | Bank | Account Number |
|------|---------------|------|----------------|
| Subject | `statement-98880270931.csv` | STATE BANK OF INDIA | 98880270931 |
| Subject | `18712602514989 statement.xlsx` | HDFC BANK LTD | 18712602514989 |
| Subject | `9299158039552286_statement.pdf` | PUNJAB NATIONAL BANK | 9299158039552286 |

## Accounts Involved

### Subject — STATE BANK OF INDIA · 98880270931
- **Statement:** `statement-98880270931.csv`
- **Full File Path:** `statements/statement-98880270931.csv`

### Subject — HDFC BANK LTD · 18712602514989
- **Statement:** `18712602514989 statement.xlsx`
- **Full File Path:** `statements/18712602514989 statement.xlsx`

### Subject — PUNJAB NATIONAL BANK · 9299158039552286
- **Statement:** `9299158039552286_statement.pdf`
- **Full File Path:** `statements/9299158039552286_statement.pdf`

## Expected Findings

### Pattern 23 — Ml Ensemble Unknown Shape

**Severity:** LOW (Safety Net — no named rule match)  
**Pattern ID:** 23  
**Amount Range:** ₹942.25 – ₹9,013.97  
**Reason:** Expected zero strong/weak findings from Patterns 1-19; surface only via Pattern 22/23 safety-net trigger.  

**Accounts Involved:**

- **Subject** — STATE BANK OF INDIA, Account `98880270931` (`statement-98880270931.csv`)
- **Subject** — HDFC BANK LTD, Account `18712602514989` (`18712602514989 statement.xlsx`)
- **Subject** — PUNJAB NATIONAL BANK, Account `9299158039552286` (`9299158039552286_statement.pdf`)

## Supporting Transactions

Open the listed statement file and locate these transactions to verify this finding:

| Date | Type | Amount (₹) | Narration | Reference / UTR |
|------|------|------------|-----------|-----------------|
| 27-04-2025 | Credit | 7,032.97 | UPI/CR/893174238041/Sonia/FDRL/soniapand22@ptaxis/UPI | `095356471710` |
| 14-05-2025 | Debit | 2,972.20 | UPI/DR/183500172691/Priya/UCBA/priyadesa75@okicici/UPI | `467783665412` |
| 23-05-2025 | Debit | 1,726.37 | UPI/DR/544232630096/Vikas/BDBL/vikas.tiwari@okicici/UPI | `829396751660` |
| 23-06-2025 | Credit | 5,226.21 | UPI/CR/025087348500/Mina/BARB/6603416355@upi/UPI | `027985568271` |
| 10-07-2025 | Debit | 9,006.81 | UPI/DR/488282508597/Rajesh/BDBL/rajeshbaja95@ybl/UPI | `592918855051` |
| 11-07-2025 | Debit | 5,653.14 | UPI/DR/114563835726/Preeti/BKID/preeti.desai@ptyes/UPI | `535495782609` |
| 13-07-2025 | Credit | 8,894.02 | UPI/CR/926026719152/Rajan/BKID/rajan322@paytm/UPI | `227909641350` |
| 15-07-2025 | Debit | 3,133.60 | UPI/DR/987594333067/Pooja/BARB/poojakulk13@aubank/UPI | `829399452932` |
| 08-05-2025 | Credit | 942.25 | UPI-Himanshu Ghosh-himanshu.ghosh@aubank-054848750988-CR VIA UPI | `720215870447` |
| 20-06-2025 | Debit | 4,834.87 | UPI-Pankaj Pillai-pankaj356@paytm-853913518653-DR VIA UPI | `835657896876` |
| 21-06-2025 | Debit | 9,013.97 | UPI-Asha Chaudhary-ashachau83@ptsbi-857174331627-DR VIA UPI | `448769094422` |
| 30-06-2025 | Credit | 6,822.12 | UPI-Vikas Joshi-vikas360@ptaxis-150282972768-CR VIA UPI | `200141500006` |
| 02-07-2025 | Debit | 3,329.37 | UPI-Lalit Joshi-9638706511@ybl-944880061941-DR VIA UPI | `454090552446` |
| 04-07-2025 | Debit | 5,499.94 | UPI-Himanshu Jain-himanshu268@oksbi-080802161907-DR VIA UPI | `154951201839` |
| 13-07-2025 | Credit | 1,600.36 | UPI-Anita Mukherjee-anitamukh54@okhdfcbank-400396951398-CR VIA UPI | `853413927757` |
| 15-07-2025 | Debit | 8,894.98 | UPI-Kiran Sethi-kiranseth62@pthdfc-292592093599-DR VIA UPI | `083911471338` |
| 27-08-2025 | Debit | 1,019.52 | UPI-Geeta Das-4616074084@paytm-802064097225-DR VIA UPI | `636231380374` |
| — | — | 942.25–9,013.97 | _(see statement)_ | `342676794978` |
| — | — | 942.25–9,013.97 | _(see statement)_ | `382693350315` |
| — | — | 942.25–9,013.97 | _(see statement)_ | `915319403689` |
| — | — | 942.25–9,013.97 | _(see statement)_ | `824523727727` |
| — | — | 942.25–9,013.97 | _(see statement)_ | `150516479835` |
| — | — | 942.25–9,013.97 | _(see statement)_ | `320904258373` |
| — | — | 942.25–9,013.97 | _(see statement)_ | `679915878301` |
| — | — | 942.25–9,013.97 | _(see statement)_ | `197206177939` |
| — | — | 942.25–9,013.97 | _(see statement)_ | `996917408409` |

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
