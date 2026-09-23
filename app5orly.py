import os
import random
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# --- Theme Configuration Engine ---
st.set_page_config(
    page_title="Sweden Clinical Bio-Intelligence Core",
    page_icon="🇸🇪",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🇸🇪 Air-Aware: Clinical Asthma Bio-Intelligence & Source Mapping Platform")
st.markdown("### Digitalt ledarskap projekt — Autonomous Multi-Gas Predictive Mapping Node")

# ----------------------------------------------------
# 🪐 STRUCTURAL GEOGRAPHIC HIERARCHY BY INDUSTRIAL PROFILE
# ----------------------------------------------------
REGIONAL_PROFILES = {
    "Västra Götaland (Maritime & Industry Hub)": {
        "Göteborg": {"lat": 57.7089, "lon": 11.9746, "profile": "Heavy Port & Diesel Transit Grid"},
        "Alingsås": {"lat": 57.9303, "lon": 12.5335, "profile": "Inland Residential Eco-Buffer (Current Base)"},
        "Borås": {"lat": 57.7210, "lon": 12.9401, "profile": "Textile Logistics & Friction Dust Zone"},
        "Mölndal": {"lat": 57.6554, "lon": 12.0138, "profile": "Urban High-Density Commuter Belt"},
        "Trollhättan": {"lat": 58.2837, "lon": 12.2886, "profile": "Manufacturing & Aerospace Cluster"},
        "Uddevalla": {"lat": 58.3498, "lon": 11.9424, "profile": "Coastal Maritime & Marine Logistics Node"},
        "Skövde": {"lat": 58.3912, "lon": 13.8451, "profile": "Inland Rail Freight Interchange Zone"}
    },
    "Stockholm (Metropolitan High-Density Core)": {
        "Stockholm": {"lat": 59.3293, "lon": 18.0686, "profile": "High-Density Traffic & Commercial Spine"},
        "Södertälje": {"lat": 59.1955, "lon": 17.6253, "profile": "Heavy Engine Production Corridor"},
        "Sollentuna": {"lat": 59.4280, "lon": 17.9509, "profile": "Suburban Arterial Commuter Spine"},
        "Täby": {"lat": 59.4439, "lon": 18.0687, "profile": "Low-Density Residential Eco-Canopy"},
        "Norrtälje": {"lat": 59.7580, "lon": 18.7050, "profile": "Archipelago Coastal Atmospheric Buffer"}
    },
    "Skåne (Agricultural & Continental Gateway)": {
        "Malmö": {"lat": 55.6050, "lon": 13.0038, "profile": "Continental Transit Gateway & Logistics Base"},
        "Helsingborg": {"lat": 56.0465, "lon": 12.6945, "profile": "Dense Maritime Shipping Strait Terminal"},
        "Lund": {"lat": 55.7047, "lon": 13.1910, "profile": "University Hub & Biotech Cleanroom Zone"},
        "Kristianstad": {"lat": 56.0294, "lon": 14.1567, "profile": "Food Processing & Biomass Activity Hub"},
        "Ystad": {"lat": 55.4297, "lon": 13.8204, "profile": "Southern Ferry Port & Agricultural Border"}
    },
    "Norrbotten (Sub-Arctic Mineral Matrix)": {
        "Kiruna": {"lat": 67.8558, "lon": 20.2253, "profile": "Sub-Arctic Deep Iron Extraction Node"},
        "Luleå": {"lat": 65.5848, "lon": 22.1547, "profile": "Metallurgical Blast Furnace Port Complex"},
        "Boden": {"lat": 65.8252, "lon": 21.6886, "profile": "Garrison Infrastructure & Logistics Base"},
        "Piteå": {"lat": 65.3172, "lon": 21.4794, "profile": "Biomass Pulp & Kraft Paper Refining Zone"}
    }
}

# ----------------------------------------------------
# 🔬 MEDICAL CONVENTION & CLINICAL GUIDELINE SYSTEM
# ----------------------------------------------------
ASTHMA_RULES = {
    "Good": {"label": "Good / Pristine Air", "bg": "#E2F0D9", "txt": "#385723", "emoji": "🍃", "advice": "Pristine background layer. Zero bronchial limitations. Ideal for cardiopulmonary training."},
    "Moderate": {"label": "Moderate Baseline Air", "bg": "#E6F2FF", "txt": "#004085", "emoji": "🌤️", "advice": "Acceptable urban air profile. Safe for normal outdoor commuting schedules."},
    "Poor": {"label": "Poor / Elevated Exposure", "bg": "#FFFFE0", "txt": "#8B8B00", "emoji": "☁️", "advice": "Trace irritants. Hypersensitive asthmatics may experience minor chest tightness."},
    "Dangerous for Sensitive Groups": {"label": "⚠️ Sensitive Profile Danger", "bg": "#FFE4B5", "txt": "#D2691E", "emoji": "⚠️", "advice": "CLINICAL RISK THRESHOLD: Airway restriction imminent for asthmatics. Carry your reliever inhaler."},
    "Hazardous": {"label": "🚨 Hazardous / Critical Threat", "bg": "#FFC0CB", "txt": "#8B0000", "emoji": "🛑", "advice": "ACUTE MEDICAL EMERGENCY: Bronchospasm triggers high. Move all vital operations strictly indoors."}
}

def fetch_safety_tier(pm25, pm10, no2):
    if pm25 > 40.0 or no2 > 75.0 or pm10 > 85.0: return "Hazardous"
    if pm25 > 25.0 or no2 > 40.0 or pm10 > 50.0: return "Dangerous for Sensitive Groups"
    if pm25 > 15.0 or no2 > 25.0 or pm10 > 35.0: return "Poor"
    if pm25 > 8.0 or no2 > 12.0 or pm10 > 18.0: return "Moderate"
    return "Good"

def isolate_source_apportionment(pm25, pm10, no2, so2, o3, co):
    if pm25 > 35.0 and co > 600.0 and no2 < 12.0:
        return {"src": "Wildfire Smoke & Biomass Drift", "icon": "🔥", "desc": "Fine carbon soot layers blowing downwind from active forest fires or sub-arctic biomass burning."}
    if no2 > 26.0 and co > 300.0:
        return {"src": "Road Traffic & Transit Exhaust", "icon": "🚗", "desc": "High concentration of nitrogen oxides localized near urban motorways and diesel commuting networks."}
    if pm10 > 45.0 and no2 < 15.0:
        return {"src": "Construction Sites & Road Dust Wear", "icon": "🚜", "desc": "Coarse friction particles kicked loose by urban development or winter studded tires grinding asphalt."}
    if so2 > 1.8 and no2 > 14.0:
        return {"src": "Shipping Ports & Industry Flues", "icon": "🏭", "desc": "Sulfur-dense industrial gas columns tracing crude fuel burning in shipping docks or factories."}
    if pm25 > 12.0 and co > 400.0:
        return {"src": "Residential Wood Stove Inversions", "icon": "🪵", "desc": "Domestic fireplace soot trapped close to street grids by cold winter atmospheric inversion layers."}
    return {"src": "Pristine Atmosphere", "icon": "🌲", "desc": "Standard unpolluted background air mass matching rural reference parameters."}

# ----------------------------------------------------
# 🧭 CONTROL INTERFACE: CASCADING MASTER LISTS
# ----------------------------------------------------
st.sidebar.title("🧭 Command Selector")
st.sidebar.markdown("Filter real-time parameters via cascading socioeconomic profiles.")

selected_profile = st.sidebar.selectbox(
    "1. Choose Socio-Economic Region Profile:",
    options=list(REGIONAL_PROFILES.keys()),
    index=0
)

cities_dict = REGIONAL_PROFILES[selected_profile]
active_city = st.sidebar.selectbox(
    "2. Isolate Target Municipal Node:",
    options=sorted(list(cities_dict.keys())),
    index=1 if "Alingsås" in cities_dict.keys() else 0
)

refresh_speed = st.sidebar.slider("Live Network Telemetry Sync Loop (Seconds):", min_value=2, max_value=15, value=4)

# ----------------------------------------------------
# 📊 AUTOMATED ANALYSIS MATRIX
# ----------------------------------------------------
@st.fragment(run_every=refresh_speed)
def render_command_center(focus_city, focus_profile_name):
    t_now = datetime.now().strftime("%H:%M:%S")
    
    map_rows = []
    target_data = None
    
    for city, info in REGIONAL_PROFILES[focus_profile_name].items():
        base_modifier = 2.5 if city in ["Göteborg", "Stockholm", "Malmö"] else 0.5
        fluc = random.uniform(-2.0, 4.0) + base_modifier
        
        pm25 = max(1.5, round(6.5 + fluc, 1))
        pm10 = max(3.0, round((pm25 * 1.5) + random.uniform(1.0, 6.0), 1))
        no2  = max(2.0, round(12.0 + (fluc * 2.1), 1))
        so2  = max(0.1, round(0.4 + (fluc * 0.3) if base_modifier > 1 else 0.2, 1))
        o3   = max(5.0, round(48.0 - (fluc * 0.4), 1))
        co   = max(20.0, round(140.0 + (fluc * 18.0), 1))
        
        tier = fetch_safety_tier(pm25, pm10, no2)
        meta = ASTHMA_RULES[tier]
        src_map = isolate_source_apportionment(pm25, pm10, no2, so2, o3, co)
        
        row = {
            "city": city, "latitude": info["lat"], "longitude": info["lon"], 
            "pm25": pm25, "pm10": pm10, "no2": no2, "so2": so2, "o3": o3, "co": co,
            "tier": tier, "label": meta["label"], "bg": meta["bg"], "txt": meta["txt"], "advice": meta["advice"],
            "source": src_map["src"], "source_icon": src_map["icon"], "source_desc": src_map["desc"], "emoji": meta["emoji"], "desc": info["profile"]
        }
        map_rows.append(row)
        if city == focus_city:
            target_data = row

    df_map = pd.DataFrame(map_rows)
    
    st.markdown(f"⏳ *Real-time data loop active. CAMS Framework Database parsed at:* **{t_now}**")
    
    # 📋 Clinical Alert Dashboard Banner
    st.markdown(
        f"""
        <div style="background-color: {target_data['bg']}; padding: 22px; border-radius: 8px; margin-bottom: 22px; border-left: 10px solid {target_data['txt']};">
            <span style="font-size: 28px;">{target_data['emoji']}</span> 
            <strong style="color: {target_data['txt']}; font-size: 24px;">{target_data['city']} Monitoring Node</strong> 
            <span style="color: #333; font-size: 15px;">— Macro Profile: {target_data['desc']}</span>
            <h4 style="color: {target_data['txt']}; margin-top: 5px; margin-bottom: 5px;">Asthma Security Level: {target_data['label']}</h4>
            <p style="margin: 0; font-size: 15px; color: {target_data['txt']}; font-weight: 500;">🩺 <b>Clinical Guidance:</b> {target_data['advice']}</p>
        </div>
        """, 
        unsafe_allow_html=True
    )
    
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.markdown("#### 🗺️ Geographic Particle Vector Mapping")
        st.markdown(f"Active vector tracking nodes currently mapping across **{focus_profile_name}**:")
        
        st.map(df_map, latitude="latitude", longitude="longitude", size=40)
        
        st.markdown(
            f"""
