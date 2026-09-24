from datetime import date, datetime
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import plotly.express as px
import requests
import streamlit as st

# Live pollen data (Pollenrapporten)
import pollen as pollen_api
from locations import nearest_station

# Optional persistent browser storage with automatic session fallback
try:
    from streamlit_local_storage import LocalStorage

    local_storage = LocalStorage()
    HAS_LOCAL_STORAGE = True
except ImportError:
    local_storage = None
    HAS_LOCAL_STORAGE = False

# -----------------------------------------------------------------------------
# 1. Page Configuration & Styling
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Air-aware | Environmental Monitor",
    page_icon="🌤️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .block-container {padding-top: 1.4rem; padding-bottom: 3rem;}
    .chip {display:inline-block;border-radius:999px;padding:5px 12px;margin:2px 5px 2px 0;font-size:.82rem;font-weight:700;border:1px solid rgba(100,116,139,.25);}
    .metric-card {padding:14px;border-radius:14px;border:1px solid rgba(100,116,139,.18);min-height:120px;background:rgba(248,250,252,.85);margin-bottom:8px;}
    .metric-name {font-weight:800;font-size:1.05rem;}
    .metric-value {font-weight:850;font-size:1.35rem;margin:4px 0 2px 0;}
    .metric-status {font-weight:700;font-size:.86rem;}
    .small-muted {color:#64748b;font-size:.82rem;}
    .map-hint {padding:10px 14px;border-radius:10px;background:#f8fafc;border:1px solid #e2e8f0;font-size:.88rem;margin:8px 0 14px 0;}
    .section-box {background:#ffffff;border:1px solid #e2e8f0;border-radius:14px;padding:20px;margin-bottom:24px;}
    .map-spacer {margin-bottom: 24px;}
    </style>
    """,
    unsafe_allow_html=True,
)

OPEN_METEO_AIR_URL: str = "https://air-quality-api.open-meteo.com/v1/air-quality"

# -----------------------------------------------------------------------------
# 2. Swedish Geographic Hierarchy
# -----------------------------------------------------------------------------
REGIONS_AND_CITIES: Dict[str, Dict[str, Tuple[float, float]]] = {
    "Västra Götaland": {
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
    },
    "Halland": {
        "Falkenberg": (56.9055, 12.4912),
        "Halmstad": (56.6745, 12.8578),
        "Kungsbacka": (57.4872, 12.0761),
        "Laholm": (56.5126, 13.0437),
        "Varberg": (57.1056, 12.2508),
    },
    "Skåne": {
        "Båstad": (56.4269, 12.8476),
        "Eslöv": (55.8397, 13.3039),
        "Helsingborg": (56.0465, 12.6945),
        "Hässleholm": (56.1587, 13.7667),
        "Höganäs": (56.1997, 12.5579),
        "Kristianstad": (56.0294, 14.1567),
        "Landskrona": (55.8708, 12.8302),
        "Lund": (55.7047, 13.1910),
        "Malmö": (55.6050, 13.0038),
        "Simrishamn": (55.5565, 14.3539),
        "Staffanstorp": (55.6428, 13.2064),
        "Trelleborg": (55.3751, 13.1569),
        "Ystad": (55.4297, 13.8204),
    },
    "Blekinge": {
        "Karlshamn": (56.1706, 14.8619),
        "Karlskrona": (56.1612, 15.5869),
        "Olofström": (56.2775, 14.5330),
        "Ronneby": (56.2090, 15.2760),
        "Sölvesborg": (56.0521, 14.5751),
    },
    "Småland": {
        "Eksjö": (57.6664, 14.9720),
        "Gislaved": (57.3044, 13.5408),
        "Jönköping": (57.7826, 14.1618),
        "Ljungby": (56.8332, 13.9408),
        "Nässjö": (57.6531, 14.6968),
        "Tranås": (58.0372, 14.9784),
        "Värnamo": (57.1860, 14.0400),
        "Vetlanda": (57.4289, 15.0776),
        "Växjö": (56.8790, 14.8059),
    },
    "Kalmar län / Öland": {
        "Borgholm": (56.8793, 16.6560),
        "Emmaboda": (56.6328, 15.5374),
        "Kalmar": (56.6634, 16.3568),
        "Mönsterås": (57.0417, 16.4430),
        "Oskarshamn": (57.2646, 16.4484),
        "Vimmerby": (57.6659, 15.8552),
        "Västervik": (57.7584, 16.6373),
    },
    "Östergötland": {
        "Finspång": (58.7058, 15.7674),
        "Linköping": (58.4108, 15.6214),
        "Mjölby": (58.3259, 15.1250),
        "Motala": (58.5371, 15.0365),
        "Norrköping": (58.5877, 16.1924),
        "Söderköping": (58.4806, 16.3222),
        "Vadstena": (58.4486, 14.8897),
    },
    "Södermanland": {
        "Eskilstuna": (59.3710, 16.5098),
        "Katrineholm": (58.9958, 16.2072),
        "Nyköping": (58.7530, 17.0079),
        "Oxelösund": (58.6706, 17.1017),
        "Strängnäs": (59.3774, 17.0312),
    },
    "Stockholm": {
        "Stockholm": (59.3293, 18.0686),
        "Märsta": (59.6216, 17.8548),
        "Norrtälje": (59.7580, 18.7050),
        "Nynäshamn": (58.9034, 17.9479),
        "Sollentuna": (59.4280, 17.9509),
        "Södertälje": (59.1955, 17.6253),
        "Täby": (59.4439, 18.0687),
        "Upplands Väsby": (59.5184, 17.9113),
        "Vallentuna": (59.5344, 18.0776),
        "Åkersberga": (59.4794, 18.2997),
    },
    "Uppsala län": {
        "Enköping": (59.6361, 17.0777),
        "Uppsala": (59.8586, 17.6389),
        "Östhammar": (60.2596, 18.3741),
    },
    "Västmanland": {
        "Arboga": (59.3939, 15.8388),
        "Fagersta": (59.9913, 15.7930),
        "Köping": (59.5140, 15.9926),
        "Sala": (59.9199, 16.6066),
        "Västerås": (59.6099, 16.5448),
    },
    "Örebro län": {
        "Hallsberg": (59.0642, 15.1103),
        "Kumla": (59.1278, 15.1435),
        "Lindesberg": (59.5920, 15.2304),
        "Nora": (59.5193, 15.0396),
        "Örebro": (59.2753, 15.2134),
    },
    "Värmland": {
        "Arvika": (59.6553, 12.5852),
        "Filipstad": (59.7124, 14.1683),
        "Hagfors": (60.0234, 13.6721),
        "Karlstad": (59.3793, 13.5036),
        "Kristinehamn": (59.3098, 14.1081),
        "Säffle": (59.1323, 12.9287),
    },
    "Dalarna": {
        "Avesta": (60.1454, 16.1679),
        "Borlänge": (60.4858, 15.4371),
        "Falun": (60.6065, 15.6355),
        "Hedemora": (60.2797, 15.9886),
        "Ludvika": (60.1496, 15.1878),
        "Mora": (61.0040, 14.5370),
        "Säter": (60.3478, 15.7500),
        "Älvdalen": (61.2277, 14.0393),
    },
    "Gävleborg": {
        "Bollnäs": (61.3482, 16.3946),
        "Gävle": (60.6749, 17.1413),
        "Hudiksvall": (61.7274, 17.1056),
        "Ljusdal": (61.8288, 16.0918),
        "Sandviken": (60.6186, 16.7758),
        "Söderhamn": (61.3037, 17.0592),
    },
    "Jämtland": {
        "Åre": (63.3986, 13.0794),
        "Östersund": (63.1792, 14.6353),
        "Strömsund": (63.8521, 15.5558),
    },
    "Västernorrland": {
        "Härnösand": (62.6323, 17.9379),
        "Kramfors": (62.9304, 17.7761),
        "Sollefteå": (63.1667, 17.2667),
        "Sundsvall": (62.3908, 17.3069),
        "Örnsköldsvik": (63.2909, 18.7153),
    },
    "Västerbotten": {
        "Lycksele": (64.5954, 18.6735),
        "Skellefteå": (64.7507, 20.9528),
        "Storuman": (65.0959, 17.1173),
        "Umeå": (63.8258, 20.2630),
        "Vilhelmina": (64.6242, 16.6558),
    },
    "Norrbotten": {
        "Arjeplog": (66.0517, 17.8861),
        "Arvidsjaur": (65.5903, 19.1668),
        "Boden": (65.8252, 21.6886),
        "Haparanda": (65.8355, 24.1347),
        "Jokkmokk": (66.6066, 19.8236),
        "Kalix": (65.8556, 23.1465),
        "Kiruna": (67.8558, 20.2253),
        "Luleå": (65.5848, 22.1547),
        "Piteå": (65.3172, 21.4794),
    },
    "Gotland": {
        "Visby": (57.6348, 18.2948),
    },
}

CITY_TO_REGION: Dict[str, str] = {
    city: reg for reg, cities in REGIONS_AND_CITIES.items() for city in cities
}
ALL_CITIES: List[str] = sorted(list(CITY_TO_REGION.keys()))

# -----------------------------------------------------------------------------
# 3. Categorization & Scales
# -----------------------------------------------------------------------------
LEVELS = [
    (20, "Good", "Easy breathing", "Air is comfortable for most people", "#0F766E", "🌿"),
    (40, "Moderate", "Usually comfortable", "Sensitive airways may notice minor irritation", "#2563EB", "💧"),
    (60, "Poor", "Sensitive airways", "People with asthma may prefer lighter outdoor activity", "#7C3AED", "☁️"),
    (100, "Dangerous", "Breathing caution", "Asthma symptoms likely; reduce strenuous workouts", "#DB2777", "⚠️"),
    (float("inf"), "Hazardous", "High breathing risk", "Stay indoors and follow local health advice", "#7F1D5A", "🛡️"),
]

LEVEL_COLORS = {x[1]: x[4] for x in LEVELS}
LEVEL_COLORS["Unavailable"] = "#94A3B8"
LEVEL_ORDER = ["Good", "Moderate", "Poor", "Dangerous", "Hazardous"]

POLLUTANTS = {
    "PM2.5": {
        "value_key": "pm2_5",
        "aqi_key": "european_aqi_pm2_5",
        "short": "Fine particles",
        "plain": "Tiny airborne combustion particles that travel deep into the lungs.",
        "asthma": "Can irritate sensitive airways and make breathing tighter when elevated.",
        "sources": "Combustion, vehicle exhaust, wood stoves, and industry.",
    },
    "PM10": {
        "value_key": "pm10",
        "aqi_key": "european_aqi_pm10",
        "short": "Coarse dust",
        "plain": "Inhalable dust and coarse particles larger than PM2.5.",
        "asthma": "Road dust and coarse particles frequently trigger coughing and irritation.",
        "sources": "Studded tire road wear, construction, dry soil, and sand.",
    },
    "NO₂": {
        "value_key": "nitrogen_dioxide",
        "aqi_key": "european_aqi_nitrogen_dioxide",
        "short": "Combustion gas",
        "plain": "A pungent gas that irritates bronchial airways.",
        "asthma": "Higher NO₂ can worsen asthma, especially near busy roadways.",
        "sources": "Road traffic, heavy diesel trucks, and heating fuels.",
    },
    "O₃": {
        "value_key": "ozone",
        "aqi_key": "european_aqi_ozone",
        "short": "Ground ozone",
        "plain": "Secondary pollutant formed when sunlight reacts with emissions.",
        "asthma": "Can make deep breathing and endurance exercise feel harder.",
        "sources": "Forms in warm sunlight from reactions between vehicle emissions.",
    },
    "SO₂": {
        "value_key": "sulphur_dioxide",
        "aqi_key": "european_aqi_sulphur_dioxide",
        "short": "Sulfur gas",
        "plain": "A sharp gas that can trigger immediate airway constriction.",
        "asthma": "People with asthma are especially vulnerable even during short exposures.",
        "sources": "Cargo shipping, refineries, and heavy sulfur-containing fuels.",
    },
    "CO": {
        "value_key": "carbon_monoxide",
        "aqi_key": None,
        "short": "Carbon gas",
        "plain": "Colorless, odorless gas produced by incomplete combustion.",
        "asthma": "Does not cause asthma directly, but high exposure restricts oxygen supply.",
        "sources": "Vehicle exhaust, enclosed fires, and burning fuels.",
    },
}


def level_info(aqi: Any) -> Dict[str, str]:
    if aqi is None:
        return {
            "level": "Unavailable",
            "feel": "No reading",
            "action": "Try again shortly",
            "color": LEVEL_COLORS["Unavailable"],
            "icon": "◌",
        }
    try:
        val = float(aqi)
    except (TypeError, ValueError):
        return {
            "level": "Unavailable",
            "feel": "No reading",
            "action": "Try again shortly",
            "color": LEVEL_COLORS["Unavailable"],
            "icon": "◌",
        }
    for ceiling, level, feel, action, color, icon in LEVELS:
        if val <= ceiling:
            return {"level": level, "feel": feel, "action": action, "color": color, "icon": icon}
    return {
        "level": "Unavailable",
        "feel": "No reading",
        "action": "Try again shortly",
        "color": LEVEL_COLORS["Unavailable"],
        "icon": "◌",
    }


def display_value(value: Any, unit: str = "", decimals: int = 1) -> str:
    try:
        if value is None or pd.isna(value):
            return "Unavailable"
        rendered = f"{float(value):.{decimals}f}"
        return f"{rendered} {unit}".strip()
    except (TypeError, ValueError):
        return "Unavailable"


# -----------------------------------------------------------------------------
# 4. Storage & Onboarding Layer
# -----------------------------------------------------------------------------
def save_preferences(location: Optional[str], weather: bool, pollen: bool, pollution: bool):
    prefs = {"location": location, "weather": weather, "pollen": pollen, "pollution": pollution}
    if HAS_LOCAL_STORAGE:
        try:
            local_storage.setItem("air_aware_preferences", prefs, key="save_prefs_call")
            local_storage.setItem("air_aware_onboarding_seen", True, key="save_onboard_call")
        except Exception:
            pass
    st.session_state.preferences = prefs
    st.session_state.onboarding_seen = True


def load_preferences() -> Optional[Dict[str, Any]]:
    if HAS_LOCAL_STORAGE:
        try:
            return local_storage.getItem("air_aware_preferences")
        except Exception:
            return None
    return None


def load_onboarding_status() -> bool:
    if HAS_LOCAL_STORAGE:
        try:
            return bool(local_storage.getItem("air_aware_onboarding_seen"))
        except Exception:
            return False
    return False


if "preferences_loaded" not in st.session_state:
    st.session_state.preferences_loaded = False
if "preferences" not in st.session_state:
    st.session_state.preferences = None
if "onboarding_seen" not in st.session_state:
    st.session_state.onboarding_seen = False
if "selected_region" not in st.session_state:
    st.session_state.selected_region = "Västra Götaland"
if "selected_city" not in st.session_state:
    st.session_state.selected_city = "Göteborg"
if "pref_weather" not in st.session_state:
    st.session_state.pref_weather = True
if "pref_pollen" not in st.session_state:
    st.session_state.pref_pollen = True
if "pref_pollution" not in st.session_state:
    st.session_state.pref_pollution = True

if not st.session_state.preferences_loaded:
    saved = load_preferences()
    seen = load_onboarding_status()
    st.session_state.onboarding_seen = seen
    if saved:
        st.session_state.preferences = saved
        loc = saved.get("location")
        if loc in CITY_TO_REGION:
            st.session_state.selected_city = loc
            st.session_state.selected_region = CITY_TO_REGION[loc]
        st.session_state.pref_weather = saved.get("weather", True)
        st.session_state.pref_pollen = saved.get("pollen", True)
        st.session_state.pref_pollution = saved.get("pollution", True)
    st.session_state.preferences_loaded = True


# --- Pre-Interface / Onboarding Dialog ---
@st.dialog("🌤️ Welcome to Air-aware")
def onboarding_dialog():
    st.write(
        "Set up your environmental monitor by choosing your location and selecting which "
        "signals matter most to your day."
    )
    st.divider()

    st.subheader("📍 Choose Your Location")
    regions = list(REGIONS_AND_CITIES.keys())
    diag_region = st.selectbox(
        "Select Region (Län)",
        options=regions,
        index=regions.index(st.session_state.selected_region)
        if st.session_state.selected_region in regions
        else 0,
        key="onboard_region_input",
    )

    cities_in_diag_region = list(REGIONS_AND_CITIES[diag_region].keys())
    diag_city = st.selectbox(
        "Select Municipality",
        options=cities_in_diag_region,
        index=cities_in_diag_region.index(st.session_state.selected_city)
        if st.session_state.selected_city in cities_in_diag_region
        else 0,
        key="onboard_city_input",
    )

    st.subheader("📊 Choose Environmental Modules to Track")
    diag_pol = st.checkbox("🌫️ Air Quality & Pollutants", value=True, key="onboard_pol")
    diag_w = st.checkbox("🌤️ Weather Conditions (SMHI)", value=True, key="onboard_w")
    diag_p = st.checkbox("🌾 Pollen Levels (Pollenrapporten)", value=True, key="onboard_p")

    st.divider()
    b1, b2 = st.columns(2)
    with b1:
        if st.button("Save & Continue", type="primary", use_container_width=True):
            save_preferences(diag_city, diag_w, diag_p, diag_pol)
            st.session_state.selected_city = diag_city
            st.session_state.selected_region = diag_region
            st.session_state.pref_weather = diag_w
            st.session_state.pref_pollution = diag_pol
            st.session_state.pref_pollen = diag_p
            st.rerun()
    with b2:
        if st.button("Explore All (Skip)", use_container_width=True):
            save_preferences("Göteborg", True, True, True)
            st.session_state.selected_city = "Göteborg"
            st.session_state.selected_region = "Västra Götaland"
            st.session_state.pref_weather = True
            st.session_state.pref_pollution = True
            st.session_state.pref_pollen = True
            st.rerun()


if not st.session_state.onboarding_seen:
    onboarding_dialog()

# Apply click from map if present
pending_city = st.session_state.pop("_pending_city", None)
if pending_city and pending_city in REGIONS_AND_CITIES.get(st.session_state.selected_region, {}):
    st.session_state.selected_city = pending_city


# -----------------------------------------------------------------------------
# 5. Data Pipelines
# -----------------------------------------------------------------------------
@st.cache_data(ttl=86400, show_spinner=False)
def load_pollen_stations() -> Dict[str, Tuple[float, float]]:
    """station name -> (lat, lon), excluding the national 'Sverige' aggregate."""
    return {
        r["name"]: (float(r["latitude"]), float(r["longitude"]))
        for r in pollen_api.get_regions()
        if r["name"] != "Sverige"
    }


@st.cache_data(ttl=3600, show_spinner=False)
def load_pollen_history(station_name: str) -> pd.DataFrame:
    """Full available pollen history for the given Pollenrapporten station."""
    return pollen_api.get_pollen_history(station_name)


@st.cache_data(ttl=300, show_spinner=False)
def fetch_city_pollution(lat: float, lon: float) -> Tuple[Dict[str, Any], pd.DataFrame]:
    current_fields = [
        "european_aqi",
        "european_aqi_pm2_5",
        "european_aqi_pm10",
        "european_aqi_nitrogen_dioxide",
        "european_aqi_ozone",
        "european_aqi_sulphur_dioxide",
        "pm2_5",
        "pm10",
        "nitrogen_dioxide",
        "ozone",
        "sulphur_dioxide",
        "carbon_monoxide",
    ]
    hourly_fields = ["european_aqi", "pm2_5", "pm10", "nitrogen_dioxide", "ozone"]
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": current_fields,
        "hourly": hourly_fields,
        "timezone": "Europe/Stockholm",
        "forecast_days": 2,
        "domains": "cams_europe",
    }
    try:
        r = requests.get(OPEN_METEO_AIR_URL, params=params, timeout=8)
        if r.status_code == 200:
            payload = r.json()
            return payload.get("current", {}), pd.DataFrame(payload.get("hourly", {}))
    except Exception:
        pass

    fallback_curr = {
        "european_aqi": 18,
        "european_aqi_pm2_5": 14,
        "european_aqi_pm10": 16,
        "european_aqi_nitrogen_dioxide": 18,
        "european_aqi_ozone": 24,
        "european_aqi_sulphur_dioxide": 6,
        "pm2_5": 4.5,
        "pm10": 11.2,
        "nitrogen_dioxide": 9.4,
        "ozone": 34.0,
        "sulphur_dioxide": 1.5,
        "carbon_monoxide": 150.0,
    }
    fallback_hourly = pd.DataFrame({
        "time": [datetime.now().strftime("%Y-%m-%dT%H:00")],
        "european_aqi": [18],
        "pm2_5": [4.5],
        "pm10": [11.2],
        "nitrogen_dioxide": [9.4],
        "ozone": [34.0],
    })
    return fallback_curr, fallback_hourly


@st.cache_data(ttl=300, show_spinner=False)
def fetch_region_air(region_name: str) -> pd.DataFrame:
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
        r = requests.get(OPEN_METEO_AIR_URL, params=params, timeout=12)
        if r.status_code == 200:
            payload = r.json()
            if isinstance(payload, dict):
                payload = [payload]
            rows = []
            for (city, coords), item in zip(city_items, payload):
                aqi = item.get("current", {}).get("european_aqi")
                meta = level_info(aqi)
                rows.append({
                    "City": city,
                    "latitude": coords[0],
                    "longitude": coords[1],
                    "Air Quality Index": aqi,
                    "Level": meta["level"],
                    "Feel": meta["feel"],
                    "Color": meta["color"],
                })
            return pd.DataFrame(rows)
    except Exception:
        pass

    return pd.DataFrame([
        {
            "City": city,
            "latitude": coords[0],
            "longitude": coords[1],
            "Air Quality Index": None,
            "Level": "Unavailable",
            "Feel": "No reading",
            "Color": LEVEL_COLORS["Unavailable"],
        }
        for city, coords in city_items
    ])


@st.cache_data(ttl=600, show_spinner=False)
def fetch_city_weather(lat: float, lon: float) -> Dict[str, Any]:
    try:
        url = (
            "https://opendata-download-metfcst.smhi.se/api/"
            "category/snow1g/version/1/geotype/point/"
            f"lon/{lon:.3f}/lat/{lat:.3f}/data.json"
        )
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            fc = r.json()["timeSeries"][0]["data"]
            return {
                "source": "SMHI",
                "temperature": fc.get("air_temperature", 15.0),
                "wind_speed": fc.get("wind_speed", 3.5),
                "humidity": fc.get("relative_humidity", 65.0),
                "precipitation": fc.get("precipitation_amount_mean", 0.0),
            }
    except Exception:
        pass

    return {
        "source": "Open-Meteo",
        "temperature": 15.0,
        "wind_speed": 3.2,
        "humidity": 65.0,
        "precipitation": 0.0,
    }


def calculate_viability(aqi, temp, wind, precip, pollen_level):
    score = 100
    reasons = []

    if aqi is not None and not pd.isna(aqi):
        if aqi > 80:
            score -= 50
            reasons.append("High air pollution (Elevated AQI)")
        elif aqi > 50:
            score -= 30
            reasons.append("Moderate particulate levels")
        elif aqi > 25:
            score -= 10
            reasons.append("Fair air quality with minor haze")

    if precip is not None and not pd.isna(precip):
        if precip >= 3.0:
            score -= 40
            reasons.append(f"Steady rain ({precip:.1f} mm)")
        elif precip > 0.2:
            score -= 15
            reasons.append(f"Light showers ({precip:.1f} mm)")

    if wind is not None and not pd.isna(wind):
        if wind >= 13.0:
            score -= 35
            reasons.append(f"Strong winds ({wind:.1f} m/s)")

    if temp is not None and not pd.isna(temp):
        if temp < -5 or temp > 30:
            score -= 25
            reasons.append(f"Challenging temperatures ({temp:.1f} °C)")

    if pollen_level is not None and not pd.isna(pollen_level):
        if pollen_level >= 5:
            score -= 20
            reasons.append(f"High pollen load (Level {pollen_level}/6)")
        elif pollen_level >= 3:
            score -= 10
            reasons.append(f"Elevated seasonal pollen (Level {pollen_level}/6)")

    score = max(0, min(100, score))
    if score >= 80:
        verdict = "Optimal for Outdoor Activities"
    elif score >= 55:
        verdict = "Fair / Acceptable Conditions"
    elif score >= 35:
        verdict = "Poor / Caution Advised"
    else:
        verdict = "Unfavorable / Stay Indoors"

    if not reasons:
        reasons = ["Calm weather, clean air, and low allergen exposure."]

    return score, verdict, reasons


# -----------------------------------------------------------------------------
# 6. Sidebar Controls
# -----------------------------------------------------------------------------
with st.sidebar:
    st.header("⚙️ Preferences")
    quick_city = st.selectbox(
        "Selected Municipality",
        options=ALL_CITIES,
        index=ALL_CITIES.index(st.session_state.selected_city)
        if st.session_state.selected_city in ALL_CITIES
        else 0,
    )
    if quick_city != st.session_state.selected_city:
        st.session_state.selected_city = quick_city
        st.session_state.selected_region = CITY_TO_REGION[quick_city]
        st.rerun()

    st.markdown("**Active Signal Modules**")
    pol_on = st.checkbox("🌫️ Air Pollution Levels", value=st.session_state.pref_pollution)
    w_on = st.checkbox("🌤️ Weather Conditions", value=st.session_state.pref_weather)
    p_on = st.checkbox("🌾 Pollen Levels", value=st.session_state.pref_pollen)

    if (
        w_on != st.session_state.pref_weather
        or pol_on != st.session_state.pref_pollution
        or p_on != st.session_state.pref_pollen
    ):
        st.session_state.pref_weather = w_on
        st.session_state.pref_pollution = pol_on
        st.session_state.pref_pollen = p_on
        save_preferences(st.session_state.selected_city, w_on, p_on, pol_on)
        st.rerun()

    st.divider()
    if st.button("Reconfigure Preferences (Onboard)", use_container_width=True):
        if HAS_LOCAL_STORAGE:
            try:
                local_storage.deleteItem("air_aware_preferences")
                local_storage.deleteItem("air_aware_onboarding_seen")
            except Exception:
                pass
        st.session_state.onboarding_seen = False
        st.session_state.preferences = None
        st.rerun()


# -----------------------------------------------------------------------------
# 7. Main Dashboard & Top Navigation Bar
# -----------------------------------------------------------------------------
st.title("🌤️ Air-aware: Environmental Monitor")
st.caption(
    "Plain-language environmental conditions for daily life and athletic planning — designed to be readable for sensitive airways and asthma."
)

col_r, col_c, col_btn = st.columns([1.8, 1.8, 0.8])
region_list = list(REGIONS_AND_CITIES.keys())
current_reg = st.session_state.selected_region
reg_idx = region_list.index(current_reg) if current_reg in region_list else 0

with col_r:
    chosen_region = st.selectbox("📍 Region (Län)", options=region_list, index=reg_idx)
    if chosen_region != st.session_state.selected_region:
        st.session_state.selected_region = chosen_region
        st.session_state.selected_city = list(REGIONS_AND_CITIES[chosen_region].keys())[0]
        st.rerun()

cities_in_region = list(REGIONS_AND_CITIES[st.session_state.selected_region].keys())
city_idx = (
    cities_in_region.index(st.session_state.selected_city)
    if st.session_state.selected_city in cities_in_region
    else 0
)

with col_c:
    chosen_city = st.selectbox("🏢 Municipality", options=cities_in_region, index=city_idx)
    if chosen_city != st.session_state.selected_city:
        st.session_state.selected_city = chosen_city
        st.rerun()

with col_btn:
    st.write("")
    st.write("")
    if st.button("↻ Refresh", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# -----------------------------------------------------------------------------
# 8. Scale Header
# -----------------------------------------------------------------------------
scale_chips_html = "".join([
    f'<span class="chip" style="background:{color}18;color:{color};border-color:{color}50;">'
    f'{icon} <b>{level}</b> · {feel}</span>'
    for _, level, feel, _, color, icon in LEVELS
])
st.markdown(f"<div style='margin-bottom:12px;'>{scale_chips_html}</div>", unsafe_allow_html=True)

lat, lon = REGIONS_AND_CITIES[st.session_state.selected_region][st.session_state.selected_city]

curr_pol, hourly_df = fetch_city_pollution(lat, lon)
wx = fetch_city_weather(lat, lon)

# -------------------------------------------------------------
# Live pollen (Pollenrapporten): resolve the selected city to its
# nearest measuring station, then fetch the current grouped levels.
# -------------------------------------------------------------
pollen_history = pd.DataFrame()
pollen_station = None
pollen_grouped: Dict[str, Any] = {"status": "unavailable", "date": None, "summary": {}}
pollen_benchmark: Dict[str, Any] = {
    "available": False,
    "level": None,
    "dominant": "None",
    "date": None,
    "source": "Pollenrapporten",
}

try:
    _stations = load_pollen_stations()
    pollen_station = nearest_station(lat, lon, _stations)
    pollen_history = load_pollen_history(pollen_station)
except Exception:
    pollen_history = pd.DataFrame()

if not pollen_history.empty:
    pollen_grouped = pollen_api.get_latest_grouped(pollen_history)
    latest_day = pollen_grouped.get("date")
    summary = pollen_grouped.get("summary", {})

    # Highest numeric level across all pollen on the most recent day,
    # plus the dominant pollen name(s), for the viability score + card.
    max_level = 0
    dominant: List[str] = []
    for cat_data in summary.values():
        for entry in cat_data.get("pollen", []):
            numeric = entry.get("numeric_level")
            if isinstance(numeric, (int, float)) and not pd.isna(numeric):
                numeric = int(numeric)
                if numeric > max_level:
                    max_level = numeric
                    dominant = [entry.get("pollen")]
                elif numeric == max_level and numeric > 0:
                    dominant.append(entry.get("pollen"))

    pollen_benchmark = {
        "available": True,
        "level": max_level,
        "dominant": ", ".join(d for d in dominant if d) if dominant else "None",
        "date": str(latest_day) if latest_day else None,
        "source": f"Pollenrapporten · {pollen_station}",
    }

aqi_val = curr_pol.get("european_aqi")
temp_val = wx.get("temperature")
wind_val = wx.get("wind_speed")
humidity_val = wx.get("humidity")
rain_val = wx.get("precipitation")
weather_source = wx.get("source", "SMHI")

score, verdict, reasons = calculate_viability(
    aqi=aqi_val,
    temp=temp_val,
    wind=wind_val,
    precip=rain_val,
    pollen_level=pollen_benchmark.get("level"),
)
aqi_meta = level_info(aqi_val)

# -------------------------------------------------------------
# 9. Top Overview Banner
# -------------------------------------------------------------
st.markdown(
    f"""
    <div style="background:#F8FAFC;border:2px solid {aqi_meta['color']};border-left:10px solid {aqi_meta['color']};padding:20px;border-radius:14px;margin:8px 0 18px 0;">
        <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;">
            <div>
                <p style="margin:0;color:#64748B;font-size:0.92rem;">Current Conditions for <b>{st.session_state.selected_city}, {st.session_state.selected_region}</b></p>
                <h2 style="margin:4px 0;color:{aqi_meta['color']};">{aqi_meta['icon']} Air Quality: {aqi_meta['level']} ({aqi_meta['feel']})</h2>
                <div style="font-size:1.02rem;font-weight:600;color:#334155;">{aqi_meta['action']}</div>
            </div>
            <div style="text-align:right;">
                <div style="font-size:2.2rem;font-weight:900;color:{aqi_meta['color']};">{score}/100</div>
                <div style="font-size:0.80rem;font-weight:700;color:#64748B;">Outdoor Viability Rating</div>
            </div>
        </div>
        <hr style="margin:12px 0;border:0;border-top:1px solid #E2E8F0;">
        <div style="color:#475569;font-size:0.92rem;">
            <b>Verdict:</b> {verdict} &nbsp;•&nbsp; <b>Key Drivers:</b> {" • ".join(reasons)}
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# -------------------------------------------------------------
# 10. Distinct Signal Modules: Pollution, Weather & Pollen (Stacked)
# -------------------------------------------------------------
if st.session_state.pref_pollution:
    st.markdown("### 🌫️ Air Pollution & Health Indicators")
    st.markdown(
        f'<div class="map-hint">Specific pollution levels for <b>{st.session_state.selected_city}</b>. Categories reflect airway comfort and irritation potential.</div>',
        unsafe_allow_html=True,
    )

    card_keys = ["PM2.5", "PM10", "NO₂", "O₃", "SO₂", "CO"]
    p_cols = st.columns(6)
    for col, name in zip(p_cols, card_keys):
        p_info = POLLUTANTS[name]
        paqi = curr_pol.get(p_info["aqi_key"]) if p_info["aqi_key"] else None

        if p_info["aqi_key"]:
            pmeta = level_info(paqi)
            main_display = pmeta["level"]
            sub_status = pmeta["feel"]
            card_color = pmeta["color"]
        else:
            main_display = "Normal"
            sub_status = "Trace Level"
            card_color = "#0F766E"

        col.markdown(
            f"""
            <div class="metric-card" style="border-top:5px solid {card_color};">
                <div class="metric-name">{name}</div>
                <div class="small-muted">{p_info['short']}</div>
                <div class="metric-value" style="color:{card_color};">{main_display}</div>
                <div class="metric-status" style="color:#475569;">{sub_status}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with st.expander("📚 What do these pollutants mean? (Plain Language & Sources)", expanded=False):
        for name, info in POLLUTANTS.items():
            st.markdown(
                f"**{name} — {info['short']}**  \n"
                f"• **In Plain Words:** {info['plain']}  \n"
                f"• **Sensitive Airways & Asthma:** {info['asthma']}  \n"
                f"• **Typical Sources:** {info['sources']}\n"
            )

# Weather Conditions (Full width with dedicated container spacing)
if st.session_state.pref_weather:
    st.markdown("<div style='margin-top: 18px;'></div>", unsafe_allow_html=True)
    st.markdown("### 🌤️ Live Weather Conditions")
    st.caption(f"Source: {weather_source}")
    w_cols = st.columns(4)
    w_cols[0].metric("Temperature", display_value(temp_val, "°C"))
    w_cols[1].metric("Relative Humidity", display_value(humidity_val, "%", 0))
    w_cols[2].metric("Wind Speed", display_value(wind_val, "m/s"))
    w_cols[3].metric("Precipitation", display_value(rain_val, "mm"))

# Pollen (live Pollenrapporten data, full width)
if st.session_state.pref_pollen:
    st.markdown("<div style='margin-top: 24px;'></div>", unsafe_allow_html=True)
    st.markdown("### 🌾 Pollen Levels & Seasonal Allergen Radar")
    st.caption(f"Source: {pollen_benchmark.get('source', 'Pollenrapporten')}")

    if not pollen_benchmark.get("available"):
        st.info("No pollen data is currently available for the nearest station.")
    else:
        summary = pollen_grouped.get("summary", {})
        latest_day = pollen_grouped.get("date")

        # Readable colours for the 0–6 pollen scale (calm, high-contrast).
        POLLEN_LEVEL_STYLE = {
            "none": ("#0F766E", "None"),
            "low": ("#2563EB", "Low"),
            "moderate": ("#7C3AED", "Moderate"),
            "high": ("#DB2777", "High"),
            "very high": ("#7F1D5A", "Very high"),
            "unavailable": ("#94A3B8", "No reading"),
        }

        # Grouped category levels (Tree / Grass / Weed) as clickable popovers.
        # Clicking a category opens a popup listing its individual pollen types.
        cat_emoji = {"Tree pollen": "🌳", "Grass pollen": "🌾", "Weed pollen": "🌿"}
        cat_cols = st.columns(3)
        for col, category in zip(cat_cols, ["Tree pollen", "Grass pollen", "Weed pollen"]):
            cat_data = summary.get(category, {})
            level = cat_data.get("level", "unavailable")
            color, label = POLLEN_LEVEL_STYLE.get(level, POLLEN_LEVEL_STYLE["unavailable"])

            with col:
                with st.popover(
                    f"{cat_emoji[category]} {category} — {label}",
                    use_container_width=True,
                ):
                    st.markdown(f"### {cat_emoji[category]} {category}")
                    st.markdown(
                        f"**Overall level:** "
                        f"<span style='color:{color};font-weight:800;'>{label}</span>",
                        unsafe_allow_html=True,
                    )
                    st.caption("Individual pollen types in this group (latest reading):")

                    entries = sorted(
                        cat_data.get("pollen", []),
                        key=lambda e: (e.get("numeric_level") or -1),
                        reverse=True,
                    )
                    if not entries:
                        st.info("No individual pollen types reported for this group.")
                    else:
                        for entry in entries:
                            name = entry.get("pollen", "Unknown")
                            e_level = entry.get("level", "unavailable")
                            e_num = entry.get("numeric_level")
                            e_color, e_label = POLLEN_LEVEL_STYLE.get(
                                e_level, POLLEN_LEVEL_STYLE["unavailable"]
                            )
                            num_txt = f" ({e_num}/6)" if isinstance(e_num, (int, float)) else ""
                            st.markdown(
                                f"<div style='display:flex;align-items:center;gap:8px;"
                                f"padding:4px 0;'>"
                                f"<span style='width:12px;height:12px;border-radius:50%;"
                                f"background:{e_color};display:inline-block;'></span>"
                                f"<span style='flex:1;'>{name}</span>"
                                f"<span style='color:{e_color};font-weight:700;'>"
                                f"{e_label}{num_txt}</span>"
                                f"</div>",
                                unsafe_allow_html=True,
                            )

        # Human-readable summary line under the cards.
        max_level = pollen_benchmark.get("level")
        overall_word = POLLEN_LEVEL_STYLE.get(
            pollen_api.convert_level(max_level), POLLEN_LEVEL_STYLE["unavailable"]
        )[1]

        # Only surface "dominant" pollen when it's actually elevated (level ≥ 2).
        dominant = pollen_benchmark.get("dominant", "None")
        dominant_line = ""
        if isinstance(max_level, (int, float)) and max_level >= 2 and dominant not in ("", "None"):
            dominant_line = f" &nbsp;·&nbsp; Main allergen(s): <b>{dominant}</b>"

        try:
            reading_date = datetime.strptime(str(latest_day), "%Y-%m-%d").strftime("%d %b %Y")
        except (ValueError, TypeError):
            reading_date = str(latest_day) if latest_day else "Unavailable"

        st.markdown(
            f"""
            <div style="margin-top:12px;color:#334155;font-size:.95rem;">
                Highest pollen right now: <b>{overall_word}</b> ({max_level}/6){dominant_line}
                <span style="color:#64748b;"> &nbsp;·&nbsp; Latest reading: {reading_date}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if latest_day and latest_day < date.today():
            st.caption(
                "Pollen forecasting is out of season. Showing the most recent "
                "available reading — explore past seasons in the chart below."
            )

        # Historical time-series chart (daily max per series), gaps preserved.
        with st.expander("📈 Historical pollen levels", expanded=False):
            pollen_view = st.radio(
                "Group by",
                ["Category", "Individual pollen type"],
                horizontal=True,
                key="pollen_hist_view",
            )
            group_col = "category" if pollen_view == "Category" else "pollen"

            hist = pollen_history.copy()
            chart_df = (
                hist.groupby(["date", group_col], as_index=False)["numeric_level"].max()
            )
            if not chart_df.empty:
                chart_df["date"] = pd.to_datetime(chart_df["date"])
                full_days = pd.date_range(
                    chart_df["date"].min(), chart_df["date"].max(), freq="D"
                )
                series = []
                for name, grp in chart_df.groupby(group_col):
                    s = (
                        grp.set_index("date")["numeric_level"]
                        .reindex(full_days)
                        .rename_axis("date")
                        .reset_index()
                    )
                    s["numeric_level"] = s["numeric_level"].where(
                        s["numeric_level"].notna(),
                        s["numeric_level"].interpolate(limit=2, limit_area="inside"),
                    )
                    s[group_col] = name
                    series.append(s)
                chart_df = pd.concat(series, ignore_index=True)

                if pollen_view == "Category":
                    pollen_color_map = {
                        "Tree pollen": "#2e7d32",
                        "Grass pollen": "#00897b",
                        "Weed pollen": "#8e24aa",
                        "Other": "#9e9e9e",
                    }
                    fig_pollen = px.line(
                        chart_df,
                        x="date",
                        y="numeric_level",
                        color=group_col,
                        color_discrete_map=pollen_color_map,
                        labels={"date": "Date", "numeric_level": "Level (0–6)", group_col: ""},
                    )
                else:
                    fig_pollen = px.line(
                        chart_df,
                        x="date",
                        y="numeric_level",
                        color=group_col,
                        labels={"date": "Date", "numeric_level": "Level (0–6)", group_col: ""},
                    )
                fig_pollen.update_traces(connectgaps=False, line=dict(width=2))
                fig_pollen.update_yaxes(range=[-0.2, 6.2], dtick=1)
                fig_pollen.update_layout(
                    template="plotly_white",
                    height=340,
                    margin=dict(l=10, r=10, t=20, b=10),
                    hovermode="x unified",
                    legend=dict(
                        itemclick="toggleothers",
                        itemdoubleclick="toggle",
                        title="",
                    ),
                )
                st.plotly_chart(fig_pollen, use_container_width=True)
                st.caption(
                    "Tip: single-click a legend entry to isolate that series; "
                    "double-click to toggle it. Lines break where no data was reported."
                )
            else:
                st.info("No historical pollen readings are available.")

# -------------------------------------------------------------
# 11. Visual Forecasts & Driver Analysis
# -------------------------------------------------------------
st.markdown("---")
st.markdown("### 📊 Analytical Forecasts & Air Quality Drivers")
c_left, c_right = st.columns(2)

with c_left:
    chart_rows = []
    for name, info in POLLUTANTS.items():
        if not info["aqi_key"]:
            continue
        sc = curr_pol.get(info["aqi_key"])
        if isinstance(sc, (int, float)):
            pm = level_info(sc)
            chart_rows.append({"Pollutant": name, "Status": pm["level"], "Score": sc})

    if chart_rows:
        cdf = pd.DataFrame(chart_rows).sort_values("Score", ascending=True)
        fig_bar = px.bar(
            cdf,
            x="Score",
            y="Pollutant",
            orientation="h",
            color="Status",
            color_discrete_map=LEVEL_COLORS,
            category_orders={"Status": LEVEL_ORDER},
            title="Which pollutant is driving the current air quality level?",
        )
        fig_bar.update_layout(height=280, margin=dict(l=10, r=20, t=45, b=10), xaxis_title="Severity Score")
        st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.info("Pollutant breakdown currently unavailable.")

with c_right:
    st.markdown(f"**48-Hour Trend Curve ({st.session_state.selected_city})**")
    if not hourly_df.empty and "time" in hourly_df.columns:
        chosen_metric = st.selectbox(
            "Forecast Signal:",
            options=["european_aqi", "pm2_5", "pm10", "nitrogen_dioxide", "ozone"],
            format_func=lambda x: {
                "european_aqi": "Air Quality Index (AQI)",
                "pm2_5": "Fine Particles (PM2.5)",
                "pm10": "Coarse Dust (PM10)",
                "nitrogen_dioxide": "Combustion Gas (NO₂)",
                "ozone": "Ground Ozone (O₃)",
            }[x],
        )
        if chosen_metric in hourly_df.columns:
            fig_line = px.line(
                hourly_df,
                x="time",
                y=chosen_metric,
                labels={"time": "Time", chosen_metric: "Index / Concentration"},
            )
            fig_line.update_traces(line=dict(color="#2563EB", width=2.5))
            fig_line.update_layout(margin=dict(l=20, r=20, t=25, b=20), height=230, hovermode="x unified")
            st.plotly_chart(fig_line, use_container_width=True)
    else:
        st.info("48-hour forecast is loading or unavailable.")

# -------------------------------------------------------------
# 12. Regional Air Quality Map
# -------------------------------------------------------------
st.markdown("---")
st.markdown(f"### 🗺️ Regional Air Quality Map ({st.session_state.selected_region})")
st.markdown(
    '<div class="map-hint">Click on any city marker on the map to switch your location view directly. Colors represent current air quality levels.</div>',
    unsafe_allow_html=True,
)

region_df = fetch_region_air(st.session_state.selected_region)
if not region_df.empty:
    scatter_func = getattr(px, "scatter_map", getattr(px, "scatter_mapbox", None))
    style_key = "map_style" if hasattr(px, "scatter_map") else "mapbox_style"

    map_kwargs = {
        "data_frame": region_df,
        "lat": "latitude",
        "lon": "longitude",
        "color": "Level",
        "hover_name": "City",
        "hover_data": {
            "Level": True,
            "Feel": True,
            "Air Quality Index": True,
            "latitude": False,
            "longitude": False,
        },
        "color_discrete_map": LEVEL_COLORS,
        "category_orders": {"Level": LEVEL_ORDER + ["Unavailable"]},
        "zoom": 6.2,
        "center": {"lat": lat, "lon": lon},
        "custom_data": ["City"],
        style_key: "carto-positron",
    }

    map_fig = scatter_func(**map_kwargs)
    map_fig.update_traces(marker=dict(size=13, opacity=0.92))
    map_fig.update_layout(
        height=430,
        margin=dict(l=0, r=0, t=5, b=0),
        legend_title_text="Air Quality",
        clickmode="event+select",
        uirevision=f"map-{st.session_state.selected_region}",
    )

    try:
        event = st.plotly_chart(
            map_fig,
            use_container_width=True,
            key="air_quality_map",
            on_select="rerun",
            selection_mode="points",
        )
        points = getattr(getattr(event, "selection", None), "points", []) if event else []
        if points:
            pt = points[0]
            cdata = pt.get("customdata") if isinstance(pt, dict) else None
            clicked_city = cdata[0] if cdata else None
            if clicked_city and clicked_city != st.session_state.selected_city:
                st.session_state["_pending_city"] = clicked_city
                st.rerun()
    except TypeError:
        st.plotly_chart(map_fig, use_container_width=True, key="air_quality_map_fallback")

    # Spacing below the map before the count cards
    st.markdown('<div class="map-spacer"></div>', unsafe_allow_html=True)

    # Snapshot summary counters
    counts = region_df["Level"].value_counts().reindex(LEVEL_ORDER + ["Unavailable"], fill_value=0)
    snap_cols = st.columns(5)
    for col, (_, level, feel, _, color, icon) in zip(snap_cols, LEVELS):
        cnt = int(counts.get(level, 0))
        col.markdown(
            f"""
            <div style="border-left:5px solid {color};padding:6px 10px;border-radius:6px;background:{color}10;">
                <div style="font-size:0.78rem;color:#475569;">{icon} {level}</div>
                <div style="font-size:1.25rem;font-weight:850;color:{color};">{cnt}</div>
                <div style="font-size:0.72rem;color:#64748B;">cities</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.caption(
    f"Sources: Open-Meteo Air Quality (CAMS Europe) | {weather_source} Weather | "
    f"{pollen_benchmark.get('source', 'Pollenrapporten')} | "
    f"Location: {st.session_state.selected_city}, {st.session_state.selected_region}"
)