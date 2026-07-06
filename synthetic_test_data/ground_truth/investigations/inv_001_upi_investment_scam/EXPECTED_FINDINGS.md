# Expected Findings — UPI Investment Scam — Victim Defrauded via Fake Mutual Fund Scheme

## Pattern 19 — First Contact Large Transfer

**Pattern Name:** first_contact_large_transfer  
**Pattern ID:** 19  
**Expected Confidence:** High  
**Why It Should Trigger:**  
Detects a large-value transfer (RTGS/IMPS/NEFT) where the two parties have no prior transaction history, indicating a first-ever contact that is immediately high value.  

**Accounts Involved:**
- `1974187568_statement.csv` — KOTAK MAHINDRA BANK LTD 1974187568 (Victim / Originator)
- `83871366032735 statement.pdf` — HDFC BANK LTD 83871366032735 (First Receiver (Mule Layer 1))
- `73056887297587_SOA.xlsx` — BANDHAN BANK LIMITED 73056887297587 (Routing / Pass-Through (Layer 2))
- `1185080153_statement.csv` — KOTAK MAHINDRA BANK LTD 1185080153 (Pooling Account (Layer 3))
- `30654527754078-01-12-2024to08-05-2026.pdf` — THE FEDERAL BANK LIMITED 30654527754078 (Cash-Out Account (Final Layer))

**Supporting References:**
- Initial RTGS: `R95720579226`
- Pass-through credits: `051698095623`, `508863857173`, `445482069527`
- Pooling inflows: `389922137580`, `384915118541`, `200216494773`
- Cash-out ATM: `867662226469`

## Pattern 3 — Pass Through Routing

**Pattern Name:** pass_through_routing  
**Pattern ID:** 3  
**Expected Confidence:** High  
**Why It Should Trigger:**  
Detects accounts that receive credits from multiple unrelated sources and rapidly forward the funds onward, retaining little residual balance. Characteristic of money mule or pass-through accounts.  

**Accounts Involved:**
- `1974187568_statement.csv` — KOTAK MAHINDRA BANK LTD 1974187568 (Victim / Originator)
- `83871366032735 statement.pdf` — HDFC BANK LTD 83871366032735 (First Receiver (Mule Layer 1))
- `73056887297587_SOA.xlsx` — BANDHAN BANK LIMITED 73056887297587 (Routing / Pass-Through (Layer 2))
- `1185080153_statement.csv` — KOTAK MAHINDRA BANK LTD 1185080153 (Pooling Account (Layer 3))
- `30654527754078-01-12-2024to08-05-2026.pdf` — THE FEDERAL BANK LIMITED 30654527754078 (Cash-Out Account (Final Layer))

**Supporting References:**
- Initial RTGS: `R95720579226`
- Pass-through credits: `051698095623`, `508863857173`, `445482069527`
- Pooling inflows: `389922137580`, `384915118541`, `200216494773`
- Cash-out ATM: `867662226469`

## Pattern 4 — Fund Pooling

**Pattern Name:** fund_pooling  
**Pattern ID:** 4  
**Expected Confidence:** High  
**Why It Should Trigger:**  
Detects rapid accumulation of funds from multiple senders within a short window, consistent with a pooling account aggregating proceeds before onward disbursement.  

**Accounts Involved:**
- `1974187568_statement.csv` — KOTAK MAHINDRA BANK LTD 1974187568 (Victim / Originator)
- `83871366032735 statement.pdf` — HDFC BANK LTD 83871366032735 (First Receiver (Mule Layer 1))
- `73056887297587_SOA.xlsx` — BANDHAN BANK LIMITED 73056887297587 (Routing / Pass-Through (Layer 2))
- `1185080153_statement.csv` — KOTAK MAHINDRA BANK LTD 1185080153 (Pooling Account (Layer 3))
- `30654527754078-01-12-2024to08-05-2026.pdf` — THE FEDERAL BANK LIMITED 30654527754078 (Cash-Out Account (Final Layer))

**Supporting References:**
- Initial RTGS: `R95720579226`
- Pass-through credits: `051698095623`, `508863857173`, `445482069527`
- Pooling inflows: `389922137580`, `384915118541`, `200216494773`
- Cash-out ATM: `867662226469`

## Pattern 9 — Credit To Cash Out

**Pattern Name:** credit_to_cash_out  
**Pattern ID:** 9  
**Expected Confidence:** High  
**Why It Should Trigger:**  
Detects a large inward credit (NEFT/IMPS/UPI) followed within a short window by one or more ATM withdrawals of a near-equivalent total amount, suggesting rapid cash-out of proceeds.  

**Accounts Involved:**
- `1974187568_statement.csv` — KOTAK MAHINDRA BANK LTD 1974187568 (Victim / Originator)
- `83871366032735 statement.pdf` — HDFC BANK LTD 83871366032735 (First Receiver (Mule Layer 1))
- `73056887297587_SOA.xlsx` — BANDHAN BANK LIMITED 73056887297587 (Routing / Pass-Through (Layer 2))
- `1185080153_statement.csv` — KOTAK MAHINDRA BANK LTD 1185080153 (Pooling Account (Layer 3))
- `30654527754078-01-12-2024to08-05-2026.pdf` — THE FEDERAL BANK LIMITED 30654527754078 (Cash-Out Account (Final Layer))

**Supporting References:**
- Initial RTGS: `R95720579226`
- Pass-through credits: `051698095623`, `508863857173`, `445482069527`
- Pooling inflows: `389922137580`, `384915118541`, `200216494773`
- Cash-out ATM: `867662226469`
