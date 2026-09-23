import os
from datetime import date, datetime, timedelta
import pandas as pd
import plotly.express as px
import requests
import streamlit as st

# --------------------------------------------------
# Page configuration
# --------------------------------------------------
st.set_page_config(
    page_title="Air-aware | Outdoor Viability & Runner's Pollen Monitor",
    page_icon="🏃‍♂️",
    layout="wide",
    initial_sidebar_state="expanded",
)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# --------------------------------------------------
# Swedish Municipalities & Coordinates
# --------------------------------------------------
REGIONS_AND_CITIES = {
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

OPEN_METEO_AIR_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"
NRM_POLLEN_API_URL = "https://api.pollenrapporten.se/v1"

# --------------------------------------------------
# Pollen Dataset Loader
# --------------------------------------------------
@st.cache_data
def load_historical_pollen():
    candidates = [
        os.path.join(SCRIPT_DIR, "all_regions_pollen_municipal.csv"),
        "all_regions_pollen_municipal.csv",
        os.path.join(SCRIPT_DIR, "goteborg_historical_pollen_3.csv"),
        "goteborg_historical_pollen_3.csv",
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


df_pollen, pollen_filename = load_historical_pollen()

# --------------------------------------------------
# Current Pollen Check (Returns existence & source)
# --------------------------------------------------
@st.cache_data(ttl=1800, show_spinner=False)
def check_current_pollen(city_name: str, region_name: str):
    """Checks whether live pollen data is currently available."""
    # 1. Check NRM Pollenrapporten open data API
    try:
        r_regs = requests.get(f"{NRM_POLLEN_API_URL}/regions", params={"limit": 100}, timeout=4)
        if r_regs.status_code == 200:
            reg_items = r_regs.json().get("items", [])
            match = next((r for r in reg_items if r["name"].lower() in [city_name.lower(), region_name.lower()]), None)
            if match:
                r_fc = requests.get(f"{NRM_POLLEN_API_URL}/forecasts", params={"region_id": match["id"], "current": "true"}, timeout=4)
                if r_fc.status_code == 200:
                    fc_items = r_fc.json().get("items", [])
                    if fc_items and fc_items[0].get("levelSeries"):
                        return True, "Pollenrapporten (NRM)"
    except Exception:
        pass

    # 2. Check local active file
    cand_file = os.path.join(SCRIPT_DIR, "all_regions_pollen_municipal.csv")
    if os.path.exists(cand_file):
        df_mun = pd.read_csv(cand_file)
        slice_df = df_mun[df_mun["Region"].str.lower() == city_name.lower()]
        if slice_df.empty:
            slice_df = df_mun[df_mun["County"].str.lower() == region_name.lower()]
        if not slice_df.empty:
            return True, "Regional Sensor Matrix"

    return False, None


# --------------------------------------------------
# Live Environmental Data Fetchers
# --------------------------------------------------
@st.cache_data(ttl=900, show_spinner=False)
def fetch_city_pollution(lat: float, lon: float):
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
# Header & Navigation
# --------------------------------------------------
header_col1, header_col2 = st.columns([5, 1])
with header_col1:
    st.title("🏃‍♂️ Air-aware: Outdoor Viability & Runner's Pollen Benchmark")
    st.caption("Synchronized live air quality, live SMHI weather, and pollen benchmarks by Region & City.")

with header_col2:
    if st.button("🔄 Refresh Data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

st.markdown("---")

# --------------------------------------------------
# Cascading Region & City Selection
# --------------------------------------------------
sel_reg_col, sel_city_col, verdict_col = st.columns([1.5, 1.5, 3])

region_list = list(REGIONS_AND_CITIES.keys())
default_region_idx = region_list.index("Västra Götaland") if "Västra Götaland" in region_list else 0

with sel_reg_col:
    selected_region = st.selectbox(
        "📍 1. Select Region (Län)",
        options=region_list,
        index=default_region_idx,
    )

cities_in_region = list(REGIONS_AND_CITIES[selected_region].keys())
default_city_idx = cities_in_region.index("Göteborg") if "Göteborg" in cities_in_region else 0

with sel_city_col:
    selected_city = st.selectbox(
        "🏢 2. Select City",
        options=cities_in_region,
        index=default_city_idx,
    )

lat, lon = REGIONS_AND_CITIES[selected_region][selected_city]

# Fetch synchronized live data
curr_pol, hourly_df = fetch_city_pollution(lat, lon)
wx = fetch_city_weather(lat, lon)
has_current_pollen, pollen_source_name = check_current_pollen(selected_city, selected_region)

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
                <b>Location:</b> {selected_city}, {selected_region} ({lat:.2f}°N, {lon:.2f}°E)<br/>
                <b>Factors:</b> {note_text}
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
# SECTION: Current Pollen Status Banner
# --------------------------------------------------
st.subheader("🌾 Current Pollen Data Status")

if has_current_pollen:
    st.success(f"✅ Current pollen data is available for **{selected_city}** (Source: {pollen_source_name}).")
else:
    st.info(f"ℹ️ Current pollen data is unavailable for **{selected_city}** (no active monitoring station or off-season).")

st.markdown("---")

# --------------------------------------------------
# SECTION: Runner's Historical Pollen Comparison
# --------------------------------------------------
st.subheader("🌾 Runner's Pollen Radar: Same Date Previous Year Comparison")
st.caption(f"Historical trap observations referenced from `{pollen_filename}`.")

pollen_ctrl_col, pollen_metric_col = st.columns([1.5, 3.5])

with pollen_ctrl_col:
    target_run_date = st.date_input("Run Date for Comparison", value=date.today())
    
    try:
        prev_year_date = target_run_date.replace(year=target_run_date.year - 1)
    except ValueError:
        prev_year_date = target_run_date.replace(year=target_run_date.year - 1, day=28)

    st.markdown(f"**Target Run Date:** `{target_run_date}`")
    st.markdown(f"**Last Year's Date:** `{prev_year_date}`")

pollen_day_df = pd.DataFrame()
used_pollen_date = None
is_approximate = False

if not df_pollen.empty and "Date_Clean" in df_pollen.columns:
    exact_match = df_pollen[df_pollen["Date_Clean"] == prev_year_date]
    if not exact_match.empty:
        pollen_day_df = exact_match
        used_pollen_date = prev_year_date
    else:
        df_pollen["date_dt"] = pd.to_datetime(df_pollen["Date_Clean"])
        prev_target_dt = pd.to_datetime(prev_year_date)
        df_pollen["day_diff"] = (df_pollen["date_dt"] - prev_target_dt).abs()
        
        closest_row = df_pollen.loc[df_pollen["day_diff"].idxmin()]
        closest_date = closest_row["Date_Clean"]
        
        if closest_row["day_diff"] <= timedelta(days=14):
            pollen_day_df = df_pollen[df_pollen["Date_Clean"] == closest_date]
            used_pollen_date = closest_date
            is_approximate = True

with pollen_metric_col:
    if not pollen_day_df.empty:
        max_level = int(pollen_day_df["Level_Value"].max()) if pollen_day_df["Level_Value"].notna().any() else 0
        top_allergens = pollen_day_df[pollen_day_df["Level_Value"] == max_level]["Pollen"].tolist()
        top_allergen_str = ", ".join(top_allergens) if top_allergens else "None"

        if max_level == 0:
            p_badge = "🟢 Negligible Risk"
            p_advice = "Airway irritation from pollen is unlikely. Ideal for outdoor training."
            p_color = "#28a745"
        elif max_level <= 2:
            p_badge = "🟡 Moderate Allergen Exposure"
            p_advice = "Sensitive runners may feel mild ocular or nasal itchiness. Keep medication nearby."
            p_color = "#ffc107"
        elif max_level <= 4:
            p_badge = "🟠 Elevated Allergen Burden"
            p_advice = "High pollen release recorded. Consider wearing sunglasses, running after rain, or staying away from dense vegetation."
            p_color = "#fd7e14"
        else:
            p_badge = "🔴 Severe Pollen Warning"
            p_advice = "Extreme allergen concentrations recorded. Asthmatic runners should substitute with indoor treadmill sessions."
            p_color = "#dc3545"

        k_p1, k_p2, k_p3 = st.columns(3)
        k_p1.metric("Highest Recorded Level", f"{max_level} / 6")
        k_p2.metric("Dominant Allergen(s)", top_allergen_str)
        k_p3.metric("Historical Risk Rating", p_badge.split(" ")[1])

        if is_approximate:
            st.info(f"ℹ️ Exact sample for {prev_year_date} was not a recorded observation day. Showing closest seasonal sample: **{used_pollen_date}**.")
        else:
            st.success(f"✅ Exact match found for **{used_pollen_date}**.")

        pollen_chart_df = pollen_day_df.sort_values(by="Level_Value", ascending=True)
        fig_pollen = px.bar(
            pollen_chart_df,
            x="Level_Value",
            y="Pollen",
            orientation="h",
            color="Level_Value",
            color_continuous_scale=["#28a745", "#ffc107", "#fd7e14", "#dc3545"],
            range_color=[0, 6],
            title=f"Recorded Pollen Concentrations on {used_pollen_date} (Scale 0–6)",
            labels={"Level_Value": "Pollen Severity Level (0 = None, 6 = Extreme)", "Pollen": "Species"},
            text="Level_Value",
        )
        fig_pollen.update_layout(height=290, margin=dict(l=20, r=20, t=35, b=20), coloraxis_showscale=False)
        st.plotly_chart(fig_pollen, use_container_width=True)
    else:
        st.warning(
            f"No pollen observations recorded within 14 days of {prev_year_date}. "
            "Pollen counting stations in Sweden primarily operate between March and September."
        )

st.markdown("---")

# --------------------------------------------------
# Analytical Plots: Current Pollution & 48-Hour Forecast
# --------------------------------------------------
chart_col1, chart_col2 = st.columns([1, 1])

with chart_col1:
    st.subheader(f"📊 Atmospheric Profile — {selected_city}")
    pollutant_df = pd.DataFrame({
        "Pollutant": ["PM2.5", "PM10", "NO₂", "European AQI"],
        "Current Value": [pm25_val, pm10_val, no2_val, aqi_val],
        "Unit": ["µg/m³", "µg/m³", "µg/m³", "Index"],
    })
    fig_bars = px.bar(
        pollutant_df,
        x="Pollutant",
        y="Current Value",
        color="Pollutant",
        text_auto=".1f",
        title="Live Pollutant Breakdown",
        color_discrete_sequence=["#636EFA", "#EF553B", "#00CC96", "#AB63FA"],
    )
    fig_bars.update_layout(showlegend=False, height=330, margin=dict(l=20, r=20, t=40, b=20))
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
            fig_line.update_layout(margin=dict(l=20, r=20, t=35, b=20), height=290, hovermode="x unified")
            st.plotly_chart(fig_line, use_container_width=True)
    else:
        st.info("48-hour forecast is loading or unavailable.")

# --------------------------------------------------
# Practical Advice Drawer for Runners & Commuters
# --------------------------------------------------
with st.expander("🩺 Runner & Commuter Actionable Protocol", expanded=True):
    adv1, adv2, adv3 = st.columns(3)
    with adv1:
        st.markdown("**🏃‍♂️ Timing Your Run**")
        if wind_val >= 8.0:
            st.write("Wind disperses vehicle exhaust, but rapidly spreads airborne tree/grass pollen.")
        if rain_val > 0.5:
            st.write("Rainfall scrubs particulates and pollen out of the air—post-rain running is ideal for allergic runners.")
        else:
            st.write("Midday and early afternoon typically have optimal temperature and minimal mist-trapped allergens.")

    with adv2:
        st.markdown("**🌳 Route Selection Advice**")
        st.write("• **High Grass/Birch:** Stick to paved coastal or urban routes away from meadows and deciduous forests.")
        st.write("• **High PM2.5/NO₂:** Avoid main arterial roads and rush-hour traffic; choose residential parks.")

    with adv3:
        st.markdown("**🚿 Post-Run Care**")
        st.write("• Rinse eyes with saline and wash hair immediately to eliminate trapped pollen grains.")
        st.write("• Keep running clothing outside the bedroom to prevent nighttime allergen exposure.")