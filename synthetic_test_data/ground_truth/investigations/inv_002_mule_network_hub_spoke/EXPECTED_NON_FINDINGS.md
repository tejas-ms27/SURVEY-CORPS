# Expected Non-Findings — Mule Network — Hub-and-Spoke Aggregation for Organised Cyber Fraud

The following patterns must NOT be reported as findings for this case.  
Triggering any of these would constitute a false positive.

| Pattern | Pattern Name | Reason Must Not Fire |
|---------|-------------|----------------------|
| 7 | circular flow | Funds do not return to any spoke — the flow is unidirectional into the hub. |
| 17 | round trip | No return leg detected in any spoke statement. |
| 18 | dormant reactivation | None of the spoke or hub accounts was dormant before this activity. |
| 1 | duplicate verification | No duplicate rows detected. |
| 5 | structuring smurfing | Individual transfer amounts are not calibrated below reporting thresholds. |
