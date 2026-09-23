import streamlit as st

from sample_data_jonnamada import air_data, pollen_data
from recommendations import get_recommendation, get_pollen_status

result = get_recommendation(air_data, pollen_data)
pollen_status = get_pollen_status(pollen_data)

st.set_page_config(
    page_title="Air Aware",
    page_icon="🌿",
    layout="centered"
)

st.title("Air Aware")
st.caption("Understand the air before you go outside")

location = st.selectbox("Location", ["Gothenburg"])

st.info("Prototype currently displaying sample data.")

st.header(result["title"])
st.write(result["message"])

air_column, pollen_column = st.columns(2)

with air_column:
    st.subheader("Air quality")
    st.write(air_data["status"].title())

with pollen_column:
    st.subheader("Pollen")
    st.write(pollen_status.replace("_", " ").title())

st.subheader("Pollen details")

tree, grass, weed = st.columns(3)
tree.metric("Tree", pollen_data["tree"].title())
grass.metric("Grass", pollen_data["grass"].title())
weed.metric("Weed", pollen_data["weed"].title())

def display_value(value, unit=""):
    if value is None:
        return "Unavailable"

    return f"{value} {unit}".strip()

st.metric(
    "PM2.5",
    display_value(air_data.get("pm25"), "µg/m³")
)

st.metric(
    "PM10",
    display_value(air_data.get("pm10"), "µg/m³")
)

st.metric(
    "NO₂",
    display_value(air_data.get("no2"), "µg/m³")
)