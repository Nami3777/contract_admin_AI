# User Research: Construction Contract Administration Workflow

## My Background

- **Role:** Junior Field Inspector (Heavy Civil Construction)
- **Duration:** 2 years (2021-2023)
- **Project:** $25M+ highway expansion, Eastern Canada
- **Team:** 1 Contract Administrator + 4-6 field inspectors

## Research Methodology

**Approach:** Direct field observation over 2 years

**Methods:**
- Submitted Daily Work Records (DWRs) as field inspector
- Observed Contract Administrator reconciliation workflow
- Analyzed 50+ reconciliation reports
- Informal conversations with CA and project team
- Documented time delays and discrepancies

**Validation:** Based on real project documents, not assumptions

---

## The Problem Observed

### Context
Contract Administrators must reconcile Daily Work Records submitted by contractors against inspector measurements, especially for change order work (extra work requiring payment validation).

### Real Example from Documents

**Reconciliation Challenge:**
- **Contractor submitted:** 8 man-hours, 2 machines, June 7, 2021
- **Inspector submitted:** 37 man-hours, 6 machines, June 18, 2021
- **Both linked to:** Same Change Order (CO-8)
- **Submitted:** July 7 (3-4 weeks after work completed)

**CA's Dilemma:**
- Are these the same work or different days? (dates don't match)
- Which quantities are correct? (362% variance in labor!)
- How to verify weeks after work was done?
- Manual comparison required: 2-4 hours per DWR pair

---

## Key Pain Points

### 1. Time-Consuming Manual Process 
**Observed workflow:**
- Extract data from contractor PDF: 30-60 minutes
- Extract data from inspector PDF: 30-60 minutes
- Compare line-by-line in spreadsheet: 30-60 minutes
- Investigate discrepancies: 1-2 hours

**Total:** 2-4 hours per DWR reconciliation

**Frequency:** 20-40 change order DWRs per project

**Annual impact:** 60-120 hours per year of pure data entry

---

### 2. Reporting Delays 
**Timeline observed:**
- Work completed: Early June
- DWRs submitted: Early July (3-4 weeks later)
- Reconciliation: Mid-late July
- Approval: August

**Problem:** By the time disputes arise (6-8 weeks after work), difficult to verify:
- Field crew moved to different area
- Memory faded ("What did we do June 7?")
- Evidence harder to collect

---

### 3. Conflicting Data 
**Common discrepancies observed:**
- Labor hours: Variances of 50-300% not uncommon
- Equipment: Different machines listed
- Dates: Same work recorded on different days
- Materials: Different quantities or units

**Impact:** Every discrepancy requires investigation (phone calls, field note review, coordination meetings)

---

### 4. Error-Prone Process 
**Errors observed:**
- Data entry typos (manual typing from PDF)
- Formula errors in Excel ("forgot to copy formula to new row")
- Version control issues (v1, v2, v2_final, v2_final_revised)
- Missed line items (scrolled past without noticing)

**Error rate:** ~15% of reconciliations had mistakes requiring rework

---

## Business Impact

### Per Project (Conservative Estimate)

**Assumptions:**
- 30 change order DWRs per project
- 3 hours average per reconciliation
- $50/hour loaded cost for CA time

**Direct costs:**
- Time: 30 DWRs × 3 hours = 90 hours
- Cost: 90 hours × $50 = $4,500 per project
- Error rework: ~$1,000 per project
- **Total: $5,500 per project in direct waste**

### For 10-CA Organization

**Annual costs:**
- Labor: $45,000/year (90 hrs × 10 CAs × $50/hr)
- Errors: $10,000/year
- **Total: $55,000/year in measurable waste**

### Intangible Costs

**Also observed but harder to quantify:**
- Delayed contractor payments → relationship strain
- Reactive management → missed risks
- Compliance risks → audit trail gaps

---

## User Needs (Prioritized)

### Must Have
1. **Automated data extraction** from PDFs (eliminate manual typing)
2. **Side-by-side comparison** (contractor vs inspector, instant view)
3. **Automatic discrepancy flagging** (highlight items needing review)
4. **Validation rules** (catch obvious errors before human review)

### Should Have
5. **Workflow status tracking** (where is each reconciliation?)
6. **Historical comparison** (is this variance normal?)

### Nice to Have
7. **Predictive alerts** (quantity seems unusual, verify?)
8. **Trend analysis** (contractor accuracy over time)

---

## Key Insights

### Insight 1: PDF Format Non-Negotiable
**Observation:** Government regulations require PDF submissions

**Implication:** Solution must handle PDF input (can't ask users to change format)

**Challenge:** Construction PDFs are messy (scanned, handwritten, inconsistent)

---

### Insight 2: Speed Enables Better Verification
**Observation:** 3-4 week delay makes verification difficult

**Realization:** Real-time (or next-day) processing would enable:
- Verify while memory fresh
- Re-measure if needed (staff still on site)
- Resolve disputes faster (before they escalate)

**Product decision:** Prioritize speed of processing

---

### Insight 3: Change Orders = High-Value Target
**Observation:**
- Regular work: Routine, contract prices, less dispute
- Change order work: Extra payment, requires validation, disputes common

**Data:** 80% of reconciliation time spent on 20% of DWRs (change orders)

**Product decision:** Focus automation on change orders first (highest ROI)

---

### Insight 4: Trust = Adoption
**Observation:** CAs skeptical of automation 

**Concern:** "What if the AI makes a mistake and I don't catch it?"

**Product decision:** 
- Never remove human decision-making
- AI flags issues, humans resolve
- Build validation framework (show your work)
- Preserve accountability

---

## Validation

### How I Know This Is Real

**Direct observation:**
- Worked alongside CA for 2 years
- Submitted inspector's diaries myself (experienced the process)
- Saw delays firsthand (June work reconciled in August)

**Document evidence:**
- Real reconciliation reports (23-60 line items)
- Real discrepancies (8 vs 37 man-hours)
- Real approval workflows (5-9 stages)

**Time estimates:**
- Conservative (2-4 hours may underestimate)
- Based on observation, not speculation
- Validated in informal conversations

**Confidence level:** High

This is not hypothetical. This is a real problem, with real costs, affecting real people.

---

## Target User Persona

**Primary User: Contract Administrator**

**Profile:**
- Experience: 10-15 years in construction
- Education: Civil Engineering or Construction Management
- Salary: $70-80K/year
- Age: 35-50
- Reports to: Project Manager or Ministry CA

**Responsibilities (What they SHOULD do):**
- Risk management and issue resolution
- Quality oversight and compliance
- Stakeholder coordination
- Contract interpretation
- Strategic decision-making

**Reality (What they ACTUALLY do):**
- 50-60% time on data entry and reconciliation
- 20-30% time on coordination and meetings
- 10-20% time on actual strategic work

**Pain:**
> "I watched the CA spend the time validating one reconciliation report—checking contractor quantities against inspector measurements, line by line. They mentioned wanting more time for actual contract oversight, but validation work always took priority because payment depended on it being accurate."

**Motivation:**
- Get back to strategic work
- Feel productive (not just busy)
- Build career (not stuck in admin)
- Go home on time (not working evenings to catch up)

---

## Conclusion

Based on 2 years of field observation, Contract Administrators face a clear, measurable problem:

- **60-120 hours/year** wasted on manual data processing
- **$5,500+ per project** in direct costs
- **3-4 week delays** prevent proactive management
- **15% error rate** creates compliance risk

This is a high-value problem worth solving.

The opportunity: Automate PDF extraction → save 80%+ of reconciliation time → free CAs to do strategic work.

Next: [[SOLUTION_DESIGN.md]] - How we solve this problem
