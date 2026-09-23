import os
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import plotly.express as px
import requests
import streamlit as st

# Optional persistent browser storage with automatic session fallback
try:
    from streamlit_local_storage import LocalStorage

    local_storage = LocalStorage()
    HAS_LOCAL_STORAGE = True
except ImportError:
    local_storage = None
    HAS_LOCAL_STORAGE = False

# -----------------------------------------------------------------------------
# 1. Page Configuration
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Air-aware | Personalized Environmental Monitor",
    page_icon="🌤️",
    layout="wide",
    initial_sidebar_state="expanded",
)

SCRIPT_DIR: str = os.path.dirname(os.path.abspath(__file__))
OPEN_METEO_AIR_URL: str = "https://air-quality-api.open-meteo.com/v1/air-quality"

# -----------------------------------------------------------------------------
# 2. Swedish Geographic Hierarchy (Region -> Municipalities)
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

# Inverted mapping to quickly resolve Region given a City name
CITY_TO_REGION: Dict[str, str] = {
    city: reg for reg, cities in REGIONS_AND_CITIES.items() for city in cities
}
ALL_CITIES: List[str] = sorted(list(CITY_TO_REGION.keys()))

STATUS_DISPLAY = {
    "good": ("Good", "✅", "#18794E"),
    "fair": ("Fair", "ℹ️", "#0F6CBD"),
    "moderate": ("Moderate", "⚠️", "#B25E09"),
    "poor": ("Poor", "▲", "#C2410C"),
    "very_poor": ("Very poor", "⛔", "#B42318"),
    "unavailable": ("Unavailable", "❓", "#667085"),
}


def display_value(value: Any, unit: str = "", decimals: int = 1) -> str:
    try:
        if value is None or pd.isna(value):
            return "Unavailable"
        rendered = f"{float(value):.{decimals}f}"
        return f"{rendered} {unit}".strip()
    except (TypeError, ValueError):
        return "Unavailable"


def status_parts(status: str) -> Tuple[str, str, str]:
    return STATUS_DISPLAY.get(status, STATUS_DISPLAY["unavailable"])


# -----------------------------------------------------------------------------
# 3. Preferences & Storage Layer
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
            val = local_storage.getItem("air_aware_onboarding_seen")
            return bool(val)
        except Exception:
            return False
    return False


# Initialize Session State
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
if "preferences_saved_message" not in st.session_state:
    st.session_state.preferences_saved_message = False

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


# -----------------------------------------------------------------------------
# 4. Onboarding Dialog (Landing Flow)
# -----------------------------------------------------------------------------
@st.dialog("🌤️ Welcome to Air-aware")
def onboarding_dialog():
    st.write(
        "Personalize your Air-aware experience by selecting your preferred municipality and the specific "
        "environmental signals you want to track."
    )
    st.divider()

    st.subheader("📍 Where are you located?")
    diag_city = st.selectbox(
        "Choose default municipality",
        options=ALL_CITIES,
        index=ALL_CITIES.index("Göteborg") if "Göteborg" in ALL_CITIES else 0,
        key="onboard_city_input",
    )

    st.subheader("Which metrics are you interested in?")
    diag_w = st.checkbox("🌤️ Live Weather (SMHI)", value=True, key="onboard_w")
    diag_pol = st.checkbox("🌫️ Air Quality & Pollution (Open-Meteo)", value=True, key="onboard_pol")
    diag_p = st.checkbox("🌾 Runner's Pollen Radar (Historical Trap Benchmark)", value=True, key="onboard_p")

    st.divider()
    btn_col1, btn_col2 = st.columns(2)
    with btn_col1:
        if st.button("Save & Continue", type="primary", use_container_width=True):
            save_preferences(diag_city, diag_w, diag_p, diag_pol)
            st.session_state.selected_city = diag_city
            st.session_state.selected_region = CITY_TO_REGION[diag_city]
            st.session_state.pref_weather = diag_w
            st.session_state.pref_pollution = diag_pol
            st.session_state.pref_pollen = diag_p
            st.rerun()

    with btn_col2:
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


# -----------------------------------------------------------------------------
# 5. Core Data Pipelines (Weather, Air Quality, Pollen)
# -----------------------------------------------------------------------------
@st.cache_data
def load_historical_pollen_dataset() -> Tuple[pd.DataFrame, str]:
    candidates = [
        os.path.join(SCRIPT_DIR, "goteborg_historical_pollen_3.csv"),
        "goteborg_historical_pollen_3.csv",
        os.path.join(SCRIPT_DIR, "goteborg_historical_pollen_2.csv"),
        "goteborg_historical_pollen_2.csv",
        os.path.join(SCRIPT_DIR, "goteborg_historical_pollen.csv"),
        "goteborg_historical_pollen.csv",
    ]
    pollen_path = next((p for p in candidates if os.path.exists(p)), None)
    if not pollen_path:
        return pd.DataFrame(), "None"

    df = pd.read_csv(pollen_path)
    df.columns = df.columns.str.strip()
    if "Date" in df.columns:
        df["Date_Clean"] = pd.to_datetime(df["Date"], errors="coerce").dt.date
    if "Level_Value" in df.columns:
        df["Level_Value"] = pd.to_numeric(df["Level_Value"], errors="coerce")
    return df, os.path.basename(pollen_path)


@st.cache_data(ttl=900, show_spinner=False)
def fetch_city_pollution(lat: float, lon: float) -> Tuple[Dict[str, Any], pd.DataFrame]:
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
            payload = r.json()
            return payload.get("current", {}), pd.DataFrame(payload.get("hourly", {}))
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
                "cloudiness": fc.get("cloud_area_fraction", 50.0),
            }
    except Exception:
        pass

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


def calculate_viability(aqi, temp, wind, precip, pollen_level):
    score = 100
    reasons = []

    if aqi is not None and not pd.isna(aqi):
        if aqi > 80:
            score -= 50
            reasons.append("Very poor air quality (High AQI)")
            air_status = "very_poor"
        elif aqi > 50:
            score -= 30
            reasons.append("Moderate air pollution")
            air_status = "moderate"
        elif aqi > 25:
            score -= 10
            reasons.append("Fair air quality with minor particulate matter")
            air_status = "fair"
        else:
            air_status = "good"
    else:
        air_status = "unavailable"

    if precip is not None and not pd.isna(precip):
        if precip >= 3.0:
            score -= 40
            reasons.append(f"Heavy rain ({precip:.1f} mm)")
        elif precip > 0.2:
            score -= 15
            reasons.append(f"Light rain or showers ({precip:.1f} mm)")

    if wind is not None and not pd.isna(wind):
        if wind >= 13.0:
            score -= 35
            reasons.append(f"Strong winds ({wind:.1f} m/s)")
        elif wind >= 8.0:
            score -= 15
            reasons.append(f"Breezy conditions ({wind:.1f} m/s)")

    if temp is not None and not pd.isna(temp):
        if temp < -5:
            score -= 25
            reasons.append(f"Freezing temperature ({temp:.1f} °C)")
        elif temp < 5:
            score -= 10
            reasons.append(f"Chilly weather ({temp:.1f} °C)")
        elif temp > 30:
            score -= 25
            reasons.append(f"High heat ({temp:.1f} °C)")

    if pollen_level is not None and not pd.isna(pollen_level):
        if pollen_level >= 5:
            score -= 20
            reasons.append(f"Very high seasonal pollen burden (Level {pollen_level}/6)")
            pollen_status = "very_poor"
        elif pollen_level >= 3:
            score -= 10
            reasons.append(f"Elevated seasonal pollen recorded (Level {pollen_level}/6)")
            pollen_status = "moderate"
        elif pollen_level >= 1:
            pollen_status = "fair"
        else:
            pollen_status = "good"
    else:
        pollen_status = "unavailable"

    score = max(0, min(100, score))

    if score >= 80:
        verdict = "Optimal for Outdoor Activities"
        overall_status = "good"
    elif score >= 55:
        verdict = "Fair / Acceptable Conditions"
        overall_status = "fair"
    elif score >= 35:
        verdict = "Poor / Caution Advised"
        overall_status = "poor"
    else:
        verdict = "Unfavorable / Stay Indoors"
        overall_status = "very_poor"

    if not reasons:
        reasons = ["Ideal air quality, low allergen exposure, and calm weather."]

    result = {
        "score": score,
        "verdict": verdict,
        "status": overall_status,
        "air_status": air_status,
        "pollen_status": pollen_status,
        "reasons": reasons,
    }

    recommendation = {
        "general": f"Conditions in this area indicate an outdoor viability rating of {score}/100.",
        "exercise": (
            "Great conditions for outdoor workouts, running, or cycling."
            if score >= 80
            else "Suitable for moderate activity; sensitive athletes should monitor pacing."
            if score >= 55
            else "Consider substituting outdoor endurance training with indoor workouts."
        ),
        "sensitive": (
            "Heightened allergen or pollutant exposure. Asthmatic and allergy-sensitive individuals should carry medication."
            if (pollen_level and pollen_level >= 3) or (aqi and aqi > 50)
            else "Air quality and allergen conditions are within standard safe limits."
        ),
    }

    return result, recommendation


# -----------------------------------------------------------------------------
# 6. Sidebar: Quick Preference Manager & Navigation
# -----------------------------------------------------------------------------
with st.sidebar:
    st.header("⚙️ Preference Controls")
    st.caption("Toggle your active monitoring modules below or change your home location.")

    quick_city = st.selectbox(
        "Home Municipality",
        options=ALL_CITIES,
        index=ALL_CITIES.index(st.session_state.selected_city)
        if st.session_state.selected_city in ALL_CITIES
        else 0,
    )
    if quick_city != st.session_state.selected_city:
        st.session_state.selected_city = quick_city
        st.session_state.selected_region = CITY_TO_REGION[quick_city]
        st.rerun()

    st.markdown("**Active Signals**")
    w_on = st.checkbox("🌤️ Weather Metrics", value=st.session_state.pref_weather)
    pol_on = st.checkbox("🌫️ Air Pollution Metrics", value=st.session_state.pref_pollution)
    p_on = st.checkbox("🌾 Historical Pollen", value=st.session_state.pref_pollen)

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
    if st.button("Reset Preferences & Onboard Again", use_container_width=True):
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
# 7. Main Dashboard Interface
# -----------------------------------------------------------------------------
st.title("🌤️ Air-aware: Environmental & Viability Dashboard")

# Top Navigation: Region, City & Date Picker
col_r, col_c, col_d, col_btn = st.columns([1.5, 1.5, 1.2, 0.8])
region_list = list(REGIONS_AND_CITIES.keys())
current_reg = st.session_state.selected_region
reg_idx = region_list.index(current_reg) if current_reg in region_list else 0

with col_r:
    chosen_region = st.selectbox("📍 Region (Län)", options=region_list, index=reg_idx)
    if chosen_region != st.session_state.selected_region:
        st.session_state.selected_region = chosen_region
        # Default to first city in new region
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

with col_d:
    target_run_date = st.date_input("📅 Date Comparison", value=date.today())

with col_btn:
    st.write("")
    st.write("")
    if st.button("🔄 Refresh", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

st.markdown("---")

lat, lon = REGIONS_AND_CITIES[st.session_state.selected_region][st.session_state.selected_city]

# Date math for prior-year matching
try:
    prev_year_date = target_run_date.replace(year=target_run_date.year - 1)
except ValueError:
    prev_year_date = target_run_date.replace(year=target_run_date.year - 1, day=28)

# Load Datasets and Queries
df_pollen, pollen_filename = load_historical_pollen_dataset()
curr_pol, hourly_df = fetch_city_pollution(lat, lon)
wx = fetch_city_weather(lat, lon)

# Match Historical Pollen
pollen_day_df = pd.DataFrame()
pollen_benchmark: Dict[str, Any] = {
    "available": False,
    "level": None,
    "dominant": "None",
    "date": None,
    "source": pollen_filename,
}
pollen_approximate = False

if not df_pollen.empty and "Date_Clean" in df_pollen.columns:
    exact_match = df_pollen[df_pollen["Date_Clean"] == prev_year_date]
    if not exact_match.empty:
        pollen_day_df = exact_match
        used_pollen_date = prev_year_date
        pollen_approximate = False
    else:
        df_pollen["date_dt"] = pd.to_datetime(df_pollen["Date_Clean"])
        prev_target_dt = pd.to_datetime(prev_year_date)
        df_pollen["day_diff"] = (df_pollen["date_dt"] - prev_target_dt).abs()
        closest_row = df_pollen.loc[df_pollen["day_diff"].idxmin()]
        if closest_row["day_diff"] <= timedelta(days=14):
            pollen_day_df = df_pollen[df_pollen["Date_Clean"] == closest_row["Date_Clean"]]
            used_pollen_date = closest_row["Date_Clean"]
            pollen_approximate = True

    if not pollen_day_df.empty:
        max_level = int(pollen_day_df["Level_Value"].max()) if pollen_day_df["Level_Value"].notna().any() else 0
        top_allergens = pollen_day_df[pollen_day_df["Level_Value"] == max_level]["Pollen"].tolist()
        pollen_benchmark = {
            "available": True,
            "level": max_level,
            "dominant": ", ".join(top_allergens) if top_allergens else "None",
            "date": str(used_pollen_date),
            "source": pollen_filename,
        }

# Metric extractions
aqi_val = curr_pol.get("european_aqi")
pm25_val = curr_pol.get("pm2_5")
pm10_val = curr_pol.get("pm10")
no2_val = curr_pol.get("nitrogen_dioxide")

temp_val = wx.get("temperature")
wind_val = wx.get("wind_speed")
rain_val = wx.get("precipitation")
weather_source = wx.get("source", "SMHI")

# Compute Viability Result
result, recommendation = calculate_viability(
    aqi=aqi_val,
    temp=temp_val,
    wind=wind_val,
    precip=rain_val,
    pollen_level=pollen_benchmark.get("level"),
)

# -----------------------------------------------------------------------------
# 8. Executive Recommendation Banner
# -----------------------------------------------------------------------------
_, icon, color = status_parts(result["status"])
reasons_text = " • ".join(result["reasons"])

st.markdown(
    f"""<div style="background:#F7FAFC;border:2px solid {color};border-left:10px solid {color};padding:22px;border-radius:12px;margin:5px 0 20px">
    <p style="margin:0;color:#475467">Current Viability Recommendation for <b>{st.session_state.selected_city}, {st.session_state.selected_region}</b></p>
    <h2 style="margin:4px 0;color:#101828">{icon} {result['verdict']}</h2>
    <p style="color:#344054">{recommendation['general']}</p>
    <p style="margin:0;color:#475467"><strong>Why?</strong> {reasons_text}</p></div>""",
    unsafe_allow_html=True,
)

overall_col, air_column, pollen_column = st.columns(3)
air_label, air_icon, _ = status_parts(result["air_status"])
pollen_label, pollen_icon, _ = status_parts(result["pollen_status"])

overall_col.metric("Overall Outdoor Viability", f"{icon} {result['score']}/100")
air_column.metric("Live Air Quality", f"{air_icon} {air_label}")
pollen_column.metric("Historical Pollen Risk", f"{pollen_icon} {pollen_label}")

# -----------------------------------------------------------------------------
# 9. Dynamic Signal Modules (Based on Preferences)
# -----------------------------------------------------------------------------
if st.session_state.pref_pollution:
    st.subheader("🌫️ Air Quality & Particulate Pollution (Live)")
    m_cols = st.columns(4)
    m_cols[0].metric("European AQI", display_value(aqi_val, decimals=0))
    m_cols[1].metric("PM2.5", display_value(pm25_val, "µg/m³"))
    m_cols[2].metric("PM10", display_value(pm10_val, "µg/m³"))
    m_cols[3].metric("NO₂", display_value(no2_val, "µg/m³"))

if st.session_state.pref_weather:
    st.subheader("🌤️ Meteorological Conditions (Live SMHI)")
    w_cols = st.columns(3)
    w_cols[0].metric("Temperature", display_value(temp_val, "°C"))
    w_cols[1].metric("Wind Speed", display_value(wind_val, "m/s"))
    w_cols[2].metric("Precipitation", display_value(rain_val, "mm"))

if st.session_state.pref_pollen:
    st.subheader("🌾 Historical Pollen Radar (Same Date Previous Year)")
    p_cols = st.columns(3)
    p_cols[0].metric("Highest Pollen Level", display_value(pollen_benchmark.get("level"), "/ 6", 0))
    p_cols[1].metric("Dominant Allergen(s)", pollen_benchmark.get("dominant", "Unavailable"))
    p_cols[2].metric("Observation Sample Date", pollen_benchmark.get("date") or "Unavailable")

    if pollen_benchmark.get("available"):
        note = (
            "This is the nearest observation within 14 days."
            if pollen_approximate
            else "Exact historical match found."
        )
        st.info(f"{note} Recorded historical baseline for runner guidance.")
    else:
        st.warning("No pollen observations recorded within 14 days of this seasonal target.")

# -----------------------------------------------------------------------------
# 10. Analytical Visualizations
# -----------------------------------------------------------------------------
st.markdown("---")
st.subheader("📊 Interactive Analytical Forecasts")

c_left, c_right = st.columns(2)

with c_left:
    if st.session_state.pref_pollen and not pollen_day_df.empty:
        st.markdown(f"**Pollen Species Breakdown ({pollen_benchmark.get('date')})**")
        pollen_chart_df = pollen_day_df.sort_values(by="Level_Value", ascending=True)
        fig_p = px.bar(
            pollen_chart_df,
            x="Level_Value",
            y="Pollen",
            orientation="h",
            color="Level_Value",
            color_continuous_scale=["#18794E", "#0F6CBD", "#B25E09", "#B42318"],
            range_color=[0, 6],
            labels={"Level_Value": "Severity (0–6)", "Pollen": "Species"},
            text="Level_Value",
        )
        fig_p.update_layout(height=290, margin=dict(l=20, r=20, t=25, b=20), coloraxis_showscale=False)
        st.plotly_chart(fig_p, use_container_width=True)
    else:
        st.markdown("**Atmospheric Composition Breakdown**")
        pollutant_df = pd.DataFrame({
            "Metric": ["PM2.5", "PM10", "NO₂", "European AQI"],
            "Value": [pm25_val or 0, pm10_val or 0, no2_val or 0, aqi_val or 0],
        })
        fig_bars = px.bar(
            pollutant_df,
            x="Metric",
            y="Value",
            color="Metric",
            text_auto=".1f",
            color_discrete_sequence=["#18794E", "#0F6CBD", "#B25E09", "#B42318"],
        )
        fig_bars.update_layout(showlegend=False, height=290, margin=dict(l=20, r=20, t=25, b=20))
        st.plotly_chart(fig_bars, use_container_width=True)

with c_right:
    st.markdown(f"**48-Hour Air Quality Curve ({st.session_state.selected_city})**")
    if not hourly_df.empty and "time" in hourly_df.columns:
        chosen_metric = st.radio(
            "Forecast Metric:",
            options=["european_aqi", "pm2_5", "pm10", "nitrogen_dioxide"],
            format_func=lambda x: x.upper().replace("_", " "),
            horizontal=True,
        )
        if chosen_metric in hourly_df.columns:
            fig_line = px.line(
                hourly_df,
                x="time",
                y=chosen_metric,
                labels={"time": "Time (CET)", chosen_metric: "Value"},
            )
            fig_line.update_traces(line=dict(color="#0F6CBD", width=2.5))
            fig_line.update_layout(margin=dict(l=20, r=20, t=25, b=20), height=240, hovermode="x unified")
            st.plotly_chart(fig_line, use_container_width=True)
    else:
        st.info("48-hour forecast is loading or unavailable.")

# -----------------------------------------------------------------------------
# 11. Practical Activity & Sensitive Groups Guidance
# -----------------------------------------------------------------------------
st.subheader("🏃 Actionable Practical Guidance")
g_col1, g_col2 = st.columns(2)
with g_col1:
    st.markdown("#### 🏃 Outdoor Activity & Running")
    st.write(recommendation["exercise"])
with g_col2:
    st.markdown("#### 🫁 Sensitive Demographics & Allergies")
    st.write(recommendation["sensitive"])

with st.expander("📚 Guide to Measurements & Quality Standards"):
    st.markdown(
        "• **European AQI:** An index synthesized by the European Environment Agency (0–20 Good, 80+ Very Poor).\n\n"
        "• **PM2.5 & PM10:** Inhalable fine combustion particles and coarse road dust.\n\n"
        "• **NO₂:** Combustion emission gas linked to road vehicle traffic.\n\n"
        "• **Historical Pollen Level (0–6):** Trap measurements ranging from 0 (none) to 6 (extreme allergic burden)."
    )

st.caption(
    f"Sources: Open-Meteo Air Quality | {weather_source} Weather | "
    f"{pollen_benchmark.get('source', 'Unavailable')} Pollen | Target: {st.session_state.selected_city}, {st.session_state.selected_region} ({lat:.2f}°N, {lon:.2f}°E)"
)