# Expected Case Reconstruction — UPI Investment Scam — Victim Defrauded via Fake Mutual Fund Scheme

## Step-by-Step Money Movement

### Step 1 — Victim Transfer (First Contact Large Transfer)
- **Date:** Located in `1974187568_statement.csv` under reference `R95720579226`
- **Action:** Victim (Kotak account 1974187568) sends ₹6,42,000 via RTGS to
  HDFC account 83871366032735.
- **Signal:** This is the first-ever transaction between these two parties —
  no prior history exists in either statement.
- **Receiving statement:** The same ref `R95720579226` appears as a credit in
  `83871366032735 statement.pdf` (HDFC Bank).

### Step 2 — First Receiver Routes Funds (Pass-Through)
- **Date:** Within 24–48 hours of receipt
- **Action:** HDFC account 83871366032735 forwards funds onward via UPI/IMPS.
- **Receiving account:** Bandhan Bank account 73056887297587 (`73056887297587_SOA.xlsx`)
- **Signal:** The Bandhan account shows multiple unrelated inbound credits
  (refs: 051698095623, 508863857173, 445482069527, 810040308391, 745952975950)
  followed by rapid onward routing — a classic pass-through pattern.

### Step 3 — Funds Pooled (Fund Pooling)
- **Date:** Within 2–5 days of initial transfer
- **Action:** Kotak account 1185080153 receives funds from multiple sources
  (including the Bandhan routing account) in a short window.
- **Supporting refs in `1185080153_statement.csv`:**
  389922137580, 384915118541, 200216494773, 162947856305, 915009796170
- **Signal:** Multiple unrelated senders, tight time window, no outward
  retail spend — consistent with a pooling mule.

### Step 4 — Cash Withdrawal (Credit to Cash Out)
- **Date:** Within 1–3 days of pooling
- **Action:** Federal Bank account 30654527754078 receives a large inward
  credit (ref 563801007073) and within hours makes ATM withdrawals (ref 867662226469)
  equivalent to the credited amount.
- **Statement:** `30654527754078-01-12-2024to08-05-2026.pdf`
- **Signal:** Rapid credit-to-ATM pattern eliminates any legitimate commercial purpose.

## Reconstruction Summary

| Step | From | To | Amount (Approx) | Method | Reference |
|------|------|----|-----------------|--------|-----------|
| 1 | Victim (Kotak 1974187568) | HDFC 83871366032735 | ₹6,42,000 | RTGS | R95720579226 |
| 2 | HDFC 83871366032735 | Bandhan 73056887297587 | ₹4,00,000–₹6,00,000 | UPI/IMPS | Multiple |
| 3 | Bandhan + others → Kotak 1185080153 | (pooled) | ₹3,00,000–₹8,50,000 | UPI/NEFT | Multiple |
| 4 | Kotak 1185080153 → Federal 30654527754078 | ATM Cash | ₹1,45,000–₹1,86,000 | ATM | 867662226469 |

**Conclusion:** Funds originating from the victim's UPI payment were layered
through three mule accounts and withdrawn as cash within 3–5 banking days,
consistent with a organised UPI investment scam network.

---

## Key Reference Numbers for Manual Verification

- **Initial RTGS:** `R95720579226`
- **Pass-through credits:** `051698095623`, `508863857173`, `445482069527`
- **Pooling inflows:** `389922137580`, `384915118541`, `200216494773`
- **Cash-out ATM:** `867662226469`
