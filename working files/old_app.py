import os
import random
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# ----------------------------------------------------
# Page Configuration
# ----------------------------------------------------
st.set_page_config(
    page_title="Sweden National Air Quality Platform",
    page_icon="🇸🇪",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("🇸🇪 Air-Aware Sweden: National Real-Time Monitoring Platform")
st.markdown("### Digitalt ledarskap projekt — Dynamic Source Mapping & Live Safety Matrix")

# ----------------------------------------------------
# 🪐 DATABASE DICTIONARIES & LISTS
# ----------------------------------------------------
SWEDISH_REGIONS = [
    "Blekinge", "Dalarna", "Gotland", "Gävleborg", "Halland", 
    "Jämtland", "Jönköping", "Kalmar", "Kronoberg", "Norrbotten", 
    "Skåne", "Stockholm", "Södermanland", "Uppsala", "Värmland", 
    "Västerbotten", "Västernorrland", "Västmanland", "Västra Götaland", 
    "Örebro", "Östergötland"
]

SWEDISH_MUNICIPALITIES = [
    "Gothenburg", "Alingsås", "Stockholm City", "Malmö", "Uppsala City", "Kiruna", "Borås", "Lund"
]

# ----------------------------------------------------
# 🧭 SIDEBAR PLATFORM ROUTER
# ----------------------------------------------------
st.sidebar.title("🧭 Platform Control Room")
view_mode = st.sidebar.radio(
    "Select Platform Module View:",
    ["📊 All-Sweden Regional Matrix", "🏙️ Specific Municipal Cities"]
)

refresh_rate = st.sidebar.slider("Live Update Refresh Rate (Seconds):", min_value=2, max_value=15, value=4)

# ----------------------------------------------------
# 🔬 HEALTH SAFETY TIERS
# ----------------------------------------------------
def calculate_safety_tier(pm25, pm10, no2):
    if pm25 > 50.0 or no2 > 80.0 or pm10 > 100.0:
        return {"tier": "Hazardous / Dangerous", "color": "#FFC0CB", "text_color": "#8B0000", "emoji": "🛑", "tip": "Wear masks. Avoid heavy outdoor physical stress."}
    if pm25 > 25.0 or no2 > 40.0 or pm10 > 50.0:
        return {"tier": "Dangerous for Sensitive Groups", "color": "#FFE4B5", "text_color": "#D2691E", "emoji": "⚠️", "tip": "Asthma risk. Sensitive individuals should stay indoors."}
    if pm25 > 15.0 or no2 > 25.0 or pm10 > 35.0:
        return {"tier": "Poor", "color": "#FFFFE0", "text_color": "#8B8B00", "emoji": "☁️", "tip": "Trace pollutants detected. Minor irritations possible."}
    if pm25 > 8.0 or no2 > 12.0 or pm10 > 18.0:
        return {"tier": "Moderate", "color": "#E6F2FF", "text_color": "#004085", "emoji": "🌤️", "tip": "Standard urban baseline atmospheric layer. Safe for standard travel."}
    return {"tier": "Good", "color": "#E2F0D9", "text_color": "#385723", "emoji": "🍃", "tip": "Excellent pristine conditions! Perfectly clean air."}

# ----------------------------------------------------
# DATA PIPELINE MATRIX
# ----------------------------------------------------
def generate_live_dataframe(target_locations, timestamp_str):
    rows = []
    for loc in target_locations:
        if loc in ["Stockholm", "Västra Götaland", "Skåne", "Gothenburg", "Stockholm City", "Malmö"]:
            pm25 = round(random.uniform(9.0, 24.0), 1)
            pm10 = round(random.uniform(16.0, 38.0), 1)
            no2  = round(random.uniform(25.0, 44.0), 1)
            so2  = round(random.uniform(0.4, 1.1), 1)
            source = "Vehicle & Traffic Exhaust"
        elif loc in ["Norrbotten", "Gävleborg", "Kiruna"]:
            pm25 = round(random.uniform(6.0, 16.0), 1)
            pm10 = round(random.uniform(18.0, 45.0), 1)
            no2  = round(random.uniform(8.0, 18.0), 1)
            so2  = round(random.uniform(2.2, 4.0), 1)
            source = "Heavy Industry & Shipping Ports"
        elif loc in ["Alingsås", "Lund", "Borås"] and random.choice([True, False]):
            pm25 = round(random.uniform(3.0, 12.0), 1)
            pm10 = round(random.uniform(7.0, 20.0), 1)
            no2  = round(random.uniform(4.0, 15.0), 1)
            so2  = round(random.uniform(0.1, 0.4), 1)
            source = "Residential Wood Heating / Biomass"
        else:
            pm25 = round(random.uniform(1.5, 7.5), 1)
            pm10 = round(random.uniform(3.0, 14.0), 1)
            no2  = round(random.uniform(2.0, 11.0), 1)
            so2  = round(random.uniform(0.1, 0.5), 1)
            source = "Baseline / Background Atmosphere"
            
        tier_data = calculate_safety_tier(pm25, pm10, no2)
        
        rows.append({
            "Timestamp": timestamp_str,
            "Location": loc,
            "PM2.5 (µg/m³)": pm25,
            "PM10 (µg/m³)": pm10,
            "NO₂ Gas (µg/m³)": no2,
            "SO₂ Gas (µg/m³)": so2,
            "Primary Source Profile": source,
            "Safety Classification": tier_data["tier"],
            "UI_Color": tier_data["color"],
            "UI_Text": tier_data["text_color"],
            "UI_Emoji": tier_data["emoji"],
            "Health Advisory": tier_data["tip"]
        })
    return pd.DataFrame(rows)

# ----------------------------------------------------
# RENDERING PANEL LOOPS
# ----------------------------------------------------
current_time = datetime.now().strftime("%H:%M:%S")

if view_mode == "📊 All-Sweden Regional Matrix":
    st.sidebar.markdown("---")
    st.sidebar.subheader("🇸🇪 Regional View Filters")
    
    selected_regions = st.sidebar.multiselect(
        "Isolate Specific Counties (Län):",
        options=sorted(SWEDISH_REGIONS),
        default=["Stockholm", "Västra Götaland", "Skåne", "Uppsala", "Norrbotten"],
        key="regions_filter"
    )
    
    @st.fragment(run_every=refresh_rate)
    def render_regional_matrix(locations):
        t_now = datetime.now().strftime("%H:%M:%S")
        df_live = generate_live_dataframe(SWEDISH_REGIONS, t_now)
        st.markdown(f"⏳ *Auto-updating regional grid live. Sync time:* **{t_now}**")
        
        filtered_df = df_live[df_live["Location"].isin(locations)]
        if not filtered_df.empty:
            chart_data = filtered_df.melt(id_vars=["Location"], value_vars=["PM2.5 (µg/m³)", "PM10 (µg/m³)", "NO₂ Gas (µg/m³)", "SO₂ Gas (µg/m³)"], var_name="Pollutant", value_name="Concentration")
            fig = px.bar(chart_data, x="Location", y="Concentration", color="Pollutant", barmode="group", height=420, color_discrete_sequence=px.colors.qualitative.Safe)
            st.plotly_chart(fig, use_container_width=True)
            
            for idx, row in filtered_df.iterrows():
                st.markdown(f"""<div style="background-color: {row['UI_Color']}; padding: 15px; border-radius: 8px; margin-bottom: 10px; border-left: 8px solid {row['UI_Text']};"><span style="font-size: 20px;">{row['UI_Emoji']}</span> <strong style="color: {row['UI_Text']}; font-size: 16px;">{row['Location']} Region</strong> — Status: <span style="font-weight: bold; color: {row['UI_Text']};">{row['Safety Classification']}</span> | <u>Driver:</u> <b>{row['Primary Source Profile']}</b><br><small>📊 PM2.5: {row['PM2.5 (µg/m³)']} | PM10: {row['PM10 (µg/m³)']} | NO₂: {row['NO₂ Gas (µg/m³)']}</small></div>""", unsafe_allow_html=True)
    
    render_regional_matrix(selected_regions)

else:
    st.sidebar.markdown("---")
    st.sidebar.subheader("🏙️ City View Filters")
    
    selected_cities = st.sidebar.multiselect(
        "Isolate Specific Municipal Cities:",
        options=sorted(SWEDISH_MUNICIPALITIES),
        default=["Gothenburg", "Alingsås", "Stockholm City"],
        key="cities_filter"
    )
    
    @st.fragment(run_every=refresh_rate)
    def render_municipal_matrix(locations):
        t_now = datetime.now().strftime("%H:%M:%S")
        df_live = generate_live_dataframe(SWEDISH_MUNICIPALITIES, t_now)
        st.markdown(f"⏳ *Auto-updating municipal grid live. Sync time:* **{t_now}**")
        
        filtered_df = df_live[df_live["Location"].isin(locations)]
        if not filtered_df.empty:
            chart_data = filtered_df.melt(id_vars=["Location"], value_vars=["PM2.5 (µg/m³)", "PM10 (µg/m³)", "NO₂ Gas (µg/m³)", "SO₂ Gas (µg/m³)"], var_name="Pollutant", value_name="Concentration")
            fig = px.bar(chart_data, x="Location", y="Concentration", color="Pollutant", barmode="group", height=420, color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig, use_container_width=True)
            
            for idx, row in filtered_df.iterrows():
                st.markdown(f"""<div style="background-color: {row['UI_Color']}; padding: 15px; border-radius: 8px; margin-bottom: 10px; border-left: 8px solid {row['UI_Text']};"><span style="font-size: 20px;">{row['UI_Emoji']}</span> <strong style="color: {row['UI_Text']}; font-size: 16px;">City of {row['Location']}</strong> — Status: <span style="font-weight: bold; color: {row['UI_Text']};">{row['Safety Classification']}</span> | <u>Driver:</u> <b>{row['Primary Source Profile']}</b><br><small>📊 PM2.5: {row['PM2.5 (µg/m³)']} | PM10: {row['PM10 (µg/m³)']} | NO₂: {row['NO₂ Gas (µg/m³)']}</small></div>""", unsafe_allow_html=True)

    render_municipal_matrix(selected_cities)

# Glossary
st.markdown("---")
st.subheader("📚 Platform Environmental Tier Glossary")
g1, g2, g3, g4, g5 = st.columns(5)
g1.markdown("<div style='background-color:#E2F0D9; padding:10px; border-radius:5px; text-align:center; color:#385723; font-weight:bold;'>🍃 Good</div>", unsafe_allow_html=True)
g2.markdown("<div style='background-color:#E6F2FF; padding:10px; border-radius:5px; text-align:center; color:#004085; font-weight:bold;'>🌤️ Moderate</div>", unsafe_allow_html=True)
g3.markdown("<div style='background-color:#FFFFE0; padding:10px; border-radius:5px; text-align:center; color:#8B8B00; font-weight:bold;'>☁️ Poor</div>", unsafe_allow_html=True)
g4.markdown("<div style='background-color:#FFE4B5; padding:10px; border-radius:5px; text-align:center; color:#D2691E; font-weight:bold;'>⚠️ Sensitive Groups</div>", unsafe_allow_html=True)
