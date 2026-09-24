# Air-aware

Air-aware is a Streamlit application for monitoring air quality, weather, and
pollen conditions in Swedish municipalities. It is designed to make the data
easier to understand for people with asthma and other sensitive airways.

## Main application

The submission entry point is:

```text
Digitalt ledarskap projekt/app.py
```

Run the application from the `Digitalt ledarskap projekt` directory.

## Required files

These files are required for `app.py`:

| File | Purpose |
| --- | --- |
| `app.py` | Main Streamlit user interface and data pipeline |
| `pollen.py` | Retrieves and processes pollen data |
| `locations.py` | Swedish locations and nearest pollen-station lookup |
| `logotype.jpeg` | Application logo and favicon |
| `requirements.txt` | Python package dependencies |

The application retrieves live data from Open-Meteo, SMHI, and Pollenrapporten.
An internet connection is therefore required while the application is running.
No API key is currently required.

## Setup

1. Open PowerShell in the `Air-aware` project folder.
2. Enter the application folder:

```powershell
cd "Digitalt ledarskap projekt"
```

3. Create and activate a Python virtual environment:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

4. Install the required packages from `requirements.txt`:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If PowerShell does not allow environment activation, install packages through
the environment's Python executable instead:

```powershell
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Start the application

From the same directory, run:

```powershell
streamlit run app.py
```

Streamlit will display a local address, normally:

```text
http://localhost:8501
```

Open that address in a browser. The app can still run without
`streamlit-local-storage`, but browser preferences will only last for the
current session.

## Submission package

Submit a ZIP containing the following files:

```text
Air-aware/
├── README.md
└── Digitalt ledarskap projekt/
	├── app.py
	├── pollen.py
	├── locations.py
	├── logotype.jpeg
	└── requirements.txt
```
