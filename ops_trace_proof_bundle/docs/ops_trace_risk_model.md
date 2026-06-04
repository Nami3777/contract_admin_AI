# OpsTrace Risk Model - FMEA/FTA-Inspired Review Structure

This note explains how OpsTrace can support compliance and system-safety thinking without claiming certification-grade SORA, FMEA, FTA, or FHA expertise.

Safe positioning:

> OpsTrace uses an FMEA/FTA-inspired exception structure to make operational evidence gaps visible, route them to human review, and preserve an audit trail.

Unsafe positioning:

> OpsTrace performs formal UAS certification, SORA, FMEA, FTA, or FHA assessment.

## Why Risk Lives Between Documents

In the source workflow, individual documents are useful but incomplete:

- a DWR says work happened
- a contractor record may disagree
- an Instruction Notice may require action
- a certificate may prove compliance
- an incident record may require follow-up
- a change record may create commercial or quality impact

OpsTrace treats missing links, conflicting records, and expired evidence as operational risk signals.

## FMEA-Inspired Exception Fields

| Field | OpsTrace Meaning | Example |
|---|---|---|
| Failure mode | What can go wrong in the workflow | Certificate expired before review date |
| Effect | Why it matters | Quality evidence may not be audit-ready |
| Cause | Likely source of the gap | Calibration record not updated or not linked |
| Detection method | How OpsTrace flags it | Deterministic expiry check |
| Mitigation | What the reviewer should do | Request valid certificate or block closure |
| Residual status | What remains after review | Open / accepted / resolved / rejected |

## FTA-Inspired Top Events

OpsTrace can group exceptions under top operational events:

| Top Event | Contributing Exception Paths |
|---|---|
| Work package not audit-ready | Missing evidence, unlinked certificate, unresolved instruction |
| Production or field record cannot be trusted | CA/contractor mismatch, date mismatch, quantity variance |
| Compliance evidence incomplete | Expired certificate, missing acceptance record, unlinked calibration record |
| Safety or operational exception not closed | Incident recorded without corrective-action evidence |

## FHA-Inspired Hazard Framing

OpsTrace can describe hazards in operational language:

| Functional Hazard | Operational Effect |
|---|---|
| Unclear instruction closure | Team may believe required action is complete without evidence |
| Expired measurement certificate | Quality verification may be based on invalid measurement evidence |
| Conflicting work records | Payment, schedule, or quality decisions may rely on disputed data |
| Missing incident follow-up | Similar issue may repeat because corrective action is not visible |

## Manufacturing / AIT Equivalent

| OpsTrace Source Scenario | Manufacturing / AIT Scenario |
|---|---|
| DWR discrepancy | Operator record and supervisor/system record disagree |
| Instruction Notice without closure evidence | Work instruction update not linked to station execution record |
| Expired calibration certificate | Test or inspection equipment is out of valid calibration window |
| Incident notification | Nonconformance or safety event without closure evidence |
| Change Order | Engineering change / rework order that needs traceable execution proof |

## AI Safety Boundary

AI is allowed to:

- classify document type
- summarize evidence gaps
- suggest likely missing evidence
- draft reviewer questions
- group similar exceptions

AI is not allowed to:

- approve closure
- accept risk
- validate payment
- certify compliance
- override deterministic rule checks

This boundary is the main product judgment:

> AI helps reviewers see the risk faster; it does not become the authority that accepts the risk.

## Future Add-On

A next iteration can add a `risk_register` table:

- `risk_id`
- `linked_exception_id`
- `failure_mode`
- `effect`
- `cause`
- `detection_method`
- `mitigation_action`
- `residual_status`
- `review_owner`

This would support safety/compliance storytelling for aerospace, UAS, robotics, and regulated production roles while remaining honest about certification boundaries.
