# Expected Case Reconstruction — Dormant Account Takeover + Large First-Contact Fraud Transfer

## UCO Bank Dormant Account Reactivation

### Dormancy Evidence
- **Account:** UCO Bank 5699090930288949
- **Statement file:** `5699090930288949-26-12-2024to28-10-2025.pdf`
- **Observation:** The statement shows a prolonged gap with zero transactions,
  followed by a sudden burst of three transactions:
  1. Ref `122531129346` — First transaction post-dormancy
  2. Ref `885307217643` — Rapid follow-up transaction
  3. Ref `891723038808` — Third transaction within the burst window
- **Amount range:** ₹1,170 to ₹1,44,000 (escalating from small test to large amount)
- **Signal:** Dormant accounts reactivated for fraud typically begin with a
  small test transaction, then escalate — this account follows that exact pattern.

## First-Contact Large Transfer (Kotak → HDFC)

### Transfer Evidence
- **Originator:** Kotak account 1974187568 (`1974187568_statement.csv`)
- **Receiver:** HDFC account 83871366032735 (`83871366032735 statement.pdf`)
- **Reference:** `R95720579226` (RTGS)
- **Amount:** ₹6,42,000
- **Signal:** Searching `1974187568_statement.csv` for ref `R95720579226`
  shows this is the first-ever transaction between these parties — no prior
  credit or debit involving the HDFC account number or UPI handle appears
  anywhere in the Kotak statement history.

## Investigation Hypothesis

The reactivated UCO dormant account and the freshly utilised Kotak account
appear to be part of the same fraud activation wave. The dormant UCO account
may have been taken over (credentials compromised), while the Kotak account
may be a newly recruited mule account. Both were activated in close proximity
to receive or forward fraud proceeds.

## Reconstruction Summary

| Event | Account | Bank | Amount | Reference | Signal |
|-------|---------|------|--------|-----------|--------|
| Dormant burst tx 1 | 5699090930288949 | UCO | ~₹1,170 | 122531129346 | First post-dormancy tx |
| Dormant burst tx 2 | 5699090930288949 | UCO | ~₹50,000 | 885307217643 | Escalation |
| Dormant burst tx 3 | 5699090930288949 | UCO | ~₹1,44,000 | 891723038808 | Large reactivation |
| First-contact RTGS | 1974187568 (sender) | Kotak | ₹6,42,000 | R95720579226 | No prior relationship |
| First-contact receipt | 83871366032735 (receiver) | HDFC | ₹6,42,000 | R95720579226 | First inflow from Kotak |

---

## Key Reference Numbers for Manual Verification

- **Dormant account — first transaction after dormancy:** `122531129346`
- **Dormant account — reactivation burst tx 2:** `885307217643`
- **Dormant account — reactivation burst tx 3:** `891723038808`
- **First-contact RTGS (originator debit):** `R95720579226`
- **First-contact RTGS (receiver credit):** `R95720579226`
