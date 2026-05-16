# PostHog Metrics Plan - Contract Admin AI

This plan defines product analytics for a future pilot. The current project is not production-deployed and does not yet collect live usage analytics.

Goal:

> Measure whether the tool reduces contract review friction, where users drop off, and when AI outputs require human judgment.

## Event Schema

| Event | When It Fires | Key Properties |
|---|---|---|
| `document_pair_uploaded` | User uploads CA and contractor PDFs | `file_count`, `file_size_bucket`, `source_type`, `session_id` |
| `extraction_started` | PDF text extraction / AI extraction begins | `change_order`, `model_version`, `parser_strategy` |
| `extraction_completed` | Structured extraction finishes | `duration_seconds`, `schema_valid`, `missing_field_count`, `line_item_count` |
| `reconciliation_completed` | Deterministic variance logic finishes | `matches`, `flags`, `new_items`, `missing_items`, `duration_seconds` |
| `human_review_required` | Any item needs review | `review_item_count`, `reason`, `max_variance_pct` |
| `flag_reviewed` | User inspects a flagged discrepancy | `status`, `category`, `variance_pct`, `decision` |
| `report_exported` | User exports or copies review output | `format`, `item_count`, `review_required` |
| `session_completed` | User reaches a review-ready outcome | `total_duration_seconds`, `review_required`, `exported` |
| `processing_failed` | Upload, extraction, validation, or reconciliation fails | `stage`, `error_type`, `recoverable` |

## Funnels

### Funnel 1 - Core Workflow Completion

`document_pair_uploaded` -> `extraction_completed` -> `reconciliation_completed` -> `report_exported`

Product question:

> Where do users drop off before getting a review-ready report?

### Funnel 2 - Human Review Resolution

`human_review_required` -> `flag_reviewed` -> `session_completed`

Product question:

> Are review-required discrepancies being resolved, or do they create dead ends?

## Product Questions

1. Where do users drop off?
2. Which discrepancies trigger the most review?
3. Does the tool reduce end-to-end review time?
4. Which document types fail most often?
5. Do users trust the output enough to export a report?
6. Are humans reviewing the right exceptions, or too many low-risk items?

## Success Metrics For A Pilot

| Metric | Why It Matters |
|---|---|
| Upload-to-report completion rate | Measures basic usability and reliability. |
| Median review-ready time | Measures whether the product delivers the time-saving promise. |
| Human-review trigger rate | Shows how much work remains for contract administrators. |
| Export rate | Proxy for user trust and perceived usefulness. |
| Processing failure rate | Operational reliability signal. |
| Flag review completion rate | Measures whether exception routing is actionable. |

## Implementation Note

For a Vercel/static demo, this can start as a metrics plan. Real PostHog tracking should be added only when the demo has a stable public workflow and safe sample data.

No current claim should say "usage analytics" or "production analytics" until live tracking exists.
