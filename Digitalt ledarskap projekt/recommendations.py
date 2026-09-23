STATUS_RANK = {
    "good": 0,
    "moderate": 1,
    "poor": 2,
    "very_poor": 3,
    "unavailable": -1,
}


def normalize_status(status):
    if status is None:
        return "unavailable"

    normalized = str(status).strip().lower().replace(" ", "_")

    mapping = {
        "low": "good",
        "good": "good",
        "medium": "moderate",
        "moderate": "moderate",
        "high": "poor",
        "poor": "poor",
        "very_high": "very_poor",
        "very_poor": "very_poor",
    }

    return mapping.get(normalized, "unavailable")


def get_worst_status(statuses):
    normalized_statuses = [
        normalize_status(status) for status in statuses
    ]

    available_statuses = [
        status for status in normalized_statuses
        if status != "unavailable"
    ]

    if not available_statuses:
        return "unavailable"

    return max(
        available_statuses,
        key=lambda status: STATUS_RANK[status]
    )


def get_pollen_status(pollen_data):
    return get_worst_status([
        pollen_data.get("tree"),
        pollen_data.get("grass"),
        pollen_data.get("weed"),
    ])


def get_combined_status(air_data, pollen_data):
    air_status = normalize_status(air_data.get("status"))
    pollen_status = get_pollen_status(pollen_data)

    return get_worst_status([air_status, pollen_status])

RECOMMENDATIONS = {
    "good": {
        "title": "Good time to go outside",
        "message": "Current conditions are favourable for most people."
    },
    "moderate": {
        "title": "Generally okay to go outside",
        "message": "Sensitive people should pay attention to symptoms."
    },
    "poor": {
        "title": "Take precautions outdoors",
        "message": (
            "Sensitive people may want to reduce intense or prolonged "
            "outdoor activities."
        )
    },
    "very_poor": {
        "title": "Consider changing your plans",
        "message": (
            "Sensitive people may want to postpone strenuous "
            "outdoor activities."
        )
    },
    "unavailable": {
        "title": "Current conditions unavailable",
        "message": "There is not enough information to provide a recommendation."
    },
}


def get_recommendation(air_data, pollen_data):
    status = get_combined_status(air_data, pollen_data)

    return {
        "status": status,
        "title": RECOMMENDATIONS[status]["title"],
        "message": RECOMMENDATIONS[status]["message"],
    }