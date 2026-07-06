# Investigation Cases Index

Each sub-folder is a complete cybercrime investigation case for testing the Case Reconstruction Engine.

| ID | Title | Fraud Type | Patterns |
|----|-------|-----------|---------|
| INV_001 | [UPI Investment Scam — Victim Defrauded via Fake Mutual Fund Scheme](inv_001_upi_investment_scam/CASE_DESCRIPTION.md) | UPI Investment Scam | first contact large transfer, pass through routing, fund pooling, credit to cash out |
| INV_002 | [Mule Network — Hub-and-Spoke Aggregation for Organised Cyber Fraud](inv_002_mule_network_hub_spoke/CASE_DESCRIPTION.md) | Mule Network / Hub-and-Spoke | hub ranking, fund pooling |
| INV_003 | [Circular Money Laundering — Layered Round-Trip via Multi-Bank Chain](inv_003_circular_money_laundering/CASE_DESCRIPTION.md) | Layered Money Laundering / Circular Flow | circular flow, money trail, round trip |
| INV_004 | [Dormant Account Takeover + Large First-Contact Fraud Transfer](inv_004_dormant_account_takeover/CASE_DESCRIPTION.md) | Account Takeover / Dormant Account Exploitation | dormant reactivation, first contact large transfer |
| INV_005 | [Smurfing + Structured Cash Placement via Multiple Channels](inv_005_smurfing_structured_placement/CASE_DESCRIPTION.md) | Structured Cash Placement / Smurfing | structuring smurfing, round value debit, credit to cash out |
| INV_006 | [Business Email Fraud — Fake Supplier Payment with Shared UPI Handle](inv_006_business_email_fraud_shared_upi/CASE_DESCRIPTION.md) | Business Email Fraud / Shared Credential Abuse | shared upi, low value testing, reversal clusters |

## How to Use

1. Open the `CASE_DESCRIPTION.md` to understand the investigation scenario.
2. Open the statement files listed in each case (from the source pattern folders).
3. Run the Case Reconstruction Engine on those statements.
4. Compare the engine output against `EXPECTED_RECONSTRUCTION.md`.
5. Verify all patterns in `EXPECTED_PATTERNS.md` fired.
6. Verify no patterns in `EXPECTED_NON_FINDINGS.md` fired.
7. Check the narrative quality against `EXPECTED_FINDINGS.md`.
