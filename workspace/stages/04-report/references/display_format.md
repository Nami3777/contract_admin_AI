# Display Format Reference — Stage 04

## Status Colours (index.html CSS classes)

| Status | Badge Class | Colour | Meaning |
|--------|-------------|--------|---------|
| MATCH | `.status-match` | Green (#28a745) | Within ±5% variance |
| FLAG | `.status-flag` | Red (#cc0000) | Exceeds ±5% — requires CA review |
| NEW | `.status-new` | Blue (#007bff) | Contractor claims item not in CA report |
| MISSING | `.status-match` (grey tone) | Grey | In CA report, absent from Contractor |

## Summary Chips

Shown above the table after analysis completes:

- ✅ N Matches — green chip
- 🔴 N Flags — red chip
- 🆕 N New — blue chip
- ❓ N Missing — grey chip
- ⏱ Ns — neutral chip (processing time)

## Value Formatting

- Numeric values: 2 decimal places + unit (e.g. "4.00 man-hours")
- Missing values: em dash "—"
- Variance: 1 decimal place + "%" (e.g. "12.5%")

## Loading State

Button text changes to "Analyzing…" and is disabled during processing.
Status bar shows: "Extracting data with Claude AI… (10–20 seconds)"

## Error State

Status bar shows red background with error message from API.
Button re-enabled so user can retry.
