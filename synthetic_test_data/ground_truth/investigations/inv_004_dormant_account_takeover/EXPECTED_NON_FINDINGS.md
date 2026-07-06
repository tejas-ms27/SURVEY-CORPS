# Expected Non-Findings — Dormant Account Takeover + Large First-Contact Fraud Transfer

The following patterns must NOT be reported as findings for this case.  
Triggering any of these would constitute a false positive.

| Pattern | Pattern Name | Reason Must Not Fire |
|---------|-------------|----------------------|
| 7 | circular flow | Funds do not loop back to originator. |
| 12 | hub ranking | Only 1–2 accounts involved; no hub aggregation pattern. |
| 5 | structuring smurfing | Amounts do not follow sub-threshold structuring. |
| 14 | reversal clusters | No debit-reversal pairs detected. |
| 16 | shared upi | No shared UPI handle across accounts. |
