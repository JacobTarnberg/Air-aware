import os
from datetime import date, datetime, timedelta
from math import asin, cos, radians, sin, sqrt

import pandas as pd
import plotly.express as px
import requests
import streamlit as st

from interface import (
    render_category_sections,
    render_location_map,
    render_overall_result,
    render_sidebar_preferences,
    show_result_dialog_if_requested,
    show_welcome_if_needed,
)
from recommendations import describe_overall_conditions
from sample_data_jonnamada import REGIONS_AND_CITIES

st.set_page_config(page_title="Air Aware", page_icon="🌿", layout="wide")
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
AIR_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"
POLLEN_URL = "https://api.pollenrapporten.se/v1"

@st.cache_data
def load_historical_pollen():
    names = ("goteborg_historical_pollen_3.csv", "goteborg_historical_pollen_2.csv", "goteborg_historical_pollen.csv")
    path = next((os.path.join(SCRIPT_DIR, name) for name in names if os.path.exists(os.path.join(SCRIPT_DIR, name))), None)
    if path is None: return pd.DataFrame(), "None"
    frame = pd.read_csv(path); frame.columns = frame.columns.str.strip()
    if "Date" in frame: frame["Date_Clean"] = pd.to_datetime(frame["Date"], errors="coerce").dt.date
    if "Level_Value" in frame: frame["Level_Value"] = pd.to_numeric(frame["Level_Value"], errors="coerce")
    return frame, os.path.basename(path)

@st.cache_data(ttl=900, show_spinner=False)
def fetch_city_pollution(latitude, longitude):
    current = ["european_aqi", "pm10", "pm2_5", "nitrogen_dioxide", "ozone", "sulphur_dioxide", "carbon_monoxide", "european_aqi_pm2_5", "european_aqi_pm10", "european_aqi_nitrogen_dioxide", "european_aqi_ozone", "european_aqi_sulphur_dioxide", "us_aqi_carbon_monoxide"]
    hourly = ["european_aqi", "pm2_5", "pm10", "nitrogen_dioxide"]
    try:
        response = requests.get(AIR_URL, params={"latitude": latitude, "longitude": longitude, "current": ",".join(current), "hourly": ",".join(hourly), "timezone": "Europe/Stockholm", "forecast_days": 2}, timeout=10)
        response.raise_for_status(); payload = response.json()
        return payload.get("current", {}), pd.DataFrame(payload.get("hourly", {})), False
    except (requests.RequestException, ValueError):
        fallback = {"european_aqi": 18, "pm2_5": 4.5, "pm10": 11.2, "nitrogen_dioxide": 9.4}
        return fallback, pd.DataFrame({"time": [datetime.now().isoformat(timespec="hours")], **{key: [value] for key, value in fallback.items()}}), True

@st.cache_data(ttl=600, show_spinner=False)
def fetch_city_weather(latitude, longitude):
    variables = "temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m,wind_direction_10m"
    try:
        response = requests.get(WEATHER_URL, params={"latitude": latitude, "longitude": longitude, "current": variables, "wind_speed_unit": "ms", "timezone": "Europe/Stockholm"}, timeout=10)
        response.raise_for_status(); current = response.json().get("current", {})
        return {"source": "Open-Meteo", "temperature": current.get("temperature_2m"), "wind_speed": current.get("wind_speed_10m"), "wind_direction": current.get("wind_direction_10m"), "humidity": current.get("relative_humidity_2m"), "precipitation": current.get("precipitation"), "fallback": False}
    except (requests.RequestException, ValueError):
        return {"source": "Estimated fallback", "temperature": 16.0, "wind_speed": 3.0, "wind_direction": None, "humidity": 60.0, "precipitation": 0.0, "fallback": True}

def _items(payload): return payload.get("items", []) if isinstance(payload, dict) and isinstance(payload.get("items", []), list) else []

def _distance(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(radians, map(float, (lat1, lon1, lat2, lon2)))
    value = sin((lat2-lat1)/2)**2 + cos(lat1)*cos(lat2)*sin((lon2-lon1)/2)**2
    return 2 * 6371 * asin(sqrt(value))

def _pollen_level(level):
    try: level = int(level)
    except (TypeError, ValueError): return None
    return "None detected" if level <= 0 else "Low" if level == 1 else "Moderate" if level == 2 else "High" if level == 3 else "Very high"

@st.cache_data(ttl=1800, show_spinner=False)
def fetch_live_pollen(latitude, longitude, planned_date):
    info = {"available": False, "source": "Pollenrapporten", "region": None, "latitude": None, "longitude": None, "distance_km": None, "forecast_date": None, "forecast_text": None, "reason": None}
    try:
        response = requests.get(f"{POLLEN_URL}/regions", params={"offset": 0, "limit": 100}, timeout=10); response.raise_for_status()
        regions = _items(response.json()); nearest = min(regions, key=lambda row: _distance(latitude, longitude, row["latitude"], row["longitude"])) if regions else None
        if not nearest: info["reason"] = "No pollen forecast region was found."; return [], info
        info.update({"region": nearest.get("name"), "latitude": nearest.get("latitude"), "longitude": nearest.get("longitude"), "distance_km": _distance(latitude, longitude, nearest["latitude"], nearest["longitude"])})
        response = requests.get(f"{POLLEN_URL}/pollen-types", params={"offset": 0, "limit": 100}, timeout=10); response.raise_for_status()
        names = {row.get("id"): row.get("name", "Unknown pollen") for row in _items(response.json())}
        response = requests.get(f"{POLLEN_URL}/forecasts", params={"region_id": nearest.get("id"), "current": "true", "offset": 0, "limit": 100}, timeout=10); response.raise_for_status()
        target, records = planned_date.isoformat(), []
        for forecast in _items(response.json()):
            for level in forecast.get("levelSeries", []) or []:
                day = str(level.get("time", ""))[:10]
                if day == target and _pollen_level(level.get("level")) is not None:
                    records.append({"name": names.get(level.get("pollenId"), "Unknown pollen"), "level": _pollen_level(level.get("level")), "numeric_level": level.get("level"), "date": day})
            if records: info.update({"available": True, "forecast_date": target, "forecast_text": forecast.get("text")}); break
        if not records: info["reason"] = "Pollenrapporten has no numerical pollen forecast for the selected date. This may happen outside the active pollen season."
        return records, info
    except (requests.RequestException, ValueError, KeyError) as error:
        info["reason"] = "The Pollenrapporten API could not be reached."; info["technical_error"] = str(error); return [], info

def previous_year_safe(target):
    try: return target.replace(year=target.year - 1)
    except ValueError: return target.replace(year=target.year - 1, day=28)

def select_pollen_benchmark(frame, target):
    if frame.empty or not {"Date_Clean", "Level_Value"}.issubset(frame.columns): return pd.DataFrame(), None, False
    exact = frame[frame["Date_Clean"] == target]
    if not exact.empty: return exact.copy(), target, False
    valid = frame.dropna(subset=["Date_Clean"]).copy()
    if valid.empty: return pd.DataFrame(), None, False
    valid["day_difference"] = (pd.to_datetime(valid["Date_Clean"]) - pd.Timestamp(target)).abs(); nearest = valid.loc[valid["day_difference"].idxmin()]
    if nearest["day_difference"] <= timedelta(days=14):
        nearest_date = nearest["Date_Clean"]; return valid[valid["Date_Clean"] == nearest_date].copy(), nearest_date, True
    return pd.DataFrame(), None, False

def pollen_number_to_level(value):
    try: value = float(value)
    except (TypeError, ValueError): return None
    return "None detected" if value <= 0 else "Low" if value <= 1 else "Moderate" if value <= 2 else "High" if value <= 4 else "Very high"

def convert_historical(frame):
    records = []
    for _, row in frame.iterrows():
        if pd.isna(row.get("Pollen")): continue
        level = row.get("Level_Description") if "Level_Description" in frame.columns and pd.notna(row.get("Level_Description")) else pollen_number_to_level(row.get("Level_Value"))
        records.append({"name": str(row.get("Pollen")), "level": str(level) if level is not None else None})
    return records

# Header and first-visit experience
show_welcome_if_needed()
preferences = render_sidebar_preferences()
title, refresh = st.columns([5, 1])
with title:
    st.title("🌿 Air Aware")
    st.caption("Understand the air before you go outside.")
with refresh:
    if st.button("🔄 Refresh", use_container_width=True): st.cache_data.clear(); st.rerun()

regions = list(REGIONS_AND_CITIES); default_region = regions.index("Västra Götaland") if "Västra Götaland" in regions else 0
region_col, city_col, date_col = st.columns(3)
with region_col: selected_region = st.selectbox("Region", regions, index=default_region)
cities = list(REGIONS_AND_CITIES[selected_region]); default_city = cities.index("Göteborg") if "Göteborg" in cities else 0
with city_col: selected_city = st.selectbox("City", cities, index=default_city)
with date_col: target_date = st.date_input("Planned activity date", value=date.today())
latitude, longitude = REGIONS_AND_CITIES[selected_region][selected_city]

# Data
historical_frame, pollen_filename = load_historical_pollen()
air, hourly, air_fallback = fetch_city_pollution(latitude, longitude)
weather = fetch_city_weather(latitude, longitude)
comparison_date = previous_year_safe(target_date)
pollen_day, used_date, approximate = select_pollen_benchmark(historical_frame, comparison_date)
historical_records = convert_historical(pollen_day)
live_records, pollen_info = fetch_live_pollen(latitude, longitude, target_date)
pollen_records = live_records or historical_records
pollen_mode = "Current regional forecast" if live_records else "Historical Gothenburg fallback"

if air_fallback: st.warning("Live air-quality data is unavailable; clearly marked fallback values are being used.")
if weather.get("fallback"): st.warning("Live weather data is unavailable; estimated fallback values are being used.")
if live_records:
    st.success(f"Using the current pollen forecast for {pollen_info.get('region')} ({pollen_info.get('distance_km', 0):.0f} km from the selected location).")
else:
    st.warning(f"{pollen_info.get('reason')} Using the historical Gothenburg benchmark instead.")

result = describe_overall_conditions(
    air_data=air, pollen_records=pollen_records, weather_data=weather,
    selected_categories=preferences["selected_categories"], selected_gases=preferences["selected_gases"],
    selected_pollen_groups=preferences["selected_pollen_groups"], selected_pollen_types=preferences["selected_pollen_types"], selected_weather=preferences["selected_weather"],
)

render_overall_result(result)
show_result_dialog_if_requested(result)
st.markdown("### Your selected condition areas")
render_category_sections(result, air, weather, pollen_records)

with st.expander("📍 Location and data coverage map"):
    render_location_map(selected_city, latitude, longitude, pollen_info)

with st.expander("📈 48-hour air-quality forecast"):
    choices = [name for name in ("european_aqi", "pm2_5", "pm10", "nitrogen_dioxide") if name in hourly.columns]
    if not hourly.empty and "time" in hourly and choices:
        metric = st.radio("Measurement", choices, format_func=lambda x: {"european_aqi": "Overall pollution index", "pm2_5": "PM2.5 particles", "pm10": "PM10 particles", "nitrogen_dioxide": "Nitrogen dioxide"}[x], horizontal=True)
        st.plotly_chart(px.line(hourly, x="time", y=metric, labels={"time": "Time", metric: "Value"}), use_container_width=True)
    else: st.info("The 48-hour forecast is unavailable.")

with st.expander("🌾 Historical pollen comparison"):
    st.caption(f"Current recommendation source: {pollen_mode}. Historical file: {pollen_filename}.")
    if not pollen_day.empty:
        if approximate: st.info(f"Closest historical observation to {comparison_date}: {used_date}.")
        figure = px.bar(pollen_day.sort_values("Level_Value"), x="Level_Value", y="Pollen", orientation="h", color="Level_Value", range_color=[0, 6], text="Level_Value", labels={"Level_Value": "Pollen level", "Pollen": "Species"})
        figure.update_layout(height=320, coloraxis_showscale=False); st.plotly_chart(figure, use_container_width=True)
    else: st.info("No suitable historical observation was found.")

st.caption("Air and weather: Open-Meteo · Pollen: Pollenrapporten or clearly marked historical fallback · Air Aware does not replace medical advice.")
