import streamlit as st
import requests
from datetime import datetime


# --------------------------------------------------
# Page settings
# --------------------------------------------------

st.set_page_config(
    page_title="Air-aware",
    page_icon="🌤️"
)


# --------------------------------------------------
# Swedish cities and towns
# Coordinates: latitude, longitude
# --------------------------------------------------

locations = {

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

    # Uppsala County
    "Enköping": (59.6361, 17.0777),
    "Uppsala": (59.8586, 17.6389),
    "Östhammar": (60.2596, 18.3741),

    # Västmanland
    "Arboga": (59.3939, 15.8388),
    "Fagersta": (59.9913, 15.7930),
    "Köping": (59.5140, 15.9926),
    "Sala": (59.9199, 16.6066),
    "Västerås": (59.6099, 16.5448),

    # Örebro County
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


# --------------------------------------------------
# SMHI weather API
# --------------------------------------------------

@st.cache_data(ttl=600)
def get_weather(latitude, longitude):

    url = (
        "https://opendata-download-metfcst.smhi.se/api/"
        "category/snow1g/version/1/geotype/point/"
        f"lon/{longitude}/lat/{latitude}/data.json"
    )

    response = requests.get(
        url,
        timeout=10
    )

    response.raise_for_status()

    data = response.json()

    # Get first forecast time
    forecast = data["timeSeries"][0]

    # Get weather data
    weather = forecast["data"]

    return {
        "time": forecast["time"],
        "temperature": weather.get("air_temperature"),
        "wind_speed": weather.get("wind_speed"),
        "humidity": weather.get("relative_humidity"),
        "precipitation": weather.get("precipitation_amount_mean"),
        "cloudiness": weather.get("cloud_area_fraction"),
        "weather_symbol": weather.get("symbol_code")
    }


# --------------------------------------------------
# Interface
# --------------------------------------------------

st.title("🌤️ Air-aware")

st.write(
    "Select a city to see the latest "
    "available weather forecast from SMHI."
)


# --------------------------------------------------
# Searchable city selection
# --------------------------------------------------

city = st.selectbox(
    "📍 Search or select a city",
    options=sorted(locations.keys()),
    index=None,
    placeholder="Start typing a city name..."
)


# --------------------------------------------------
# Wait for city selection
# --------------------------------------------------

if city is None:

    st.info(
        "Type the beginning of a city name in the field above "
        "and then select a city."
    )

else:

    latitude, longitude = locations[city]

    try:

        weather = get_weather(
            latitude,
            longitude
        )

        # --------------------------------------------------
        # Forecast time
        # --------------------------------------------------

        forecast_time = datetime.fromisoformat(
            weather["time"].replace("Z", "+00:00")
        )

        st.subheader(f"🌤️ Weather in {city}")

        st.caption(
            "SMHI forecast time: "
            + forecast_time.strftime(
                "%Y-%m-%d %H:%M UTC"
            )
        )

        # --------------------------------------------------
        # Main weather information
        # --------------------------------------------------

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "🌡️ Temperature",
                f"{weather['temperature']} °C"
            )

        with col2:
            st.metric(
                "💨 Wind",
                f"{weather['wind_speed']} m/s"
            )

        with col3:
            st.metric(
                "💧 Humidity",
                f"{weather['humidity']} %"
            )

        # --------------------------------------------------
        # Additional weather information
        # --------------------------------------------------

        col4, col5 = st.columns(2)

        with col4:
            st.metric(
                "🌧️ Precipitation",
                f"{weather['precipitation']} mm"
            )

        with col5:
            st.metric(
                "☁️ Cloudiness",
                f"{weather['cloudiness']} %"
            )

        # --------------------------------------------------
        # Source
        # --------------------------------------------------

        st.divider()

        st.caption(
            "Source: SMHI – SNOW1g meteorological forecast"
        )

    except requests.RequestException as error:

        st.error(
            f"Could not retrieve weather data from SMHI: {error}"
        )

    except (
        KeyError,
        IndexError,
        TypeError,
        ValueError
    ) as error:

        st.error(
            f"An unexpected error occurred in SMHI's data: {error}"
        )