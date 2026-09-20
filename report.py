"""
report.py
Analytical report generator providing formatted executive HTML reports with built-in print-to-PDF capability.
"""

from datetime import datetime

def generate_html_report(kpis, pandas_analysis, sql_analysis, insights, validation_report):
    """
    Generates a beautifully styled, print-friendly standalone HTML report.
    """
    timestamp = datetime.now().strftime("%B %d, %Y - %I:%M %p")
    
    reg_rows = ""
    for r in pandas_analysis.get('regional_performance', []):
        reg_rows += f"""
        <tr>
            <td><strong>{r['region']}</strong></td>
            <td>{r['total_orders']}</td>
            <td>{r['total_quantity']}</td>
            <td>₹{r['total_sales']:,.2f}</td>
            <td>₹{r['total_profit']:,.2f}</td>
            <td><span class="badge {'positive' if r['profit_margin'] >= 10 else 'neutral'}">{r['profit_margin']}%</span></td>
        </tr>
        """

    cat_rows = ""
    for c in pandas_analysis.get('category_performance', []):
        cat_rows += f"""
        <tr>
            <td><strong>{c['category']}</strong></td>
            <td>{c['total_orders']}</td>
            <td>{c['total_quantity']}</td>
            <td>₹{c['total_sales']:,.2f}</td>
            <td>₹{c['total_profit']:,.2f}</td>
            <td><span class="badge {'positive' if c['profit_margin'] >= 10 else 'neutral'}">{c['profit_margin']}%</span></td>
        </tr>
        """

    prod_rows = ""
    for p in pandas_analysis.get('top_products', []):
        prod_rows += f"""
        <tr>
            <td><strong>{p['product']}</strong></td>
            <td>{p['category']}</td>
            <td>{p['total_quantity']}</td>
            <td>₹{p['total_sales']:,.2f}</td>
            <td>₹{p['total_profit']:,.2f}</td>
            <td><span class="badge {'positive' if p['profit_margin'] >= 10 else ('negative' if p['profit_margin'] < 0 else 'neutral')}">{p['profit_margin']}%</span></td>
        </tr>
        """

    insights_html = ""
    for ins in insights:
        badge_class = ins.get('type', 'info')
        insights_html += f"""
        <div class="insight-box {badge_class}">
            <div class="insight-header">
                <span class="badge {badge_class}">{ins.get('category', 'Insight')}</span>
                <h4>{ins.get('title', '')}</h4>
            </div>
            <p>{ins.get('detail', '')}</p>
        </div>
        """

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Executive Business Analytics Report</title>
    <style>
        :root {{
            --primary: #1e293b;
            --secondary: #0f172a;
            --accent: #2563eb;
            --success: #16a34a;
            --warning: #d97706;
            --danger: #dc2626;
            --bg: #f8fafc;
            --card-bg: #ffffff;
            --border: #e2e8f0;
            --text: #334155;
            --text-heading: #0f172a;
        }}

        body {{
            font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, Helvetica, Arial, sans-serif;
            background-color: var(--bg);
            color: var(--text);
            margin: 0;
            padding: 40px 20px;
            line-height: 1.6;
        }}

        .report-container {{
            max-width: 1000px;
            margin: 0 auto;
            background: var(--card-bg);
            padding: 40px;
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
            border: 1px solid var(--border);
        }}

        .header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 3px solid var(--accent);
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}

        .header h1 {{
            margin: 0;
            font-size: 26px;
            color: var(--text-heading);
            font-weight: 700;
        }}

        .header .meta {{
            text-align: right;
            font-size: 13px;
            color: #64748b;
        }}

        .btn-print {{
            background-color: var(--accent);
            color: white;
            border: none;
            padding: 10px 18px;
            border-radius: 6px;
            font-weight: 600;
            cursor: pointer;
            margin-bottom: 20px;
            float: right;
        }}

        .btn-print:hover {{
            background-color: #1d4ed8;
        }}

        .section-title {{
            font-size: 18px;
            color: var(--text-heading);
            border-left: 4px solid var(--accent);
            padding-left: 12px;
            margin-top: 35px;
            margin-bottom: 18px;
        }}

        .kpi-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
            margin-bottom: 30px;
        }}

        .kpi-card {{
            background: #f1f5f9;
            padding: 18px;
            border-radius: 8px;
            border-left: 4px solid var(--accent);
        }}

        .kpi-card.green {{ border-left-color: var(--success); }}
        .kpi-card.amber {{ border-left-color: var(--warning); }}

        .kpi-label {{
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: #64748b;
            margin-bottom: 4px;
        }}

        .kpi-value {{
            font-size: 22px;
            font-weight: 700;
            color: var(--text-heading);
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 25px;
            font-size: 14px;
        }}

        th, td {{
            padding: 12px 14px;
            text-align: left;
            border-bottom: 1px solid var(--border);
        }}

        th {{
            background-color: #f8fafc;
            color: #475569;
            font-weight: 600;
            text-transform: uppercase;
            font-size: 12px;
        }}

        tr:hover {{
            background-color: #f1f5f9;
        }}

        .badge {{
            display: inline-block;
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 600;
        }}

        .badge.positive {{ background-color: #dcfce7; color: #15803d; }}
        .badge.negative {{ background-color: #fee2e2; color: #b91c1c; }}
        .badge.warning {{ background-color: #fef3c7; color: #b45309; }}
        .badge.neutral, .badge.info {{ background-color: #e0f2fe; color: #0369a1; }}

        .insight-box {{
            background-color: #f8fafc;
            border: 1px solid var(--border);
            border-left: 4px solid var(--accent);
            padding: 16px;
            border-radius: 8px;
            margin-bottom: 14px;
        }}

        .insight-box.positive {{ border-left-color: var(--success); background-color: #f0fdf4; }}
        .insight-box.warning {{ border-left-color: var(--warning); background-color: #fffbeb; }}
        .insight-box.negative {{ border-left-color: var(--danger); background-color: #fef2f2; }}
        .insight-box.info {{ border-left-color: var(--accent); background-color: #eff6ff; }}

        .insight-header {{
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 6px;
        }}

        .insight-header h4 {{
            margin: 0;
            color: var(--text-heading);
            font-size: 15px;
        }}

        .insight-box p {{
            margin: 0;
            font-size: 13.5px;
            color: #475569;
        }}

        .footer {{
            text-align: center;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid var(--border);
            font-size: 12px;
            color: #94a3b8;
        }}

        @media print {{
            body {{
                background-color: white;
                padding: 0;
            }}
            .report-container {{
                box-shadow: none;
                border: none;
                width: 100%;
                max-width: 100%;
                padding: 0;
            }}
            .btn-print {{
                display: none;
            }}
        }}
    </style>
</head>
<body>

    <div class="report-container">
        <button class="btn-print" onclick="window.print()">Print / Save as PDF</button>

        <div class="header">
            <div>
                <h1>Business Analytics Executive Report</h1>
                <div style="font-size: 14px; color: #64748b; margin-top: 4px;">Automated Data & KPI Performance Analysis</div>
            </div>
            <div class="meta">
                <div><strong>Generated:</strong> {timestamp}</div>
                <div><strong>Records Processed:</strong> {validation_report.get('valid_rows', 0)}</div>
                <div><strong>Engine:</strong> Python Pandas + SQLite SQL</div>
            </div>
        </div>

        <h3 class="section-title">1. Executive Key Performance Indicators (KPIs)</h3>
        <div class="kpi-grid">
            <div class="kpi-card green">
                <div class="kpi-label">Total Revenue</div>
                <div class="kpi-value">₹{kpis.get('total_sales', 0):,.2f}</div>
            </div>
            <div class="kpi-card green">
                <div class="kpi-label">Total Net Profit</div>
                <div class="kpi-value">₹{kpis.get('total_profit', 0):,.2f}</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">Profit Margin</div>
                <div class="kpi-value">{kpis.get('profit_margin', 0)}%</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">Total Orders</div>
                <div class="kpi-value">{kpis.get('total_orders', 0)}</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">Average Order Value</div>
                <div class="kpi-value">₹{kpis.get('avg_order_value', 0):,.2f}</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">Total Quantity Sold</div>
                <div class="kpi-value">{kpis.get('total_quantity', 0)}</div>
            </div>
        </div>

        <h3 class="section-title">2. Automated Business Insights</h3>
        {insights_html}

        <h3 class="section-title">3. Regional Performance Analysis</h3>
        <table>
            <thead>
                <tr>
                    <th>Region</th>
                    <th>Orders</th>
                    <th>Units Sold</th>
                    <th>Sales Revenue</th>
                    <th>Net Profit</th>
                    <th>Profit Margin</th>
                </tr>
            </thead>
            <tbody>
                {reg_rows}
            </tbody>
        </table>

        <h3 class="section-title">4. Category Breakdown</h3>
        <table>
            <thead>
                <tr>
                    <th>Category</th>
                    <th>Orders</th>
                    <th>Units Sold</th>
                    <th>Sales Revenue</th>
                    <th>Net Profit</th>
                    <th>Profit Margin</th>
                </tr>
            </thead>
            <tbody>
                {cat_rows}
            </tbody>
        </table>

        <h3 class="section-title">5. Top Product Contributors</h3>
        <table>
            <thead>
                <tr>
                    <th>Product</th>
                    <th>Category</th>
                    <th>Units Sold</th>
                    <th>Sales Revenue</th>
                    <th>Net Profit</th>
                    <th>Profit Margin</th>
                </tr>
            </thead>
            <tbody>
                {prod_rows}
            </tbody>
        </table>

        <div class="footer">
            Report generated by Business Analytics Web App | Portfolio Demonstration Project
        </div>
    </div>

</body>
</html>
"""
    return html_content
