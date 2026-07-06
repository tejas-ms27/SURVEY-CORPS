# Expected Case Reconstruction — Business Email Fraud — Fake Supplier Payment with Shared UPI Handle

## Step 1 — Account Validation via Low-Value Test Transfers

Before the main fraud payment, the fraudster sent micro-amounts between
PNB account 0165684919172270 and Kotak account 9456806565 to confirm
account validity and UPI routing.

| Test | Reference | Confirmation |
|------|-----------|-------------|
| Test 1 | U40014894936 | Both `0165684919172270_statement.pdf` (PNB) and `9456806565_statement.xlsx` (Kotak) contain this ref — cross-validated |
| Test 2 | U22264596871 | Same cross-validation — debit in one, credit in other |
| Test 3 | U44532517544 | Third probe confirming bidirectional channel |

**To verify:** Open both statements and search for each ref — it must appear
in both statements as complementary debit/credit entries.

## Step 2 — Main Fraud Payments via Shared UPI Handle

The fraudster's UPI handle (`akash37@okaxis`) appears in both:
- Federal Bank account 99138197699213 (`99138197699213-*.csv`), ref `454765872505`
- Bandhan Bank account 35398829268638 (`35398829268638_SOA.csv`), ref `001614410230`

**Amount range:** ₹3,250–₹7,490 per transaction
**Signal:** The same UPI handle receiving payments in two nominally unrelated
accounts proves the same individual controls both accounts.

## Step 3 — Victim Reversal Attempts

After discovering the fraud, the victim (UCO Bank account 5029518734468697)
attempted to reverse payments. These appear as debit-reversal clusters:

| Cycle | Debit Ref | Reversal Ref | Amount Range |
|-------|-----------|-------------|-------------|
| 1 | U31538669531 | 740682745330 | ₹11,400–₹28,700 |
| 2 | U71434768704 | 241754535853 | ₹11,400–₹28,700 |
| 3 | U61130734906 | 510631731294 | ₹11,400–₹28,700 |

**Statement:** `5029518734468697-01-12-2024to08-05-2026.pdf`
**To verify:** Each cycle should show a UPI debit followed closely (within
hours or days) by a matching reversal credit of the exact same amount.

## Reconstruction Summary

| Phase | Account | Bank | Event | Key Reference |
|-------|---------|------|-------|--------------|
| Validation | PNB 0165684919172270 ↔ Kotak 9456806565 | PNB / Kotak | 3× micro-probe transfers | U40014894936, U22264596871, U44532517544 |
| Fraud payment 1 | Federal 99138197699213 | Federal | UPI receipt via akash37@okaxis | 454765872505 |
| Fraud payment 2 | Bandhan 35398829268638 | Bandhan | UPI receipt via same handle | 001614410230 |
| Victim reversal | UCO 5029518734468697 | UCO | 3× debit-reversal attempts | U31538669531 … 510631731294 |

---

## Key Reference Numbers for Manual Verification

- **Shared UPI tx in Mule 1 (Federal):** `454765872505`
- **Shared UPI tx in Mule 2 (Bandhan):** `001614410230`
- **Test transfer 1 (both sides):** `U40014894936`
- **Test transfer 2 (both sides):** `U22264596871`
- **Test transfer 3 (both sides):** `U44532517544`
- **Reversal cluster debit 1:** `U31538669531`
- **Reversal cluster credit 1:** `740682745330`
- **Reversal cluster debit 2:** `U71434768704`
- **Reversal cluster credit 2:** `241754535853`
- **Reversal cluster debit 3:** `U61130734906`
- **Reversal cluster credit 3:** `510631731294`
