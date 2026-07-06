# Expected Findings — Circular Money Laundering — Layered Round-Trip via Multi-Bank Chain

## Pattern 7 — Circular Flow

**Pattern Name:** circular_flow  
**Pattern ID:** 7  
**Expected Confidence:** High  
**Why It Should Trigger:**  
Detects a closed-loop flow where funds originate from Account A, pass through one or more intermediaries, and eventually return to Account A, indicating layering or wash transactions.  

**Accounts Involved:**
- `statement-16965968123.txt` — STATE BANK OF INDIA 16965968123 (Originator (Loop Start/End))
- `statement-25347399309.csv` — STATE BANK OF INDIA 25347399309 (Intermediary 1)
- `statement-23088623376.txt` — STATE BANK OF INDIA 23088623376 (Intermediary 2)
- `2561038363701767-01-12-2024to07-05-2026.pdf` — UCO BANK 2561038363701767 (Final Hop (Returns to Originator))
- `7966944653_statement.xlsx` — KOTAK MAHINDRA BANK LTD 7966944653 (Money Trail — Sender)
- `statement-48420599781.txt` — STATE BANK OF INDIA 48420599781 (Money Trail — Receiver)

**Supporting References:**
- Hop 1 (Originator → Intermediary 1): `N64528068915`
- Hop 2 (Intermediary 1 → Intermediary 2): `I72988444765`
- Hop 3 (Intermediary 2 → Final Hop): `N93051572449`
- Hop 4 (Final Hop → Originator, completes loop): `N50221616826`
- Parallel trail debit/credit: `I55274060571`

## Pattern 8 — Money Trail

**Pattern Name:** money_trail  
**Pattern ID:** 8  
**Expected Confidence:** High  
**Why It Should Trigger:**  
Detects a corroborated multi-hop fund movement where the same UTR/reference number appears as a debit in the sender's statement and a credit in the receiver's statement.  

**Accounts Involved:**
- `statement-16965968123.txt` — STATE BANK OF INDIA 16965968123 (Originator (Loop Start/End))
- `statement-25347399309.csv` — STATE BANK OF INDIA 25347399309 (Intermediary 1)
- `statement-23088623376.txt` — STATE BANK OF INDIA 23088623376 (Intermediary 2)
- `2561038363701767-01-12-2024to07-05-2026.pdf` — UCO BANK 2561038363701767 (Final Hop (Returns to Originator))
- `7966944653_statement.xlsx` — KOTAK MAHINDRA BANK LTD 7966944653 (Money Trail — Sender)
- `statement-48420599781.txt` — STATE BANK OF INDIA 48420599781 (Money Trail — Receiver)

**Supporting References:**
- Hop 1 (Originator → Intermediary 1): `N64528068915`
- Hop 2 (Intermediary 1 → Intermediary 2): `I72988444765`
- Hop 3 (Intermediary 2 → Final Hop): `N93051572449`
- Hop 4 (Final Hop → Originator, completes loop): `N50221616826`
- Parallel trail debit/credit: `I55274060571`

## Pattern 17 — Round Trip

**Pattern Name:** round_trip  
**Pattern ID:** 17  
**Expected Confidence:** High  
**Why It Should Trigger:**  
Detects a round-trip pattern where funds sent from Account A reach Account B via an intermediary and are subsequently returned to Account A through a different channel.  

**Accounts Involved:**
- `statement-16965968123.txt` — STATE BANK OF INDIA 16965968123 (Originator (Loop Start/End))
- `statement-25347399309.csv` — STATE BANK OF INDIA 25347399309 (Intermediary 1)
- `statement-23088623376.txt` — STATE BANK OF INDIA 23088623376 (Intermediary 2)
- `2561038363701767-01-12-2024to07-05-2026.pdf` — UCO BANK 2561038363701767 (Final Hop (Returns to Originator))
- `7966944653_statement.xlsx` — KOTAK MAHINDRA BANK LTD 7966944653 (Money Trail — Sender)
- `statement-48420599781.txt` — STATE BANK OF INDIA 48420599781 (Money Trail — Receiver)

**Supporting References:**
- Hop 1 (Originator → Intermediary 1): `N64528068915`
- Hop 2 (Intermediary 1 → Intermediary 2): `I72988444765`
- Hop 3 (Intermediary 2 → Final Hop): `N93051572449`
- Hop 4 (Final Hop → Originator, completes loop): `N50221616826`
- Parallel trail debit/credit: `I55274060571`
