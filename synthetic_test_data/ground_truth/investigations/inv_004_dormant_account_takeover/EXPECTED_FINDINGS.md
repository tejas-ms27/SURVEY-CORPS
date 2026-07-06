# Expected Findings — Dormant Account Takeover + Large First-Contact Fraud Transfer

## Pattern 18 — Dormant Reactivation

**Pattern Name:** dormant_reactivation  
**Pattern ID:** 18  
**Expected Confidence:** High  
**Why It Should Trigger:**  
Detects a long period of dormancy (no transactions) followed by a sudden burst of high-value activity, consistent with account reactivation for fraud use.  

**Accounts Involved:**
- `5699090930288949-26-12-2024to28-10-2025.pdf` — UCO BANK 5699090930288949 (Dormant Account (Reactivated))
- `1974187568_statement.csv` — KOTAK MAHINDRA BANK LTD 1974187568 (First-Contact Originator)
- `83871366032735 statement.pdf` — HDFC BANK LTD 83871366032735 (First-Contact Receiver)

**Supporting References:**
- Dormant account — first transaction after dormancy: `122531129346`
- Dormant account — reactivation burst tx 2: `885307217643`
- Dormant account — reactivation burst tx 3: `891723038808`
- First-contact RTGS (originator debit): `R95720579226`
- First-contact RTGS (receiver credit): `R95720579226`

## Pattern 19 — First Contact Large Transfer

**Pattern Name:** first_contact_large_transfer  
**Pattern ID:** 19  
**Expected Confidence:** High  
**Why It Should Trigger:**  
Detects a large-value transfer (RTGS/IMPS/NEFT) where the two parties have no prior transaction history, indicating a first-ever contact that is immediately high value.  

**Accounts Involved:**
- `5699090930288949-26-12-2024to28-10-2025.pdf` — UCO BANK 5699090930288949 (Dormant Account (Reactivated))
- `1974187568_statement.csv` — KOTAK MAHINDRA BANK LTD 1974187568 (First-Contact Originator)
- `83871366032735 statement.pdf` — HDFC BANK LTD 83871366032735 (First-Contact Receiver)

**Supporting References:**
- Dormant account — first transaction after dormancy: `122531129346`
- Dormant account — reactivation burst tx 2: `885307217643`
- Dormant account — reactivation burst tx 3: `891723038808`
- First-contact RTGS (originator debit): `R95720579226`
- First-contact RTGS (receiver credit): `R95720579226`
