# Expected Case Reconstruction — Circular Money Laundering — Layered Round-Trip via Multi-Bank Chain

## Circular Flow — Step-by-Step

### Hop 1 — Originator sends to Intermediary 1
- **From:** SBI account 16965968123 (`statement-16965968123.txt`)
- **To:** SBI account 25347399309 (`statement-25347399309.csv`)
- **Reference:** `N64528068915`
- **Corroboration:** Debit in originator's statement; Credit in Intermediary 1's statement.
- **Amount:** ~₹1,83,465–₹1,94,000

### Hop 2 — Intermediary 1 → Intermediary 2
- **From:** SBI account 25347399309
- **To:** SBI account 23088623376 (`statement-23088623376.txt`)
- **Reference:** `I72988444765`
- **Corroboration:** Debit in Intermediary 1; Credit in Intermediary 2.

### Hop 3 — Intermediary 2 → UCO Bank (Final Hop)
- **From:** SBI account 23088623376
- **To:** UCO Bank account 2561038363701767 (`2561038363701767-*.pdf`)
- **Reference:** `N93051572449`
- **Corroboration:** Debit in Intermediary 2; Credit in UCO statement.

### Hop 4 — UCO Bank returns funds to Originator (Loop Closed)
- **From:** UCO Bank account 2561038363701767
- **To:** SBI account 16965968123 (same as Hop 1 sender)
- **Reference:** `N50221616826`
- **Corroboration:** Debit in UCO statement; Credit in SBI originator statement.
- **This closes the loop.** Funds return to their starting point.

## Parallel Money Trail

Simultaneously, a separate corroborated transfer occurs:
- **Sender:** Kotak account 7966944653 (`7966944653_statement.xlsx`)
- **Receiver:** SBI account 48420599781 (`statement-48420599781.txt`)
- **Reference:** `I55274060571`
- **Amount:** ₹1,75,149.55
- **Corroboration:** Debit in Kotak statement; Credit in SBI statement with identical ref.

## Reconstruction Summary

| Hop | From Account | To Account | Bank(s) | Reference | Signal |
|-----|-------------|-----------|---------|-----------|--------|
| 1 | SBI 16965968123 | SBI 25347399309 | SBI→SBI | N64528068915 | Circular Start |
| 2 | SBI 25347399309 | SBI 23088623376 | SBI→SBI | I72988444765 | Intermediary |
| 3 | SBI 23088623376 | UCO 2561038363701767 | SBI→UCO | N93051572449 | Cross-Bank |
| 4 | UCO 2561038363701767 | SBI 16965968123 | UCO→SBI | N50221616826 | Loop Closed |
| P1 | Kotak 7966944653 | SBI 48420599781 | Kotak→SBI | I55274060571 | Parallel Trail |

The circular loop and the parallel money trail collectively demonstrate a
coordinated layering operation using four accounts across two banks.

---

## Key Reference Numbers for Manual Verification

- **Hop 1 (Originator → Intermediary 1):** `N64528068915`
- **Hop 2 (Intermediary 1 → Intermediary 2):** `I72988444765`
- **Hop 3 (Intermediary 2 → Final Hop):** `N93051572449`
- **Hop 4 (Final Hop → Originator, completes loop):** `N50221616826`
- **Parallel trail debit/credit:** `I55274060571`
