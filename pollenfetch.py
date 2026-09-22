import streamlit as st
import requests
import pandas as pd

BASE_URL = "https://api.pollenrapporten.se/v1"

st.set_page_config(page_title="Pollenrapporten Forecast", page_icon="🌿", layout="wide")

# --- Cached API Calls ---

@st.cache_data(ttl=3600)
def fetch_pollen_types():
    """Fetch pollen definitions to map pollen IDs to human-readable names."""
    try:
        response = requests.get(f"{BASE_URL}/pollen-types", timeout=10)
        response.raise_for_status()
        items = response.json().get("items", [])
        return {item["id"]: item.get("name", item["id"]) for item in items}
    except requests.RequestException:
        return {}

@st.cache_data(ttl=3600)
def fetch_regions():
    """Fetch all available monitoring regions."""
    try:
        response = requests.get(f"{BASE_URL}/regions", timeout=10)
        response.raise_for_status()
        return response.json().get("items", [])
    except requests.RequestException as e:
        st.error(f"Failed to load regions: {e}")
        return []

def fetch_forecast(region_id):
    """Fetch the latest active forecast for a chosen region."""
    params = {"region_id": region_id, "current": "true"}
    try:
        response = requests.get(f"{BASE_URL}/forecasts", params=params, timeout=10)
        response.raise_for_status()
        return response.json().get("items", [])
    except requests.RequestException as e:
        st.error(f"Failed to load forecast: {e}")
        return []

# --- UI Setup ---

st.title("🌿 Swedish Pollen Forecast")
st.caption("Live data sourced from [pollenrapporten.se](https://api.pollenrapporten.se/docs)")

regions = fetch_regions()
pollen_map = fetch_pollen_types()

if not regions:
    st.warning("No region data available at the moment.")
    st.stop()

# Sort regions alphabetically
regions_sorted = sorted(regions, key=lambda x: x.get("name", ""))
region_names = [r["name"] for r in regions_sorted]

# Select Region
selected_name = st.selectbox("Select a region:", region_names, index=0)
selected_region = next(r for r in regions_sorted if r["name"] == selected_name)

# --- Data Display ---

with st.spinner(f"Loading forecast for {selected_name}..."):
    forecasts = fetch_forecast(selected_region["id"])

if not forecasts:
    st.info(f"No active forecast published for {selected_name}.")
else:
    for forecast in forecasts:
        start = forecast.get("startDate", "N/A")
        end = forecast.get("endDate", "N/A")
        desc = forecast.get("description", "")
        
        st.subheader(f"Forecast Period: {start} to {end}")
        if desc:
            st.info(desc)

        level_series = forecast.get("levelSeries", [])
        
        if not level_series:
            st.write("No granular daily level data found in this forecast.")
            continue

        # Flatten records for DataFrame display
        rows = []
        for entry in level_series:
            p_id = entry.get("pollenId")
            p_name = pollen_map.get(p_id, p_id)
            rows.append({
                "Date": entry.get("date"),
                "Pollen Type": p_name,
                "Predicted Level": entry.get("value")
            })

        df = pd.DataFrame(rows)
        
        # Display as a pivot table: Dates as columns, Pollen Types as rows
        pivot_df = df.pivot_table(
            index="Pollen Type", 
            columns="Date", 
            values="Predicted Level", 
            aggfunc="first"
        ).fillna("-")

        st.dataframe(pivot_df, use_container_width=True)

        # Region coordinates
        lat = selected_region.get("latitude")
        lon = selected_region.get("longitude")
        if lat and lon:
            with st.expander("📍 View Station Location"):
                st.map(pd.DataFrame([{"lat": lat, "lon": lon}]))