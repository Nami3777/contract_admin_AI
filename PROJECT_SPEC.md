# Project: Contract Admin AI — Technical Implementation

## Purpose

Build a working AI document reconciliation pipeline for construction contract administration. This is a real prototype that processes contractor and inspector PDFs, extracts structured data, compares quantities, flags discrepancies, and stores results with audit trails.

The pipeline currently exists as an Agile Robots inspection system (Diana 7 robot reports). We are translating it to the construction domain: Daily Work Report (DWR) reconciliation.

---

## Architecture — 4 Layers

### Layer 1: Ingestion (ingest.py)
- Input: PDF documents (contractor DWRs, inspector DWRs, change orders, information requests)
- Processing: Docling converts PDF → Markdown, preserving table structures
- Fallback: PyMuPDF if Docling fails on complex layouts
- Output: Markdown text ready for LLM extraction

### Layer 2: Extraction (extract.py)
- Input: Markdown text from Layer 1
- Processing: Ollama + Llama 3.2 (local LLM, no cloud)
- Schema: Pydantic V2 models enforce structured output
- Retry: Up to 3 attempts if LLM returns invalid JSON
- Output: Validated structured data (DWRLineItem objects)

### Layer 3: Validation & Reconciliation
- Type check: quantities are numbers, dates valid, fields not empty
- Range check: impossible values flagged (28 hrs/day, negative quantities)
- Logic check: contradictions detected (date mismatches, status conflicts)
- Reconciliation: side-by-side comparison of contractor vs inspector data
- Variance threshold: >5% triggers FLAG, within 5% = MATCH
- Human review: items below 90% confidence escalated to Contract Administrator

### Layer 4: Storage & Audit (SQLite)
- Every extraction stored with timestamps and confidence scores
- Parameterized queries (SQL injection prevention)
- ACID compliant
- Full audit trail: source PDF → AI extraction → validation → human decision → final output

---

## Directory Structure

```
contract-admin-ai/
├── input/                          # Source documents
│   ├── dwrs/                       # Daily Work Reports
│   │   ├── contractor/             # Contractor-submitted DWRs
│   │   └── inspector/              # Inspector DWRs
│   ├── change_orders/              # Change Order documents
│   └── info_requests/              # Information Requests
│
├── output/                         # All pipeline outputs
│   ├── markdown/                   # Intermediate markdown (from ingestion)
│   │   └── {date}_{doc_type}_{id}.md
│   ├── extractions/                # JSON extractions (from LLM)
│   │   └── {date}_{doc_type}_{id}.json
│   ├── reconciliations/            # Reconciliation reports
│   │   └── {change_order}_{date}.json
│   └── reports/                    # Human-readable reports
│       ├── html/                   # HTML reconciliation tables
│       └── csv/                    # CSV exports for Excel
│
├── data/                           # Persistent storage
│   ├── contract_admin.db           # SQLite database
│   └── audit_log.jsonl             # Append-only audit trail
│
├── src/                            # Source code
│   ├── ingest.py                   # Layer 1: PDF → Markdown
│   ├── extract.py                  # Layer 2: Markdown → Structured Data
│   ├── reconcile.py                # Layer 3: Comparison logic
│   ├── storage.py                  # Layer 4: Database operations
│   ├── schemas.py                  # Pydantic models (shared)
│   ├── batch.py                    # Batch processing orchestrator
│   └── view_findings.py            # Query and display results
│
├── tests/                          # Test suite
│   ├── test_pipeline.py            # Integration tests
│   ├── test_extraction.py          # Unit tests for extraction
│   └── fixtures/                   # Test PDFs and expected outputs
│       ├── mock_dwrs/
│       └── expected_outputs/
│
├── config/                         # Configuration
│   ├── settings.yaml               # Runtime settings
│   └── prompts/                    # LLM prompt templates
│       ├── dwr_extraction.txt
│       └── change_order_extraction.txt
│
└── scripts/                        # Utility scripts
    ├── generate_mock_dwr.py        # Generate test data
    └── setup_directories.py        # Initialize directory structure
```

---

## Batch Processing Design

### batch.py — Orchestrator

```python
# Conceptual design for batch processing

class BatchProcessor:
    """Process multiple documents in a single run"""
    
    def __init__(self, config: BatchConfig):
        self.input_dir = config.input_dir
        self.output_dir = config.output_dir
        self.db = DatabaseManager(config.db_path)
        self.batch_id = generate_batch_id()  # e.g., "batch_20250213_143022"
    
    def discover_documents(self) -> List[DocumentPair]:
        """
        Find matching contractor/inspector pairs for reconciliation.
        Matching logic:
        - Same change order number (CO-21, CO-55, etc.)
        - Same or adjacent work dates
        - One from contractor/, one from inspector/
        """
        pass
    
    def process_batch(self, pairs: List[DocumentPair]) -> BatchResult:
        """
        Process all document pairs:
        1. Ingest both PDFs → markdown
        2. Extract structured data from both
        3. Reconcile and calculate variances
        4. Store results with batch_id linkage
        5. Generate reports
        """
        pass
    
    def generate_batch_report(self, results: BatchResult) -> Path:
        """Create summary report for entire batch"""
        pass
```

### Batch Processing Features

1. **Document Discovery**
   - Scan input directories for new PDFs
   - Match contractor/inspector pairs by change order + date
   - Flag orphan documents (no matching pair found)
   - Skip already-processed documents (idempotency)

2. **Parallel Processing** (future enhancement)
   - Process independent document pairs concurrently
   - Respect Ollama's single-model constraint
   - Queue management for large batches

3. **Progress Tracking**
   - Real-time status updates during processing
   - Estimated time remaining
   - Failure isolation (one bad PDF doesn't stop batch)

4. **Batch Reporting**
   - Summary: X documents processed, Y discrepancies found
   - Per-change-order breakdown
   - Export to CSV for Excel review
   - HTML dashboard for quick review

### CLI Interface

```bash
# Process all new documents
python -m src.batch run

# Process specific change order
python -m src.batch run --change-order CO-21

# Dry run (discover pairs without processing)
python -m src.batch discover

# Reprocess specific batch
python -m src.batch reprocess --batch-id batch_20250213_143022

# Generate reports only (no extraction)
python -m src.batch report --format html --output ./reports/
```

---

## Domain: Construction Contract Administration

### Document Types
- **DWR (Daily Work Report):** Submitted by both contractor and inspector for each work day. Contains labor hours, equipment usage, material quantities, work descriptions. These are the primary documents for reconciliation.
- **Change Order:** Modifications to the original contract scope. Contains line items with agreed quantities and rates.
- **Information Request:** Clarifications between contractor, inspector, and Contract Administrator.
- **Reconciliation Report:** Output comparing contractor vs inspector claims per change order.

### Key Fields to Extract
- Change order number (e.g., CO-8)
- Work date
- Submitted by (contractor name or inspector name)
- Labor: role, hours, count
- Equipment: type, hours, count
- Materials: type, quantity, unit (tonnes, m², linear meters)
- Work description / location
- Weather conditions (if present)
- Signatures / approval status

### Reconciliation Logic
- Match line items between contractor and inspector DWRs by category + description
- Calculate variance percentage for each matched pair
- Flag items present in one report but missing from the other (NEW items)
- Flag date mismatches between paired reports
- Aggregate totals by change order

---

## Technical Stack

- **Python 3.10+**
- **Docling** — PDF to Markdown conversion (preserves tables)
- **PyMuPDF (fitz)** — Fallback PDF reader
- **Ollama** — Local LLM inference server
- **Llama 3.2** — Language model for extraction
- **Pydantic V2** — Schema validation and type enforcement
- **SQLite** — Storage with parameterized queries
- **pytest** — Testing framework

---

## Recommendations & Concerns

### High Priority

1. **Document Pairing Strategy**
   - Current: Manual pairing assumed
   - Concern: Real DWRs may have inconsistent naming/dating
   - Recommendation: Build flexible matching with fuzzy date tolerance (±1 day) and confirmation prompts

2. **Extraction Confidence Scoring**
   - Current: Binary pass/fail via Pydantic validation
   - Concern: LLM may extract plausible but incorrect values
   - Recommendation: Add confidence scores per field, flag low-confidence extractions for human review
   - Implementation: Have LLM output confidence alongside values, or use multiple extraction passes

3. **Unit Normalization**
   - Current: Units stored as extracted
   - Concern: "tonnes" vs "t" vs "metric tons" will break matching
   - Recommendation: Unit normalization layer with canonical mappings
   - Example: `{"tonnes": "t", "metric tons": "t", "cubic meters": "m³", "cu m": "m³"}`

4. **Line Item Matching Algorithm**
   - Current: Exact string matching implied
   - Concern: "Backhoe excavation" vs "Excavation - Backhoe" won't match
   - Recommendation: Fuzzy matching with similarity threshold (e.g., 85% Levenshtein)
   - Alternative: LLM-assisted semantic matching for ambiguous cases

### Medium Priority

5. **Audit Trail Completeness**
   - Current: Timestamps and source PDFs tracked
   - Enhancement: Add diff tracking for re-extractions, user decision logging
   - Format: Append-only JSONL for immutable audit log

6. **Error Recovery**
   - Current: Retry logic for LLM failures
   - Enhancement: Checkpoint system for long batches
   - Benefit: Resume from failure point instead of restarting entire batch

7. **Prompt Versioning**
   - Current: Prompts embedded in code
   - Risk: Prompt changes break reproducibility
   - Recommendation: External prompt files with version tracking
   - Store prompt version in extraction records for audit

8. **Multi-Page DWR Handling**
   - Current: Single extraction per document
   - Concern: Multi-page DWRs may have continuation tables
   - Recommendation: Page-aware extraction with table continuation detection

### Lower Priority (Future Enhancements)

9. **Change Order Context**
   - Current: DWRs processed in isolation
   - Enhancement: Load change order approved quantities as reference
   - Benefit: Flag when DWR quantities exceed approved totals

10. **Historical Trend Analysis**
    - Future: Track variance patterns over time per contractor
    - Value: Identify systematic over/under-reporting

11. **Export Integrations**
    - Future: Direct export to contract management systems
    - Consider: API design for integration with provincial systems

---

## Database Schema (Updated for Batch Processing)

```sql
-- Batch tracking
CREATE TABLE batches (
    batch_id TEXT PRIMARY KEY,
    started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    completed_at DATETIME,
    status TEXT CHECK(status IN ('running', 'completed', 'failed', 'partial')),
    documents_processed INTEGER DEFAULT 0,
    documents_failed INTEGER DEFAULT 0,
    config_json TEXT  -- Store batch configuration for reproducibility
);

-- Document ingestion records
CREATE TABLE documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    batch_id TEXT REFERENCES batches(batch_id),
    file_path TEXT NOT NULL,
    file_hash TEXT NOT NULL,  -- SHA256 for deduplication
    document_type TEXT CHECK(document_type IN ('contractor_dwr', 'inspector_dwr', 'change_order', 'info_request')),
    change_order TEXT,  -- e.g., "CO-21"
    work_date DATE,
    ingested_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    markdown_path TEXT,
    status TEXT CHECK(status IN ('ingested', 'extracted', 'reconciled', 'failed'))
);

-- Extracted line items
CREATE TABLE line_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER REFERENCES documents(id),
    category TEXT CHECK(category IN ('labor', 'equipment', 'material')),
    description TEXT NOT NULL,
    quantity REAL,
    unit TEXT,
    hours REAL,  -- For labor/equipment
    count INTEGER,  -- For labor (workers) or equipment (units)
    rate REAL,  -- If available
    extraction_confidence REAL CHECK(extraction_confidence BETWEEN 0 AND 1),
    raw_text TEXT,  -- Original text that was extracted
    extracted_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Reconciliation results
CREATE TABLE reconciliations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    batch_id TEXT REFERENCES batches(batch_id),
    change_order TEXT NOT NULL,
    work_date DATE,
    contractor_doc_id INTEGER REFERENCES documents(id),
    inspector_doc_id INTEGER REFERENCES documents(id),
    reconciled_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    total_items INTEGER,
    matched_items INTEGER,
    flagged_items INTEGER,
    new_items INTEGER,  -- Items in one but not other
    status TEXT CHECK(status IN ('auto_approved', 'needs_review', 'reviewed', 'disputed'))
);

-- Individual line item comparisons
CREATE TABLE reconciliation_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    reconciliation_id INTEGER REFERENCES reconciliations(id),
    contractor_item_id INTEGER REFERENCES line_items(id),
    inspector_item_id INTEGER REFERENCES line_items(id),
    match_status TEXT CHECK(match_status IN ('MATCH', 'FLAG', 'NEW_CONTRACTOR', 'NEW_INSPECTOR')),
    variance_percent REAL,
    contractor_value REAL,
    inspector_value REAL,
    notes TEXT,
    reviewed_by TEXT,  -- For human review tracking
    reviewed_at DATETIME,
    review_decision TEXT CHECK(review_decision IN ('accepted', 'rejected', 'adjusted'))
);

-- Audit log (append-only)
CREATE TABLE audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    event_type TEXT NOT NULL,
    entity_type TEXT,  -- 'document', 'line_item', 'reconciliation', etc.
    entity_id INTEGER,
    user_id TEXT,  -- If applicable
    old_value TEXT,  -- JSON
    new_value TEXT,  -- JSON
    metadata TEXT  -- JSON for additional context
);

-- Indexes for common queries
CREATE INDEX idx_documents_change_order ON documents(change_order);
CREATE INDEX idx_documents_batch ON documents(batch_id);
CREATE INDEX idx_line_items_document ON line_items(document_id);
CREATE INDEX idx_reconciliations_change_order ON reconciliations(change_order);
CREATE INDEX idx_audit_log_entity ON audit_log(entity_type, entity_id);
```

---

## Current Codebase (Agile Robots → To Be Translated)

### Files being translated:
- `ingest_v2.py` → `src/ingest.py` — Change Diana 7 report handling to construction DWR handling
- `extract_v2.py` → `src/extract.py` — Change robot inspection schema to DWR line item schema
- `test_pipeline.py` → `tests/test_pipeline.py` — Update test cases for construction data
- `view_findings.py` → `src/view_findings.py` — Update display for reconciliation comparison
- `generate_mock_pdf.py` → `scripts/generate_mock_dwr.py` — Generate realistic construction DWR test data

### New files to create:
- `src/schemas.py` — Shared Pydantic models for DWR data structures
- `src/reconcile.py` — Comparison and variance calculation logic
- `src/storage.py` — Database operations (extracted from extract.py)
- `src/batch.py` — Batch processing orchestrator
- `scripts/setup_directories.py` — Initialize project directory structure
- `config/settings.yaml` — Runtime configuration

### What stays the same:
- Docling + PyMuPDF fallback pattern
- Ollama integration and retry logic
- Pydantic validation approach
- SQLite storage with audit trails
- Pipeline orchestration pattern

### What changes:
- Pydantic schemas (robot findings → DWR line items)
- Extraction prompts (robot inspection → construction quantities)
- Validation rules (construction-specific ranges and logic)
- Mock data (robot reports → contractor/inspector DWRs)
- Reconciliation logic (new — comparing two documents side by side)
- View output (findings table → reconciliation comparison)

---

## Anonymization Rules

All real information must be anonymized in any output, demo, or public-facing code:
- Person names → first + last letter with special characters (e.g., D***n O'H**a)
- Company names → same pattern
- Document/contract numbers → partial redaction (e.g., CO-8 → C*-8)
- Addresses and project locations → generalized or redacted
- Keep generic construction terms as-is (Foreman, Backhoe, Cold Patch, etc.)

---

## How to Use This Project

When I upload field reports:
- Analyze the document structure (what fields exist, how tables are formatted)
- Propose Pydantic schemas that capture the data
- Identify extraction challenges (handwritten vs typed, table formats, multi-page)
- Suggest mock data patterns based on real document structure

When working on pipeline code:
- Translate Agile Robots patterns to construction domain
- Maintain the 4-layer architecture
- Keep all code production-quality (error handling, logging, type hints)
- Test with both mock data and real anonymized reports
- Ensure SQLite schema supports reconciliation (two-document comparison)

When generating mock data:
- Use realistic construction quantities and roles
- Include deliberate discrepancies for testing (variance detection)
- Include edge cases: missing items, date mismatches, unit conflicts
- Anonymize all names and identifiers

---

## Success Criteria

The pipeline is "demo-ready" when it can:
1. Accept two PDFs (contractor DWR + inspector DWR) for the same change order
2. Extract structured line items from both
3. Compare and calculate variances
4. Flag discrepancies above 5% threshold
5. Store results with full audit trail
6. Display a reconciliation summary (matching the technical_demo.html table format)
7. Run end-to-end in under 30 seconds on local hardware

### Batch Processing Success Criteria
8. Process multiple document pairs in a single run
9. Handle missing pairs gracefully (orphan detection)
10. Skip already-processed documents (idempotency via file hash)
11. Generate batch summary report
12. Recover from partial failures without data loss

---

## Next Steps (Prioritized)

1. **Create directory structure** — Run setup script to initialize folders
2. **Extract schemas.py** — Define DWR Pydantic models based on real document analysis
3. **Update ingest.py** — Adapt for batch input directory scanning
4. **Update extract.py** — New prompts and schemas for DWR extraction
5. **Build reconcile.py** — Core comparison logic with fuzzy matching
6. **Build batch.py** — Orchestrator tying it all together
7. **Test with real PDFs** — CO-21, CO-55, CO-56 document pairs
8. **Iterate on extraction prompts** — Tune based on real extraction quality
