import streamlit as st


STATUS_DISPLAY = {
    "good": ("Good", "✅", "#18794E"), "fair": ("Fair", "ℹ️", "#0F6CBD"),
    "moderate": ("Moderate", "⚠️", "#B25E09"), "poor": ("Poor", "▲", "#C2410C"),
    "very_poor": ("Very poor", "⛔", "#B42318"), "unavailable": ("Unavailable", "❓", "#667085"),
}


def display_value(value, unit="", decimals=1):
    try:
        rendered = f"{float(value):.{decimals}f}"
        return f"{rendered} {unit}".strip()
    except (TypeError, ValueError):
        return "Unavailable"


def status_parts(status):
    return STATUS_DISPLAY.get(status, STATUS_DISPLAY["unavailable"])


def show_air_aware_dashboard(city, region, result, recommendation, aqi, pm25, pm10, no2, temperature, wind_speed, precipitation, weather_source, pollen_benchmark, pollen_approximate):
    _, icon, color = status_parts(result["status"])
    reasons = " • ".join(result["reasons"])
    st.markdown(
        f"""<div style="background:#F7FAFC;border:2px solid {color};border-left:10px solid {color};padding:24px;border-radius:12px;margin:10px 0 20px">
        <p style="margin:0;color:#475467">Current recommendation for {city}, {region}</p>
        <h2 style="margin:5px 0;color:#101828">{icon} {result['verdict']}</h2>
        <p style="color:#344054">{recommendation['general']}</p>
        <p style="margin:0;color:#475467"><strong>Why?</strong> {reasons}</p></div>""",
        unsafe_allow_html=True,
    )

    overall, air_column, pollen_column = st.columns(3)
    air_label, air_icon, _ = status_parts(result["air_status"])
    pollen_label, pollen_icon, _ = status_parts(result["pollen_status"])
    overall.metric("Outdoor viability", f"{icon} {result['score']}/100")
    air_column.metric("Air quality", f"{air_icon} {air_label}")
    pollen_column.metric("Historical pollen", f"{pollen_icon} {pollen_label}")

    st.subheader("Current measurements")
    metrics = st.columns(4)
    metrics[0].metric("European AQI", display_value(aqi, decimals=0))
    metrics[1].metric("PM2.5", display_value(pm25, "µg/m³"))
    metrics[2].metric("PM10", display_value(pm10, "µg/m³"))
    metrics[3].metric("NO₂", display_value(no2, "µg/m³"))
    weather = st.columns(3)
    weather[0].metric("Temperature", display_value(temperature, "°C"))
    weather[1].metric("Wind speed", display_value(wind_speed, "m/s"))
    weather[2].metric("Precipitation", display_value(precipitation, "mm"))

    st.subheader("Historical pollen benchmark")
    pollen_columns = st.columns(3)
    pollen_columns[0].metric("Highest level", display_value(pollen_benchmark.get("level"), "/ 6", 0))
    pollen_columns[1].metric("Dominant allergen(s)", pollen_benchmark.get("dominant", "Unavailable"))
    pollen_columns[2].metric("Observation date", pollen_benchmark.get("date") or "Unavailable")
    if pollen_benchmark.get("available"):
        message = "This is the nearest observation within 14 days." if pollen_approximate else "An exact historical-date match was found."
        st.info(message + " This is historical context, not a live pollen forecast.")
    else:
        st.warning("No suitable historical pollen observation was found.")

    st.subheader("Practical advice")
    activity, sensitive = st.columns(2)
    with activity:
        st.markdown("#### 🏃 Outdoor activity")
        st.write(recommendation["exercise"])
    with sensitive:
        st.markdown("#### 🫁 Sensitive groups")
        st.write(recommendation["sensitive"])

    with st.expander("What do these measurements mean?"):
        st.markdown("**European AQI:** Lower values mean cleaner air.\n\n**PM2.5:** Very small airborne particles.\n\n**PM10:** Inhalable particles such as dust.\n\n**NO₂:** A gas commonly associated with traffic and combustion.")
    st.caption(f"Air quality: Open-Meteo | Weather: {weather_source} | Pollen: {pollen_benchmark.get('source', 'Unavailable')}")
