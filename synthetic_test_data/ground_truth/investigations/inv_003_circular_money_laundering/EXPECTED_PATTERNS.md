# Expected Patterns — Circular Money Laundering — Layered Round-Trip via Multi-Bank Chain

The following pattern detectors are expected to fire on this case:

✓ **Pattern 7 — Circular Flow**
  - Detects a closed-loop flow where funds originate from Account A, pass through one or more intermediaries, and eventually return to Account A, indicating layering or wash transactions.

✓ **Pattern 8 — Money Trail**
  - Detects a corroborated multi-hop fund movement where the same UTR/reference number appears as a debit in the sender's statement and a credit in the receiver's statement.

✓ **Pattern 17 — Round Trip**
  - Detects a round-trip pattern where funds sent from Account A reach Account B via an intermediary and are subsequently returned to Account A through a different channel.
