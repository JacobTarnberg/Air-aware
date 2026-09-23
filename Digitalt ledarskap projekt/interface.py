import streamlit as st


STATUS_DISPLAY = {
    "good": {
        "label": "Good",
        "icon": "✅",
        "color": "#18794E",
    },
    "fair": {
        "label": "Fair",
        "icon": "ℹ️",
        "color": "#0F6CBD",
    },
    "moderate": {
        "label": "Moderate",
        "icon": "⚠️",
        "color": "#B25E09",
    },
    "poor": {
        "label": "Poor",
        "icon": "▲",
        "color": "#C2410C",
    },
    "very_poor": {
        "label": "Very poor",
        "icon": "⛔",
        "color": "#B42318",
    },
    "extremely_poor": {
        "label": "Extremely poor",
        "icon": "🚫",
        "color": "#7A1F5C",
    },
    "unavailable": {
        "label": "Unavailable",
        "icon": "❓",
        "color": "#667085",
    },
}


def display_value(value, unit="", decimals=1):
    """
    Format a number for the interface.
    """

    if value is None:
        return "Unavailable"

    try:
        return f"{float(value):.{decimals}f} {unit}".strip()

    except (TypeError, ValueError):
        return "Unavailable"


def get_status_display(status):
    """
    Return visual information for a status.
    """

    return STATUS_DISPLAY.get(
        status,
        STATUS_DISPLAY["unavailable"],
    )


def show_main_recommendation(result, recommendation, city):
    """
    Display the main outdoor recommendation.
    """

    display = get_status_display(result["status"])

    reasons_text = " • ".join(result["reasons"])

    st.markdown(
        f"""
        <div style="
            background-color: #F7FAFC;
            border: 2px solid {display['color']};
            border-left: 10px solid {display['color']};
            padding: 24px;
            border-radius: 12px;
            margin-bottom: 20px;
        ">
            <p style="
                margin: 0 0 5px 0;
                color: #475467;
                font-size: 1rem;
            ">
                Current outdoor recommendation for {city}
            </p>

            <h2 style="
                margin: 0;
                color: #101828;
            ">
                {display['icon']} {result['verdict']}
            </h2>

            <p style="
                margin: 10px 0 0 0;
                color: #344054;
                font-size: 1.05rem;
            ">
                {recommendation['general']}
            </p>

            <p style="
                margin: 12px 0 0 0;
                color: #475467;
                font-size: 0.9rem;
            ">
                <strong>Why?</strong> {reasons_text}
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def show_status_overview(result):
    """
    Display overall, air-quality and pollen statuses.
    """

    st.subheader("Conditions at a glance")

    overall_display = get_status_display(result["status"])
    air_display = get_status_display(result["air_status"])
    pollen_display = get_status_display(result["pollen_status"])

    overall_column, air_column, pollen_column = st.columns(3)

    overall_column.metric(
        "Outdoor viability",
        f"{overall_display['icon']} {result['score']}/100",
        help="Combined score based on air quality, weather and pollen when available.",
    )

    air_column.metric(
        "Air quality",
        f"{air_display['icon']} {air_display['label']}",
    )

    pollen_column.metric(
        "Pollen",
        f"{pollen_display['icon']} {pollen_display['label']}",
    )


def show_environmental_metrics(
    aqi,
    pm25,
    pm10,
    no2,
    temperature,
    wind_speed,
    precipitation,
):
    """
    Display current environmental measurements.
    """

    st.subheader("Current measurements")

    first, second, third, fourth = st.columns(4)

    first.metric(
        "European AQI",
        display_value(aqi, decimals=0),
    )

    second.metric(
        "PM2.5",
        display_value(pm25, "µg/m³"),
    )

    third.metric(
        "PM10",
        display_value(pm10, "µg/m³"),
    )

    fourth.metric(
        "NO₂",
        display_value(no2, "µg/m³"),
    )

    temperature_column, wind_column, rain_column = st.columns(3)

    temperature_column.metric(
        "Temperature",
        display_value(temperature, "°C"),
    )

    wind_column.metric(
        "Wind speed",
        display_value(wind_speed, "m/s"),
    )

    rain_column.metric(
        "Precipitation",
        display_value(precipitation, "mm"),
    )


def show_pollen_details(pollen_data=None):
    """
    Display pollen categories.

    This automatically shows unavailable until pollen is connected.
    """

    st.subheader("Pollen details")

    pollen_data = pollen_data or {}

    tree = pollen_data.get("tree")
    grass = pollen_data.get("grass")
    weed = pollen_data.get("weed")

    tree_column, grass_column, weed_column = st.columns(3)

    tree_column.metric(
        "Tree pollen",
        str(tree).replace("_", " ").title()
        if tree is not None
        else "Unavailable",
    )

    grass_column.metric(
        "Grass pollen",
        str(grass).replace("_", " ").title()
        if grass is not None
        else "Unavailable",
    )

    weed_column.metric(
        "Weed pollen",
        str(weed).replace("_", " ").title()
        if weed is not None
        else "Unavailable",
    )

    if not pollen_data:
        st.info(
            "Pollen data has not been connected yet. "
            "The current outdoor score does not include pollen."
        )


def show_practical_advice(recommendation):
    """
    Display advice for different users.
    """

    st.subheader("Practical advice")

    exercise_column, sensitive_column = st.columns(2)

    with exercise_column:
        st.markdown("#### 🏃 Outdoor activity")
        st.write(recommendation["exercise"])

    with sensitive_column:
        st.markdown("#### 🫁 Sensitive groups")
        st.write(recommendation["sensitive"])


def show_explanations():
    """
    Explain technical measurements.
    """

    with st.expander("What do these measurements mean?"):
        st.markdown(
            """
            **European AQI:** A combined air-quality index. Lower values
            represent cleaner air.

            **PM2.5:** Very small particles that can travel deeply into
            the lungs.

            **PM10:** Inhalable particles such as dust and road particles.

            **NO₂:** Nitrogen dioxide, a gas commonly associated with
            traffic and combustion.

            **Outdoor viability score:** Air Aware's simplified score based
            on air quality, weather and pollen when available.
            """
        )


def show_data_information(
    pollution_source="Open-Meteo",
    weather_source="Unknown",
    pollen_source=None,
    updated_at=None,
):
    """
    Display data sources and update information.
    """

    st.caption(
        f"Air-quality source: {pollution_source} | "
        f"Weather source: {weather_source} | "
        f"Pollen source: {pollen_source or 'Not connected'}"
    )

    if updated_at is not None:
        st.caption(f"Last retrieved: {updated_at}")


def show_air_aware_dashboard(
    city,
    result,
    recommendation,
    aqi,
    pm25,
    pm10,
    no2,
    temperature,
    wind_speed,
    precipitation,
    weather_source,
    pollen_data=None,
    pollen_source=None,
):
    """
    Display the complete Air Aware summary.

    app_jonnamada.py only needs to call this one function.
    """

    show_main_recommendation(
        result=result,
        recommendation=recommendation,
        city=city,
    )

    show_status_overview(result)

    show_environmental_metrics(
        aqi=aqi,
        pm25=pm25,
        pm10=pm10,
        no2=no2,
        temperature=temperature,
        wind_speed=wind_speed,
        precipitation=precipitation,
    )

    show_pollen_details(pollen_data)

    show_practical_advice(recommendation)

    show_explanations()

    show_data_information(
        pollution_source="Open-Meteo",
        weather_source=weather_source,
        pollen_source=pollen_source,
        updated_at=None,
    )
