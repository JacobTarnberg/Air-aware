import requests
import pandas as pd

def fetch_who_sample(indicator="WHOSIS_000001", limit=100, output_csv="who_sample.csv"):
    # WHO GHO OData API endpoint
    # Using $top to restrict records and $filter to get clean, country-level data
    url = f"https://ghoapi.azureedge.net/api/{indicator}?$top={limit}&$filter=SpatialDimType eq 'COUNTRY'"
    
    response = requests.get(url)
    response.raise_for_status()
    
    raw_data = response.json().get("value", [])
    df = pd.DataFrame(raw_data)
    
    # Select and rename the most relevant columns
    columns_to_keep = {
        "SpatialDim": "country_code",
        "TimeDim": "year",
        "Dim1": "sex",
        "NumericValue": "value",
        "Comments": "comments"
    }
    
    # Filter to existing columns in the returned payload
    available_cols = [col for col in columns_to_keep.keys() if col in df.columns]
    df_clean = df[available_cols].rename(columns=columns_to_keep)
    
    # Save to CSV
    if output_csv:
        df_clean.to_csv(output_csv, index=False)
        print(f"Saved {len(df_clean)} rows to {output_csv}")
        
    return df_clean

if __name__ == "__main__":
    sample_df = fetch_who_sample(limit=50)
    print(sample_df.head())