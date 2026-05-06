# Stage 02 — Extract: Plain Text → Structured DWRReport

**Job**: You are a construction contract data extraction specialist. Read the plain-text DWR output from Stage 01 and return a structured `DWRReport` object with zero invented data.

---

## Inputs

| Source | File/Location | Section/Scope | Why |
|--------|---------------|---------------|-----|
| CA text | Stage 01 output | Full string | Document to extract from |
| Contractor text | Stage 01 output | Full string | Document to extract from |
| Pydantic schema | `references/schema.md` | Full file | Required output structure |
| Extraction rules | `references/extraction_rules.md` | Full file | Domain-specific parsing rules |

---

## Process

1. Receive plain-text DWR content from Stage 01
2. Parse HEADER fields first (Contract No, Record ID, Date, Times)
3. Parse WEATHER section
4. Parse LABOUR table — join multi-line entries, extract number/hours/total
5. Parse EQUIPMENT table — join fragmented equipment names, extract hours
6. Parse MATERIALS table — extract category, description, units, quantity
7. Parse COMMENTS — free text only
8. Extract CHANGE ORDER number (pattern: "CO-NN")
9. Validate via Pydantic V2 — retry up to 3 times on validation failure
10. Return populated `DWRReport` object

**Critical rule**: If a value is not explicitly in the text, return `null`. Do NOT estimate or calculate.

**Model**: `claude-haiku-4-5-20251001` via Anthropic tool use API (structured output enforced by schema).

---

## Outputs

| Artifact | Location | Format |
|----------|----------|--------|
| CA DWRReport | Returned to Stage 03 | Pydantic `DWRReport` object |
| Contractor DWRReport | Returned to Stage 03 | Pydantic `DWRReport` object |

---

## Implementation

```
api/extractor.py → async def extract_dwr_with_claude(content: str) -> DWRReport
demo/schemas.py  → class DWRReport (Pydantic V2 schema, unchanged)
```

Both extractions run concurrently (`asyncio.gather`) — total latency ≈ 8–12s.
