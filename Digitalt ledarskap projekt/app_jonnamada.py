from datetime import datetime
import pandas as pd
import plotly.express as px
import requests
import streamlit as st
from recommendations import calculate_viability, get_recommendation
from interface import show_air_aware_dashboard

# --------------------------------------------------
# Page configuration
# --------------------------------------------------
st.set_page_config(
    page_title="Air-aware | Outdoor Viability Index",
    page_icon="🚶‍♂️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --------------------------------------------------
# Swedish Municipalities & Coordinates
# --------------------------------------------------
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
    # Halland
    "Falkenberg": (56.9055, 12.4912),
    "Halmstad": (56.6745, 12.8578),
    "Kungsbacka": (57.4872, 12.0761),
    "Varberg": (57.1056, 12.2508),
    # Skåne
    "Helsingborg": (56.0465, 12.6945),
    "Lund": (55.7047, 13.1910),
    "Malmö": (55.6050, 13.0038),
    # Other Key Cities
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

OPEN_METEO_AIR_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"


# --------------------------------------------------
# Safe API Fetchers with Fallbacks
# --------------------------------------------------
@st.cache_data(ttl=900, show_spinner=False)
def fetch_city_pollution(lat: float, lon: float):
    """Fetch live and 48-hour air quality from Open-Meteo."""
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": ["european_aqi", "pm10", "pm2_5", "nitrogen_dioxide", "ozone"],
        "hourly": ["european_aqi", "pm2_5", "pm10", "nitrogen_dioxide"],
        "timezone": "Europe/Stockholm",
        "forecast_days": 2,
    }
    try:
        r = requests.get(OPEN_METEO_AIR_URL, params=params, timeout=5)
        if r.status_code == 200:
            data = r.json()
            curr = data.get("current", {})
            hourly = pd.DataFrame(data.get("hourly", {}))
            return curr, hourly
    except Exception:
        pass

    fallback_curr = {"european_aqi": 18, "pm2_5": 4.5, "pm10": 11.2, "nitrogen_dioxide": 9.4}
    fallback_hourly = pd.DataFrame({
        "time": [datetime.now().strftime("%Y-%m-%dT%H:00")],
        "european_aqi": [18],
        "pm2_5": [4.5],
        "pm10": [11.2],
        "nitrogen_dioxide": [9.4],
    })
    return fallback_curr, fallback_hourly


@st.cache_data(ttl=600, show_spinner=False)
def fetch_city_weather(lat: float, lon: float):
    """Fetch weather data from SMHI or Open-Meteo fallback."""
    # 1. SMHI
    try:
        url = (
            "https://opendata-download-metfcst.smhi.se/api/"
            "category/snow1g/version/1/geotype/point/"
            f"lon/{lon:.3f}/lat/{lat:.3f}/data.json"
        )
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            data = r.json()
            fc = data["timeSeries"][0]["data"]
            return {
                "source": "SMHI",
                "temperature": fc.get("air_temperature", 15.0),
                "wind_speed": fc.get("wind_speed", 3.5),
                "humidity": fc.get("relative_humidity", 65.0),
                "precipitation": fc.get("precipitation_amount_mean", 0.0),
                "cloudiness": fc.get("cloud_area_fraction", 50.0),
            }
    except Exception:
        pass

    # 2. Open-Meteo Weather fallback
    try:
        om_url = "https://api.open-meteo.com/v1/forecast"
        om_params = {
            "latitude": lat,
            "longitude": lon,
            "current": ["temperature_2m", "relative_humidity_2m", "precipitation", "wind_speed_10m", "cloud_cover"],
        }
        r = requests.get(om_url, params=om_params, timeout=5)
        if r.status_code == 200:
            c = r.json().get("current", {})
            return {
                "source": "Open-Meteo",
                "temperature": c.get("temperature_2m", 15.0),
                "wind_speed": c.get("wind_speed_10m", 3.5),
                "humidity": c.get("relative_humidity_2m", 65.0),
                "precipitation": c.get("precipitation", 0.0),
                "cloudiness": c.get("cloud_cover", 50.0),
            }
    except Exception:
        pass

    return {
        "source": "Estimated",
        "temperature": 16.0,
        "wind_speed": 3.0,
        "humidity": 60.0,
        "precipitation": 0.0,
        "cloudiness": 30.0,
    }


# --------------------------------------------------
# Viability Decision Engine
# --------------------------------------------------
def calculate_viability(aqi, temp, wind, precip):
    score = 100
    reasons = []

    if aqi is not None:
        if aqi > 80:
            score -= 50
            reasons.append("Very poor air quality (High AQI)")
        elif aqi > 50:
            score -= 30
            reasons.append("Moderate air pollution")
        elif aqi > 25:
            score -= 10
            reasons.append("Fair air quality with minor particulate matter")

    if precip is not None:
        if precip >= 3.0:
            score -= 40
            reasons.append(f"Heavy rain ({precip:.1f} mm)")
        elif precip > 0.2:
            score -= 15
            reasons.append(f"Light rain or showers ({precip:.1f} mm)")

    if wind is not None:
        if wind >= 13.0:
            score -= 35
            reasons.append(f"Strong winds ({wind:.1f} m/s)")
        elif wind >= 8.0:
            score -= 15
            reasons.append(f"Breezy conditions ({wind:.1f} m/s)")

    if temp is not None:
        if temp < -5:
            score -= 25
            reasons.append(f"Freezing temperature ({temp:.1f} °C)")
        elif temp < 5:
            score -= 10
            reasons.append(f"Chilly weather ({temp:.1f} °C)")
        elif temp > 30:
            score -= 25
            reasons.append(f"High heat ({temp:.1f} °C)")

    score = max(0, min(100, score))

    if score >= 80:
        verdict = "Optimal for Outdoor Activities"
        color = "#28a745"
        icon = "🟢"
    elif score >= 55:
        verdict = "Fair / Acceptable Conditions"
        color = "#ffc107"
        icon = "🟡"
    elif score >= 35:
        verdict = "Poor / Caution Advised"
        color = "#fd7e14"
        icon = "🟠"
    else:
        verdict = "Unfavorable / Stay Indoors"
        color = "#dc3545"
        icon = "🔴"

    return score, verdict, color, icon, reasons


# --------------------------------------------------
# Header & Controls
# --------------------------------------------------
header_col1, header_col2 = st.columns([5, 1])
with header_col1:
    st.title("🚶‍♂️ Air-aware: Outdoor Viability Engine")
    st.caption("Live synthesis of air quality (Copernicus / Open-Meteo) and meteorological conditions (SMHI)[cite: 3, 4].")

with header_col2:
    if st.button("🔄 Refresh Data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

st.markdown("---")

# --------------------------------------------------
# Location Selector & Computation
# --------------------------------------------------
available_cities = sorted(list(LOCATIONS.keys()))
default_idx = available_cities.index("Göteborg") if "Göteborg" in available_cities else 0

city_col, verdict_col = st.columns([2, 3])

with city_col:
    selected_city = st.selectbox("📍 Select Municipality / City", options=available_cities, index=default_idx)

lat, lon = LOCATIONS[selected_city]

curr_pol, hourly_df = fetch_city_pollution(lat, lon)
wx = fetch_city_weather(lat, lon)

aqi_val = curr_pol.get("european_aqi", 15)
pm25_val = curr_pol.get("pm2_5", 5.0)
pm10_val = curr_pol.get("pm10", 12.0)
no2_val = curr_pol.get("nitrogen_dioxide", 8.0)

temp_val = wx.get("temperature", 15.0)
wind_val = wx.get("wind_speed", 3.0)
rain_val = wx.get("precipitation", 0.0)
hum_val = wx.get("humidity", 60.0)
wx_source = wx.get("source", "SMHI")

score, verdict, v_color, v_icon, notes = calculate_viability(aqi_val, temp_val, wind_val, rain_val)

with verdict_col:
    note_text = ", ".join(notes) if notes else "Ideal conditions with minimal pollution and calm weather."
    st.markdown(
        f"""
        <div style="background-color: #1a1c24; padding: 18px 22px; border-radius: 8px; border-left: 7px solid {v_color};">
            <h3 style="margin: 0; color: white;">Viability Score: <span style="color:{v_color};">{score}/100</span> — {v_icon} {verdict}</h3>
            <p style="color: #c9d1d9; margin: 6px 0 0 0; font-size: 0.95rem;">
                <b>City:</b> {selected_city} ({lat:.2f}°N, {lon:.2f}°E) | <b>Factors:</b> {note_text}
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("###")

# --------------------------------------------------
# Metric Matrix
# --------------------------------------------------
m1, m2, m3, m4, m5, m6 = st.columns(6)
m1.metric("European AQI", f"{aqi_val:.0f}", help="European Air Quality Index: 0–20 Good, 80+ Very Poor")
m2.metric("PM2.5 / PM10", f"{pm25_val:.1f} / {pm10_val:.1f} µg/m³")
m3.metric("NO₂ Level", f"{no2_val:.1f} µg/m³")
m4.metric("Temperature", f"{temp_val:.1f} °C")
m5.metric("Wind Speed", f"{wind_val:.1f} m/s")
m6.metric("Precipitation", f"{rain_val:.1f} mm", help=f"Source: {wx_source}")

st.markdown("---")

# --------------------------------------------------
# Analytical Plots (No Map)
# --------------------------------------------------
chart_col1, chart_col2 = st.columns([1, 1])

with chart_col1:
    st.subheader(f"📊 Atmospheric Profile — {selected_city}")
    
    pollutant_df = pd.DataFrame({
        "Pollutant": ["PM2.5", "PM10", "NO₂", "European AQI"],
        "Current Value": [pm25_val, pm10_val, no2_val, aqi_val],
        "Unit": ["µg/m³", "µg/m³", "µg/m³", "Index"]
    })
    
    fig_bars = px.bar(
        pollutant_df,
        x="Pollutant",
        y="Current Value",
        color="Pollutant",
        text_auto=".1f",
        title="Current Air Quality Breakdown",
        color_discrete_sequence=["#636EFA", "#EF553B", "#00CC96", "#AB63FA"]
    )
    fig_bars.update_layout(showlegend=False, height=340, margin=dict(l=20, r=20, t=40, b=20))
    st.plotly_chart(fig_bars, use_container_width=True)

with chart_col2:
    st.subheader(f"📈 48-Hour Forecast Curve — {selected_city}")
    if not hourly_df.empty and "time" in hourly_df.columns:
        metric_choice = st.radio(
            "Select Parameter to Chart:",
            options=["european_aqi", "pm2_5", "pm10", "nitrogen_dioxide"],
            format_func=lambda x: x.upper().replace("_", " "),
            horizontal=True,
        )
        if metric_choice in hourly_df.columns:
            fig_line = px.line(
                hourly_df,
                x="time",
                y=metric_choice,
                title=f"Predicted {metric_choice.upper().replace('_', ' ')} (Next 48 Hours)",
                labels={"time": "Date / Time", metric_choice: "Value"},
            )
            fig_line.update_traces(line=dict(color="#1f77b4", width=2.5))
            fig_line.update_layout(margin=dict(l=20, r=20, t=35, b=20), height=300, hovermode="x unified")
            st.plotly_chart(fig_line, use_container_width=True)
    else:
        st.info("48-hour forecast is loading or unavailable.")

# --------------------------------------------------
# Practical Advice Drawer
# --------------------------------------------------
with st.expander("🩺 Health, Exercise & Commute Advisory", expanded=True):
    adv1, adv2, adv3 = st.columns(3)
    with adv1:
        st.markdown("**🏃‍♂️ Exercise Recommendation**")
        if score >= 80:
            st.success("Great conditions for outdoor exercise, jogging, or cycling.")
        elif score >= 55:
            st.info("Suitable for moderate activities. Consider pacing yourself if windy or humid.")
        else:
            st.warning("Consider shifting your workouts indoors to avoid particulate or harsh weather.")

    with adv2:
        st.markdown("**👶 Sensitive Groups**")
        if aqi_val > 50 or pm25_val > 25:
            st.error("Elevated pollution. Asthmatics and sensitive individuals should limit long outdoor stays.")
        else:
            st.success("Air quality is well within safety thresholds for sensitive groups.")

    with adv3:
        st.markdown("**🧥 Recommended Gear**")
        gear = []
        if rain_val > 0.1:
            gear.append("Rain jacket or umbrella")
        if wind_val >= 8.0:
            gear.append("Windbreaker")
        if temp_val <= 5.0:
            gear.append("Thermal layers & gloves")
        if not gear:
            gear.append("Comfortable outdoor clothing")
        st.write(", ".join(gear))
