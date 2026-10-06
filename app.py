"""RateRight PGH — Streamlit daily parking-demand forecast demo."""

from __future__ import annotations

import json
from pathlib import Path

import folium
import pandas as pd
import plotly.express as px
import streamlit as st
from folium.plugins import HeatMap
from streamlit_folium import st_folium


DATA_FILE = Path(__file__).parent / "data" / "demo-data.json"
COLORS = {"Low": "#22a06b", "Normal": "#e0a01b", "High": "#df4545"}


st.set_page_config(
    page_title="RateRight PGH",
    page_icon="🅿️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
      .stApp {background: #f3f6f9;}
      [data-testid="stSidebar"] {background: #f7f9fc; border-right:1px solid #d9e1ea;}
      [data-testid="stSidebar"] * {color: #14283d !important;}
      [data-testid="stSidebar"] input {color:#14283d !important;}
      [data-testid="stSidebar"] [data-baseweb="select"] > div {
        background:#ffffff !important; color:#14283d !important;
      }
      .hero {background:#0b1f33; color:white; border-radius:18px; padding:22px 26px;
             margin-bottom:18px; border-left:7px solid #f3b61f;}
      .hero h1 {margin:0; font-size:2.1rem;}
      .hero p {margin:6px 0 0; color:#c9d4df;}
      .legend {display:flex; gap:20px; flex-wrap:wrap; margin:4px 0 12px; color:#405268;}
      .dot {height:12px; width:12px; border-radius:50%; display:inline-block; margin-right:6px;}
      .note {background:#fff8e1; border-left:5px solid #e0a01b; padding:12px 14px;
             border-radius:8px; color:#594600;}
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data
def load_data() -> tuple[dict, pd.DataFrame, pd.DataFrame]:
    """Load the forecast JSON and return metadata, zones and daily records."""
    if not DATA_FILE.exists():
        raise FileNotFoundError(
            "data/demo-data.json is missing. Run `python preprocess.py` first."
        )
    payload = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    zones = pd.DataFrame(payload["zones"])
    daily = pd.DataFrame(payload["records"])
    daily["date"] = pd.to_datetime(daily["date"]).dt.date
    return payload["metadata"], zones, daily


def make_map(snapshot: pd.DataFrame) -> folium.Map:
    """Build a Pittsburgh-centered heatmap and labeled zone markers."""
    center = [snapshot["latitude"].mean(), snapshot["longitude"].mean()]
    parking_map = folium.Map(
        location=center,
        zoom_start=13,
        # OpenStreetMap works without a CARTO/Mapbox API key.  CARTO's
        # no-key tiles may display an "API KEY REQUIRED" watermark.
        tiles="OpenStreetMap",
        control_scale=True,
        prefer_canvas=True,
    )

    # Normalize heat weights only for map rendering. The displayed metric remains
    # the unscaled transactions-per-payment-point value.
    max_activity = max(float(snapshot["transactions_per_point"].max()), 1.0)
    heat_rows = [
        [row.latitude, row.longitude, row.transactions_per_point / max_activity]
        for row in snapshot.itertuples()
    ]
    HeatMap(
        heat_rows,
        name="Demand heatmap",
        min_opacity=0.25,
        radius=42,
        blur=30,
        max_zoom=16,
        gradient={0.2: "#2cb67d", 0.6: "#f0b429", 0.8: "#f36b4b", 1.0: "#d62839"},
    ).add_to(parking_map)

    for row in snapshot.itertuples():
        popup = folium.Popup(
            f"<b>{row.zone}</b><br>Forecast transactions per payment point: "
            f"{row.transactions_per_point:.2f}"
            f"<br>Forecast transactions: {row.forecast:.1f}"
            f"<br>Payment points: {int(row.payment_point_count)}"
            f"<br>Historical normal: {row.historical_normal:.1f}"
            f"<br>Change vs normal: {row.change_vs_normal_percent:+.1f}%",
            max_width=250,
        )
        folium.CircleMarker(
            [row.latitude, row.longitude],
            radius=9,
            color="white",
            weight=2,
            fill=True,
            fill_color=COLORS[row.activity_level],
            fill_opacity=0.95,
            tooltip=f"{row.zone}: {row.transactions_per_point:.2f} forecast transactions/point",
            popup=popup,
        ).add_to(parking_map)

    # Explicit bounds keep the initial view on the nine Pittsburgh zones.
    padding = 0.006
    parking_map.fit_bounds(
        [
            [snapshot["latitude"].min() - padding, snapshot["longitude"].min() - padding],
            [snapshot["latitude"].max() + padding, snapshot["longitude"].max() + padding],
        ]
    )
    folium.LayerControl(collapsed=True).add_to(parking_map)
    return parking_map


metadata, zones, daily = load_data()
available_dates = [
    value.date()
    for value in pd.date_range(metadata["period_start"], metadata["period_end"], freq="D")
]

with st.sidebar:
    st.markdown("## Explore demand")
    chosen_date = st.date_input(
        "Arrival date",
        value=available_dates[0],
        min_value=available_dates[0],
        max_value=available_dates[-1],
    )
    selected_zone = st.selectbox("Zone for weekly profile", sorted(zones["zone"]))
    st.markdown("---")
    st.caption("Daily forecast: November 1–7, 2024")

st.markdown(
    """
    <div class="hero">
      <h1>RateRight PGH</h1>
      <p>Explore the seven-day paid parking demand forecast before you drive.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

snapshot = daily[
    (daily["date"] == chosen_date) & daily["supported_day"] & daily["forecast"].notna()
].merge(zones[["zone", "latitude", "longitude", "payment_point_count"]], on="zone")

if snapshot.empty:
    st.error("No published forecast is available for this date.")
    st.stop()

snapshot["transactions_per_point"] = snapshot["forecast"] / snapshot["payment_point_count"]
snapshot["activity_level"] = snapshot["signal"]

peak = snapshot.loc[snapshot["transactions_per_point"].idxmax()]
high_count = int((snapshot["activity_level"] == "High").sum())

c1, c2, c3, c4 = st.columns(4)
c1.metric("Forecast transactions", f"{snapshot['forecast'].sum():,.0f}")
c2.metric(
    "Highest activity zone",
    peak["zone"],
    f"{peak['transactions_per_point']:.2f} transactions/point",
)
c3.metric("High-demand zones", high_count)
c4.metric("Historical normal", f"{snapshot['historical_normal'].sum():,.0f}")

st.subheader(f"Daily forecast heatmap · {chosen_date.strftime('%B %-d, %Y')}")
st.markdown(
    """
    <div class="legend">
      <span><i class="dot" style="background:#22a06b"></i>Low: more than 20% below normal</span>
      <span><i class="dot" style="background:#e0a01b"></i>Normal: within ±20% of normal</span>
      <span><i class="dot" style="background:#df4545"></i>High: more than 20% above normal</span>
    </div>
    """,
    unsafe_allow_html=True,
)

left, right = st.columns([1.75, 1], gap="large")
with left:
    st_folium(
        make_map(snapshot),
        height=590,
        use_container_width=True,
        returned_objects=[],
        key=f"map-{chosen_date}",
    )

with right:
    st.markdown("### Zone ranking")
    ranking = snapshot.sort_values("transactions_per_point", ascending=False).copy()
    ranking["Forecast / Point"] = ranking["transactions_per_point"].map(
        lambda value: f"{value:.2f}"
    )
    ranking["Status"] = ranking["activity_level"]
    ranking["Forecast Transactions"] = ranking["forecast"].map(lambda value: f"{value:.1f}")
    st.dataframe(
        ranking[["zone", "Forecast / Point", "Status", "Forecast Transactions"]].rename(
            columns={"zone": "Zone"}
        ),
        hide_index=True,
        use_container_width=True,
        height=390,
    )
    st.markdown(
        '<div class="note"><b>Important:</b> this shows forecast daily paid transactions '
        "per active payment point, not physical parking occupancy.</div>",
        unsafe_allow_html=True,
    )

st.markdown("### Selected zone: seven-day demand profile")
zone_daily = daily[daily["zone"] == selected_zone].sort_values("date").copy()
point_count = int(zones.loc[zones["zone"] == selected_zone, "payment_point_count"].iloc[0])
zone_daily["transactions_per_point"] = zone_daily["forecast"] / point_count
fig = px.line(
    zone_daily,
    x="date",
    y="transactions_per_point",
    markers=True,
    labels={
        "date": "Date",
        "transactions_per_point": "Daily Forecast Transactions per Payment Point",
    },
)
chart_max = max(float(zone_daily["transactions_per_point"].max()) * 1.1, 1.2)
fig.update_traces(line_color="#2165d6", line_width=3)
fig.update_layout(
    height=330,
    margin=dict(l=10, r=10, t=15, b=10),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="white",
    xaxis=dict(dtick="D1", tickformat="%b %d"),
    yaxis=dict(range=[0, chart_max]),
)
st.plotly_chart(fig, use_container_width=True)

with st.expander("How the index is calculated"):
    st.markdown(
        "**Forecast Transactions per Payment Point** = forecast daily paid transactions ÷ the "
        "number of active physical payment points assigned to that zone."
    )
    st.write(
        "This is a daily activity-rate proxy, not a physical parking occupancy percentage. "
        "November 3 has insufficient weekday support, so it appears as a gap rather than zero."
    )
