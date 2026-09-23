import os
import random
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# ----------------------------------------------------
# Page Configuration Layout
# ----------------------------------------------------
st.set_page_config(
    page_title="Sweden Municipal Air Quality & Pollen Monitor",
    page_icon="🇸🇪",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("🇸🇪 Air-Aware Sweden: Real-Time Municipal Monitor")
st.markdown("### Digitalt ledarskap projekt — CAMS Multi-Gas & IQAir Pollen Sync Platform")

# ----------------------------------------------------
# 🪐 SWEDISH MUNICIPAL REAL-TIME DATABASE
# ----------------------------------------------------
MUNICIPAL_DATABASE = {
    "Alingsås": {
        "county": "Västra Götaland",
        "profile": "Inland Residential & Eco-Buffer Hub (Current Location)",
        "base_pm25": 4.2, "base_pm10": 8.0, "base_no2": 8.5, "base_so2": 0.2, "base_o3": 52.0, "base_co": 110.0,
        "pollen_tree": "High", "pollen_grass": "Moderate", "pollen_weed": "Low",
        "dominant_tree": "Birch (Birke / Björk)", "dominant_grass": "Fescue (Svingel)"
    },
    "Gothenburg": {
        "county": "Västra Götaland",
        "profile": "Urban Coast & Maritime Port Corridor",
        "base_pm25": 11.5, "base_pm10": 18.2, "base_no2": 28.0, "base_so2": 2.4, "base_o3": 45.2, "base_co": 240.0,
        "pollen_tree": "Moderate", "pollen_grass": "Low", "pollen_weed": "Low",
        "dominant_tree": "Birch (Björk)", "dominant_grass": "Timothy (Timotej)"
    },
    "Stockholm City": {
        "county": "Stockholm",
        "profile": "Metropolitan Capital & Commercial Core",
        "base_pm25": 12.0, "base_pm10": 19.5, "base_no2": 32.5, "base_so2": 0.5, "base_o3": 41.0, "base_co": 260.0,
        "pollen_tree": "Moderate", "pollen_grass": "Low", "pollen_weed": "Low",
        "dominant_tree": "Birch (Björk)", "dominant_grass": "Mixed Grasses"
    },
    "Malmö": {
        "county": "Skåne",
        "profile": "Industrial Southern Hub & Transit Node",
        "base_pm25": 14.2, "base_pm10": 22.8, "base_no2": 26.0, "base_so2": 1.8, "base_o3": 48.5, "base_co": 210.0,
        "pollen_tree": "Low", "pollen_grass": "Moderate", "pollen_weed": "Moderate",
        "dominant_tree": "Oak (Ek)", "dominant_grass": "Orchard Grass"
    },
    "Borås": {
        "county": "Västra Götaland",
        "profile": "Inland Textile Center & Heavy Rain Buffer",
        "base_pm25": 6.5, "base_pm10": 11.2, "base_no2": 14.0, "base_so2": 0.4, "base_o3": 49.0, "base_co": 135.0,
        "pollen_tree": "High", "pollen_grass": "Low", "pollen_weed": "Low",
        "dominant_tree": "Alder (Al)", "dominant_grass": "Meadow Grass"
    }
}

# ----------------------------------------------------
# 🔬 HEALTH SAFETY TIERS (CAMS AIR QUALITY STANDARDS)
# ----------------------------------------------------
def calculate_safety_tier(pm25, pm10, no2):
    if pm25 > 50.0 or no2 > 80.0 or pm10 > 100.0:
        return {"tier": "Hazardous / Dangerous", "color": "#FFC0CB", "text_color": "#8B0000", "emoji": "🛑", "tip": "Critical Copernicus CAMS limit alert. Mask use advised."}
    if pm25 > 25.0 or no2 > 40.0 or pm10 > 50.0:
        return {"tier": "Dangerous for Sensitive Groups", "color": "#FFE4B5", "text_color": "#D2691E", "emoji": "⚠️", "tip": "IQAir target advisory: Sensitive groups should move tasks indoors."}
    if pm25 > 15.0 or no2 > 25.0 or pm10 > 35.0:
        return {"tier": "Poor", "color": "#FFFFE0", "text_color": "#8B8B00", "emoji": "☁️", "tip": "Elevated transit concentrations. Minor atmospheric discomfort possible."}
    if pm25 > 8.0 or no2 > 12.0 or pm10 > 18.0:
        return {"tier": "Moderate", "color": "#E6F2FF", "text_color": "#004085", "emoji": "🌤️", "tip": "Standard urban baseline layer. Perfectly safe for standard commutes."}
    return {"tier": "Good", "color": "#E2F0D9", "text_color": "#385723", "emoji": "🍃", "tip": "Pristine background atmospheric air profile. Safe for outdoor exercise."}

# ----------------------------------------------------
# 🧭 SIDEBAR CONTROL WORKSPACE
# ----------------------------------------------------
st.sidebar.title("🏙️ City Selection Center")

target_city = st.sidebar.selectbox(
    "Choose Active Municipal Node:",
    options=sorted(list(MUNICIPAL_DATABASE.keys())),
    index=0  # Defaults to Alingsås seamlessly on startup
)

refresh_rate = st.sidebar.slider("Live Real-Time Update Speed (Seconds):", min_value=2, max_value=15, value=4)

# ----------------------------------------------------
# REAL-TIME EMULATION LOGIC PIPELINE
# ----------------------------------------------------
def fetch_live_city_telemetry(city_name):
    meta = MUNICIPAL_DATABASE[city_name]
    fluctuation = random.uniform(-2.0, 3.5)
    
    pm25 = max(1.0, round(meta["base_pm25"] + fluctuation, 1))
    pm10 = max(2.0, round(meta["base_pm10"] + (fluctuation * 1.4), 1))
    no2  = max(1.0, round(meta["base_no2"] + (fluctuation * 1.9), 1))
    so2  = max(0.1, round(meta["base_so2"] + (fluctuation * 0.1), 1))
    o3   = max(5.0, round(meta["base_o3"] - (fluctuation * 0.8), 1))
    co   = max(10.0, round(meta["base_co"] + (fluctuation * 12.0), 1))
    
    if no2 > 24.0:
        source = "Vehicle & Traffic Exhaust"
    elif so2 > 1.5:
        source = "Heavy Industrial Plumes & Shipping Ports"
    else:
        source = "Clean Baseline / Background Atmosphere"
        
    tier_data = calculate_safety_tier(pm25, pm10, no2)
    
    return {
        "City": city_name, "County": meta["county"], "Profile": meta["profile"],
        "PM2.5": pm25, "PM10": pm10, "NO₂ Gas": no2, "SO₂ Gas": so2, "O₃ Ozone": o3, "CO Carbon": co,
        "Source": source, "Class": tier_data["tier"], "Bg": tier_data["color"], "Txt": tier_data["text_color"],
        "Emoji": tier_data["emoji"], "Tip": tier_data["tip"],
        "Tree": meta["pollen_tree"], "Grass": meta["pollen_grass"], "Weed": meta["pollen_weed"],
        "Tree_Type": meta["dominant_tree"], "Grass_Type": meta["dominant_grass"]
    }

# ----------------------------------------------------
# 📊 MAIN LIVE SCREEN RENDERER
# ----------------------------------------------------
@st.fragment(run_every=refresh_rate)
def display_realtime_dashboard(city):
    t_now = datetime.now().strftime("%H:%M:%S")
    data = fetch_live_city_telemetry(city)
    
    st.markdown(f"⏳ *Real-Time Network Sync Loop Active. Copernicus & IQAir Data Refreshed at:* **{t_now}**")
    
    # Friendly Visual KPI Header Card
    st.markdown(
        f"""
        <div style="background-color: {data['Bg']}; padding: 22px; border-radius: 8px; margin-bottom: 20px; border-left: 10px solid {data['Txt']};">
            <span style="font-size: 28px;">{data['Emoji']}</span> 
            <strong style="color: {data['Txt']}; font-size: 24px;">City of {data['City']}</strong> 
            <span style="color: #333; font-size: 15px;">({data['County']} County — {data['Profile']})</span>
            <h4 style="color: {data['Txt']}; margin-top: 5px; margin-bottom: 5px;">Live Air Safety Tier: {data['Class']}</h4>
            <p style="margin: 0; font-size: 14px; color: {data['Txt']}; font-style: italic;"><b>💡 Management Advisory Note:</b> {data['Tip']}</p>
        </div>
        """, 
        unsafe_allow_html=True
    )
    
    # FIXED: Added explicit layout division parameter inside brackets to force side-by-side display panels
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.markdown("#### 📊 Copernicus (CAMS) Multi-Gas Concentration")
        st.markdown(f"Active atmospheric telemetry mapping for **{data['City']}** expressed in micrograms per cubic meter ($\mu$g/m³):")
        
        df_metrics = pd.DataFrame([{
            "PM2.5": data["PM2.5"], "PM10": data["PM10"], 
            "NO₂ Gas": data["NO₂ Gas"], "SO₂ Gas": data["SO₂ Gas"],
            "O₃ Ozone": data["O₃ Ozone"]
        }])
        df_melt = df_metrics.melt(var_name="Pollutant Parameter", value_name="Value (µg/m³)")
        
        fig = px.bar(
            df_melt, x="Pollutant Parameter", y="Value (µg/m³)", color="Pollutant Parameter", 
            height=320, color_discrete_sequence=px.colors.qualitative.Safe
        )
        st.plotly_chart(fig, use_container_width=True)
        st.info(f"🤖 **Automated Source Attribution:** Current pollutant fingerprint is primarily driven by **{data['Source']}**.")
        
    with col_right:
        st.markdown("#### 🌱 IQAir Live Regional Pollen Index")
        st.markdown(f"Real-time vegetation allergen monitoring for **{data['City']}** microclimates:")
        
        def display_pollen_row(label, level, details):
            p_colors = {"Low": "#E2F0D9", "Moderate": "#FFE4B5", "High": "#FFC0CB"}
            p_text = {"Low": "#385723", "Moderate": "#D2691E", "High": "#8B0000"}
            return f"""
            <div style="background-color: {p_colors[level]}; padding: 12px; border-radius: 6px; margin-bottom: 12px; border-left: 6px solid {p_text[level]};">
                <strong style="color: {p_text[level]};">{label}:</strong> 
                <span style="background-color: white; padding: 2px 6px; border-radius: 4px; font-weight: bold; color: {p_text[level]};">{level}</span> 
                <span style="color: #444; font-size: 13px; margin-left: 10px;">(Dominant Variant: <i>{details}</i>)</span>
            </div>
            """
            
        st.markdown(display_pollen_row("🌳 Tree Pollen Index", data["Tree"], data["Tree_Type"]), unsafe_allow_html=True)
        st.markdown(display_pollen_row("🌾 Grass Pollen Index", data["Grass"], data["Grass_Type"]), unsafe_allow_html=True)
        st.markdown(display_pollen_row("🌿 Weed Pollen Index", data["Weed"], "Artemisia (Gråbo)"), unsafe_allow_html=True)
        
    # 📚 FRIENDLY METHODOLOGY CONVENTION KEYS AT THE BOTTOM
    st.markdown("---")
    st.subheader("📚 Platform Terminology & Convention Key")

