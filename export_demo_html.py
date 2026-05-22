"""
Export Reconciliation Data to Complete HTML Demo

Reads contract_admin.db and generates a complete HTML file with:
- Real reconciliation data embedded as JavaScript
- Professional dark theme styling preserved
- Dynamic tables, metrics, and metadata
- Static narrative and pipeline sections

Output: reconciliation_demo_live.html
Usage: python export_demo_html.py
"""

import sqlite3
import json
from pathlib import Path
from typing import List, Dict, Any, Tuple
from datetime import datetime


class ReconciliationHTMLExporter:
    """Export reconciliation data to complete HTML demo"""
    
    def __init__(self, db_path: str = "contract_admin.db"):
        self.db_path = Path(db_path)
        
        if not self.db_path.exists():
            raise FileNotFoundError(f"❌ Database not found: {self.db_path}")
    
    def get_project_metadata(self) -> Dict[str, Any]:
        """Extract project-level metadata from first DWR"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT contract_no, contractor, region, highway
                FROM dwr_headers
                LIMIT 1
            ''')
            row = cursor.fetchone()
            
            if not row:
                return {
                    'contract_no': '2020-4091',
                    'contractor': 'Anonymized',
                    'region': 'Ontario',
                    'highway': 'Unknown'
                }
            
            return dict(row)
    
    def get_summary_metrics(self) -> Dict[str, Any]:
        """Calculate executive summary metrics"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Total line items
            cursor.execute("SELECT COUNT(*) FROM reconciliation")
            total_items = cursor.fetchone()[0]
            
            # By status
            cursor.execute('''
                SELECT status, COUNT(*) as count
                FROM reconciliation
                GROUP BY status
            ''')
            by_status = dict(cursor.fetchall())
            
            # Change orders
            cursor.execute('''
                SELECT COUNT(DISTINCT change_order)
                FROM reconciliation
            ''')
            total_cos = cursor.fetchone()[0]
            
            matches = by_status.get('MATCH', 0)
            flags = by_status.get('FLAG', 0)
            new_items = by_status.get('NEW', 0)
            missing = by_status.get('MISSING', 0)
            
            reconciled = matches + flags
            progress_ratio = f"{reconciled}/{total_items}" if total_items > 0 else "0/0"
            progress_pct = int((reconciled / total_items * 100)) if total_items > 0 else 0
            
            return {
                'total_line_items': total_items,
                'total_change_orders': total_cos,
                'matches': matches,
                'flags': flags,
                'new_items': new_items,
                'missing': missing,
                'reconciliation_progress': progress_ratio,
                'reconciliation_pct': progress_pct,
                'audit_trail_status': 'Complete' if total_items > 0 else 'No Data'
            }
    
    def get_change_order_priority(self, change_order: str) -> Tuple[int, int, int]:
        """
        Calculate priority for tab ordering.
        Returns: (priority_class, flag_count, item_count)
        Priority: FLAGS > NEW items > Most items
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Count flags
            cursor.execute('''
                SELECT COUNT(*) FROM reconciliation
                WHERE change_order = ? AND status = 'FLAG'
            ''', (change_order,))
            flags = cursor.fetchone()[0]
            
            # Count new items
            cursor.execute('''
                SELECT COUNT(*) FROM reconciliation
                WHERE change_order = ? AND status = 'NEW'
            ''', (change_order,))
            new_items = cursor.fetchone()[0]
            
            # Total items
            cursor.execute('''
                SELECT COUNT(*) FROM reconciliation
                WHERE change_order = ?
            ''', (change_order,))
            total = cursor.fetchone()[0]
            
            # Priority class: 1=has flags, 2=has new items, 3=only matches
            if flags > 0:
                priority = 1
            elif new_items > 0:
                priority = 2
            else:
                priority = 3
            
            return (priority, -flags, -total)  # Negative for descending sort
    
    def get_change_orders_sorted(self, max_tabs: int = 5) -> List[str]:
        """Get change orders sorted by priority, limited to max_tabs"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT DISTINCT change_order
                FROM reconciliation
                WHERE change_order IS NOT NULL
                ORDER BY change_order
            ''')
            all_cos = [row[0] for row in cursor.fetchall()]
        
        # Sort by priority
        co_with_priority = [(co, self.get_change_order_priority(co)) for co in all_cos]
        co_with_priority.sort(key=lambda x: x[1])
        
        # Take top N
        return [co for co, _ in co_with_priority[:max_tabs]]
    
    def get_change_order_data(self, change_order: str) -> Dict[str, Any]:
        """Get all reconciliation items for a specific change order"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    category, description,
                    ca_value, contractor_value,
                    unit, variance_pct, status, notes
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
            
            items = []
            for row in cursor.fetchall():
                item = dict(row)
                
                # Format for display
                if item['ca_value'] is not None:
                    item['ca_display'] = f"{item['ca_value']:.2f} {item['unit']}"
                else:
                    item['ca_display'] = "—"
                
                if item['contractor_value'] is not None:
                    item['contractor_display'] = f"{item['contractor_value']:.2f} {item['unit']}"
                else:
                    item['contractor_display'] = "—"
                
                if item['variance_pct'] is not None:
                    item['variance_display'] = f"{item['variance_pct']:+.1f}%"
                    item['variance_class'] = 'variance-positive' if item['variance_pct'] > 0 else 'variance-zero'
                else:
                    item['variance_display'] = "—"
                    item['variance_class'] = 'variance-zero'
                
                # CSS classes for status badges
                item['status_class'] = f"status-{item['status'].lower()}"
                
                items.append(item)
            
            return {
                'change_order': change_order,
                'items': items
            }
    
    def generate_html(self, output_path: str = "reconciliation_demo_live.html"):
        """Generate complete HTML file with embedded data"""
        
        print("=" * 70)
        print("📊 GENERATING RECONCILIATION DEMO HTML")
        print("=" * 70)
        
        # Gather data
        print("\n📥 Extracting data from database...")
        metadata = self.get_project_metadata()
        metrics = self.get_summary_metrics()
        change_orders = self.get_change_orders_sorted(max_tabs=5)
        
        if not change_orders:
            print("❌ No reconciliation data found in database")
            print("💡 Run extract_final.py first to process DWR pairs")
            return False
        
        print(f"   ✓ Found {len(change_orders)} change order(s)")
        print(f"   ✓ Total items: {metrics['total_line_items']}")
        print(f"   ✓ Flags: {metrics['flags']}, Matches: {metrics['matches']}")
        
        # Get data for each CO
        co_data = {}
        for co in change_orders:
            co_data[co] = self.get_change_order_data(co)
            print(f"   ✓ {co}: {len(co_data[co]['items'])} items")
        
        # Generate HTML
        print("\n🔨 Building HTML...")
        html = self._build_html_template(metadata, metrics, change_orders, co_data)
        
        # Write file
        output_file = Path(output_path)
        output_file.write_text(html, encoding='utf-8')
        
        print(f"\n✅ Generated: {output_file}")
        print(f"   📊 {metrics['total_line_items']} line items across {len(change_orders)} change orders")
        print(f"   📁 File size: {output_file.stat().st_size / 1024:.1f} KB")
        print("\n💡 Open {output_file.name} in your browser to view the demo")
        print("=" * 70)
        
        return True
    
    def _build_html_template(self, metadata: Dict, metrics: Dict, 
                            change_orders: List[str], co_data: Dict) -> str:
        """Build complete HTML document"""
        
        # Generate tab buttons HTML
        tab_buttons = []
        for i, co in enumerate(change_orders):
            active_class = "active" if i == 0 else ""
            co_items = co_data[co]['items']
            has_flags = any(item['status'] == 'FLAG' for item in co_items)
            status_indicator = "🚨" if has_flags else "✅"
            
            tab_buttons.append(
                f'<button class="tab-btn {active_class}" '
                f'onclick="showTab(\'{co}\')">{co} {status_indicator}</button>'
            )
        
        tabs_html = "\n                ".join(tab_buttons)
        
        # Generate table HTML for each CO
        tables_html = []
        for i, co in enumerate(change_orders):
            display_style = "table" if i == 0 else "none"
            items = co_data[co]['items']
            
            rows_html = []
            for item in items:
                rows_html.append(f'''
                    <tr>
                        <td><span class="status-badge {item['status_class']}">{item['status']}</span></td>
                        <td>{item['category']}</td>
                        <td>{item['description']}</td>
                        <td>{item['ca_display']}</td>
                        <td>{item['contractor_display']}</td>
                        <td class="{item['variance_class']}">{item['variance_display']}</td>
                    </tr>''')
            
            table_html = f'''
            <table id="table-{co}" style="display:{display_style};">
                <thead>
                    <tr>
                        <th>Status</th>
                        <th>Category</th>
                        <th>Description</th>
                        <th>CA Value</th>
                        <th>Contractor Value</th>
                        <th>Variance</th>
                    </tr>
                </thead>
                <tbody>
                    {"".join(rows_html)}
                </tbody>
            </table>'''
            
            tables_html.append(table_html)
        
        all_tables = "\n            ".join(tables_html)
        
        # Build complete HTML
        html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MTO Contract {metadata['contract_no']} — Reconciliation Portfolio</title>
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        html, body {{
            font-family: 'Montserrat', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            line-height: 1.6;
            background: #131313;
            color: #bbbbbb;
            scroll-behavior: smooth;
        }}
        
        /* HEADER / NAVIGATION */
        header {{
            background: #0f0f0f;
            border-bottom: 1px solid #2a2a2a;
            padding: 20px 40px;
            position: sticky;
            top: 0;
            z-index: 100;
        }}
        
        .header-content {{
            max-width: 1400px;
            margin: 0 auto;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        .logo {{
            font-size: 1.2em;
            font-weight: 700;
            color: #ffffff;
            letter-spacing: -0.5px;
        }}
        
        .header-nav {{
            display: flex;
            gap: 30px;
            align-items: center;
        }}
        
        .header-nav a {{
            color: #bbbbbb;
            text-decoration: none;
            font-size: 0.9em;
            font-weight: 500;
            transition: color 0.3s;
        }}
        
        .header-nav a:hover {{
            color: #ffffff;
        }}
        
        /* HERO / PROJECT HEADER */
        .project-hero {{
            background: linear-gradient(135deg, #1a1a1a 0%, #131313 100%);
            padding: 60px 40px;
            border-bottom: 1px solid #2a2a2a;
        }}
        
        .project-hero-content {{
            max-width: 1400px;
            margin: 0 auto;
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 60px;
            align-items: center;
        }}
        
        .project-title-section h1 {{
            font-size: 3em;
            font-weight: 700;
            color: #ffffff;
            margin-bottom: 12px;
            letter-spacing: -1px;
        }}
        
        .project-status {{
            display: inline-block;
            padding: 8px 16px;
            background: #2a2a2a;
            border: 1px solid #3a3a3a;
            border-radius: 4px;
            color: #bbbbbb;
            font-size: 0.85em;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 20px;
        }}
        
        .project-description {{
            color: #999999;
            font-size: 1em;
            line-height: 1.7;
            margin-bottom: 20px;
        }}
        
        .project-metadata {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }}
        
        .metadata-item {{
            background: #1a1a1a;
            padding: 16px;
            border: 1px solid #2a2a2a;
            border-radius: 4px;
        }}
        
        .metadata-label {{
            color: #777777;
            font-size: 0.8em;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 6px;
            font-weight: 600;
        }}
        
        .metadata-value {{
            color: #ffffff;
            font-size: 1.1em;
            font-weight: 700;
        }}
        
        /* EXECUTIVE SUMMARY CARDS */
        .executive-summary {{
            background: #131313;
            padding: 50px 40px;
            border-bottom: 1px solid #2a2a2a;
        }}
        
        .summary-container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        
        .summary-title {{
            font-size: 1.2em;
            font-weight: 700;
            color: #ffffff;
            margin-bottom: 30px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        .summary-cards {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
        }}
        
        .summary-card {{
            background: #1a1a1a;
            border: 1px solid #2a2a2a;
            padding: 24px;
            border-radius: 4px;
            transition: all 0.3s ease;
        }}
        
        .summary-card:hover {{
            border-color: #3a3a3a;
            background: #1f1f1f;
        }}
        
        .card-label {{
            color: #777777;
            font-size: 0.8em;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 12px;
            font-weight: 600;
        }}
        
        .card-value {{
            font-size: 2.4em;
            font-weight: 700;
            color: #ffffff;
            margin-bottom: 8px;
        }}
        
        .card-detail {{
            color: #888888;
            font-size: 0.9em;
        }}
        
        /* PROJECT NARRATIVE */
        .project-narrative {{
            background: #0f0f0f;
            padding: 50px 40px;
            border-bottom: 1px solid #2a2a2a;
        }}
        
        .narrative-container {{
            max-width: 1000px;
            margin: 0 auto;
        }}
        
        .narrative-title {{
            font-size: 1.8em;
            font-weight: 700;
            color: #ffffff;
            margin-bottom: 20px;
            letter-spacing: -0.5px;
        }}
        
        .narrative-text {{
            color: #999999;
            font-size: 1em;
            line-height: 1.8;
            margin-bottom: 16px;
        }}
        
        /* PIPELINE SECTION */
        .pipeline-section {{
            background: #131313;
            padding: 50px 40px;
            border-bottom: 1px solid #2a2a2a;
        }}
        
        .pipeline-container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        
        .section-title {{
            font-size: 1.2em;
            font-weight: 700;
            color: #ffffff;
            margin-bottom: 30px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        .mermaid {{
            background: #1a1a1a;
            padding: 30px;
            border: 1px solid #2a2a2a;
            border-radius: 4px;
            overflow-x: auto;
        }}
        
        /* RECONCILIATION TABLE SECTION */
        .reconciliation-section {{
            background: #0f0f0f;
            padding: 50px 40px;
            border-bottom: 1px solid #2a2a2a;
        }}
        
        .reconciliation-container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        
        .section-tabs {{
            display: flex;
            gap: 10px;
            margin-bottom: 24px;
            flex-wrap: wrap;
            border-bottom: 1px solid #2a2a2a;
        }}
        
        .tab-btn {{
            padding: 12px 20px;
            background: transparent;
            border: none;
            border-bottom: 2px solid transparent;
            cursor: pointer;
            font-weight: 600;
            font-size: 0.9em;
            color: #777777;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            transition: all 0.3s ease;
            font-family: 'Montserrat', sans-serif;
        }}
        
        .tab-btn:hover {{
            color: #ffffff;
        }}
        
        .tab-btn.active {{
            color: #ffffff;
            border-bottom-color: #ffffff;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            background: #1a1a1a;
            border: 1px solid #2a2a2a;
            border-radius: 4px;
            overflow: hidden;
            margin-top: 20px;
        }}
        
        th {{
            background: #0f0f0f;
            color: #ffffff;
            padding: 16px 14px;
            text-align: left;
            font-weight: 700;
            text-transform: uppercase;
            font-size: 0.8em;
            letter-spacing: 0.5px;
            border-bottom: 1px solid #2a2a2a;
        }}
        
        td {{
            padding: 14px;
            border-bottom: 1px solid #2a2a2a;
            color: #bbbbbb;
        }}
        
        tr:last-child td {{
            border-bottom: none;
        }}
        
        tr:hover {{
            background: #252525;
        }}
        
        /* STATUS BADGES */
        .status-badge {{
            display: inline-block;
            padding: 6px 12px;
            border-radius: 4px;
            font-weight: 700;
            font-size: 0.75em;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        .status-flag {{
            background: rgba(204, 0, 0, 0.15);
            color: #ff6b6b;
            border: 1px solid rgba(204, 0, 0, 0.3);
        }}
        
        .status-match {{
            background: rgba(40, 167, 69, 0.15);
            color: #51cf66;
            border: 1px solid rgba(40, 167, 69, 0.3);
        }}
        
        .status-new {{
            background: rgba(0, 123, 255, 0.15);
            color: #74c0fc;
            border: 1px solid rgba(0, 123, 255, 0.3);
        }}
        
        .status-missing {{
            background: rgba(255, 193, 7, 0.15);
            color: #ffd43b;
            border: 1px solid rgba(255, 193, 7, 0.3);
        }}
        
        .variance-positive {{
            color: #ff6b6b;
            font-weight: 700;
        }}
        
        .variance-zero {{
            color: #51cf66;
            font-weight: 700;
        }}
        
        .value-missing {{
            color: #666666;
            font-style: italic;
        }}
        
        /* FOOTER */
        footer {{
            background: #0f0f0f;
            border-top: 1px solid #2a2a2a;
            padding: 40px;
        }}
        
        .footer-content {{
            max-width: 1400px;
            margin: 0 auto;
            text-align: center;
        }}
        
        .footer-text {{
            color: #666666;
            font-size: 0.9em;
            margin-bottom: 12px;
        }}
        
        .footer-link {{
            color: #888888;
            text-decoration: none;
            transition: color 0.3s;
        }}
        
        .footer-link:hover {{
            color: #ffffff;
        }}
        
        /* RESPONSIVE */
        @media (max-width: 1024px) {{
            .project-hero-content {{
                grid-template-columns: 1fr;
                gap: 30px;
            }}
            
            .project-title-section h1 {{
                font-size: 2.2em;
            }}
            
            .summary-cards {{
                grid-template-columns: repeat(2, 1fr);
            }}
        }}
        
        @media (max-width: 768px) {{
            header {{
                padding: 16px 20px;
            }}
            
            .header-content {{
                flex-direction: column;
                gap: 16px;
            }}
            
            .project-hero {{
                padding: 40px 20px;
            }}
            
            .project-title-section h1 {{
                font-size: 1.8em;
            }}
            
            .project-metadata {{
                grid-template-columns: 1fr;
            }}
            
            .summary-cards {{
                grid-template-columns: 1fr;
            }}
            
            .executive-summary,
            .pipeline-section,
            .reconciliation-section,
            .project-narrative {{
                padding: 40px 20px;
            }}
            
            .section-tabs {{
                gap: 8px;
            }}
            
            .tab-btn {{
                padding: 10px 14px;
                font-size: 0.8em;
            }}
            
            table {{
                font-size: 0.85em;
            }}
            
            th, td {{
                padding: 10px 8px;
            }}
        }}
    </style>
</head>
<body>
    <!-- HEADER -->
    <header>
        <div class="header-content">
            <div class="logo">Contract Reconciliation</div>
            <nav class="header-nav">
                <a href="#overview">Overview</a>
                <a href="#pipeline">Pipeline</a>
                <a href="#data">Data</a>
                <a href="#github">GitHub</a>
            </nav>
        </div>
    </header>
    
    <!-- PROJECT HERO -->
    <section class="project-hero">
        <div class="project-hero-content">
            <div class="project-title-section">
                <span class="project-status">Active Project</span>
                <h1>MTO Contract {metadata['contract_no']}</h1>
                <p class="project-description">Automated reconciliation and variance analysis for Ministry of Transportation contract administration, comparing contractor daily work reports against contract administrator records.</p>
            </div>
            <div class="project-metadata">
                <div class="metadata-item">
                    <div class="metadata-label">Location</div>
                    <div class="metadata-value">{metadata['region']}, Canada</div>
                </div>
                <div class="metadata-item">
                    <div class="metadata-label">Contractor</div>
                    <div class="metadata-value">{metadata['contractor']}</div>
                </div>
                <div class="metadata-item">
                    <div class="metadata-label">Highway</div>
                    <div class="metadata-value">{metadata.get('highway', 'N/A')}</div>
                </div>
                <div class="metadata-item">
                    <div class="metadata-label">Status</div>
                    <div class="metadata-value">In Review</div>
                </div>
            </div>
        </div>
    </section>
    
    <!-- EXECUTIVE SUMMARY -->
    <section class="executive-summary" id="overview">
        <div class="summary-container">
            <div class="summary-title">Project Metrics</div>
            <div class="summary-cards">
                <div class="summary-card">
                    <div class="card-label">Total Line Items</div>
                    <div class="card-value">{metrics['total_line_items']}</div>
                    <div class="card-detail">Across {metrics['total_change_orders']} change orders</div>
                </div>
                <div class="summary-card">
                    <div class="card-label">Reconciliation Progress</div>
                    <div class="card-value">{metrics['reconciliation_progress']}</div>
                    <div class="card-detail">{metrics['reconciliation_pct']}% matched or reviewed</div>
                </div>
                <div class="summary-card">
                    <div class="card-label">Flagged Items</div>
                    <div class="card-value">{metrics['flags']}</div>
                    <div class="card-detail">Require manual review</div>
                </div>
                <div class="summary-card">
                    <div class="card-label">Audit Trail</div>
                    <div class="card-value">{metrics['audit_trail_status']}</div>
                    <div class="card-detail">All records documented</div>
                </div>
            </div>
        </div>
    </section>
    
    <!-- PROJECT NARRATIVE -->
    <section class="project-narrative">
        <div class="narrative-container">
            <h2 class="narrative-title">Project Overview</h2>
            <p class="narrative-text">This reconciliation project addresses a critical challenge in construction contract administration: ensuring accurate alignment between contractor daily work reports (DWRs) and contract administrator (CA) records. The Ministry of Transportation requires precise documentation of labor hours, equipment usage, and material quantities to maintain compliance with regulatory standards and cost control objectives.</p>
            <p class="narrative-text">The automated reconciliation pipeline processes multiple DWR pairs, standardizes data using Pydantic V2 validation, and applies variance analysis with a ±5% threshold. Items exceeding this threshold are flagged for manual review, ensuring that only legitimate variances are recorded and that cost control measures remain effective throughout the project lifecycle.</p>
            <p class="narrative-text">This portfolio demonstrates the technical sophistication required for enterprise-grade contract administration, combining natural language processing, data standardization, and compliance-focused reporting into a single, auditable system.</p>
        </div>
    </section>
    
    <!-- PIPELINE VISUALIZATION -->
    <section class="pipeline-section" id="pipeline">
        <div class="pipeline-container">
            <h2 class="section-title">Reconciliation Pipeline</h2>
            <div class="mermaid">
                graph LR
                    A["CA Daily Work Report<br/>DWR-007"] -->|Extract & Validate| B["Standardize Data<br/>Pydantic V2"]
                    C["Contractor Report<br/>DWR-009"] -->|Extract & Validate| B
                    B -->|Compare Line Items| D["Variance Analysis<br/>Llama 3.2 Local"]
                    D -->|Apply Threshold| E["Flag Review<br/>±5% Tolerance"]
                    E -->|Generate Report| F["Reconciliation Output<br/>Change Order"]
            </div>
        </div>
    </section>
    
    <!-- RECONCILIATION DATA -->
    <section class="reconciliation-section" id="data">
        <div class="reconciliation-container">
            <h2 class="section-title">Reconciliation Data</h2>
            
            <div class="section-tabs">
                {tabs_html}
            </div>
            
            {all_tables}
        </div>
    </section>
    
    <!-- FOOTER -->
    <footer>
        <div class="footer-content">
            <p class="footer-text">Contract Reconciliation System — Built with Python, Pydantic V2, Ollama/Llama 3.2</p>
            <p class="footer-text"><a href="https://github.com/yourusername/contract-admin-ai" class="footer-link" id="github">View on GitHub</a></p>
            <p class="footer-text" style="font-size: 0.8em; color: #555555; margin-top: 16px;">© 2025 Contract Administration Portfolio. All rights reserved.</p>
        </div>
    </footer>
    
    <script>
        // Initialize Mermaid
        mermaid.initialize({{ 
            startOnLoad: true,
            theme: 'dark',
            themeVariables: {{
                primaryColor: '#2a2a2a',
                primaryTextColor: '#ffffff',
                primaryBorderColor: '#3a3a3a',
                lineColor: '#3a3a3a',
                secondaryColor: '#1a1a1a',
                tertiaryColor: '#131313',
                fontSize: '14px',
                fontFamily: 'Montserrat, sans-serif'
            }},
            flowchart: {{
                useMaxWidth: true,
                htmlLabels: true,
                curve: 'basis'
            }}
        }});
        
        // Tab switching
        function showTab(tabId) {{
            // Hide all tables
            const tables = document.querySelectorAll('table[id^="table-"]');
            tables.forEach(table => table.style.display = 'none');
            
            // Show selected table
            const selectedTable = document.getElementById('table-' + tabId);
            if (selectedTable) {{
                selectedTable.style.display = 'table';
            }}
            
            // Update button states
            document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
            event.target.classList.add('active');
        }}
    </script>
</body>
</html>'''
        
        return html


# ============================================================
# Main Entry Point
# ============================================================

def main():
    """Generate HTML demo from database"""
    
    try:
        exporter = ReconciliationHTMLExporter()
    except FileNotFoundError as e:
        print(str(e))
        print("\n💡 To generate the demo:")
        print("   1. Run: python ingest_pymupdf.py")
        print("   2. Run: python extract_final.py")
        print("   3. Run: python export_demo_html.py")
        return 1
    
    success = exporter.generate_html()
    
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
