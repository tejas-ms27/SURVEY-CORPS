# Expected Patterns — Business Email Fraud — Fake Supplier Payment with Shared UPI Handle

The following pattern detectors are expected to fire on this case:

✓ **Pattern 16 — Shared Upi**
  - Detects the same UPI handle or beneficiary identifier appearing across two or more separate account statements, linking accounts that are nominally unrelated.

✓ **Pattern 13 — Low Value Testing**
  - Detects reciprocal micro-transfers (₹1–₹50) flowing in both directions between two accounts, a classic account validation or channel-testing technique used before large fraud transfers.

✓ **Pattern 14 — Reversal Clusters**
  - Detects clusters of UPI debit transactions each followed by a matching reversal credit, repeating across multiple cycles, suggesting systematic reversal exploitation.
