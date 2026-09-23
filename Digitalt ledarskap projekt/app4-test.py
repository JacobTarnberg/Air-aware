import time

import pandas as pd

import plotly.express as px

import pydeck as pdk

import requests

import streamlit as st
 
st.set_page_config(

    page_title="Sweden Air Quality Dashboard",

    page_icon="🇸🇪",

    layout="wide",

)
 
# --- Locations Dictionary ---

LOCATIONS = {

    # Västra Götaland

    "Alingsås": (57.9303, 12.5335),

    "Bengtsfors": (58.9974, 12.2324),

    "Borås": (57.7210, 12.9401),

    "Falköping": (58.1735, 13.5507),

    "Göteborg": (57.7089, 11.9746),

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

    # Halland

    "Falkenberg": (56.9055, 12.4912),

    "Halmstad": (56.6745, 12.8578),

    "Kungsbacka": (57.4872, 12.0761),

    "Laholm": (56.5126, 13.0437),

    "Varberg": (57.1056, 12.2508),

    # Skåne

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

    # Blekinge

    "Karlshamn": (56.1706, 14.8619),

    "Karlskrona": (56.1612, 15.5869),

    "Olofström": (56.2775, 14.5330),

    "Ronneby": (56.2090, 15.2760),

    "Sölvesborg": (56.0521, 14.5751),

    # Småland

    "Eksjö": (57.6664, 14.9720),

    "Gislaved": (57.3044, 13.5408),

    "Jönköping": (57.7826, 14.1618),

    "Ljungby": (56.8332, 13.9408),

    "Nässjö": (57.6531, 14.6968),

    "Tranås": (58.0372, 14.9784),

    "Värnamo": (57.1860, 14.0400),

    "Vetlanda": (57.4289, 15.0776),

    "Växjö": (56.8790, 14.8059),

    # Öland / Kalmar län

    "Borgholm": (56.8793, 16.6560),

    "Emmaboda": (56.6328, 15.5374),

    "Kalmar": (56.6634, 16.3568),

    "Mönsterås": (57.0417, 16.4430),

    "Oskarshamn": (57.2646, 16.4484),

    "Vimmerby": (57.6659, 15.8552),

    "Västervik": (57.7584, 16.6373),

    # Östergötland

    "Finspång": (58.7058, 15.7674),

    "Linköping": (58.4108, 15.6214),

    "Mjölby": (58.3259, 15.1250),

    "Motala": (58.5371, 15.0365),

    "Norrköping": (58.5877, 16.1924),

    "Söderköping": (58.4806, 16.3222),

    "Vadstena": (58.4486, 14.8897),

    # Södermanland

    "Eskilstuna": (59.3710, 16.5098),

    "Katrineholm": (58.9958, 16.2072),

    "Nyköping": (58.7530, 17.0079),

    "Oxelösund": (58.6706, 17.1017),

    "Strängnäs": (59.3774, 17.0312),

    # Stockholm

    "Stockholm": (59.3293, 18.0686),

    "Norrtälje": (59.7580, 18.7050),

    "Nynäshamn": (58.9034, 17.9479),

    "Märsta": (59.6216, 17.8548),

    "Sollentuna": (59.4280, 17.9509),

    "Södertälje": (59.1955, 17.6253),

    "Täby": (59.4439, 18.0687),

    "Upplands Väsby": (59.5184, 17.9113),

    "Vallentuna": (59.5344, 18.0776),

    "Åkersberga": (59.4794, 18.2997),

    # Uppsala län

    "Enköping": (59.6361, 17.0777),

    "Uppsala": (59.8586, 17.6389),

    "Östhammar": (60.2596, 18.3741),

    # Västmanland

    "Arboga": (59.3939, 15.8388),

    "Fagersta": (59.9913, 15.7930),

    "Köping": (59.5140, 15.9926),

    "Sala": (59.9199, 16.6066),

    "Västerås": (59.6099, 16.5448),

    # Örebro län

    "Hallsberg": (59.0642, 15.1103),

    "Kumla": (59.1278, 15.1435),

    "Lindesberg": (59.5920, 15.2304),

    "Nora": (59.5193, 15.0396),

    "Örebro": (59.2753, 15.2134),

    # Värmland

    "Arvika": (59.6553, 12.5852),

    "Filipstad": (59.7124, 14.1683),

    "Hagfors": (60.0234, 13.6721),

    "Karlstad": (59.3793, 13.5036),

    "Kristinehamn": (59.3098, 14.1081),

    "Säffle": (59.1323, 12.9287),

    # Dalarna

    "Avesta": (60.1454, 16.1679),

    "Borlänge": (60.4858, 15.4371),

    "Falun": (60.6065, 15.6355),

    "Hedemora": (60.2797, 15.9886),

    "Ludvika": (60.1496, 15.1878),

    "Mora": (61.0040, 14.5370),

    "Säter": (60.3478, 15.7500),

    "Älvdalen": (61.2277, 14.0393),

    # Gävleborg

    "Bollnäs": (61.3482, 16.3946),

    "Gävle": (60.6749, 17.1413),

    "Hudiksvall": (61.7274, 17.1056),

    "Ljusdal": (61.8288, 16.0918),

    "Sandviken": (60.6186, 16.7758),

    "Söderhamn": (61.3037, 17.0592),

    # Jämtland

    "Åre": (63.3986, 13.0794),

    "Östersund": (63.1792, 14.6353),

    "Strömsund": (63.8521, 15.5558),

    # Västernorrland

    "Härnösand": (62.6323, 17.9379),

    "Kramfors": (62.9304, 17.7761),

    "Sollefteå": (63.1667, 17.2667),

    "Sundsvall": (62.3908, 17.3069),

    "Örnsköldsvik": (63.2909, 18.7153),

    # Västerbotten

    "Lycksele": (64.5954, 18.6735),

    "Skellefteå": (64.7507, 20.9528),

    "Storuman": (65.0959, 17.1173),

    "Umeå": (63.8258, 20.2630),

    "Vilhelmina": (64.6242, 16.6558),

    # Norrbotten

    "Arjeplog": (66.0517, 17.8861),

    "Arvidsjaur": (65.5903, 19.1668),

    "Boden": (65.8252, 21.6886),

    "Haparanda": (65.8355, 24.1347),

    "Jokkmokk": (66.6066, 19.8236),

    "Kalix": (65.8556, 23.1465),

    "Kiruna": (67.8558, 20.2253),

    "Luleå": (65.5848, 22.1547),

    "Piteå": (65.3172, 21.4794),

    # Gotland

    "Visby": (57.6348, 18.2948),

}
 
API_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"

BATCH_SIZE = 50
 
 
def get_aqi_color(aqi):

    """European AQI color bands [R, G, B, Alpha]."""

    if aqi <= 20:

        return [80, 240, 120, 180]    # Good: Green

    elif aqi <= 40:

        return [160, 230, 80, 180]    # Fair: Yellow-green

    elif aqi <= 60:

        return [255, 200, 50, 180]    # Moderate: Yellow

    elif aqi <= 80:

        return [255, 120, 50, 180]    # Poor: Orange

    elif aqi <= 100:

        return [240, 60, 60, 180]     # Very poor: Red

    return [150, 50, 180, 200]        # Extremely poor: Purple
 
 
@st.cache_data(ttl=1800, show_spinner=False)

def fetch_all_data(locations_dict):

    """Fetches and caches data from Open-Meteo for 30 minutes."""

    all_current = []

    all_hourly = []

    items = list(locations_dict.items())
 
    for i in range(0, len(items), BATCH_SIZE):

        batch = dict(items[i : i + BATCH_SIZE])

        names = list(batch.keys())

        lats = [str(coord[0]) for coord in batch.values()]

        lons = [str(coord[1]) for coord in batch.values()]
 
        params = {

            "latitude": ",".join(lats),

            "longitude": ",".join(lons),

            "current": [

                "european_aqi",

                "us_aqi",

                "pm10",

                "pm2_5",

                "nitrogen_dioxide",

                "ozone",

                "sulphur_dioxide",

            ],

            "hourly": ["pm2_5", "pm10", "nitrogen_dioxide", "ozone", "european_aqi"],

            "timezone": "Europe/Stockholm",

            "forecast_days": 2,

        }
 
        resp = requests.get(API_URL, params=params)

        resp.raise_for_status()

        payload = resp.json()

        data_list = payload if isinstance(payload, list) else [payload]
 
        for city, data in zip(names, data_list):

            curr = data.get("current", {})

            curr_row = {

                "city": city,

                "lat": data.get("latitude"),

                "lon": data.get("longitude"),

                **curr,

            }

            all_current.append(curr_row)
 
            hourly = data.get("hourly", {})

            if "time" in hourly:

                city_hourly = pd.DataFrame(hourly)

                city_hourly["city"] = city

                all_hourly.append(city_hourly)
 
        time.sleep(0.2)
 
    df_curr = pd.DataFrame(all_current)

    df_hour = pd.concat(all_hourly, ignore_index=True) if all_hourly else pd.DataFrame()

    return df_curr, df_hour
 
 
# --- Header & Refresh ---

col_title, col_btn = st.columns([5, 1])

with col_title:

    st.title("🇸🇪 Sweden Real-Time Air Quality Monitor")

    st.caption("Live and forecast atmospheric data via Open-Meteo & Copernicus Atmosphere Monitoring Service (CAMS)")

with col_btn:

    if st.button("🔄 Refresh Data", use_container_width=True):

        st.cache_data.clear()

        st.rerun()
 
with st.spinner("Fetching data for Swedish municipalities..."):

    df_current, df_hourly = fetch_all_data(LOCATIONS)
 
# Add visualization color column

df_current["color"] = df_current["european_aqi"].apply(get_aqi_color)
 
# --- Top Key Performance Indicators ---

kpi1, kpi2, kpi3, kpi4 = st.columns(4)

best_city = df_current.sort_values("european_aqi").iloc[0]

worst_city = df_current.sort_values("european_aqi", ascending=False).iloc[0]
 
kpi1.metric("Monitored Locations", len(df_current))

kpi2.metric("National Avg European AQI", f"{df_current['european_aqi'].mean():.1f}")

kpi3.metric("Cleanest Air", f"{best_city['city']}", f"AQI {best_city['european_aqi']}")

kpi4.metric("Highest Pollution", f"{worst_city['city']}", f"AQI {worst_city['european_aqi']}", delta_color="inverse")
 
# --- Interactive Map & Rankings ---

st.subheader("Geographic Air Quality Index (European Scale)")
 
layer = pdk.Layer(

    "ScatterplotLayer",

    data=df_current,

    get_position=["lon", "lat"],

    get_fill_color="color",

    get_radius=18000,

    pickable=True,

    auto_highlight=True,

)
 
view_state = pdk.ViewState(

    latitude=60.1282,

    longitude=16.6435,

    zoom=4.5,

    pitch=0,

)
 
map_col, table_col = st.columns([3, 2])
 
with map_col:

    st.pydeck_chart(

        pdk.Deck(

            layers=[layer],

            initial_view_state=view_state,

            tooltip={

                "html": "<b>{city}</b><br/>"

                "European AQI: <b>{european_aqi}</b><br/>"

                "PM2.5: {pm2_5} µg/m³<br/>"

                "PM10: {pm10} µg/m³<br/>"

                "NO₂: {nitrogen_dioxide} µg/m³",

                "style": {"color": "white", "backgroundColor": "rgba(20, 20, 20, 0.85)"},

            },

        )

    )
 
with table_col:

    st.markdown("**Leaderboard (Ranked by Pollutant Level)**")

    sort_metric = st.selectbox(

        "Sort By Metric:",

        ["european_aqi", "pm2_5", "pm10", "nitrogen_dioxide", "ozone"],

        index=0,

    )

    ranked_df = df_current[["city", "european_aqi", "pm2_5", "pm10", "nitrogen_dioxide", "ozone"]].sort_values(

        by=sort_metric, ascending=False

    )

    st.dataframe(ranked_df, use_container_width=True, height=450, hide_index=True)
 
# --- Detailed Forecast for a Selected City ---

st.divider()

st.subheader("Station Forecast Deep Dive")
 
selected_city = st.selectbox("Select a city to inspect 48-hour trends:", list(LOCATIONS.keys()), index=list(LOCATIONS.keys()).index("Göteborg"))
 
city_hourly_data = df_hourly[df_hourly["city"] == selected_city].copy()
 
if not city_hourly_data.empty:

    chart_metric = st.radio(

        "Select metric to chart:",

        ["european_aqi", "pm2_5", "pm10", "nitrogen_dioxide", "ozone"],

        horizontal=True,

    )
 
    fig = px.line(

        city_hourly_data,

        x="time",

        y=chart_metric,

        title=f"48-Hour {chart_metric.upper().replace('_', ' ')} Forecast for {selected_city}",

        labels={"time": "Date / Time (CET)", chart_metric: chart_metric.upper()},

        template="plotly_white",

    )

    fig.update_traces(line=dict(color="#1f77b4", width=2.5))

    st.plotly_chart(fig, use_container_width=True)
 
    with st.expander(f"View raw forecast data for {selected_city}"):

        st.dataframe(city_hourly_data, use_container_width=True)
 