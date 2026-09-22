import datetime
import time
import pandas as pd
import requests

BASE_URL = "https://api.pollenrapporten.se/v1"
OUTPUT_FILE = "goteborg_historical_pollen.csv"


def get_lookups():
    """Fetch lookup maps for regions, pollen types, and level definitions."""
    headers = {"User-Agent": "Mozilla/5.0"}

    # 1. Regions
    r_reg = requests.get(f"{BASE_URL}/regions", headers=headers).json()
    reg_items = r_reg.get("items", r_reg) if isinstance(r_reg, dict) else r_reg
    regions = {r["id"]: r.get("name") for r in reg_items if isinstance(r, dict) and "id" in r}

    # Find Göteborg
    goteborg_id = next(
        (rid for rid, name in regions.items() if "göteborg" in name.lower() or "gothenburg" in name.lower()),
        list(regions.keys())[0] if regions else None
    )

    # 2. Pollen Types
    r_types = requests.get(f"{BASE_URL}/pollen-types", headers=headers).json()
    type_items = r_types.get("items", r_types) if isinstance(r_types, dict) else r_types
    pollen_types = {}
    for t in type_items:
        if isinstance(t, dict) and "id" in t:
            # Use Swedish name or general name
            name = t.get("name") or t.get("swedish_name") or t.get("label") or str(t["id"])
            pollen_types[t["id"]] = name

    # 3. Level Definitions (0=No, 1=Low, 2=Moderate, 3=High, etc.)
    levels = {}
    try:
        r_levels = requests.get(f"{BASE_URL}/pollen-level-definitions", headers=headers).json()
        lvl_items = r_levels.get("items", r_levels) if isinstance(r_levels, dict) else r_levels
        for lvl in lvl_items:
            if isinstance(lvl, dict) and "id" in lvl:
                levels[lvl["id"]] = lvl.get("description") or lvl.get("name") or str(lvl.get("level"))
    except Exception:
        pass

    return goteborg_id, regions, pollen_types, levels


def fetch_forecast_records(region_id, start_date, end_date):
    """Fetch forecasts within a date window."""
    params = {
        "region_id": region_id,
        "start_date": start_date,
        "end_date": end_date,
        "limit": 100
    }
    resp = requests.get(f"{BASE_URL}/forecasts", params=params, timeout=20)
    if resp.status_code != 200:
        return []

    raw = resp.json()
    if isinstance(raw, dict):
        return raw.get("items") or raw.get("data", {}).get("items") or [raw]
    return raw if isinstance(raw, list) else []


def main():
    print("1. Fetching lookup definitions (regions, pollen types, levels)...")
    goteborg_id, regions_map, pollen_map, level_map = get_lookups()
    city_name = regions_map.get(goteborg_id, "Göteborg")
    print(f"   Target Region: {city_name} (ID: {goteborg_id})")
    print(f"   Loaded {len(pollen_map)} pollen species definitions.")

    # Historical query window
    current_year = datetime.date.today().year
    years = list(range(2021, current_year + 1))

    all_rows = []

    print("\n2. Fetching forecasts...")
    for year in years:
        start_str = f"{year}-03-01"
        end_str = f"{year}-09-30" if year < current_year else datetime.date.today().isoformat()

        print(f"   -> Querying season {year} ({start_str} to {end_str})...")
        forecast_items = fetch_forecast_records(goteborg_id, start_str, end_str)

        for fc in forecast_items:
            if not isinstance(fc, dict):
                continue

            # Check for levelSeries
            series = fc.get("levelSeries") or fc.get("level_series") or fc.get("series") or []
            
            # If no levelSeries array, inspect items directly
            if not series and "forecastItems" in fc:
                series = fc["forecastItems"]

            for entry in series:
                # 1. Resolve date
                date_val = entry.get("date") or fc.get("startDate")

                # 2. Resolve pollen name
                p_id = entry.get("pollen_id") or entry.get("pollenId") or entry.get("pollen_type_id")
                p_obj = entry.get("pollenType") or entry.get("pollen_type")
                if isinstance(p_obj, dict):
                    pollen_name = p_obj.get("name") or pollen_map.get(p_obj.get("id"), "Unknown")
                else:
                    pollen_name = pollen_map.get(p_id, entry.get("name", "Unknown"))

                # 3. Resolve level value & description
                lvl_id = entry.get("level_id") or entry.get("levelId") or entry.get("level")
                if isinstance(lvl_id, dict):
                    val = lvl_id.get("value") or lvl_id.get("level")
                    desc = lvl_id.get("description") or lvl_id.get("name")
                else:
                    val = lvl_id
                    desc = level_map.get(lvl_id, f"Level {lvl_id}" if lvl_id is not None else None)

                all_rows.append({
                    "Date": date_val,
                    "Region": city_name,
                    "Pollen": pollen_name,
                    "Level_Value": val,
                    "Level_Description": desc,
                    "Forecast_Start": fc.get("startDate"),
                    "Forecast_End": fc.get("endDate")
                })

        time.sleep(0.2)

    if not all_rows:
        print("\nNo rows generated. Printing sample raw response for inspection:")
        test_resp = requests.get(f"{BASE_URL}/forecasts?region_id={goteborg_id}&limit=1").json()
        print(test_resp)
        return

    df = pd.DataFrame(all_rows)
    # Remove records that lack pollen identification
    df.dropna(subset=["Pollen"], inplace=True)
    df = df[~df["Pollen"].isin(["All", "Unknown"])]
    df.drop_duplicates(subset=["Date", "Region", "Pollen"], inplace=True)
    df.sort_values(by=["Date", "Pollen"], inplace=True)

    df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")
    print(f"\nSuccess! Written {len(df)} populated records to '{OUTPUT_FILE}'.")
    print(df.head(10))


if __name__ == "__main__":
    main()