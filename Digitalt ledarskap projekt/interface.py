import html
import streamlit as st

from recommendations import get_personalized_advice, get_status_config

CATEGORY_NAMES = {"air_quality": "Air quality & particles", "gases": "Gases", "pollen": "Pollen", "weather": "Weather conditions"}
GAS_NAMES = {"NO2": "Nitrogen dioxide (NO₂)", "O3": "Ozone (O₃)", "SO2": "Sulphur dioxide (SO₂)", "CO": "Carbon monoxide (CO)"}
POLLEN_NAMES = {"tree": "Tree pollen", "grass": "Grass pollen", "weed": "Weed pollen"}
WEATHER_NAMES = {"wind": "Wind speed & direction", "precipitation": "Precipitation", "humidity": "Humidity"}
MEASUREMENT_INFO = {
    "PM2.5": "Very small particles from smoke, traffic and combustion that can reach deep into the lungs.",
    "PM10": "Larger inhalable particles such as road dust, pollen fragments and construction dust.",
    "NO₂": "Nitrogen dioxide: a gas mainly linked to traffic and combustion.",
    "O₃": "Ground-level ozone: a gas that can irritate the lungs, especially during exercise.",
    "SO₂": "Sulphur dioxide: a gas produced by burning sulphur-containing fuels.",
    "CO": "Carbon monoxide: a colourless gas produced by incomplete combustion.",
    "Wind": "Stronger wind can make activity uncomfortable and can spread pollen, but may disperse traffic pollution.",
    "Precipitation": "Rain can affect comfort and often removes particles and pollen from the air.",
    "Humidity": "How much moisture is in the air. Very dry or hot, humid air can feel uncomfortable.",
}

def _empty_preferences():
    return {"selected_categories": [], "selected_gases": [], "selected_pollen_groups": [], "selected_pollen_types": None, "selected_weather": []}

def _initialize_preferences():
    if "air_aware_preferences" not in st.session_state:
        st.session_state.air_aware_preferences = _empty_preferences()
    if "air_aware_welcome_complete" not in st.session_state:
        st.session_state.air_aware_welcome_complete = False

@st.dialog("Welcome to Air Aware", width="large")
def _welcome_dialog():
    st.write("Choose what you want Air Aware to consider. You can skip this and change everything later in the sidebar.")
    categories = st.multiselect("What matters to you?", list(CATEGORY_NAMES), format_func=lambda x: CATEGORY_NAMES[x], key="welcome_categories")
    st.caption("No selection means Air Aware considers air quality, gases, pollen and weather.")
    left, right = st.columns(2)
    if left.button("Use these preferences", type="primary", use_container_width=True):
        prefs = _empty_preferences(); prefs["selected_categories"] = categories
        st.session_state.air_aware_preferences = prefs
        st.session_state.air_aware_welcome_complete = True
        st.session_state.show_personalized_dialog = True
        st.rerun()
    if right.button("Continue without choosing", use_container_width=True):
        st.session_state.air_aware_preferences = _empty_preferences()
        st.session_state.air_aware_welcome_complete = True
        st.rerun()

def show_welcome_if_needed():
    _initialize_preferences()
    if not st.session_state.air_aware_welcome_complete:
        _welcome_dialog()

def render_sidebar_preferences():
    _initialize_preferences(); saved = st.session_state.air_aware_preferences
    with st.sidebar:
        st.header("⚙️ Your preferences")
        st.caption("Empty selections mean: consider everything available.")
        with st.form("preferences_form"):
            categories = st.multiselect("Main categories", list(CATEGORY_NAMES), default=saved.get("selected_categories", []), format_func=lambda x: CATEGORY_NAMES[x])
            effective = categories or list(CATEGORY_NAMES)
            gases = st.multiselect("Gases", list(GAS_NAMES), default=saved.get("selected_gases", []), format_func=lambda x: GAS_NAMES[x]) if "gases" in effective else []
            pollen_groups = st.multiselect("Pollen allergies", list(POLLEN_NAMES), default=saved.get("selected_pollen_groups", []), format_func=lambda x: POLLEN_NAMES[x]) if "pollen" in effective else []
            pollen_text = st.text_input("Specific pollen types", value=", ".join(saved.get("selected_pollen_types") or []), placeholder="Björk, Gräs, Gråbo") if "pollen" in effective else ""
            weather = st.multiselect("Weather factors", list(WEATHER_NAMES), default=saved.get("selected_weather", []), format_func=lambda x: WEATHER_NAMES[x]) if "weather" in effective else []
            submitted = st.form_submit_button("Apply preferences", type="primary", use_container_width=True)
        if submitted:
            pollen_types = [x.strip() for x in pollen_text.split(",") if x.strip()] or None
            st.session_state.air_aware_preferences = {"selected_categories": categories, "selected_gases": gases, "selected_pollen_groups": pollen_groups, "selected_pollen_types": pollen_types, "selected_weather": weather}
            st.session_state.show_personalized_dialog = True
            st.rerun()
        if st.button("Show welcome choices again", use_container_width=True):
            st.session_state.air_aware_welcome_complete = False; st.rerun()
    return st.session_state.air_aware_preferences

def _status_card(title, severity, subtitle="", icon=None):
    config = get_status_config(severity); icon = icon or config["icon"]
    st.markdown(f"""<div style='border:1px solid #E2E8F0;border-top:7px solid {config['color']};border-radius:14px;padding:16px;background:white;min-height:150px'>
    <div style='font-size:1.6rem'>{icon}</div><div style='font-weight:700;color:#334155'>{html.escape(title)}</div>
    <div style='font-size:1.35rem;font-weight:800;color:{config['color']};margin:7px 0'>{html.escape(config['short_label'])}</div>
    <div style='font-size:.85rem;color:#64748B'>{html.escape(subtitle)}</div></div>""", unsafe_allow_html=True)

def render_overall_result(result, city=None, region=None):
    config = get_status_config(result.get("severity")); causes = result.get("causes", [])
    cause_text = ", ".join(causes) if causes else "Not enough available information"
    selected_detail = []
    for cause in causes:
        selected_detail.extend(result.get("groups", {}).get(cause, {}).get("causes", []))
    detail_text = ", ".join(selected_detail)
    reason = cause_text + (f" — {detail_text}" if detail_text else "")
    advice = get_personalized_advice(result)
    location = ", ".join(value for value in (city, region) if value)
    with st.container(border=True):
        st.markdown(
            f"<div style='height:7px;background:{config['color']};"
            "border-radius:8px;margin:-8px 0 14px 0'></div>",
            unsafe_allow_html=True,
        )
        st.markdown(f"**{html.escape(location)}**")
        st.markdown(
            f"<div style='font-size:2rem;font-weight:800;color:{config['color']}'>"
            f"{config['icon']} {html.escape(config['short_label'])}</div>",
            unsafe_allow_html=True,
        )
        st.write(config["message"])
        st.markdown(f"**Recommendation:** {advice}")

        with st.expander("Why am I seeing this result?", expanded=False):
            st.write(f"The main reason is: **{reason}**")
            selected_names = {
                "air_quality": "Air quality and particles",
                "gases": "Gases",
                "pollen": "Pollen",
                "weather": "Weather conditions",
            }
            selected = result.get("selected_categories", [])
            if selected:
                st.caption(
                    "Included in this result: "
                    + ", ".join(selected_names.get(item, item) for item in selected)
                )

def render_category_sections(result, air, weather, pollen_records):
    groups = result.get("groups", {})
    cards = st.columns(max(1, len(groups)))
    icons = {"Air quality": "🌫️", "Gases": "🏭", "Pollen": "🌿", "Weather": "🌦️"}
    raw_values = {"PM2.5": (air.get("pm2_5"), "µg/m³"), "PM10": (air.get("pm10"), "µg/m³"), "NO₂": (air.get("nitrogen_dioxide"), "µg/m³"), "O₃": (air.get("ozone"), "µg/m³"), "SO₂": (air.get("sulphur_dioxide"), "µg/m³"), "CO": (air.get("carbon_monoxide"), "µg/m³"), "Wind": (weather.get("wind_speed"), "m/s"), "Precipitation": (weather.get("precipitation"), "mm"), "Humidity": (weather.get("humidity"), "%")}
    for column, (name, group) in zip(cards, groups.items()):
        group_config = get_status_config(group.get("severity"))
        popover_label = (
            f"{icons.get(name, 'ℹ️')} {name} · "
            f"{group_config['short_label']}"
        )
        with column:
            with st.popover(popover_label, use_container_width=True):
                st.markdown(
                    f"### {group_config['icon']} {name}: "
                    f"{group_config['short_label']}"
                )
                st.caption(group_config["message"])

                if name == "Air quality":
                    st.caption("Overall pollution index summarises the strongest air-pollution concern. Lower is cleaner. It does not include pollen or weather.")
                    st.write(f"Overall pollution index: **{air.get('european_aqi', 'Unavailable')}**")

                for item, severity in group.get("items", {}).items():
                    config = get_status_config(severity)
                    raw, unit = raw_values.get(item, (None, ""))

                    if name == "Pollen":
                        match = next(
                            (
                                value
                                for value in pollen_records
                                if value.get("name") == item
                            ),
                            {},
                        )
                        raw_text = match.get("level", "Unavailable")
                    else:
                        raw_text = (
                            "Unavailable"
                            if raw is None
                            else f"{float(raw):.1f} {unit}".strip()
                        )

                    st.markdown(
                        f"**{config['icon']} {item}: "
                        f"<span style='color:{config['color']}'>"
                        f"{config['short_label']}</span>** · {raw_text}",
                        unsafe_allow_html=True,
                    )

                    if item in MEASUREMENT_INFO:
                        st.caption(MEASUREMENT_INFO[item])

                if name == "Weather":
                    st.caption(
                        f"Wind direction: {group.get('wind_direction', 'Unavailable')} · "
                        f"Humidity feels: {group.get('humidity_description', 'Unavailable')}"
                    )

@st.dialog("Your personalized outdoor conditions", width="large")
def _result_dialog(result):
    config = get_status_config(result.get("severity")); st.markdown(f"## {config['icon']} {config['short_label']}")
    st.write(get_personalized_advice(result)); st.caption(config["message"])

def show_result_dialog_if_requested(result):
    if st.session_state.get("show_personalized_dialog"):
        st.session_state.show_personalized_dialog = False
        _result_dialog(result)

def render_location_map(city, latitude, longitude, pollen_info):
    st.subheader("Location overview")
    points = [{"lat": latitude, "lon": longitude, "label": f"Selected location: {city}"}]
    if pollen_info.get("latitude") is not None and pollen_info.get("longitude") is not None:
        points.append({"lat": float(pollen_info["latitude"]), "lon": float(pollen_info["longitude"]), "label": f"Pollen region: {pollen_info.get('region', 'Unknown')}"})
    st.map(points, latitude="lat", longitude="lon", size=90, color="#0F6CBD")
    st.caption("This map shows data reference points. The available APIs do not identify street-level areas to avoid. For pollution, prefer routes away from major roads when the result advises caution.")
