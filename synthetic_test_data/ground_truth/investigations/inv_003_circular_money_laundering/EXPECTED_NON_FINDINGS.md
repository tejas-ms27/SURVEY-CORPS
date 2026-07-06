# Expected Non-Findings — Circular Money Laundering — Layered Round-Trip via Multi-Bank Chain

The following patterns must NOT be reported as findings for this case.  
Triggering any of these would constitute a false positive.

| Pattern | Pattern Name | Reason Must Not Fire |
|---------|-------------|----------------------|
| 5 | structuring smurfing | No pattern of sub-threshold deposits is present. |
| 12 | hub ranking | No single account receives from more than two others in this chain. |
| 18 | dormant reactivation | None of these accounts was dormant before the circular activity. |
| 19 | first contact large transfer | The parties have prior transaction history within the dataset. |
| 13 | low value testing | No micro-transfer probing is present. |
