import streamlit as st


# --------------------------------------------------
# Visual status settings
# --------------------------------------------------

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


# --------------------------------------------------
# Formatting helpers
# --------------------------------------------------

def display_value(value, unit="", decimals=1):
    """
    Format a measurement for display.
    """

    if value is None:
        return "Unavailable"

    try:
        formatted_value = f"{float(value):.{decimals}f}"

        if unit:
            return f"{formatted_value} {unit}"

        return formatted_value

    except (TypeError, ValueError):
        return "Unavailable"


def format_pollen_value(value):
    """
    Format a pollen status.
    """

    if value is None:
        return "Unavailable"

    return str(value).replace("_", " ").title()


def get_status_display(status):
    """
    Find the visual settings for a status.
    """

    return STATUS_DISPLAY.get(
        status,
        STATUS_DISPLAY["unavailable"],
    )


# --------------------------------------------------
# Main recommendation
# --------------------------------------------------

def show_main_recommendation(result, recommendation, city):
    """
    Display the main recommendation card.
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
            margin-top: 10px;
            margin-bottom: 20px;
        ">
            <p style="
                margin: 0 0 5px 0;
                color: #475467;
                font-size: 1rem;
            ">
                Current recommendation for {city}
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


# --------------------------------------------------
# Status overview
# --------------------------------------------------

def show_status_overview(result):
    """
    Display overall, air and pollen statuses.
    """

    st.subheader("Conditions at a glance")

    overall_display = get_status_display(
        result["status"]
    )

    air_display = get_status_display(
        result["air_status"]
    )

    pollen_display = get_status_display(
        result["pollen_status"]
    )

    overall_column, air_column, pollen_column = st.columns(3)

    overall_column.metric(
        "Outdoor viability",
        f"{overall_display['icon']} {result['score']}/100",
    )

    air_column.metric(
        "Air quality",
        f"{air_display['icon']} {air_display['label']}",
    )

    pollen_column.metric(
        "Pollen",
        f"{pollen_display['icon']} {pollen_display['label']}",
    )


# --------------------------------------------------
# Environmental measurements
# --------------------------------------------------

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
    Display current air and weather measurements.
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


# --------------------------------------------------
# Pollen
# --------------------------------------------------

def show_pollen_details(pollen_data, using_sample_pollen):
    """
    Display tree, grass and weed pollen.
    """

    st.subheader("Pollen details")

    tree_column, grass_column, weed_column = st.columns(3)

    tree_column.metric(
        "Tree pollen",
        format_pollen_value(pollen_data.get("tree")),
    )

    grass_column.metric(
        "Grass pollen",
        format_pollen_value(pollen_data.get("grass")),
    )

    weed_column.metric(
        "Weed pollen",
        format_pollen_value(pollen_data.get("weed")),
    )

    if using_sample_pollen:
        st.info(
            "The pollen values are sample data for the prototype. "
            "Live pollen information is not connected yet."
        )


# --------------------------------------------------
# Advice
# --------------------------------------------------

def show_practical_advice(recommendation):
    """
    Display activity and sensitive-group advice.
    """

    st.subheader("Practical advice")

    exercise_column, sensitive_column = st.columns(2)

    with exercise_column:
        st.markdown("#### 🏃 Outdoor activity")
        st.write(recommendation["exercise"])

    with sensitive_column:
        st.markdown("#### 🫁 Sensitive groups")
        st.write(recommendation["sensitive"])


# --------------------------------------------------
# Explanations
# --------------------------------------------------

def show_explanations():
    """
    Explain technical terms.
    """

    with st.expander("What do these measurements mean?"):
        st.markdown(
            """
            **European AQI:** A combined air-quality index.
            Lower values represent cleaner air.

            **PM2.5:** Very small particles that can travel
            deeply into the lungs.

            **PM10:** Inhalable particles such as dust and
            road particles.

            **NO₂:** Nitrogen dioxide, a gas commonly connected
            to traffic and combustion.

            **Outdoor viability:** Air Aware's simplified score
            based on air quality, weather and pollen.
            """
        )


# --------------------------------------------------
# Data sources
# --------------------------------------------------

def show_data_information(
    weather_source,
    pollen_data,
    using_sample_pollen,
):
    """
    Display sources and pollen update information.
    """

    if using_sample_pollen:
        pollen_source = pollen_data.get(
            "source",
            "Sample pollen data",
        )
    else:
        pollen_source = pollen_data.get(
            "source",
            "Unknown pollen source",
        )

    st.caption(
        f"Air-quality source: Open-Meteo | "
        f"Weather source: {weather_source} | "
        f"Pollen source: {pollen_source}"
    )

    pollen_updated = pollen_data.get("updated_at")

    if pollen_updated:
        st.caption(
            f"Pollen data timestamp: {pollen_updated}"
        )


# --------------------------------------------------
# Complete dashboard
# --------------------------------------------------

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
    pollen_data,
    using_sample_pollen,
):
    """
    Display the complete Air Aware summary.
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

    show_pollen_details(
        pollen_data=pollen_data,
        using_sample_pollen=using_sample_pollen,
    )

    show_practical_advice(recommendation)

    show_explanations()

    show_data_information(
        weather_source=weather_source,
        pollen_data=pollen_data,
        using_sample_pollen=using_sample_pollen,
    )
