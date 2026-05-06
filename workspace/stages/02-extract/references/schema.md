# DWRReport Pydantic Schema Reference

Source: `demo/schemas.py`

## Top-Level Structure

```
DWRReport
├── header: DWRHeader          (required)
├── weather: WeatherRecord     (optional)
├── labour: List[LabourLineItem]
├── equipment: List[EquipmentLineItem]
├── materials: List[MaterialLineItem]
└── comments: List[DWRComment]
```

## DWRHeader Fields

| Field | Type | Required | Notes |
|---|---|---|---|
| contract_no | str | yes | e.g. "2020-4091" |
| record_id | str | yes | e.g. "2020-4091-DWR-7" |
| contractor | str | yes | Company name |
| created_by | str | yes | Person's name |
| dwr_date | str | yes | "DD-Mon-YY" format |
| from_time | str | yes | "HH:MM" 24hr |
| to_time | str | yes | "HH:MM" 24hr |
| status | str | default "Draft" | Draft/Reviewed/T&M |
| change_order | str | optional | "CO-21" format |
| highway | str | optional | Highway number |
| region | str | optional | Region name |

## LabourLineItem Fields

| Field | Type | Constraints | Notes |
|---|---|---|---|
| classification | str | min_length=1 | "Foreman", "Skilled Labourer", etc. |
| number | int | ge=0 | Worker count |
| hours_each | float | ge=0, le=24 | Hours per worker |
| total_man_hours | float | ge=0, le=100 | number × hours_each |
| reconciled_* | optional | null if absent | CA-adjusted values |

## EquipmentLineItem Fields

| Field | Type | Constraints |
|---|---|---|
| equipment_name | str | min_length=1 |
| hours_worked | float | ge=0, le=24 |
| hours_standby | float | default 0.0 |
| down_time | float | default 0.0 |
| operator_included | bool | optional |

## MaterialLineItem Fields

| Field | Type | Notes |
|---|---|---|
| material | str | Category name |
| material_description | str | optional, detailed desc |
| units | str | optional: EA, m, tonne, m2 |
| quantity | float | optional |
