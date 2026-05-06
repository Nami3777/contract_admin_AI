# DWR Document Structure Reference

**Standard**: Ontario Ministry of Transportation (MTO) Daily Work Record format.

## Section Order (always this sequence)

1. **Header** — Contract No, Record ID, Contractor name, Created by, DWR Date, From/To Time, Status, Change Order
2. **Weather** — Temperature (°C), Wind Speed, Precipitation, Visibility
3. **Labour** — Classification, Number of workers, Hours each, Total man-hours. Repeats per worker type.
4. **Equipment** — Equipment name (may span multiple lines), Owned/Rented, Hours worked, Standby hours, Down time, Operator included
5. **Material Supplied by Contractor** — Category, Description, Units, Quantity, New/Used
6. **Comments** — Free text description of work performed
7. **Change Order** — Linked CO number (e.g. "2020-4091-CO-21")

## Key Parsing Challenges

- Equipment names fragment across lines (e.g. "94 INTL" / "4900" / "TANDEM" / "CRASH" = one item)
- Reconciled values may or may not be present depending on document type (CA vs Contractor)
- "T&M" status appears inline and should not be treated as a line item
- Section headers ("Labour", "Equipment", "Material") are plain text — no special markup

## CA vs Contractor Differences

| Field | CA (Inspector) Report | Contractor Report |
|---|---|---|
| Created by | Inspector name | Contractor rep name |
| Reconciled values | Often present | Usually absent |
| Status | "Draft" or "Reviewed" | "T&M" common |
| Discrepancy direction | Source of truth | May claim more hours/materials |
