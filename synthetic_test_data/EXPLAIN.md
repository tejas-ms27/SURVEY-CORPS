# What Is This Dataset and How to Use It

---

## What Is This?

This is a **fake (synthetic) bank statement dataset** created for testing a fraud detection pipeline.

All names, account numbers, and transactions inside the statements are fabricated. No real person's data is used. But the statements look and feel exactly like real Indian bank statements — same column names, same narration formats, same bank names (SBI, HDFC, Axis, Kotak, etc.).

The purpose is to test whether your fraud detection pipeline can correctly find fraud patterns — and correctly stay silent when there is no fraud.

---

## What Is Inside?

```
synthetic_test_data/
│
├── clean_control/                        ← Normal accounts, no fraud planted
├── pattern_01_duplicate_verification/    ← Fraud pattern 01 planted here
├── pattern_02_failed_reversed_transaction/
├── pattern_03_pass_through_routing/
├── pattern_04_fund_pooling/
├── pattern_05_structuring_smurfing/
├── pattern_07_circular_flow/
├── pattern_08_money_trail/
├── pattern_09_credit_to_cash_out/
├── pattern_10_cross_statement_links/
├── pattern_11_balance_parking/
├── pattern_12_hub_ranking/
├── pattern_13_low_value_testing/
├── pattern_14_reversal_clusters/
├── pattern_15_round_value_debit/
├── pattern_16_shared_upi/
├── pattern_17_round_trip/
├── pattern_18_dormant_reactivation/
├── pattern_19_first_contact_large_transfer/
├── pattern_22_llm_lead_unknown_shape/    ← No named pattern; only AI/ML should catch this
├── pattern_23_ml_ensemble_unknown_shape/ ← Same as above
├── combined_all_patterns/                ← All patterns together in one big set
└── ground_truth/
    └── investigations/                   ← Full cybercrime case scenarios
```

Each pattern folder has:
- A `statements/` subfolder with the actual bank statement files (PDF, CSV, XLSX, TXT)
- A `GROUND_TRUTH.md` file telling you exactly what your pipeline should find

---

## What Are the Fraud Patterns?

Each numbered folder tests one specific fraud behaviour:

| Pattern | What It Tests |
|---------|--------------|
| 01 — Duplicate Verification | Same transaction appears twice in a statement |
| 02 — Failed Reversed Transaction | A debit is reversed by an exact matching credit |
| 03 — Pass Through Routing | Account receives money and immediately forwards it |
| 04 — Fund Pooling | Multiple people send money to one account in a short time |
| 05 — Structuring / Smurfing | Cash deposits kept just below ₹50,000 to avoid reporting |
| 07 — Circular Flow | Money goes A → B → C → D → back to A |
| 08 — Money Trail | Same UTR number appears in two different accounts (sender + receiver) |
| 09 — Credit to Cash Out | Large deposit followed immediately by ATM withdrawal |
| 10 — Cross Statement Links | Same bank reference found in two separate account statements |
| 11 — Balance Parking | Large credit sits untouched in an account for a long time |
| 12 — Hub Ranking | One account receives money from many unrelated accounts |
| 13 — Low Value Testing | Tiny amounts (₹1–₹50) sent back and forth to test an account |
| 14 — Reversal Clusters | Repeated pattern of debit followed by reversal, many times |
| 15 — Round Value Debit | Transfers in suspiciously round amounts (₹25,000, ₹50,000, etc.) |
| 16 — Shared UPI | Same UPI handle appears across two separate account statements |
| 17 — Round Trip | Money sent out and returned via a different route |
| 18 — Dormant Reactivation | Account inactive for months, suddenly bursts into activity |
| 19 — First Contact Large Transfer | First-ever transaction between two parties is a huge amount |
| 22 — LLM Unknown Shape | Suspicious but no named rule; only an AI reading the narrations would catch it |
| 23 — ML Unknown Shape | Suspicious but only a machine learning model would detect it statistically |

---

## How to Test Your Pipeline — Pattern by Pattern

Go one folder at a time.

**Example: Testing Pattern 03 (Pass Through Routing)**

1. Go to `pattern_03_pass_through_routing/statements/`
2. Upload all the files inside to your pipeline
3. Your pipeline should report a Pass Through Routing finding on the subject account
4. Open `pattern_03_pass_through_routing/GROUND_TRUTH.md` to see:
   - Which account is the subject
   - Which UTR numbers are the evidence transactions
   - Which accounts are clean controls (should NOT get flagged)

Do this for every pattern folder. Each folder is independent.

---

## How to Test Your Pipeline — Investigation Cases

Investigations test whether your pipeline can handle a **complete real-world fraud case** where multiple patterns appear together across multiple accounts.

There are 6 investigation cases inside `ground_truth/investigations/`.

| Case | What It Simulates |
|------|------------------|
| INV_001 — UPI Investment Scam | Victim sends ₹6.4 lakh → routed through 3 mule accounts → cash withdrawn |
| INV_002 — Mule Network | 7 accounts all funnel money into one central hub account |
| INV_003 — Circular Money Laundering | Money travels A → B → C → D → back to A across SBI and UCO |
| INV_004 — Dormant Account Takeover | Dormant account suddenly wakes up alongside a first-contact large transfer |
| INV_005 — Smurfing + Cash Placement | Cash placed in small chunks → layered as round transfers → withdrawn |
| INV_006 — Business Email Fraud | Fake supplier UPI handle used across two accounts + reversal attempts |

**How to run an investigation test:**

1. Open the investigation folder, e.g. `ground_truth/investigations/inv_001_upi_investment_scam/`
2. Open `CASE_DESCRIPTION.md` — it lists all the statement files needed and which pattern folders they live in
3. Collect those statement files from the pattern folders mentioned
4. Upload them all together into your pipeline
5. Check your pipeline output against the 4 files in the investigation folder:

| File | What to Check |
|------|--------------|
| `EXPECTED_PATTERNS.md` | Every listed pattern must fire |
| `EXPECTED_FINDINGS.md` | Correct accounts and UTR numbers must be cited |
| `EXPECTED_NON_FINDINGS.md` | These patterns must NOT fire (false positives) |
| `EXPECTED_RECONSTRUCTION.md` | The money flow narrative your pipeline produces should match this |

---

## What Is the clean_control Folder?

This folder has normal, everyday banking accounts with no fraud planted.

Upload these to your pipeline and it should find **nothing suspicious**. If your pipeline flags these accounts, that is a false positive problem.

---

## What Is the combined_all_patterns Folder?

This folder has all fraud patterns mixed together inside one large set of accounts — like a real investigation dataset where you do not know in advance which accounts are suspicious.

Use this to test whether your pipeline can find all the patterns when they are not labelled or separated.

---

## What Are the Statement File Formats?

The statements come in 4 formats, just like real bank statements:

| Format | Banks |
|--------|-------|
| PDF | SBI, HDFC, Axis, Kotak, Bandhan, Federal, BOI, BOB, UCO, PNB |
| CSV | SBI, HDFC, Axis, Kotak, Bandhan, Federal, BOI, BOB, UCO |
| XLSX | SBI, HDFC, Axis, Kotak, Bandhan, Federal, BOI, BOB, UCO, PNB |
| TXT | SBI, PNB |

Your pipeline must be able to read all four formats.

---

## Quick Reference — Where Is Everything?

| What you need | Where to find it |
|---------------|-----------------|
| Bank statement files | Inside each `pattern_XX_.../statements/` folder |
| What your pipeline should find | `pattern_XX_.../GROUND_TRUTH.md` |
| Investigation case description | `ground_truth/investigations/inv_00X_.../CASE_DESCRIPTION.md` |
| Which patterns should fire in a case | `ground_truth/investigations/inv_00X_.../EXPECTED_PATTERNS.md` |
| Which patterns must NOT fire | `ground_truth/investigations/inv_00X_.../EXPECTED_NON_FINDINGS.md` |
| Full money flow for a case | `ground_truth/investigations/inv_00X_.../EXPECTED_RECONSTRUCTION.md` |
| All cases listed | `ground_truth/investigations/INDEX.md` |

---

## One-Line Summary

> Upload the statements from a folder into your pipeline, then open the GROUND_TRUTH.md or EXPECTED_*.md files beside it to know exactly what your pipeline should and should not report.
