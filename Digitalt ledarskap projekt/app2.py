import os
from datetime import datetime
import streamlit as st
import pandas as pd
import requests
import plotly.express as px

# ----------------------------------------------------
# Page Configuration
# ----------------------------------------------------
st.set_page_config(
    page_title="Air-aware | Environmental & Weather Monitor",
    page_icon="🌤️",
    layout="wide",
    initial_sidebar_state="expanded",
)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# ----------------------------------------------------
# City Coordinates (Västra Götaland & Swedish Cities)
# ----------------------------------------------------
LOCATIONS = {
    # Västra Götaland
    "Göteborg": (57.7089, 11.9746),
    "Alingsås": (57.9303, 12.5335),
    "Bengtsfors": (58.9974, 12.2324),
    "Borås": (57.7210, 12.9401),
    "Falköping": (58.1735, 13.5507),
    "Hjo": (58.3019, 14.2874),
    "Kungälv": (57.8700, 11.9675),
    "Lidköping": (58.5052, 13.1577),
    "Lilla Edet": (58.1333, 12.1333),
    "Lysekil": (58.2740, 11.4350),
    "Mariestad": (58.7097, 13.8237),
    "Mölndal": (57.6554, 12.0138),
    "Skara": (58.3866, 13.4384),
    "Skövde": (58.3912, 13.8451),
    "Strömstad": (58.9394, 11.1712),
    "Tanumshede": (58.7236, 11.3250),
    "Tibro": (58.4245, 14.1612),
    "Tidaholm": (58.1804, 13.9583),
    "Trollhättan": (58.2837, 12.2886),
    "Ulricehamn": (57.7916, 13.4142),
    "Uddevalla": (58.3498, 11.9424),
    "Vänersborg": (58.3807, 12.3234),
    "Åmål": (58.9898, 12.6390),
    # Other Major Regions
    "Stockholm": (59.3293, 18.0686),
    "Malmö": (55.6050, 13.0038),
    "Uppsala": (59.8586, 17.6389),
    "Linköping": (58.4108, 15.6214),
    "Örebro": (59.2753, 15.2134),
    "Västerås": (59.6099, 16.5448),
    "Helsingborg": (56.0465, 12.6945),
    "Jönköping": (57.7826, 14.1618),
    "Umeå": (63.8258, 20.2630),
    "Gävle": (60.6749, 17.1413),
    "Halmstad": (56.6745, 12.8578),
    "Karlstad": (59.3793, 13.5036),
    "Sundsvall": (62.3908, 17.3069),
    "Luleå": (65.5848, 22.1547),
    "Visby": (57.6348, 18.2948),
}

# ----------------------------------------------------
# SMHI Live Weather API
# ----------------------------------------------------
@st.cache_data(ttl=600)
def get_live_weather(latitude: float, longitude: float):
    url = (
        "https://opendata-download-metfcst.smhi.se/api/"
        "category/snow1g/version/1/geotype/point/"
        f"lon/{longitude}/lat/{latitude}/data.json"
    )
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    data = response.json()

    forecast = data["timeSeries"][0]
    weather = forecast["data"]

    return {
        "time": forecast["time"],
        "temperature": weather.get("air_temperature"),
        "wind_speed": weather.get("wind_speed"),
        "humidity": weather.get("relative_humidity"),
        "precipitation": weather.get("precipitation_amount_mean"),
        "cloudiness": weather.get("cloud_area_fraction"),
        "weather_symbol": weather.get("symbol_code"),
    }

# ----------------------------------------------------
# Data Loading & Caching (Air Quality & Pollen)
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
# Top Navigation Bar: City / Region, Station & View Mode
# ----------------------------------------------------
st.title("🌤️ Air-aware: Weather, Air Quality & Pollen Monitor")

STATION_MAP = {
    "Femman": [c for c in df_air.columns if c.startswith("Femman_")],
    "Haga (Norra & Södra)": [c for c in df_air.columns if c.startswith("Haga")],
    "Lejonet": [c for c in df_air.columns if c.startswith("Lejonet_")],
    "Mobil 1": [c for c in df_air.columns if c.startswith("Mobil1_")],
    "Mobil 2": [c for c in df_air.columns if c.startswith("Mobil2_")],
    "Mobil 3": [c for c in df_air.columns if c.startswith("Mobil3_")],
    "All Stations": [c for c in df_air.columns if c not in ["Date", "Time", "Time_Clean", "DateTime"]],
}

# Combine location list with any unique regions from pollen file
available_cities = sorted(list(LOCATIONS.keys()))
default_city_idx = available_cities.index("Göteborg") if "Göteborg" in available_cities else 0

top_col1, top_col2, top_col3 = st.columns([1.5, 2, 1.5])

with top_col1:
    selected_city = st.selectbox("📍 Select City / Region", options=available_cities, index=default_city_idx)

with top_col2:
    selected_station = st.selectbox("🏢 Select Air Quality Station", options=list(STATION_MAP.keys()), index=0)

with top_col3:
    view_mode = st.radio("⏱️ Aggregation Mode", options=["Daily View", "Weekly Trend"], horizontal=True)

st.markdown("---")

# ----------------------------------------------------
# Live SMHI Weather Section
# ----------------------------------------------------
lat, lon = LOCATIONS[selected_city]

with st.container():
    st.subheader(f"🌤️ Live Weather Conditions — {selected_city}")
    try:
        live_weather = get_live_weather(lat, lon)
        forecast_dt = datetime.fromisoformat(live_weather["time"].replace("Z", "+00:00"))
        st.caption(f"SMHI Forecast valid: {forecast_dt.strftime('%Y-%m-%d %H:%M UTC')} | Coords: {lat:.2f}°N, {lon:.2f}°E")

        w_col1, w_col2, w_col3, w_col4, w_col5 = st.columns(5)
        w_col1.metric("🌡️ Temperature", f"{live_weather['temperature']} °C")
        w_col2.metric("💨 Wind Speed", f"{live_weather['wind_speed']} m/s")
        w_col3.metric("💧 Humidity", f"{live_weather['humidity']} %")
        w_col4.metric("🌧️ Precip.", f"{live_weather['precipitation']} mm")
        w_col5.metric("☁️ Cloudiness", f"{live_weather['cloudiness']} %")
    except Exception as e:
        st.warning(f"Could not retrieve live SMHI weather for {selected_city}: {e}")

st.markdown("---")

# Filter pollen matching the selected city or general fallback
pollen_region_df = (
    df_pollen[df_pollen["Region"].str.lower() == selected_city.lower()].copy()
    if not df_pollen.empty
    else pd.DataFrame()
)
if pollen_region_df.empty and not df_pollen.empty:
    # Default to available pollen data if exact Swedish town isn't a direct trap region
    pollen_region_df = df_pollen.copy()

# ----------------------------------------------------
# Sidebar: Metric Selection & Controls
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

    # Station KPI metrics
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
    st.subheader(f"🌾 Pollen Index — {selected_city} ({selected_date})")
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
        st.info(f"No pollen observations recorded for {selected_city} on {selected_date}.")

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
            title=f"Weekly Average Pollen Levels — {selected_city}",
            labels={"DateTime": "Week Ending", "Level_Value": "Average Pollen Level (0–6)", "Pollen": "Species"},
        )
        fig_weekly_pollen.update_layout(hovermode="x unified", legend=dict(orientation="h", y=-0.25))
        st.plotly_chart(fig_weekly_pollen, use_container_width=True)

# ----------------------------------------------------
# Raw Data Drawer
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