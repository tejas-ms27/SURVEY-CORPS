# Expected Findings — Smurfing + Structured Cash Placement via Multiple Channels

## Pattern 5 — Structuring Smurfing

**Pattern Name:** structuring_smurfing  
**Pattern ID:** 5  
**Expected Confidence:** High  
**Why It Should Trigger:**  
Detects a pattern of cash deposits each staying just below the ₹50,000 reporting threshold. Consistent with deliberate structuring to evade currency transaction reporting obligations.  

**Accounts Involved:**
- `750850479834326_statement.xlsx` — AXIS BANK LIMITED 750850479834326 (Placement Account (Structuring))
- `85315254644320 statement.pdf` — HDFC BANK LTD 85315254644320 (Layering Account (Round Values))
- `30654527754078-01-12-2024to08-05-2026.pdf` — THE FEDERAL BANK LIMITED 30654527754078 (Integration / Cash-Out Account)

**Supporting References:**
- Structuring deposits (Axis): `014782139565`, `396821238320`, `125229000046`, `669291167555`, `270281220048`, `735929287799`, `544113730778`, `469609805690`
- Round-value transfers (HDFC): `219871512217`, `899751038969`, `246372423033`, `099577519299`, `984982294808`, `425877947807`, `872406510315`
- Cash-out credit inflow: `563801007073`
- Cash-out ATM withdrawal: `867662226469`

## Pattern 15 — Round Value Debit

**Pattern Name:** round_value_debit  
**Pattern ID:** 15  
**Expected Confidence:** High  
**Why It Should Trigger:**  
Detects clusters of outward transfers in round rupee values (multiples of ₹5,000 or ₹10,000) occurring in the same period as non-round routine spending, inconsistent with normal behaviour.  

**Accounts Involved:**
- `750850479834326_statement.xlsx` — AXIS BANK LIMITED 750850479834326 (Placement Account (Structuring))
- `85315254644320 statement.pdf` — HDFC BANK LTD 85315254644320 (Layering Account (Round Values))
- `30654527754078-01-12-2024to08-05-2026.pdf` — THE FEDERAL BANK LIMITED 30654527754078 (Integration / Cash-Out Account)

**Supporting References:**
- Structuring deposits (Axis): `014782139565`, `396821238320`, `125229000046`, `669291167555`, `270281220048`, `735929287799`, `544113730778`, `469609805690`
- Round-value transfers (HDFC): `219871512217`, `899751038969`, `246372423033`, `099577519299`, `984982294808`, `425877947807`, `872406510315`
- Cash-out credit inflow: `563801007073`
- Cash-out ATM withdrawal: `867662226469`

## Pattern 9 — Credit To Cash Out

**Pattern Name:** credit_to_cash_out  
**Pattern ID:** 9  
**Expected Confidence:** High  
**Why It Should Trigger:**  
Detects a large inward credit (NEFT/IMPS/UPI) followed within a short window by one or more ATM withdrawals of a near-equivalent total amount, suggesting rapid cash-out of proceeds.  

**Accounts Involved:**
- `750850479834326_statement.xlsx` — AXIS BANK LIMITED 750850479834326 (Placement Account (Structuring))
- `85315254644320 statement.pdf` — HDFC BANK LTD 85315254644320 (Layering Account (Round Values))
- `30654527754078-01-12-2024to08-05-2026.pdf` — THE FEDERAL BANK LIMITED 30654527754078 (Integration / Cash-Out Account)

**Supporting References:**
- Structuring deposits (Axis): `014782139565`, `396821238320`, `125229000046`, `669291167555`, `270281220048`, `735929287799`, `544113730778`, `469609805690`
- Round-value transfers (HDFC): `219871512217`, `899751038969`, `246372423033`, `099577519299`, `984982294808`, `425877947807`, `872406510315`
- Cash-out credit inflow: `563801007073`
- Cash-out ATM withdrawal: `867662226469`
