# Case: UPI Investment Scam — Victim Defrauded via Fake Mutual Fund Scheme

**Investigation ID:** INV_001  
**Fraud Type:** UPI Investment Scam  
**Number of Accounts:** 5  
**Approximate Money Involved:** ₹6,42,000 initial transfer; total proceeds pooled ~₹3,00,000–₹8,50,000  

## Background

A private individual was approached via WhatsApp with an offer to invest in a
"guaranteed return" mutual fund scheme. The victim was instructed to transfer
funds via UPI/RTGS to a seemingly legitimate account. The account turned out to
be a mule routing account. Funds were immediately forwarded through two more
intermediary accounts and ultimately withdrawn as cash.

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
| Victim / Originator | `1974187568_statement.csv` | KOTAK MAHINDRA BANK LTD | 1974187568 |
| First Receiver (Mule Layer 1) | `83871366032735 statement.pdf` | HDFC BANK LTD | 83871366032735 |
| Routing / Pass-Through (Layer 2) | `73056887297587_SOA.xlsx` | BANDHAN BANK LIMITED | 73056887297587 |
| Pooling Account (Layer 3) | `1185080153_statement.csv` | KOTAK MAHINDRA BANK LTD | 1185080153 |
| Cash-Out Account (Final Layer) | `30654527754078-01-12-2024to08-05-2026.pdf` | THE FEDERAL BANK LIMITED | 30654527754078 |

## Source Pattern Folders

- `pattern_03/statements/`
- `pattern_04/statements/`
- `pattern_09/statements/`
- `pattern_19/statements/`
