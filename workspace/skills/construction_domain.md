# Construction Domain Knowledge

## DWR (Daily Work Record)

The primary document type this tool processes. Submitted by both the Contract Administrator (CA/Inspector) and the Contractor independently for the same day's work. Discrepancies between the two are the basis for payment disputes.

**Who submits**: Both CA and Contractor, independently, for the same work date.
**Purpose**: Record of labour hours, equipment usage, and materials consumed for Time & Materials (T&M) payment claims.
**Standard**: Ontario MTO (Ministry of Transportation Ontario) format.

## Key Terminology

| Term | Meaning |
|---|---|
| CA | Contract Administrator — the inspector representing the client (MTO) |
| DWR | Daily Work Record — the form both parties submit |
| Change Order (CO) | Approved modification to the original contract scope |
| T&M | Time & Materials — payment basis where actuals are billed vs lump sum |
| ±5% threshold | MTO standard: variances within 5% are acceptable; beyond requires review |
| FLAG | A line item where CA and Contractor values differ by more than 5% |
| MATCH | A line item where values agree within ±5% |
| NEW | A Contractor-reported item absent from the CA report |
| MISSING | A CA-reported item absent from the Contractor report |

## FIDIC / NEC Contracts (future scope)

The current implementation is calibrated for Ontario MTO DWR format. Future expansion to FIDIC (Fédération Internationale des Ingénieurs-Conseils) and NEC (New Engineering Contract) formats would require new extraction rules in Stage 02 and different variance thresholds in Stage 03.

FIDIC contracts are the international standard used in infrastructure projects across EU, Middle East, and Asia — relevant for Samsung SDS, Hyundai AutoEver, and European consulting engagements.

## EU AI Act Relevance

This tool is a **non-high-risk AI system** under EU AI Act classification (Article 6, Annex III). However:
- The audit trail (SQLite, timestamps, model provenance) satisfies Article 9 risk management requirements
- The deterministic Layer 3 (no AI in financial calculations) satisfies Article 14 human oversight requirements
- GDPR compliance: no personal data stored; all test data is anonymized or synthetic

Positioning for EU AI Act-aware hiring managers: "compliance-native architecture from day one."
