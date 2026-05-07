# Security Audit — DWR Reconciliation Platform

**Audit Date:** May 7, 2026
**Architecture:** FastAPI backend + Claude API (Anthropic) + Vanilla JS frontend
**Deployment target:** Railway (backend), GitHub Pages (frontend)

---

## 1. Data Privacy

**No user data is retained.**
- Uploaded PDFs are written to OS temp files, processed, then deleted in the `finally` block of every request — even on error.
- No database, no logging of file contents, no persistent storage of any user-supplied data.
- The `ANTHROPIC_API_KEY` is never exposed to the frontend or included in any response.

**Synthetic test data only in the repository.**
- All PDF fixtures and sample outputs use anonymized, generated contractor names and non-identifying project numbers.
- No real MTO contract data, real inspector names, or real project locations are committed.

---

## 2. Input Validation

Three layers applied before any file reaches the Claude API:

| Check | Where | Detail |
|-------|-------|--------|
| Content-Type hint | FastAPI `UploadFile` | Field declared as PDF; wrong type raises 422 |
| File size limit | `_validate_pdf()` in `main.py` | Max 5 MB per file; returns HTTP 413 |
| PDF magic bytes | `_validate_pdf()` in `main.py` | First 4 bytes must be `%PDF`; returns HTTP 400 |

A malformed or oversized file is rejected before any LLM call is made, protecting both cost and compute.

---

## 3. API Key & Secrets

- `ANTHROPIC_API_KEY` is loaded from environment variable only (`os.environ.get(...)`).
- `.env` is gitignored. `.env.example` (committed) contains only the placeholder `sk-ant-your-key-here`.
- The `/health` endpoint returns `{"status": "ok"}` only — no key presence or model info exposed.
- Railway injects the key at runtime via its secrets manager; it never touches the filesystem.

---

## 4. Cost Controls

**Per-request cost: ~$0.015 USD** (Haiku pricing: $0.80/M input tokens, $4.00/M output tokens).

Controls that cap runaway spend:
- 5 MB file size limit → limits input token count per call (~4,000–6,000 tokens typical DWR)
- `max_tokens=4096` output cap — sufficient for any DWR, prevents runaway generation
- Two Claude calls per request (CA + Contractor run concurrently via `asyncio.gather`) — concurrent, not sequential, so latency is ~10s not ~20s
- Module-level `AsyncAnthropic` singleton — one connection pool, no per-request setup overhead
- No retry loops that could silently multiply cost: retry only on `ValidationError` (schema mismatch), not on network errors

**No rate limiting is implemented in the demo.** For production, add a middleware rate limiter (e.g., `slowapi`) keyed on IP.

---

## 5. Error Handling

- All unhandled exceptions in `/api/reconcile` return `HTTP 500` with a generic message: `"Processing failed. Please check your PDFs and try again."`
- Internal stack traces are never forwarded to the caller.
- `HTTPException` re-raised directly so validation errors (400, 413) surface correctly.

---

## 6. CORS Policy

Current setting: `allow_origins=["*"]`.

This is appropriate for a public demo with no authenticated endpoints and no session state. If authentication or user-specific data is added in future, restrict to specific origins.

---

## 7. Design Principles (EU AI Act Alignment)

1. **AI extracts — Python calculates.** Financial variance calculations use pure Python only. The LLM is never trusted for arithmetic.
2. **Structured output via tool use.** Claude is forced to return a typed JSON object matching the `DWRReport` Pydantic schema — no free-text parsing, no hallucinated structure.
3. **Audit fields in every response.** Each response includes `processing_time_seconds`, model version is fixed in code (`claude-haiku-4-5-20251001`), and `source_type` ("CA" / "Contractor") is tagged per record.
4. **Human-verifiable outputs.** Every discrepancy is shown with the raw CA value, raw Contractor value, and calculated variance — nothing is hidden in a black box summary.

---

## 8. Findings Summary

| Area | Status | Note |
|------|--------|------|
| Private data in repo | FIXED | `project.local.md`, `STUDY.md` gitignored; config rewritten |
| API key exposure | CLEAR | Env var only; never in code or response |
| File size / DoS protection | FIXED | 5 MB limit + magic byte check |
| Cost runaway | MITIGATED | max_tokens=4096, file size cap, no cost-multiplying retries |
| Internal error leakage | FIXED | Generic 500 message; no stack traces to caller |
| Temp file cleanup | FIXED | `finally` block with None-guard covers all error paths |
| Client singleton | FIXED | `AsyncAnthropic` created once at module level |
| Rate limiting | OPEN | Acceptable for demo; add `slowapi` before commercial launch |
| CORS | ACCEPTABLE | `allow_origins=["*"]` safe for unauthenticated public demo |

**Risk Assessment:** LOW for public demo deployment as-is.
**Open item before commercial launch:** IP-based rate limiting.
