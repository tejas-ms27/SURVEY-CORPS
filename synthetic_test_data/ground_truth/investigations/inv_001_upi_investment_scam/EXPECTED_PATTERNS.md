# Expected Patterns — UPI Investment Scam — Victim Defrauded via Fake Mutual Fund Scheme

The following pattern detectors are expected to fire on this case:

✓ **Pattern 19 — First Contact Large Transfer**
  - Detects a large-value transfer (RTGS/IMPS/NEFT) where the two parties have no prior transaction history, indicating a first-ever contact that is immediately high value.

✓ **Pattern 3 — Pass Through Routing**
  - Detects accounts that receive credits from multiple unrelated sources and rapidly forward the funds onward, retaining little residual balance. Characteristic of money mule or pass-through accounts.

✓ **Pattern 4 — Fund Pooling**
  - Detects rapid accumulation of funds from multiple senders within a short window, consistent with a pooling account aggregating proceeds before onward disbursement.

✓ **Pattern 9 — Credit To Cash Out**
  - Detects a large inward credit (NEFT/IMPS/UPI) followed within a short window by one or more ATM withdrawals of a near-equivalent total amount, suggesting rapid cash-out of proceeds.
