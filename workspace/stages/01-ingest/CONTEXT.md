# Stage 01 — Ingest: PDF → Plain Text

**Job**: Extract readable text from a construction DWR PDF. No interpretation, no analysis. Raw text only.

---

## Inputs

| Source | File/Location | Section/Scope | Why |
|--------|---------------|---------------|-----|
| CA PDF upload | `api/main.py` (UploadFile) | Full file | Source document from Contract Administrator |
| Contractor PDF upload | `api/main.py` (UploadFile) | Full file | Source document from Contractor |
| Domain reference | `references/dwr_structure.md` | Full file | Understand what text patterns to expect |

---

## Process

1. Open the PDF using PyMuPDF (`fitz.open()`)
2. Iterate pages; prefix each with `## Page N` heading
3. Extract raw text (`page.get_text()`) — preserve line breaks, do not reformat
4. Concatenate pages with double newline separator
5. Close the document handle
6. Return the full string to Stage 02

**Do not**: OCR, interpret, summarize, or modify the text. Output is verbatim.

---

## Outputs

| Artifact | Location | Format |
|----------|----------|--------|
| CA text | `output/ca_text.md` (runtime, temp) | Plain markdown string, page-separated |
| Contractor text | `output/contractor_text.md` (runtime, temp) | Plain markdown string, page-separated |

---

## Implementation

```
api/pipeline.py → def pdf_to_text(pdf_path: str) -> str
```

Typical output size: 2,000–6,000 characters per DWR.
