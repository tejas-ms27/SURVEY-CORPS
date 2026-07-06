# Case: Business Email Fraud — Fake Supplier Payment with Shared UPI Handle

**Investigation ID:** INV_006  
**Fraud Type:** Business Email Fraud / Shared Credential Abuse  
**Number of Accounts:** 5  
**Approximate Money Involved:** Shared UPI payments: ₹3,250–₹7,490 per transaction; Test transfers: ₹2–₹27; Reversal attempts: ₹11,400–₹28,700  

## Background

A fraudster impersonated a supplier and diverted invoice payments to two
separate mule accounts. Both mule accounts received payments to the same
fraudulent UPI handle, linking them as controlled by the same individual
or group. Additionally, a low-value test transfer was used to validate
account details before the main payment was executed — a common BEC technique.
A reversal cluster was also detected on the victim-side account, suggesting
the victim attempted to reverse the payment after discovering the fraud.

## Investigation Objective

Verify that the Case Reconstruction Engine can:

1. Identify all accounts involved in this case from the provided statements.
2. Reconstruct the complete chronological money movement.
3. Correctly assign roles (victim, mule, routing, pooling, cash-out) to each account.
4. Generate an investigation narrative that a CID officer could use directly.
5. Surface the correct pattern detectors and suppress false positives.

## Dataset Files for This Case

| Role | Statement File | Bank | Account Number |
|------|--------------|------|----------------|
| Mule Account 1 (Shared UPI) | `99138197699213-02-12-2024to08-05-2026.csv` | THE FEDERAL BANK LIMITED | 99138197699213 |
| Mule Account 2 (Shared UPI) | `35398829268638_SOA.csv` | BANDHAN BANK LIMITED | 35398829268638 |
| Test-Transfer Originator | `0165684919172270_statement.pdf` | PUNJAB NATIONAL BANK | 0165684919172270 |
| Test-Transfer Counterparty | `9456806565_statement.xlsx` | KOTAK MAHINDRA BANK LTD | 9456806565 |
| Victim Account (Reversal Attempts) | `5029518734468697-01-12-2024to08-05-2026.pdf` | UCO BANK | 5029518734468697 |

## Source Pattern Folders

- `pattern_13/statements/`
- `pattern_14/statements/`
- `pattern_16/statements/`
