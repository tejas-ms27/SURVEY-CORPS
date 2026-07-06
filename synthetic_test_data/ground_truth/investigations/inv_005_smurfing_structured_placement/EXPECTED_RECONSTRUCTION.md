# Expected Case Reconstruction — Smurfing + Structured Cash Placement via Multiple Channels

## Stage 1 — Placement (Structuring / Smurfing)

**Account:** Axis Bank 750850479834326
**Statement:** `750850479834326_statement.xlsx`

Eight separate cash deposits, each below ₹50,000, are deposited into the
Axis Bank account over the fraud window. The structuring is evident from
the tight amount band (₹44,900–₹49,900) and the cadence of deposits.

| # | Reference | Amount Range |
|---|-----------|-------------|
| 1 | 014782139565 | ₹44,900–₹49,900 |
| 2 | 396821238320 | ₹44,900–₹49,900 |
| 3 | 125229000046 | ₹44,900–₹49,900 |
| 4 | 669291167555 | ₹44,900–₹49,900 |
| 5 | 270281220048 | ₹44,900–₹49,900 |
| 6 | 735929287799 | ₹44,900–₹49,900 |
| 7 | 544113730778 | ₹44,900–₹49,900 |
| 8 | 469609805690 | ₹44,900–₹49,900 |

**To verify:** Open `750850479834326_statement.xlsx`, search for each ref above,
confirm each is a credit entry with amount in the ₹44,900–₹49,900 band.

## Stage 2 — Layering (Round-Value Debits)

**Account:** HDFC Bank 85315254644320
**Statement:** `85315254644320 statement.pdf`

Seven outward transfers in conspicuously round rupee amounts
(₹25,000–₹85,000) occur in the same period, interspersed with
normal non-round retail spending (groceries, utilities, UPI).

| # | Reference | Amount Range |
|---|-----------|-------------|
| 1 | 219871512217 | ₹25,000–₹85,000 |
| 2 | 899751038969 | ₹25,000–₹85,000 |
| 3 | 246372423033 | ₹25,000–₹85,000 |
| 4 | 099577519299 | ₹25,000–₹85,000 |
| 5 | 984982294808 | ₹25,000–₹85,000 |
| 6 | 425877947807 | ₹25,000–₹85,000 |
| 7 | 872406510315 | ₹25,000–₹85,000 |

## Stage 3 — Integration / Cash Out

**Account:** Federal Bank 30654527754078
**Statement:** `30654527754078-01-12-2024to08-05-2026.pdf`

A large inward credit (ref `563801007073`, ₹1,45,000–₹1,86,000) is
followed within hours to days by ATM withdrawals (ref `867662226469`)
consuming the equivalent amount. No legitimate retail expenditure
pattern follows the credit — the funds are extracted as cash directly.

## Reconstruction Summary

| Stage | Account | Bank | Activity | References |
|-------|---------|------|----------|-----------|
| Placement | 750850479834326 | Axis Bank | 8 × sub-₹50K cash deposits | 014782139565 … 469609805690 |
| Layering | 85315254644320 | HDFC | 7 × round-value outward transfers | 219871512217 … 872406510315 |
| Integration | 30654527754078 | Federal Bank | Large credit → immediate ATM cash | 563801007073 → 867662226469 |

---

## Key Reference Numbers for Manual Verification

- **Structuring deposits (Axis):** `014782139565`, `396821238320`, `125229000046`, `669291167555`, `270281220048`, `735929287799`, `544113730778`, `469609805690`
- **Round-value transfers (HDFC):** `219871512217`, `899751038969`, `246372423033`, `099577519299`, `984982294808`, `425877947807`, `872406510315`
- **Cash-out credit inflow:** `563801007073`
- **Cash-out ATM withdrawal:** `867662226469`
