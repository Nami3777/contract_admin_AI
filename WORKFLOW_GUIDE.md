# Contract Administration Reconciliation Pipeline
## Complete Workflow Guide

This project implements an automated reconciliation system for construction contract administration, comparing contractor Daily Work Reports (DWRs) against Contract Administrator (CA) records.

---

## Architecture: 4-Layer Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│ Layer 1: Ingestion (PDF → Markdown)                         │
│ ingest_pymupdf.py - PyMuPDF extraction                      │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Layer 2: Extraction (Markdown → Structured Data)            │
│ extract_final.py - Ollama/Llama 3.2 + Pydantic validation  │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Layer 3: Reconciliation (Compare CA vs Contractor)          │
│ Built into extract_final.py - Pure Python logic             │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Layer 4: Storage & Presentation (SQLite + HTML)             │
│ contract_admin.db - Full audit trail                        │
│ view_reconciliation.py - Console display                    │
│ export_demo_html.py - Generate visual demo                  │
└─────────────────────────────────────────────────────────────┘
```

---

## Quick Start

### Prerequisites
```bash
# Required packages
pip install pymupdf ollama pydantic

# Start Ollama service (if not running)
ollama serve

# Pull Llama 3.2 model
ollama pull llama3.2
```

### Step 1: Ingest PDFs
```bash
# Place your DWR PDFs in the working directory
# Naming convention: *DWR*CA*.pdf or *DWR*Contractor*.pdf

python ingest_pymupdf.py
```

**Output:** `markdown_output/` directory with `.md` files

**What it does:**
- Extracts text from all DWR PDFs
- Preserves table structure
- Handles encoding issues (Unicode/emoji)
- Standardizes filenames for matching

---

### Step 2: Extract & Reconcile
```bash
python extract_final.py
```

**Output:** `contract_admin.db` SQLite database

**What it does:**
- Uses Llama 3.2 to extract structured data (labour, equipment, materials)
- Validates with Pydantic schemas
- Matches CA + Contractor DWR pairs by Change Order
- Compares line items with ±5% variance threshold
- Stores complete audit trail in database

**Processing:**
- ~30-60 seconds per DWR pair (depending on complexity)
- Retry logic (3 attempts) for LLM extraction failures
- Progress displayed in console

---

### Step 3: View Results (Console)
```bash
python view_reconciliation.py
```

**What it shows:**
- Database statistics (total items, by status)
- Reconciliation tables by Change Order
- Line-by-line comparison with variance percentages
- DWR extraction summaries

**Example output:**
```
📊 RECONCILIATION: CO-21
========================================
  Summary: ✅ 7 MATCH | 🚨 0 FLAG | 🆕 0 NEW | ❓ 0 MISSING

  Category     Description                       CA    Contr   Var%   Status
  ────────────────────────────────────────────────────────────────────────
  Labour       Foreman                          2.0     2.0   0.0%  ✅ MATCH
  Equipment    94 INTL 4900 TANDEM CRASH        4.0     4.0   0.0%  ✅ MATCH
```

---

### Step 4: Generate Visual Demo (HTML)
```bash
python export_demo_html.py
```

**Output:** `reconciliation_demo_live.html`

**What it creates:**
- Complete standalone HTML file (no external dependencies)
- Professional dark theme with Montserrat typography
- Real data embedded from database
- Tab system for multiple Change Orders
- Executive summary metrics
- Mermaid pipeline diagram
- Responsive design (mobile-friendly)

**Features:**
- Status badges: 🚨 FLAG, ✅ MATCH, 🆕 NEW, ❓ MISSING
- Color-coded variances (red for positive, green for zero)
- Hover effects and smooth transitions
- Print-friendly styling

**Usage:** Double-click the HTML file to open in browser

---

## File Descriptions

### Core Pipeline Files

**`ingest_pymupdf.py`**
- PDF → Markdown converter
- Bypasses Docling complexity
- Smart filename parsing with regex
- Handles both CA and Contractor naming conventions
- Uses `errors="replace"` for Unicode safety

**`extract_final.py`**
- Main extraction + reconciliation engine
- Integrates Ollama API with structured output
- Pydantic V2 schemas for validation
- SQLite database manager with audit trails
- Reconciliation logic with fuzzy matching
- Batch processing for multiple DWR pairs

**`view_reconciliation.py`**
- Console query tool for database
- Displays statistics and reconciliation results
- Formatted tables with emojis and status indicators
- Useful for quick verification

**`export_demo_html.py`**
- HTML generator with embedded data
- Queries database and builds complete webpage
- Preserves professional styling
- Smart tab selection (max 5 COs, prioritized by FLAGS)
- Single-file output for easy sharing

### Schema Definitions

**`schemas.py`**
- Pydantic V2 models for DWR data
- Enforces data types and ranges
- Enums for controlled vocabularies
- Validation logic for construction quantities

### Supporting Files

**`generate_mock_dwr.py`**
- Creates synthetic test data
- Generates matched CA + Contractor pairs
- Includes deliberate discrepancies for testing
- Useful for pipeline validation

**`reconcile.py`**
- Standalone reconciliation module
- Pure Python comparison logic (no AI)
- Markdown parsing functions
- Can be used independently of extraction pipeline

---

## Database Schema

**Tables:**
- `dwr_headers` - Metadata from each DWR
- `labour_items` - Labour line items with hours
- `equipment_items` - Equipment usage records
- `material_items` - Material quantities
- `reconciliation` - Comparison results (CA vs Contractor)

**Key Features:**
- Foreign key constraints
- Timestamps on all insertions
- Source tracking (PDF filename, model used)
- Full audit trail

**Query examples:**
```sql
-- Get all FLAGS for a change order
SELECT * FROM reconciliation 
WHERE change_order = 'CO-21' AND status = 'FLAG';

-- Count reconciliation status
SELECT status, COUNT(*) FROM reconciliation 
GROUP BY status;

-- Find DWRs by date range
SELECT * FROM dwr_headers 
WHERE dwr_date BETWEEN '01-Aug-21' AND '31-Aug-21';
```

---

## Reconciliation Logic

### Matching Strategy
1. **Normalize descriptions** (lowercase, remove extra spaces)
2. **Match by exact description** within same category
3. **Calculate variance percentage**: `(Contractor - CA) / CA * 100`

### Status Rules
- **MATCH**: Variance within ±5%
- **FLAG**: Variance exceeds ±5%
- **NEW**: Present in Contractor report only
- **MISSING**: Present in CA report only

### Categories
- **Labour**: Man-hours by classification (Foreman, Operator, etc.)
- **Equipment**: Hours by equipment type (Backhoe, Truck, etc.)
- **Material**: Quantities by material (Granular, Fence, etc.)

---

## Customization

### Adjust Variance Threshold
Edit `extract_final.py`:
```python
def calculate_variance(ca_value: float, contractor_value: float) -> Tuple[float, str]:
    variance_pct = ((contractor_value - ca_value) / ca_value) * 100
    
    if abs(variance_pct) <= 5.0:  # Change this threshold
        return variance_pct, "MATCH"
```

### Change LLM Model
Edit `extract_final.py`:
```python
def main():
    model_name = "llama3.2"  # Try: "llama3.1", "mistral", etc.
```

### Customize HTML Styling
Edit `export_demo_html.py` CSS section:
```python
# Search for color definitions
background: #131313;  # Dark background
color: #bbbbbb;       # Text color
```

---

## Troubleshooting

### "Database not found"
**Problem:** Running viewer/exporter before extraction
**Solution:** Run `extract_final.py` first

### "No markdown files found"
**Problem:** PDF ingestion not completed
**Solution:** Run `ingest_pymupdf.py` first

### "Ollama connection failed"
**Problem:** Ollama service not running
**Solution:** `ollama serve` in separate terminal

### "Extraction timeout"
**Problem:** Large or complex PDFs taking too long
**Solution:** Increase timeout in `extract_final.py` or split PDFs

### "Unicode decode error"
**Problem:** Special characters in PDFs
**Solution:** Already handled with `errors="replace"` in ingestion

---

## Performance Notes

**Processing Times:**
- Ingestion: ~1-2 seconds per PDF
- Extraction: ~30-60 seconds per DWR (LLM dependent)
- Reconciliation: Instant (pure Python)
- HTML generation: ~1-2 seconds

**Resource Requirements:**
- RAM: ~2GB for Llama 3.2
- Disk: ~2GB for model, ~10MB for database
- CPU: Any modern processor (no GPU needed)

---

## Demo Workflow Summary

```bash
# Complete workflow from PDFs to visual demo
python ingest_pymupdf.py         # Step 1: Extract PDFs → Markdown
python extract_final.py          # Step 2: Extract + Reconcile → Database
python view_reconciliation.py    # Step 3: View results in console
python export_demo_html.py       # Step 4: Generate visual demo

# Open reconciliation_demo_live.html in browser
```

---

## Next Steps

**Production Enhancements:**
- [ ] Fuzzy matching for line item descriptions
- [ ] Unit normalization (hrs vs. hours vs. h)
- [ ] Confidence scoring on extractions
- [ ] Web UI with real-time updates
- [ ] Batch processing CLI
- [ ] PDF annotation with variance highlights

**Portfolio Improvements:**
- [ ] Add project screenshots to README
- [ ] Record demo video
- [ ] Create architecture diagram
- [ ] Write technical blog post
- [ ] Prepare interview talking points

---

## License & Attribution

This project demonstrates production-quality AI document processing for construction contract administration. Built with Python, Pydantic V2, PyMuPDF, and Ollama/Llama 3.2.

All MTO data anonymized per privacy requirements.

---

**Questions?** Check console output for detailed error messages and troubleshooting hints.
