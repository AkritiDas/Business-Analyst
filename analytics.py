"""
analytics.py
Data processing, validation, KPI calculation, and business insight generation.
"""

import pandas as pd
import numpy as np
from datetime import datetime

# Standard canonical column names expected by the system
CANONICAL_COLUMNS = {
    'order_id': ['order_id', 'orderid', 'order id', 'id', 'transaction_id'],
    'order_date': ['order_date', 'orderdate', 'date', 'transaction_date', 'order date'],
    'customer_id': ['customer_id', 'customerid', 'customer id', 'customer', 'client_id'],
    'product': ['product', 'product_name', 'item', 'product name', 'item_name'],
    'category': ['category', 'product_category', 'cat', 'category_name'],
    'region': ['region', 'territory', 'location', 'zone', 'area', 'state'],
    'quantity': ['quantity', 'qty', 'units', 'quantity_sold', 'count'],
    'sales': ['sales', 'revenue', 'amount', 'total_sales', 'total_amount', 'price'],
    'profit': ['profit', 'margin', 'net_profit', 'earnings', 'profit_amount']
}

def map_column_names(df):
    """
    Dynamically maps raw dataframe columns to standardized canonical names.
    Returns mapped dataframe and column mapping dictionary.
    """
    column_mapping = {}
    df_cols_lower = {str(col).strip().lower(): col for col in df.columns}
    
    for canonical, aliases in CANONICAL_COLUMNS.items():
        found = False
        for alias in aliases:
            if alias in df_cols_lower:
                column_mapping[df_cols_lower[alias]] = canonical
                found = True
                break
        # Fallback partial match search if exact match fails
        if not found:
            for col_lower, orig_col in df_cols_lower.items():
                if canonical in col_lower and orig_col not in column_mapping:
                    column_mapping[orig_col] = canonical
                    found = True
                    break

    # Rename matched columns
    mapped_df = df.rename(columns=column_mapping)
    return mapped_df, column_mapping

def validate_and_clean_csv(file_path):
    """
    Validates CSV format, standardizes column names, cleans numeric and date fields,
    and returns processed DataFrame and a validation report dictionary.
    """
    validation_report = {
        'status': 'success',
        'errors': [],
        'warnings': [],
        'total_rows': 0,
        'valid_rows': 0,
        'mapped_columns': {}
    }
    
    try:
        # Read CSV
        df = pd.read_csv(file_path)
        validation_report['total_rows'] = len(df)
        
        if df.empty:
            validation_report['status'] = 'error'
            validation_report['errors'].append('Uploaded CSV file is completely empty.')
            return None, validation_report

        # Map column names
        df, mapped = map_column_names(df)
        validation_report['mapped_columns'] = mapped
        
        # Check mandatory core columns
        required = ['sales', 'region', 'product']
        missing_required = [req for req in required if req not in df.columns]
        if missing_required:
            validation_report['status'] = 'error'
            validation_report['errors'].append(f"Missing mandatory required columns: {', '.join(missing_required)}")
            return None, validation_report

        # Supply fallbacks for missing optional columns
        if 'order_id' not in df.columns:
            df['order_id'] = [f"ORD-{idx+1:04d}" for idx in range(len(df))]
            validation_report['warnings'].append("Generated default Order IDs ('order_id' column was missing).")
            
        if 'order_date' not in df.columns:
            df['order_date'] = datetime.today().strftime('%Y-%m-%d')
            validation_report['warnings'].append("Assigned current date ('order_date' column was missing).")
            
        if 'customer_id' not in df.columns:
            df['customer_id'] = [f"CUST-{idx+1:03d}" for idx in range(len(df))]
            
        if 'category' not in df.columns:
            df['category'] = 'General'
            
        if 'quantity' not in df.columns:
            df['quantity'] = 1
            validation_report['warnings'].append("Set default Quantity to 1 ('quantity' column was missing).")
            
        if 'profit' not in df.columns:
            # Estimate profit as 15% of sales if not provided
            df['profit'] = df['sales'].apply(lambda x: float(str(x).replace('$', '').replace('₹', '').replace(',', '')) * 0.15 if pd.notnull(x) else 0)
            validation_report['warnings'].append("Estimated profit at 15% of sales ('profit' column was missing).")

        # Clean string formatting
        for str_col in ['product', 'category', 'region', 'order_id', 'customer_id']:
            if str_col in df.columns:
                df[str_col] = df[str_col].astype(str).str.strip()

        # Clean numeric fields (Sales, Profit, Quantity)
        for num_col in ['sales', 'profit', 'quantity']:
            if num_col in df.columns:
                df[num_col] = df[num_col].astype(str).str.replace('$', '', regex=False)\
                                                     .str.replace('₹', '', regex=False)\
                                                     .str.replace(',', '', regex=False)\
                                                     .str.strip()
                df[num_col] = pd.to_numeric(df[num_col], errors='coerce').fillna(0)

        # Ensure Quantity is integer
        df['quantity'] = df['quantity'].astype(int)

        # Clean and parse date column
        try:
            df['order_date'] = pd.to_datetime(df['order_date'], errors='coerce').dt.strftime('%Y-%m-%d')
            df['order_date'] = df['order_date'].fillna(datetime.today().strftime('%Y-%m-%d'))
        except Exception:
            df['order_date'] = datetime.today().strftime('%Y-%m-%d')

        # Drop rows with zero or negative sales if invalid
        invalid_sales_count = (df['sales'] <= 0).sum()
        if invalid_sales_count > 0:
            validation_report['warnings'].append(f"Found {invalid_sales_count} rows with zero or negative sales.")

        validation_report['valid_rows'] = len(df)
        
        # Standardize column headers casing for SQL compatibility
        df.columns = [col.lower() for col in df.columns]
        
        return df, validation_report

    except Exception as e:
        validation_report['status'] = 'error'
        validation_report['errors'].append(f"Failed to process CSV file: {str(e)}")
        return None, validation_report


def calculate_kpis(df):
    """
    Calculates primary business KPIs from the dataframe.
    """
    if df is None or df.empty:
        return {
            'total_sales': 0,
            'total_profit': 0,
            'total_orders': 0,
            'total_customers': 0,
            'avg_order_value': 0,
            'profit_margin': 0,
            'total_quantity': 0,
            'avg_profit_per_order': 0
        }

    total_sales = float(df['sales'].sum())
    total_profit = float(df['profit'].sum())
    total_orders = int(df['order_id'].nunique())
    total_customers = int(df['customer_id'].nunique())
    total_quantity = int(df['quantity'].sum())
    
    avg_order_value = total_sales / total_orders if total_orders > 0 else 0
    profit_margin = (total_profit / total_sales * 100) if total_sales > 0 else 0
    avg_profit_per_order = total_profit / total_orders if total_orders > 0 else 0

    return {
        'total_sales': round(total_sales, 2),
        'total_profit': round(total_profit, 2),
        'total_orders': total_orders,
        'total_customers': total_customers,
        'avg_order_value': round(avg_order_value, 2),
        'profit_margin': round(profit_margin, 2),
        'total_quantity': total_quantity,
        'avg_profit_per_order': round(avg_profit_per_order, 2)
    }


def perform_pandas_analysis(df):
    """
    Performs analytical aggregations using Pandas.
    """
    if df is None or df.empty:
        return {}

    # Regional Performance
    region_perf = df.groupby('region').agg(
        total_sales=('sales', 'sum'),
        total_profit=('profit', 'sum'),
        total_orders=('order_id', 'nunique'),
        total_quantity=('quantity', 'sum')
    ).reset_index()
    region_perf['profit_margin'] = (region_perf['total_profit'] / region_perf['total_sales'] * 100).round(2)
    region_perf = region_perf.sort_values(by='total_sales', ascending=False)

    # Category Performance
    category_perf = df.groupby('category').agg(
        total_sales=('sales', 'sum'),
        total_profit=('profit', 'sum'),
        total_orders=('order_id', 'nunique'),
        total_quantity=('quantity', 'sum')
    ).reset_index()
    category_perf['profit_margin'] = (category_perf['total_profit'] / category_perf['total_sales'] * 100).round(2)
    category_perf = category_perf.sort_values(by='total_sales', ascending=False)

    # Top Products by Sales
    product_perf = df.groupby(['product', 'category']).agg(
        total_sales=('sales', 'sum'),
        total_profit=('profit', 'sum'),
        total_quantity=('quantity', 'sum')
    ).reset_index()
    product_perf['profit_margin'] = (product_perf['total_profit'] / product_perf['total_sales'] * 100).round(2)
    top_products = product_perf.sort_values(by='total_sales', ascending=False).head(10)
    
    # Loss-making / Low margin products
    loss_products = product_perf[product_perf['total_profit'] < 0].sort_values(by='total_profit', ascending=True)

    # Time series / Date trend
    df['order_date_dt'] = pd.to_datetime(df['order_date'], errors='coerce')
    date_trend = df.groupby(df['order_date_dt'].dt.strftime('%Y-%m')).agg(
        total_sales=('sales', 'sum'),
        total_profit=('profit', 'sum')
    ).reset_index().rename(columns={'order_date_dt': 'month'})
    date_trend = date_trend.sort_values(by='month')

    return {
        'regional_performance': region_perf.to_dict(orient='records'),
        'category_performance': category_perf.to_dict(orient='records'),
        'top_products': top_products.to_dict(orient='records'),
        'loss_products': loss_products.to_dict(orient='records'),
        'date_trend': date_trend.to_dict(orient='records')
    }


def generate_automated_insights(df, kpis, pandas_analysis):
    """
    Generates intelligent dynamic business insights based on dataset stats.
    """
    insights = []
    
    if df is None or df.empty or not pandas_analysis:
        return ["No data available to generate business insights."]

    reg_perf = pandas_analysis.get('regional_performance', [])
    cat_perf = pandas_analysis.get('category_performance', [])
    top_prods = pandas_analysis.get('top_products', [])
    loss_prods = pandas_analysis.get('loss_products', [])

    # 1. Regional Sales Leader & Growth Insight
    if reg_perf:
        top_region = reg_perf[0]
        lowest_region = reg_perf[-1]
        reg_share = round((top_region['total_sales'] / kpis['total_sales'] * 100), 1) if kpis['total_sales'] > 0 else 0
        insights.append({
            'category': 'Regional Leader',
            'type': 'positive',
            'title': f"Highest Revenue Contributor: {top_region['region']} Region",
            'detail': f"The {top_region['region']} region generated ₹{top_region['total_sales']:,.2f} in total revenue ({reg_share}% of total business revenue) with a profit margin of {top_region['profit_margin']}%."
        })
        if len(reg_perf) > 1:
            insights.append({
                'category': 'Regional Opportunity',
                'type': 'warning',
                'title': f"Underperforming Region: {lowest_region['region']}",
                'detail': f"The {lowest_region['region']} region recorded the lowest sales volume of ₹{lowest_region['total_sales']:,.2f}. Consider targeted promotional campaigns or regional distributor reviews."
            })

    # 2. Product Performance Insight
    if top_prods:
        top_prod = top_prods[0]
        insights.append({
            'category': 'Product Star',
            'type': 'positive',
            'title': f"Best Selling Product: {top_prod['product']}",
            'detail': f"{top_prod['product']} in the '{top_prod['category']}' category generated ₹{top_prod['total_sales']:,.2f} across {top_prod['total_quantity']} units sold."
        })

    # 3. Category Dominance Insight
    if cat_perf:
        top_cat = cat_perf[0]
        cat_share = round((top_cat['total_sales'] / kpis['total_sales'] * 100), 1) if kpis['total_sales'] > 0 else 0
        insights.append({
            'category': 'Category Driver',
            'type': 'info',
            'title': f"Dominant Product Category: {top_cat['category']}",
            'detail': f"The {top_cat['category']} category accounts for {cat_share}% of total sales (₹{top_cat['total_sales']:,.2f}) and generated ₹{top_cat['total_profit']:,.2f} in net profit."
        })

    # 4. Profitability & Loss Alert Insight
    if loss_prods:
        total_loss = sum(p['total_profit'] for p in loss_prods)
        loss_prod_names = ", ".join([p['product'] for p in loss_prods[:3]])
        insights.append({
            'category': 'Profitability Risk',
            'type': 'negative',
            'title': f"Negative Profit Margin Alert ({len(loss_prods)} Products)",
            'detail': f"Products like {loss_prod_names} are running at a net loss totaling ₹{abs(total_loss):,.2f}. Review pricing strategy, supplier costs, or discount structure."
        })
    else:
        insights.append({
            'category': 'Health Indicator',
            'type': 'positive',
            'title': 'Strong Overall Margin Portfolio',
            'detail': f"All key product categories are operating with positive net margins. Overall business profit margin stands at {kpis['profit_margin']}%."
        })

    # 5. Order Value Efficiency Insight
    insights.append({
        'category': 'Executive Summary',
        'type': 'info',
        'title': 'Average Transaction & Customer Efficiency',
        'detail': f"Average Order Value (AOV) is ₹{kpis['avg_order_value']:,.2f} with an average profit of ₹{kpis['avg_profit_per_order']:,.2f} per order across {kpis['total_customers']} unique customers."
    })

    return insights
