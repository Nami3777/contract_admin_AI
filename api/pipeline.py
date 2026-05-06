"""
Reconciliation pipeline: PDF → text → Claude extraction → Python reconciliation.

Layer 1: PyMuPDF (PDF → plain text)
Layer 2: Claude API (text → structured DWRReport via tool use)
Layer 3: Pure Python variance calculation (deterministic, no AI)
"""
import asyncio
import time
import re
from typing import List, Optional

import fitz  # PyMuPDF

from .extractor import extract_dwr_with_claude

# -----------------------------------------------------------------------
# Layer 1: PDF → text
# -----------------------------------------------------------------------

def pdf_to_text(pdf_path: str) -> str:
    doc = fitz.open(pdf_path)
    pages = []
    for page_num, page in enumerate(doc, 1):
        pages.append(f"## Page {page_num}\n\n{page.get_text()}")
    doc.close()
    return "\n\n".join(pages)


# -----------------------------------------------------------------------
# Layer 3: Reconciliation (pure Python — copied from demo/extract.py)
# No dependency on Ollama; works with DWRReport Pydantic objects.
# -----------------------------------------------------------------------

def _calc_variance(ca_val: float, con_val: float):
    if ca_val == 0 and con_val == 0:
        return 0.0, "MATCH"
    if ca_val == 0:
        return 100.0, "FLAG"
    pct = abs(con_val - ca_val) / ca_val * 100
    return round(pct, 1), "FLAG" if pct > 5.0 else "MATCH"


def _norm_labour(name: str) -> str:
    return name.lower().strip().replace("/", " ").replace("  ", " ")


def _norm_equip(name: str) -> str:
    clean = re.sub(r'[^A-Z0-9 ]', '', name.upper().strip())
    parts = clean.split()
    if len(parts) >= 2 and parts[0].isdigit():
        return f"{parts[0]} {parts[1]}"
    return parts[0] if parts else clean


def reconcile_reports(ca_report, contractor_report) -> List[dict]:
    results = []

    # Labour
    ca_lab = {_norm_labour(l.classification): l for l in ca_report.labour}
    con_lab = {_norm_labour(l.classification): l for l in contractor_report.labour}
    for key in sorted(set(ca_lab) | set(con_lab)):
        ca, con = ca_lab.get(key), con_lab.get(key)
        if ca and con:
            var, status = _calc_variance(ca.total_man_hours, con.total_man_hours)
            results.append({
                "category": "Labour", "description": ca.classification,
                "ca_value": ca.total_man_hours, "contractor_value": con.total_man_hours,
                "unit": "man-hours", "variance_pct": var, "status": status,
                "notes": f"CA: {ca.remarks or '—'} | Contractor: {con.remarks or '—'}"
                         if (ca.remarks or con.remarks) else None
            })
        elif ca:
            results.append({
                "category": "Labour", "description": ca.classification,
                "ca_value": ca.total_man_hours, "contractor_value": None,
                "unit": "man-hours", "variance_pct": None, "status": "MISSING",
                "notes": "Present in CA report only"
            })
        else:
            results.append({
                "category": "Labour", "description": con.classification,
                "ca_value": None, "contractor_value": con.total_man_hours,
                "unit": "man-hours", "variance_pct": None, "status": "NEW",
                "notes": "Present in Contractor report only"
            })

    # Equipment (by simplified match key)
    ca_eq = {_norm_equip(e.equipment_name): e for e in ca_report.equipment}
    con_eq = {_norm_equip(e.equipment_name): e for e in contractor_report.equipment}
    for key in sorted(set(ca_eq) | set(con_eq)):
        ca, con = ca_eq.get(key), con_eq.get(key)
        if ca and con:
            var, status = _calc_variance(ca.hours_worked, con.hours_worked)
            display = ca.equipment_name if len(ca.equipment_name) >= len(con.equipment_name) else con.equipment_name
            results.append({
                "category": "Equipment", "description": display,
                "ca_value": ca.hours_worked, "contractor_value": con.hours_worked,
                "unit": "hours", "variance_pct": var, "status": status, "notes": None
            })
        elif ca:
            results.append({
                "category": "Equipment", "description": ca.equipment_name,
                "ca_value": ca.hours_worked, "contractor_value": None,
                "unit": "hours", "variance_pct": None, "status": "MISSING",
                "notes": "Present in CA report only"
            })
        else:
            results.append({
                "category": "Equipment", "description": con.equipment_name,
                "ca_value": None, "contractor_value": con.hours_worked,
                "unit": "hours", "variance_pct": None, "status": "NEW",
                "notes": "Present in Contractor report only"
            })

    # Materials
    def _mat_key(m) -> str:
        return (m.material_description or m.material).lower().strip()

    ca_mats = {_mat_key(m): m for m in ca_report.materials}
    con_mats = {_mat_key(m): m for m in contractor_report.materials}
    for key in sorted(set(ca_mats) | set(con_mats)):
        ca, con = ca_mats.get(key), con_mats.get(key)
        if ca and con:
            var, status = _calc_variance(ca.quantity or 0, con.quantity or 0)
            results.append({
                "category": "Material",
                "description": ca.material_description or ca.material,
                "ca_value": ca.quantity, "contractor_value": con.quantity,
                "unit": ca.units or "EA", "variance_pct": var, "status": status, "notes": None
            })
        elif ca:
            results.append({
                "category": "Material",
                "description": ca.material_description or ca.material,
                "ca_value": ca.quantity, "contractor_value": None,
                "unit": ca.units or "EA", "variance_pct": None, "status": "MISSING",
                "notes": "Present in CA report only"
            })
        else:
            results.append({
                "category": "Material",
                "description": con.material_description or con.material,
                "ca_value": None, "contractor_value": con.quantity,
                "unit": con.units or "EA", "variance_pct": None, "status": "NEW",
                "notes": "Present in Contractor report only"
            })

    return results


# -----------------------------------------------------------------------
# Main entry point
# -----------------------------------------------------------------------

async def run_pipeline(ca_pdf_path: str, contractor_pdf_path: str) -> dict:
    start = time.perf_counter()

    # Layer 1: PDF → text (sync, fast)
    ca_text = pdf_to_text(ca_pdf_path)
    con_text = pdf_to_text(contractor_pdf_path)

    # Layer 2: LLM extraction (async, run concurrently)
    ca_report, con_report = await asyncio.gather(
        extract_dwr_with_claude(ca_text, "CA"),
        extract_dwr_with_claude(con_text, "Contractor")
    )

    # Layer 3: Reconciliation (sync, pure Python)
    items = reconcile_reports(ca_report, con_report)

    elapsed = round(time.perf_counter() - start, 1)

    return {
        "change_order": ca_report.header.change_order or "N/A",
        "work_date": ca_report.header.dwr_date,
        "ca_record_id": ca_report.header.record_id,
        "contractor_record_id": con_report.header.record_id,
        "processing_time_seconds": elapsed,
        "summary": {
            "total": len(items),
            "matches": sum(1 for r in items if r["status"] == "MATCH"),
            "flags": sum(1 for r in items if r["status"] == "FLAG"),
            "new": sum(1 for r in items if r["status"] == "NEW"),
            "missing": sum(1 for r in items if r["status"] == "MISSING"),
        },
        "items": items
    }
