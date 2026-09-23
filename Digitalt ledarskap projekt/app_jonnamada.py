from datetime import datetime

import pandas as pd
import plotly.express as px
import requests
import streamlit as st

from interface import show_air_aware_dashboard
from recommendations import (
    calculate_viability,
    get_recommendation,
)
from sample_data_jonnamada import sample_pollen_data


# --------------------------------------------------
# Page configuration
# --------------------------------------------------

st.set_page_config(
    page_title="Air Aware",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)


# --------------------------------------------------
# Locations
# --------------------------------------------------

LOCATIONS = {
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
    "Falkenberg": (56.9055, 12.4912),
    "Halmstad": (56.6745, 12.8578),
    "Kungsbacka": (57.4872, 12.0761),
    "Varberg": (57.1056, 12.2508),
    "Helsingborg": (56.0465, 12.6945),
    "Lund": (55.7047, 13.1910),
    "Malmö": (55.6050, 13.0038),
    "Stockholm": (59.3293, 18.0686),
    "Uppsala": (59.8586, 17.6389),
    "Linköping": (58.4108, 15.6214),
    "Örebro": (59.2753, 15.2134),
    "Västerås": (59.6099, 16.5448),
    "Jönköping": (57.7826, 14.1618),
    "Umeå": (63.8258, 20.2630),
    "Karlstad": (59.3793, 13.5036),
    "Visby": (57.6348, 18.2948),
}


OPEN_METEO_AIR_URL = (
    "https://air-quality-api.open-meteo.com/v1/air-quality"
)

OPEN_METEO_WEATHER_URL = (
    "https://api.open-meteo.com/v1/forecast"
)


# This remains True until a live pollen API is connected.
USING_SAMPLE_POLLEN = True


# --------------------------------------------------
# Air-quality API
# --------------------------------------------------

@st.cache_data(ttl=900, show_spinner=False)
def fetch_city_pollution(lat, lon):
    """
    Fetch current and forecast air-quality data.
    """

    params = {
        "latitude": lat,
        "longitude": lon,
        "current": (
            "european_aqi,"
            "pm10,"
            "pm2_5,"
            "nitrogen_dioxide,"
            "ozone"
        ),
        "hourly": (
            "european_aqi,"
            "pm2_5,"
            "pm10,"
            "nitrogen_dioxide"
        ),
        "timezone": "Europe/Stockholm",
        "forecast_days": 2,
    }

    try:
        response = requests.get(
            OPEN_METEO_AIR_URL,
            params=params,
            timeout=10,
        )

        response.raise_for_status()

        data = response.json()

        current = data.get("current", {})
        hourly = pd.DataFrame(
            data.get("hourly", {})
        )

        return current, hourly, False

    except requests.RequestException:
        fallback_current = {
            "european_aqi": 18,
            "pm2_5": 4.5,
            "pm10": 11.2,
            "nitrogen_dioxide": 9.4,
        }

        fallback_hourly = pd.DataFrame({
            "time": [
                datetime.now().strftime(
                    "%Y-%m-%dT%H:00"
                )
            ],
            "european_aqi": [18],
            "pm2_5": [4.5],
            "pm10": [11.2],
            "nitrogen_dioxide": [9.4],
        })

        return fallback_current, fallback_hourly, True


# --------------------------------------------------
# Weather API
# --------------------------------------------------

@st.cache_data(ttl=600, show_spinner=False)
def fetch_city_weather(lat, lon):
    """
    Fetch current weather data from Open-Meteo.
    """

    params = {
        "latitude": lat,
        "longitude": lon,
        "current": (
            "temperature_2m,"
            "relative_humidity_2m,"
            "precipitation,"
            "wind_speed_10m,"
            "cloud_cover"
        ),
        "timezone": "Europe/Stockholm",
    }

    try:
        response = requests.get(
            OPEN_METEO_WEATHER_URL,
            params=params,
            timeout=10,
        )

        response.raise_for_status()

        current = response.json().get(
            "current",
            {},
        )

        return {
            "source": "Open-Meteo",
            "temperature": current.get(
                "temperature_2m"
            ),
            "wind_speed": current.get(
                "wind_speed_10m"
            ),
            "humidity": current.get(
                "relative_humidity_2m"
            ),
            "precipitation": current.get(
                "precipitation"
            ),
            "cloudiness": current.get(
                "cloud_cover"
            ),
            "using_fallback": False,
        }

    except requests.RequestException:
        return {
            "source": "Estimated fallback",
            "temperature": 16.0,
            "wind_speed": 3.0,
            "humidity": 60.0,
            "precipitation": 0.0,
            "cloudiness": 30.0,
            "using_fallback": True,
        }


# --------------------------------------------------
# Header
# --------------------------------------------------

header_column, refresh_column = st.columns([5, 1])

with header_column:
    st.title("🌿 Air Aware")
    st.caption(
        "Understand the air before you go outside."
    )

with refresh_column:
    if st.button(
        "🔄 Refresh",
        use_container_width=True,
    ):
        st.cache_data.clear()
        st.rerun()


# --------------------------------------------------
# Location selection
# --------------------------------------------------

available_cities = sorted(LOCATIONS.keys())

default_city_index = (
    available_cities.index("Göteborg")
    if "Göteborg" in available_cities
    else 0
)

selected_city = st.selectbox(
    "📍 Select municipality or city",
    options=available_cities,
    index=default_city_index,
)

latitude, longitude = LOCATIONS[selected_city]


# --------------------------------------------------
# Retrieve live data
# --------------------------------------------------

current_pollution, hourly_data, air_fallback = (
    fetch_city_pollution(
        latitude,
        longitude,
    )
)

weather_data = fetch_city_weather(
    latitude,
    longitude,
)


# --------------------------------------------------
# Extract values
# --------------------------------------------------

aqi_value = current_pollution.get(
    "european_aqi"
)

pm25_value = current_pollution.get(
    "pm2_5"
)

pm10_value = current_pollution.get(
    "pm10"
)

no2_value = current_pollution.get(
    "nitrogen_dioxide"
)

temperature_value = weather_data.get(
    "temperature"
)

wind_value = weather_data.get(
    "wind_speed"
)

rain_value = weather_data.get(
    "precipitation"
)

weather_source = weather_data.get(
    "source",
    "Unknown",
)


# --------------------------------------------------
# Pollen data
# --------------------------------------------------

# This is temporary sample data.
# Replace this later with the live pollen API result.

pollen_data = sample_pollen_data


# --------------------------------------------------
# Calculate recommendation
# --------------------------------------------------

viability_result = calculate_viability(
    aqi=aqi_value,
    temperature=temperature_value,
    wind_speed=wind_value,
    precipitation=rain_value,
    pollen_data=pollen_data,
)

recommendation = get_recommendation(
    viability_result
)


# --------------------------------------------------
# Fallback warnings
# --------------------------------------------------

if air_fallback:
    st.warning(
        "The live air-quality API could not be reached. "
        "Temporary fallback air-quality values are being shown."
    )

if weather_data.get("using_fallback"):
    st.warning(
        "The live weather API could not be reached. "
        "Estimated weather values are being shown."
    )


# --------------------------------------------------
# Display Jonna's interface
# --------------------------------------------------

show_air_aware_dashboard(
    city=selected_city,
    result=viability_result,
    recommendation=recommendation,
    aqi=aqi_value,
    pm25=pm25_value,
    pm10=pm10_value,
    no2=no2_value,
    temperature=temperature_value,
    wind_speed=wind_value,
    precipitation=rain_value,
    weather_source=weather_source,
    pollen_data=pollen_data,
    using_sample_pollen=USING_SAMPLE_POLLEN,
)

st.markdown("---")


# --------------------------------------------------
# Additional charts
# --------------------------------------------------

chart_column_one, chart_column_two = st.columns(2)

with chart_column_one:
    st.subheader(
        f"Current air-quality profile — {selected_city}"
    )

    pollutant_data = pd.DataFrame({
        "Measurement": [
            "PM2.5",
            "PM10",
            "NO₂",
            "European AQI",
        ],
        "Value": [
            pm25_value,
            pm10_value,
            no2_value,
            aqi_value,
        ],
    })

    pollutant_chart = px.bar(
        pollutant_data,
        x="Measurement",
        y="Value",
        color="Measurement",
        text_auto=".1f",
        title="Current measurements",
        color_discrete_sequence=[
            "#0F6CBD",
            "#67C7E8",
            "#18794E",
            "#7A1F5C",
        ],
    )

    pollutant_chart.update_layout(
        showlegend=False,
        height=340,
        margin={
            "l": 20,
            "r": 20,
            "t": 40,
            "b": 20,
        },
    )

    st.plotly_chart(
        pollutant_chart,
        use_container_width=True,
    )


with chart_column_two:
    st.subheader(
        f"48-hour forecast — {selected_city}"
    )

    chart_options = [
        "european_aqi",
        "pm2_5",
        "pm10",
        "nitrogen_dioxide",
    ]

    available_chart_options = [
        option
        for option in chart_options
        if option in hourly_data.columns
    ]

    if (
        not hourly_data.empty
        and "time" in hourly_data.columns
        and available_chart_options
    ):
        selected_measurement = st.radio(
            "Select measurement",
            options=available_chart_options,
            format_func=lambda value: (
                value.upper().replace("_", " ")
            ),
            horizontal=True,
        )

        measurement_label = (
            selected_measurement
            .upper()
            .replace("_", " ")
        )

        forecast_chart = px.line(
            hourly_data,
            x="time",
            y=selected_measurement,
            title=(
                f"Predicted {measurement_label} "
                f"for the next 48 hours"
            ),
            labels={
                "time": "Date and time",
                selected_measurement: "Value",
            },
        )

        forecast_chart.update_traces(
            line={
                "color": "#0F6CBD",
                "width": 2.5,
            }
        )

        forecast_chart.update_layout(
            height=340,
            hovermode="x unified",
            margin={
                "l": 20,
                "r": 20,
                "t": 40,
                "b": 20,
            },
        )

        st.plotly_chart(
            forecast_chart,
            use_container_width=True,
        )

    else:
        st.info(
            "The 48-hour forecast is unavailable."
        )


# --------------------------------------------------
# General disclaimer
# --------------------------------------------------

st.caption(
    "Air Aware provides general environmental information "
    "and does not replace individual medical advice."
)
