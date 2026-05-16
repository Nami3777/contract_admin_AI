# Builder Stack Narrative

This project is a proof bundle for AI Product Builder roles. It shows how I use modern builder tools to move from workflow pain to visible product proof.

## Stack

| Tool | Role In This Project | Product Signal |
|---|---|---|
| Cursor | Fast codebase navigation, documentation restructuring, implementation planning | I can work inside a real repo and ship changes quickly. |
| n8n | Workflow orchestration around AI extraction, deterministic validation, and human review | I understand where AI belongs in a workflow and where it does not. |
| Vercel | Static portfolio/demo visibility | Recruiters and hiring managers can inspect the product without setup. |
| PostHog | Product analytics plan for pilot instrumentation | I can define behavior metrics, funnels, and product questions. |
| Claude / LLM | Structured extraction from messy DWR documents | I can apply AI to real operational workflows. |
| Python / FastAPI / Pydantic | Local API, validation, deterministic reconciliation | I can build beyond prompt demos. |

## Product Judgment

I considered making the workflow fully agentic. I rejected that because contract reconciliation affects payments, compliance, and auditability.

The product boundary is:

- AI extracts messy document data.
- Deterministic logic calculates financial variance.
- Human reviewers approve exceptions.
- Analytics measure workflow friction and trust.

## Defense / UAV Transfer

The same stack transfers to UAV and defense operations:

- n8n can orchestrate flight-test readiness workflows.
- PostHog can measure blocker resolution, readiness completion, and handoff failures.
- Cursor can accelerate internal tooling prototypes.
- Vercel can make prototypes visible to team leads and hiring managers.
- Eval thinking supports reliability, failure cases, and trust boundaries.

Defense/UAV positioning:

> I use AI and workflow orchestration to make operational systems more reliable, with clear boundaries between automation, deterministic checks, and human approval.
