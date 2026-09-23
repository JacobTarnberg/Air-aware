import streamlit as st


<<<<<<< HEAD
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

=======
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

>>>>>>> 49c23a2 (for Jonna and Mádá to work with)
    if value is None:
        return "Unavailable"

    try:
<<<<<<< HEAD
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
=======
        return f"{float(value):.{decimals}f} {unit}".strip()

    except (TypeError, ValueError):
        return "Unavailable"


def get_status_display(status):
    """
    Return visual information for a status.
>>>>>>> 49c23a2 (for Jonna and Mádá to work with)
    """

    return STATUS_DISPLAY.get(
        status,
        STATUS_DISPLAY["unavailable"],
    )


<<<<<<< HEAD
# --------------------------------------------------
# Main recommendation
# --------------------------------------------------

def show_main_recommendation(result, recommendation, city):
    """
    Display the main recommendation card.
    """

    display = get_status_display(result["status"])
=======
def show_main_recommendation(result, recommendation, city):
    """
    Display the main outdoor recommendation.
    """

    display = get_status_display(result["status"])

>>>>>>> 49c23a2 (for Jonna and Mádá to work with)
    reasons_text = " • ".join(result["reasons"])

    st.markdown(
        f"""
        <div style="
            background-color: #F7FAFC;
            border: 2px solid {display['color']};
            border-left: 10px solid {display['color']};
            padding: 24px;
            border-radius: 12px;
<<<<<<< HEAD
            margin-top: 10px;
=======
>>>>>>> 49c23a2 (for Jonna and Mádá to work with)
            margin-bottom: 20px;
        ">
            <p style="
                margin: 0 0 5px 0;
                color: #475467;
                font-size: 1rem;
            ">
<<<<<<< HEAD
                Current recommendation for {city}
=======
                Current outdoor recommendation for {city}
>>>>>>> 49c23a2 (for Jonna and Mádá to work with)
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


<<<<<<< HEAD
# --------------------------------------------------
# Status overview
# --------------------------------------------------

def show_status_overview(result):
    """
    Display overall, air and pollen statuses.
=======
def show_status_overview(result):
    """
    Display overall, air-quality and pollen statuses.
>>>>>>> 49c23a2 (for Jonna and Mádá to work with)
    """

    st.subheader("Conditions at a glance")

<<<<<<< HEAD
    overall_display = get_status_display(
        result["status"]
    )

    air_display = get_status_display(
        result["air_status"]
    )

    pollen_display = get_status_display(
        result["pollen_status"]
    )
=======
    overall_display = get_status_display(result["status"])
    air_display = get_status_display(result["air_status"])
    pollen_display = get_status_display(result["pollen_status"])
>>>>>>> 49c23a2 (for Jonna and Mádá to work with)

    overall_column, air_column, pollen_column = st.columns(3)

    overall_column.metric(
        "Outdoor viability",
        f"{overall_display['icon']} {result['score']}/100",
<<<<<<< HEAD
=======
        help="Combined score based on air quality, weather and pollen when available.",
>>>>>>> 49c23a2 (for Jonna and Mádá to work with)
    )

    air_column.metric(
        "Air quality",
        f"{air_display['icon']} {air_display['label']}",
    )

    pollen_column.metric(
        "Pollen",
        f"{pollen_display['icon']} {pollen_display['label']}",
    )


<<<<<<< HEAD
# --------------------------------------------------
# Environmental measurements
# --------------------------------------------------

=======
>>>>>>> 49c23a2 (for Jonna and Mádá to work with)
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
<<<<<<< HEAD
    Display current air and weather measurements.
=======
    Display current environmental measurements.
>>>>>>> 49c23a2 (for Jonna and Mádá to work with)
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

<<<<<<< HEAD
=======
    pollen_data = pollen_data or {}

    tree = pollen_data.get("tree")
    grass = pollen_data.get("grass")
    weed = pollen_data.get("weed")

>>>>>>> 49c23a2 (for Jonna and Mádá to work with)
    tree_column, grass_column, weed_column = st.columns(3)

    tree_column.metric(
        "Tree pollen",
<<<<<<< HEAD
        format_pollen_value(pollen_data.get("tree")),
=======
        str(tree).replace("_", " ").title()
        if tree is not None
        else "Unavailable",
>>>>>>> 49c23a2 (for Jonna and Mádá to work with)
    )

    grass_column.metric(
        "Grass pollen",
<<<<<<< HEAD
        format_pollen_value(pollen_data.get("grass")),
=======
        str(grass).replace("_", " ").title()
        if grass is not None
        else "Unavailable",
>>>>>>> 49c23a2 (for Jonna and Mádá to work with)
    )

    weed_column.metric(
        "Weed pollen",
<<<<<<< HEAD
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
=======
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
>>>>>>> 49c23a2 (for Jonna and Mádá to work with)
    """

    st.subheader("Practical advice")

    exercise_column, sensitive_column = st.columns(2)

    with exercise_column:
        st.markdown("#### 🏃 Outdoor activity")
        st.write(recommendation["exercise"])

    with sensitive_column:
        st.markdown("#### 🫁 Sensitive groups")
        st.write(recommendation["sensitive"])


<<<<<<< HEAD
# --------------------------------------------------
# Explanations
# --------------------------------------------------

def show_explanations():
    """
    Explain technical terms.
=======
def show_explanations():
    """
    Explain technical measurements.
>>>>>>> 49c23a2 (for Jonna and Mádá to work with)
    """

    with st.expander("What do these measurements mean?"):
        st.markdown(
            """
<<<<<<< HEAD
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
=======
            **European AQI:** A combined air-quality index. Lower values
            represent cleaner air.

            **PM2.5:** Very small particles that can travel deeply into
            the lungs.

            **PM10:** Inhalable particles such as dust and road particles.

            **NO₂:** Nitrogen dioxide, a gas commonly associated with
            traffic and combustion.

            **Outdoor viability score:** Air Aware's simplified score based
            on air quality, weather and pollen when available.
>>>>>>> 49c23a2 (for Jonna and Mádá to work with)
            """
        )


<<<<<<< HEAD
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
=======
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

>>>>>>> 49c23a2 (for Jonna and Mádá to work with)

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
<<<<<<< HEAD
    pollen_data,
    using_sample_pollen,
):
    """
    Display the complete Air Aware summary.
=======
    pollen_data=None,
    pollen_source=None,
):
    """
    Display the complete Air Aware summary.

    app_jonnamada.py only needs to call this one function.
>>>>>>> 49c23a2 (for Jonna and Mádá to work with)
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

<<<<<<< HEAD
    show_pollen_details(
        pollen_data=pollen_data,
        using_sample_pollen=using_sample_pollen,
    )
=======
    show_pollen_details(pollen_data)
>>>>>>> 49c23a2 (for Jonna and Mádá to work with)

    show_practical_advice(recommendation)

    show_explanations()

    show_data_information(
<<<<<<< HEAD
        weather_source=weather_source,
        pollen_data=pollen_data,
        using_sample_pollen=using_sample_pollen,
    )
=======
        pollution_source="Open-Meteo",
        weather_source=weather_source,
        pollen_source=pollen_source,
        updated_at=None,
    )
>>>>>>> 49c23a2 (for Jonna and Mádá to work with)
