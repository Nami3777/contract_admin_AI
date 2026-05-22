"""
Generate Mock DWR PDFs for Testing
Based on real Ontario MTO DWR format analyzed from uploaded documents.

Creates matched CA + Contractor pairs with deliberate discrepancies
for testing the reconciliation pipeline.
"""
import sys
import io

# Force UTF-8 encoding on Windows to handle emojis
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from pathlib import Path
from datetime import datetime


def generate_mock_dwr_markdown(
    record_id: str,
    created_by: str,
    dwr_date: str,
    from_time: str,
    to_time: str,
    change_order: str,
    source_type: str,  # "CA" or "Contractor"
    labour: list,
    equipment: list,
    materials: list,
    comments: list,
    temperature: float = 20.0,
) -> str:
    """Generate a markdown representation of a DWR matching Ontario MTO format"""

    # Header
    md = f"""# DAILY WORK RECORD - DETAILS REPORT

| Field | Value |
|---|---|
| Contract No. | 2020-4091 |
| Contractor | C**o P****g Inc. |
| Created by | {created_by} |
| Region | Eastern |
| Highway | 417 |
| Record ID | {record_id} |
| DWR Date | {dwr_date} |
| Status | Reviewed |
| From Time (24 Hr) | {from_time} |
| To Time (24 Hr) | {to_time} |

## Weather

| Temperature (C) | Wind Speed | Precipitation Condition | Visibility | Road Conditions | Time |
|---|---|---|---|---|---|
| {temperature} | Light | No Precipitation | Good | Dry | {from_time} |

## DWR Associated To

Linked Change Order (Only if Applicable): 2020-4091-{change_order}

## Labour

| Classification | Number | Reconciled Number | Hours Each | Reconciled Hours | Total Man Hours | Reconciled Man Hours | Remarks | Status |
|---|---|---|---|---|---|---|---|---|
"""

    for item in labour:
        rec_num = item.get('rec_number', '')
        rec_hrs = item.get('rec_hours', '')
        rec_man_hrs = item.get('rec_man_hours', '')
        status = item.get('status', '')
        remarks = item.get('remarks', '')
        md += f"| {item['classification']} | {item['number']} | {rec_num} | {item['hours_each']:.2f} | {rec_hrs} | {item['total']:.2f} | {rec_man_hrs} | {remarks} | {status} |\n"

    md += "\n## Equipment\n\n"
    md += "| Equipment Name | Asset Number | Rented or Owned | Hours Worked | Hours Stand By | Down Time | Operator Include | Remarks | Reconciled Hours Worked | Status |\n"
    md += "|---|---|---|---|---|---|---|---|---|---|\n"

    for item in equipment:
        rec_hrs = item.get('rec_hours', '')
        status = item.get('status', '')
        remarks = item.get('remarks', '')
        md += f"| {item['name']} | 0 | Owned | {item['hours']:.2f} | 0.00 | 0.00 | No | {remarks} | {rec_hrs} | {status} |\n"

    if materials:
        md += "\n## Material Supplied by Contractor\n\n"
        md += "| Material | Material Description | Units | Quantity | New or Used | Remarks | Reconciled Quantity | Status |\n"
        md += "|---|---|---|---|---|---|---|---|\n"
        for item in materials:
            rec_qty = item.get('rec_quantity', '')
            status = item.get('status', '')
            remarks = item.get('remarks', '')
            md += f"| {item['material']} | {item['description']} | {item['units']} | {item['quantity']:.2f} | {item.get('new_used', 'New')} | {remarks} | {rec_qty} | {status} |\n"

    if comments:
        md += "\n## Comments\n\n"
        md += "| No | Comments | User | Date | Stage |\n"
        md += "|---|---|---|---|---|\n"
        for i, comment in enumerate(comments, 1):
            md += f"| {i} | {comment['text']} | {comment.get('user', created_by)} | {dwr_date} | Draft |\n"

    return md


def generate_test_pair_co21():
    """Generate CO-21 pair: Traffic protection work (based on real DWR-007/009)"""

    # CA (Inspector) version — DWR-007
    ca_labour = [
        {"classification": "Foreman", "number": 1, "hours_each": 2.0, "total": 2.0},
        {"classification": "Skilled Labourer (Grademan)", "number": 2, "hours_each": 2.0, "total": 4.0},
        {"classification": "Driver / Teamster", "number": 2, "hours_each": 2.0, "total": 4.0},
        {"classification": "Operator (Backhoe)", "number": 1, "hours_each": 2.0, "total": 2.0},
    ]
    ca_equipment = [
        {"name": "10 CAT 420 BACKHOE", "hours": 2.0},
        {"name": "94 INTL 4900 TANDEM CRASH", "hours": 4.0, "remarks": "2 Crash Trucks, 2 hours each"},
        {"name": "15 CHEV 2500 4X2", "hours": 2.0},
    ]

    ca_md = generate_mock_dwr_markdown(
        record_id="2020-4091-DWR-7",
        created_by="B***n G*****e",
        dwr_date="05-Aug-21",
        from_time="12:00", to_time="14:00",
        change_order="CO-21",
        source_type="CA",
        labour=ca_labour,
        equipment=ca_equipment,
        materials=[],
        comments=[],
        temperature=20.0,
    )

    # Contractor version — DWR-009 (with reconciled values filled in)
    con_labour = [
        {"classification": "Foreman", "number": 1, "rec_number": 1, "hours_each": 2.0, "rec_hours": "2.00", "total": 2.0, "rec_man_hours": "2.00", "status": "T&M"},
        {"classification": "Skilled Labourer (Grademan)", "number": 2, "rec_number": 2, "hours_each": 2.0, "rec_hours": "2.00", "total": 4.0, "rec_man_hours": "4.00", "status": "T&M"},
        {"classification": "Operator (Backhoe)", "number": 1, "rec_number": 1, "hours_each": 2.0, "rec_hours": "2.00", "total": 2.0, "rec_man_hours": "2.00", "status": "T&M"},
        {"classification": "Driver / Teamster", "number": 2, "rec_number": 2, "hours_each": 2.0, "rec_hours": "2.00", "total": 4.0, "rec_man_hours": "4.00", "status": "T&M"},
    ]
    con_equipment = [
        {"name": "15 CHEV 2500 4X2", "hours": 2.0, "rec_hours": "2.00", "status": "T&M"},
        {"name": "94 INTL 4900 TANDEM CRASH", "hours": 4.0, "rec_hours": "4.00",
         "remarks": "Only 1 crash truck in list, two were used, 4 hours charged to one to cover the second truck.",
         "status": "T&M"},
        {"name": "10 CAT 420 BACKHOE", "hours": 2.0, "rec_hours": "2.00", "status": "T&M"},
    ]

    con_md = generate_mock_dwr_markdown(
        record_id="2020-4091-DWR-9",
        created_by="D***n O'H**a",
        dwr_date="05-Aug-21",
        from_time="12:00", to_time="14:00",
        change_order="CO-21",
        source_type="Contractor",
        labour=con_labour,
        equipment=con_equipment,
        materials=[],
        comments=[],
        temperature=20.0,
    )

    return ca_md, con_md


def generate_test_pair_co56():
    """Generate CO-56 pair: Fence reinstatement with materials (based on real DWR-060/061)"""

    # CA version — DWR-060
    ca_labour = [
        {"classification": "Foreman", "number": 1, "hours_each": 4.0, "total": 4.0, "remarks": "J**n D*****o"},
        {"classification": "Skilled Labourer (Grademan)", "number": 2, "hours_each": 4.0, "total": 8.0, "remarks": "D*****k P***n, A*****w C*****d"},
        {"classification": "Driver / Teamster", "number": 1, "hours_each": 4.0, "total": 4.0, "remarks": "A****e P***n (Crash Truck)"},
    ]
    ca_equipment = [
        {"name": "94 INTL 4900 TANDEM CRASH", "hours": 4.0, "remarks": "DT466 / 98468"},
        {"name": "12 CHEV 2500HD", "hours": 4.0, "remarks": "5123979"},
    ]
    ca_materials = [
        {"material": "Performance Requirement - Highway Fence", "description": "Page Wire Field Fence", "units": "EA", "quantity": 1.0, "new_used": "New"},
        {"material": "Performance Requirement - Highway Fence", "description": "T-Bars for Fence", "units": "EA", "quantity": 20.0, "new_used": "New"},
    ]
    ca_comments = [
        {"text": "DWR DESCRIPTION - Extra work to reinstate fence damaged in traffic accident on 2021.09.26 in WBL between Highway 138 interchange and CVIF off-ramp."}
    ]

    ca_md = generate_mock_dwr_markdown(
        record_id="2020-4091-DWR-60",
        created_by="B***n G*****e",
        dwr_date="07-Dec-21",
        from_time="12:00", to_time="16:00",
        change_order="CO-56",
        source_type="CA",
        labour=ca_labour,
        equipment=ca_equipment,
        materials=ca_materials,
        comments=ca_comments,
        temperature=-3.4,
    )

    # Contractor version — DWR-061 (with reconciled values)
    con_labour = [
        {"classification": "Foreman", "number": 1, "rec_number": 1, "hours_each": 4.0, "rec_hours": "4.00", "total": 4.0, "rec_man_hours": "4.00", "remarks": "C**o P****g - J**n D*****o", "status": "T&M"},
        {"classification": "Skilled Labourer (Grademan)", "number": 2, "rec_number": 2, "hours_each": 4.0, "rec_hours": "4.00", "total": 8.0, "rec_man_hours": "8.00", "remarks": "C**o P****g - D*****k P***n and A*****w C*****d", "status": "T&M"},
        {"classification": "Driver / Teamster", "number": 1, "rec_number": 1, "hours_each": 4.0, "rec_hours": "4.00", "total": 4.0, "rec_man_hours": "4.00", "remarks": "C**o P****g - A****e P***n", "status": "T&M"},
    ]
    con_equipment = [
        {"name": "94 INTL 4900 TANDEM CRASH", "hours": 4.0, "rec_hours": "4.00", "remarks": "DT466/98468", "status": "T&M"},
        {"name": "12 CHEV 2500HD", "hours": 4.0, "rec_hours": "4.00", "remarks": "3/4 ton - 5123979", "status": "T&M"},
    ]
    con_materials = [
        {"material": "Performance Requirement - Highway Fence", "description": "Page Wire Field Fence", "units": "EA", "quantity": 1.0, "new_used": "New", "remarks": "Page Wire Field Fence - 1 roll", "rec_quantity": "1.00", "status": "T&M"},
        {"material": "Performance Requirement - Highway Fence", "description": "T-Bars for Fence", "units": "EA", "quantity": 20.0, "new_used": "New", "remarks": "T-bar for field fence 7'", "rec_quantity": "20.00", "status": "T&M"},
    ]
    con_comments = [
        {"text": "Reinstate fence damaged by travelling public in accident back on Sept. 26 on WBL. As directed by A***n (MPCE)"}
    ]

    con_md = generate_mock_dwr_markdown(
        record_id="2020-4091-DWR-61",
        created_by="D***n O'H**a",
        dwr_date="07-Dec-21",
        from_time="12:00", to_time="16:00",
        change_order="CO-56",
        source_type="Contractor",
        labour=con_labour,
        equipment=con_equipment,
        materials=con_materials,
        comments=con_comments,
        temperature=-3.4,
    )

    return ca_md, con_md


def generate_test_pair_with_discrepancy():
    """Generate a synthetic pair with deliberate discrepancies for testing FLAG detection"""

    ca_labour = [
        {"classification": "Foreman", "number": 1, "hours_each": 8.0, "total": 8.0},
        {"classification": "Skilled Labourer (Grademan)", "number": 3, "hours_each": 8.0, "total": 24.0},
        {"classification": "Operator (Excavator)", "number": 1, "hours_each": 8.0, "total": 8.0},
    ]
    ca_equipment = [
        {"name": "CAT 320 EXCAVATOR", "hours": 8.0},
        {"name": "INTL TANDEM DUMP", "hours": 6.0},
    ]
    ca_materials = [
        {"material": "Granular", "description": "Granular B Type II", "units": "tonne", "quantity": 45.0},
    ]

    ca_md = generate_mock_dwr_markdown(
        record_id="2020-4091-DWR-TEST-CA",
        created_by="Test Inspector",
        dwr_date="15-Sep-21",
        from_time="07:00", to_time="15:00",
        change_order="CO-99",
        source_type="CA",
        labour=ca_labour,
        equipment=ca_equipment,
        materials=ca_materials,
        comments=[{"text": "Test DWR with deliberate discrepancies for pipeline validation"}],
        temperature=18.0,
    )

    # Contractor version: deliberate discrepancies
    con_labour = [
        {"classification": "Foreman", "number": 1, "hours_each": 10.0, "total": 10.0, "status": "T&M"},  # +25% FLAG
        {"classification": "Skilled Labourer (Grademan)", "number": 3, "hours_each": 8.0, "total": 24.0, "status": "T&M"},  # MATCH
        {"classification": "Operator (Excavator)", "number": 1, "hours_each": 8.0, "total": 8.0, "status": "T&M"},  # MATCH
        {"classification": "Flagperson", "number": 1, "hours_each": 8.0, "total": 8.0, "status": "T&M"},  # NEW item
    ]
    con_equipment = [
        {"name": "CAT 320 EXCAVATOR", "hours": 8.0, "status": "T&M"},  # MATCH
        {"name": "INTL TANDEM DUMP", "hours": 8.0, "status": "T&M"},  # +33% FLAG
        {"name": "CHEV PICKUP", "hours": 8.0, "status": "T&M"},  # NEW
    ]
    con_materials = [
        {"material": "Granular", "description": "Granular B Type II", "units": "tonne", "quantity": 52.0, "status": "T&M"},  # +15.6% FLAG
    ]

    con_md = generate_mock_dwr_markdown(
        record_id="2020-4091-DWR-TEST-CON",
        created_by="Test Contractor Rep",
        dwr_date="15-Sep-21",
        from_time="07:00", to_time="17:00",  # Note: contractor claims 10hr day vs CA's 8hr
        change_order="CO-99",
        source_type="Contractor",
        labour=con_labour,
        equipment=con_equipment,
        materials=con_materials,
        comments=[{"text": "Extra flagperson required per MTO safety directive. Dump truck additional 2hrs for material hauling."}],
        temperature=18.0,
    )

    return ca_md, con_md


def main():
    """Generate all mock DWR files"""
    output_dir = Path("markdown_output")
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("🏗️  GENERATING MOCK DWR TEST DATA")
    print("=" * 70)

    # CO-21 pair (based on real data)
    print("\n📄 Generating CO-21 pair (traffic protection)...")
    ca_md, con_md = generate_test_pair_co21()
    (output_dir / "2020-4091-DWR-007__CA__2021_07_16_CO-21_.md").write_text(ca_md)
    (output_dir / "2020-4091-DWR-009__Contractor__2021_07_16_CO-21_.md").write_text(con_md)
    print("  ✓ CO-21 pair generated")

    # CO-56 pair (based on real data, with materials)
    print("\n📄 Generating CO-56 pair (fence reinstatement)...")
    ca_md, con_md = generate_test_pair_co56()
    (output_dir / "2020-4091-DWR-060__CA__2021_11_29_CO-56_.md").write_text(ca_md)
    (output_dir / "2020-4091-DWR-061__Contractor__2021_11_29_CO-56_.md").write_text(con_md)
    print("  ✓ CO-56 pair generated")

    # Synthetic discrepancy pair (for demo)
    print("\n📄 Generating CO-99 pair (synthetic with discrepancies)...")
    ca_md, con_md = generate_test_pair_with_discrepancy()
    (output_dir / "2020-4091-DWR-TEST__CA__2021_09_15_CO-99_.md").write_text(ca_md)
    (output_dir / "2020-4091-DWR-TEST__Contractor__2021_09_15_CO-99_.md").write_text(con_md)
    print("  ✓ CO-99 pair generated (with deliberate discrepancies)")

    print(f"\n{'=' * 70}")
    print(f"✅ Generated 3 DWR pairs (6 files) in {output_dir}/")
    print(f"{'=' * 70}")
    print(f"\n💡 Expected reconciliation results:")
    print(f"   CO-21: All MATCH (labour/equipment hours identical)")
    print(f"   CO-56: All MATCH (labour/equipment/materials identical)")
    print(f"   CO-99: Multiple FLAGS (Foreman +25%, Dump +33%, Granular +15.6%)")
    print(f"          Plus NEW items (Flagperson, Pickup truck)")

    return 0


if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
