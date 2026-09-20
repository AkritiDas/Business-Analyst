"""
database.py
SQLite database connection management, table setup, and raw SQL analytics execution.
"""

import sqlite3
import pandas as pd
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'business.db')

def get_connection():
    """Returns a connection to the SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the SQLite database with proper schema."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sales_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id TEXT,
            order_date TEXT,
            customer_id TEXT,
            product TEXT,
            category TEXT,
            region TEXT,
            quantity INTEGER,
            sales REAL,
            profit REAL
        )
    """)
    conn.commit()
    conn.close()

def save_dataframe_to_db(df):
    """
    Saves cleaned dataframe to SQLite database, replacing previous table content.
    """
    init_db()
    conn = get_connection()
    
    # Store dataframe into SQLite table 'sales_data'
    df.to_sql('sales_data', conn, if_exists='replace', index=False)
    
    # Create indexes for optimal SQL query performance
    cursor = conn.cursor()
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_region ON sales_data(region);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_category ON sales_data(category);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_product ON sales_data(product);")
    conn.commit()
    conn.close()

def execute_sql_query(query, params=()):
    """Executes a SQL query and returns results as list of dictionaries."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def run_sql_analytics(region_filter=None):
    """
    Executes dedicated analytical SQL queries against SQLite database.
    Returns structured results along with the actual raw SQL query string for UI display.
    """
    where_clause = ""
    params = []
    if region_filter and region_filter != 'All Regions':
        where_clause = "WHERE region = ?"
        params.append(region_filter)

    sql_results = {}

    # 1. Executive Aggregates Query
    query_exec = f"""
        SELECT 
            COUNT(*) as record_count,
            COUNT(DISTINCT order_id) as total_orders,
            COUNT(DISTINCT customer_id) as total_customers,
            ROUND(SUM(sales), 2) as total_sales,
            ROUND(SUM(profit), 2) as total_profit,
            ROUND(AVG(sales), 2) as avg_order_value,
            ROUND((SUM(profit) * 100.0 / SUM(sales)), 2) as profit_margin_pct
        FROM sales_data
        {where_clause};
    """
    sql_results['executive_summary'] = {
        'query': query_exec.strip(),
        'data': execute_sql_query(query_exec, params)
    }

    # 2. Regional Breakdown Query
    query_region = f"""
        SELECT 
            region,
            COUNT(DISTINCT order_id) as order_count,
            SUM(quantity) as total_units,
            ROUND(SUM(sales), 2) as total_sales,
            ROUND(SUM(profit), 2) as total_profit,
            ROUND((SUM(profit) * 100.0 / SUM(sales)), 2) as margin_pct
        FROM sales_data
        {where_clause}
        GROUP BY region
        ORDER BY total_sales DESC;
    """
    sql_results['region_analysis'] = {
        'query': query_region.strip(),
        'data': execute_sql_query(query_region, params)
    }

    # 3. Category Breakdown Query
    query_category = f"""
        SELECT 
            category,
            COUNT(DISTINCT order_id) as order_count,
            SUM(quantity) as total_units,
            ROUND(SUM(sales), 2) as total_sales,
            ROUND(SUM(profit), 2) as total_profit,
            ROUND((SUM(profit) * 100.0 / SUM(sales)), 2) as margin_pct
        FROM sales_data
        {where_clause}
        GROUP BY category
        ORDER BY total_sales DESC;
    """
    sql_results['category_analysis'] = {
        'query': query_category.strip(),
        'data': execute_sql_query(query_category, params)
    }

    # 4. Top Products Query
    query_product = f"""
        SELECT 
            product,
            category,
            SUM(quantity) as total_units,
            ROUND(SUM(sales), 2) as total_sales,
            ROUND(SUM(profit), 2) as total_profit,
            ROUND((SUM(profit) * 100.0 / SUM(sales)), 2) as margin_pct
        FROM sales_data
        {where_clause}
        GROUP BY product, category
        ORDER BY total_sales DESC
        LIMIT 10;
    """
    sql_results['product_analysis'] = {
        'query': query_product.strip(),
        'data': execute_sql_query(query_product, params)
    }

    # 5. Customer Top Value SQL Query
    query_customers = f"""
        SELECT 
            customer_id,
            COUNT(DISTINCT order_id) as order_count,
            SUM(quantity) as total_items,
            ROUND(SUM(sales), 2) as total_spent,
            ROUND(SUM(profit), 2) as profit_generated
        FROM sales_data
        {where_clause}
        GROUP BY customer_id
        ORDER BY total_spent DESC
        LIMIT 5;
    """
    sql_results['customer_analysis'] = {
        'query': query_customers.strip(),
        'data': execute_sql_query(query_customers, params)
    }

    return sql_results
