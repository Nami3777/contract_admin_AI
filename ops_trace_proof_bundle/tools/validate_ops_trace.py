import json
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = ROOT / "data" / "ops_trace_fixture.json"
OUT_PATH = ROOT / "data" / "ops_trace_dashboard_output.json"
VARIANCE_THRESHOLD_PCT = 5


def parse_date(value):
    if not value:
        return None
    return date.fromisoformat(value)


def group_documents(documents):
    grouped = defaultdict(list)
    for doc in documents:
        grouped[doc["linked_work_package"]].append(doc)
    return grouped


def dwr_discrepancy_checks(documents, review_date):
    exceptions = []
    grouped = group_documents(documents)
    for work_package, docs in grouped.items():
        ca_docs = [doc for doc in docs if doc["document_type"] == "CA_DWR"]
        contractor_docs = [doc for doc in docs if doc["document_type"] == "CONTRACTOR_DWR"]
        for ca_doc in ca_docs:
            for contractor_doc in contractor_docs:
                reasons = []
                variance_pct = None
                if ca_doc.get("document_date") != contractor_doc.get("document_date"):
                    reasons.append("date mismatch")
                if ca_doc.get("reference_id") != contractor_doc.get("reference_id"):
                    reasons.append("reference mismatch")
                if ca_doc.get("activity_code") != contractor_doc.get("activity_code"):
                    reasons.append("activity mismatch")
                if ca_doc.get("quantity_value") is not None and contractor_doc.get("quantity_value") is not None:
                    ca_value = float(ca_doc["quantity_value"])
                    contractor_value = float(contractor_doc["quantity_value"])
                    variance_pct = 100 if ca_value == 0 else abs(contractor_value - ca_value) / ca_value * 100
                    if variance_pct > VARIANCE_THRESHOLD_PCT:
                        reasons.append(f"quantity variance {variance_pct:.1f}% exceeds {VARIANCE_THRESHOLD_PCT}% threshold")
                if reasons:
                    exceptions.append(
                        {
                            "exception_id": f"EX-AUTO-DWR-{len(exceptions) + 1:03d}",
                            "source_document_id": ca_doc["document_id"],
                            "related_document_id": contractor_doc["document_id"],
                            "exception_type": "DWR_DISCREPANCY",
                            "severity": "High" if variance_pct and variance_pct > 20 else "Medium",
                            "evidence_gap": "; ".join(reasons),
                            "owner": "Human reviewer",
                            "review_status": "Open",
                            "created_date": review_date.isoformat(),
                            "resolved_date": None,
                            "linked_work_package": work_package,
                        }
                    )
    return exceptions


def instruction_closure_checks(documents, evidence_links, review_date):
    linked_sources = {link["source_document_id"] for link in evidence_links}
    linked_targets = {link["target_document_id"] for link in evidence_links}
    linked_docs = linked_sources | linked_targets
    exceptions = []
    for doc in documents:
        if doc["document_type"] == "INSTRUCTION_NOTICE" and doc["document_id"] not in linked_docs:
            exceptions.append(
                {
                    "exception_id": f"EX-AUTO-INSTR-{len(exceptions) + 1:03d}",
                    "source_document_id": doc["document_id"],
                    "related_document_id": None,
                    "exception_type": "MISSING_FOLLOW_UP_EVIDENCE",
                    "severity": "Medium",
                    "evidence_gap": "Instruction Notice is issued but no linked follow-up evidence exists.",
                    "owner": "Human reviewer",
                    "review_status": "Open",
                    "created_date": review_date.isoformat(),
                    "resolved_date": None,
                    "linked_work_package": doc["linked_work_package"],
                }
            )
    return exceptions


def certificate_validity_checks(documents, review_date):
    exceptions = []
    for doc in documents:
        if doc["document_type"] not in {"CERTIFICATE", "CALIBRATION_CERTIFICATE"}:
            continue
        expires_on = parse_date(doc.get("expires_on"))
        if expires_on and expires_on < review_date:
            exceptions.append(
                {
                    "exception_id": f"EX-AUTO-CERT-{len(exceptions) + 1:03d}",
                    "source_document_id": doc["document_id"],
                    "related_document_id": None,
                    "exception_type": "EXPIRED_CERTIFICATE",
                    "severity": "High",
                    "evidence_gap": f"Certificate expired on {expires_on.isoformat()} before review date {review_date.isoformat()}.",
                    "owner": "Human reviewer",
                    "review_status": "Open",
                    "created_date": review_date.isoformat(),
                    "resolved_date": None,
                    "linked_work_package": doc["linked_work_package"],
                }
            )
        elif doc["status"] not in {"accepted", "recorded"}:
            exceptions.append(
                {
                    "exception_id": f"EX-AUTO-CERT-{len(exceptions) + 1:03d}",
                    "source_document_id": doc["document_id"],
                    "related_document_id": None,
                    "exception_type": "CERTIFICATE_STATUS_REVIEW",
                    "severity": "Medium",
                    "evidence_gap": f"Certificate status is {doc['status']} and requires review.",
                    "owner": "Human reviewer",
                    "review_status": "Open",
                    "created_date": review_date.isoformat(),
                    "resolved_date": None,
                    "linked_work_package": doc["linked_work_package"],
                }
            )
    return exceptions


def build_dashboard_output(fixture, exceptions):
    documents = fixture["document_register"]
    exception_counts = Counter(item["exception_type"] for item in exceptions)
    severity_counts = Counter(item["severity"] for item in exceptions)
    open_exceptions = [item for item in exceptions if item["review_status"] == "Open"]

    return {
        "project": fixture["project"],
        "summary": {
            "document_count": len(documents),
            "evidence_link_count": len(fixture["evidence_links"]),
            "exception_count": len(exceptions),
            "open_exception_count": len(open_exceptions),
            "clean_batch_count": 1,
            "review_required": bool(open_exceptions),
        },
        "exception_counts": dict(exception_counts),
        "severity_counts": dict(severity_counts),
        "exceptions": exceptions,
        "document_register": documents,
        "evidence_links": fixture["evidence_links"],
        "manufacturing_mapping": fixture["manufacturing_mapping"],
    }


def main():
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    review_date = parse_date(fixture["project"]["review_date"])
    documents = fixture["document_register"]
    evidence_links = fixture["evidence_links"]

    exceptions = []
    exceptions.extend(dwr_discrepancy_checks(documents, review_date))
    exceptions.extend(instruction_closure_checks(documents, evidence_links, review_date))
    exceptions.extend(certificate_validity_checks(documents, review_date))

    output = build_dashboard_output(fixture, exceptions)
    OUT_PATH.write_text(json.dumps(output, indent=2), encoding="utf-8")

    expected_types = {"DWR_DISCREPANCY", "MISSING_FOLLOW_UP_EVIDENCE", "EXPIRED_CERTIFICATE"}
    actual_types = {item["exception_type"] for item in exceptions}
    assert expected_types.issubset(actual_types), f"Missing expected exceptions: {expected_types - actual_types}"
    assert len(exceptions) == 3, f"Expected 3 exceptions, got {len(exceptions)}"
    assert output["summary"]["document_count"] == 12
    assert output["summary"]["open_exception_count"] == 3
    assert output["summary"]["clean_batch_count"] == 1

    print(json.dumps(output["summary"], indent=2))
    print(f"Saved dashboard output: {OUT_PATH}")


if __name__ == "__main__":
    main()
