# Case: Dormant Account Takeover + Large First-Contact Fraud Transfer

**Investigation ID:** INV_004  
**Fraud Type:** Account Takeover / Dormant Account Exploitation  
**Number of Accounts:** 3  
**Approximate Money Involved:** Dormant reactivation: ₹1,170–₹1,44,000; First-contact RTGS: ₹6,42,000  

## Background

A UCO Bank account that had been dormant for an extended period was suddenly
reactivated and used to receive and forward a large transfer. In parallel, a
Kotak Bank account with no prior transaction history received a first-time
large RTGS transfer. Together these incidents suggest a coordinated account
takeover scheme where dormant accounts and freshly opened mule accounts are
activated simultaneously for a fraud event.

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
| Dormant Account (Reactivated) | `5699090930288949-26-12-2024to28-10-2025.pdf` | UCO BANK | 5699090930288949 |
| First-Contact Originator | `1974187568_statement.csv` | KOTAK MAHINDRA BANK LTD | 1974187568 |
| First-Contact Receiver | `83871366032735 statement.pdf` | HDFC BANK LTD | 83871366032735 |

## Source Pattern Folders

- `pattern_18/statements/`
- `pattern_19/statements/`
