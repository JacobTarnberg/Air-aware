import unicodedata

STATUS_CONFIG = {
    0: {"label": "Good", "short_label": "Good", "color": "#22C55E", "icon": "✅", "message": "Conditions are suitable for most people."},
    1: {"label": "Moderate", "short_label": "Moderate", "color": "#EAB308", "icon": "ℹ️", "message": "Conditions are generally acceptable."},
    2: {"label": "Dangerous for sensitive people", "short_label": "Sensitive groups: caution", "color": "#F97316", "icon": "⚠️", "message": "Sensitive people may experience effects."},
    3: {"label": "Poor", "short_label": "Poor", "color": "#EF4444", "icon": "⛔", "message": "Health effects are possible. Consider precautions."},
    4: {"label": "Hazardous", "short_label": "Hazardous", "color": "#7C3AED", "icon": "🚫", "message": "Serious conditions. Strong precautions are advised."},
    None: {"label": "Unavailable", "short_label": "Unavailable", "color": "#64748B", "icon": "❓", "message": "There is not enough data for an assessment."},
}

def get_status_config(severity): return STATUS_CONFIG.get(severity, STATUS_CONFIG[None]).copy()

def safe_number(value):
    try: return None if value is None else float(value)
    except (TypeError, ValueError): return None

def categorize_by_thresholds(value, thresholds):
    value = safe_number(value)
    if value is None: return None
    for severity, limit in enumerate(thresholds):
        if value <= limit: return severity
    return 4

def get_worst_result(items):
    available = {k: v for k, v in items.items() if v is not None}
    if not available: return {"severity": None, "causes": []}
    severity = max(available.values())
    return {"severity": severity, "causes": [k for k, v in available.items() if v == severity]}

def describe_group_result(result):
    answer = dict(result); answer.update(get_status_config(result.get("severity"))); return answer

EUROPEAN_AQI_THRESHOLDS = [20, 40, 60, 100]
PARTICLE_THRESHOLDS = {"pm2_5": [5, 15, 50, 140], "pm10": [15, 45, 120, 270]}
GAS_THRESHOLDS = {"nitrogen_dioxide": [10, 25, 60, 150], "ozone": [60, 100, 120, 180], "sulphur_dioxide": [20, 40, 125, 275]}

def _prefer_aqi(data, raw_key, aqi_key, raw_thresholds):
    if data.get(aqi_key) is not None: return categorize_by_thresholds(data[aqi_key], EUROPEAN_AQI_THRESHOLDS)
    return categorize_by_thresholds(data.get(raw_key), raw_thresholds)

def evaluate_air_quality(data):
    data = data or {}
    items = {
        "PM2.5": _prefer_aqi(data, "pm2_5", "european_aqi_pm2_5", PARTICLE_THRESHOLDS["pm2_5"]),
        "PM10": _prefer_aqi(data, "pm10", "european_aqi_pm10", PARTICLE_THRESHOLDS["pm10"]),
    }
    result = get_worst_result(items); result["items"] = items; return result

def evaluate_gases(data, selected_gases=None):
    data = data or {}; selected = {str(x).upper().replace("₂", "2").replace("₃", "3") for x in selected_gases} if selected_gases else {"NO2", "O3", "SO2", "CO"}; items = {}
    specs = {"NO2": ("NO₂", "nitrogen_dioxide", "european_aqi_nitrogen_dioxide"), "O3": ("O₃", "ozone", "european_aqi_ozone"), "SO2": ("SO₂", "sulphur_dioxide", "european_aqi_sulphur_dioxide")}
    for key, (label, raw, aqi) in specs.items():
        if key in selected: items[label] = _prefer_aqi(data, raw, aqi, GAS_THRESHOLDS[raw])
    if "CO" in selected: items["CO"] = categorize_by_thresholds(data.get("us_aqi_carbon_monoxide"), [50, 100, 150, 300])
    result = get_worst_result(items); result["items"] = items; return result

def normalize_text(value):
    text = unicodedata.normalize("NFKD", str(value or "")).encode("ascii", "ignore").decode().lower()
    return " ".join(text.replace("_", " ").replace("-", " ").split())

def categorize_pollen_level(level):
    return {"none": 0, "none detected": 0, "inga halter": 0, "low": 1, "laga halter": 1, "moderate": 2, "mattliga halter": 2, "low to moderate": 2, "laga till mattliga halter": 2, "high": 3, "hoga halter": 3, "moderate to high": 3, "mattliga till hoga halter": 3, "very high": 4, "mycket hoga halter": 4, "high to very high": 4}.get(normalize_text(level))

POLLEN_GROUPS = {
    "tree": {"al", "alm", "bjork", "bok", "ek", "hassel", "salix", "salg", "vide", "birch", "tree", "alder", "hazel", "oak", "elm"},
    "grass": {"gras", "grass"}, "weed": {"grabo", "ambrosia", "mugwort", "ragweed", "weed"},
}

def get_pollen_group(name):
    text = normalize_text(name)
    for group, words in POLLEN_GROUPS.items():
        if any(word in text for word in words): return group
    return "other"

def evaluate_pollen(records, selected_groups=None, selected_pollen_types=None):
    groups = {normalize_text(x) for x in selected_groups} if selected_groups else None
    types = {normalize_text(x) for x in selected_pollen_types} if selected_pollen_types else None
    items = {}
    for row in records or []:
        name = str(row.get("name", "Unknown pollen"))
        if types and normalize_text(name) not in types: continue
        if not types and groups and get_pollen_group(name) not in groups: continue
        items[name] = categorize_pollen_level(row.get("level"))
    result = get_worst_result(items); result["items"] = items; return result

def categorize_humidity(humidity, temperature=None):
    humidity, temperature = safe_number(humidity), safe_number(temperature)
    if humidity is None or not 0 <= humidity <= 100: return None
    if temperature is not None and temperature >= 30 and humidity >= 80: return 3
    if temperature is not None and temperature >= 25 and humidity >= 70: return 2
    if humidity < 30: return 1
    if humidity <= 60: return 0
    if humidity <= 80: return 1
    return 2

def get_humidity_description(value):
    value = safe_number(value)
    if value is None or not 0 <= value <= 100: return "Unavailable"
    return "Dry" if value < 30 else "Comfortable" if value <= 60 else "Humid" if value <= 80 else "Very humid"

def get_wind_direction(value):
    value = safe_number(value)
    if value is None or not 0 <= value <= 360: return "Unavailable"
    return ["North", "North-east", "East", "South-east", "South", "South-west", "West", "North-west"][round(value / 45) % 8]

def evaluate_weather(data, selected_weather=None):
    data = data or {}; selected = {str(x).lower() for x in selected_weather} if selected_weather else {"wind", "precipitation", "humidity"}; items = {}
    if "wind" in selected: items["Wind"] = categorize_by_thresholds(data.get("wind_speed"), [5, 8, 13, 21])
    if "precipitation" in selected: items["Precipitation"] = categorize_by_thresholds(data.get("precipitation"), [0.2, 1, 3, 10])
    if "humidity" in selected: items["Humidity"] = categorize_humidity(data.get("humidity"), data.get("temperature"))
    result = get_worst_result(items)
    result.update({"items": items, "wind_direction": get_wind_direction(data.get("wind_direction")), "humidity_description": get_humidity_description(data.get("humidity"))})
    return result

ALL_CATEGORIES = ["air_quality", "gases", "pollen", "weather"]

def normalize_category_selection(selected):
    if not selected: return ALL_CATEGORIES.copy()
    aliases = {"air quality": "air_quality", "air_quality": "air_quality", "particles": "air_quality", "gases": "gases", "gas": "gases", "pollen": "pollen", "weather": "weather", "weather conditions": "weather"}
    result = []
    for item in selected:
        category = aliases.get(normalize_text(item))
        if category and category not in result: result.append(category)
    return result

def evaluate_overall_conditions(air_data=None, pollen_records=None, weather_data=None, selected_categories=None, selected_gases=None, selected_pollen_groups=None, selected_pollen_types=None, selected_weather=None):
    categories = normalize_category_selection(selected_categories); groups = {}
    if "air_quality" in categories: groups["Air quality"] = evaluate_air_quality(air_data)
    if "gases" in categories: groups["Gases"] = evaluate_gases(air_data, selected_gases)
    if "pollen" in categories: groups["Pollen"] = evaluate_pollen(pollen_records, selected_pollen_groups, selected_pollen_types)
    if "weather" in categories: groups["Weather"] = evaluate_weather(weather_data, selected_weather)
    items = {name: group.get("severity") for name, group in groups.items()}
    result = get_worst_result(items); result.update({"items": items, "groups": groups, "selected_categories": categories}); return result

def describe_overall_conditions(**kwargs): return describe_group_result(evaluate_overall_conditions(**kwargs))

def get_personalized_advice(result):
    causes, severity = result.get("causes", []), result.get("severity")
    if "Pollen" in causes: return "Keep your allergy medication or inhaler nearby and monitor your symptoms."
    if "Gases" in causes or "Air quality" in causes: return "Consider a quieter route away from heavy traffic, especially during rush hour."
    if "Weather" in causes: return "Adjust the timing, clothing or intensity of your plans." if severity is not None and severity >= 2 else "Weather conditions look suitable for a walk or outdoor activity."
    if severity == 0: return "It looks like a good time to go outside."
    if severity is None: return "Some information is unavailable, so check again before leaving."
    return "Pay attention to how you feel and adjust your outdoor plans if needed."
