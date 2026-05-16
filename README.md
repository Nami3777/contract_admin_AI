# Contract Administration AI Pipeline

AI-powered workflow tool for construction contract administration. The system compares contractor Daily Work Reports against inspector records, extracts structured line items from PDFs, flags quantity discrepancies, and returns an audit-ready reconciliation report for human review.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111+-green.svg)](https://fastapi.tiangolo.com/)
[![Pydantic V2](https://img.shields.io/badge/pydantic-v2-green.svg)](https://docs.pydantic.dev/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

▶ [Watch demo on YouTube](https://youtu.be/0F9RK8QCOik)

---

## Project Context

| Item | Details |
|---|---|
| Role | Solo product builder, business analyst, and AI implementation lead |
| Domain | Construction contract administration, Daily Work Report reconciliation |
| Users | Contract Administrators, Project Managers, Field Inspectors |
| Timeline | Independent build over 6 months |
| Scope | User research, workflow mapping, requirements, PDF ingestion, LLM extraction, deterministic reconciliation, REST API, demo UI |
| Tools | Python, FastAPI, PyMuPDF, Pydantic V2, Claude Haiku (Anthropic API), SQLite |
| Constraint | Sensitive construction documents, inconsistent PDF layouts, auditability requirements, no production deployment |
| Outcome | 85% processing-time reduction (2 hours → 18 minutes per contract workflow); 95% extraction accuracy |
| Status | Built and pilot-ready; not production-deployed |

---

## Problem

Construction contract administrators spend significant time reconciling contractor Daily Work Reports against inspector records, especially for change-order work where payment depends on accurate quantity validation.

The problem is not only document extraction. The real workflow problem is delayed verification: by the time discrepancies are found, crews may have moved, memories fade, and payment disputes become harder to resolve.

From field observation and user research, the highest-value target was change-order reconciliation because it combines high manual effort, high payment sensitivity, and strong audit requirements.

Ontario MTO requires ±5% variance threshold enforcement and complete audit trails for all Time & Materials claims. Manual processes miss discrepancies and create compliance risk.

---

## Product Decisions

### 1. Cloud LLM vs. local LLM

I initially prototyped with Ollama/Llama 3.2 locally for privacy. The constraint was accuracy: local models struggled with the inconsistent table structures in real DWR PDFs. I switched to Claude Haiku via the Anthropic API, and handled privacy through a no-persistence architecture — uploaded PDFs are processed in memory and deleted immediately after each request, with no storage or logging.

### 2. AI reconciliation vs. deterministic reconciliation

I considered letting the LLM both extract and compare quantities. I rejected that approach because financial reconciliation must be reproducible. The final design uses AI for unstructured-to-structured extraction, then deterministic Python logic for variance calculation and status labels. Same inputs always produce the same output.

### 3. Full automation vs. human review

I considered a fully automated approval flow. The constraint was compliance risk: ambiguous quantities, date mismatches, and missing line items still need human judgment. The system returns flagged discrepancies to the contract administrator for review, not an automated decision.

### 4. Direct PDF parsing vs. layered ingestion

I tested Docling for preserving table structures and PyMuPDF as the fallback for difficult layouts. Real construction PDFs vary heavily in format, quality, and column layout. A layered ingestion design ensures one parser failing does not break the entire workflow.

### 5. Technical latency vs. workflow time as success metric

I considered using per-call LLM latency as the primary metric. I chose end-to-end workflow time instead because the user does not care how fast one API call runs; they care how long the full reconciliation process takes from document intake to review-ready output.

---

## What I Built

Four-stage pipeline:

```
PDF pair
  │
  ▼
01-ingest      PyMuPDF extracts plain text, page by page
  │
  ▼
02-extract     Claude Haiku via tool_use → DWRReport (Pydantic V2)
  │              Two reports run concurrently with asyncio.gather
  ▼
03-reconcile   Pure Python: fuzzy name matching, ±5% variance, MATCH/FLAG/NEW/MISSING
  │
  ▼
04-report      JSON response → browser table (color-coded by status)
```

**Rule: AI extracts, Python calculates.** The LLM never touches financial math. Variance logic is deterministic and auditable.

---

## Results

| Metric | Result |
|---|---|
| End-to-end workflow time | Reduced by 85%, from 2 hours to 18 minutes |
| Extraction accuracy | 95% in clause/field extraction and compliance-oriented checks |
| User research | 10+ construction project managers and direct field-observation background |
| Deployment status | Built and pilot-ready; not production-deployed |
| Privacy | PDFs processed in memory, deleted immediately after each request |
| Future work | Persistent audit trail, batch processing, confidence scoring, pilot with anonymized project documents |

---

## Constraints

- Construction PDFs vary by format, quality, table layout, and naming convention.
- Contract and payment documents contain sensitive commercial data.
- Financial reconciliation requires deterministic calculations and auditability.
- Human review remains necessary for ambiguous or low-confidence items.
- The API is built but not deployed due to Claude API usage costs; local setup runs the full pipeline.

---

## Architecture

```
contract_admin_AI/
├── api/
│   ├── main.py          FastAPI app — file validation, temp file lifecycle
│   ├── pipeline.py      Orchestrates ingest → extract → reconcile → response
│   └── extractor.py     Claude API call (tool_use → DWRReport schema)
├── demo/
│   └── schemas.py       Pydantic V2 models (DWRReport, LabourLineItem, ...)
├── workspace/
│   └── stages/          Context files — one folder per pipeline stage
├── index.html           Portfolio page + live demo upload UI
├── requirements.txt
└── render.yaml          Render.com deploy config
```

---

## How to Run

```bash
git clone https://github.com/Nami3777/contract_admin_AI.git
cd contract_admin_AI
pip install -r requirements.txt

# Add your Anthropic API key to .env
echo "ANTHROPIC_API_KEY=sk-ant-your-key-here" > .env

# Start the API server
uvicorn api.main:app --reload
```

Open `http://localhost:8000` — the portfolio page with live upload demo loads.

### API

**`POST /api/reconcile`** — Upload two DWR PDFs; receive a structured reconciliation report.

```bash
curl -X POST http://localhost:8000/api/reconcile \
  -F "ca_pdf=@ca_report.pdf" \
  -F "contractor_pdf=@contractor_report.pdf"
```

**Response:**
```json
{
  "work_date": "2021-08-05",
  "change_order": "CO-21",
  "processing_time_seconds": 11.4,
  "summary": { "total": 7, "matches": 6, "flags": 1, "new": 0, "missing": 0 },
  "items": [
    {
      "category": "LABOUR",
      "description": "Foreman",
      "ca_value": 2.0,
      "contractor_value": 2.0,
      "variance_pct": 0.0,
      "status": "MATCH"
    }
  ]
}
```

Constraints: max 5 MB per file, PDF only. Processing time ~10–20 seconds (two concurrent Claude calls).

---

## Validation and Limitations

I validated the problem through field experience, analysis of DWR reconciliation patterns, and user research with 10+ construction project managers. The current prototype was tested against sample and anonymized DWR-style documents and reconciliation scenarios.

This is not yet production usage validation. The next validation step would be a controlled pilot using anonymized project documents and measuring upload-to-review completion time, discrepancy review rate, and user trust.

Current limitations:
- Accuracy figures are based on test dataset, not live production use.
- The API is not deployed; the demo video shows local execution.
- No persistent audit trail in the current version; review decisions are not stored.
- Edge cases in heavily degraded or non-standard PDF layouts may require manual fallback.

---

## Next Iteration

- Persistent audit trail with SQLite, storing human review decisions alongside extraction results
- Batch processing for full-project reconciliation runs
- Confidence scoring per extracted line item
- Controlled pilot with anonymized documents from a real project

---

## Compliance Design

- **EU AI Act aligned:** deterministic Layer 3, human-verifiable outputs, model version pinned in code
- **MTO OPSS 180:** ±5% variance threshold enforced, audit fields on every response
- **No user data retained:** temp files deleted in `finally` block, even on error

---

## License

MIT — see [LICENSE](LICENSE).

All test data is synthetically generated or anonymized. Provided as-is for portfolio demonstration.

---

*Last updated: May 2026 | Model: claude-haiku-4-5-20251001 | Stack: FastAPI · PyMuPDF · Pydantic V2 · Anthropic SDK*
