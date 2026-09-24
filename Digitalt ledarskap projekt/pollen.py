"""
Pollenrapporten API layer.

Provides current + historical pollen data, with pollen names resolved
from the /pollen-types endpoint and grouped into Tree / Grass / Weed / Other.
"""

from typing import Optional

import pandas as pd
import requests

BASE_URL = "https://api.pollenrapporten.se/v1"

# ---------------------------------------------------------
# Pollen grouping
# ---------------------------------------------------------
# Names are matched case-insensitively against the API's Swedish names
# (from /pollen-types): Hassel, Al, Tall, "Sälg och viden", Alm, Björk,
# Bok, Ek, Gran, Gräs, Gråbo, Malörtsambrosia, Alternaria, Cladosporium,
# Epicoccum.

POLLEN_GROUPS = {
    "Tree pollen": {
        "hassel", "al", "alm", "björk", "bok", "ek", "gran", "tall",
        "sälg och viden", "sälg & viden",
    },
    "Grass pollen": {
        "gräs",
    },
    "Weed pollen": {
        "gråbo", "malörtsambrosia",
    },
}


def get_pollen_group(pollen_name: str) -> str:
    """Convert an individual pollen type into an application category."""
    name = (pollen_name or "").strip().lower()
    for group, pollen_types in POLLEN_GROUPS.items():
        if name in pollen_types:
            return group
    return "Other"


# ---------------------------------------------------------
# Level conversion (API uses a 0-6 scale)
# ---------------------------------------------------------

LEVEL_MAP = {
    0: "none",
    1: "low",
    2: "low",
    3: "moderate",
    4: "high",
    5: "very high",
    6: "very high",
}

LEVEL_ORDER = {
    "unavailable": -1,
    "none": 0,
    "low": 1,
    "moderate": 2,
    "high": 3,
    "very high": 4,
}


def convert_level(level) -> str:
    """Convert a numeric forecast level into a human-readable level."""
    if level is None:
        return "unavailable"
    try:
        level = int(level)
    except (TypeError, ValueError):
        return "unavailable"
    return LEVEL_MAP.get(level, "unavailable")


# ---------------------------------------------------------
# API helpers
# ---------------------------------------------------------

def api_get(endpoint: str, params: Optional[dict] = None) -> dict:
    """Generic GET request to Pollenrapporten."""
    url = f"{BASE_URL}{endpoint}"
    response = requests.get(
        url,
        params=params,
        timeout=15,
        headers={"User-Agent": "PollenStreamlitApp/1.0"},
    )
    response.raise_for_status()
    return response.json()


def api_get_all(endpoint: str, params: Optional[dict] = None) -> list:
    """GET every page of a paginated endpoint and return all items."""
    params = dict(params or {})
    params.setdefault("limit", 100)
    offset = 0
    items: list = []
    while True:
        params["offset"] = offset
        data = api_get(endpoint, params)
        page = data.get("items", [])
        items.extend(page)
        meta = data.get("_meta", {})
        total = meta.get("totalRecords", len(items))
        if len(items) >= total or not page:
            break
        offset += len(page)
    return items


# ---------------------------------------------------------
# Regions & pollen types
# ---------------------------------------------------------

def get_regions() -> list:
    """Return all regions available from Pollenrapporten."""
    return api_get_all("/regions")


def find_region(region_name: str) -> Optional[dict]:
    """Find a region record by (case-insensitive) name."""
    target = region_name.strip().lower()
    for region in get_regions():
        if region["name"].strip().lower() == target:
            return region
    return None


def get_pollen_name_map() -> dict:
    """Return a mapping of pollenId -> human-readable name."""
    items = api_get_all("/pollen-types")
    return {item["id"]: item["name"] for item in items}


# ---------------------------------------------------------
# Forecast fetching
# ---------------------------------------------------------

def _forecast_rows(forecasts: list, name_map: dict) -> list:
    """Flatten forecast items into per-pollen, per-day rows."""
    rows = []
    for forecast in forecasts:
        f_start = forecast.get("startDate")
        f_end = forecast.get("endDate")
        for entry in forecast.get("levelSeries", []):
            pollen_id = entry.get("pollenId")
            name = name_map.get(pollen_id, str(pollen_id))
            numeric = entry.get("level")
            rows.append(
                {
                    "pollen_id": pollen_id,
                    "pollen": name,
                    "category": get_pollen_group(name),
                    "numeric_level": numeric,
                    "level": convert_level(numeric),
                    "time": entry.get("time"),
                    "forecast_start": f_start,
                    "forecast_end": f_end,
                }
            )
    return rows


def get_pollen_history(region_name: str) -> pd.DataFrame:
    """
    Return the full available pollen history for a region as a DataFrame:
        columns: pollen_id, pollen, category, numeric_level, level, time (datetime)

    Data comes entirely from the Pollenrapporten forecasts endpoint.
    """
    region = find_region(region_name)
    if region is None:
        raise ValueError(f"Region '{region_name}' was not found.")

    name_map = get_pollen_name_map()
    forecasts = api_get_all(
        "/forecasts", params={"region_id": region["id"]}
    )
    rows = _forecast_rows(forecasts, name_map)
    if not rows:
        return pd.DataFrame(
            columns=[
                "pollen_id", "pollen", "category",
                "numeric_level", "level", "time",
                "forecast_start", "forecast_end", "in_window",
            ]
        )

    df = pd.DataFrame(rows)
    df["time"] = pd.to_datetime(df["time"], errors="coerce")
    df = df.dropna(subset=["time"]).sort_values("time")
    # Collapse duplicate (pollen, day) entries to the max level of the day.
    df["date"] = df["time"].dt.date

    # Flag rows whose day falls within the issuing forecast's stated window.
    # Days beyond forecast_end are low-confidence "overhang" projections.
    fstart = pd.to_datetime(df["forecast_start"], errors="coerce").dt.date
    fend = pd.to_datetime(df["forecast_end"], errors="coerce").dt.date
    df["in_window"] = (df["date"] >= fstart) & (df["date"] <= fend)
    # If a forecast lacks window dates, treat the row as in-window.
    df.loc[fstart.isna() | fend.isna(), "in_window"] = True

    df = (
        df.sort_values("numeric_level")
        .drop_duplicates(subset=["pollen_id", "date"], keep="last")
        .sort_values("time")
        .reset_index(drop=True)
    )
    return df


def aggregate_group_level(levels) -> str:
    """Highest reported level for a category (ignoring unavailable)."""
    valid = [lvl for lvl in levels if lvl in LEVEL_ORDER and lvl != "unavailable"]
    if not valid:
        return "unavailable"
    return max(valid, key=lambda x: LEVEL_ORDER[x])


def get_latest_grouped(df: pd.DataFrame) -> dict:
    """
    From a history DataFrame, take the most recent day that has data and
    group it into Tree / Grass / Weed / Other.
    """
    if df.empty:
        return {"status": "unavailable", "date": None, "summary": {}}

    latest_date = df["date"].max()
    day = df[df["date"] == latest_date]

    summary = {}
    for category in ["Tree pollen", "Grass pollen", "Weed pollen", "Other"]:
        cat = day[day["category"] == category]
        summary[category] = {
            "level": aggregate_group_level(cat["level"].tolist()),
            "pollen": cat[["pollen", "level", "numeric_level"]].to_dict("records"),
        }

    return {"status": "available", "date": latest_date, "summary": summary}
