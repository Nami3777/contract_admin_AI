# Extraction Rules — Stage 02

These rules resolve ambiguous cases during LLM extraction.

## Equipment Name Assembly

Equipment names fragment across lines in the source PDF. Always join:
- "94 INTL" + "4900" + "TANDEM" + "CRASH" → `"94 INTL 4900 TANDEM CRASH"`
- "10 CAT 420" + "BACKHOE" → `"10 CAT 420 BACKHOE"`
- The leading number (10, 12, 15, 94) is the **asset number** — part of the name, not a count

## Reconciled Values

- CA (Inspector) reports often contain reconciled values alongside raw values
- Contractor reports usually do NOT have reconciled values
- If absent → set all `reconciled_*` fields to `null`

## Null vs Zero

- `null` = value was not present in the document
- `0.0` = value was explicitly stated as zero
- Never infer; only extract

## Skip These Items

- "Material Supplied by Contractor" — this is a section heading, not a material entry
- Column header words ("Type", "Units", "Status") standing alone — not data rows
- "T&M" appearing as a standalone entry — it is a status, not a classification

## Change Order Extraction

- Target pattern: `2020-4091-CO-21` or just `CO-21`
- Extract only the CO portion: `"CO-21"`
- "Linked Change Order (Only if Applicable)" is the field label — extract the value after it

## Accuracy Constraints

- Do not calculate: if total_man_hours is not explicitly stated, do not compute from number × hours_each
- Do not interpolate: missing equipment hours → null, not zero
- Do not deduplicate: if the same classification appears twice, include both entries
