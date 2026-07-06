# Expected Case Reconstruction — Mule Network — Hub-and-Spoke Aggregation for Organised Cyber Fraud

## Step-by-Step Money Movement

All transfers flow from individual spoke accounts into the central hub
(Kotak account 2583442857). Every spoke-to-hub transfer is corroborated
by matching entries on both the spoke's statement and the hub's statement.

### Spoke-to-Hub Transfer Map

| Spoke | Bank | Account | Transfer Ref | Direction |
|-------|------|---------|-------------|-----------|
| Spoke 1 | PUNJAB NATIONAL BANK | 2871288856142199 | N39558289002 | Spoke → Hub |
| Spoke 2 | THE FEDERAL BANK LIMITED | 12691319567650 | I43243339199 | Spoke → Hub |
| Spoke 3 | UCO BANK | 5089515621605975 | I71359001100 | Spoke → Hub |
| Spoke 4 | HDFC BANK LTD | 59347392058238 | I75823920825 | Spoke → Hub |
| Spoke 5 | THE FEDERAL BANK LIMITED | 81206073174626 | I18986330736 | Spoke → Hub |
| Spoke 6 | STATE BANK OF INDIA | 99628833989 | U72411748544 | Spoke → Hub |
| Spoke 7 | PUNJAB NATIONAL BANK | 5226559152743878 | N65830057946 | Spoke → Hub |

### Corroboration Method
For each ref above:
1. Open the spoke's statement file and locate the debit entry with that ref.
2. Open `2583442857_statement.xlsx` (hub) and locate the matching credit entry with the same ref.
3. Amounts must match exactly — this is the cross-statement corroboration requirement.

### Hub Behaviour
- The hub account (Kotak 2583442857) receives from 7 distinct accounts across
  5 different banks within the analysis window.
- This concentration of inflows from multiple unrelated sources, combined with
  the hub's own outward routing behaviour, is the core hub_ranking signal.

## Reconstruction Summary

Seven spoke accounts, each at a different bank and in different cities,
funnel proceeds into a single Kotak hub account. The hub account shows
no corresponding retail expenditure — all inflows are received and held
or forwarded. This is the structural signature of a professional money
mule network operating across multiple banking relationships simultaneously.

---

## Key Reference Numbers for Manual Verification

- **Spoke 1 → Hub:** `N39558289002`
- **Spoke 2 → Hub:** `I43243339199`
- **Spoke 3 → Hub:** `I71359001100`
- **Spoke 4 → Hub:** `I75823920825`
- **Spoke 5 → Hub:** `I18986330736`
- **Spoke 6 → Hub:** `U72411748544`
- **Spoke 7 → Hub:** `N65830057946`
