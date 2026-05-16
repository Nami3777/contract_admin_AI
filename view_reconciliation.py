"""
View Reconciliation Results from Contract Administration Database

Queries the contract_admin.db created by extract_final.py and displays:
- DWR extraction summaries (CA vs Contractor)
- Reconciliation comparisons by change order
- Variance analysis with FLAGS
- Summary statistics

Usage: python view_reconciliation.py
"""

import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime


class ReconciliationDatabase:
    """Query and display reconciliation data from contract administration"""
    
    def __init__(self, db_path: str = "contract_admin.db"):
        self.db_path = Path(db_path)
        
        if not self.db_path.exists():
            print(f"⚠️  Database not found: {self.db_path}")
            print("💡 Run extract_final.py first to create and populate the database")
            raise FileNotFoundError(f"Database file not found: {self.db_path}")
    
    def get_all_dwrs(self) -> List[Dict[str, Any]]:
        """Retrieve all DWR headers"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    record_id, contract_no, contractor, created_by,
                    dwr_date, from_time, to_time, status, change_order,
                    source_type, pdf_source, extraction_timestamp
                FROM dwr_headers
                ORDER BY dwr_date DESC, extraction_timestamp DESC
            ''')
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_dwr_details(self, record_id: str) -> Dict[str, Any]:
        """Get complete DWR with all line items"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get header
            cursor.execute('''
                SELECT * FROM dwr_headers WHERE record_id = ?
            ''', (record_id,))
            header = dict(cursor.fetchone())
            
            # Get labour
            cursor.execute('''
                SELECT * FROM labour_items WHERE dwr_record_id = ?
            ''', (record_id,))
            labour = [dict(row) for row in cursor.fetchall()]
            
            # Get equipment
            cursor.execute('''
                SELECT * FROM equipment_items WHERE dwr_record_id = ?
            ''', (record_id,))
            equipment = [dict(row) for row in cursor.fetchall()]
            
            # Get materials
            cursor.execute('''
                SELECT * FROM material_items WHERE dwr_record_id = ?
            ''', (record_id,))
            materials = [dict(row) for row in cursor.fetchall()]
            
            return {
                'header': header,
                'labour': labour,
                'equipment': equipment,
                'materials': materials
            }
    
    def get_reconciliation_by_co(self, change_order: str) -> List[Dict[str, Any]]:
        """Get all reconciliation items for a specific change order"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    category, description, 
                    ca_value, contractor_value,
                    unit, variance_pct, status, notes,
                    work_date, ca_record_id, contractor_record_id
                FROM reconciliation
                WHERE change_order = ?
                ORDER BY 
                    CASE status
                        WHEN 'FLAG' THEN 1
                        WHEN 'NEW' THEN 2
                        WHEN 'MISSING' THEN 3
                        WHEN 'MATCH' THEN 4
                    END,
                    category, description
            ''', (change_order,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_all_change_orders(self) -> List[str]:
        """Get list of all change orders in database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT DISTINCT change_order 
                FROM reconciliation 
                WHERE change_order IS NOT NULL
                ORDER BY change_order
            ''')
            return [row[0] for row in cursor.fetchall()]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Calculate summary statistics"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            stats = {}
            
            # Total DWRs
            cursor.execute("SELECT COUNT(*) FROM dwr_headers")
            stats['total_dwrs'] = cursor.fetchone()[0]
            
            # By source type
            cursor.execute('''
                SELECT source_type, COUNT(*) as count 
                FROM dwr_headers 
                GROUP BY source_type
            ''')
            stats['by_source'] = dict(cursor.fetchall())
            
            # Total reconciliation items
            cursor.execute("SELECT COUNT(*) FROM reconciliation")
            stats['total_items'] = cursor.fetchone()[0]
            
            # By status
            cursor.execute('''
                SELECT status, COUNT(*) as count 
                FROM reconciliation 
                GROUP BY status
            ''')
            stats['by_status'] = dict(cursor.fetchall())
            
            # Change orders processed
            cursor.execute('''
                SELECT COUNT(DISTINCT change_order) 
                FROM reconciliation
            ''')
            stats['change_orders'] = cursor.fetchone()[0]
            
            # Latest extraction
            cursor.execute('''
                SELECT MAX(extraction_timestamp) 
                FROM dwr_headers
            ''')
            latest = cursor.fetchone()[0]
            stats['latest_extraction'] = latest if latest else "No data"
            
            return stats


# ============================================================
# Display Functions
# ============================================================

def print_dwr_summary(dwr: Dict[str, Any]):
    """Pretty print a single DWR summary"""
    h = dwr['header']
    source_emoji = "🔵" if h['source_type'] == "CA" else "🟠"
    
    print(f"\n{source_emoji} {h['record_id']} ({h['source_type']})")
    print(f"   Date: {h['dwr_date']} | Time: {h['from_time']}-{h['to_time']}")
    print(f"   Created by: {h['created_by']}")
    print(f"   Change Order: {h['change_order'] or 'N/A'}")
    
    total_labour = sum(item['total_man_hours'] for item in dwr['labour'] if item['total_man_hours'])
    total_equipment = sum(item['hours_worked'] for item in dwr['equipment'] if item['hours_worked'])
    
    if dwr['labour']:
        print(f"   Labour: {len(dwr['labour'])} items, {total_labour:.1f} total man-hours")
    if dwr['equipment']:
        print(f"   Equipment: {len(dwr['equipment'])} items, {total_equipment:.1f} total hours")
    if dwr['materials']:
        print(f"   Materials: {len(dwr['materials'])} items")


def print_reconciliation_table(items: List[Dict[str, Any]], change_order: str):
    """Pretty print reconciliation comparison table"""
    
    flags = [i for i in items if i['status'] == 'FLAG']
    matches = [i for i in items if i['status'] == 'MATCH']
    new_items = [i for i in items if i['status'] == 'NEW']
    missing = [i for i in items if i['status'] == 'MISSING']
    
    print(f"\n{'=' * 90}")
    print(f"📊 RECONCILIATION: {change_order}")
    print(f"{'=' * 90}")
    print(f"\n  Summary: ✅ {len(matches)} MATCH | 🚨 {len(flags)} FLAG | "
          f"🆕 {len(new_items)} NEW | ❓ {len(missing)} MISSING")
    
    if not items:
        print("\n  ⚠️  No reconciliation data found")
        return
    
    # Display table header
    print(f"\n  {'Category':<12} {'Description':<35} {'CA':>10} {'Contr':>10} {'Var%':>8} {'Status':<8}")
    print(f"  {'-' * 90}")
    
    # Display items
    for item in items:
        ca_val = f"{item['ca_value']:.1f}" if item['ca_value'] is not None else "—"
        con_val = f"{item['contractor_value']:.1f}" if item['contractor_value'] is not None else "—"
        var_pct = f"{item['variance_pct']:+.1f}%" if item['variance_pct'] is not None else "—"
        
        emoji = {
            'FLAG': '🚨',
            'MATCH': '✅',
            'NEW': '🆕',
            'MISSING': '❓'
        }.get(item['status'], '⚪')
        
        desc = item['description'][:33]
        cat = item['category'][:10]
        
        print(f"  {cat:<12} {desc:<35} {ca_val:>10} {con_val:>10} {var_pct:>8} {emoji} {item['status']:<8}")
        
        # Show notes for important statuses
        if item.get('notes') and item['status'] in ('FLAG', 'NEW', 'MISSING'):
            note_text = item['notes'][:70]
            print(f"  {'':>12} 💬 {note_text}")


def print_statistics(stats: Dict[str, Any]):
    """Pretty print database statistics"""
    print("\n" + "=" * 70)
    print("📊 DATABASE STATISTICS")
    print("=" * 70)
    
    print(f"\n📄 Total DWRs: {stats['total_dwrs']}")
    
    if stats.get('by_source'):
        print(f"\n📋 By Source:")
        for source, count in stats['by_source'].items():
            emoji = "🔵" if source == "CA" else "🟠"
            print(f"   {emoji} {source}: {count}")
    
    print(f"\n🔗 Change Orders: {stats['change_orders']}")
    print(f"📊 Total Line Items: {stats['total_items']}")
    
    if stats.get('by_status'):
        print(f"\n🎯 Reconciliation Status:")
        status_order = ['MATCH', 'FLAG', 'NEW', 'MISSING']
        for status in status_order:
            count = stats['by_status'].get(status, 0)
            if count > 0:
                emoji = {'MATCH': '✅', 'FLAG': '🚨', 'NEW': '🆕', 'MISSING': '❓'}.get(status, '⚪')
                print(f"   {emoji} {status}: {count}")
    
    print(f"\n🕒 Latest Extraction: {stats['latest_extraction']}")
    print("=" * 70)


# ============================================================
# Main Entry Point
# ============================================================

def main():
    """Display reconciliation results from database"""
    
    try:
        db = ReconciliationDatabase()
    except FileNotFoundError:
        return 1
    
    # Get statistics
    try:
        stats = db.get_statistics()
    except Exception as e:
        print(f"❌ Database query failed: {e}")
        return 1
    
    # Display statistics
    print_statistics(stats)
    
    # Get all change orders
    change_orders = db.get_all_change_orders()
    
    if not change_orders:
        print("\n⚠️  No reconciliation data found")
        print("💡 Run extract_final.py to process DWR pairs")
        return 1
    
    # Display reconciliation for each change order
    for co in change_orders:
        items = db.get_reconciliation_by_co(co)
        print_reconciliation_table(items, co)
    
    # Display DWR summaries
    print("\n" + "=" * 70)
    print("📄 DWR EXTRACTION SUMMARIES")
    print("=" * 70)
    
    dwrs = db.get_all_dwrs()
    for dwr_header in dwrs:
        try:
            dwr = db.get_dwr_details(dwr_header['record_id'])
            print_dwr_summary(dwr)
        except Exception as e:
            print(f"⚠️  Could not load details for {dwr_header['record_id']}: {e}")
    
    print("\n" + "=" * 70)
    print(f"✅ Query complete: {len(change_orders)} change order(s) reconciled")
    print("=" * 70)
    
    return 0


if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
