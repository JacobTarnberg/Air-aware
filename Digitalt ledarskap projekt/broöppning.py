import requests

# Replace with your key from data.goteborg.se
APP_ID = "YOUR_APP_ID"

# Endpoint for BridgeService v2.0
URL = f"https://data.goteborg.se/BridgeService/v2.0/GetEvents/{APP_ID}?format=json"


def check_bridge_status():
    try:
        response = requests.get(URL, timeout=10)
        response.raise_for_status()
        data = response.json()

        # Print the raw payload to inspect the exact properties returned
        print("Raw API response:")
        print(data)

        # The payload typically returns a list of events or a status object
        # Example inspection:
        if isinstance(data, dict):
            # Check common keys used by BridgeService
            is_open = data.get("IsOpen") or data.get("isBridgeOpen")
            print(f"\nBridge Open: {is_open}")
        elif isinstance(data, list) and len(data) > 0:
            latest = data[0]
            print(f"\nLatest event: {latest}")

        return data

    except requests.exceptions.RequestException as err:
        print(f"Request failed: {err}")
        return None


if __name__ == "__main__":
    check_bridge_status()