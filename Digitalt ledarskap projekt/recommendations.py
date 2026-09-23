# --------------------------------------------------
# Status ranking
# --------------------------------------------------

STATUS_RANK = {
    "good": 0,
    "fair": 1,
    "moderate": 2,
    "poor": 3,
    "very_poor": 4,
    "extremely_poor": 5,
    "unavailable": -1,
}


# --------------------------------------------------
# Helper functions
# --------------------------------------------------

def safe_number(value):
    """
    Convert a value to a number.

    Return None if the value cannot be converted.
    """

    try:
        if value is None:
            return None

        return float(value)

    except (TypeError, ValueError):
        return None


def get_worst_status(statuses):
    """
    Return the worst available status from a list.
    """

    available_statuses = [
        status
        for status in statuses
        if status in STATUS_RANK and status != "unavailable"
    ]

    if not available_statuses:
        return "unavailable"

    return max(
        available_statuses,
        key=lambda status: STATUS_RANK[status],
    )


# --------------------------------------------------
# Air quality
# --------------------------------------------------

def get_air_status(aqi):
    """
    Convert the European AQI number into a readable status.
    """

    aqi = safe_number(aqi)

    if aqi is None:
        return "unavailable"

    if aqi <= 20:
        return "good"

    if aqi <= 40:
        return "fair"

    if aqi <= 60:
        return "moderate"

    if aqi <= 80:
        return "poor"

    if aqi <= 100:
        return "very_poor"

    return "extremely_poor"


# --------------------------------------------------
# Pollen
# --------------------------------------------------

def normalize_pollen_status(status):
    """
    Convert different pollen labels to our status system.
    """

    if status is None:
        return "unavailable"

    normalized = str(status).strip().lower().replace(" ", "_")

    mapping = {
        "none": "good",
        "very_low": "good",
        "low": "good",
        "good": "good",

        "low_to_moderate": "fair",
        "fair": "fair",

        "medium": "moderate",
        "moderate": "moderate",

        "moderate_to_high": "poor",
        "high": "poor",
        "poor": "poor",

        "very_high": "very_poor",
        "very_poor": "very_poor",

        "extreme": "extremely_poor",
        "extremely_high": "extremely_poor",
        "extremely_poor": "extremely_poor",
    }

    return mapping.get(normalized, "unavailable")


def get_pollen_status(pollen_data=None):
    """
    Find the worst pollen status.

    If pollen_data is missing, return unavailable.
    """

    if not pollen_data:
        return "unavailable"

    tree_status = normalize_pollen_status(
        pollen_data.get("tree")
    )

    grass_status = normalize_pollen_status(
        pollen_data.get("grass")
    )

    weed_status = normalize_pollen_status(
        pollen_data.get("weed")
    )

    return get_worst_status([
        tree_status,
        grass_status,
        weed_status,
    ])


# --------------------------------------------------
# Viability calculation
# --------------------------------------------------

def calculate_viability(
    aqi,
    temperature,
    wind_speed,
    precipitation,
    pollen_data=None,
):
    """
    Calculate an outdoor viability score from 0 to 100.
    """

    score = 100
    reasons = []

    aqi = safe_number(aqi)
    temperature = safe_number(temperature)
    wind_speed = safe_number(wind_speed)
    precipitation = safe_number(precipitation)

    air_status = get_air_status(aqi)
    pollen_status = get_pollen_status(pollen_data)

    # Air-quality deductions
    air_deductions = {
        "good": 0,
        "fair": 5,
        "moderate": 15,
        "poor": 30,
        "very_poor": 50,
        "extremely_poor": 65,
        "unavailable": 0,
    }

    score -= air_deductions[air_status]

    air_reasons = {
        "fair": "Air quality is fair",
        "moderate": "Air pollution is moderate",
        "poor": "Air quality is poor",
        "very_poor": "Air quality is very poor",
        "extremely_poor": "Air quality is extremely poor",
    }

    if air_status in air_reasons:
        reasons.append(air_reasons[air_status])

    # Pollen deductions
    pollen_deductions = {
        "good": 0,
        "fair": 5,
        "moderate": 10,
        "poor": 20,
        "very_poor": 30,
        "extremely_poor": 40,
        "unavailable": 0,
    }

    score -= pollen_deductions[pollen_status]

    pollen_reasons = {
        "fair": "Pollen levels are slightly elevated",
        "moderate": "Pollen levels are moderate",
        "poor": "Pollen levels are high",
        "very_poor": "Pollen levels are very high",
        "extremely_poor": "Pollen levels are extremely high",
    }

    if pollen_status in pollen_reasons:
        reasons.append(pollen_reasons[pollen_status])

    # Rain deductions
    if precipitation is not None:
        if precipitation >= 3:
            score -= 40
            reasons.append(
                f"Heavy rain ({precipitation:.1f} mm)"
            )

        elif precipitation > 0.2:
            score -= 15
            reasons.append(
                f"Light rain ({precipitation:.1f} mm)"
            )

    # Wind deductions
    if wind_speed is not None:
        if wind_speed >= 13:
            score -= 35
            reasons.append(
                f"Strong wind ({wind_speed:.1f} m/s)"
            )

        elif wind_speed >= 8:
            score -= 15
            reasons.append(
                f"Breezy conditions ({wind_speed:.1f} m/s)"
            )

    # Temperature deductions
    if temperature is not None:
        if temperature < -5:
            score -= 25
            reasons.append(
                f"Very cold temperature ({temperature:.1f} °C)"
            )

        elif temperature < 5:
            score -= 10
            reasons.append(
                f"Cold temperature ({temperature:.1f} °C)"
            )

        elif temperature > 30:
            score -= 25
            reasons.append(
                f"High temperature ({temperature:.1f} °C)"
            )

    score = max(0, min(100, score))

    if score >= 80:
        status = "good"
        verdict = "Good time to go outside"

    elif score >= 55:
        status = "moderate"
        verdict = "Generally okay to go outside"

    elif score >= 35:
        status = "poor"
        verdict = "Take precautions outdoors"

    else:
        status = "very_poor"
        verdict = "Consider changing your plans"

    if not reasons:
        reasons.append(
            "Conditions are currently favourable for most people"
        )

    return {
        "score": score,
        "status": status,
        "verdict": verdict,
        "reasons": reasons,
        "air_status": air_status,
        "pollen_status": pollen_status,
    }


# --------------------------------------------------
# Recommendation text
# --------------------------------------------------

def get_recommendation(result):
    """
    Create understandable advice from the calculated result.
    """

    status = result["status"]
    air_status = result["air_status"]
    pollen_status = result["pollen_status"]

    general_messages = {
        "good": (
            "Current conditions are suitable for most "
            "outdoor activities."
        ),
        "moderate": (
            "Outdoor activities are generally possible, "
            "but sensitive people should pay attention "
            "to symptoms."
        ),
        "poor": (
            "Consider shortening intense or prolonged "
            "outdoor activities."
        ),
        "very_poor": (
            "Consider postponing strenuous outdoor activities "
            "or choosing an indoor alternative."
        ),
    }

    exercise_messages = {
        "good": (
            "Good conditions for walking, running and cycling."
        ),
        "moderate": (
            "Moderate outdoor activity should be possible. "
            "Take breaks if you feel discomfort."
        ),
        "poor": (
            "Choose a shorter or less intense outdoor activity."
        ),
        "very_poor": (
            "Consider moving intense exercise indoors."
        ),
    }

    sensitive_messages = []

    if air_status in [
        "moderate",
        "poor",
        "very_poor",
        "extremely_poor",
    ]:
        sensitive_messages.append(
            "People with asthma or breathing conditions should "
            "monitor symptoms and keep prescribed medication available."
        )

    if pollen_status in [
        "moderate",
        "poor",
        "very_poor",
        "extremely_poor",
    ]:
        sensitive_messages.append(
            "People with pollen allergies should consider their "
            "usual allergy precautions."
        )

    if not sensitive_messages:
        sensitive_messages.append(
            "No specific warning is currently identified. "
            "Continue to follow your usual health advice."
        )

    return {
        "general": general_messages[status],
        "exercise": exercise_messages[status],
        "sensitive": " ".join(sensitive_messages),
    }
