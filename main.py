import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go
from data_transformation import transform_for_time_heatmap

# Updated color palette with better contrast
COLORS = {
    "pink": "#FF9BB3",  # Primary background color
    "yellow": "#FFE082",  # Accent color for headers and highlights
    "blue": "#A2DDF0",  # Secondary accent color
    "white": "#FFFFFF",  # For text and backgrounds
    "black": "#333333",  # For text and borders
    "light_bg": "#FFE6EE",  # Light pink background
    "dark_text": "#333333",  # Dark text for contrast
    "pink_gradient": [
        "#E0E0E0", "#F5F5F5", "#FFE1EC", "#FFD1E1", 
        "#FFC2D6", "#FFB3CB", "#FFA3C1", "#FF94B6",
        "#FF85AB", "#FF75A0", "#FF6696", "#FF568B"
    ]
}

DEFAULT_HEATMAP_COLORSCALE = 'Pinkyl'
SITE_NAME = 'Closer Than You Think'

# Set page config for mobile-first design
st.set_page_config(page_title=SITE_NAME, page_icon="💕", layout='wide')

# Load data from parquet file
@st.cache_data
def load_data():
    df = pd.read_parquet("data/full_call_logs.parquet") # parquet files retain the data types
    df_calendar = pd.read_parquet("data/calendar_minutes.parquet")
    return df, df_calendar

# Load the data
df, df_calendar = load_data()

# Custom CSS for mobile optimization, better readability, and custom font
st.markdown(f"""
<style>
    @import url("https://fonts.googleapis.com/css2?family=Montserrat:ital,wght@0,100..900;1,100..900&family=Nunito:ital,wght@0,200..1000;1,200..1000&display=swap");
    body {{
        background-color: {COLORS["light_bg"]};
        color: {COLORS["dark_text"]};
        font-family: 'Montserrat', 'Nunito', sans-serif;
    }}
    h1, h2, h3 {{
        margin-top: 0.8rem !important;
        margin-bottom: 0.8rem !important;
        color: {COLORS["dark_text"]} !important;
        font-weight: 700; /* Bold for headings */
    }}
    .metric-container {{
    background-color: {COLORS["white"]};
    border-radius: 10px;
    padding: 10px;
    }}
    .section-header {{
        padding: 0.75rem;
        border-radius: 5px;
        margin-bottom: 1rem;
        margin-top: 1.5rem;
        font-weight: bold;
        text-align: center;
        font-size: 1.25rem;
        background-color: {COLORS["yellow"]};
        color: {COLORS["dark_text"]};
        border: 1px solid {COLORS["black"]};
    }}
    .stRadio > div {{
        display: flex;
        justify-content: center;
    }}
    .stRadio label {{
        color: {COLORS["dark_text"]} !important;
        font-weight: 500 !important;
    }}
</style>
""", unsafe_allow_html=True)

# App title and introduction with custom styling
st.markdown(f"""
<h1 style='text-align: center; color: {COLORS["dark_text"]}; background-color: {COLORS["pink"]}; 
padding: 1rem; border-radius: 10px; margin-bottom: 0.5rem;'>{SITE_NAME} 👩‍❤️‍👨</h1>
<p style='text-align: center; margin-bottom: 2rem; color: {COLORS["black"]}; font-weight: 500;'>
Visualizing our connection across Singapore and New Zealand</p>
""", unsafe_allow_html=True)

# Simplified mobile-friendly filters

# Month-Year Range Filter
unique_month_years = df[f'Start_Month_Year_SG'].unique() # get the unique month-years. it is possible for start and end month year to have different months although it is highly unlikely.
start_month_year, end_month_year = st.select_slider(
    "",
    options=unique_month_years,
    value=(unique_month_years[0], unique_month_years[-1])
)

# Button to switch between SG and NZ timings
timezone = st.radio("", ["Singapore (SG)", "New Zealand (NZ)"], horizontal=True)
tz_suffix = "SG" if timezone == "Singapore (SG)" else "NZ"

# Filter data based on selected month-year range
filtered_df = df[(df[f'Start_Month_Year_{tz_suffix}'] >= start_month_year) & (df[f'End_Month_Year_{tz_suffix}'] <= end_month_year)]

# Basic statistics at the top for immediate insights
st.markdown(f"""
<div class='section-header' style='background-color: {COLORS["yellow"]}; color: {COLORS["dark_text"]};'>
Overview
</div>
""", unsafe_allow_html=True)

total_calls = len(filtered_df)
total_duration = filtered_df["Call_Length_Minutes"].sum()
avg_duration = filtered_df["Call_Length_Minutes"].mean()
median_duration = filtered_df["Call_Length_Minutes"].median()
max_duration = filtered_df["Call_Length_Minutes"].max()

# Mobile-friendly metrics layout with better contrast
col1, col2 = st.columns(2)
with col1:
    st.metric("Total Calls", f"{total_calls}")
    st.metric("Total Hours", f"{total_duration/60:,.0f}")
    st.metric("Median Call Duration (min)", f"{median_duration:,.0f}")
    
with col2:
    st.metric("Total Minutes", f"{total_duration:,.0f}")
    st.metric("Avg Call Duration (min)", f"{avg_duration:,.0f}")
    st.metric("Max Call Duration (min)", f"{max_duration:,.0f}")

# Add a divider
st.markdown("---")

#####

# SECTION: Calendar heatmap

st.markdown(f"""
<div class='section-header' style='background-color: {COLORS["yellow"]}; color: {COLORS["dark_text"]};'>
Our Call Calendar ({tz_suffix})
</div>
""", unsafe_allow_html=True)

# Use the appropriate datetime columns based on the selected timezone
mins_col = f"Total_Mins_{tz_suffix}"

# Reference df_calendar filtered
start_dt_filter =  pd.to_datetime(start_month_year, format='%Y-%m')
end_dt_filter = pd.to_datetime(end_month_year, format='%Y-%m') + pd.DateOffset(months=1) # include the last month itself also
calendar_data = df_calendar[(df_calendar[f'date'] >= start_dt_filter) 
                            & (df_calendar[f'date'] < end_dt_filter)]

# Extract day for the calendar heatmap
calendar_data["Weekday"] = (calendar_data['date'].dt.dayofweek + 1) % 7

# Ensure the week start date is always a Sunday
calendar_data["Week_Start_Date"] = calendar_data['date'] - pd.to_timedelta(calendar_data["Weekday"], unit='d')

# Create a pivot table for the heatmap (using Duration_Minutes for the heatmap values)
heatmap_data = calendar_data.pivot_table(
    index="Weekday",  # Rows: Days of the week (Sunday to Saturday)
    columns="Week_Start_Date",   # Columns: Start date of each week (Sunday)
    values=mins_col,  # Values: Total call duration in minutes
    aggfunc="sum",    # Sum the durations for each day
    fill_value=0      # Fill missing values with 0
)

# Ensure customdata includes the full datetime
customdata = calendar_data.pivot_table(
    index="Weekday",
    columns="Week_Start_Date",
    values="date",  # Pass the full date
    aggfunc="first",  # Use the first available date per week-day pair
    fill_value=pd.NaT  # Fill missing values with NaT (not a time)
)

# Convert datetime to string format with minutes
customdata = customdata.map(lambda x: x.strftime('%d %b %y') if pd.notna(x) else '')

# Calculate the start date of each week for the x-axis labels
week_start_dates = calendar_data["Week_Start_Date"].unique()
week_start_dates = pd.Series(week_start_dates).sort_values().reset_index(drop=True)
week_start_dates = pd.to_datetime(week_start_dates)  # Ensure datetime format
week_start_labels = week_start_dates.dt.strftime("%d %b %y")  # Format for x-axis labels

# Reorder the heatmap data columns based on chronological order
heatmap_data = heatmap_data[week_start_dates]
customdata = customdata[week_start_dates]

# Create the heatmap using plotly
fig = go.Figure(data=go.Heatmap(
    z=heatmap_data.values,  # Data values (call durations)
    x=week_start_labels,  # Use formatted start dates as x-axis labels
    y=["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"],  # Weekday labels (starting from Sunday)
    colorscale=DEFAULT_HEATMAP_COLORSCALE,  # GitHub-like green color scale
    hoverongaps=False,
    hovertemplate=(
        "Date: %{customdata}<br>"  # Add full date and time
        "Day: %{y}<br>"
        "Duration (min): %{z:,.0f}<extra></extra>"
    ),
    customdata=customdata.values,  # Attach full date-time data
    showscale=False,
))

week_start_labels = list(week_start_dates.dt.strftime("%d %b %y"))  # Convert to list

# Customize layout
fig.update_layout(
    xaxis=dict(
        # title="Week Start Date (Sunday)",
        # title_font=dict(size=12, color=COLORS["dark_text"]),  # Larger font for better readability
        # showticklabels=False,  # Hide tick labels
        # ticks="",  # Remove tick markers
        tickfont=dict(size=10, color=COLORS["dark_text"]),  # Larger font for better readability
        tickvals=list(range(len(week_start_labels))),  # Use indices for tick positions
        ticktext=week_start_labels,  # Use formatted start dates as tick labels
        tickangle=40,  # Tilt the labels for the x-axis diagonally
    ),
    yaxis=dict(
        tickfont=dict(size=12, color=COLORS["dark_text"]),  # Larger font for better readability
        autorange="reversed",  # Reverse the y-axis to match GitHub's layout
    ),
    hoverlabel=dict(
        font_family="Montserrat, Nunito, sans-serif",  # Match Streamlit font
        font_size=12,  # Set font size
        font_color=COLORS["white"],  # Set font color
        bgcolor=COLORS["pink"],  # Set background color of hover text
        bordercolor=COLORS["black"],  # Set border color of hover text
    ),
    height=400,
    width = 2000,
    margin=dict(l=50, r=50, t=50, b=70),
    # paper_bgcolor=COLORS["white"],
    # plot_bgcolor=COLORS["white"],
    font=dict(color=COLORS["dark_text"], size=12),
    dragmode=False,  # This disables zoom on drag
    hovermode='closest'
)

# Display the heatmap
# st.plotly_chart(fig, use_container_width=True)

# Convert the Plotly figure to HTML
plotly_html = fig.to_html(full_html=False)

# Create a scrollable HTML container with custom CSS
scrollable_html = f"""
<style>
    @import url("https://fonts.googleapis.com/css2?family=Montserrat:ital,wght@0,100..900;1,100..900&family=Nunito:ital,wght@0,200..1000;1,200..1000&display=swap");
    .scrollable-container {{
        width: 100%;
        overflow-x: auto;
        font-family: 'Montserrat', 'Nunito', sans-serif;
        color: {COLORS["dark_text"]};
        background-color: {COLORS["pink"]};  /* Fill the container with a specific color */
    }}
    .scrollable-container .plotly .hovertext {{
        font-family: 'Montserrat', 'Nunito', sans-serif !important;
        color: {COLORS["dark_text"]} !important;
    }}
    .scrollable-container .plotly .xaxis {{
        font-family: 'Montserrat', 'Nunito', sans-serif !important;
        color: {COLORS["dark_text"]} !important;
    }}
</style>
<div class="scrollable-container">
    {plotly_html}
</div>
"""

# Display the scrollable chart in Streamlit
st.components.v1.html(scrollable_html, height=420)

# Add a divider
st.markdown("---")

#####

#####

# SECTION: Time of day heatmap
st.markdown(f"""
<div class='section-header' style='background-color: {COLORS["yellow"]}; color: {COLORS["dark_text"]};'>
Favourite Time To Talk ({tz_suffix})
</div>
""", unsafe_allow_html=True)

### DATA TRANSFORMATION ###

df_day_hour = transform_for_time_heatmap(filtered_df)

### END OF DATA TRANSFORMATION ###


# Ensure all hour-day combinations are present (for empty cells)
all_days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]

# Map numeric Day_of_Week to day names
df_day_hour["Day_Name"] = df_day_hour["Day_of_Week"].map(lambda x: all_days[x])

# Create a pivot table for the heatmap
heatmap_data = df_day_hour.pivot_table(
    index="Day_Name",    # Rows: Days of the week (as names)
    columns="Hour",      # Columns: Hours of the day
    values=f"minutes_{tz_suffix}",  # Values: Total call duration in minutes
    aggfunc="sum",       # Sum the durations for each day-hour combination
    fill_value=0         # Fill missing values with 0
)

# Reorder the rows to start with Sunday and end with Saturday
heatmap_data = heatmap_data.reindex(all_days)

# Create the heatmap using plotly
fig_time = go.Figure(data=go.Heatmap(
    z=heatmap_data.values,  # Data values (call durations)
    x=list(range(24)),      # Hours of the day (0 to 23)
    y=heatmap_data.index,   # Days of the week (as names)
    colorscale=DEFAULT_HEATMAP_COLORSCALE,  # Updated color scheme
    showscale=False,
    hoverongaps=False,
    hovertemplate=(
        "Day: %{y}<br>"
        "Hour: %{x}<br>"
        "Duration (min): %{z:,.0f}<extra></extra>"
    )
))

# Customize layout
fig_time.update_layout(
    xaxis=dict(
        tickmode='array',
        tickvals=list(range(24)),
        ticktext=[f"{h % 12 or 12} {'AM' if h < 12 else 'PM'}" for h in range(24)],
        title="Hour of Day",
        title_font=dict(size=12, color=COLORS["dark_text"]),
        tickfont=dict(size=10, color=COLORS["dark_text"]),
        tickangle=-40,
    ),
    yaxis=dict(
        # title="Day of Week",
        # title_font=dict(size=12, color=COLORS["dark_text"]),
        tickfont=dict(size=12, color=COLORS["dark_text"]),
        categoryorder='array',  # Ensure the y-axis is ordered as specified
        categoryarray=all_days,  # Order: Sunday to Saturday
        autorange="reversed"
    ),
    hoverlabel=dict(
    font_family="Montserrat, Nunito, sans-serif",  # Match Streamlit font
    font_size=12,  # Set font size
    font_color=COLORS["white"],  # Set font color
    bgcolor=COLORS["pink"],  # Set background color of hover text
    bordercolor=COLORS["black"],  # Set border color of hover text
    ),
    height=400,
    width=2000,
    margin=dict(l=50, r=50, t=50, b=70),
    paper_bgcolor=COLORS["white"],
    plot_bgcolor=COLORS["white"],
    font=dict(color=COLORS["dark_text"], size=14),
    dragmode=False,  # This disables zoom on drag
    hovermode='closest'
)

# Display the heatmap
# st.plotly_chart(fig_time, use_container_width=True)

# Convert the Plotly figure to HTML
plotly_html = fig_time.to_html(full_html=False)

# Create a scrollable HTML container with custom CSS
scrollable_html = f"""
<style>
    @import url("https://fonts.googleapis.com/css2?family=Montserrat:ital,wght@0,100..900;1,100..900&family=Nunito:ital,wght@0,200..1000;1,200..1000&display=swap");
    .scrollable-container {{
        display: flex;
        height: 100%;             /* Ensure the container takes full height */
        width: 100%;
        overflow-x: auto;
        font-family: 'Montserrat', 'Nunito', sans-serif;
        color: {COLORS["dark_text"]};
        background-color: {COLORS["white"]};  /* Fill the container with a specific color */
    }}
    .scrollable-container .plotly .hovertext {{
        font-family: 'Montserrat', 'Nunito', sans-serif !important;
        color: {COLORS["dark_text"]} !important;
    }}
    .scrollable-container .plotly .xaxis {{
        font-family: 'Montserrat', 'Nunito', sans-serif !important;
        color: {COLORS["dark_text"]} !important;
    }}
</style>
<div class="scrollable-container">
    {plotly_html}
</div>
"""

# Display the scrollable chart in Streamlit
st.components.v1.html(scrollable_html, height=420)

# Add a divider
st.markdown("---")

#####

# SECTION: Call duration trend - simplified for mobile
st.markdown(f"""
<div class='section-header' style='background-color: {COLORS["yellow"]}; color: {COLORS["dark_text"]};'>
Call Duration Trend
</div>
""", unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    # Add a dropdown for time interval (day, week, month)
    time_interval = st.selectbox(
        "Select Time Interval",
        ["Days", "Weeks", "Months"],
        label_visibility='hidden'
    )

with col2: 
    # Add a dropdown for metric (average or total minutes)
    metric = st.selectbox(
        "Select Metric",
        ["Total Minutes", "Average Minutes"],
        label_visibility='hidden'
    )

# Reference df_calendar filtered
start_dt_filter =  pd.to_datetime(start_month_year, format='%Y-%m')
end_dt_filter = pd.to_datetime(end_month_year, format='%Y-%m') + pd.DateOffset(months=1) # include the last month itself also
df_call_trend = df_calendar[(df_calendar[f'date'] >= start_dt_filter) 
                            & (df_calendar[f'date'] < end_dt_filter)]

# Convert the 'date' column to datetime (if not already)
df_call_trend['date'] = pd.to_datetime(df_call_trend['date'])

# Select the appropriate column based on the timezone
mins_col = f"Total_Mins_{tz_suffix}"

# Filter out rows with NaN values in the selected column
trend_data = df_call_trend[['date', mins_col]].dropna()

# Group by the selected time interval
if time_interval == "Days":
    trend_data["Interval"] = trend_data["date"]  # Use the date directly
elif time_interval == "Weeks":
    # Calculate the start of the week (Sunday)
    trend_data["Interval"] = trend_data["date"] - pd.to_timedelta(trend_data["date"].dt.dayofweek + 1, unit='d')
elif time_interval == "Months":
    trend_data["Interval"] = trend_data["date"].dt.to_period('M').dt.start_time  # Start of the month

# Calculate the selected metric
if metric == "Average Minutes":
    trend_data = trend_data.groupby("Interval")[mins_col].mean().reset_index()
    y_axis_label = "Avg Minutes"
else:  # Total Minutes
    trend_data = trend_data.groupby("Interval")[mins_col].sum().reset_index()
    y_axis_label = "Total Minutes"

# Sort the data by interval for proper plotting
trend_data = trend_data.sort_values("Interval")

# Format the x-axis labels
if time_interval == "Weeks":
    trend_data["Interval_Label"] = trend_data["Interval"].dt.strftime("%Y-%m-%d")  # Format as "YYYY-MM-DD"
elif time_interval == "Months":
    trend_data["Interval_Label"] = trend_data["Interval"].dt.strftime("%b %Y")  # Format as "Jan 2024"
else:
    trend_data["Interval_Label"] = trend_data["Interval"].dt.strftime("%Y-%m-%d")  # Format as "YYYY-MM-DD"

# Create the line chart
fig_duration = px.line(
    trend_data, 
    x="Interval_Label",
    y=mins_col,
    labels={"Interval_Label": time_interval, mins_col: y_axis_label},
    markers=True,
)

# Customize the line chart
fig_duration.update_traces(
    line_color=COLORS["pink"],
    marker=dict(color=COLORS["pink"], size=8),  # Adjust marker size for better visibility
    hovertemplate=(
        f"{time_interval}: %{{x}}<br>"
        f"{y_axis_label}: %{{y:,.1f}}<extra></extra>"
    )
)

fig_duration.update_layout(
    height=500,
    width=1800,
    margin=dict(l=50, r=50, t=50, b=50),
    paper_bgcolor=COLORS["white"],
    plot_bgcolor=COLORS["white"],
    font=dict(color=COLORS["dark_text"], size=12),
    yaxis=dict(
        title=y_axis_label,
        title_font=dict(size=12, color=COLORS["dark_text"]),
        tickfont=dict(size=10, color=COLORS["dark_text"]),
        showgrid=False,
    ),
    xaxis=dict(
        title=time_interval,
        title_font=dict(size=12, color=COLORS["dark_text"]),
        tickfont=dict(size=10, color=COLORS["dark_text"]),
        showgrid=False,
        showline=False
    ),
    dragmode=False,  # This disables zoom on drag
    hovermode='closest'
)

# Display the line chart
# st.plotly_chart(fig_duration, use_container_width=True)

# Convert the Plotly figure to HTML
plotly_html = fig_duration.to_html(full_html=False)

# Create a scrollable HTML container with custom CSS
scrollable_html = f"""
<style>
    @import url("https://fonts.googleapis.com/css2?family=Montserrat:ital,wght@0,100..900;1,100..900&family=Nunito:ital,wght@0,200..1000;1,200..1000&display=swap");
    .scrollable-container {{
        display: flex;
        height: 100%;
        overflow-x: auto;
        font-family: 'Montserrat', 'Nunito', sans-serif;
        color: {COLORS["dark_text"]};
        background-color: {COLORS["white"]};  /* Ensure the background is white */
    }}
    .scrollable-container .plotly .hovertext {{
        font-family: 'Montserrat', 'Nunito', sans-serif !important;
        color: {COLORS["dark_text"]} !important;
    }}
    .scrollable-container .plotly .xaxis {{
        font-family: 'Montserrat', 'Nunito', sans-serif !important;
        color: {COLORS["dark_text"]} !important;
    }}
</style>
<div class="scrollable-container">
    {plotly_html}
</div>
"""

# Display the scrollable chart in Streamlit
st.components.v1.html(scrollable_html, height=520)

# Add a divider
st.markdown("---")

#####

# SECTION: Call Distribution
st.markdown(f"""
<div class='section-header' style='background-color: {COLORS["yellow"]}; color: {COLORS["dark_text"]};'>
Call Duration Distribution
</div>
""", unsafe_allow_html=True)

col1, _, _= st.columns(3)

with col1:
    # Create a slider to adjust bin size
    bin_size = st.slider('Select Bin Size', min_value=5, max_value=50, value=30, step=5)

# Create a histogram of call durations
fig_distribution = px.histogram(
    filtered_df,
    x="Call_Length_Minutes",
    nbins=bin_size,
    labels={"Call_Length_Minutes": "Call Duration (Minutes)"},
    color_discrete_sequence=[COLORS["pink"]],
)

# Customize layout for better readability
fig_distribution.update_layout(
    height=500,
    width=550,
    margin=dict(l=50, r=50, t=50, b=50),
    paper_bgcolor=COLORS["white"],
    plot_bgcolor=COLORS["white"],
    font=dict(color=COLORS["dark_text"], size=12),
    xaxis=dict(
        title_font=dict(size=14, color=COLORS["dark_text"]),
        tickfont=dict(size=12, color=COLORS["dark_text"]),
        showgrid=False,
    ),
    yaxis=dict(
        title = "No. of Calls",
        title_font=dict(size=14, color=COLORS["dark_text"]),
        tickfont=dict(size=12, color=COLORS["dark_text"]),
        showgrid=False,
    ),
    dragmode=False,  # This disables zoom on drag
    hovermode='closest'
)

# st.plotly_chart(fig_distribution, use_container_width=True)

# Convert the Plotly figure to HTML
plotly_html = fig_distribution.to_html(full_html=False)

# Create a scrollable HTML container with custom CSS
scrollable_html = f"""
<style>
    @import url("https://fonts.googleapis.com/css2?family=Montserrat:ital,wght@0,100..900;1,100..900&family=Nunito:ital,wght@0,200..1000;1,200..1000&display=swap");
    .scrollable-container {{
        display: flex;
        justify-content: center;
        height: 100%;             /* Ensure the container takes full height */
        width: 100%;
        overflow-x: auto;
        font-family: 'Montserrat', 'Nunito', sans-serif;
        color: {COLORS["dark_text"]};
        background-color: {COLORS["pink"]};  /* Fill the container with a specific color */
        padding-left: 20px;  /* Add left padding */
        padding-right: 20px;  /* Add right padding */
    }}
    .scrollable-container .plotly .hovertext {{
        font-family: 'Montserrat', 'Nunito', sans-serif !important;
        color: {COLORS["dark_text"]} !important;
    }}
    .scrollable-container .plotly .xaxis {{
        font-family: 'Montserrat', 'Nunito', sans-serif !important;
        color: {COLORS["dark_text"]} !important;
    }}
</style>
<div class="scrollable-container">
    {plotly_html}
</div>
"""

# Display the scrollable chart in Streamlit
st.components.v1.html(scrollable_html, height=520)

# Add a divider
st.markdown("---")

#####

# Footer
st.markdown(f"<p style='text-align: center; color: {COLORS['dark_text']}; font-size: 0.8rem;'>{SITE_NAME} by Imran</p>", unsafe_allow_html=True)