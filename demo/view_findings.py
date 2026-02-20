"""
Layer 4: Database Query & Display for Construction DWR Reconciliation
Translates view_findings.py for Construction domain.
"""

import sqlite3
from pathlib import Path
from typing import List, Dict, Any


class ReconciliationDatabase:
    """Query and display reconciliation data from the database"""

    def __init__(self, db_path: str = "contract_admin.db"):
        self.db_path = Path(db_path)
        if not self.db_path.exists():
            print(f"⚠️  Database not found: {self.db_path}")
            print("💡 Run extract.py first to create and populate the database")
            raise FileNotFoundError(f"Database file not found: {self.db_path}")

    def get_all_reconciliation(self) -> List[Dict[str, Any]]:
        """Retrieve all reconciliation results"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM reconciliation
                ORDER BY change_order, category, description
            ''')
            return [dict(row) for row in cursor.fetchall()]

    def get_flags(self) -> List[Dict[str, Any]]:
        """Get only flagged discrepancies"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM reconciliation
                WHERE status IN ('FLAG', 'NEW', 'MISSING')
                ORDER BY
                    CASE status
                        WHEN 'FLAG' THEN 1
                        WHEN 'MISSING' THEN 2
                        WHEN 'NEW' THEN 3
                    END,
                    variance_pct DESC
            ''')
            return [dict(row) for row in cursor.fetchall()]

    def get_dwr_summary(self) -> List[Dict[str, Any]]:
        """Get summary of all extracted DWRs"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT
                    h.record_id, h.dwr_date, h.created_by, h.source_type,
                    h.change_order, h.status,
                    (SELECT COUNT(*) FROM labour_items WHERE dwr_record_id = h.record_id) as labour_count,
                    (SELECT SUM(total_man_hours) FROM labour_items WHERE dwr_record_id = h.record_id) as total_labour_hrs,
                    (SELECT COUNT(*) FROM equipment_items WHERE dwr_record_id = h.record_id) as equip_count,
                    (SELECT SUM(hours_worked) FROM equipment_items WHERE dwr_record_id = h.record_id) as total_equip_hrs,
                    (SELECT COUNT(*) FROM material_items WHERE dwr_record_id = h.record_id) as material_count
                FROM dwr_headers h
                ORDER BY h.change_order, h.source_type
            ''')
            return [dict(row) for row in cursor.fetchall()]

    def get_statistics(self) -> Dict[str, Any]:
        """Calculate summary statistics"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            stats = {}

            cursor.execute("SELECT COUNT(*) FROM dwr_headers")
            stats['total_dwrs'] = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(DISTINCT change_order) FROM dwr_headers WHERE change_order IS NOT NULL")
            stats['change_orders'] = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM reconciliation")
            stats['total_line_items'] = cursor.fetchone()[0]

            cursor.execute("SELECT status, COUNT(*) FROM reconciliation GROUP BY status")
            stats['by_status'] = dict(cursor.fetchall())

            cursor.execute("SELECT COUNT(*) FROM reconciliation WHERE status = 'FLAG'")
            stats['flags'] = cursor.fetchone()[0]

            cursor.execute("SELECT MAX(reconciliation_timestamp) FROM reconciliation")
            latest = cursor.fetchone()[0]
            stats['latest_reconciliation'] = latest if latest else "No data"

            return stats

    def get_labour_comparison(self, change_order: str) -> List[Dict[str, Any]]:
        """Get side-by-side labour comparison for a specific change order"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute('''
                SELECT
                    r.description as classification,
                    r.ca_value as ca_hours,
                    r.contractor_value as contractor_hours,
                    r.variance_pct,
                    r.status,
                    r.notes
                FROM reconciliation r
                WHERE r.change_order = ? AND r.category = 'Labour'
                ORDER BY r.description
            ''', (change_order,))
            return [dict(row) for row in cursor.fetchall()]


def print_statistics(stats: Dict[str, Any]):
    """Pretty print database statistics"""
    print(f"\n{'=' * 70}")
    print(f"📊 DATABASE STATISTICS")
    print(f"{'=' * 70}")

    print(f"\n  📈 Total DWRs Extracted: {stats['total_dwrs']}")
    print(f"  📋 Change Orders Covered: {stats['change_orders']}")
    print(f"  📝 Reconciliation Line Items: {stats['total_line_items']}")

    print(f"\n  🎯 Reconciliation Status:")
    status_emoji = {'MATCH': '✅', 'FLAG': '🔴', 'NEW': '🆕', 'MISSING': '❓'}
    for status in ['MATCH', 'FLAG', 'NEW', 'MISSING']:
        count = stats['by_status'].get(status, 0)
        if count > 0:
            print(f"     {status_emoji.get(status, '•')} {status}: {count}")

    print(f"\n  🕒 Latest Reconciliation: {stats['latest_reconciliation']}")
    print(f"{'=' * 70}")


def print_dwr_table(dwrs: List[Dict[str, Any]]):
    """Print DWR summary table"""
    print(f"\n{'=' * 70}")
    print(f"📋 EXTRACTED DWRs")
    print(f"{'=' * 70}")

    print(f"\n  {'Record ID':<25} {'Date':<12} {'Source':<12} {'CO':<8} {'Labour':>7} {'Equip':>6} {'Mat':>4}")
    print(f"  {'─' * 80}")

    for dwr in dwrs:
        source_emoji = "🔍" if dwr['source_type'] == 'CA' else "🏗️"
        print(f"  {dwr['record_id']:<25} {dwr['dwr_date']:<12} "
              f"{source_emoji} {dwr['source_type']:<10} {dwr['change_order'] or 'N/A':<8} "
              f"{dwr['total_labour_hrs'] or 0:>6.1f}h {dwr['total_equip_hrs'] or 0:>5.1f}h "
              f"{dwr['material_count']:>3}")


def print_flags(flags: List[Dict[str, Any]]):
    """Print flagged discrepancies requiring attention"""
    if not flags:
        print(f"\n✅ No discrepancies found — all items reconciled within 5% threshold")
        return

    print(f"\n{'=' * 70}")
    print(f"🚨 DISCREPANCIES REQUIRING REVIEW ({len(flags)} items)")
    print(f"{'=' * 70}")

    print(f"\n  {'CO':<8} {'Category':<12} {'Description':<25} {'CA':>8} {'Contr':>8} {'Var%':>7} {'Status':<8}")
    print(f"  {'─' * 85}")

    for item in flags:
        ca_val = f"{item['ca_value']:.1f}" if item['ca_value'] is not None else "—"
        con_val = f"{item['contractor_value']:.1f}" if item['contractor_value'] is not None else "—"
        var_pct = f"{item['variance_pct']:.1f}%" if item['variance_pct'] is not None else "—"

        emoji = "🔴" if item['status'] == 'FLAG' else "🆕" if item['status'] == 'NEW' else "❓"

        desc = item['description'][:23]
        print(f"  {item['change_order']:<8} {item['category']:<12} {desc:<25} "
              f"{ca_val:>8} {con_val:>8} {var_pct:>7} {emoji} {item['status']}")

        if item.get('notes'):
            print(f"  {'':>8} {'':>12} 📝 {item['notes'][:55]}")


def print_reconciliation_table(items: List[Dict[str, Any]], change_order: str):
    """Print full reconciliation table for a change order"""
    print(f"\n{'=' * 70}")
    print(f"📊 RECONCILIATION DETAIL: {change_order}")
    print(f"{'=' * 70}")

    print(f"\n  {'Category':<12} {'Description':<28} {'CA':>8} {'Contr':>8} {'Var%':>7} {'Status':<8}")
    print(f"  {'─' * 80}")

    for item in items:
        ca_val = f"{item['ca_value']:.1f}" if item['ca_value'] is not None else "—"
        con_val = f"{item['contractor_value']:.1f}" if item['contractor_value'] is not None else "—"
        var_pct = f"{item['variance_pct']:.1f}%" if item['variance_pct'] is not None else "—"

        emoji = "🔴" if item['status'] == 'FLAG' else \
                "✅" if item['status'] == 'MATCH' else \
                "🆕" if item['status'] == 'NEW' else "❓"

        desc = item['description'][:26]
        print(f"  {item['category']:<12} {desc:<28} {ca_val:>8} {con_val:>8} {var_pct:>7} {emoji} {item['status']}")


def main():
    """Display all reconciliation data from database"""
    try:
        db = ReconciliationDatabase()
    except FileNotFoundError:
        return 1

    try:
        stats = db.get_statistics()
        dwrs = db.get_dwr_summary()
        flags = db.get_flags()
        all_items = db.get_all_reconciliation()
    except Exception as e:
        print(f"❌ Database query failed: {e}")
        return 1

    # Display statistics
    print_statistics(stats)

    # Display extracted DWRs
    if dwrs:
        print_dwr_table(dwrs)

    # Display flags
    print_flags(flags)

    # Display full reconciliation by change order
    if all_items:
        change_orders = set(item['change_order'] for item in all_items)
        for co in sorted(change_orders):
            co_items = [item for item in all_items if item['change_order'] == co]
            print_reconciliation_table(co_items, co)

    print(f"\n{'=' * 70}")
    print(f"✓ Query complete: {len(all_items)} reconciliation items displayed")
    print(f"{'=' * 70}")

    return 0


if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)