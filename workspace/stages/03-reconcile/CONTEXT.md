# Stage 03 — Reconcile: Two DWRReports → Variance Results

**Job**: You are a deterministic variance calculator. Compare CA and Contractor DWRReport objects using pure Python math. No AI, no inference. Same inputs always produce same outputs.

---

## Inputs

| Source | File/Location | Section/Scope | Why |
|--------|---------------|---------------|-----|
| CA DWRReport | Stage 02 output | Full object | Inspector's recorded values |
| Contractor DWRReport | Stage 02 output | Full object | Contractor's claimed values |
| Variance rules | `references/variance_rules.md` | Full file | Threshold and matching logic |

---

## Process

1. **Labour reconciliation**
   - Normalize classification names (lowercase, strip, unify "/" separators)
   - Match CA items to Contractor items by normalized name
   - Calculate variance: `|contractor - CA| / CA × 100`
   - Flag if variance > 5%
   - Mark unmatched CA items as MISSING; unmatched Contractor items as NEW

2. **Equipment reconciliation**
   - Normalize equipment names (uppercase, strip punctuation)
   - Generate simplified match key: first two tokens (e.g. "94 INTL 4900 TANDEM" → "94 INTL")
   - Match by simplified key to handle fragmented vs full names
   - Apply same ±5% variance threshold on `hours_worked`

3. **Materials reconciliation**
   - Normalize `material_description` (or `material` if no description) lowercase
   - Match and compare `quantity` values
   - Apply ±5% threshold

4. Concatenate all three category results into a single flat list
5. Return list of reconciliation dicts with: category, description, ca_value, contractor_value, unit, variance_pct, status, notes

**Non-negotiable**: Do not use an LLM for this stage. All math is `abs(a - b) / a * 100`.

---

## Outputs

| Artifact | Location | Format |
|----------|----------|--------|
| Reconciliation list | Returned to Stage 04 | `List[dict]` with status MATCH/FLAG/NEW/MISSING |

---

## Implementation

```
api/pipeline.py → def reconcile_reports(ca_report, contractor_report) -> List[dict]
```

Statuses: `MATCH` (≤5% variance), `FLAG` (>5%), `NEW` (Contractor only), `MISSING` (CA only).
