# Project Configuration — Public

## Project

**Name**: DWR Contract Reconciliation Platform
**Purpose**: Automate comparison of contractor and inspector Daily Work Records for Ontario MTO construction contracts.

## Canonical Metrics

| Metric | Value | Source |
|---|---|---|
| Time reduction | 85% (2 hours → 18 minutes per pair) | Measured against manual baseline |
| Extraction accuracy | 95% | NLP clause extraction validation |

Do not use other figures in any application or documentation material.

## Tech Stack

| Layer | Technology | Reason |
|---|---|---|
| PDF parsing | PyMuPDF (fitz) | Fast, no cloud dependency |
| LLM extraction | Claude claude-haiku-4-5-20251001 | Structured output via tool use |
| Data validation | Pydantic V2 | Schema enforcement, retry logic |
| API server | FastAPI + Uvicorn | Async, Python-native |
| Frontend | Vanilla HTML/CSS/JS | No build step, GitHub Pages compatible |
| Deployment | Railway (backend) + GitHub Pages (frontend) | Free tiers |

## ICM Methodology

This workspace applies Van Clief & McDermott's Interpretable Context Methodology (arXiv:2603.16021).
New pipeline stages: create `workspace/stages/NN-name/` with `CONTEXT.md` before writing any code.

## Design Principles

1. AI extracts — Python calculates. Never use LLM for financial math.
2. No user data is stored. Uploaded PDFs are deleted after processing.
3. Audit trail maintained in structured output (timestamps, model version, source type).
4. EU AI Act compatible: deterministic Layer 3, human-verifiable outputs.

## Private Config

Candidate-specific details (role targets, compensation, visa timeline) are in
`workspace/_config/project.local.md` — gitignored, never committed.
