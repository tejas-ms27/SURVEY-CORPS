# Expected Patterns — Mule Network — Hub-and-Spoke Aggregation for Organised Cyber Fraud

The following pattern detectors are expected to fire on this case:

✓ **Pattern 12 — Hub Ranking**
  - Detects a central hub account that receives funds from an unusually large number of distinct sender accounts within the analysis window, a hallmark of mule network aggregation.

✓ **Pattern 4 — Fund Pooling**
  - Detects rapid accumulation of funds from multiple senders within a short window, consistent with a pooling account aggregating proceeds before onward disbursement.
