import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go
from data_transformation import transform_for_time_heatmap

# Modern, sleek palette — pink stays the romance, but cream backgrounds and refined accents let it breathe
COLORS = {
    "bg": "#FDF7F5",
    "card": "#FFFFFF",
    "primary": "#E8617D",         # refined coral-rose
    "primary_soft": "#FFE4EA",
    "primary_dark": "#C44569",
    "secondary": "#9B7BB8",       # dusty plum
    "accent": "#E8B85C",          # warm champagne (replaces bright yellow)
    "text": "#2D2D3F",
    "text_muted": "#8B8593",
    "border": "#F0E5E7",
}

# Custom smooth pink gradient for heatmaps (replaces 'Pinkyl')
HEATMAP_COLORSCALE = [
    [0.0, "#FDF7F5"],
    [0.15, "#FFE4EA"],
    [0.35, "#FFB8C7"],
    [0.55, "#F47B96"],
    [0.75, "#E8617D"],
    [1.0, "#C44569"],
]

SITE_NAME = 'Closer Than You Think'

st.set_page_config(
    page_title=SITE_NAME,
    page_icon="💕",
    layout='wide',
    initial_sidebar_state='collapsed',
)


@st.cache_data
def load_data():
    df = pd.read_parquet("data/full_call_logs.parquet")
    df_calendar = pd.read_parquet("data/calendar_minutes.parquet")
    return df, df_calendar


df, df_calendar = load_data()

# === Modern design system CSS ===
st.markdown(f"""
<style>
    @import url("https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Playfair+Display:ital,wght@1,500;1,700&display=swap");

    .stApp {{
        background: {COLORS["bg"]};
    }}

    .block-container {{
        padding-top: 2rem !important;
        padding-bottom: 3rem !important;
        max-width: 1400px;
    }}

    body, .stApp, p, span, div, label, .stMarkdown {{
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        color: {COLORS["text"]};
    }}

    h1, h2, h3, h4 {{
        font-family: 'Inter', sans-serif;
        color: {COLORS["text"]};
        letter-spacing: -0.02em;
    }}

    /* Hide Streamlit chrome */
    #MainMenu, footer, header {{visibility: hidden;}}

    /* === Hero === */
    .hero {{
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
        padding: 1.5rem 1rem 2rem;
        margin-bottom: 1.5rem;
        width: 100%;
    }}
    .hero-title, .hero-subtitle, .hero-badge {{
        margin-left: auto;
        margin-right: auto;
    }}
    .hero-title {{
        font-size: 3.25rem;
        font-weight: 800;
        letter-spacing: -0.035em;
        background: linear-gradient(135deg, {COLORS["primary"]} 0%, {COLORS["secondary"]} 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin: 0 0 0.5rem 0;
        line-height: 1.05;
    }}
    .hero-italic {{
        font-family: 'Playfair Display', serif;
        font-style: italic;
        font-weight: 500;
    }}
    .hero-subtitle {{
        font-size: 1.05rem;
        color: {COLORS["text_muted"]};
        margin: 0 auto;
        font-weight: 400;
        max-width: 560px;
    }}
    .hero-badge {{
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        background: {COLORS["primary_soft"]};
        color: {COLORS["primary_dark"]};
        padding: 0.35rem 0.9rem;
        border-radius: 999px;
        font-size: 0.8rem;
        font-weight: 600;
        margin-bottom: 1rem;
        letter-spacing: 0.02em;
    }}
    .heart-pulse {{
        display: inline-block;
        animation: heartbeat 1.6s ease-in-out infinite;
    }}
    @keyframes heartbeat {{
        0%, 100% {{ transform: scale(1); }}
        25% {{ transform: scale(1.15); }}
        50% {{ transform: scale(1); }}
        75% {{ transform: scale(1.12); }}
    }}

    /* === Filter card === */
    .filter-card {{
        background: {COLORS["card"]};
        border: 1px solid {COLORS["border"]};
        border-radius: 16px;
        padding: 1.25rem 1.5rem 0.75rem;
        box-shadow: 0 1px 3px rgba(232, 97, 125, 0.05);
        margin-bottom: 2rem;
    }}

    /* === Section header === */
    .section-header {{
        display: flex;
        align-items: center;
        gap: 0.85rem;
        margin: 2.5rem 0 1.25rem 0;
    }}
    .section-icon {{
        width: 40px;
        height: 40px;
        border-radius: 12px;
        background: linear-gradient(135deg, {COLORS["primary_soft"]} 0%, #FFF1F5 100%);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.2rem;
        flex-shrink: 0;
    }}
    .section-title {{
        font-size: 1.35rem;
        font-weight: 700;
        color: {COLORS["text"]};
        margin: 0;
        letter-spacing: -0.015em;
    }}
    .section-sub {{
        font-size: 0.8rem;
        color: {COLORS["text_muted"]};
        margin: 0;
        font-weight: 500;
    }}
    .section-line {{
        flex: 1;
        height: 1px;
        background: linear-gradient(to right, {COLORS["border"]}, transparent);
        margin-left: 0.5rem;
    }}

    /* === Metric cards (custom grid, not st.metric) === */
    .metrics-grid {{
        display: grid;
        grid-template-columns: repeat(6, 1fr);
        gap: 0.9rem;
    }}
    @media (max-width: 1100px) {{
        .metrics-grid {{ grid-template-columns: repeat(3, 1fr); }}
    }}
    @media (max-width: 600px) {{
        .metrics-grid {{ grid-template-columns: repeat(2, 1fr); }}
    }}
    .metric-card {{
        background: {COLORS["card"]};
        border: 1px solid {COLORS["border"]};
        border-radius: 16px;
        padding: 1.15rem 1.1rem;
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 1px 3px rgba(232, 97, 125, 0.05);
        position: relative;
        overflow: hidden;
    }}
    .metric-card::before {{
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, {COLORS["primary"]} 0%, {COLORS["secondary"]} 100%);
        opacity: 0;
        transition: opacity 0.25s ease;
    }}
    .metric-card:hover {{
        transform: translateY(-4px);
        box-shadow: 0 14px 28px rgba(232, 97, 125, 0.14);
        border-color: {COLORS["primary_soft"]};
    }}
    .metric-card:hover::before {{ opacity: 1; }}
    .metric-icon {{
        width: 34px;
        height: 34px;
        border-radius: 10px;
        background: {COLORS["primary_soft"]};
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1rem;
        margin-bottom: 0.7rem;
    }}
    .metric-value {{
        font-size: 1.7rem;
        font-weight: 800;
        color: {COLORS["text"]};
        line-height: 1.05;
        letter-spacing: -0.025em;
    }}
    .metric-unit {{
        font-size: 0.85rem;
        font-weight: 600;
        color: {COLORS["text_muted"]};
        margin-left: 0.2rem;
    }}
    .metric-label {{
        font-size: 0.7rem;
        color: {COLORS["text_muted"]};
        margin-top: 0.45rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.07em;
    }}

    /* === Chart card === */
    .chart-card {{
        background: {COLORS["card"]};
        border: 1px solid {COLORS["border"]};
        border-radius: 16px;
        padding: 1rem 1.25rem;
        box-shadow: 0 1px 3px rgba(232, 97, 125, 0.05);
        margin-bottom: 1rem;
    }}

    /* === Chart cards (keyed containers) === */
    .st-key-filter_card,
    .st-key-cal_card,
    .st-key-time_heatmap_card,
    .st-key-trend_card,
    .st-key-histogram_card {{
        background: {COLORS["card"]} !important;
        border: 1px solid {COLORS["border"]} !important;
        border-radius: 16px !important;
        padding: 1rem 1.25rem !important;
        box-shadow: 0 1px 3px rgba(232, 97, 125, 0.05) !important;
        margin-bottom: 1rem !important;
    }}
    .st-key-filter_card > div,
    .st-key-cal_card > div,
    .st-key-time_heatmap_card > div,
    .st-key-trend_card > div,
    .st-key-histogram_card > div {{
        background: {COLORS["card"]} !important;
        border-radius: 16px !important;
    }}

    /* === Widget styling === */
    .stSelectbox label, .stSlider label, .stRadio label, .stSelectSlider label {{
        font-size: 0.75rem !important;
        font-weight: 600 !important;
        color: {COLORS["text_muted"]} !important;
        text-transform: uppercase;
        letter-spacing: 0.06em;
    }}
    .stSelectbox > div > div, .stSlider > div, .stSelectSlider > div {{
        font-family: 'Inter', sans-serif;
    }}

    /* Radio pills */
    .stRadio [role="radiogroup"] {{
        gap: 0.5rem;
    }}
    .stRadio [role="radiogroup"] > label {{
        background: {COLORS["bg"]};
        padding: 0.35rem 0.9rem;
        border-radius: 10px;
        border: 1px solid {COLORS["border"]};
        transition: all 0.2s ease;
    }}
    .stRadio [role="radiogroup"] > label:hover {{
        border-color: {COLORS["primary"]};
        background: {COLORS["primary_soft"]};
    }}

    /* Slider thumb color */
    .stSlider [data-baseweb="slider"] [role="slider"],
    .stSelectSlider [data-baseweb="slider"] [role="slider"] {{
        background: {COLORS["primary"]} !important;
        border-color: {COLORS["primary"]} !important;
    }}

    /* Footer */
    .footer {{
        text-align: center;
        padding: 2.5rem 1rem 0.5rem;
        color: {COLORS["text_muted"]};
        font-size: 0.85rem;
    }}
    .footer-heart {{
        color: {COLORS["primary"]};
        display: inline-block;
        animation: heartbeat 1.6s ease-in-out infinite;
    }}

    /* Plotly modebar styling */
    .js-plotly-plot .modebar {{
        background: transparent !important;
    }}
    .js-plotly-plot .modebar-btn path {{
        fill: {COLORS["text_muted"]} !important;
    }}
    .js-plotly-plot .modebar-btn:hover path {{
        fill: {COLORS["primary"]} !important;
    }}
</style>
""", unsafe_allow_html=True)


# === Helpers ===
def section_header(emoji, title, subtitle=""):
    sub_html = f'<p class="section-sub">{subtitle}</p>' if subtitle else ''
    st.markdown(f"""
    <div class="section-header">
        <div class="section-icon">{emoji}</div>
        <div>
            <h2 class="section-title">{title}</h2>
            {sub_html}
        </div>
        <div class="section-line"></div>
    </div>
    """, unsafe_allow_html=True)


def metric_card(emoji, value, label, unit=""):
    unit_html = f'<span class="metric-unit">{unit}</span>' if unit else ''
    return (
        f'<div class="metric-card">'
        f'<div class="metric-icon">{emoji}</div>'
        f'<div class="metric-value">{value}{unit_html}</div>'
        f'<div class="metric-label">{label}</div>'
        f'</div>'
    )


def style_fig(fig, height=380, show_grid_y=False):
    """Apply consistent modern styling to any plotly figure."""
    fig.update_layout(
        height=height,
        margin=dict(l=20, r=20, t=20, b=40),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Inter, sans-serif', color=COLORS['text'], size=12),
        hoverlabel=dict(
            font_family='Inter, sans-serif',
            font_size=13,
            bgcolor=COLORS['card'],
            bordercolor=COLORS['primary'],
            font_color=COLORS['text'],
        ),
    )
    fig.update_xaxes(
        showgrid=False,
        zeroline=False,
        showline=False,
        tickfont=dict(size=11, color=COLORS['text_muted']),
    )
    fig.update_yaxes(
        showgrid=show_grid_y,
        gridcolor=COLORS['border'],
        zeroline=False,
        showline=False,
        tickfont=dict(size=11, color=COLORS['text_muted']),
    )
    return fig


PLOTLY_CONFIG = {
    'displayModeBar': 'hover',
    'displaylogo': False,
    'modeBarButtonsToRemove': ['lasso2d', 'select2d', 'autoScale2d', 'toggleSpikelines'],
    'toImageButtonOptions': {'format': 'png', 'filename': 'closer-than-you-think', 'scale': 2},
}


# === Hero ===
st.markdown(f"""
<div class="hero">
    <div class="hero-badge"><span class="heart-pulse">💕</span> Singapore × New Zealand</div>
    <h1 class="hero-title">Closer Than <span class="hero-italic">You Think</span></h1>
    <p class="hero-subtitle">A love story told through phone calls — across timezones, oceans, and 8,400 km.</p>
</div>
""", unsafe_allow_html=True)


# === Filters ===
with st.container(key="filter_card"):
    fcol1, fcol2 = st.columns([3, 2])

    with fcol1:
        unique_month_years = df['Start_Month_Year_SG'].unique()
        start_month_year, end_month_year = st.select_slider(
            "Date Range",
            options=unique_month_years,
            value=(unique_month_years[0], unique_month_years[-1]),
            key="date_range_slider",
        )

    with fcol2:
        timezone = st.radio(
            "Timezone",
            ["Singapore (SG)", "New Zealand (NZ)"],
            horizontal=True,
            key="timezone_radio",
        )
        tz_suffix = "SG" if timezone == "Singapore (SG)" else "NZ"

filtered_df = df[
    (df[f'Start_Month_Year_{tz_suffix}'] >= start_month_year) &
    (df[f'End_Month_Year_{tz_suffix}'] <= end_month_year)
]


# === Overview metrics ===
section_header("✨", "Overview", f"{start_month_year} → {end_month_year}")

total_calls = len(filtered_df)
total_duration = filtered_df["Call_Length_Minutes"].sum()
avg_duration = filtered_df["Call_Length_Minutes"].mean() if total_calls else 0
median_duration = filtered_df["Call_Length_Minutes"].median() if total_calls else 0
max_duration = filtered_df["Call_Length_Minutes"].max() if total_calls else 0

metrics_html = (
    '<div class="metrics-grid">'
    + metric_card("📞", f"{total_calls:,}", "Total Calls")
    + metric_card("⏳", f"{total_duration/60:,.0f}", "Total Hours")
    + metric_card("⏱️", f"{total_duration:,.0f}", "Total Minutes")
    + metric_card("💬", f"{avg_duration:,.0f}", "Avg Duration", unit="min")
    + metric_card("📊", f"{median_duration:,.0f}", "Median Duration", unit="min")
    + metric_card("🏆", f"{max_duration:,.0f}", "Longest Call", unit="min")
    + '</div>'
)
st.html(metrics_html)


# === SECTION: Calendar heatmap ===
# Custom Plotly heatmap that fits the full date range into one viewport-width row.
# Uses month-based x-axis labels with subtle month divider lines for readability.
section_header("📅", "Our Call Calendar", f"Each square is a day · showing {tz_suffix} time")

mins_col = f"Total_Mins_{tz_suffix}"

start_dt_filter = pd.to_datetime(start_month_year, format='%Y-%m')
end_dt_filter = pd.to_datetime(end_month_year, format='%Y-%m') + pd.DateOffset(months=1)

calendar_data = df_calendar[
    (df_calendar['date'] >= start_dt_filter) &
    (df_calendar['date'] < end_dt_filter)
].copy()

# Sunday-first weekday (Sun=0, Sat=6)
calendar_data["Weekday"] = (calendar_data['date'].dt.dayofweek + 1) % 7
calendar_data["Week_Start_Date"] = calendar_data['date'] - pd.to_timedelta(calendar_data["Weekday"], unit='d')

heatmap_data = calendar_data.pivot_table(
    index="Weekday",
    columns="Week_Start_Date",
    values=mins_col,
    aggfunc="sum",
    fill_value=0,
).reindex(range(7), fill_value=0)

week_start_dates = pd.Series(sorted(heatmap_data.columns))
heatmap_data = heatmap_data[week_start_dates]

# Per-cell actual date for the hover tooltip
date_text = [
    [(wsd + pd.Timedelta(days=d)).strftime('%a, %d %b %Y') for wsd in week_start_dates]
    for d in range(7)
]

# Month tick positions: first week of each new month (based on midweek date)
month_tick_x, month_tick_label = [], []
prev_month = None
for i, wsd in enumerate(week_start_dates):
    midweek = wsd + pd.Timedelta(days=3)
    if midweek.month != prev_month:
        month_tick_x.append(i)
        month_tick_label.append(midweek.strftime('%b %Y'))
        prev_month = midweek.month

# Subtle vertical lines between months
month_divider_shapes = [
    dict(
        type='line',
        xref='x', yref='y',
        x0=month_tick_x[i] - 0.5, x1=month_tick_x[i] - 0.5,
        y0=-0.5, y1=6.5,
        line=dict(color=COLORS['border'], width=2),
    )
    for i in range(1, len(month_tick_x))
]

fig_cal = go.Figure(data=go.Heatmap(
    z=heatmap_data.values,
    x=list(range(len(week_start_dates))),
    y=['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'],
    customdata=date_text,
    colorscale=HEATMAP_COLORSCALE,
    hoverongaps=False,
    hovertemplate=(
        "<b>%{customdata}</b><br>"
        "<span style='color:#8B8593'>Minutes:</span> %{z:,.0f}<extra></extra>"
    ),
    showscale=False,
    xgap=3,
    ygap=3,
    zmin=0,
))

fig_cal.update_layout(
    xaxis=dict(
        tickmode='array',
        tickvals=month_tick_x,
        ticktext=month_tick_label,
        tickfont=dict(size=11, color=COLORS['text']),
        showgrid=False, zeroline=False, showline=False,
        side='bottom',
    ),
    yaxis=dict(
        tickfont=dict(size=11, color=COLORS['text_muted']),
        autorange='reversed',
        showgrid=False, zeroline=False, showline=False,
    ),
    shapes=month_divider_shapes,
    hoverlabel=dict(
        font_family='Inter, sans-serif',
        font_size=13,
        font_color=COLORS['text'],
        bgcolor=COLORS['card'],
        bordercolor=COLORS['primary'],
    ),
    height=280,
    margin=dict(l=40, r=20, t=20, b=45),
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    font=dict(family='Inter, sans-serif', color=COLORS['text'], size=12),
)

with st.container(key="cal_card"):
    st.plotly_chart(fig_cal, use_container_width=True, config=PLOTLY_CONFIG)


# === SECTION: Time of day heatmap ===
section_header("⏰", "Favourite Time To Talk", f"Showing {tz_suffix} time")

df_day_hour = transform_for_time_heatmap(filtered_df)

all_days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
df_day_hour["Day_Name"] = df_day_hour["Day_of_Week"].map(lambda x: all_days[x])

heatmap_data = df_day_hour.pivot_table(
    index="Day_Name",
    columns="Hour",
    values=f"minutes_{tz_suffix}",
    aggfunc="sum",
    fill_value=0,
)
heatmap_data = heatmap_data.reindex(all_days)

# Tick at every 3 hours for readability
hour_tickvals = [0, 3, 6, 9, 12, 15, 18, 21]
hour_ticktext = ['12 AM', '3 AM', '6 AM', '9 AM', '12 PM', '3 PM', '6 PM', '9 PM']

fig_time = go.Figure(data=go.Heatmap(
    z=heatmap_data.values,
    x=list(range(24)),
    y=heatmap_data.index,
    colorscale=HEATMAP_COLORSCALE,
    showscale=False,
    hoverongaps=False,
    hovertemplate=(
        "<b>%{y}</b> at <b>%{x}:00</b><br>"
        "<span style='color:#8B8593'>Duration:</span> %{z:,.0f} min<extra></extra>"
    ),
    xgap=3,
    ygap=3,
))

fig_time.update_layout(
    xaxis=dict(
        tickmode='array',
        tickvals=hour_tickvals,
        ticktext=hour_ticktext,
        tickfont=dict(size=11, color=COLORS["text_muted"]),
        showgrid=False,
    ),
    yaxis=dict(
        tickfont=dict(size=11, color=COLORS["text_muted"]),
        categoryorder='array',
        categoryarray=all_days,
        autorange="reversed",
        showgrid=False,
    ),
    hoverlabel=dict(
        font_family="Inter, sans-serif",
        font_size=13,
        font_color=COLORS["text"],
        bgcolor=COLORS["card"],
        bordercolor=COLORS["primary"],
    ),
    height=380,
    margin=dict(l=40, r=20, t=20, b=40),
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    font=dict(family='Inter, sans-serif', color=COLORS["text"], size=12),
)

with st.container(key="time_heatmap_card"):
    st.plotly_chart(fig_time, use_container_width=True, config=PLOTLY_CONFIG)


# === SECTION: Call duration trend ===
section_header("📈", "How Our Calls Have Grown", "Track total or average call time over your chosen interval")

with st.container(key="trend_card"):
    ctrl1, ctrl2, _ = st.columns([1, 1, 2])
    with ctrl1:
        time_interval = st.selectbox("Interval", ["Days", "Weeks", "Months"], index=1, key="trend_interval")
    with ctrl2:
        metric = st.selectbox("Metric", ["Total Minutes", "Average Minutes"], key="trend_metric")

    df_call_trend = df_calendar[
        (df_calendar['date'] >= start_dt_filter) &
        (df_calendar['date'] < end_dt_filter)
    ].copy()
    df_call_trend['date'] = pd.to_datetime(df_call_trend['date'])
    mins_col = f"Total_Mins_{tz_suffix}"
    trend_data = df_call_trend[['date', mins_col]].dropna()

    if time_interval == "Days":
        trend_data["Interval"] = trend_data["date"]
    elif time_interval == "Weeks":
        trend_data["Interval"] = trend_data["date"] - pd.to_timedelta(trend_data["date"].dt.dayofweek + 1, unit='d')
    else:
        trend_data["Interval"] = trend_data["date"].dt.to_period('M').dt.start_time

    if metric == "Average Minutes":
        trend_data = trend_data.groupby("Interval")[mins_col].mean().reset_index()
        y_axis_label = "Avg Minutes"
    else:
        trend_data = trend_data.groupby("Interval")[mins_col].sum().reset_index()
        y_axis_label = "Total Minutes"

    trend_data = trend_data.sort_values("Interval")

    if time_interval == "Months":
        trend_data["Interval_Label"] = trend_data["Interval"].dt.strftime("%b %Y")
    else:
        trend_data["Interval_Label"] = trend_data["Interval"].dt.strftime("%d %b %Y")

    fig_duration = go.Figure()
    fig_duration.add_trace(go.Scatter(
        x=trend_data["Interval_Label"],
        y=trend_data[mins_col],
        mode='lines+markers',
        line=dict(color=COLORS["primary"], width=2.5, shape='spline', smoothing=0.8),
        marker=dict(color=COLORS["primary"], size=7, line=dict(color=COLORS["card"], width=2)),
        fill='tozeroy',
        fillcolor='rgba(232, 97, 125, 0.08)',
        hovertemplate=(
            f"<b>%{{x}}</b><br>"
            f"<span style='color:#8B8593'>{y_axis_label}:</span> %{{y:,.1f}}<extra></extra>"
        ),
    ))

    fig_duration.update_layout(
        height=420,
        margin=dict(l=20, r=20, t=20, b=50),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Inter, sans-serif', color=COLORS["text"], size=12),
        hoverlabel=dict(
            font_family="Inter, sans-serif",
            font_size=13,
            font_color=COLORS["text"],
            bgcolor=COLORS["card"],
            bordercolor=COLORS["primary"],
        ),
        hovermode='x unified',
        xaxis=dict(
            showgrid=False,
            showline=False,
            zeroline=False,
            tickfont=dict(size=10, color=COLORS["text_muted"]),
            showspikes=True,
            spikemode='across',
            spikethickness=1,
            spikecolor=COLORS["primary_soft"],
            spikedash='solid',
        ),
        yaxis=dict(
            title=dict(text=y_axis_label, font=dict(size=11, color=COLORS["text_muted"])),
            showgrid=True,
            gridcolor=COLORS["border"],
            zeroline=False,
            showline=False,
            tickfont=dict(size=10, color=COLORS["text_muted"]),
        ),
    )

    st.plotly_chart(fig_duration, use_container_width=True, config=PLOTLY_CONFIG)


# === SECTION: Distribution histogram ===
section_header("📊", "Call Duration Distribution", "How long do our calls usually last?")

with st.container(key="histogram_card"):
    bcol, _ = st.columns([1, 3])
    with bcol:
        bin_size = st.slider('Bin Size', min_value=5, max_value=50, value=30, step=5, key="bin_size_slider")

    # Build histogram with explicit bin edges anchored at 0 so no bin spans negative values
    call_durations = filtered_df["Call_Length_Minutes"].dropna()
    if len(call_durations):
        max_val = float(call_durations.max())
        bin_width = max(1.0, max_val / max(bin_size, 1))
    else:
        max_val, bin_width = 60.0, 5.0
    x_max = max_val + bin_width  # extend by one bin width so the max value isn't clipped

    fig_distribution = go.Figure(data=go.Histogram(
        x=call_durations,
        xbins=dict(start=0, end=x_max, size=bin_width),
        marker=dict(
            color=COLORS["primary"],
            line=dict(color=COLORS["primary_dark"], width=1),
        ),
        opacity=0.85,
        hovertemplate=(
            "<b>%{x} min</b><br>"
            "<span style='color:#8B8593'>Calls:</span> %{y}<extra></extra>"
        ),
    ))
    fig_distribution.update_layout(
        height=420,
        margin=dict(l=20, r=20, t=20, b=50),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Inter, sans-serif', color=COLORS["text"], size=12),
        hoverlabel=dict(
            font_family="Inter, sans-serif",
            font_size=13,
            font_color=COLORS["text"],
            bgcolor=COLORS["card"],
            bordercolor=COLORS["primary"],
        ),
        bargap=0.08,
        xaxis=dict(
            title=dict(text="Call Duration (minutes)", font=dict(size=11, color=COLORS["text_muted"])),
            showgrid=False,
            zeroline=False,
            showline=False,
            rangemode='nonnegative',
            range=[0, x_max],
            tickfont=dict(size=10, color=COLORS["text_muted"]),
        ),
        yaxis=dict(
            title=dict(text="Number of Calls", font=dict(size=11, color=COLORS["text_muted"])),
            showgrid=True,
            gridcolor=COLORS["border"],
            zeroline=False,
            showline=False,
            tickfont=dict(size=10, color=COLORS["text_muted"]),
        ),
    )

    st.plotly_chart(fig_distribution, use_container_width=True, config=PLOTLY_CONFIG)


# === Footer ===
st.markdown(f"""
<div class="footer">
    Built with <span class="footer-heart">❤</span> by Imran &middot; {SITE_NAME}
</div>
""", unsafe_allow_html=True)
