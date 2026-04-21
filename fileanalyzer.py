from flask import Flask, request, render_template_string
import base64
from io import BytesIO
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd

app = Flask(__name__)

PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cloud Cost Analytics</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Sora:wght@300;400;500;600&display=swap" rel="stylesheet">
    <style>
        *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

        :root {
            --bg:         #08090b;
            --surface:    #0e1117;
            --surface2:   #141821;
            --border:     rgba(255,255,255,0.07);
            --border-hi:  rgba(255,255,255,0.13);
            --text:       #e8eaf0;
            --muted:      #6b7280;
            --accent:     #5b8af7;
            --accent-dim: rgba(91,138,247,0.12);
            --green:      #34d399;
            --green-dim:  rgba(52,211,153,0.1);
            --amber:      #f59e0b;
            --amber-dim:  rgba(245,158,11,0.1);
            --red:        #f87171;
            --red-dim:    rgba(248,113,113,0.1);
            --mono:       'DM Mono', monospace;
            --sans:       'Sora', sans-serif;
            --radius:     14px;
            --radius-lg:  22px;
        }

        body {
            background: var(--bg);
            font-family: var(--sans);
            color: var(--text);
            min-height: 100vh;
            font-size: 14px;
            line-height: 1.6;
        }

        /* ── Layout ─────────────────────────────── */
        .shell {
            max-width: 1240px;
            margin: 0 auto;
            padding: 40px 32px 80px;
        }

        /* ── Top bar ────────────────────────────── */
        .topbar {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 48px;
        }
        .topbar-brand {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .topbar-icon {
            width: 32px; height: 32px;
            background: var(--accent-dim);
            border: 1px solid rgba(91,138,247,0.25);
            border-radius: 8px;
            display: flex; align-items: center; justify-content: center;
            font-size: 15px;
        }
        .topbar-title {
            font-size: 15px;
            font-weight: 500;
            letter-spacing: -0.01em;
            color: var(--text);
        }
        .topbar-sub {
            font-family: var(--mono);
            font-size: 11px;
            color: var(--muted);
            margin-top: 1px;
        }
        .badge {
            font-family: var(--mono);
            font-size: 10px;
            font-weight: 500;
            padding: 3px 10px;
            border-radius: 99px;
            letter-spacing: 0.04em;
            text-transform: uppercase;
        }
        

        /* ── Page heading ───────────────────────── */
        .page-heading {
            margin-bottom: 36px;
        }
        .page-heading h1 {
            font-size: 32px;
            font-weight: 600;
            letter-spacing: -0.03em;
            color: #f0f2f8;
            margin-bottom: 6px;
        }
        .page-heading p {
            color: var(--muted);
            font-size: 14px;
            max-width: 480px;
        }

        /* ── Upload card ────────────────────────── */
        .upload-card {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: var(--radius-lg);
            padding: 28px;
            margin-bottom: 32px;
            display: flex;
            align-items: center;
            gap: 20px;
        }
        .upload-zone {
            flex: 1;
            border: 1px dashed var(--border-hi);
            border-radius: var(--radius);
            padding: 20px 24px;
            display: flex;
            align-items: center;
            gap: 14px;
            cursor: pointer;
            transition: border-color 0.2s, background 0.2s;
        }
        .upload-zone:hover {
            border-color: rgba(91,138,247,0.4);
            background: var(--accent-dim);
        }
        .upload-icon {
            width: 40px; height: 40px;
            background: var(--surface2);
            border: 1px solid var(--border-hi);
            border-radius: 10px;
            display: flex; align-items: center; justify-content: center;
            font-size: 18px;
            flex-shrink: 0;
        }
        .upload-text strong {
            display: block;
            font-size: 13px;
            font-weight: 500;
            color: var(--text);
            margin-bottom: 2px;
        }
        .upload-text span {
            font-size: 12px;
            color: var(--muted);
            font-family: var(--mono);
        }
        input[type="file"] {
            position: absolute;
            opacity: 0;
            width: 0; height: 0;
        }
        .file-name {
            font-family: var(--mono);
            font-size: 12px;
            color: var(--accent);
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            max-width: 220px;
        }
        .file-name.empty { color: var(--muted); }

        .btn-analyze {
            background: var(--accent);
            color: #fff;
            border: none;
            border-radius: var(--radius);
            padding: 0 28px;
            height: 44px;
            font-family: var(--sans);
            font-size: 13px;
            font-weight: 500;
            letter-spacing: -0.01em;
            cursor: pointer;
            white-space: nowrap;
            transition: opacity 0.15s, transform 0.1s;
            flex-shrink: 0;
        }
        .btn-analyze:hover { opacity: 0.88; }
        .btn-analyze:active { transform: scale(0.97); }

        /* ── Error ──────────────────────────────── */
        .error-msg {
            background: var(--red-dim);
            border: 1px solid rgba(248,113,113,0.2);
            border-radius: var(--radius);
            padding: 14px 20px;
            color: var(--red);
            font-size: 13px;
            margin-bottom: 28px;
        }

        /* ── KPI row ────────────────────────────── */
        .kpi-row {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 16px;
            margin-bottom: 20px;
        }
        .kpi-card {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: var(--radius-lg);
            padding: 22px 24px;
            position: relative;
            overflow: hidden;
        }
        .kpi-card::before {
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0;
            height: 1px;
            background: linear-gradient(90deg, transparent, var(--kpi-accent, var(--accent)), transparent);
            opacity: 0.5;
        }
        .kpi-card.c-blue  { --kpi-accent: #5b8af7; }
        .kpi-card.c-green { --kpi-accent: #34d399; }
        .kpi-card.c-amber { --kpi-accent: #f59e0b; }
        .kpi-card.c-purple { --kpi-accent: #a78bfa; }

        .kpi-label {
            font-family: var(--mono);
            font-size: 10px;
            font-weight: 500;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            color: var(--muted);
            margin-bottom: 10px;
        }
        .kpi-value {
            font-size: 28px;
            font-weight: 600;
            letter-spacing: -0.03em;
            color: #f0f2f8;
            margin-bottom: 8px;
            line-height: 1;
        }
        .kpi-trend {
            font-size: 12px;
            color: var(--green);
            font-family: var(--mono);
        }
        .kpi-trend.down { color: var(--red); }
        .kpi-trend.neutral { color: var(--muted); }

        /* ── Chart grid ─────────────────────────── */
        .chart-grid {
            display: grid;
            grid-template-columns: repeat(12, 1fr);
            gap: 16px;
        }
        .chart-card {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: var(--radius-lg);
            padding: 24px;
            overflow: hidden;
        }
        .chart-card.span-8 { grid-column: span 8; }
        .chart-card.span-4 { grid-column: span 4; }

        .chart-header {
            margin-bottom: 18px;
        }
        .chart-title {
            font-size: 14px;
            font-weight: 500;
            color: #e0e3ec;
            margin-bottom: 4px;
            letter-spacing: -0.01em;
        }
        .chart-desc {
            font-size: 12px;
            color: var(--muted);
            font-family: var(--mono);
        }

        .chart-img {
            width: 100%;
            border-radius: 10px;
            display: block;
            background: var(--bg);
        }

        /* ── Empty state ────────────────────────── */
        .empty-state {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: 200px;
            gap: 10px;
            opacity: 0.35;
        }
        .empty-icon { font-size: 32px; }
        .empty-text {
            font-family: var(--mono);
            font-size: 12px;
            color: var(--muted);
        }

        /* ── Divider label ──────────────────────── */
        .section-label {
            font-family: var(--mono);
            font-size: 10px;
            font-weight: 500;
            letter-spacing: 0.1em;
            text-transform: uppercase;
            color: var(--muted);
            margin-bottom: 14px;
            margin-top: 36px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .section-label::after {
            content: '';
            flex: 1;
            height: 1px;
            background: var(--border);
        }

        @media (max-width: 1024px) {
            .kpi-row { grid-template-columns: repeat(2, 1fr); }
            .chart-card.span-8,
            .chart-card.span-4 { grid-column: span 12; }
        }
        @media (max-width: 640px) {
            .shell { padding: 24px 16px 60px; }
            .kpi-row { grid-template-columns: 1fr 1fr; }
            .upload-card { flex-direction: column; align-items: stretch; }
            .topbar { flex-direction: column; align-items: flex-start; gap: 12px; }
        }
    </style>
</head>
<body>
<div class="shell">

    <!-- Top bar -->
    <div class="topbar">
        <div class="topbar-brand">
            <div class="topbar-icon">☁</div>
            <div>
                <div class="topbar-title">CloudLens</div>
                <div class="topbar-sub">cost analytics</div>
            </div>
        </div>
    </div>

    <!-- Page heading -->
    <div class="page-heading">
        <h1>Cost Dashboard</h1>
        <p>Upload a CSV to analyse your cloud spend across departments, services, and regions.</p>
    </div>

    <!-- Upload card -->
    <div class="upload-card">
        <form method="POST" enctype="multipart/form-data" style="display:contents">
            <label class="upload-zone" for="csv-input">
                <div class="upload-icon">📂</div>
                <div class="upload-text">
                    <strong>Drop your CSV here</strong>
                    <span>Requires: Date, Cost_INR, Department, Service_Type, Application, Region</span>
                </div>
                <input type="file" name="myfile" id="csv-input" accept=".csv" onchange="updateName(this)">
            </label>
            <div class="file-name {% if not filename %}empty{% endif %}" id="fname">
                {% if filename %}{{ filename }}{% else %}no file chosen{% endif %}
            </div>
            <button type="submit" class="btn-analyze">Analyse →</button>
        </form>
    </div>

    {% if error %}
    <div class="error-msg">{{ error }}</div>
    {% endif %}

    <!-- KPI row -->
    <div class="section-label">Key metrics</div>
    <div class="kpi-row">
        <div class="kpi-card c-blue">
            <div class="kpi-label">Total Spend</div>
            <div class="kpi-value">₹{{ kpis.total_cost if kpis else '—' }}</div>
            <div class="kpi-trend">all time</div>
        </div>
        <div class="kpi-card c-green">
            <div class="kpi-label">Avg Daily Cost</div>
            <div class="kpi-value">₹{{ kpis.avg_daily_cost if kpis else '—' }}</div>
            <div class="kpi-trend">per day</div>
        </div>
        <div class="kpi-card c-amber">
            <div class="kpi-label">Top Department</div>
            <div class="kpi-value" style="font-size:18px;margin-top:6px;">{{ kpis.top_department_name if kpis else '—' }}</div>
            <div class="kpi-trend neutral">₹{{ kpis.top_department_cost if kpis else '' }}</div>
        </div>
        <div class="kpi-card c-purple">
            <div class="kpi-label">Top Application</div>
            <div class="kpi-value" style="font-size:18px;margin-top:6px;">{{ kpis.top_application_name if kpis else '—' }}</div>
            <div class="kpi-trend neutral">₹{{ kpis.top_application_cost if kpis else '' }}</div>
        </div>
    </div>

    <!-- Charts -->
    <div class="section-label">Spend breakdown</div>
    <div class="chart-grid">

        <!-- Trend line — wide -->
        <div class="chart-card span-8">
            <div class="chart-header">
                <div class="chart-title">Daily Cost Trend</div>
                <div class="chart-desc">total spend over time across all services</div>
            </div>
            {% if charts %}
            <img class="chart-img" src="data:image/png;base64,{{ charts.trend_line }}" alt="Cost trend">
            {% else %}
            <div class="empty-state"><div class="empty-icon">📈</div><div class="empty-text">upload a CSV to render</div></div>
            {% endif %}
        </div>

        <!-- Service pie -->
        <div class="chart-card span-4">
            <div class="chart-header">
                <div class="chart-title">Service Breakdown</div>
                <div class="chart-desc">cost share by service type</div>
            </div>
            {% if charts %}
            <img class="chart-img" src="data:image/png;base64,{{ charts.service_pie }}" alt="Service pie">
            {% else %}
            <div class="empty-state"><div class="empty-icon">🥧</div><div class="empty-text">upload a CSV to render</div></div>
            {% endif %}
        </div>

        <!-- Department bar -->
        <div class="chart-card span-4">
            <div class="chart-header">
                <div class="chart-title">By Department</div>
                <div class="chart-desc">ranked by total spend</div>
            </div>
            {% if charts %}
            <img class="chart-img" src="data:image/png;base64,{{ charts.department_bar }}" alt="Department bar">
            {% else %}
            <div class="empty-state"><div class="empty-icon">🏢</div><div class="empty-text">upload a CSV to render</div></div>
            {% endif %}
        </div>

        <!-- Region bar -->
        <div class="chart-card span-4">
            <div class="chart-header">
                <div class="chart-title">Regional Distribution</div>
                <div class="chart-desc">cost by cloud region</div>
            </div>
            {% if charts %}
            <img class="chart-img" src="data:image/png;base64,{{ charts.region_bar }}" alt="Region bar">
            {% else %}
            <div class="empty-state"><div class="empty-icon">🌍</div><div class="empty-text">upload a CSV to render</div></div>
            {% endif %}
        </div>

        <!-- Top apps -->
        <div class="chart-card span-4">
            <div class="chart-header">
                <div class="chart-title">Top Applications</div>
                <div class="chart-desc">highest spend, top 8</div>
            </div>
            {% if charts %}
            <img class="chart-img" src="data:image/png;base64,{{ charts.top_app_bar }}" alt="Top apps">
            {% else %}
            <div class="empty-state"><div class="empty-icon">📦</div><div class="empty-text">upload a CSV to render</div></div>
            {% endif %}
        </div>

        <!-- Rolling average — full width -->
        <div class="chart-card span-12" style="grid-column: span 12;">
            <div class="chart-header">
                <div class="chart-title">Rolling Average Trend</div>
                <div class="chart-desc">daily spend · 7-day rolling average overlay</div>
            </div>
            {% if charts %}
            <img class="chart-img" src="data:image/png;base64,{{ charts.rolling_avg }}" alt="Rolling average trend">
            {% else %}
            <div class="empty-state"><div class="empty-icon">📈</div><div class="empty-text">upload a CSV to render</div></div>
            {% endif %}
        </div>

        <!-- Monthly bars — full width -->
        <div class="chart-card" style="grid-column: span 12;">
            <div class="chart-header">
                <div class="chart-title">Monthly Cost by Service</div>
                <div class="chart-desc">grouped by service type</div>
            </div>
            {% if charts %}
            <img class="chart-img" src="data:image/png;base64,{{ charts.monthly_bars }}" alt="Monthly cost by service type">
            {% else %}
            <div class="empty-state"><div class="empty-icon">📊</div><div class="empty-text">upload a CSV to render</div></div>
            {% endif %}
        </div>

    </div>
</div>

<script>
function updateName(input) {
    const el = document.getElementById('fname');
    if (input.files[0]) {
        el.textContent = input.files[0].name;
        el.classList.remove('empty');
    } else {
        el.textContent = 'no file chosen';
        el.classList.add('empty');
    }
}
</script>
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def index():
    filename = None
    error = None
    kpis = None
    charts = {}

    if request.method == "POST":
        file = request.files.get("myfile")
        filename = file.filename if file else None

        if file and file.filename != "":
            try:
                analysis = analyze_costs(file)
                kpis = {
                    "total_cost":           f"{analysis['total_cost']:,}",
                    "avg_daily_cost":        f"{analysis['avg_daily_cost']:,}",
                    "top_department_name":   analysis['top_department_name'],
                    "top_department_cost":   f"{analysis['top_department_cost']:,}",
                    "top_application_name":  analysis['top_application_name'],
                    "top_application_cost":  f"{analysis['top_application_cost']:,}",
                }
                charts = {
                    "service_pie":      create_chart_image(plot_service_pie(analysis['service_costs'])),
                    "department_bar":   create_chart_image(plot_bar(analysis['department_cost'], 'Cost by Department', 'Department')),
                    "region_bar":       create_chart_image(plot_bar(analysis['region_cost'], 'Cost by Region', 'Region')),
                    "trend_line":       create_chart_image(plot_trend_line(analysis['cost_trend'])),
                    "top_app_bar":      create_chart_image(plot_top_applications(analysis['top_application_costs'])),
                    "rolling_avg":      create_chart_image(plot_rolling_average(analysis['cost_trend'])),
                    "monthly_bars":     create_chart_image(plot_monthly_bars(analysis['monthly_service'])),
                }
            except Exception as exc:
                error = f"Could not analyse file — {exc}"
        else:
            error = "No file chosen. Please pick a CSV."

    return render_template_string(PAGE, filename=filename, error=error, kpis=kpis, charts=charts)


def analyze_costs(csv_file):
    df = pd.read_csv(csv_file)
    if 'Date' not in df.columns:
        raise ValueError('CSV must include a Date column.')
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    if df['Date'].isna().all():
        raise ValueError('Could not parse any Date values.')
    if 'Cost_INR' not in df.columns:
        raise ValueError('CSV must include a Cost_INR column.')
    df['Cost_INR'] = pd.to_numeric(df['Cost_INR'], errors='coerce').fillna(0)
    df = df.dropna(subset=['Department', 'Service_Type', 'Application', 'Region', 'Date'])

    total_cost = int(df['Cost_INR'].sum())
    daily_cost = df.groupby('Date')['Cost_INR'].sum()
    avg_daily_cost = int(daily_cost.mean())

    department_cost       = df.groupby('Department')['Cost_INR'].sum().sort_values(ascending=False)
    region_cost           = df.groupby('Region')['Cost_INR'].sum().sort_values(ascending=False)
    service_costs         = df.groupby('Service_Type')['Cost_INR'].sum().sort_values(ascending=False)
    top_application_costs = df.groupby('Application')['Cost_INR'].sum().sort_values(ascending=False).head(8)

    # monthly cost by service type
    df['Month'] = df['Date'].dt.to_period('M')
    monthly_service = (
        df.groupby(['Month', 'Service_Type'])['Cost_INR']
        .sum()
        .unstack(fill_value=0)
        .sort_index()
    )

    return {
        'total_cost':            total_cost,
        'avg_daily_cost':        avg_daily_cost,
        'top_department_name':   department_cost.index[0],
        'top_department_cost':   int(department_cost.iloc[0]),
        'top_application_name':  top_application_costs.index[0],
        'top_application_cost':  int(top_application_costs.iloc[0]),
        'department_cost':       department_cost,
        'region_cost':           region_cost,
        'service_costs':         service_costs,
        'cost_trend':            daily_cost.sort_index(),
        'top_application_costs': top_application_costs,
        'monthly_service':       monthly_service,
    }


BG = '#08090b'
SURFACE = '#0e1117'
TEXT = '#e8eaf0'
MUTED = '#6b7280'
GRID = '#1a1e28'

def _fig(w=6, h=4.2):
    fig, ax = plt.subplots(figsize=(w, h), dpi=110, facecolor=BG)
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(SURFACE)
    for spine in ax.spines.values():
        spine.set_color(GRID)
    ax.tick_params(colors=MUTED, labelsize=9)
    ax.grid(color=GRID, linewidth=0.6, alpha=0.7)
    return fig, ax

def create_chart_image(fig):
    buf = BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight', facecolor=BG)
    buf.seek(0)
    data = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)
    return data

def plot_service_pie(series):
    fig, ax = plt.subplots(figsize=(5, 4.2), dpi=110, facecolor=BG)
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)
    palette = ['#5b8af7','#34d399','#f59e0b','#a78bfa','#f87171','#22d3ee','#fb923c','#e879f9']
    wedges, _, autotexts = ax.pie(
        series.values,
        labels=series.index,
        autopct='%1.1f%%',
        startangle=140,
        colors=palette[:len(series)],
        textprops={'fontsize': 9, 'color': TEXT},
        wedgeprops={'linewidth': 1.2, 'edgecolor': BG},
        pctdistance=0.78,
    )
    for t in autotexts:
        t.set_color(TEXT)
        t.set_fontsize(8)
    ax.set_title('Service share', pad=14, color=TEXT, fontsize=11, fontweight='500')
    fig.tight_layout()
    return fig

def plot_bar(series, title, ylabel):
    fig, ax = _fig()
    colors = ['#5b8af7'] + ['#2d4a8a'] * (len(series) - 1)
    bars = ax.barh(series.index[::-1], series.values[::-1], color=colors[::-1],
                   height=0.62, linewidth=0)
    ax.set_title(title, pad=12, color=TEXT, fontsize=11, fontweight='500')
    ax.set_xlabel('Cost (₹)', color=MUTED, fontsize=9)
    ax.set_ylabel(ylabel, color=MUTED, fontsize=9)
    ax.xaxis.set_tick_params(labelcolor=MUTED)
    ax.yaxis.set_tick_params(labelcolor=TEXT)
    ax.grid(axis='x', color=GRID, linewidth=0.6)
    ax.grid(axis='y', visible=False)
    for spine in ax.spines.values():
        spine.set_color(GRID)
    fig.tight_layout()
    return fig

def plot_trend_line(series):
    fig, ax = _fig(w=7, h=4)
    ax.fill_between(series.index, series.values, alpha=0.12, color='#5b8af7')
    ax.plot(series.index, series.values, color='#5b8af7', linewidth=1.8, solid_capstyle='round')
    ax.scatter(series.index, series.values, color='#5b8af7', s=28, zorder=5,
               edgecolors=BG, linewidths=1.2)
    ax.set_title('Daily cost trend', pad=12, color=TEXT, fontsize=11, fontweight='500')
    ax.set_xlabel('Date', color=MUTED, fontsize=9)
    ax.set_ylabel('Total Cost (₹)', color=MUTED, fontsize=9)
    ax.grid(color=GRID, linewidth=0.6)
    for spine in ax.spines.values():
        spine.set_color(GRID)
    fig.autofmt_xdate(rotation=30)
    fig.tight_layout()
    return fig

def plot_top_applications(series):
    fig, ax = _fig()
    colors = ['#34d399'] + ['#1a6649'] * (len(series) - 1)
    ax.barh(series.index[::-1], series.values[::-1], color=colors[::-1],
            height=0.62, linewidth=0)
    ax.set_title('Top applications', pad=12, color=TEXT, fontsize=11, fontweight='500')
    ax.set_xlabel('Cost (₹)', color=MUTED, fontsize=9)
    ax.set_ylabel('Application', color=MUTED, fontsize=9)
    ax.xaxis.set_tick_params(labelcolor=MUTED)
    ax.yaxis.set_tick_params(labelcolor=TEXT)
    ax.grid(axis='x', color=GRID, linewidth=0.6)
    ax.grid(axis='y', visible=False)
    for spine in ax.spines.values():
        spine.set_color(GRID)
    fig.tight_layout()
    return fig

def plot_rolling_average(series, window=7):
    fig, ax = _fig(w=12, h=4)
    rolling = series.rolling(window=window, min_periods=1).mean()
    # faint raw daily bars
    ax.fill_between(series.index, series.values, alpha=0.07, color='#5b8af7')
    ax.plot(series.index, series.values, color='#5b8af7', linewidth=0.8,
            alpha=0.30, solid_capstyle='round')
    # bold rolling average fill + smooth line
    ax.fill_between(series.index, rolling.values, alpha=0.18, color='#5b8af7')
    ax.plot(series.index, rolling.values, color='#5b8af7', linewidth=2.2,
            solid_capstyle='round')
    # dots only every ~14 days to avoid clutter
    step = max(1, len(series) // 26)
    sampled_idx = series.index[::step]
    sampled_val = rolling[::step]
    ax.scatter(sampled_idx, sampled_val, color='#5b8af7', s=34, zorder=5,
               edgecolors=BG, linewidths=1.4)
    ax.set_title(f'Daily cost trend  ·  {window}-day rolling avg',
                 pad=12, color=TEXT, fontsize=11, fontweight='500')
    ax.set_xlabel('Date', color=MUTED, fontsize=9)
    ax.set_ylabel('Total Cost (₹)', color=MUTED, fontsize=9)
    ax.grid(color=GRID, linewidth=0.6)
    for spine in ax.spines.values():
        spine.set_color(GRID)
    fig.autofmt_xdate(rotation=30)
    fig.tight_layout()
    return fig


def plot_monthly_bars(monthly_service):
    SERVICE_COLORS = {
        'Compute':    '#5b8af7',
        'Storage':    '#34d399',
        'Database':   '#a78bfa',
        'Networking': '#f59e0b',
    }
    services     = list(monthly_service.columns)
    n_months     = len(monthly_service)
    n_svc        = len(services)
    bar_w        = 0.7 / n_svc
    x            = np.arange(n_months)
    month_labels = [str(p) for p in monthly_service.index]

    fig, ax = _fig(w=max(12, n_months * 1.1), h=4.2)

    for i, svc in enumerate(services):
        offset = (i - n_svc / 2 + 0.5) * bar_w
        color  = SERVICE_COLORS.get(svc, '#94a3b8')
        ax.bar(
            x + offset,
            monthly_service[svc].values,
            width=bar_w * 0.88,
            color=color,
            linewidth=0,
            label=svc,
        )

    ax.set_xticks(x)
    ax.set_xticklabels(month_labels, rotation=30, ha='right', fontsize=9, color=MUTED)
    ax.set_title('Monthly cost by service type', pad=12, color=TEXT, fontsize=11, fontweight='500')
    ax.set_xlabel('Month', color=MUTED, fontsize=9)
    ax.set_ylabel('Total Cost (₹)', color=MUTED, fontsize=9)
    ax.xaxis.set_tick_params(labelcolor=MUTED)
    ax.yaxis.set_tick_params(labelcolor=MUTED)
    ax.grid(axis='y', color=GRID, linewidth=0.6)
    ax.grid(axis='x', visible=False)
    for spine in ax.spines.values():
        spine.set_color(GRID)
    ax.legend(
        fontsize=9, framealpha=0, labelcolor=TEXT,
        loc='upper left', ncol=min(4, n_svc),
        handlelength=1.2, handleheight=0.9,
        handletextpad=0.5, columnspacing=1.4,
    )
    fig.tight_layout()
    return fig


if __name__ == "__main__":
    app.run(debug=True)