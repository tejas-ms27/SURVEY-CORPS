# Expected Patterns — Dormant Account Takeover + Large First-Contact Fraud Transfer

The following pattern detectors are expected to fire on this case:

✓ **Pattern 18 — Dormant Reactivation**
  - Detects a long period of dormancy (no transactions) followed by a sudden burst of high-value activity, consistent with account reactivation for fraud use.

✓ **Pattern 19 — First Contact Large Transfer**
  - Detects a large-value transfer (RTGS/IMPS/NEFT) where the two parties have no prior transaction history, indicating a first-ever contact that is immediately high value.
