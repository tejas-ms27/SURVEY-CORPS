# Expected Non-Findings — UPI Investment Scam — Victim Defrauded via Fake Mutual Fund Scheme

The following patterns must NOT be reported as findings for this case.  
Triggering any of these would constitute a false positive.

| Pattern | Pattern Name | Reason Must Not Fire |
|---------|-------------|----------------------|
| 7 | circular flow | Funds do not return to originator — the chain terminates at cash withdrawal. |
| 1 | duplicate verification | No duplicate transaction rows detected in any statement. |
| 5 | structuring smurfing | Deposits are not kept below ₹50,000 threshold; this is a single large transfer. |
| 18 | dormant reactivation | None of these accounts show prior dormancy before the fraud window. |
| 16 | shared upi | Different UPI handles are used at each hop; no shared handle across accounts. |
