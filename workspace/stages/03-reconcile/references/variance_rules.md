# Variance Rules — Stage 03

## Threshold

**±5%** is the Ontario MTO regulatory standard for T&M contract reconciliation.

```
variance_pct = abs(contractor_value - ca_value) / ca_value * 100

if variance_pct <= 5.0 → MATCH
if variance_pct >  5.0 → FLAG
```

## Special Cases

| Condition | Formula | Status |
|---|---|---|
| Both values are 0.0 | variance = 0.0 | MATCH |
| CA value is 0, Contractor claims > 0 | variance = 100.0 | FLAG |
| CA has item, Contractor does not | variance = null | MISSING |
| Contractor has item, CA does not | variance = null | NEW |

## Matching Normalization

**Labour**: `name.lower().strip().replace("/", " ")`
- "Driver / Teamster" → "driver  teamster" → "driver teamster"

**Equipment**: Extract first two tokens as match key
- "94 INTL 4900 TANDEM CRASH" → match key "94 INTL"
- "10 CAT 420 BACKHOE" → match key "10 CAT"
- Rationale: CA and Contractor may use different name lengths for same asset

**Materials**: `(description or category).lower().strip()`

## Units by Category

| Category | Unit |
|---|---|
| Labour | man-hours |
| Equipment | hours |
| Material | as specified (EA, m, tonne, m2, etc.) |

## Notes Field Population

- MATCH: notes = null (no explanation needed)
- FLAG: notes = "CA: [remarks] | Contractor: [remarks]" if either has remarks; else null
- NEW: notes = "Present in Contractor report only"
- MISSING: notes = "Present in CA report only"
