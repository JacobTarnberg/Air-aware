import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ----------------------------------------------------
# Page Configuration
# ----------------------------------------------------
st.set_page_config(
    page_title="Gothenburg Air Quality & Pollen Monitor",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded",
)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# ----------------------------------------------------
# Data Loading & Caching
# ----------------------------------------------------
@st.cache_data
def load_datasets():
    # 1. Load Air Quality Data
    air_candidates = [
        os.path.join(SCRIPT_DIR, "Airquality_2.csv"),
        "Airquality_2.csv",
        os.path.join(SCRIPT_DIR, "Airquality.csv"),
        "Airquality.csv",
    ]
    air_file = next((p for p in air_candidates if os.path.exists(p)), None)

    if not air_file:
        st.error("⚠️ Neither `Airquality_2.csv` nor `Airquality.csv` was found.")
        st.stop()

    df_air = pd.read_csv(air_file, low_memory=False)
    df_air.columns = df_air.columns.str.strip()
    df_air["Date"] = pd.to_datetime(df_air["Date"], errors="coerce").dt.date
    df_air["Time_Clean"] = df_air["Time"].astype(str).str.split("+").str[0]
    df_air["DateTime"] = pd.to_datetime(
        df_air["Date"].astype(str) + " " + df_air["Time_Clean"], errors="coerce"
    )

    non_metrics = ["Date", "Time", "Time_Clean", "DateTime"]
    metric_cols = [c for c in df_air.columns if c not in non_metrics]
    for col in metric_cols:
        df_air[col] = pd.to_numeric(df_air[col], errors="coerce")

    # 2. Load Pollen Data
    pollen_candidates = [
        os.path.join(SCRIPT_DIR, "goteborg_historical_pollen_3.csv"),
        "goteborg_historical_pollen_3.csv",
        os.path.join(SCRIPT_DIR, "goteborg_historical_pollen_2.csv"),
        "goteborg_historical_pollen_2.csv",
        os.path.join(SCRIPT_DIR, "goteborg_historical_pollen.csv"),
        "goteborg_historical_pollen.csv",
    ]
    pollen_file = next((p for p in pollen_candidates if os.path.exists(p)), None)

    df_pollen = pd.DataFrame()
    if pollen_file:
        df_pollen = pd.read_csv(pollen_file)
        df_pollen.columns = df_pollen.columns.str.strip()
        if "Date" in df_pollen.columns:
            df_pollen["Date"] = pd.to_datetime(df_pollen["Date"], errors="coerce").dt.date
            df_pollen["DateTime"] = pd.to_datetime(df_pollen["Date"])
        if "Level_Value" in df_pollen.columns:
            df_pollen["Level_Value"] = pd.to_numeric(df_pollen["Level_Value"], errors="coerce")
        if "Region" not in df_pollen.columns or df_pollen["Region"].isna().all():
            df_pollen["Region"] = "Göteborg"

    return df_air, df_pollen, os.path.basename(air_file), (os.path.basename(pollen_file) if pollen_file else "None")


df_air, df_pollen, air_fname, pollen_fname = load_datasets()

# ----------------------------------------------------
# Top Navigation Bar: Region, Station & View Mode
# ----------------------------------------------------
st.title("🌱 Gothenburg Environmental Monitor: Air Quality & Pollen")
st.caption(f"Loaded datasets: `{air_fname}` & `{pollen_fname}`")

# Station groupings based on Airquality column prefixes
STATION_MAP = {
    "Femman": [c for c in df_air.columns if c.startswith("Femman_")],
    "Haga (Norra & Södra)": [c for c in df_air.columns if c.startswith("Haga")],
    "Lejonet": [c for c in df_air.columns if c.startswith("Lejonet_")],
    "Mobil 1": [c for c in df_air.columns if c.startswith("Mobil1_")],
    "Mobil 2": [c for c in df_air.columns if c.startswith("Mobil2_")],
    "Mobil 3": [c for c in df_air.columns if c.startswith("Mobil3_")],
    "All Stations": [c for c in df_air.columns if c not in ["Date", "Time", "Time_Clean", "DateTime"]],
}

available_regions = sorted(df_pollen["Region"].dropna().unique().tolist()) if not df_pollen.empty else ["Göteborg"]
if not available_regions:
    available_regions = ["Göteborg"]

col_reg, col_stat, col_mode = st.columns([1.5, 2, 1.5])

with col_reg:
    selected_region = st.selectbox("📍 Select Region", options=available_regions, index=0)

with col_stat:
    selected_station = st.selectbox("🏢 Select Air Quality Station", options=list(STATION_MAP.keys()), index=0)

with col_mode:
    view_mode = st.radio("⏱️ Aggregation Mode", options=["Daily View", "Weekly Trend"], horizontal=True)

st.markdown("---")

pollen_region_df = (
    df_pollen[df_pollen["Region"] == selected_region].copy() if not df_pollen.empty else pd.DataFrame()
)

# ----------------------------------------------------
# Sidebar: Metric Selection
# ----------------------------------------------------
st.sidebar.header("⚙️ Metric Toggles")

station_metrics = STATION_MAP[selected_station]
selected_air_metrics = st.sidebar.multiselect(
    "Air Quality Metrics",
    options=station_metrics,
    default=station_metrics[: min(4, len(station_metrics))],
)

available_pollens = sorted(pollen_region_df["Pollen"].dropna().unique().tolist()) if not pollen_region_df.empty else []
selected_pollens = st.sidebar.multiselect(
    "Pollen Species",
    options=available_pollens,
    default=available_pollens[: min(5, len(available_pollens))],
)

# ----------------------------------------------------
# View Mode 1: Daily View
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
    day_pollen = (
        pollen_region_df[pollen_region_df["Date"] == selected_date]
        if not pollen_region_df.empty
        else pd.DataFrame()
    )

    # Key Metrics Bar
    k1, k2, k3, k4 = st.columns(4)
    pm25_col = next((c for c in station_metrics if "PM25" in c), None)
    pm10_col = next((c for c in station_metrics if "PM10" in c), None)
    no2_col = next((c for c in station_metrics if "NO2" in c), None)

    k1.metric("Station", selected_station)
    k2.metric(
        "Avg PM2.5",
        f"{day_air[pm25_col].mean():.1f} µg/m³" if pm25_col and day_air[pm25_col].notna().any() else "N/A",
    )
    k3.metric(
        "Avg PM10",
        f"{day_air[pm10_col].mean():.1f} µg/m³" if pm10_col and day_air[pm10_col].notna().any() else "N/A",
    )
    k4.metric(
        "Avg NO₂",
        f"{day_air[no2_col].mean():.1f} µg/m³" if no2_col and day_air[no2_col].notna().any() else "N/A",
    )

    # Hourly Line Plot
    st.subheader(f"Hourly Sensor Observations — {selected_date}")
    if selected_air_metrics:
        fig_air = px.line(
            day_air,
            x="Time_Clean",
            y=selected_air_metrics,
            markers=True,
            title=f"{selected_station} Hourly Trends",
            labels={"Time_Clean": "Time of Day", "value": "Measured Value", "variable": "Sensor"},
        )
        fig_air.update_layout(hovermode="x unified", legend=dict(orientation="h", y=-0.25))
        st.plotly_chart(fig_air, use_container_width=True)
    else:
        st.info("Select at least one air quality metric in the sidebar.")

    # Daily Pollen Bar Plot
    st.subheader(f"🌾 Pollen Index — {selected_region} ({selected_date})")
    if not day_pollen.empty and selected_pollens:
        day_pollen_filtered = day_pollen[day_pollen["Pollen"].isin(selected_pollens)]
        fig_pollen = px.bar(
            day_pollen_filtered,
            x="Pollen",
            y="Level_Value",
            color="Pollen",
            text="Level_Description" if "Level_Description" in day_pollen_filtered.columns else None,
            title=f"Recorded Pollen Risk Levels on {selected_date}",
            labels={"Level_Value": "Level (0–6)", "Pollen": "Species"},
        )
        fig_pollen.update_traces(textposition="outside")
        fig_pollen.update_layout(yaxis=dict(range=[0, 6], dtick=1))
        st.plotly_chart(fig_pollen, use_container_width=True)
    else:
        st.info(f"No pollen observations recorded for {selected_region} on {selected_date}.")

# ----------------------------------------------------
# View Mode 2: Weekly Trend
# ----------------------------------------------------
else:
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

    mask_air = (df_air["Date"] >= start_d) & (df_air["Date"] <= end_d)
    air_slice = df_air[mask_air].copy()

    # Weekly Resampling for Air Quality
    if not air_slice.empty and selected_air_metrics:
        weekly_air = (
            air_slice.dropna(subset=["DateTime"])
            .resample("W-MON", on="DateTime")[selected_air_metrics]
            .mean()
            .reset_index()
        )
    else:
        weekly_air = pd.DataFrame()

    # Weekly Aggregation for Pollen
    if not pollen_region_df.empty and selected_pollens:
        mask_pollen = (pollen_region_df["Date"] >= start_d) & (pollen_region_df["Date"] <= end_d)
        pollen_slice = pollen_region_df[mask_pollen & pollen_region_df["Pollen"].isin(selected_pollens)].copy()

        if not pollen_slice.empty:
            weekly_pollen = (
                pollen_slice.groupby(["Pollen", pd.Grouper(key="DateTime", freq="W-MON")])["Level_Value"]
                .mean()
                .reset_index()
            )
        else:
            weekly_pollen = pd.DataFrame()
    else:
        weekly_pollen = pd.DataFrame()

    st.subheader(f"Weekly Trends ({start_d} to {end_d})")

    if not weekly_air.empty and selected_air_metrics:
        fig_weekly_air = px.line(
            weekly_air,
            x="DateTime",
            y=selected_air_metrics,
            markers=True,
            title=f"Weekly Average Sensor Concentrations — {selected_station}",
            labels={"DateTime": "Week Ending", "value": "Mean Concentration", "variable": "Sensor"},
        )
        fig_weekly_air.update_layout(hovermode="x unified", legend=dict(orientation="h", y=-0.25))
        st.plotly_chart(fig_weekly_air, use_container_width=True)

    if not weekly_pollen.empty:
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
# Data Inspection Drawer
# ----------------------------------------------------
with st.expander("📋 Inspect Raw Tables"):
    tab1, tab2 = st.tabs(["Air Quality Data", "Pollen Data"])
    with tab1:
        st.dataframe(df_air.head(100), use_container_width=True)
    with tab2:
        if not df_pollen.empty:
            st.dataframe(pollen_region_df.head(100), use_container_width=True)
        else:
            st.write("No pollen data available.")