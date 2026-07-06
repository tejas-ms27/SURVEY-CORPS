# Expected Findings — Business Email Fraud — Fake Supplier Payment with Shared UPI Handle

## Pattern 16 — Shared Upi

**Pattern Name:** shared_upi  
**Pattern ID:** 16  
**Expected Confidence:** High  
**Why It Should Trigger:**  
Detects the same UPI handle or beneficiary identifier appearing across two or more separate account statements, linking accounts that are nominally unrelated.  

**Accounts Involved:**
- `99138197699213-02-12-2024to08-05-2026.csv` — THE FEDERAL BANK LIMITED 99138197699213 (Mule Account 1 (Shared UPI))
- `35398829268638_SOA.csv` — BANDHAN BANK LIMITED 35398829268638 (Mule Account 2 (Shared UPI))
- `0165684919172270_statement.pdf` — PUNJAB NATIONAL BANK 0165684919172270 (Test-Transfer Originator)
- `9456806565_statement.xlsx` — KOTAK MAHINDRA BANK LTD 9456806565 (Test-Transfer Counterparty)
- `5029518734468697-01-12-2024to08-05-2026.pdf` — UCO BANK 5029518734468697 (Victim Account (Reversal Attempts))

**Supporting References:**
- Shared UPI tx in Mule 1 (Federal): `454765872505`
- Shared UPI tx in Mule 2 (Bandhan): `001614410230`
- Test transfer 1 (both sides): `U40014894936`
- Test transfer 2 (both sides): `U22264596871`
- Test transfer 3 (both sides): `U44532517544`
- Reversal cluster debit 1: `U31538669531`
- Reversal cluster credit 1: `740682745330`
- Reversal cluster debit 2: `U71434768704`
- Reversal cluster credit 2: `241754535853`
- Reversal cluster debit 3: `U61130734906`
- Reversal cluster credit 3: `510631731294`

## Pattern 13 — Low Value Testing

**Pattern Name:** low_value_testing  
**Pattern ID:** 13  
**Expected Confidence:** High  
**Why It Should Trigger:**  
Detects reciprocal micro-transfers (₹1–₹50) flowing in both directions between two accounts, a classic account validation or channel-testing technique used before large fraud transfers.  

**Accounts Involved:**
- `99138197699213-02-12-2024to08-05-2026.csv` — THE FEDERAL BANK LIMITED 99138197699213 (Mule Account 1 (Shared UPI))
- `35398829268638_SOA.csv` — BANDHAN BANK LIMITED 35398829268638 (Mule Account 2 (Shared UPI))
- `0165684919172270_statement.pdf` — PUNJAB NATIONAL BANK 0165684919172270 (Test-Transfer Originator)
- `9456806565_statement.xlsx` — KOTAK MAHINDRA BANK LTD 9456806565 (Test-Transfer Counterparty)
- `5029518734468697-01-12-2024to08-05-2026.pdf` — UCO BANK 5029518734468697 (Victim Account (Reversal Attempts))

**Supporting References:**
- Shared UPI tx in Mule 1 (Federal): `454765872505`
- Shared UPI tx in Mule 2 (Bandhan): `001614410230`
- Test transfer 1 (both sides): `U40014894936`
- Test transfer 2 (both sides): `U22264596871`
- Test transfer 3 (both sides): `U44532517544`
- Reversal cluster debit 1: `U31538669531`
- Reversal cluster credit 1: `740682745330`
- Reversal cluster debit 2: `U71434768704`
- Reversal cluster credit 2: `241754535853`
- Reversal cluster debit 3: `U61130734906`
- Reversal cluster credit 3: `510631731294`

## Pattern 14 — Reversal Clusters

**Pattern Name:** reversal_clusters  
**Pattern ID:** 14  
**Expected Confidence:** High  
**Why It Should Trigger:**  
Detects clusters of UPI debit transactions each followed by a matching reversal credit, repeating across multiple cycles, suggesting systematic reversal exploitation.  

**Accounts Involved:**
- `99138197699213-02-12-2024to08-05-2026.csv` — THE FEDERAL BANK LIMITED 99138197699213 (Mule Account 1 (Shared UPI))
- `35398829268638_SOA.csv` — BANDHAN BANK LIMITED 35398829268638 (Mule Account 2 (Shared UPI))
- `0165684919172270_statement.pdf` — PUNJAB NATIONAL BANK 0165684919172270 (Test-Transfer Originator)
- `9456806565_statement.xlsx` — KOTAK MAHINDRA BANK LTD 9456806565 (Test-Transfer Counterparty)
- `5029518734468697-01-12-2024to08-05-2026.pdf` — UCO BANK 5029518734468697 (Victim Account (Reversal Attempts))

**Supporting References:**
- Shared UPI tx in Mule 1 (Federal): `454765872505`
- Shared UPI tx in Mule 2 (Bandhan): `001614410230`
- Test transfer 1 (both sides): `U40014894936`
- Test transfer 2 (both sides): `U22264596871`
- Test transfer 3 (both sides): `U44532517544`
- Reversal cluster debit 1: `U31538669531`
- Reversal cluster credit 1: `740682745330`
- Reversal cluster debit 2: `U71434768704`
- Reversal cluster credit 2: `241754535853`
- Reversal cluster debit 3: `U61130734906`
- Reversal cluster credit 3: `510631731294`
