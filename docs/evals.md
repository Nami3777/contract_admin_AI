# Eval Plan - Contract Admin AI

This eval plan defines how to measure whether the Contract Admin AI system is reliable enough for contract-administrator review.

Important distinction:

> AI system evals measure extraction quality. Deterministic tests measure reconciliation correctness.

## Eval Goals

1. Verify that AI extraction returns valid structured data.
2. Detect missing, hallucinated, or incorrectly parsed fields.
3. Confirm deterministic reconciliation logic produces correct `MATCH`, `FLAG`, `NEW`, and `MISSING` statuses.
4. Identify when human review must be triggered.
5. Measure latency and failure modes before any pilot.

## Metrics

| Metric | What It Measures | Target / Interpretation |
|---|---|---|
| Schema validity rate | Percentage of AI outputs that validate against Pydantic schema | High schema validity means extraction output is machine-usable. |
| Field extraction accuracy | Correct extraction of date, change order, labour, equipment, material, quantities, units | Core AI quality metric. |
| Missing field rate | Required fields absent from extraction | Higher rate means human review or parser fallback needed. |
| Hallucinated field rate | AI returns values not present in source document | Critical trust/safety risk. |
| Variance calculation correctness | Python/n8n logic applies +/-5% rule correctly | Must be deterministic and near 100% for test fixtures. |
| Human-review trigger rate | Percentage of items routed to review | Helps measure how much work remains for humans. |
| Latency per document pair | Time from upload to review-ready report | Product metric tied to workflow value. |
| Processing failure rate | Failed PDF parsing, extraction, validation, or reconciliation | Operational reliability signal. |

## Test Scenarios

| Scenario | Expected Result | Eval Type |
|---|---|---|
| Clean matching DWR pair | All comparable line items return `MATCH` | Deterministic reconciliation test |
| >5% quantity variance | Item returns `FLAG` and routes to human review | Business rule test |
| Date mismatch | Human review required | Workflow safety test |
| Missing contractor item | Item returns `MISSING` | Reconciliation coverage test |
| Missing inspector/CA item | Item returns `NEW` | Reconciliation coverage test |
| Degraded PDF/table layout issue | Extraction failure or low-confidence review path | AI extraction robustness test |

## Human-Review Triggers

The system should require human review when:

- variance is greater than 5%
- an item is `NEW` or `MISSING`
- change order numbers do not match
- work dates do not match
- required fields are missing
- schema validation fails
- source text is too degraded for reliable extraction
- AI output contains values not traceable to the source document

## Eval Dataset

Use anonymized DWR-style fixture data, not private project PDFs.

Minimum fixture set:

1. `clean_match_pair`
2. `variance_flag_pair`
3. `missing_contractor_item_pair`
4. `new_contractor_item_pair`
5. `date_mismatch_pair`
6. `degraded_layout_pair`

## Why This Matters

For contract reconciliation, the product risk is not only "wrong extraction." It is a user trusting an AI output that should have been reviewed.

The eval strategy therefore separates AI extraction quality, deterministic variance correctness, human-review routing quality, and product workflow latency.
