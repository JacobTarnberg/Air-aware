import os
from datetime import date, datetime, timedelta

import pandas as pd
import plotly.express as px
import requests
import streamlit as st

from interface import show_air_aware_dashboard
from recommendations import calculate_viability, get_recommendation, pollen_level_to_status
from sample_data_jonnamada import EMPTY_POLLEN_BENCHMARK, REGIONS_AND_CITIES

st.set_page_config(page_title="Air Aware | Outdoor Viability & Pollen Monitor", page_icon="🏃‍♂️", layout="wide")
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
AIR_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"


@st.cache_data
def load_historical_pollen():
    candidates = [os.path.join(SCRIPT_DIR, name) for name in (
        "goteborg_historical_pollen_3.csv", "goteborg_historical_pollen_2.csv", "goteborg_historical_pollen.csv"
    )]
    path = next((item for item in candidates if os.path.exists(item)), None)
    if path is None:
        return pd.DataFrame(), "None"
    frame = pd.read_csv(path)
    frame.columns = frame.columns.str.strip()
    if "Date" in frame.columns:
        frame["Date_Clean"] = pd.to_datetime(frame["Date"], errors="coerce").dt.date
    if "Level_Value" in frame.columns:
        frame["Level_Value"] = pd.to_numeric(frame["Level_Value"], errors="coerce")
    return frame, os.path.basename(path)


@st.cache_data(ttl=900, show_spinner=False)
def fetch_city_pollution(latitude, longitude):
    params = {"latitude": latitude, "longitude": longitude, "current": "european_aqi,pm10,pm2_5,nitrogen_dioxide,ozone", "hourly": "european_aqi,pm2_5,pm10,nitrogen_dioxide", "timezone": "Europe/Stockholm", "forecast_days": 2}
    try:
        response = requests.get(AIR_URL, params=params, timeout=10)
        response.raise_for_status()
        payload = response.json()
        return payload.get("current", {}), pd.DataFrame(payload.get("hourly", {})), False
    except (requests.RequestException, ValueError):
        current = {"european_aqi": 18, "pm2_5": 4.5, "pm10": 11.2, "nitrogen_dioxide": 9.4}
        hourly = pd.DataFrame({"time": [datetime.now().isoformat(timespec="hours")], **{key: [value] for key, value in current.items()}})
        return current, hourly, True


@st.cache_data(ttl=600, show_spinner=False)
def fetch_city_weather(latitude, longitude):
    params = {"latitude": latitude, "longitude": longitude, "current": "temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m", "timezone": "Europe/Stockholm"}
    try:
        response = requests.get(WEATHER_URL, params=params, timeout=10)
        response.raise_for_status()
        current = response.json().get("current", {})
        return {"source": "Open-Meteo", "temperature": current.get("temperature_2m"), "wind_speed": current.get("wind_speed_10m"), "humidity": current.get("relative_humidity_2m"), "precipitation": current.get("precipitation"), "fallback": False}
    except (requests.RequestException, ValueError):
        return {"source": "Estimated fallback", "temperature": 16.0, "wind_speed": 3.0, "humidity": 60.0, "precipitation": 0.0, "fallback": True}


def previous_year_safe(target):
    try:
        return target.replace(year=target.year - 1)
    except ValueError:
        return target.replace(year=target.year - 1, day=28)


def select_pollen_benchmark(frame, target):
    if frame.empty or not {"Date_Clean", "Level_Value"}.issubset(frame.columns):
        return pd.DataFrame(), None, False
    exact = frame[frame["Date_Clean"] == target]
    if not exact.empty:
        return exact.copy(), target, False
    valid = frame.dropna(subset=["Date_Clean"]).copy()
    if valid.empty:
        return pd.DataFrame(), None, False
    valid["day_difference"] = (pd.to_datetime(valid["Date_Clean"]) - pd.Timestamp(target)).abs()
    nearest = valid.loc[valid["day_difference"].idxmin()]
    if nearest["day_difference"] <= timedelta(days=14):
        nearest_date = nearest["Date_Clean"]
        return valid[valid["Date_Clean"] == nearest_date].copy(), nearest_date, True
    return pd.DataFrame(), None, False


df_pollen, pollen_filename = load_historical_pollen()
title_column, refresh_column = st.columns([5, 1])
with title_column:
    st.title("🏃‍♂️ Air Aware: Outdoor Viability & Pollen Monitor")
    st.caption("Live air quality and weather, with a historical Gothenburg pollen benchmark.")
with refresh_column:
    if st.button("🔄 Refresh", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

region_column, city_column, date_column = st.columns(3)
regions = list(REGIONS_AND_CITIES)
with region_column:
    selected_region = st.selectbox("1. Select region", regions, index=regions.index("Västra Götaland"))
cities = list(REGIONS_AND_CITIES[selected_region])
with city_column:
    selected_city = st.selectbox("2. Select city", cities, index=cities.index("Göteborg") if "Göteborg" in cities else 0)
with date_column:
    target_date = st.date_input("3. Planned activity date", value=date.today())

latitude, longitude = REGIONS_AND_CITIES[selected_region][selected_city]
air, hourly, air_fallback = fetch_city_pollution(latitude, longitude)
weather = fetch_city_weather(latitude, longitude)
comparison_date = previous_year_safe(target_date)
pollen_day, used_date, approximate = select_pollen_benchmark(df_pollen, comparison_date)
pollen = EMPTY_POLLEN_BENCHMARK.copy()
if not pollen_day.empty:
    level = pollen_day["Level_Value"].max()
    level = int(level) if pd.notna(level) else 0
    dominant = pollen_day.loc[pollen_day["Level_Value"] == level, "Pollen"].dropna().astype(str).tolist() if "Pollen" in pollen_day.columns else []
    pollen.update({"level": level, "status": pollen_level_to_status(level), "dominant": ", ".join(dominant) or "None", "date": str(used_date), "source": pollen_filename, "available": True})

aqi, pm25, pm10, no2 = air.get("european_aqi"), air.get("pm2_5"), air.get("pm10"), air.get("nitrogen_dioxide")
temperature, wind, rain = weather.get("temperature"), weather.get("wind_speed"), weather.get("precipitation")
result = calculate_viability(aqi, temperature, wind, rain, pollen)
recommendation = get_recommendation(result)
if air_fallback:
    st.warning("Live air-quality data is unavailable, so fallback values are shown.")
if weather.get("fallback"):
    st.warning("Live weather data is unavailable, so fallback values are shown.")
if selected_city != "Göteborg":
    st.info("The pollen benchmark uses Gothenburg historical observations and is not local to the selected city.")

show_air_aware_dashboard(city=selected_city, region=selected_region, result=result, recommendation=recommendation, aqi=aqi, pm25=pm25, pm10=pm10, no2=no2, temperature=temperature, wind_speed=wind, precipitation=rain, weather_source=weather.get("source", "Unknown"), pollen_benchmark=pollen, pollen_approximate=approximate)

st.divider()
st.subheader("Historical pollen species")
if not pollen_day.empty:
    figure = px.bar(pollen_day.sort_values("Level_Value"), x="Level_Value", y="Pollen", orientation="h", color="Level_Value", range_color=[0, 6], text="Level_Value", title=f"Gothenburg observations on {used_date}", labels={"Level_Value": "Severity (0–6)", "Pollen": "Species"})
    figure.update_layout(height=320, coloraxis_showscale=False)
    st.plotly_chart(figure, use_container_width=True)
else:
    st.warning(f"No pollen observation was found within 14 days of {comparison_date}.")

st.divider()
left, right = st.columns(2)
with left:
    values = pd.DataFrame({"Pollutant": ["PM2.5", "PM10", "NO₂", "European AQI"], "Value": [pm25, pm10, no2, aqi]})
    figure = px.bar(values, x="Pollutant", y="Value", color="Pollutant", text_auto=".1f", title=f"Live pollution — {selected_city}")
    figure.update_layout(showlegend=False, height=330)
    st.plotly_chart(figure, use_container_width=True)
with right:
    choices = [name for name in ("european_aqi", "pm2_5", "pm10", "nitrogen_dioxide") if name in hourly.columns]
    if not hourly.empty and "time" in hourly.columns and choices:
        metric = st.radio("Forecast parameter", choices, format_func=lambda value: value.upper().replace("_", " "), horizontal=True)
        figure = px.line(hourly, x="time", y=metric, title=f"Next 48 hours: {metric.upper().replace('_', ' ')}")
        figure.update_layout(height=300, hovermode="x unified")
        st.plotly_chart(figure, use_container_width=True)
    else:
        st.info("The 48-hour forecast is unavailable.")

st.caption("Historical pollen observations are a seasonal benchmark, not a live forecast. Air Aware does not replace medical advice.")
