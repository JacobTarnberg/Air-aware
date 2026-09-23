STATUS_RANK = {"good": 0, "fair": 1, "moderate": 2, "poor": 3, "very_poor": 4, "unavailable": -1}


def safe_number(value):
    try:
        return None if value is None else float(value)
    except (TypeError, ValueError):
        return None


def get_air_status(aqi):
    value = safe_number(aqi)
    if value is None:
        return "unavailable"
    if value <= 20:
        return "good"
    if value <= 40:
        return "fair"
    if value <= 60:
        return "moderate"
    if value <= 80:
        return "poor"
    return "very_poor"


def pollen_level_to_status(level):
    value = safe_number(level)
    if value is None:
        return "unavailable"
    if value == 0:
        return "good"
    if value <= 2:
        return "moderate"
    if value <= 4:
        return "poor"
    return "very_poor"


def calculate_viability(aqi, temperature, wind_speed, precipitation, pollen_benchmark=None):
    score = 100
    reasons = []
    air_status = get_air_status(aqi)
    pollen_status = (pollen_benchmark or {}).get("status", "unavailable")
    score -= {"good": 0, "fair": 5, "moderate": 15, "poor": 30, "very_poor": 50, "unavailable": 0}[air_status]
    score -= {"good": 0, "fair": 5, "moderate": 10, "poor": 20, "very_poor": 30, "unavailable": 0}.get(pollen_status, 0)
    if air_status not in ("good", "unavailable"):
        reasons.append(f"Air quality is {air_status.replace('_', ' ')}")
    if pollen_status not in ("good", "unavailable"):
        reasons.append(f"Historical pollen risk is {pollen_status.replace('_', ' ')}")

    temperature, wind_speed, precipitation = safe_number(temperature), safe_number(wind_speed), safe_number(precipitation)
    if precipitation is not None:
        if precipitation >= 3:
            score -= 40
            reasons.append(f"Heavy rain ({precipitation:.1f} mm)")
        elif precipitation > 0.2:
            score -= 15
            reasons.append(f"Light rain ({precipitation:.1f} mm)")
    if wind_speed is not None:
        if wind_speed >= 13:
            score -= 35
            reasons.append(f"Strong wind ({wind_speed:.1f} m/s)")
        elif wind_speed >= 8:
            score -= 15
            reasons.append(f"Breezy conditions ({wind_speed:.1f} m/s)")
    if temperature is not None:
        if temperature < -5:
            score -= 25
            reasons.append(f"Very cold temperature ({temperature:.1f} °C)")
        elif temperature < 5:
            score -= 10
            reasons.append(f"Cold temperature ({temperature:.1f} °C)")
        elif temperature > 30:
            score -= 25
            reasons.append(f"High temperature ({temperature:.1f} °C)")

    score = max(0, min(100, score))
    if score >= 80:
        status, verdict = "good", "Good time to go outside"
    elif score >= 55:
        status, verdict = "moderate", "Generally okay to go outside"
    elif score >= 35:
        status, verdict = "poor", "Take precautions outdoors"
    else:
        status, verdict = "very_poor", "Consider changing your plans"
    if not reasons:
        reasons.append("Conditions are currently favourable for most people")
    return {"score": score, "status": status, "verdict": verdict, "reasons": reasons, "air_status": air_status, "pollen_status": pollen_status}


def get_recommendation(result):
    general = {
        "good": "Current conditions are suitable for most outdoor activities.",
        "moderate": "Outdoor activity is generally possible, but sensitive people should monitor symptoms.",
        "poor": "Consider shortening intense or prolonged outdoor activities.",
        "very_poor": "Consider postponing strenuous activity or choosing an indoor alternative.",
    }
    exercise = {
        "good": "Good conditions for walking, running and cycling.",
        "moderate": "Moderate activity should be possible. Take breaks if you feel discomfort.",
        "poor": "Choose a shorter or less intense outdoor activity.",
        "very_poor": "Consider moving intense exercise indoors.",
    }
    sensitive = []
    if result["air_status"] in ("moderate", "poor", "very_poor"):
        sensitive.append("People with asthma or breathing conditions should follow their usual precautions.")
    if result["pollen_status"] in ("moderate", "poor", "very_poor"):
        sensitive.append("People with pollen allergies should follow their usual allergy precautions.")
    if not sensitive:
        sensitive.append("No specific warning is currently identified.")
    return {"general": general[result["status"]], "exercise": exercise[result["status"]], "sensitive": " ".join(sensitive)}
