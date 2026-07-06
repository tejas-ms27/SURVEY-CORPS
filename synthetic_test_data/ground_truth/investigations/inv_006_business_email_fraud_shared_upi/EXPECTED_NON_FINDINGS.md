# Expected Non-Findings — Business Email Fraud — Fake Supplier Payment with Shared UPI Handle

The following patterns must NOT be reported as findings for this case.  
Triggering any of these would constitute a false positive.

| Pattern | Pattern Name | Reason Must Not Fire |
|---------|-------------|----------------------|
| 4 | fund pooling | Amounts pooled are not from multiple unrelated senders at scale. |
| 12 | hub ranking | No hub-spoke aggregation; only two mule accounts linked by UPI handle. |
| 7 | circular flow | Funds do not return to any originator. |
| 11 | balance parking | No large credit left unspent; amounts are small. |
| 5 | structuring smurfing | No sub-threshold cash deposit structuring detected. |
