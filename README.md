# RateRight PGH — Daily Parking-Demand Forecast Demo

RateRight PGH is a Streamlit prototype for exploring short-term paid-parking
demand across nine Pittsburgh parking zones. It presents a historical forecast
demonstration for **November 1–7, 2024** at a **daily** time scale.

## What the app shows

- A daily demand heatmap for nine parking zones
- Forecast paid transactions and historical normal demand
- Zone rankings based on forecast transactions per active payment point
- High, Normal, and Low demand signals based on change from normal
- A seven-day profile for a selected zone

The bundled dataset contains 63 zone-date records. Fifty-four records have
published forecasts: six supported dates for each of the nine zones. November 3
remains unpublished because there is insufficient Sunday history; the missing
forecast is not treated as zero demand.

## Important interpretation

The app forecasts **daily paid transactions**, not physical parking occupancy,
open spaces, parking duration, revenue, or the optimal parking price.

The displayed `Forecast Transactions per Payment Point` metric is:

```text
published daily paid-transaction forecast / active physical payment points in the zone
```

A payment point is a payment device and may serve multiple parking spaces.

## Project files

```text
RateRight_PGH_Python_Demo/
├── app.py
├── requirements.txt
├── README.md
└── data/
    └── demo-data.json
```

`data/demo-data.json` is included and ready to use. The app does not require an
API key for its OpenStreetMap background.

## Run locally on macOS

Open Terminal and run:

```bash
cd /Users/jianwei/CMU-Python/TimeSeries95835/RateRight_PGH_Python_Demo
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
streamlit run app.py
```

The app normally opens at <http://localhost:8501>.

## Deploy with Streamlit Community Cloud

1. Create a GitHub repository and upload the contents of this project folder.
2. Confirm that `app.py`, `requirements.txt`, and `data/demo-data.json` are in
   the repository.
3. Sign in at <https://share.streamlit.io/> with GitHub.
4. Select **Create app** and choose the GitHub repository.
5. Set the branch to `main` and the main file path to `app.py`.
6. Select **Deploy**.

Streamlit will provide a shareable `streamlit.app` URL. The computer used to
create the app does not need to remain online after deployment.

## Forecast scope

- Forecast window: November 1–7, 2024
- Granularity: daily
- Zones: 9
- Published forecasts: 54 zone-days
- Unsupported date: November 3, 2024
- Location source: WPRDC Pittsburgh Parking Meters and Payment Points

This prototype is a historical demonstration. It is not connected to a live
transaction feed and does not automatically create future forecasts.
