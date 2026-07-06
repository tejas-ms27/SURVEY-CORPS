# Case: Mule Network — Hub-and-Spoke Aggregation for Organised Cyber Fraud

**Investigation ID:** INV_002  
**Fraud Type:** Mule Network / Hub-and-Spoke  
**Number of Accounts:** 8  
**Approximate Money Involved:** ₹31,200–₹63,400 per spoke transfer; total aggregated at hub from 7 spokes  

## Background

A central mule account (the hub) is controlled by an organised cyber-fraud group.
Multiple peripheral accounts (spokes) — each operated by a recruited money mule —
receive small amounts from fraud victims and transfer them to the hub. The hub then
aggregates the proceeds and routes them for layering. This structure makes individual
spoke accounts appear to have limited suspicious activity, while the hub shows
the full scale of the operation.

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
| Hub (Aggregator) | `2583442857_statement.xlsx` | KOTAK MAHINDRA BANK LTD | 2583442857 |
| Spoke Account 1 | `2871288856142199_statement.pdf` | PUNJAB NATIONAL BANK | 2871288856142199 |
| Spoke Account 2 | `12691319567650-01-12-2024to08-05-2026.xlsx` | THE FEDERAL BANK LIMITED | 12691319567650 |
| Spoke Account 3 | `5089515621605975-02-12-2024to08-05-2026.xlsx` | UCO BANK | 5089515621605975 |
| Spoke Account 4 | `59347392058238 statement.csv` | HDFC BANK LTD | 59347392058238 |
| Spoke Account 5 | `81206073174626-02-12-2024to08-05-2026.xlsx` | THE FEDERAL BANK LIMITED | 81206073174626 |
| Spoke Account 6 | `statement-99628833989.xlsx` | STATE BANK OF INDIA | 99628833989 |
| Spoke Account 7 | `5226559152743878_statement.txt` | PUNJAB NATIONAL BANK | 5226559152743878 |

## Source Pattern Folders

- `pattern_12/statements/`
