# n8n Workflow - Contract Admin AI

Workflow name: `Contract Admin AI: Extract -> Reconcile -> Human Review`

This workflow demonstrates how the Contract Administration AI pipeline can be orchestrated in n8n. It does not replace the local FastAPI pipeline. It models the product boundary between AI extraction, deterministic workflow logic, and human review.

> I used n8n to model the boundary between AI extraction, deterministic workflow logic, and human review.

## Status

Current status: workflow blueprint prepared for n8n Cloud.  
Next manual step: import or rebuild the workflow in n8n Cloud, run it with anonymized fixture data, and add screenshots.

Screenshot checklist:

- `assets/n8n_workflow_canvas.png` - full workflow canvas.
- `assets/n8n_variance_code_node.png` - deterministic variance Code node.
- `assets/n8n_execution_summary.png` - execution result / human-review summary.

## Workflow Purpose

The product question is not "Can AI automate contract reconciliation end to end?"

The better question is:

> Which parts should be AI, which parts should be deterministic, and where should human judgment remain?

The workflow answer:

- AI extracts structured DWR line items from messy PDFs.
- Deterministic workflow logic calculates variance and status labels.
- Human review handles financial/compliance-sensitive exceptions.

## Node-By-Node Design

| Node | Purpose | Product Reasoning |
|---|---|---|
| Manual Trigger | Starts the demo workflow | Keeps the public demo controlled and repeatable. |
| Set Fixture DWR Data | Loads anonymized CA and contractor line items | Avoids exposing private PDFs while preserving realistic reconciliation logic. |
| Deterministic Variance Check | Calculates variance and status labels | Financial reconciliation must be reproducible; LLMs should not perform approval math. |
| Needs Human Review? | Routes `FLAG`, `NEW`, and `MISSING` items | Exceptions require human judgment and auditability. |
| Human Review Summary | Creates review-ready summary | Shows what a contract administrator needs to inspect next. |
| Ready Report Summary | Creates clean completion summary for matches | Separates low-risk matches from review-required items. |

## Fixture Scenario

The workflow uses anonymized DWR-style fixture data:

- `Foreman`: match within threshold.
- `Skilled Labourer`: >5% variance, requires review.
- `Backhoe`: present in CA report, missing from contractor report.
- `Cold Patch`: present in contractor report, missing from CA report.

This covers the important routing cases: `MATCH`, `FLAG`, `MISSING`, and `NEW`.

## Deterministic Variance Logic

The workflow applies the same product principle as the FastAPI implementation:

> AI extracts. Deterministic logic calculates. Humans approve exceptions.

Business rule:

- If both values exist and variance is <= 5%, status is `MATCH`.
- If both values exist and variance is > 5%, status is `FLAG`.
- If only CA value exists, status is `MISSING`.
- If only contractor value exists, status is `NEW`.
- `FLAG`, `MISSING`, and `NEW` route to human review.

## What Should Not Be Agentic

The workflow intentionally avoids agentic approval of payment-impacting differences.

Not agentic:

- variance calculation
- status labeling
- payment/compliance approval
- final decision on ambiguous quantities

Potentially agentic later:

- summarizing review notes
- suggesting likely causes of discrepancy
- drafting follow-up questions
- grouping similar discrepancies across batches

## Why This Matters For n8n

This maps directly to n8n's AI Product Builder problem space:

- deterministic workflows
- AI output inspection
- human-in-the-loop routing
- workflow observability
- trust boundaries around AI behavior

The key product judgment:

> Not everything should be automated. The valuable product decision is deciding what belongs to AI, what belongs to workflow logic, and what belongs to a human reviewer.
