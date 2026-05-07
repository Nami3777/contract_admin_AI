# Study Guide — What This Project Is and Why

*A self-contained reference for understanding the objective, methodology, and structure.*

---

## 1. The Situation

You are a single parent with 3 teenagers living in Munich on a German work visa that expires **March 2027**. To stay, you need a job that qualifies for an EU Blue Card — filed by **September–October 2026** at the latest. That gives roughly **4–5 months** to secure a qualifying offer.

Your current role (Robot Operation Tester, Agile Robots SE) is a strategic stepping stone — paid observation of operational failure patterns — not a long-term career.

Your career destination is **GRC Specialist** (Governance, Risk & Compliance) with a workflow optimization lens, positioned in industrial automation and AI compliance. The path there is through PM / AI Implementation Consultant roles at established multinationals — companies with Blue Card sponsorship infrastructure (Accenture, SAP, Deloitte, Samsung SDS, Siemens).

Salary floor: **€65,000** (non-negotiable — below this, the Blue Card doesn't work).

---

## 2. The Strategy

The core problem was not skills — it was visibility. You have a working AI tool that eliminates 85% of manual contract reconciliation work. But it lived in a GitHub repo that no hiring manager would ever find or interact with.

The plan: **turn the tool into something live at a real URL, and use it as proof of execution** rather than a resume line item.

Van Clief's framework (repurposed metaphorically for career strategy) supports this:
- **Portable proof**: If it's not publicly accessible, it doesn't exist
- **Demonstrated execution**: Link to the tool, not a resume
- **Specific targeting**: 20 personalized outreach messages > 200 ATS applications

### Two-Track Structure

| Track | Target | Deadline | Mechanism |
|---|---|---|---|
| **A (Primary)** | Germany — Munich-adjacent role | Sep–Oct 2026 | EU Blue Card (€43,800 STEM minimum) |
| **B (Backup)** | Ireland — Dublin/Galway | Jun–Jul 2026 signed offer | Irish CSEP permit (€40,904 critical skills minimum) |

Your €70–80K target clears both thresholds with room to spare.

---

## 3. What Van Clief Actually Teaches

This is important to understand clearly: **Van Clief's "folder theory" is a technical AI architecture methodology, not a career framework.**

His published work (arXiv:2603.16021, March 2026) describes the **Interpretable Context Methodology (ICM)** — using filesystem folder structure to replace AI agent orchestration frameworks. Instead of complex agent code, you use numbered folders and plain markdown files to route a single AI through sequential tasks.

**What the executive summary you shared calls "folder theory for careers" is your own reinterpretation** — a creative metaphor that has independent merit, but Van Clief himself teaches AI systems design.

His real value to this project: **the ICM structure is exactly how we organized the pipeline stages** in `workspace/stages/`. That is genuine application of his methodology.

---

## 4. The ICM Workspace — How Van Clief's Method Is Applied Here

### The Core Idea

Instead of writing complex orchestration code, you define each pipeline stage as a folder with a `CONTEXT.md` file. The markdown file tells the AI (or the human reading it) exactly:
- What inputs this stage receives and from where
- What steps to execute
- What outputs it produces and where they go

"One stage, one job. Plain text as the interface."

### The Structure

```
workspace/
├── CONTEXT.md                    ← Read this first. Routes you to the right stage.
├── _config/
│   └── project.md                ← Project metadata: candidate profile, visa deadlines, metrics
├── skills/
│   └── construction_domain.md    ← Domain knowledge: DWR structure, FIDIC, MTO rules, EU AI Act
└── stages/
    ├── 01-ingest/
    │   ├── CONTEXT.md            ← "Job: extract text from PDF. No interpretation."
    │   └── references/
    │       └── dwr_structure.md  ← What MTO DWR documents look like
    ├── 02-extract/
    │   ├── CONTEXT.md            ← "Job: extract structured DWRReport using Claude API."
    │   └── references/
    │       ├── schema.md         ← Pydantic schema documentation
    │       └── extraction_rules.md ← How to handle edge cases (multi-line equipment names, etc.)
    ├── 03-reconcile/
    │   ├── CONTEXT.md            ← "Job: pure Python variance math. No AI."
    │   └── references/
    │       └── variance_rules.md ← ±5% threshold, MATCH/FLAG/NEW/MISSING logic
    └── 04-report/
        ├── CONTEXT.md            ← "Job: format results as JSON + render in browser."
        └── references/
            └── display_format.md ← Status colours, chip format, loading state
```

### The CONTEXT.md Format (Three Parts)

Every `CONTEXT.md` follows this exact structure:

```markdown
# Stage NN — Name: Input → Output

**Job**: One sentence. What this stage does and nothing else.

## Inputs
| Source | File/Location | Section/Scope | Why |

## Process
1. Step one (sequential, explicit)
2. Step two

## Outputs
| Artifact | Location | Format |

## Implementation
path/to/file.py → function_name()
```

### Rule for New Stages

**Write the `CONTEXT.md` before writing any code.** This forces you to think through inputs and outputs before implementation — a discipline that prevents scope creep and keeps stages decoupled.

---

## 5. The Code — What Was Built

### Architecture Overview

```
contract_admin_AI/
├── api/                          ← New: FastAPI backend (built 2026-05-06)
│   ├── main.py                   ← HTTP server: serves index.html, POST /api/reconcile
│   ├── extractor.py              ← Claude API extraction (replaces Ollama/Llama 3.2)
│   └── pipeline.py               ← Orchestrates stages 1→2→3
├── demo/                         ← Original: local Python scripts (unchanged)
│   ├── schemas.py                ← Pydantic V2 data models (shared with api/)
│   ├── extract.py                ← Original Ollama version (reference only)
│   └── reconcile.py              ← Alternative markdown-based reconciliation engine
├── workspace/                    ← New: ICM methodology structure
├── index.html                    ← Updated: added live demo upload section
├── Procfile                      ← New: Railway deployment config
├── requirements.txt              ← Updated: anthropic, fastapi, uvicorn, PyMuPDF
└── .env.example                  ← New: ANTHROPIC_API_KEY placeholder
```

### The Pipeline (How Data Flows)

```
User uploads 2 PDFs
        ↓
POST /api/reconcile (api/main.py)
        ↓
Stage 01: pdf_to_text() — PyMuPDF extracts raw text from both PDFs
        ↓
Stage 02: extract_dwr_with_claude() — runs concurrently for both PDFs
         Claude claude-haiku-4-5 + tool_use API → DWRReport (Pydantic validated)
        ↓
Stage 03: reconcile_reports() — pure Python, no AI
         Matches items by normalized name, calculates ±5% variance
         → List of {category, description, ca_value, contractor_value, variance_pct, status}
        ↓
Stage 04: JSON response assembled, returned to browser
         index.html renderResults() → colour-coded table displayed
```

### The Critical Design Decision

> **AI extracts. Python calculates.**

The LLM (Claude) only handles the hard problem: reading unstructured PDF text and outputting structured data. All financial math — variance percentages, threshold comparisons, status assignments — is pure Python. This is:
- Audit-compliant (deterministic, reproducible)
- EU AI Act compatible (human-verifiable Layer 3)
- Debuggable (if numbers are wrong, it's a math error, not a hallucination)

### Key Files Explained

**`api/extractor.py`**
- Sends the DWR text + extraction prompt to Claude
- Uses `tool_use` API with `DWRReport.model_json_schema()` as the schema
- Forces Claude to return exactly the structure Pydantic expects
- 3 retries on validation failure

**`api/pipeline.py`**
- `pdf_to_text()`: opens PDF, iterates pages, concatenates text with `## Page N` headers
- `reconcile_reports()`: the pure-Python variance engine (copied logic from `demo/extract.py`)
- `run_pipeline()`: async orchestrator — awaits both Claude extractions concurrently, then reconciles

**`api/main.py`**
- `POST /api/reconcile`: accepts two UploadFile objects, saves to temp files, runs pipeline, returns JSON
- `GET /`: serves `index.html`
- `GET /health`: returns `{"status":"ok","api_key_set":true}`

**`index.html`** (the live demo section added)
- Drag-and-drop upload zones for two PDFs
- `runAnalysis()` function: builds FormData, POSTs to `/api/reconcile`, renders results
- `renderResults()` function: populates summary chips and table rows from JSON response

---

## 6. Metrics — The Only Numbers That Count

From `your_background.md` (source of truth):

| Metric | Value | What it means |
|---|---|---|
| Time reduction | **85%** | 2 hours → 18 minutes per contract pair |
| Extraction accuracy | **95%** | NLP clause extraction accuracy |

Do not use other figures in any application material. These come from the background document.

---

## 7. The 30-Day Roadmap

| Week | Goal | Key Deliverable |
|---|---|---|
| Week 1 (May 6–12) | Ship the minimum | Live URL at railway.app — visitors can upload PDFs |
| Week 2 (May 13–19) | Make it look real | Sample PDFs, polished UI, case study README |
| Week 3 (May 20–26) | Visibility infrastructure | LinkedIn overhaul, GitHub profile README, LinkedIn post |
| Week 4 (May 27–Jun 5) | Outreach | 20 personalized messages to hiring managers at real targets |

### Real Targets (confirmed active hiring)

- **Samsung SDS Europe** (Eschborn, near Frankfurt) — AI Use Case Consultant posted Jan 2026
- **Hyundai AutoEver Europe** (Offenbach/Frankfurt) — IT/digital roles
- **Deloitte/PwC Brussels** — EU AI Act advisory practices (August 2026 compliance deadline = peak demand)
- **Accenture Industry X, Capgemini Engineering** — digital transformation in industrial/manufacturing

### The Cold Outreach Template

```
Hi [Name],

I saw [Company] is expanding AI use cases in EU operations.

I built a tool that reconciles contractor vs. inspector contract records using AI,
cutting the process from 2 hours to 18 minutes. Live demo: [URL]

I'm trilingual (Korean/English/German) and have a background in infrastructure
project management — rare combination in AI.

20-min call?
```

Rule: **link the tool, don't attach a resume.**

---

## 8. What's Next (Immediate)

Before anything else, two actions required:

1. **Push to GitHub**: `git push origin main` (2 commits pending: API backend + ICM workspace)
2. **Anthropic API key**: create at console.anthropic.com if you don't have one

Then deploy to Railway (15-minute task once the key is in hand).
