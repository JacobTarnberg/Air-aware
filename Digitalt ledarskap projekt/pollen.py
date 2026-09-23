"""pollen.py - Direct API client for Pollenrapporten (Sweden)."""
from __future__ import annotations
import requests

BASE_URL = "https://api.pollenrapporten.se/v1"
HEADERS = {"User-Agent": "AirAware/1.0 (Mozilla/5.0)"}

LEVEL_MAP = {
    0: ("Inga halter", "#00e400"),          # None - Green
    1: ("Mycket låga halter", "#7ce400"),  # Very Low
    2: ("Låga halter", "#ffff00"),         # Low - Yellow
    3: ("Måttliga halter", "#ff7e00"),     # Moderate - Orange
    4: ("Höga halter", "#ff0000"),         # High - Red
    5: ("Mycket höga halter", "#99004c"),  # Very High - Purple
    6: ("Extrema halter", "#7e0023"),      # Extreme - Maroon
}

class PollenApiError(Exception):
    pass

def get_regions() -> list[dict]:
    """Fetch all 24 official pollen monitoring stations in Sweden."""
    try:
        resp = requests.get(f"{BASE_URL}/regions", headers=HEADERS, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return data.get("items", data) if isinstance(data, dict) else data
    except Exception as e:
        raise PollenApiError(f"Failed to fetch regions: {e}") from e

def get_pollen_types() -> dict[str, dict]:
    """Fetch species definitions mapping IDs to names."""
    try:
        resp = requests.get(f"{BASE_URL}/pollen-types", headers=HEADERS, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        items = data.get("items", data) if isinstance(data, dict) else data
        return {str(item["id"]): item for item in items if isinstance(item, dict) and "id" in item}
    except Exception:
        return {}

def get_current_forecast(region_id: str) -> dict | None:
    """Fetch the latest active forecast for a specific region ID directly."""
    params = {"region_id": region_id, "current": "true"}
    try:
        resp = requests.get(f"{BASE_URL}/forecasts", params=params, headers=HEADERS, timeout=12)
        if resp.status_code != 200:
            return None
        data = resp.json()
        items = data.get("items") or (data if isinstance(data, list) else [])
        return items[0] if (isinstance(items, list) and len(items) > 0) else None
    except Exception:
        return None

def worst_level(forecast: dict | None) -> int:
    """Calculate the maximum severity level across all species."""
    if not forecast:
        return 0
    series = forecast.get("levelSeries") or forecast.get("forecastItems") or []
    levels: list[int] = []
    for entry in series:
        lvl = entry.get("level") if entry.get("level") is not None else entry.get("value")
        if lvl is not None:
            try:
                levels.append(int(lvl))
            except (ValueError, TypeError):
                continue
    return max(levels) if levels else 0

def level_label(level: int) -> str:
    return LEVEL_MAP.get(level, (f"Nivå {level}", "#9e9e9e"))[0]

def level_color(level: int) -> str:
    return LEVEL_MAP.get(level, ("Unknown", "#9e9e9e"))[1]