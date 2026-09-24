import time
from datetime import datetime

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st

# ============================================================
# AIR-AWARE SWEDEN — FRIENDLY REAL-TIME DASHBOARD
# ============================================================
st.set_page_config(
    page_title="Air-Aware Sweden",
    page_icon="🌬️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ------------------------------------------------------------
# Visual design
# ------------------------------------------------------------
st.markdown(
    """
    <style>
    .block-container {padding-top: 1.4rem; padding-bottom: 3rem;}
    .main-title {font-size:2.25rem;font-weight:800;letter-spacing:-0.02em;margin-bottom:.15rem;}
    .sub-title {font-size:1rem;color:#64748b;margin-bottom:1rem;}
    .hero {padding:18px 20px;border-radius:18px;border:1px solid rgba(100,116,139,.20);margin:8px 0 14px 0;}
    .hero-level {font-size:2rem;font-weight:850;margin:0;line-height:1.1;}
    .hero-action {font-size:1.02rem;font-weight:650;margin-top:6px;}
    .small-muted {color:#64748b;font-size:.86rem;}
    .chip {display:inline-block;border-radius:999px;padding:6px 10px;margin:3px 5px 3px 0;font-size:.80rem;font-weight:750;border:1px solid rgba(100,116,139,.20);}
    .metric-card {padding:13px 14px;border-radius:15px;border:1px solid rgba(100,116,139,.18);min-height:128px;background:rgba(248,250,252,.65);}
    .metric-name {font-weight:800;font-size:1rem;}
    .metric-value {font-weight:850;font-size:1.45rem;margin:4px 0 2px 0;}
    .metric-status {font-weight:750;font-size:.90rem;}
    .map-hint {padding:9px 12px;border-radius:12px;background:#f8fafc;border:1px solid #e2e8f0;font-size:.88rem;}
    div[data-testid="stMetricValue"] {font-size:1.65rem;}
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="main-title">🌬️ Air-Aware Sweden</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-title">Live air-quality information for everyday use — especially useful for people with asthma or sensitive airways.</div>',
    unsafe_allow_html=True,
)

# ------------------------------------------------------------
# Same Swedish locations as weatherpollutiontest-jacob.py
# ------------------------------------------------------------
REGIONS_AND_CITIES = {'Västra Götaland': {'Göteborg': (57.7089, 11.9746), 'Alingsås': (57.9303, 12.5335), 'Bengtsfors': (58.9974, 12.2324), 'Borås': (57.721, 12.9401), 'Falköping': (58.1735, 13.5507), 'Hjo': (58.3019, 14.2874), 'Kungälv': (57.87, 11.9675), 'Lidköping': (58.5052, 13.1577), 'Lilla Edet': (58.1333, 12.1333), 'Lysekil': (58.274, 11.435), 'Mariestad': (58.7097, 13.8237), 'Mölndal': (57.6554, 12.0138), 'Skara': (58.3866, 13.4384), 'Skövde': (58.3912, 13.8451), 'Strömstad': (58.9394, 11.1712), 'Tanumshede': (58.7236, 11.325), 'Tibro': (58.4245, 14.1612), 'Tidaholm': (58.1804, 13.9583), 'Trollhättan': (58.2837, 12.2886), 'Ulricehamn': (57.7916, 13.4142), 'Uddevalla': (58.3498, 11.9424), 'Vänersborg': (58.3807, 12.3234), 'Åmål': (58.9898, 12.639)}, 'Halland': {'Falkenberg': (56.9055, 12.4912), 'Halmstad': (56.6745, 12.8578), 'Kungsbacka': (57.4872, 12.0761), 'Laholm': (56.5126, 13.0437), 'Varberg': (57.1056, 12.2508)}, 'Skåne': {'Båstad': (56.4269, 12.8476), 'Eslöv': (55.8397, 13.3039), 'Helsingborg': (56.0465, 12.6945), 'Hässleholm': (56.1587, 13.7667), 'Höganäs': (56.1997, 12.5579), 'Kristianstad': (56.0294, 14.1567), 'Landskrona': (55.8708, 12.8302), 'Lund': (55.7047, 13.191), 'Malmö': (55.605, 13.0038), 'Simrishamn': (55.5565, 14.3539), 'Staffanstorp': (55.6428, 13.2064), 'Trelleborg': (55.3751, 13.1569), 'Ystad': (55.4297, 13.8204)}, 'Blekinge': {'Karlshamn': (56.1706, 14.8619), 'Karlskrona': (56.1612, 15.5869), 'Olofström': (56.2775, 14.533), 'Ronneby': (56.209, 15.276), 'Sölvesborg': (56.0521, 14.5751)}, 'Småland': {'Eksjö': (57.6664, 14.972), 'Gislaved': (57.3044, 13.5408), 'Jönköping': (57.7826, 14.1618), 'Ljungby': (56.8332, 13.9408), 'Nässjö': (57.6531, 14.6968), 'Tranås': (58.0372, 14.9784), 'Värnamo': (57.186, 14.04), 'Vetlanda': (57.4289, 15.0776), 'Växjö': (56.879, 14.8059)}, 'Kalmar län / Öland': {'Borgholm': (56.8793, 16.656), 'Emmaboda': (56.6328, 15.5374), 'Kalmar': (56.6634, 16.3568), 'Mönsterås': (57.0417, 16.443), 'Oskarshamn': (57.2646, 16.4484), 'Vimmerby': (57.6659, 15.8552), 'Västervik': (57.7584, 16.6373)}, 'Östergötland': {'Finspång': (58.7058, 15.7674), 'Linköping': (58.4108, 15.6214), 'Mjölby': (58.3259, 15.125), 'Motala': (58.5371, 15.0365), 'Norrköping': (58.5877, 16.1924), 'Söderköping': (58.4806, 16.3222), 'Vadstena': (58.4486, 14.8897)}, 'Södermanland': {'Eskilstuna': (59.371, 16.5098), 'Katrineholm': (58.9958, 16.2072), 'Nyköping': (58.753, 17.0079), 'Oxelösund': (58.6706, 17.1017), 'Strängnäs': (59.3774, 17.0312)}, 'Stockholm': {'Stockholm': (59.3293, 18.0686), 'Märsta': (59.6216, 17.8548), 'Norrtälje': (59.758, 18.705), 'Nynäshamn': (58.9034, 17.9479), 'Sollentuna': (59.428, 17.9509), 'Södertälje': (59.1955, 17.6253), 'Täby': (59.4439, 18.0687), 'Upplands Väsby': (59.5184, 17.9113), 'Vallentuna': (59.5344, 18.0776), 'Åkersberga': (59.4794, 18.2997)}, 'Uppsala län': {'Enköping': (59.6361, 17.0777), 'Uppsala': (59.8586, 17.6389), 'Östhammar': (60.2596, 18.3741)}, 'Västmanland': {'Arboga': (59.3939, 15.8388), 'Fagersta': (59.9913, 15.793), 'Köping': (59.514, 15.9926), 'Sala': (59.9199, 16.6066), 'Västerås': (59.6099, 16.5448)}, 'Örebro län': {'Hallsberg': (59.0642, 15.1103), 'Kumla': (59.1278, 15.1435), 'Lindesberg': (59.592, 15.2304), 'Nora': (59.5193, 15.0396), 'Örebro': (59.2753, 15.2134)}, 'Värmland': {'Arvika': (59.6553, 12.5852), 'Filipstad': (59.7124, 14.1683), 'Hagfors': (60.0234, 13.6721), 'Karlstad': (59.3793, 13.5036), 'Kristinehamn': (59.3098, 14.1081), 'Säffle': (59.1323, 12.9287)}, 'Dalarna': {'Avesta': (60.1454, 16.1679), 'Borlänge': (60.4858, 15.4371), 'Falun': (60.6065, 15.6355), 'Hedemora': (60.2797, 15.9886), 'Ludvika': (60.1496, 15.1878), 'Mora': (61.004, 14.537), 'Säter': (60.3478, 15.75), 'Älvdalen': (61.2277, 14.0393)}, 'Gävleborg': {'Bollnäs': (61.3482, 16.3946), 'Gävle': (60.6749, 17.1413), 'Hudiksvall': (61.7274, 17.1056), 'Ljusdal': (61.8288, 16.0918), 'Sandviken': (60.6186, 16.7758), 'Söderhamn': (61.3037, 17.0592)}, 'Jämtland': {'Åre': (63.3986, 13.0794), 'Östersund': (63.1792, 14.6353), 'Strömsund': (63.8521, 15.5558)}, 'Västernorrland': {'Härnösand': (62.6323, 17.9379), 'Kramfors': (62.9304, 17.7761), 'Sollefteå': (63.1667, 17.2667), 'Sundsvall': (62.3908, 17.3069), 'Örnsköldsvik': (63.2909, 18.7153)}, 'Västerbotten': {'Lycksele': (64.5954, 18.6735), 'Skellefteå': (64.7507, 20.9528), 'Storuman': (65.0959, 17.1173), 'Umeå': (63.8258, 20.263), 'Vilhelmina': (64.6242, 16.6558)}, 'Norrbotten': {'Arjeplog': (66.0517, 17.8861), 'Arvidsjaur': (65.5903, 19.1668), 'Boden': (65.8252, 21.6886), 'Haparanda': (65.8355, 24.1347), 'Jokkmokk': (66.6066, 19.8236), 'Kalix': (65.8556, 23.1465), 'Kiruna': (67.8558, 20.2253), 'Luleå': (65.5848, 22.1547), 'Piteå': (65.3172, 21.4794)}, 'Gotland': {'Visby': (57.6348, 18.2948)}}

OPEN_METEO_AIR_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"

# Calm, high-contrast palette — intentionally NOT traffic-light colors.
LEVELS = [
    (20, "Good", "Easy breathing", "Air is generally comfortable for most people", "#0F766E", "🌿"),
    (40, "Moderate", "Usually comfortable", "Most people are fine; sensitive airways may notice mild irritation", "#2563EB", "💧"),
    (60, "Poor", "Sensitive airways", "People with asthma may prefer lighter outdoor activity", "#7C3AED", "☁️"),
    (100, "Dangerous", "Breathing caution", "Asthma symptoms may be more likely; reduce strenuous outdoor activity", "#DB2777", "⚠️"),
    (float("inf"), "Hazardous", "High breathing risk", "Reduce outdoor exposure and follow local health guidance", "#7F1D5A", "🛡️"),
]

LEVEL_COLORS = {x[1]: x[4] for x in LEVELS}
LEVEL_COLORS["Unavailable"] = "#94A3B8"
LEVEL_ORDER = ["Good", "Moderate", "Poor", "Dangerous", "Hazardous"]

def normalize_level_label(label):
    """Keep public-facing terminology consistent across cards, charts and maps."""
    if label is None:
        return "Unavailable"
    label = str(label).strip()
    aliases = {
        "Normal": "Good",
        "Low": "Good",
        "Fair": "Moderate",
        "Very Poor": "Dangerous",
        "Extremely Poor": "Hazardous",
    }
    return aliases.get(label, label)

POLLUTANTS = {
    "PM2.5": {
        "value_key": "pm2_5", "aqi_key": "european_aqi_pm2_5", "unit": "µg/m³",
        "short": "Fine particles",
        "plain": "Tiny particles that can travel deep into the lungs.",
        "asthma": "Can irritate sensitive airways and may make breathing feel tighter when levels rise.",
        "sources": "Combustion, wood smoke, traffic, industry and secondary particles.",
    },
    "PM10": {
        "value_key": "pm10", "aqi_key": "european_aqi_pm10", "unit": "µg/m³",
        "short": "Coarse particles",
        "plain": "Airborne dust and particles larger than PM2.5.",
        "asthma": "Dust and coarse particles may trigger coughing or airway irritation in sensitive people.",
        "sources": "Road wear, dust, construction, soil and combustion.",
    },
    "NO₂": {
        "value_key": "nitrogen_dioxide", "aqi_key": "european_aqi_nitrogen_dioxide", "unit": "µg/m³",
        "short": "Combustion gas",
        "plain": "A gas that can irritate the airways.",
        "asthma": "Higher NO₂ can be uncomfortable for people with asthma, especially during outdoor activity.",
        "sources": "Road traffic, heating, industry and other fuel combustion.",
    },
    "O₃": {
        "value_key": "ozone", "aqi_key": "european_aqi_ozone", "unit": "µg/m³",
        "short": "Ground-level ozone",
        "plain": "Ozone near the ground can irritate the lungs.",
        "asthma": "Ozone can make deep breathing and exercise feel harder for sensitive airways.",
        "sources": "Forms in sunlight from reactions between other air pollutants.",
    },
    "SO₂": {
        "value_key": "sulphur_dioxide", "aqi_key": "european_aqi_sulphur_dioxide", "unit": "µg/m³",
        "short": "Sulfur dioxide",
        "plain": "A sulfur-containing gas that can irritate breathing.",
        "asthma": "People with asthma can be especially sensitive to sulfur dioxide during exposure.",
        "sources": "Some industry, shipping and sulfur-containing fuel combustion.",
    },
    "CO": {
        "value_key": "carbon_monoxide", "aqi_key": None, "unit": "µg/m³",
        "short": "Carbon monoxide",
        "plain": "A gas produced when fuels do not burn completely.",
        "asthma": "Carbon monoxide is not an asthma trigger in the same way as particles or ozone, but high exposure is harmful to everyone.",
        "sources": "Vehicle exhaust, heating, fires and incomplete combustion.",
    },
}


def level_info(aqi):
    if aqi is None:
        return {
            "level": "Unavailable", "feel": "No reading", "action": "Try again shortly",
            "color": LEVEL_COLORS["Unavailable"], "icon": "◌"
        }
    try:
        value = float(aqi)
    except (TypeError, ValueError):
        return {
            "level": "Unavailable", "feel": "No reading", "action": "Try again shortly",
            "color": LEVEL_COLORS["Unavailable"], "icon": "◌"
        }
    for ceiling, level, feel, action, color, icon in LEVELS:
        if value <= ceiling:
            return {"level": normalize_level_label(level), "feel": feel, "action": action, "color": color, "icon": icon}


CURRENT_FIELDS = [
    "european_aqi",
    "european_aqi_pm2_5", "european_aqi_pm10",
    "european_aqi_nitrogen_dioxide", "european_aqi_ozone",
    "european_aqi_sulphur_dioxide",
    "pm2_5", "pm10", "nitrogen_dioxide", "ozone",
    "sulphur_dioxide", "carbon_monoxide",
]

HOURLY_FIELDS = ["european_aqi", "pm2_5", "pm10", "nitrogen_dioxide", "ozone"]


@st.cache_data(ttl=60, show_spinner=False)
def fetch_city_air(lat: float, lon: float):
    """Fetch the latest provider value; cache only 60 s to avoid needless second-by-second API calls."""
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": CURRENT_FIELDS,
        "hourly": HOURLY_FIELDS,
        "timezone": "Europe/Stockholm",
        "forecast_days": 2,
        "domains": "cams_europe",
    }
    r = requests.get(OPEN_METEO_AIR_URL, params=params, timeout=10)
    r.raise_for_status()
    data = r.json()
    return data.get("current", {}), pd.DataFrame(data.get("hourly", {}))


@st.cache_data(ttl=300, show_spinner=False)
def fetch_region_air(region_name: str):
    """Fetch all cities in a region in one API request for color-coded map markers."""
    city_items = list(REGIONS_AND_CITIES[region_name].items())
    latitudes = ",".join(str(coords[0]) for _, coords in city_items)
    longitudes = ",".join(str(coords[1]) for _, coords in city_items)
    params = {
        "latitude": latitudes,
        "longitude": longitudes,
        "current": ["european_aqi"],
        "timezone": "Europe/Stockholm",
        "domains": "cams_europe",
    }
    try:
        r = requests.get(OPEN_METEO_AIR_URL, params=params, timeout=15)
        r.raise_for_status()
        payload = r.json()
        if isinstance(payload, dict):
            payload = [payload]
        rows = []
        for (city, coords), item in zip(city_items, payload):
            aqi = item.get("current", {}).get("european_aqi")
            meta = level_info(aqi)
            rows.append({
                "City": city, "latitude": coords[0], "longitude": coords[1],
                "Air Quality Index": aqi, "Level": normalize_level_label(meta["level"]),
                "Feel": meta["feel"], "Color": meta["color"],
            })
        return pd.DataFrame(rows)
    except Exception:
        return pd.DataFrame([
            {
                "City": city, "latitude": coords[0], "longitude": coords[1],
                "Air Quality Index": None, "Level": "Unavailable",
                "Feel": "No reading", "Color": LEVEL_COLORS["Unavailable"],
            }
            for city, coords in city_items
        ])


def safe_number(value, digits=1):
    return f"{value:.{digits}f}" if isinstance(value, (int, float)) else "—"


# ------------------------------------------------------------
# Session-state navigation: sidebar + clickable map
# ------------------------------------------------------------
if "selected_region" not in st.session_state:
    st.session_state.selected_region = "Västra Götaland"
if "selected_city" not in st.session_state:
    st.session_state.selected_city = "Göteborg"

# Apply a map click BEFORE creating the sidebar city widget.
pending = st.session_state.pop("_pending_city", None)
if pending and pending in REGIONS_AND_CITIES.get(st.session_state.selected_region, {}):
    # Safe here: this runs before the city selectbox is created.
    st.session_state.selected_city = pending
    st.session_state["city_widget"] = pending

st.sidebar.header("📍 Location")
regions = list(REGIONS_AND_CITIES.keys())
selected_region = st.sidebar.selectbox(
    "Region",
    regions,
    index=regions.index(st.session_state.selected_region) if st.session_state.selected_region in regions else 0,
    key="region_widget",
)

if selected_region != st.session_state.selected_region:
    st.session_state.selected_region = selected_region
    first_city = list(REGIONS_AND_CITIES[selected_region].keys())[0]
    st.session_state.selected_city = first_city
    st.session_state["city_widget"] = first_city
    st.rerun()

cities = list(REGIONS_AND_CITIES[selected_region].keys())
if st.session_state.selected_city not in cities:
    st.session_state.selected_city = cities[0]

city_index = cities.index(st.session_state.selected_city)
selected_city = st.sidebar.selectbox("City", cities, index=city_index, key="city_widget")
if selected_city != st.session_state.selected_city:
    st.session_state.selected_city = selected_city
    st.rerun()

selected_city = st.session_state.selected_city
lat, lon = REGIONS_AND_CITIES[selected_region][selected_city]

if st.sidebar.button("↻ Refresh source data", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

st.sidebar.caption(
    "The screen refreshes every second. Source values change only when Open-Meteo/CAMS publishes a new model value."
)

# ------------------------------------------------------------
# Friendly 5-level scale
# ------------------------------------------------------------
scale_html = ""
for _, level, feel, _, color, _ in LEVELS:
    scale_html += (
        f'<span class="chip" style="background:{color}18;color:{color};border-color:{color}55;">'
        f'{level} · {feel}</span>'
    )
st.markdown(scale_html, unsafe_allow_html=True)

# ------------------------------------------------------------
# Real-time panel — display updates every second.
# API calls stay cached for 60 seconds; source timestamp is shown.
# ------------------------------------------------------------
@st.fragment(run_every=1.0)
def live_panel():
    now = datetime.now().strftime("%H:%M:%S")
    try:
        current, hourly_df = fetch_city_air(lat, lon)
    except Exception as exc:
        st.error(f"Live air-quality data could not be loaded: {exc}")
        return

    overall_aqi = current.get("european_aqi")
    overall = level_info(overall_aqi)
    source_time = current.get("time", "Unknown")

    st.markdown(
        f"""
        <div class="hero" style="background:{overall['color']}12;border-left:8px solid {overall['color']};">
            <div class="hero-level" style="color:{overall['color']};">{overall['icon']} {overall['level']} · {overall['feel']}</div>
            <div class="hero-action">{overall['action']}</div>
            <div class="small-muted" style="margin-top:5px;"><b>Asthma view:</b> {overall['feel']}</div>
            <div style="margin-top:7px;"><b>Air Quality Index:</b> {safe_number(overall_aqi, 0)} &nbsp;·&nbsp; <b>{selected_city}</b></div>
            <div class="small-muted" style="margin-top:5px;">Screen clock: {now} · Source timestamp: {source_time}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.caption(
        "The clock updates every second. The Air Quality Index and pollutant values update only when new provider data are available."
    )

    # Compact pollutant cards
    st.subheader("Air pollution and health indicators")
    st.caption("Pollutant concentration levels. Technical units are explained in the glossary.")
    st.markdown(
        '<div class="map-hint"><b>For asthma & sensitive airways:</b> '
        'PM2.5, PM10, NO₂ and O₃ are especially useful to watch because they can be associated with airway irritation. '
        'Use the level labels together with how you feel and any advice from your healthcare professional.</div>',
        unsafe_allow_html=True,
    )
    card_names = ["PM2.5", "PM10", "NO₂", "O₃", "SO₂", "CO"]
    cols = st.columns(6)
    for col, name in zip(cols, card_names):
        info = POLLUTANTS[name]
        value = current.get(info["value_key"])
        paqi = current.get(info["aqi_key"]) if info["aqi_key"] else None
        pmeta = level_info(paqi) if info["aqi_key"] else {
            "level": "Measured", "color": "#64748B", "icon": "•"
        }
        value_text = f"{safe_number(value)}" if value is not None else "—"
        status_text = pmeta["level"] if info["aqi_key"] else "Concentration"
        col.markdown(
            f"""
            <div class="metric-card" style="border-top:5px solid {pmeta['color']};">
                <div class="metric-name"><b>{info['short']}</b></div>
                <div class="small-muted" style="margin-top:3px;">{name} · {value_text}</div>
                <div class="metric-status" style="color:{pmeta['color']};margin-top:8px;">{status_text}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        '<div class="small-muted" style="margin-top:8px;">'
        '<b>About the numbers:</b> they show how much of each pollutant is present in the air.'
        '</div>',
        unsafe_allow_html=True,
    )

    with st.expander("What does each indicator mean?", expanded=True):
        st.markdown(
            """
**Air Quality Index:** A simple overall score that tells you how clean or polluted the air is. A lower number means better air quality.

**PM2.5 — Fine particles:** Very small particles in the air. They can reach deep into the lungs and are especially important for people with asthma or sensitive airways.

**PM10 — Coarse particles:** Larger particles such as dust, pollen, road wear and construction particles. They can irritate the nose, throat and lungs.

**NO₂ — Nitrogen dioxide:** A gas mainly linked to traffic and fuel burning. Higher levels can irritate the lungs and may make asthma symptoms worse.

**O₃ — Ground-level ozone:** A gas that forms in sunlight when other pollutants react. It can make breathing feel harder, especially during exercise.

**SO₂ — Sulfur dioxide:** A gas linked to burning sulfur-containing fuels and some industrial activity. It can irritate the airways.

**CO — Carbon monoxide:** A gas produced when fuel does not burn completely. High levels reduce the amount of oxygen the blood can carry.

**Pollen:** Tiny particles released by plants. High pollen can trigger sneezing, itchy eyes, a runny nose and breathing irritation.

**Tree pollen:** Pollen mainly from trees. It is usually more important in late winter and spring.

**Grass pollen:** Pollen from grasses. It is usually more important from late spring through summer.

**Weed pollen:** Pollen from weeds. It is usually more important in late summer and early autumn.

**Good / Moderate / Poor / Dangerous / Hazardous:** These labels make the Air Quality Index easier to understand. They move from cleaner air to higher pollution and greater potential breathing risk.
            """
        )

    with st.expander("What do these pollutants mean? (Plain Language & Sources)", expanded=False):
        st.markdown(
            """
**PM2.5:** Tiny particles from traffic, smoke, cooking, fires, and industry. They can travel deep into the lungs and affect your health. **Lower is better**, with the WHO 24-hour guideline at **15 µg/m³**.

**PM10:** Larger airborne particles from road dust, construction, pollen, and industry. They can irritate your eyes, nose, throat, and lungs. **Lower is better**, with the WHO 24-hour guideline at **45 µg/m³**.

**NO₂:** A gas mainly produced by traffic, fuel burning, and industry. It can irritate your lungs and worsen respiratory problems. **Lower is better**, with the WHO 24-hour guideline at **25 µg/m³**.

**O₃:** A gas formed when pollutants react in sunlight, especially from traffic, industry, and other combustion sources. It can irritate your lungs and worsen breathing problems. **Lower is better**, with the WHO 8-hour guideline at **100 µg/m³**.

**SO₂:** A gas mainly produced by burning coal, oil, and other sulfur-containing fuels. It can irritate your airways and worsen respiratory conditions. **Lower is better**, with the WHO 24-hour guideline at **40 µg/m³**.

**CO:** A colorless, odorless gas produced mainly by incomplete combustion from vehicles, heating, cooking, and fires. It reduces the blood’s ability to carry oxygen and can affect the heart and brain. **Lower is better**, with the WHO 24-hour guideline at **4 mg/m³**.

**Pollen:** Tiny particles released by trees, grasses, and weeds. Pollen season is mainly active from **February to September**, with different plants peaking at different times. High levels can trigger sneezing, itchy eyes, and a runny nose. **Lower is better**, especially for people with pollen allergies.

**Tree pollen:** Tiny particles released by trees, mainly active from **February to May**. High levels can trigger sneezing, itchy eyes, and a runny nose. **Lower is better**, especially for people with pollen allergies.

**Grass pollen:** Tiny particles released by grasses, mainly active from **May to August**. High levels can trigger sneezing, itchy eyes, and breathing irritation. **Lower is better**, especially for people with pollen allergies.

**Weed pollen:** Tiny particles released by weeds, mainly active from **July to September**. High levels can trigger sneezing, itchy eyes, and a runny nose. **Lower is better**, especially for people with pollen allergies.
            """
        )

    # Pollutant-specific index graph
    chart_rows = []
    for name, info in POLLUTANTS.items():
        if not info["aqi_key"]:
            continue
        score = current.get(info["aqi_key"])
        if isinstance(score, (int, float)):
            meta = level_info(score)
            chart_rows.append({"Pollutant": name, "Air Quality Index": score, "Level": normalize_level_label(meta["level"])})

    if chart_rows:
        chart_df = pd.DataFrame(chart_rows).sort_values("Air Quality Index", ascending=True)
        fig = px.bar(
            chart_df,
            x="Air Quality Index",
            y="Pollutant",
            orientation="h",
            color="Level",
            text="Air Quality Index",
            color_discrete_map=LEVEL_COLORS,
            category_orders={"Level": LEVEL_ORDER},
            title="Air Quality Index by pollutant — PM2.5, PM10, NO₂, O₃ and SO₂",
        )
        fig.update_traces(texttemplate="%{text:.0f}", textposition="outside")
        fig.update_layout(
            height=335, margin=dict(l=10, r=20, t=48, b=10),
            xaxis_title="Air Quality Index score", yaxis_title="",
            legend_title_text="Level",
        )
        st.plotly_chart(fig, use_container_width=True, key="pollutant_bar")
        st.caption(
            "This chart includes PM2.5, PM10, NO₂, O₃ and SO₂ because they have pollutant-specific "
            "European Air Quality Index values. CO and pollen are shown separately and are not part "
            "of this Air Quality Index chart."
        )

    # 48-hour outlook
    if not hourly_df.empty and "time" in hourly_df.columns:
        with st.expander("48-hour outlook", expanded=False):
            choice = st.selectbox(
                "Show",
                ["european_aqi", "pm2_5", "pm10", "nitrogen_dioxide", "ozone"],
                format_func=lambda x: {
                    "european_aqi": "Air Quality Index",
                    "pm2_5": "PM2.5", "pm10": "PM10",
                    "nitrogen_dioxide": "NO₂", "ozone": "O₃",
                }[x],
                key="trend_choice",
            )
            trend = hourly_df[["time", choice]].dropna().copy()
            trend["time"] = pd.to_datetime(trend["time"], errors="coerce")
            y_label = "Air Quality Index" if choice == "european_aqi" else "µg/m³"
            trend_fig = px.line(trend, x="time", y=choice, markers=True)
            trend_fig.update_layout(
                height=300, margin=dict(l=10, r=10, t=15, b=10),
                xaxis_title="Time", yaxis_title=y_label, hovermode="x unified",
            )
            st.plotly_chart(trend_fig, use_container_width=True, key="trend_chart")


live_panel()

st.markdown("---")

# ------------------------------------------------------------
# Color-coded interactive regional map
# ------------------------------------------------------------
st.subheader("🗺️ Air quality around the region")
st.markdown(
    '<div class="map-hint">Click a city marker to open that city. Marker color shows its current Air Quality Index level.</div>',
    unsafe_allow_html=True,
)

region_df = fetch_region_air(selected_region)
if not region_df.empty:
    # Compact guide: same colors are used in cards, graph and map.
    guide_cols = st.columns(5)
    for col, (ceiling, level, feel, _, color, icon) in zip(guide_cols, LEVELS):
        range_text = (
            "0–20" if level == "Good" else
            "21–40" if level == "Moderate" else
            "41–60" if level == "Poor" else
            "61–100" if level == "Dangerous" else
            "101+"
        )
        col.markdown(
            f"""
            <div style="border:2px solid {color};border-radius:12px;padding:9px 10px;text-align:center;
                        background:{color}18;min-height:78px;">
                <div style="font-weight:850;color:{color};">{icon} {level}</div>
                <div style="font-size:.82rem;color:#334155;"><b>Air Quality Index {range_text}</b></div>
                <div style="font-size:.76rem;color:#64748b;">{feel}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Fixed marker size = no confusing numeric marker-size legend.
    map_fig = px.scatter_map(
        region_df,
        lat="latitude",
        lon="longitude",
        color="Level",
        hover_name="City",
        hover_data={
            "Air Quality Index": ":.0f",
            "Level": True,
            "Feel": True,
            "latitude": False,
            "longitude": False,
            "Color": False,
        },
        color_discrete_map=LEVEL_COLORS,
        category_orders={"Level": LEVEL_ORDER + ["Unavailable"]},
        zoom=6,
        center={"lat": lat, "lon": lon},
        map_style="carto-positron",
        custom_data=["City"],
    )

    map_fig.update_traces(marker={"size": 15, "opacity": 0.92})

    map_fig.update_layout(
        height=520,
        margin=dict(l=0, r=0, t=5, b=0),
        legend_title_text="Air quality level",
        clickmode="event+select",
        uirevision=f"map-{selected_region}",
    )

    st.caption(
        "Each dot is a city. Its color shows the current Air Quality Index level. "
        "Hover to see the city, Air Quality Index and level. Click a dot to open that city."
    )

    try:
        event = st.plotly_chart(
            map_fig,
            use_container_width=True,
            key="air_quality_map",
            on_select="rerun",
            selection_mode="points",
        )

        points = getattr(getattr(event, "selection", None), "points", []) if event is not None else []
        if points:
            point = points[0]
            customdata = point.get("customdata") if isinstance(point, dict) else None
            clicked_city = customdata[0] if customdata else None

            if clicked_city and clicked_city != selected_city:
                # Defer the widget-state update until the next run, before
                # the city selectbox is instantiated.
                st.session_state["_pending_city"] = clicked_city
                st.rerun()

    except TypeError:
        st.plotly_chart(map_fig, use_container_width=True, key="air_quality_map_fallback")
        st.caption("Upgrade Streamlit to enable direct city selection from map dots.")

    counts = region_df["Level"].value_counts().reindex(LEVEL_ORDER + ["Unavailable"], fill_value=0)
    st.markdown("#### Regional snapshot")
    summary_cols = st.columns(5)
    for col, (_, level, feel, _, color, icon) in zip(summary_cols, LEVELS):
        count = int(counts.get(level, 0))
        col.markdown(
            f"""
            <div style="border-left:5px solid {color};padding:7px 10px;border-radius:8px;background:{color}12;">
                <div style="font-size:.82rem;color:#475569;">{icon} {level}</div>
                <div style="font-size:1.35rem;font-weight:850;color:{color};">{count}</div>
                <div style="font-size:.74rem;color:#64748b;">cities</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

# ------------------------------------------------------------
# Glossary and conventions
# ------------------------------------------------------------
st.markdown("---")
with st.expander("📖 Simple dictionary", expanded=False):
    glossary = pd.DataFrame([
        ["Air Quality Index", "One score that turns several pollutant levels into an easier air-quality category."],
        ["PM2.5", "Very small airborne particles (2.5 micrometres or smaller)."],
        ["PM10", "Airborne particles 10 micrometres or smaller."],
        ["NO₂", "Nitrogen dioxide, a combustion-related gas."],
        ["O₃", "Ground-level ozone, formed in the atmosphere."],
        ["SO₂", "Sulfur dioxide, linked to sulfur-containing fuel and some industrial activity."],
        ["CO", "Carbon monoxide, produced by incomplete combustion."],
        ["Pollen", "Tiny airborne particles released by trees, grasses and weeds that can trigger allergy symptoms."],
        ["Tree pollen", "Pollen from trees, most common in late winter and spring."],
        ["Grass pollen", "Pollen from grasses, most common from late spring through summer."],
        ["Weed pollen", "Pollen from weeds, most common in late summer and early autumn."],
        ["µg/m³", "Technical unit used to measure how much of a pollutant is present in the air."],
        ["Sensitive airways", "Airways that react more easily to pollution, allergens or other irritants."],
        ["Asthma note", "A short reminder of how a pollutant may matter for people with asthma; it is not a diagnosis or medical instruction."],
        ["CAMS", "Copernicus Atmosphere Monitoring Service."],
    ], columns=["Term", "Plain-language meaning"])
    st.dataframe(glossary, hide_index=True, use_container_width=True)

with st.expander("ℹ️ How to read the air-quality levels", expanded=True):
    st.markdown(
        """
The dashboard uses five simple public-facing levels. The **Air Quality Index** is calculated from PM2.5, PM10, NO₂, O₃ and SO₂.  
Each pollutant has its own concentration range, shown below.

| Level | Air Quality Index | PM2.5 | PM10 | NO₂ | O₃ | SO₂ |
|---|---:|---:|---:|---:|---:|---:|
| **Good** | 0–20 | 0–5 | 0–15 | 0–10 | 0–60 | 0–20 |
| **Moderate** | 21–40 | >5–15 | >15–45 | >10–25 | >60–100 | >20–40 |
| **Poor** | 41–60 | >15–50 | >45–120 | >25–60 | >100–120 | >40–125 |
| **Dangerous** | 61–100 | >50–140 | >120–270 | >60–150 | >120–180 | >125–275 |
| **Hazardous** | Above 100 | >140 | >270 | >150 | >180 | >275 |

**Pollutant concentrations above are in µg/m³.**

**How to read it:**  
- The dashboard uses **Good**, not “Normal”, for the lowest-risk category.
- **Good:** Low pollution. Air is generally comfortable for most people.  
- **Moderate:** Pollution is still relatively low, but people with asthma or sensitive airways may want to pay attention to symptoms.  
- **Poor:** Pollution is elevated. Sensitive people may notice irritation or breathing discomfort.  
- **Dangerous:** High pollution. People with asthma or respiratory conditions should reduce strenuous outdoor activity.  
- **Hazardous:** Very high pollution. Reduce exposure and follow local health guidance.

**CO (carbon monoxide):** CO is measured by the app, but it is **not included in the European Air Quality Index calculation** used here. It is shown separately as a concentration indicator.

**Pollen:** Pollen is also **not part of the European Air Quality Index**. Tree, grass and weed pollen should be interpreted separately because pollen levels relate to allergy exposure rather than the pollution index.

**Important:** The European system officially has six bands. This dashboard combines them into five simpler categories for readability:  
- official **Good** → Good  
- official **Fair** → Moderate  
- official **Moderate** → Poor  
- official **Poor + Very Poor** → Dangerous  
- official **Extremely Poor** → Hazardous
        """
    )

st.caption(
    "Source: Open-Meteo Air Quality API using CAMS European data. Air-Aware is informational and does not replace official public-health alerts."
)
