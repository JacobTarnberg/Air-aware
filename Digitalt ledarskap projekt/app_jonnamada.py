from datetime import datetime

import pandas as pd
import plotly.express as px
import requests
import streamlit as st

from interface import show_air_aware_dashboard
from recommendations import calculate_viability, get_recommendation
from sample_data_jonnamada import sample_pollen_data


st.set_page_config(page_title="Air Aware", page_icon="🌿", layout="wide")

LOCATIONS = {
    "Göteborg": (57.7089, 11.9746),
    "Borås": (57.7210, 12.9401),
    "Mölndal": (57.6554, 12.0138),
    "Stockholm": (59.3293, 18.0686),
    "Malmö": (55.6050, 13.0038),
    "Uppsala": (59.8586, 17.6389),
}

AIR_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"
USING_SAMPLE_POLLEN = True


@st.cache_data(ttl=900, show_spinner=False)
def fetch_air_quality(latitude, longitude):
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": "european_aqi,pm10,pm2_5,nitrogen_dioxide",
        "hourly": "european_aqi,pm2_5,pm10,nitrogen_dioxide",
        "timezone": "Europe/Stockholm",
        "forecast_days": 2,
    }
    try:
        response = requests.get(AIR_URL, params=params, timeout=10)
        response.raise_for_status()
        payload = response.json()
        return payload.get("current", {}), pd.DataFrame(payload.get("hourly", {})), False
    except (requests.RequestException, ValueError):
        current = {
            "european_aqi": 18,
            "pm2_5": 4.5,
            "pm10": 11.2,
            "nitrogen_dioxide": 9.4,
        }
        hourly = pd.DataFrame(
            {
                "time": [datetime.now().strftime("%Y-%m-%dT%H:00")],
                "european_aqi": [18],
                "pm2_5": [4.5],
                "pm10": [11.2],
                "nitrogen_dioxide": [9.4],
            }
        )
        return current, hourly, True


@st.cache_data(ttl=600, show_spinner=False)
def fetch_weather(latitude, longitude):
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": "temperature_2m,precipitation,wind_speed_10m",
        "timezone": "Europe/Stockholm",
    }
    try:
        response = requests.get(WEATHER_URL, params=params, timeout=10)
        response.raise_for_status()
        current = response.json().get("current", {})
        return {
            "temperature": current.get("temperature_2m"),
            "wind_speed": current.get("wind_speed_10m"),
            "precipitation": current.get("precipitation"),
            "source": "Open-Meteo",
            "fallback": False,
        }
    except (requests.RequestException, ValueError):
        return {
            "temperature": 16.0,
            "wind_speed": 3.0,
            "precipitation": 0.0,
            "source": "Estimated fallback",
            "fallback": True,
        }


title_column, refresh_column = st.columns([5, 1])
with title_column:
    st.title("🌿 Air Aware")
    st.caption("Understand the air before you go outside.")
with refresh_column:
    if st.button("🔄 Refresh", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

cities = sorted(LOCATIONS)
default_index = cities.index("Göteborg")
selected_city = st.selectbox("📍 Select city", cities, index=default_index)
latitude, longitude = LOCATIONS[selected_city]

air, hourly, air_fallback = fetch_air_quality(latitude, longitude)
weather = fetch_weather(latitude, longitude)

aqi = air.get("european_aqi")
pm25 = air.get("pm2_5")
pm10 = air.get("pm10")
no2 = air.get("nitrogen_dioxide")
temperature = weather.get("temperature")
wind_speed = weather.get("wind_speed")
precipitation = weather.get("precipitation")
pollen_data = sample_pollen_data

result = calculate_viability(
    aqi=aqi,
    temperature=temperature,
    wind_speed=wind_speed,
    precipitation=precipitation,
    pollen_data=pollen_data,
)
recommendation = get_recommendation(result)

if air_fallback:
    st.warning("Live air-quality data is unavailable, so fallback values are shown.")
if weather.get("fallback"):
    st.warning("Live weather data is unavailable, so fallback values are shown.")

show_air_aware_dashboard(
    city=selected_city,
    result=result,
    recommendation=recommendation,
    aqi=aqi,
    pm25=pm25,
    pm10=pm10,
    no2=no2,
    temperature=temperature,
    wind_speed=wind_speed,
    precipitation=precipitation,
    weather_source=weather.get("source", "Unknown"),
    pollen_data=pollen_data,
    using_sample_pollen=USING_SAMPLE_POLLEN,
)

st.divider()
left_chart, right_chart = st.columns(2)
with left_chart:
    chart_data = pd.DataFrame(
        {
            "Measurement": ["PM2.5", "PM10", "NO₂", "European AQI"],
            "Value": [pm25, pm10, no2, aqi],
        }
    )
    figure = px.bar(chart_data, x="Measurement", y="Value", color="Measurement")
    figure.update_layout(showlegend=False, height=350)
    st.plotly_chart(figure, use_container_width=True)

with right_chart:
    choices = [
        name
        for name in ("european_aqi", "pm2_5", "pm10", "nitrogen_dioxide")
        if name in hourly.columns
    ]
    if not hourly.empty and "time" in hourly.columns and choices:
        selected_metric = st.selectbox("Forecast measurement", choices)
        figure = px.line(hourly, x="time", y=selected_metric)
        figure.update_layout(height=350)
        st.plotly_chart(figure, use_container_width=True)
    else:
        st.info("The 48-hour forecast is unavailable.")

st.caption("Air Aware provides general information and does not replace medical advice.")
