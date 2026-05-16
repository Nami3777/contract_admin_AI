## Contract Administration AI - Case Study

This folder contains the primary case study presentation demonstrating how AI can automate construction contract administration workflows.

### Main Document

**[Contract_Admin_AI_Case_Study.pdf](Contract_Admin_AI_Case_Study.pdf)**

*15-slide presentation covering:*
- Problem identification and user research
- Solution architecture and design decisions
- Technical implementation approach
- Business impact and ROI analysis
- Product management methodology
- Future roadmap

### Key Highlights

**Business Impact:**
- 85% reduction in reconciliation time (2 hours → 18 minutes per contract workflow)
- 95% extraction accuracy
- Pilot-ready prototype; not yet production-deployed

**PM Approach:**
- Field observation and user research with 10+ construction project managers
- Strategic design trade-offs (local LLM vs cloud; AI extraction vs deterministic reconciliation)
- Governance-first architecture (human review path, no automated financial decisions)
- Quantified outcomes with realistic scope framing

**Technical Stack:**
- PDF Processing: PyMuPDF
- AI: Claude Haiku (Anthropic API, via tool_use)
- Validation: Pydantic V2 (schema enforcement)
- API: FastAPI (REST, async)
