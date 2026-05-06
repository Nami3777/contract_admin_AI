# Workspace: DWR Contract Reconciliation Pipeline

**Protocol**: Interpretable Context Methodology (Van Clief & McDermott, 2026)
**Principle**: One stage, one job. Plain text as the interface. Load only what you need.

---

## What This Workspace Does

Automates comparison of contractor and inspector Daily Work Records (DWRs) for Ontario MTO construction contracts. Two PDF inputs → structured reconciliation report with variance flags in ~15 seconds.

**Business impact**: 85% time reduction (2 hours → 18 minutes per contract pair). 95% extraction accuracy.

---

## Stage Routing

| Stage | Folder | Job | Implementation |
|-------|--------|-----|----------------|
| 1 | `stages/01-ingest/` | PDF → plain text | `api/pipeline.py → pdf_to_text()` |
| 2 | `stages/02-extract/` | Text → structured `DWRReport` | `api/extractor.py → extract_dwr_with_claude()` |
| 3 | `stages/03-reconcile/` | Two `DWRReport` → reconciliation list | `api/pipeline.py → reconcile_reports()` |
| 4 | `stages/04-report/` | Reconciliation list → JSON response | `api/main.py → /api/reconcile` |

---

## Supporting Resources

| Resource | Location | Purpose |
|----------|----------|---------|
| Project config | `_config/project.md` | Candidate context, visa deadlines, tech decisions |
| Domain knowledge | `skills/construction_domain.md` | DWR structure, FIDIC/MTO rules, terminology |

---

## Rules for This Workspace

1. Each stage reads only from its own `references/` and the previous stage's `output/`
2. Stages do not call each other — the API layer (`api/main.py`) orchestrates
3. AI handles extraction (Stage 2); Python handles math (Stage 3). Never swap these.
4. All changes to a stage's logic must update its `CONTEXT.md` first
