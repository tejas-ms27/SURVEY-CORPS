# Expected Findings — Mule Network — Hub-and-Spoke Aggregation for Organised Cyber Fraud

## Pattern 12 — Hub Ranking

**Pattern Name:** hub_ranking  
**Pattern ID:** 12  
**Expected Confidence:** High  
**Why It Should Trigger:**  
Detects a central hub account that receives funds from an unusually large number of distinct sender accounts within the analysis window, a hallmark of mule network aggregation.  

**Accounts Involved:**
- `2583442857_statement.xlsx` — KOTAK MAHINDRA BANK LTD 2583442857 (Hub (Aggregator))
- `2871288856142199_statement.pdf` — PUNJAB NATIONAL BANK 2871288856142199 (Spoke Account 1)
- `12691319567650-01-12-2024to08-05-2026.xlsx` — THE FEDERAL BANK LIMITED 12691319567650 (Spoke Account 2)
- `5089515621605975-02-12-2024to08-05-2026.xlsx` — UCO BANK 5089515621605975 (Spoke Account 3)
- `59347392058238 statement.csv` — HDFC BANK LTD 59347392058238 (Spoke Account 4)
- `81206073174626-02-12-2024to08-05-2026.xlsx` — THE FEDERAL BANK LIMITED 81206073174626 (Spoke Account 5)
- `statement-99628833989.xlsx` — STATE BANK OF INDIA 99628833989 (Spoke Account 6)
- `5226559152743878_statement.txt` — PUNJAB NATIONAL BANK 5226559152743878 (Spoke Account 7)

**Supporting References:**
- Spoke 1 → Hub: `N39558289002`
- Spoke 2 → Hub: `I43243339199`
- Spoke 3 → Hub: `I71359001100`
- Spoke 4 → Hub: `I75823920825`
- Spoke 5 → Hub: `I18986330736`
- Spoke 6 → Hub: `U72411748544`
- Spoke 7 → Hub: `N65830057946`

## Pattern 4 — Fund Pooling

**Pattern Name:** fund_pooling  
**Pattern ID:** 4  
**Expected Confidence:** High  
**Why It Should Trigger:**  
Detects rapid accumulation of funds from multiple senders within a short window, consistent with a pooling account aggregating proceeds before onward disbursement.  

**Accounts Involved:**
- `2583442857_statement.xlsx` — KOTAK MAHINDRA BANK LTD 2583442857 (Hub (Aggregator))
- `2871288856142199_statement.pdf` — PUNJAB NATIONAL BANK 2871288856142199 (Spoke Account 1)
- `12691319567650-01-12-2024to08-05-2026.xlsx` — THE FEDERAL BANK LIMITED 12691319567650 (Spoke Account 2)
- `5089515621605975-02-12-2024to08-05-2026.xlsx` — UCO BANK 5089515621605975 (Spoke Account 3)
- `59347392058238 statement.csv` — HDFC BANK LTD 59347392058238 (Spoke Account 4)
- `81206073174626-02-12-2024to08-05-2026.xlsx` — THE FEDERAL BANK LIMITED 81206073174626 (Spoke Account 5)
- `statement-99628833989.xlsx` — STATE BANK OF INDIA 99628833989 (Spoke Account 6)
- `5226559152743878_statement.txt` — PUNJAB NATIONAL BANK 5226559152743878 (Spoke Account 7)

**Supporting References:**
- Spoke 1 → Hub: `N39558289002`
- Spoke 2 → Hub: `I43243339199`
- Spoke 3 → Hub: `I71359001100`
- Spoke 4 → Hub: `I75823920825`
- Spoke 5 → Hub: `I18986330736`
- Spoke 6 → Hub: `U72411748544`
- Spoke 7 → Hub: `N65830057946`
