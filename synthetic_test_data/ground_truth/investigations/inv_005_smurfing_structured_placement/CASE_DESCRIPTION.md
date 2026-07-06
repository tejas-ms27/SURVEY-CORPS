# Case: Smurfing + Structured Cash Placement via Multiple Channels

**Investigation ID:** INV_005  
**Fraud Type:** Structured Cash Placement / Smurfing  
**Number of Accounts:** 3  
**Approximate Money Involved:** Structuring deposits: ₹44,900–₹49,900 × 8 events; Round-value transfers: ₹25,000–₹85,000 × 7; Cash-out: ₹1,45,000–₹1,86,000  

## Background

A suspect account at Axis Bank receives a series of cash deposits, each
carefully kept below ₹50,000 to avoid Currency Transaction Report (CTR)
obligations. Simultaneously, a linked HDFC account shows a cluster of
round-value outward transfers — a hallmark of layering after successful
placement. A Federal Bank account is used as the final cash-out vehicle
via ATM withdrawals after receiving a large aggregated credit.

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
| Placement Account (Structuring) | `750850479834326_statement.xlsx` | AXIS BANK LIMITED | 750850479834326 |
| Layering Account (Round Values) | `85315254644320 statement.pdf` | HDFC BANK LTD | 85315254644320 |
| Integration / Cash-Out Account | `30654527754078-01-12-2024to08-05-2026.pdf` | THE FEDERAL BANK LIMITED | 30654527754078 |

## Source Pattern Folders

- `pattern_05/statements/`
- `pattern_09/statements/`
- `pattern_15/statements/`
