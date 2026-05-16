# Proof Bundle Audit - n8n AI Product Builder

Audit date: 2026-05-17  
Target role: n8n AI Product Builder  
Base project: Contract Admin AI

## Scorecard

| Criterion | Status | Evidence |
|---|---|---|
| Built with AI, not just described it | Pass | FastAPI pipeline uses Claude extraction with Pydantic schema validation. |
| n8n workflow screenshot exists | Pending | Build in n8n Cloud and add screenshots to `assets/`. |
| Workflow shows AI + deterministic + human review boundary | Pass, pending screenshot | `docs/n8n_workflow.md` and blueprint define extraction -> deterministic variance -> review routing. |
| Eval practice documented | Pass | `docs/evals.md` defines metrics, test scenarios, and review triggers. |
| Product analytics/PostHog plan documented | Pass | `docs/posthog_metrics_plan.md` defines events, funnels, dashboards, and pilot questions. |
| Visible demo exists | Pass | README links to YouTube demo and screenshot; Vercel static deploy is still a manual next step. |
| Clear product decisions and tradeoffs | Pass | README includes cloud/local LLM, AI/deterministic boundary, human review, parsing, and metric tradeoffs. |
| No unsafe claims | Pass with monitoring | README uses 85%, 2 hours -> 18 minutes, 95%, and not production-deployed language. |
| Recruiter can understand in 30 seconds | Pass | Project context box, screenshot, demo link, and proof-bundle section. |
| Defense/UAV transfer statement exists | Pass | `docs/builder_stack.md` maps stack to flight-test readiness and operational reliability. |

## Readiness Score

n8n readiness score: 8 / 10 before real n8n screenshots  
Callback-readiness: Strong after screenshots; Medium-Strong before screenshots

## Remaining Gaps

1. Create the actual n8n Cloud workflow and add screenshots.
2. Deploy the static portfolio page on Vercel or add the Vercel URL after deployment.
3. Add live PostHog tracking in a future iteration if the demo becomes stable and public.

## Final Hiring-Manager Signal

This proof bundle should communicate:

> I can build with AI, orchestrate trust-sensitive workflows, separate AI from deterministic logic, design evals, define product analytics, and explain why human review still matters.
