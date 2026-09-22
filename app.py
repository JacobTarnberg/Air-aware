import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ----------------------------------------------------
# Page Configuration
# ----------------------------------------------------
st.set_page_config(
    page_title="Environmental Dashboard: Air Quality & Pollen",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ----------------------------------------------------
# Data Loading & Caching
# ----------------------------------------------------
@st.cache_data
def load_datasets():
    # 1. Load Air Quality Data
    air_file = "Airquality.csv"
    if not os.path.exists(air_file):
        st.error(f"⚠️ Could not find '{air_file}'. Please place it in the application directory.")
        st.stop()

    df_air = pd.read_csv(air_file, low_memory=False)
    df_air.columns = df_air.columns.str.strip()
    df_air["Date"] = pd.to_datetime(df_air["Date"], errors="coerce").dt.date
    df_air["Time_Clean"] = df_air["Time"].astype(str).str.split("+").str[0]
    df_air["DateTime"] = pd.to_datetime(df_air["Date"].astype(str) + " " + df_air["Time_Clean"], errors="coerce")

    # Coerce sensor metrics to float
    air_metric_cols = [c for c in df_air.columns if c not in ["Date", "Time", "Time_Clean", "DateTime"]]
    for col in air_metric_cols:
        df_air[col] = pd.to_numeric(df_air[col], errors="coerce")

    # 2. Load Pollen Data
    pollen_file = "goteborg_historical_pollen_2.csv"
    if not os.path.exists(pollen_file):
        pollen_file = "goteborg_historical_pollen.csv"

    df_pollen = pd.DataFrame()
    if os.path.exists(pollen_file):
        df_pollen = pd.read_csv(pollen_file)
        df_pollen.columns = df_pollen.columns.str.strip()
        if "Date" in df_pollen.columns:
            df_pollen["Date"] = pd.to_datetime(df_pollen["Date"], errors="coerce").dt.date
        if "Level_Value" in df_pollen.columns:
            df_pollen["Level_Value"] = pd.to_numeric(df_pollen["Level_Value"], errors="coerce")
        if "Region" not in df_pollen.columns or df_pollen["Region"].isna().all():
            df_pollen["Region"] = "Göteborg"

    return df_air, df_pollen

df_air, df_pollen = load_datasets()

# ----------------------------------------------------
# Top Navigation Bar: Region, Station & Aggregation
# ----------------------------------------------------
st.title("🌱 Gothenburg Environmental Monitor: Air Quality & Pollen")

# Define stations available in the Air Quality data
STATION_MAP = {
    "Femman": [c for c in df_air.columns if c.startswith("Femman_")],
    "Haga (Norra & Södra)": [c for c in df_air.columns if c.startswith("Haga")],
    "Lejonet": [c for c in df_air.columns if c.startswith("Lejonet_")],
    "Mobil 1": [c for c in df_air.columns if c.startswith("Mobil1_")],
    "Mobil 2": [c for c in df_air.columns if c.startswith("Mobil2_")],
    "Mobil 3": [c for c in df_air.columns if c.startswith("Mobil3_")],
    "All Stations": [c for c in df_air.columns if c not in ["Date", "Time", "Time_Clean", "DateTime"]],
}

# Distinct regions from pollen or default
available_regions = sorted(df_pollen["Region"].dropna().unique().tolist()) if not df_pollen.empty else ["Göteborg"]
if not available_regions:
    available_regions = ["Göteborg"]

top_col1, top_col2, top_col3 = st.columns([1.5, 2, 1.5])

with top_col1:
    selected_region = st.selectbox("📍 Select Region", options=available_regions, index=0)

with top_col2:
    selected_station = st.selectbox("🏢 Select Air Quality Station", options=list(STATION_MAP.keys()), index=0)

with top_col3:
    view_mode = st.radio("⏱️ Time Aggregation", options=["Daily View", "Weekly Trend"], horizontal=True)

st.markdown("---")

# Filter pollen by region
pollen_region_df = df_pollen[df_pollen["Region"] == selected_region].copy() if not df_pollen.empty else pd.DataFrame()

# ----------------------------------------------------
# Sidebar Date Filters & Metric Toggles
# ----------------------------------------------------
st.sidebar.header("⚙️ View Settings")

station_metrics = STATION_MAP[selected_station]
selected_air_metrics = st.sidebar.multiselect(
    "Air Quality Metrics",
    options=station_metrics,
    default=station_metrics[: min(4, len(station_metrics))],
)

# Pollen types selection
available_pollens = sorted(pollen_region_df["Pollen"].dropna().unique().tolist()) if not pollen_region_df.empty else []
selected_pollens = st.sidebar.multiselect(
    "Pollen Species",
    options=available_pollens,
    default=available_pollens[: min(5, len(available_pollens))],
)

# ----------------------------------------------------
# View Mode 1: Daily View (Detailed Hourly Curves)
# ----------------------------------------------------
if view_mode == "Daily View":
    unique_dates = sorted(df_air["Date"].dropna().unique())
    selected_date = st.sidebar.date_input(
        "Choose Date",
        value=unique_dates[0],
        min_value=unique_dates[0],
        max_value=unique_dates[-1],
    )

    day_air = df_air[df_air["Date"] == selected_date].sort_values("DateTime")
    day_pollen = pollen_region_df[pollen_region_df["Date"] == selected_date] if not pollen_region_df.empty else pd.DataFrame()

    # KPI Metric Cards
    k1, k2, k3, k4 = st.columns(4)
    pm25_candidates = [c for c in station_metrics if "PM25" in c]
    pm10_candidates = [c for c in station_metrics if "PM10" in c]
    no2_candidates = [c for c in station_metrics if "NO2" in c]

    k1.metric("Selected Station", selected_station)
    k2.metric(
        "Avg PM2.5",
        f"{day_air[pm25_candidates[0]].mean():.1f} µg/m³" if pm25_candidates and day_air[pm25_candidates[0]].notna().any() else "N/A",
    )
    k3.metric(
        "Avg PM10",
        f"{day_air[pm10_candidates[0]].mean():.1f} µg/m³" if pm10_candidates and day_air[pm10_candidates[0]].notna().any() else "N/A",
    )
    k4.metric(
        "Avg NO₂",
        f"{day_air[no2_candidates[0]].mean():.1f} µg/m³" if no2_candidates and day_air[no2_candidates[0]].notna().any() else "N/A",
    )

    st.subheader(f"Hourly Observations on {selected_date}")

    # Plot Air Quality for the Day
    if selected_air_metrics:
        fig_air = px.line(
            day_air,
            x="Time_Clean",
            y=selected_air_metrics,
            markers=True,
            title=f"{selected_station} Hourly Sensor Data",
            labels={"Time_Clean": "Time of Day", "value": "Measured Concentration / Value", "variable": "Sensor"},
        )
        fig_air.update_layout(hovermode="x unified", legend=dict(orientation="h", y=-0.25))
        st.plotly_chart(fig_air, use_container_width=True)
    else:
        st.info("Select at least one air quality metric in the sidebar to display the hourly graph.")

    # Plot Pollen for the Day
    st.subheader(f"🌾 Pollen Index — {selected_region} ({selected_date})")
    if not day_pollen.empty and selected_pollens:
        day_pollen_filtered = day_pollen[day_pollen["Pollen"].isin(selected_pollens)]
        fig_pollen = px.bar(
            day_pollen_filtered,
            x="Pollen",
            y="Level_Value",
            color="Pollen",
            text="Level_Description",
            title=f"Recorded Pollen Risk Levels on {selected_date}",
            labels={"Level_Value": "Level (0-6)", "Pollen": "Species"},
        )
        fig_pollen.update_traces(textposition="outside")
        fig_pollen.update_layout(yaxis=dict(range=[0, 6], dtick=1))
        st.plotly_chart(fig_pollen, use_container_width=True)
    else:
        st.info(f"No pollen observations recorded for {selected_region} on {selected_date} (Pollen traps typically run March–September).")

# ----------------------------------------------------
# View Mode 2: Weekly Trend (Aggregated Comparison)
# ----------------------------------------------------
else:
    st.sidebar.subheader("Date Range for Weekly View")
    min_date = df_air["Date"].min()
    max_date = df_air["Date"].max()
    
    date_range = st.sidebar.date_input(
        "Date Range",
        value=(min_date, min_date + pd.Timedelta(days=90)),
        min_value=min_date,
        max_value=max_date,
    )

    if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
        start_d, end_d = date_range
    else:
        start_d, end_d = min_date, max_date

    # Filter Air Quality by Date Range and resample weekly
    mask_air = (df_air["Date"] >= start_d) & (df_air["Date"] <= end_d)
    weekly_air = df_air[mask_air].copy()
    weekly_air = weekly_air.set_index("DateTime")[station_metrics].resample("W-MON").mean().reset_index()

    # Filter Pollen by Date Range and resample weekly
    if not pollen_region_df.empty:
        mask_pollen = (pollen_region_df["Date"] >= start_d) & (pollen_region_df["Date"] <= end_d)
        pollen_filtered = pollen_region_df[mask_pollen & pollen_region_df["Pollen"].isin(selected_pollens)].copy()
        pollen_filtered["DateTime"] = pd.to_datetime(pollen_filtered["Date"])
        weekly_pollen = (
            pollen_filtered.groupby(["DateTime", "Pollen"])["Level_Value"]
            .mean()
            .reset_index()
            .set_index("DateTime")
            .groupby("Pollen")
            .resample("W-MON")["Level_Value"]
            .mean()
            .reset_index()
        )
    else:
        weekly_pollen = pd.DataFrame()

    st.subheader(f"Weekly Trends ({start_d} to {end_d})")

    # Air Quality Weekly Chart
    if selected_air_metrics:
        fig_weekly_air = px.line(
            weekly_air,
            x="DateTime",
            y=selected_air_metrics,
            markers=True,
            title=f"Weekly Average Concentrations — {selected_station}",
            labels={"DateTime": "Week Ending", "value": "Mean Concentration", "variable": "Sensor"},
        )
        fig_weekly_air.update_layout(hovermode="x unified", legend=dict(orientation="h", y=-0.25))
        st.plotly_chart(fig_weekly_air, use_container_width=True)

    # Pollen Weekly Chart
    if not weekly_pollen.empty and selected_pollens:
        fig_weekly_pollen = px.line(
            weekly_pollen,
            x="DateTime",
            y="Level_Value",
            color="Pollen",
            markers=True,
            title=f"Weekly Average Pollen Levels — {selected_region}",
            labels={"DateTime": "Week Ending", "Level_Value": "Average Pollen Level (0–6)", "Pollen": "Species"},
        )
        fig_weekly_pollen.update_layout(hovermode="x unified", legend=dict(orientation="h", y=-0.25))
        st.plotly_chart(fig_weekly_pollen, use_container_width=True)

# ----------------------------------------------------
# Data Export Drawer
# ----------------------------------------------------
with st.expander("📥 Inspect & Download Raw Data"):
    tab1, tab2 = st.tabs(["Air Quality Data", "Pollen Data"])
    with tab1:
        st.dataframe(df_air.head(100), use_container_width=True)
    with tab2:
        if not df_pollen.empty:
            st.dataframe(pollen_region_df.head(100), use_container_width=True)
        else:
            st.write("No pollen data available to preview.")