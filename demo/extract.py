"""
Layer 2: LLM Extraction for Construction DWRs

Uses Ollama + Llama 3.2 with Pydantic V2 structured output.
Extracts labour, equipment, materials, and metadata from DWR markdown.
"""

import ollama
import json
import sqlite3
from pydantic import ValidationError
from typing import List, Optional
from datetime import datetime
from pathlib import Path

from schemas import (
    DWRReport, DWRHeader, WeatherRecord,
    LabourLineItem, EquipmentLineItem, MaterialLineItem, DWRComment
)


# ============================================================
# Database Manager — Layer 4: Storage & Audit
# ============================================================

class DatabaseManager:
    """Handles all database operations for DWR extraction results"""

    def __init__(self, db_path: str = "contract_admin.db"):
        self.db_path = Path(db_path)
        self.initialize_database()

    def initialize_database(self):
        """Create database schema for construction DWR data"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # DWR Headers
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS dwr_headers (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        contract_no TEXT NOT NULL,
                        record_id TEXT NOT NULL UNIQUE,
                        contractor TEXT,
                        created_by TEXT,
                        dwr_date TEXT,
                        from_time TEXT,
                        to_time TEXT,
                        status TEXT,
                        change_order TEXT,
                        highway TEXT,
                        region TEXT,
                        source_type TEXT CHECK(source_type IN ('CA', 'Contractor')),
                        pdf_source TEXT,
                        extraction_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        model_used TEXT
                    )
                ''')

                # Labour line items
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS labour_items (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        dwr_record_id TEXT NOT NULL,
                        classification TEXT NOT NULL,
                        number INTEGER,
                        hours_each REAL,
                        total_man_hours REAL,
                        reconciled_number INTEGER,
                        reconciled_hours REAL,
                        reconciled_man_hours REAL,
                        remarks TEXT,
                        status TEXT,
                        FOREIGN KEY (dwr_record_id) REFERENCES dwr_headers(record_id)
                    )
                ''')

                # Equipment line items
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS equipment_items (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        dwr_record_id TEXT NOT NULL,
                        equipment_name TEXT NOT NULL,
                        rented_or_owned TEXT,
                        hours_worked REAL,
                        hours_standby REAL DEFAULT 0,
                        down_time REAL DEFAULT 0,
                        operator_included INTEGER,
                        remarks TEXT,
                        reconciled_hours_worked REAL,
                        reconciled_hours_standby REAL,
                        reconciled_down_time REAL,
                        status TEXT,
                        FOREIGN KEY (dwr_record_id) REFERENCES dwr_headers(record_id)
                    )
                ''')

                # Material line items
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS material_items (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        dwr_record_id TEXT NOT NULL,
                        material TEXT NOT NULL,
                        material_description TEXT,
                        units TEXT,
                        quantity REAL,
                        new_or_used TEXT,
                        remarks TEXT,
                        reconciled_quantity REAL,
                        status TEXT,
                        FOREIGN KEY (dwr_record_id) REFERENCES dwr_headers(record_id)
                    )
                ''')

                # Reconciliation results
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS reconciliation (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        change_order TEXT NOT NULL,
                        work_date TEXT,
                        ca_record_id TEXT,
                        contractor_record_id TEXT,
                        category TEXT NOT NULL,
                        description TEXT NOT NULL,
                        ca_value REAL,
                        contractor_value REAL,
                        unit TEXT DEFAULT 'hours',
                        variance_pct REAL,
                        status TEXT CHECK(status IN ('MATCH', 'FLAG', 'NEW', 'MISSING')),
                        notes TEXT,
                        reconciliation_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (ca_record_id) REFERENCES dwr_headers(record_id),
                        FOREIGN KEY (contractor_record_id) REFERENCES dwr_headers(record_id)
                    )
                ''')

                conn.commit()
                print("✓ Database initialized successfully")
        except sqlite3.Error as e:
            print(f"❌ Database initialization failed: {e}")
            raise

    def save_dwr(self, report: DWRReport, source_type: str,
                 pdf_source: str, model_name: str) -> str:
        """Save a complete DWR extraction to database. Returns record_id."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                h = report.header

                # Insert header (use REPLACE to handle re-extractions)
                cursor.execute('''
                    INSERT OR REPLACE INTO dwr_headers
                    (contract_no, record_id, contractor, created_by, dwr_date,
                     from_time, to_time, status, change_order, highway, region,
                     source_type, pdf_source, model_used)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (h.contract_no, h.record_id, h.contractor, h.created_by,
                      h.dwr_date, h.from_time, h.to_time, h.status,
                      h.change_order, h.highway, h.region,
                      source_type, pdf_source, model_name))

                # Clear old line items for re-extraction
                for table in ['labour_items', 'equipment_items', 'material_items']:
                    cursor.execute(f"DELETE FROM {table} WHERE dwr_record_id = ?",
                                   (h.record_id,))

                # Insert labour
                for item in report.labour:
                    cursor.execute('''
                        INSERT INTO labour_items
                        (dwr_record_id, classification, number, hours_each,
                         total_man_hours, reconciled_number, reconciled_hours,
                         reconciled_man_hours, remarks, status)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (h.record_id, item.classification, item.number,
                          item.hours_each, item.total_man_hours,
                          item.reconciled_number, item.reconciled_hours,
                          item.reconciled_man_hours, item.remarks, item.status))

                # Insert equipment
                for item in report.equipment:
                    cursor.execute('''
                        INSERT INTO equipment_items
                        (dwr_record_id, equipment_name, rented_or_owned,
                         hours_worked, hours_standby, down_time,
                         operator_included, remarks,
                         reconciled_hours_worked, reconciled_hours_standby,
                         reconciled_down_time, status)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (h.record_id, item.equipment_name, item.rented_or_owned,
                          item.hours_worked, item.hours_standby, item.down_time,
                          1 if item.operator_included else 0, item.remarks,
                          item.reconciled_hours_worked, item.reconciled_hours_standby,
                          item.reconciled_down_time, item.status))

                # Insert materials
                for item in report.materials:
                    cursor.execute('''
                        INSERT INTO material_items
                        (dwr_record_id, material, material_description, units,
                         quantity, new_or_used, remarks, reconciled_quantity, status)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (h.record_id, item.material, item.material_description,
                          item.units, item.quantity, item.new_or_used,
                          item.remarks, item.reconciled_quantity, item.status))

                conn.commit()
                total = len(report.labour) + len(report.equipment) + len(report.materials)
                print(f"  ✓ Saved {total} line items for {h.record_id}")
                return h.record_id

        except sqlite3.Error as e:
            print(f"  ❌ Database save failed: {e}")
            raise


# ============================================================
# LLM Extraction — Layer 2
# ============================================================

EXTRACTION_PROMPT = '''You are a construction contract administration data extraction specialist.
You will receive text from an Ontario MTO Daily Work Record (DWR) that was extracted from a PDF.
The text is NOT in table format — it flows as plain text with field names and values on separate lines.

DOCUMENT STRUCTURE:
The DWR has these sections in order:
1. HEADER: Contract No, Created Date, Contractor, Created by, Record ID, DWR Date, Status, From/To Time
2. WEATHER: Temperature, Wind Speed, Precipitation, Visibility (after "Weather" heading)
3. LABOUR: After weather data. Pattern repeats for each worker classification:
   Classification name (e.g. "Foreman", "Skilled Labourer (Grademan)", "Driver / Teamster", "Operator (Backhoe)")
   Number (count of workers)
   Reconciled Number (may or may not be present)
   Hours Each (decimal hours like 2.00, 4.00)
   Reconciled Hours (may or may not be present)
   Total Man Hours (Number x Hours Each)
   Reconciled Man Hours (may or may not be present)
   Remarks (optional text, sometimes "T&M")
   Status (optional, e.g. "T&M")
   The labour section ends at "Labour(If Operator included..."

4. EQUIPMENT: After the labour section. Pattern repeats for each piece of equipment:
   Equipment Name — MAY span multiple lines, e.g.:
     "94 INTL" + "4900" + "TANDEM" + "CRASH" = one item named "94 INTL 4900 TANDEM CRASH"
     "10 CAT 420" + "BACKHOE" = one item named "10 CAT 420 BACKHOE"
     "15 CHEV" + "2500 4X2" = one item named "15 CHEV 2500 4X2"
     "12 CHEV" + "2500HD" = one item named "12 CHEV 2500HD"
   The number prefix (10, 12, 15, 94) is the asset number and is PART of the name.
   Asset Number (usually "0")
   Owned/Rented
   Hours Worked (decimal)
   Hours Stand By (decimal, usually 0.00)
   Down Time (decimal, usually 0.00)
   Operator Include ("No" or "Yes")
   Remarks (optional text about the equipment)
   Reconciled Hours Worked (may or may not be present)
   Reconciled Hours Stand By (may or may not be present)
   Reconciled Down Time (may or may not be present)
   Status (optional, e.g. "T&M")

5. MATERIALS: After "Material" heading. Pattern repeats:
   Material category (e.g. "Performance Requirement - Highway Fence")
   Material Description (e.g. "Page Wire Field Fence", "T-Bars for Fence")
   Units (e.g. "EA", "Tonnes", "m2")
   Quantity (decimal)
   New or Used
   Remarks
   Reconciled Quantity (may or may not be present)
   Status (optional, e.g. "T&M")
   If no materials are listed, return an empty materials array.

6. COMMENTS: After "Comments" heading. Look for description text.
7. CHANGE ORDER: Near bottom, look for "Linked Change Order (Only if Applicable)" followed by something like "2020-4091-CO-21". Extract just the CO number (e.g. "CO-21").

CRITICAL RULES:
- Join multi-line equipment names into one string (e.g. "94 INTL\\n4900\\nTANDEM\\nCRASH" becomes "94 INTL 4900 TANDEM CRASH")
- Use exact numbers from the text. Do NOT calculate or estimate.
- If reconciled values are not present (typical for CA/Inspector reports), set them to null.
- If a section has column headers but no data rows, return an empty array for that section.
- The "Material Supplied by Contractor" line is NOT a material item — skip it.
- Column header words like "Type", "Units", "Status" alone are NOT data items — skip them.
- If Record ID contains "DWR-7" that means DWR number 7, record_id should be "2020-4091-DWR-7".
- Do NOT invent data. Only extract what is explicitly in the document.'''


def extract_dwr_with_llm(content: str, model_name: str = "llama3.2") -> DWRReport:
    """
    Extract structured DWR data from markdown content using local LLM.
    Includes retry logic and Pydantic validation.
    """
    max_retries = 3

    for attempt in range(max_retries):
        try:
            print(f"  🤖 Consulting {model_name} (Attempt {attempt + 1}/{max_retries})...")

            response = ollama.chat(
                model=model_name,
                messages=[
                    {'role': 'system', 'content': EXTRACTION_PROMPT},
                    {'role': 'user', 'content': content},
                ],
                format=DWRReport.model_json_schema(),
            )

            raw_json = response['message']['content']
            print(f"  📦 Received {len(raw_json)} characters of JSON")

            # Validate JSON structure
            try:
                response_data = json.loads(raw_json)
            except json.JSONDecodeError as e:
                print(f"  ⚠️  Invalid JSON from LLM: {e}")
                if attempt < max_retries - 1:
                    continue
                else:
                    raise

            # Validate with Pydantic
            try:
                validated_report = DWRReport(**response_data)
                labour_count = len(validated_report.labour)
                equip_count = len(validated_report.equipment)
                mat_count = len(validated_report.materials)
                print(f"  ✓ Validation passed: {labour_count} labour, "
                      f"{equip_count} equipment, {mat_count} material items")
                return validated_report

            except ValidationError as e:
                print(f"  ⚠️  Data validation failed: {e}")
                if attempt < max_retries - 1:
                    continue
                else:
                    raise

        except Exception as e:
            print(f"  ❌ Extraction attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                continue
            else:
                raise

    raise RuntimeError("Extraction failed after all retries")


# ============================================================
# Layer 3: Reconciliation Logic
# ============================================================

def reconcile_dwrs(ca_report: DWRReport, contractor_report: DWRReport) -> List[dict]:
    """
    Compare CA vs Contractor DWR and produce reconciliation line items.
    Uses >5% variance threshold for FLAGS.
    """
    results = []
    VARIANCE_THRESHOLD = 5.0  # percent

    def calc_variance(ca_val: float, con_val: float) -> tuple:
        """Calculate variance percentage and status"""
        if ca_val == 0 and con_val == 0:
            return 0.0, "MATCH"
        if ca_val == 0:
            return 100.0, "FLAG"
        pct = abs(con_val - ca_val) / ca_val * 100
        status = "FLAG" if pct > VARIANCE_THRESHOLD else "MATCH"
        return round(pct, 1), status

    def normalize_classification(name: str) -> str:
        """Normalize labour classification for matching"""
        return name.lower().strip().replace("/", " ").replace("  ", " ")

    # --- Reconcile Labour ---
    ca_labour = {normalize_classification(l.classification): l for l in ca_report.labour}
    con_labour = {normalize_classification(l.classification): l for l in contractor_report.labour}

    all_labour_keys = set(ca_labour.keys()) | set(con_labour.keys())
    for key in sorted(all_labour_keys):
        ca_item = ca_labour.get(key)
        con_item = con_labour.get(key)

        if ca_item and con_item:
            ca_val = ca_item.total_man_hours
            con_val = con_item.total_man_hours
            variance, status = calc_variance(ca_val, con_val)

            notes = None
            if ca_item.remarks or con_item.remarks:
                notes = f"CA: {ca_item.remarks or 'N/A'} | Contractor: {con_item.remarks or 'N/A'}"

            results.append({
                "category": "Labour",
                "description": ca_item.classification,
                "ca_value": ca_val,
                "contractor_value": con_val,
                "unit": "man-hours",
                "variance_pct": variance,
                "status": status,
                "notes": notes
            })
        elif ca_item and not con_item:
            results.append({
                "category": "Labour",
                "description": ca_item.classification,
                "ca_value": ca_item.total_man_hours,
                "contractor_value": None,
                "unit": "man-hours",
                "variance_pct": None,
                "status": "MISSING",
                "notes": "Present in CA report only"
            })
        else:
            results.append({
                "category": "Labour",
                "description": con_item.classification,
                "ca_value": None,
                "contractor_value": con_item.total_man_hours,
                "unit": "man-hours",
                "variance_pct": None,
                "status": "NEW",
                "notes": "Present in Contractor report only"
            })

    # --- Reconcile Equipment ---
    def normalize_equip(name: str) -> str:
        """Normalize equipment name for matching.
        Handles fragmented names like '94 INTL 4900 TANDEM CRASH' vs '94 INTL'.
        Extracts the asset number prefix + first keyword as the canonical key.
        """
        import re
        clean = name.upper().strip().replace("  ", " ")
        # Remove non-alphanumeric except spaces
        clean = re.sub(r'[^A-Z0-9 ]', '', clean)
        return clean.strip()

    def equip_match_key(name: str) -> str:
        """Generate a simplified matching key from equipment name.
        '94 INTL 4900 TANDEM CRASH' -> '94 INTL'
        '10 CAT 420 BACKHOE' -> '10 CAT'
        '15 CHEV 2500 4X2' -> '15 CHEV'
        '12 CHEV 2500HD' -> '12 CHEV'
        'TC-54s' -> 'TC54'
        """
        import re
        clean = name.upper().strip()
        clean = re.sub(r'[^A-Z0-9 ]', '', clean)
        parts = clean.split()
        if len(parts) >= 2 and parts[0].isdigit():
            return f"{parts[0]} {parts[1]}"
        elif len(parts) >= 1:
            return parts[0]
        return clean

    ca_equip_full = {normalize_equip(e.equipment_name): e for e in ca_report.equipment}
    con_equip_full = {normalize_equip(e.equipment_name): e for e in contractor_report.equipment}

    # Build match-key lookup: key -> full normalized name
    ca_by_key = {}
    for full_name, item in ca_equip_full.items():
        key = equip_match_key(full_name)
        ca_by_key[key] = (full_name, item)

    con_by_key = {}
    for full_name, item in con_equip_full.items():
        key = equip_match_key(full_name)
        con_by_key[key] = (full_name, item)

    # Match by simplified key
    all_equip_keys = set(ca_by_key.keys()) | set(con_by_key.keys())
    for key in sorted(all_equip_keys):
        ca_entry = ca_by_key.get(key)
        con_entry = con_by_key.get(key)

        if ca_entry and con_entry:
            ca_name, ca_item = ca_entry
            con_name, con_item = con_entry
            ca_val = ca_item.hours_worked
            con_val = con_item.hours_worked
            variance, status = calc_variance(ca_val, con_val)

            # Use the longer (more descriptive) name for display
            display_name = ca_item.equipment_name if len(ca_item.equipment_name) >= len(con_item.equipment_name) else con_item.equipment_name

            notes = None
            if ca_item.remarks or con_item.remarks:
                notes = f"CA: {ca_item.remarks or 'N/A'} | Contractor: {con_item.remarks or 'N/A'}"

            results.append({
                "category": "Equipment",
                "description": display_name,
                "ca_value": ca_val,
                "contractor_value": con_val,
                "unit": "hours",
                "variance_pct": variance,
                "status": status,
                "notes": notes
            })
        elif ca_entry and not con_entry:
            ca_name, ca_item = ca_entry
            results.append({
                "category": "Equipment",
                "description": ca_item.equipment_name,
                "ca_value": ca_item.hours_worked,
                "contractor_value": None,
                "unit": "hours",
                "variance_pct": None,
                "status": "MISSING",
                "notes": "Present in CA report only"
            })
        else:
            con_name, con_item = con_entry
            results.append({
                "category": "Equipment",
                "description": con_item.equipment_name,
                "ca_value": None,
                "contractor_value": con_item.hours_worked,
                "unit": "hours",
                "variance_pct": None,
                "status": "NEW",
                "notes": "Present in Contractor report only"
            })

    # --- Reconcile Materials ---
    def normalize_mat(item) -> str:
        desc = item.material_description or item.material
        return desc.lower().strip()

    ca_mats = {normalize_mat(m): m for m in ca_report.materials}
    con_mats = {normalize_mat(m): m for m in contractor_report.materials}

    all_mat_keys = set(ca_mats.keys()) | set(con_mats.keys())
    for key in sorted(all_mat_keys):
        ca_item = ca_mats.get(key)
        con_item = con_mats.get(key)

        if ca_item and con_item:
            ca_val = ca_item.quantity or 0
            con_val = con_item.quantity or 0
            variance, status = calc_variance(ca_val, con_val)
            results.append({
                "category": "Material",
                "description": ca_item.material_description or ca_item.material,
                "ca_value": ca_val,
                "contractor_value": con_val,
                "unit": ca_item.units or "EA",
                "variance_pct": variance,
                "status": status,
                "notes": None
            })
        elif ca_item:
            results.append({
                "category": "Material",
                "description": ca_item.material_description or ca_item.material,
                "ca_value": ca_item.quantity,
                "contractor_value": None,
                "unit": ca_item.units or "EA",
                "variance_pct": None,
                "status": "MISSING",
                "notes": "Present in CA report only"
            })
        else:
            results.append({
                "category": "Material",
                "description": con_item.material_description or con_item.material,
                "ca_value": None,
                "contractor_value": con_item.quantity,
                "unit": con_item.units or "EA",
                "variance_pct": None,
                "status": "NEW",
                "notes": "Present in Contractor report only"
            })

    return results


# ============================================================
# Display Functions
# ============================================================

def display_dwr_summary(report: DWRReport, label: str):
    """Pretty-print a DWR extraction summary"""
    h = report.header
    print(f"\n{'─' * 50}")
    print(f"  📋 {label}: {h.record_id}")
    print(f"  Date: {h.dwr_date} | Time: {h.from_time}-{h.to_time}")
    print(f"  Created by: {h.created_by}")
    print(f"  Change Order: {h.change_order or 'N/A'}")
    print(f"  Status: {h.status}")

    if report.labour:
        total_hours = sum(l.total_man_hours for l in report.labour)
        print(f"  Labour: {len(report.labour)} classifications, {total_hours} total man-hours")

    if report.equipment:
        total_equip = sum(e.hours_worked for e in report.equipment)
        print(f"  Equipment: {len(report.equipment)} items, {total_equip} total hours")

    if report.materials:
        print(f"  Materials: {len(report.materials)} items")

    if report.comments:
        print(f"  Comments: {report.comments[0].comment_text[:80]}...")


def display_reconciliation(results: List[dict], change_order: str):
    """Pretty-print reconciliation results"""
    print(f"\n{'=' * 70}")
    print(f"📊 RECONCILIATION: {change_order}")
    print(f"{'=' * 70}")

    flags = [r for r in results if r['status'] == 'FLAG']
    matches = [r for r in results if r['status'] == 'MATCH']
    new_items = [r for r in results if r['status'] == 'NEW']
    missing = [r for r in results if r['status'] == 'MISSING']

    print(f"\n  ✅ Matches: {len(matches)} | 🔴 Flags: {len(flags)} | "
          f"🆕 New: {len(new_items)} | ❓ Missing: {len(missing)}")

    # Display table
    print(f"\n  {'Category':<12} {'Description':<30} {'CA':>8} {'Contr':>8} {'Var%':>6} {'Status':<8}")
    print(f"  {'─' * 80}")

    for item in results:
        ca_val = f"{item['ca_value']:.1f}" if item['ca_value'] is not None else "—"
        con_val = f"{item['contractor_value']:.1f}" if item['contractor_value'] is not None else "—"
        var_pct = f"{item['variance_pct']:.1f}%" if item['variance_pct'] is not None else "—"

        emoji = "🔴" if item['status'] == 'FLAG' else \
                "✅" if item['status'] == 'MATCH' else \
                "🆕" if item['status'] == 'NEW' else "❓"

        desc = item['description'][:28]
        print(f"  {item['category']:<12} {desc:<30} {ca_val:>8} {con_val:>8} {var_pct:>6} {emoji} {item['status']:<8}")

        if item.get('notes') and item['status'] in ('FLAG', 'NEW', 'MISSING'):
            print(f"  {'':>12} 📝 {item['notes'][:60]}")


# ============================================================
# Main Pipeline
# ============================================================

def main():
    """Main execution: extract and reconcile DWR pairs"""
    model_name = "llama3.2"
    markdown_dir = Path("markdown_output")

    # Initialize database
    try:
        db = DatabaseManager()
    except Exception as e:
        print(f"❌ Cannot proceed without database: {e}")
        return 1

    # Discover markdown pairs — support both naming conventions
    ca_files = []
    con_files = []
    if markdown_dir.exists():
        for f in sorted(markdown_dir.glob("*.md")):
            name = f.name
            if "(CA," in name or "(CA " in name or "__CA__" in name or "_CA_" in name:
                ca_files.append(f)
            elif "Contractor" in name:
                con_files.append(f)

    if not ca_files and not con_files:
        # Try single file mode
        single = Path("report.md")
        if single.exists():
            print(f"📖 Reading {single}...")
            content = single.read_text(encoding="utf-8")
            report = extract_dwr_with_llm(content, model_name)
            display_dwr_summary(report, "Single DWR")
            db.save_dwr(report, "Unknown", str(single), model_name)
            return 0
        else:
            print("❌ No markdown files found. Run ingest.py first.")
            return 1

    print(f"\nFound {len(ca_files)} CA files, {len(con_files)} Contractor files")

    # Process each pair
    for ca_file in ca_files:
        # Find matching contractor file by change order
        import re
        co_search = re.search(r'CO-(\d+)', ca_file.stem)
        if co_search:
            co_match = f"CO-{co_search.group(1)}"
        else:
            co_match = None

        if not co_match:
            print(f"⚠️  Cannot determine CO for {ca_file.name}, skipping pair matching")
            continue

        contractor_file = None
        for cf in con_files:
            if co_match in cf.name:
                contractor_file = cf
                break

        if not contractor_file:
            print(f"⚠️  No contractor match for {co_match}")
            continue

        print(f"\n{'=' * 70}")
        print(f"📋 Processing Pair: {co_match}")
        print(f"{'=' * 70}")

        # Extract CA
        print(f"\n[CA Report] {ca_file.name}")
        ca_content = ca_file.read_text(encoding="utf-8", errors="replace")
        ca_report = extract_dwr_with_llm(ca_content, model_name)
        display_dwr_summary(ca_report, "CA (Inspector)")
        db.save_dwr(ca_report, "CA", ca_file.name, model_name)

        # Extract Contractor
        print(f"\n[Contractor Report] {contractor_file.name}")
        con_content = contractor_file.read_text(encoding="utf-8", errors="replace")
        con_report = extract_dwr_with_llm(con_content, model_name)
        display_dwr_summary(con_report, "Contractor")
        db.save_dwr(con_report, "Contractor", contractor_file.name, model_name)

        # Reconcile
        recon_results = reconcile_dwrs(ca_report, con_report)
        display_reconciliation(recon_results, co_match)

        # Save reconciliation to database
        try:
            with sqlite3.connect(db.db_path) as conn:
                cursor = conn.cursor()
                for item in recon_results:
                    cursor.execute('''
                        INSERT INTO reconciliation
                        (change_order, work_date, ca_record_id, contractor_record_id,
                         category, description, ca_value, contractor_value,
                         unit, variance_pct, status, notes)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (co_match, ca_report.header.dwr_date,
                          ca_report.header.record_id, con_report.header.record_id,
                          item['category'], item['description'],
                          item['ca_value'], item['contractor_value'],
                          item['unit'], item['variance_pct'],
                          item['status'], item.get('notes')))
                conn.commit()
                print(f"\n  ✓ Reconciliation saved to database")
        except sqlite3.Error as e:
            print(f"\n  ❌ Failed to save reconciliation: {e}")

    print(f"\n{'=' * 70}")
    print(f"✅ EXTRACTION AND RECONCILIATION COMPLETE")
    print(f"{'=' * 70}")
    return 0


if __name__ == "__main__":
    exit_code = main()

    exit(exit_code)
