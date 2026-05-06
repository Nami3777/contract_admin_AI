# Stage 04 — Report: Reconciliation List → API Response + UI Display

**Job**: Format the reconciliation results from Stage 03 into a structured JSON response and render it in the browser as a colour-coded table.

---

## Inputs

| Source | File/Location | Section/Scope | Why |
|--------|---------------|---------------|-----|
| Reconciliation list | Stage 03 output | Full list | Items to display |
| Metadata | Stage 02 output (header fields) | change_order, work_date, record IDs | Context for the report |
| Processing time | Pipeline timer | Elapsed seconds | Transparency for the user |
| Display rules | `references/display_format.md` | Full file | Colour coding and layout |

---

## Process

1. Compute summary counts: total, matches, flags, new, missing
2. Assemble JSON response object (see output schema below)
3. Return response from `POST /api/reconcile`
4. Frontend JS (`index.html`) receives JSON, renders:
   - Summary chips (counts + processing time)
   - Table rows with colour-coded status badges
   - Smooth scroll to results

---

## Outputs

| Artifact | Location | Format |
|----------|----------|--------|
| JSON response | HTTP 200 from `/api/reconcile` | See schema below |
| Rendered table | Browser DOM (`#result-tbody`) | HTML via `renderResults()` in index.html |

### Response Schema

```json
{
  "change_order": "CO-21",
  "work_date": "05-Aug-21",
  "ca_record_id": "2020-4091-DWR-7",
  "contractor_record_id": "2020-4091-DWR-9",
  "processing_time_seconds": 14.3,
  "summary": {
    "total": 8,
    "matches": 5,
    "flags": 2,
    "new": 1,
    "missing": 0
  },
  "items": [
    {
      "category": "Labour",
      "description": "Foreman",
      "ca_value": 4.0,
      "contractor_value": 4.5,
      "unit": "man-hours",
      "variance_pct": 12.5,
      "status": "FLAG",
      "notes": null
    }
  ]
}
```

---

## Implementation

```
api/main.py → POST /api/reconcile (assembles response)
index.html  → renderResults(data) (renders to DOM)
```
