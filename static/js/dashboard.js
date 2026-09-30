/**
 * dashboard.js
 * Single-Page Interactive Business Analytics Dashboard Controller
 */

// Global Chart instances container
let charts = {};

document.addEventListener('DOMContentLoaded', () => {
    initTabs();
    initRegionFilter();
    loadAnalyticsData('All Regions');
});

/**
 * Initializes Tab navigation
 */
function initTabs() {
    const tabBtns = document.querySelectorAll('.tab-btn');
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            tabBtns.forEach(b => b.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));

            btn.classList.add('active');
            const targetId = btn.getAttribute('data-tab');
            const targetContent = document.getElementById(targetId);
            if (targetContent) {
                targetContent.classList.add('active');
            }
        });
    });
}

/**
 * Initializes Region Filter dropdown listener
 */
function initRegionFilter() {
    const regionSelect = document.getElementById('regionSelect');
    if (regionSelect) {
        regionSelect.addEventListener('change', (e) => {
            const selectedRegion = e.target.value;
            loadAnalyticsData(selectedRegion);

            // Update download report button URL
            const downloadBtn = document.getElementById('btnDownloadReport');
            if (downloadBtn) {
                downloadBtn.href = `/download_report?region=${encodeURIComponent(selectedRegion)}`;
            }
        });
    }
}

/**
 * Fetches analytics data from API and updates all dashboard components
 */
async function loadAnalyticsData(region = 'All Regions') {
    try {
        const response = await fetch(`/api/analytics?region=${encodeURIComponent(region)}`);
        if (!response.ok) {
            throw new Error(`HTTP Error: ${response.status}`);
        }
        const data = await response.json();

        if (data.status === 'success') {
            updateKPICards(data.kpis);
            renderCharts(data.pandas_analysis);
            renderSQLAnalysis(data.sql_analysis);
            renderPythonAnalytics(data.pandas_analysis);
            renderInsights(data.insights);
            renderRawTable(data.raw_records);
        }
    } catch (err) {
        console.error('Failed to load analytics data:', err);
    }
}

/**
 * Updates KPI metrics cards on UI
 */
function updateKPICards(kpis) {
    if (!kpis) return;

    document.getElementById('kpiSales').textContent = `₹${kpis.total_sales.toLocaleString('en-IN', { minimumFractionDigits: 2 })}`;
    document.getElementById('kpiProfit').textContent = `₹${kpis.total_profit.toLocaleString('en-IN', { minimumFractionDigits: 2 })}`;
    document.getElementById('kpiOrders').textContent = kpis.total_orders.toLocaleString();
    document.getElementById('kpiCustomers').textContent = kpis.total_customers.toLocaleString();
    document.getElementById('kpiAOV').textContent = `₹${kpis.avg_order_value.toLocaleString('en-IN', { minimumFractionDigits: 2 })}`;
    document.getElementById('kpiMargin').textContent = `${kpis.profit_margin}%`;
    document.getElementById('kpiQuantity').textContent = kpis.total_quantity.toLocaleString();
}

/**
 * Renders Chart.js Visualizations
 */
function renderCharts(pandasAnalysis) {
    if (!pandasAnalysis) return;

    const regData = pandasAnalysis.regional_performance || [];
    const catData = pandasAnalysis.category_performance || [];
    const prodData = pandasAnalysis.top_products || [];
    const trendData = pandasAnalysis.date_trend || [];

    // Chart 1: Sales & Profit by Region (Bar Chart)
    const ctxRegion = document.getElementById('chartRegionSales');
    if (ctxRegion) {
        if (charts.region) charts.region.destroy();
        charts.region = new Chart(ctxRegion, {
            type: 'bar',
            data: {
                labels: regData.map(r => r.region),
                datasets: [
                    {
                        label: 'Sales Revenue (₹)',
                        data: regData.map(r => r.total_sales),
                        backgroundColor: '#3b82f6',
                        borderRadius: 6
                    },
                    {
                        label: 'Net Profit (₹)',
                        data: regData.map(r => r.total_profit),
                        backgroundColor: '#10b981',
                        borderRadius: 6
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { labels: { color: '#94a3b8' } },
                    tooltip: {
                        callbacks: {
                            label: (context) => `${context.dataset.label}: ₹${context.raw.toLocaleString('en-IN')}`
                        }
                    }
                },
                scales: {
                    x: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.05)' } },
                    y: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.05)' } }
                }
            }
        });
    }

    // Chart 2: Category Sales Distribution (Doughnut Chart)
    const ctxCategory = document.getElementById('chartCategorySales');
    if (ctxCategory) {
        if (charts.category) charts.category.destroy();
        charts.category = new Chart(ctxCategory, {
            type: 'doughnut',
            data: {
                labels: catData.map(c => c.category),
                datasets: [{
                    data: catData.map(c => c.total_sales),
                    backgroundColor: ['#3b82f6', '#8b5cf6', '#06b6d4', '#f59e0b', '#ec4899'],
                    borderWidth: 2,
                    borderColor: '#1e293b'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'bottom', labels: { color: '#94a3b8' } },
                    tooltip: {
                        callbacks: {
                            label: (context) => ` Sales: ₹${context.raw.toLocaleString('en-IN')}`
                        }
                    }
                }
            }
        });
    }

    // Chart 3: Top 10 Products Revenue (Horizontal Bar Chart)
    const ctxProducts = document.getElementById('chartTopProducts');
    if (ctxProducts) {
        if (charts.products) charts.products.destroy();
        charts.products = new Chart(ctxProducts, {
            type: 'bar',
            data: {
                labels: prodData.map(p => p.product),
                datasets: [{
                    label: 'Revenue (₹)',
                    data: prodData.map(p => p.total_sales),
                    backgroundColor: '#8b5cf6',
                    borderRadius: 6
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { labels: { color: '#94a3b8' } },
                    tooltip: {
                        callbacks: {
                            label: (context) => ` Revenue: ₹${context.raw.toLocaleString('en-IN')}`
                        }
                    }
                },
                scales: {
                    x: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.05)' } },
                    y: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.05)' } }
                }
            }
        });
    }

    // Chart 4: Time Series Trend (Line Chart)
    const ctxTrend = document.getElementById('chartTrend');
    if (ctxTrend) {
        if (charts.trend) charts.trend.destroy();
        charts.trend = new Chart(ctxTrend, {
            type: 'line',
            data: {
                labels: trendData.map(t => t.month),
                datasets: [
                    {
                        label: 'Monthly Sales (₹)',
                        data: trendData.map(t => t.total_sales),
                        borderColor: '#3b82f6',
                        backgroundColor: 'rgba(59, 130, 246, 0.1)',
                        fill: true,
                        tension: 0.3
                    },
                    {
                        label: 'Monthly Profit (₹)',
                        data: trendData.map(t => t.total_profit),
                        borderColor: '#10b981',
                        backgroundColor: 'rgba(16, 185, 129, 0.1)',
                        fill: true,
                        tension: 0.3
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { labels: { color: '#94a3b8' } }
                },
                scales: {
                    x: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.05)' } },
                    y: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.05)' } }
                }
            }
        });
    }
}

/**
 * Renders dedicated SQL Analysis Section
 */
function renderSQLAnalysis(sqlAnalysis) {
    if (!sqlAnalysis) return;

    const sqlContainer = document.getElementById('sqlQueriesContainer');
    if (!sqlContainer) return;

    let html = '';

    const sections = [
        { key: 'executive_summary', title: '1. SQLite Executive Aggregations' },
        { key: 'region_analysis', title: '2. Regional Sales & Margin SQL Query' },
        { key: 'category_analysis', title: '3. Category Aggregation SQL Query' },
        { key: 'product_analysis', title: '4. Top 10 Products SQL Performance' },
        { key: 'customer_analysis', title: '5. High Value Customer SQL Query' }
    ];

    sections.forEach(sec => {
        const item = sqlAnalysis[sec.key];
        if (item) {
            html += `
            <div class="sql-card">
                <div class="sql-header">
                    <div class="sql-title">
                        <span>${sec.title}</span>
                    </div>
                    <span class="sql-badge">SQLite Engine</span>
                </div>
                <div class="code-block">${escapeHtml(item.query)}</div>
                
                <div class="table-wrapper">
                    <table class="data-table">
                        <thead>
                            <tr>
                                ${Object.keys(item.data[0] || {}).map(k => `<th>${k.replace('_', ' ')}</th>`).join('')}
                            </tr>
                        </thead>
                        <tbody>
                            ${item.data.map(row => `
                                <tr>
                                    ${Object.values(row).map(val => `<td>${formatValue(val)}</td>`).join('')}
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            </div>
            `;
        }
    });

    sqlContainer.innerHTML = html;
}

/**
 * Renders Python Pandas Analytics tab
 */
function renderPythonAnalytics(pandasAnalysis) {
    if (!pandasAnalysis) return;

    const pyContainer = document.getElementById('pandasAnalysisContainer');
    if (!pyContainer) return;

    let html = `
    <div class="chart-grid">
        <div class="chart-card">
            <div class="chart-header">
                <div class="chart-title">Pandas Regional Performance Dataframe</div>
            </div>
            <div class="table-wrapper">
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>Region</th><th>Orders</th><th>Units</th><th>Sales (₹)</th><th>Profit (₹)</th><th>Margin %</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${(pandasAnalysis.regional_performance || []).map(r => `
                            <tr>
                                <td><strong>${r.region}</strong></td>
                                <td>${r.total_orders}</td>
                                <td>${r.total_quantity}</td>
                                <td>₹${r.total_sales.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</td>
                                <td>₹${r.total_profit.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</td>
                                <td><span class="badge ${r.profit_margin >= 10 ? 'positive' : 'neutral'}">${r.profit_margin}%</span></td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        </div>

        <div class="chart-card">
            <div class="chart-header">
                <div class="chart-title">Pandas Category Aggregation</div>
            </div>
            <div class="table-wrapper">
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>Category</th><th>Orders</th><th>Units</th><th>Sales (₹)</th><th>Profit (₹)</th><th>Margin %</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${(pandasAnalysis.category_performance || []).map(c => `
                            <tr>
                                <td><strong>${c.category}</strong></td>
                                <td>${c.total_orders}</td>
                                <td>${c.total_quantity}</td>
                                <td>₹${c.total_sales.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</td>
                                <td>₹${c.total_profit.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</td>
                                <td><span class="badge ${c.profit_margin >= 10 ? 'positive' : 'neutral'}">${c.profit_margin}%</span></td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    `;

    pyContainer.innerHTML = html;
}

/**
 * Renders Dynamic Business Insights Cards
 */
function renderInsights(insights) {
    const container = document.getElementById('insightsContainer');
    if (!container || !insights) return;

    let html = '';
    insights.forEach(ins => {
        html += `
        <div class="insight-card ${ins.type || 'info'}">
            <div class="insight-cat-tag">${ins.category || 'Business Insight'}</div>
            <div class="insight-card-title">${escapeHtml(ins.title)}</div>
            <div class="insight-card-body">${escapeHtml(ins.detail)}</div>
        </div>
        `;
    });

    container.innerHTML = html;
}

/**
 * Renders Raw Data Records Table
 */
function renderRawTable(records) {
    const tableHead = document.getElementById('rawTableHead');
    const tableBody = document.getElementById('rawTableBody');

    if (!records || records.length === 0) return;

    const cols = Object.keys(records[0]);
    if (tableHead) {
        tableHead.innerHTML = `<tr>${cols.map(c => `<th>${c.replace('_', ' ')}</th>`).join('')}</tr>`;
    }

    if (tableBody) {
        tableBody.innerHTML = records.map(r => `
            <tr>
                ${cols.map(c => `<td>${formatValue(r[c])}</td>`).join('')}
            </tr>
        `).join('');
    }
}

// Helper utilities
function escapeHtml(str) {
    return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function formatValue(val) {
    if (typeof val === 'number') {
        return val % 1 === 0 ? val.toLocaleString() : val.toLocaleString('en-IN', { minimumFractionDigits: 2 });
    }
    return escapeHtml(val);
}
