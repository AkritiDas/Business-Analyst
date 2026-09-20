"""
app.py
Flask Web Application Controller for Business Analytics Web App.
"""

import os
import pandas as pd
from flask import Flask, render_template, request, jsonify, redirect, url_for, send_file, Response
from werkzeug.utils import secure_filename

import analytics
import database
import report

app = Flask(__name__)
app.secret_key = 'business-analytics-secret-key-2024'

# Directories configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max upload size

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Global in-memory cache for processed active dataset
CURRENT_DATASET = {
    'df': None,
    'validation_report': None,
    'filename': None
}

def load_default_sample():
    """Loads the bundled sample sales dataset into the system."""
    sample_path = os.path.join(UPLOAD_FOLDER, 'sample_sales_data.csv')
    if os.path.exists(sample_path):
        df, val_report = analytics.validate_and_clean_csv(sample_path)
        if df is not None:
            database.save_dataframe_to_db(df)
            CURRENT_DATASET['df'] = df
            CURRENT_DATASET['validation_report'] = val_report
            CURRENT_DATASET['filename'] = 'sample_sales_data.csv'
            return True
    return False

# Ensure database table exists on startup and load default sample data
database.init_db()
load_default_sample()


@app.route('/')
def index():
    """Renders the Upload landing page."""
    has_active_data = CURRENT_DATASET['df'] is not None
    active_filename = CURRENT_DATASET['filename'] if has_active_data else None
    return render_template('index.html', has_active_data=has_active_data, active_filename=active_filename)


@app.route('/upload', methods=['POST'])
def upload_file():
    """Handles CSV upload, validates columns, cleans data, and updates SQLite DB."""
    if 'file' not in request.files:
        return jsonify({'status': 'error', 'message': 'No file part in request.'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'status': 'error', 'message': 'No file selected for uploading.'}), 400

    if not file.filename.lower().endswith('.csv'):
        return jsonify({'status': 'error', 'message': 'Invalid file format. Please upload a valid CSV file.'}), 400

    try:
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        # Process & Validate
        df, validation_report = analytics.validate_and_clean_csv(file_path)

        if validation_report['status'] == 'error':
            return jsonify({
                'status': 'error',
                'message': 'CSV Validation Failed.',
                'errors': validation_report['errors']
            }), 400

        # Save to SQLite database
        database.save_dataframe_to_db(df)

        # Update current active dataset
        CURRENT_DATASET['df'] = df
        CURRENT_DATASET['validation_report'] = validation_report
        CURRENT_DATASET['filename'] = filename

        return jsonify({
            'status': 'success',
            'message': 'File uploaded, validated, processed, and stored in SQLite successfully!',
            'filename': filename,
            'report': validation_report,
            'redirect': url_for('dashboard')
        })

    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Server error processing file: {str(e)}'}), 500


@app.route('/demo')
def load_demo():
    """Loads bundled sample dataset for 1-click test drive."""
    if load_default_sample():
        return redirect(url_for('dashboard'))
    return redirect(url_for('index'))


@app.route('/dashboard')
def dashboard():
    """Renders the main analytics workspace."""
    if CURRENT_DATASET['df'] is None:
        load_default_sample()

    if CURRENT_DATASET['df'] is None:
        return redirect(url_for('index'))

    # Extract distinct regions for dynamic dropdown filter
    regions = sorted(CURRENT_DATASET['df']['region'].dropna().unique().tolist())
    filename = CURRENT_DATASET['filename']
    val_report = CURRENT_DATASET['validation_report']

    return render_template('dashboard.html', regions=regions, filename=filename, val_report=val_report)


@app.route('/api/analytics')
def get_analytics_api():
    """
    Returns filtered analytics (KPIs, SQL queries, Pandas aggregations, and Insights)
    in JSON format based on optional 'region' query parameter.
    """
    df = CURRENT_DATASET['df']
    if df is None:
        return jsonify({'error': 'No dataset active. Please upload a CSV first.'}), 404

    region_filter = request.args.get('region', 'All Regions')

    # Filter dataframe if a specific region is requested
    if region_filter and region_filter != 'All Regions':
        filtered_df = df[df['region'].str.lower() == region_filter.lower()]
    else:
        filtered_df = df

    # 1. Compute KPIs
    kpis = analytics.calculate_kpis(filtered_df)

    # 2. Compute Pandas aggregations
    pandas_analysis = analytics.perform_pandas_analysis(filtered_df)

    # 3. Execute SQL queries against SQLite database
    sql_analysis = database.run_sql_analytics(region_filter)

    # 4. Generate dynamic business insights
    insights = analytics.generate_automated_insights(filtered_df, kpis, pandas_analysis)

    # 5. Raw records preview (top 50)
    raw_records = filtered_df.head(50).to_dict(orient='records')

    # Available regions list
    all_regions = sorted(df['region'].unique().tolist())

    return jsonify({
        'status': 'success',
        'active_region': region_filter,
        'all_regions': all_regions,
        'kpis': kpis,
        'pandas_analysis': pandas_analysis,
        'sql_analysis': sql_analysis,
        'insights': insights,
        'raw_records': raw_records,
        'dataset_info': {
            'filename': CURRENT_DATASET['filename'],
            'total_rows': len(df),
            'filtered_rows': len(filtered_df),
            'columns': list(df.columns)
        }
    })


@app.route('/download_report')
def download_report():
    """Generates and serves the downloadable executive analytical HTML report."""
    df = CURRENT_DATASET['df']
    if df is None:
        return "No dataset active", 404

    region_filter = request.args.get('region', 'All Regions')
    if region_filter and region_filter != 'All Regions':
        filtered_df = df[df['region'].str.lower() == region_filter.lower()]
    else:
        filtered_df = df

    kpis = analytics.calculate_kpis(filtered_df)
    pandas_analysis = analytics.perform_pandas_analysis(filtered_df)
    sql_analysis = database.run_sql_analytics(region_filter)
    insights = analytics.generate_automated_insights(filtered_df, kpis, pandas_analysis)
    val_report = CURRENT_DATASET['validation_report'] or {}

    html_code = report.generate_html_report(kpis, pandas_analysis, sql_analysis, insights, val_report)
    
    return Response(
        html_code,
        mimetype='text/html',
        headers={'Content-Disposition': 'inline; filename=business_analytics_report.html'}
    )


@app.route('/sample_csv')
def download_sample_csv():
    """Provides sample CSV download link."""
    sample_path = os.path.join(UPLOAD_FOLDER, 'sample_sales_data.csv')
    if os.path.exists(sample_path):
        return send_file(sample_path, as_attachment=True, download_name='sample_sales_data.csv')
    return "Sample CSV file not found", 404


if __name__ == '__main__':
    print("Starting Business Analytics Web Application on http://127.0.0.1:5000")
    app.run(debug=True, port=5000)
