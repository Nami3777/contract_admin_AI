# Project Configuration

## Candidate

**Name**: Namyun Kim ("Nami")
**Role being targeted**: AI Engineer / AI Implementation Consultant / Digital Transformation Consultant
**Career destination (2–3 yr)**: GRC Specialist (Governance, Risk & Compliance) with workflow optimization lens

## Visa Constraints (non-negotiable)

| Deadline | Action Required |
|---|---|
| **Sep–Oct 2026** | Blue Card (Germany) application submitted — role must be secured before this |
| **Jun–Jul 2026** | Ireland CSEP signed offer needed (Track B, parallel) |
| **Mar 2027** | German work visa expires — hard stop |

Salary floor: **€65,000** (non-negotiable). Target: €70,000–€80,000.

## Why This Project Exists

Portfolio proof for job applications. The tool demonstrates:
1. Domain expertise (construction contract administration, EGIS background)
2. Technical execution (FastAPI + Claude API + Pydantic V2 + PyMuPDF)
3. Product ownership (user research → build → deploy, solo)
4. EU AI Act alignment (audit trails, deterministic math in Layer 3, GDPR-compatible)

## Tech Stack

| Layer | Technology | Why |
|---|---|---|
| PDF parsing | PyMuPDF (fitz) | Fast, no cloud dependency, already proven |
| LLM extraction | Claude claude-haiku-4-5-20251001 | Structured output via tool use, fast, cheap |
| Data validation | Pydantic V2 | Schema enforcement, retry on failure |
| API server | FastAPI + Uvicorn | Async, Python-native, Railway-compatible |
| Frontend | Vanilla HTML/CSS/JS | No build step, instant deploy on GitHub Pages |
| Deployment | Railway (backend) + GitHub Pages (frontend) | Free tiers, fast setup |

## ICM Methodology Note

This workspace practices Van Clief & McDermott's Interpretable Context Methodology (arXiv:2603.16021).
Each pipeline stage has its own `CONTEXT.md` that defines inputs, process, and outputs.
New stages or features: create a new numbered folder under `workspace/stages/` before writing code.

## Metrics (source of truth — do not change without re-testing)

- **85% time reduction**: 2 hours → 18 minutes per contract pair
- **95% extraction accuracy** (NLP clause extraction)
- Do not use other figures in any application material
