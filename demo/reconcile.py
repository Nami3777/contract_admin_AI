"""
Reconciliation Engine for DWR Comparison

Pure Python logic to compare CA (Inspector) vs Contractor DWRs.
This is Layer 3 of the pipeline - deterministic comparison, no AI.

Key principle: AI extracts the data, Python does the math.
"""

import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field


# ============================================================
# Data Structures (mirrors schemas.py but simpler for parsing)
# ============================================================

@dataclass
class ParsedLineItem:
    """Generic line item extracted from markdown"""
    category: str  # "Labour", "Equipment", "Material"
    description: str  # Classification or equipment name
    value: float  # Hours or quantity
    unit: str = "hours"
    remarks: str = ""


@dataclass
class ParsedDWR:
    """Parsed DWR document"""
    record_id: str = ""
    created_by: str = ""
    dwr_date: str = ""
    change_order: str = ""
    from_time: str = ""
    to_time: str = ""
    source_type: str = ""  # "CA" or "Contractor"
    labour: List[ParsedLineItem] = field(default_factory=list)
    equipment: List[ParsedLineItem] = field(default_factory=list)
    materials: List[ParsedLineItem] = field(default_factory=list)


@dataclass
class ReconciliationItem:
    """Single comparison result"""
    category: str
    description: str
    ca_value: Optional[float]
    contractor_value: Optional[float]
    unit: str
    variance_pct: Optional[float]
    status: str  # "MATCH", "FLAG", "NEW", "MISSING"
    notes: str = ""


@dataclass
class ReconciliationResult:
    """Complete reconciliation output"""
    change_order: str
    work_date: str
    ca_record_id: str
    contractor_record_id: str
    ca_created_by: str
    contractor_created_by: str
    items: List[ReconciliationItem] = field(default_factory=list)
    
    @property
    def flags_count(self) -> int:
        return sum(1 for item in self.items if item.status == "FLAG")
    
    @property
    def matches_count(self) -> int:
        return sum(1 for item in self.items if item.status == "MATCH")
    
    @property
    def new_count(self) -> int:
        return sum(1 for item in self.items if item.status == "NEW")
    
    @property
    def missing_count(self) -> int:
        return sum(1 for item in self.items if item.status == "MISSING")


# ============================================================
# Markdown Parsing
# ============================================================

def parse_header_value(content: str, field_name: str) -> str:
    """Extract a value from the header table"""
    pattern = rf"\|\s*{re.escape(field_name)}\s*\|\s*([^|]+)\s*\|"
    match = re.search(pattern, content, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return ""


def parse_change_order(content: str) -> str:
    """Extract linked change order number"""
    # Pattern: "2020-4091-CO-21" or just "CO-21"
    pattern = r"(?:2020-4091-)?(CO-\d+)"
    match = re.search(pattern, content)
    if match:
        return match.group(1)
    return ""


def parse_table_section(content: str, section_name: str) -> List[List[str]]:
    """Extract rows from a markdown table section"""
    # Find the section
    pattern = rf"##\s*{re.escape(section_name)}.*?\n\n(.*?)(?=\n##|\Z)"
    match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
    if not match:
        return []
    
    section = match.group(1)
    rows = []
    
    for line in section.split('\n'):
        line = line.strip()
        if line.startswith('|') and not line.startswith('|---') and not line.startswith('| Field'):
            # Split by | and clean up
            cells = [cell.strip() for cell in line.split('|')[1:-1]]
            if cells and len(cells) > 1:
                # Skip header row (check if first cell looks like a header)
                if cells[0] not in ['Classification', 'Equipment Name', 'Material', 
                                    'Temperature (C)', 'No']:
                    rows.append(cells)
    
    return rows


def parse_labour_table(content: str) -> List[ParsedLineItem]:
    """Parse the Labour section"""
    items = []
    rows = parse_table_section(content, "Labour")
    
    for row in rows:
        if len(row) >= 6:
            try:
                classification = row[0]
                # Total man hours is typically in column 5 (0-indexed)
                total_hours = float(row[5]) if row[5] else 0.0
                remarks = row[7] if len(row) > 7 else ""
                
                items.append(ParsedLineItem(
                    category="Labour",
                    description=classification,
                    value=total_hours,
                    unit="man-hours",
                    remarks=remarks
                ))
            except (ValueError, IndexError):
                continue
    
    return items


def parse_equipment_table(content: str) -> List[ParsedLineItem]:
    """Parse the Equipment section"""
    items = []
    rows = parse_table_section(content, "Equipment")
    
    for row in rows:
        if len(row) >= 4:
            try:
                equipment_name = row[0]
                # Hours worked is typically in column 3
                hours = float(row[3]) if row[3] else 0.0
                remarks = row[7] if len(row) > 7 else ""
                
                items.append(ParsedLineItem(
                    category="Equipment",
                    description=equipment_name,
                    value=hours,
                    unit="hours",
                    remarks=remarks
                ))
            except (ValueError, IndexError):
                continue
    
    return items


def parse_materials_table(content: str) -> List[ParsedLineItem]:
    """Parse the Material Supplied by Contractor section"""
    items = []
    rows = parse_table_section(content, "Material Supplied by Contractor")
    
    for row in rows:
        if len(row) >= 4:
            try:
                material = row[0]
                description = row[1] if len(row) > 1 else ""
                units = row[2] if len(row) > 2 else ""
                quantity = float(row[3]) if row[3] else 0.0
                
                full_desc = f"{material} - {description}" if description else material
                
                items.append(ParsedLineItem(
                    category="Material",
                    description=full_desc,
                    value=quantity,
                    unit=units,
                ))
            except (ValueError, IndexError):
                continue
    
    return items


def parse_dwr_markdown(content: str, filename: str = "") -> ParsedDWR:
    """Parse a complete DWR markdown file"""
    dwr = ParsedDWR()
    
    # Extract header info
    dwr.record_id = parse_header_value(content, "Record ID")
    dwr.created_by = parse_header_value(content, "Created by")
    dwr.dwr_date = parse_header_value(content, "DWR Date")
    dwr.from_time = parse_header_value(content, "From Time \\(24 Hr\\)")
    dwr.to_time = parse_header_value(content, "To Time \\(24 Hr\\)")
    dwr.change_order = parse_change_order(content)
    
    # Determine source type from filename or content
    if "__CA__" in filename or "Inspector" in dwr.created_by:
        dwr.source_type = "CA"
    elif "__Contractor__" in filename:
        dwr.source_type = "Contractor"
    else:
        # Check for T&M status in content (Contractor indicator)
        if "| T&M |" in content:
            dwr.source_type = "Contractor"
        else:
            dwr.source_type = "CA"
    
    # Parse tables
    dwr.labour = parse_labour_table(content)
    dwr.equipment = parse_equipment_table(content)
    dwr.materials = parse_materials_table(content)
    
    return dwr


# ============================================================
# Reconciliation Logic
# ============================================================

def normalize_description(desc: str) -> str:
    """Normalize description for matching (lowercase, remove extra spaces)"""
    return re.sub(r'\s+', ' ', desc.lower().strip())


def calculate_variance(ca_value: float, contractor_value: float) -> Tuple[float, str]:
    """
    Calculate variance percentage and determine status.
    
    Returns: (variance_pct, status)
    Status: "MATCH" if within 5%, "FLAG" if exceeds 5%
    """
    if ca_value == 0 and contractor_value == 0:
        return 0.0, "MATCH"
    
    if ca_value == 0:
        # CA has zero, contractor has value - treat as significant
        return 100.0, "FLAG"
    
    variance_pct = ((contractor_value - ca_value) / ca_value) * 100
    
    if abs(variance_pct) <= 5.0:
        return variance_pct, "MATCH"
    else:
        return variance_pct, "FLAG"


def match_items(
    ca_items: List[ParsedLineItem],
    contractor_items: List[ParsedLineItem]
) -> List[ReconciliationItem]:
    """
    Match line items between CA and Contractor reports.
    Uses normalized description matching.
    """
    results = []
    
    # Create lookup by normalized description
    ca_lookup: Dict[str, ParsedLineItem] = {
        normalize_description(item.description): item 
        for item in ca_items
    }
    contractor_lookup: Dict[str, ParsedLineItem] = {
        normalize_description(item.description): item 
        for item in contractor_items
    }
    
    # Track which items have been matched
    matched_contractor_keys = set()
    
    # Process CA items - find matches in Contractor
    for ca_key, ca_item in ca_lookup.items():
        if ca_key in contractor_lookup:
            # Found match
            con_item = contractor_lookup[ca_key]
            matched_contractor_keys.add(ca_key)
            
            variance_pct, status = calculate_variance(ca_item.value, con_item.value)
            
            notes = ""
            if status == "FLAG":
                diff = con_item.value - ca_item.value
                notes = f"Contractor claims {diff:+.2f} {ca_item.unit} more than CA"
            
            results.append(ReconciliationItem(
                category=ca_item.category,
                description=ca_item.description,
                ca_value=ca_item.value,
                contractor_value=con_item.value,
                unit=ca_item.unit,
                variance_pct=variance_pct,
                status=status,
                notes=notes
            ))
        else:
            # CA has item, Contractor doesn't
            results.append(ReconciliationItem(
                category=ca_item.category,
                description=ca_item.description,
                ca_value=ca_item.value,
                contractor_value=None,
                unit=ca_item.unit,
                variance_pct=None,
                status="MISSING",
                notes="Present in CA report but missing from Contractor report"
            ))
    
    # Find items only in Contractor (NEW items)
    for con_key, con_item in contractor_lookup.items():
        if con_key not in matched_contractor_keys:
            results.append(ReconciliationItem(
                category=con_item.category,
                description=con_item.description,
                ca_value=None,
                contractor_value=con_item.value,
                unit=con_item.unit,
                variance_pct=None,
                status="NEW",
                notes="New item claimed by Contractor, not in CA report"
            ))
    
    return results


def reconcile_dwrs(ca_dwr: ParsedDWR, contractor_dwr: ParsedDWR) -> ReconciliationResult:
    """
    Perform full reconciliation between CA and Contractor DWRs.
    """
    result = ReconciliationResult(
        change_order=ca_dwr.change_order or contractor_dwr.change_order,
        work_date=ca_dwr.dwr_date or contractor_dwr.dwr_date,
        ca_record_id=ca_dwr.record_id,
        contractor_record_id=contractor_dwr.record_id,
        ca_created_by=ca_dwr.created_by,
        contractor_created_by=contractor_dwr.created_by,
    )
    
    # Reconcile each category
    labour_items = match_items(ca_dwr.labour, contractor_dwr.labour)
    equipment_items = match_items(ca_dwr.equipment, contractor_dwr.equipment)
    material_items = match_items(ca_dwr.materials, contractor_dwr.materials)
    
    result.items = labour_items + equipment_items + material_items
    
    return result


# ============================================================
# File Operations
# ============================================================

def find_dwr_pairs(directory: Path) -> List[Tuple[Path, Path]]:
    """
    Find matching CA + Contractor DWR pairs by filename convention.
    
    Expected format: XXXX-DWR-XXX__CA__YYYY_MM_DD_CO-XX_.md
                    XXXX-DWR-XXX__Contractor__YYYY_MM_DD_CO-XX_.md
    """
    pairs = []
    
    ca_files = list(directory.glob("*__CA__*.md"))
    
    for ca_file in ca_files:
        # Extract the change order from filename
        co_match = re.search(r'(CO-\d+)', ca_file.name)
        if not co_match:
            continue
        
        change_order = co_match.group(1)
        
        # Find matching contractor file
        contractor_pattern = f"*__Contractor__*{change_order}*.md"
        contractor_files = list(directory.glob(contractor_pattern))
        
        if contractor_files:
            pairs.append((ca_file, contractor_files[0]))
    
    return pairs


def reconcile_from_files(ca_path: Path, contractor_path: Path) -> ReconciliationResult:
    """Load and reconcile two DWR files"""
    ca_content = ca_path.read_text(encoding='utf-8')
    contractor_content = contractor_path.read_text(encoding='utf-8')
    
    ca_dwr = parse_dwr_markdown(ca_content, ca_path.name)
    contractor_dwr = parse_dwr_markdown(contractor_content, contractor_path.name)
    
    return reconcile_dwrs(ca_dwr, contractor_dwr)


# ============================================================
# Display Functions
# ============================================================

def print_reconciliation_report(result: ReconciliationResult):
    """Pretty print a reconciliation report to console"""
    print("\n" + "=" * 80)
    print(f"📊 RECONCILIATION REPORT: {result.change_order}")
    print("=" * 80)
    print(f"Work Date: {result.work_date}")
    print(f"CA Report: {result.ca_record_id} (by {result.ca_created_by})")
    print(f"Contractor Report: {result.contractor_record_id} (by {result.contractor_created_by})")
    print("-" * 80)
    print(f"Summary: {result.matches_count} MATCH | {result.flags_count} FLAG | {result.new_count} NEW | {result.missing_count} MISSING")
    print("=" * 80)
    
    # Group by category
    for category in ["Labour", "Equipment", "Material"]:
        category_items = [item for item in result.items if item.category == category]
        if not category_items:
            continue
        
        print(f"\n📋 {category.upper()}")
        print("-" * 60)
        
        for item in category_items:
            status_emoji = {
                "MATCH": "✅",
                "FLAG": "🚨",
                "NEW": "🆕",
                "MISSING": "❓"
            }.get(item.status, "❓")
            
            ca_str = f"{item.ca_value:.2f}" if item.ca_value is not None else "—"
            con_str = f"{item.contractor_value:.2f}" if item.contractor_value is not None else "—"
            var_str = f"{item.variance_pct:+.1f}%" if item.variance_pct is not None else "—"
            
            print(f"  {status_emoji} {item.description}")
            print(f"     CA: {ca_str} {item.unit} | Contractor: {con_str} {item.unit} | Variance: {var_str}")
            if item.notes:
                print(f"     💬 {item.notes}")
    
    print("\n" + "=" * 80)


# ============================================================
# Main Entry Point
# ============================================================

def main():
    """Process all DWR pairs in markdown_output directory"""
    output_dir = Path("markdown_output")
    
    if not output_dir.exists():
        print("❌ markdown_output/ directory not found")
        print("💡 Run python generate_mock_dwr.py first")
        return 1
    
    print("=" * 80)
    print("🔍 DWR RECONCILIATION ENGINE")
    print("=" * 80)
    
    pairs = find_dwr_pairs(output_dir)
    
    if not pairs:
        print("❌ No DWR pairs found")
        return 1
    
    print(f"\n📁 Found {len(pairs)} DWR pair(s) to reconcile\n")
    
    all_results = []
    
    for ca_path, contractor_path in pairs:
        print(f"Processing: {ca_path.name}")
        print(f"         vs {contractor_path.name}")
        
        result = reconcile_from_files(ca_path, contractor_path)
        all_results.append(result)
        print_reconciliation_report(result)
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 OVERALL SUMMARY")
    print("=" * 80)
    total_flags = sum(r.flags_count for r in all_results)
    total_matches = sum(r.matches_count for r in all_results)
    total_new = sum(r.new_count for r in all_results)
    
    print(f"Total pairs processed: {len(all_results)}")
    print(f"Total line items: {total_matches + total_flags + total_new}")
    print(f"  ✅ Matches: {total_matches}")
    print(f"  🚨 Flags: {total_flags}")
    print(f"  🆕 New items: {total_new}")
    
    if total_flags > 0:
        print(f"\n⚠️  {total_flags} items require CA review")
    else:
        print("\n✅ All items reconciled within tolerance")
    
    return 0


if __name__ == "__main__":
    exit(main())
