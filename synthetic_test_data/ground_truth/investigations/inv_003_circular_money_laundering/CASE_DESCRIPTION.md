# Case: Circular Money Laundering — Layered Round-Trip via Multi-Bank Chain

**Investigation ID:** INV_003  
**Fraud Type:** Layered Money Laundering / Circular Flow  
**Number of Accounts:** 6  
**Approximate Money Involved:** Circular loop: ₹1,83,465–₹1,94,000; Parallel trail: ₹1,75,149  

## Background

A criminal group launders proceeds by moving funds through a chain of accounts
at different banks, eventually returning the funds to the originating account.
This circular flow creates an appearance of legitimate commercial activity
(payments between businesses) while obscuring the illicit origin. Simultaneously,
a parallel money trail confirms cross-bank fund movement corroborated by
matching UTR numbers on both sides of each transfer.

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
| Originator (Loop Start/End) | `statement-16965968123.txt` | STATE BANK OF INDIA | 16965968123 |
| Intermediary 1 | `statement-25347399309.csv` | STATE BANK OF INDIA | 25347399309 |
| Intermediary 2 | `statement-23088623376.txt` | STATE BANK OF INDIA | 23088623376 |
| Final Hop (Returns to Originator) | `2561038363701767-01-12-2024to07-05-2026.pdf` | UCO BANK | 2561038363701767 |
| Money Trail — Sender | `7966944653_statement.xlsx` | KOTAK MAHINDRA BANK LTD | 7966944653 |
| Money Trail — Receiver | `statement-48420599781.txt` | STATE BANK OF INDIA | 48420599781 |

## Source Pattern Folders

- `pattern_07/statements/`
- `pattern_08/statements/`
