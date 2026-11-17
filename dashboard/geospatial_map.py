"""AERIS Dashboard - Geospatial Map Page
Interactive Pan-India Spatial Mapping with Click-to-Query Atmospheric Intelligence.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from src.geospatial import (
    INDIAN_CITIES_GEO,
    fetch_live_air_quality,
    classify_cpcb_aqi,
    create_india_air_quality_map,
)
from src.preprocessing import NAAQS_STANDARDS
from src.analysis import AERIS_PALETTE


@st.cache_data(ttl=3600, show_spinner=False)
def get_pan_india_snapshot():
    """Builds a cached pan-India snapshot with baseline concentrations."""
    snapshot = []
    for item in INDIAN_CITIES_GEO:
        lat, lon = item["Lat"], item["Lon"]
        # Fast regional baseline calculation
        if lat > 25.0 and lon < 85.0:  # Indo-Gangetic Plain
            pm25 = 98.4
        elif lat < 18.0 and lon < 78.0:  # Southern Plateau / Coastal
            pm25 = 38.6
        elif lon > 88.0:  # North-East
            pm25 = 32.1
        elif lat < 20.0 and lon < 74.0:  # Coastal Mumbai/Goa
            pm25 = 48.5
        else:
            pm25 = 62.0

        cat, color = classify_cpcb_aqi(pm25)
        snapshot.append({
            **item,
            "PM2.5": pm25,
            "AQI_Category": cat,
            "Color": color
        })
    return snapshot


def render_geospatial_map_page(df: pd.DataFrame) -> None:
    """Renders the Pan-India interactive geospatial intelligence map and location drill-down."""
    st.markdown("## 🗺️ Pan-India Geospatial Risk Map & Live Intelligence")
    st.caption("Click any monitoring station on the map or query custom coordinates anywhere across India")

    # 1. Location Selection Controls
    mode = st.radio(
        "Navigation Mode:",
        options=["📍 Select from 44+ Pan-India CPCB Airsheds", "🌐 Custom Coordinates Anywhere in India"],
        horizontal=True
    )

    cities_snapshot = get_pan_india_snapshot()
    city_names = [c["City"] for c in cities_snapshot]

    target_lat = 28.6139
    target_lon = 77.2090
    target_name = "Delhi"
    target_state = "Delhi NCR"
    target_station = "Anand Vihar CAAQMS"

    if mode == "📍 Select from 44+ Pan-India CPCB Airsheds":
        c_col1, c_col2 = st.columns([2, 1])
        with c_col1:
            selected_city = st.selectbox(
                "Choose City / Monitoring Airshed:",
                options=city_names,
                index=0,
                help="Select any major city across North, South, East, West, Central, and North-East India."
            )
        with c_col2:
            st.info(f"💡 You can also inspect coordinates by typing custom coordinates below.")

        sel_info = next((item for item in cities_snapshot if item["City"] == selected_city), cities_snapshot[0])
        target_lat = sel_info["Lat"]
        target_lon = sel_info["Lon"]
        target_name = sel_info["City"]
        target_state = sel_info["State"]
        target_station = sel_info["Station"]

    else:  # Custom Coordinates Mode
        st.markdown("#### Enter Custom Geographic Coordinates (Anywhere in India):")
        coord_col1, coord_col2, coord_col3 = st.columns([1, 1, 2])
        with coord_col1:
            custom_lat = st.number_input("Latitude (°N):", min_value=8.0, max_value=37.0, value=26.8467, step=0.01)
        with coord_col2:
            custom_lon = st.number_input("Longitude (°E):", min_value=68.0, max_value=97.0, value=80.9462, step=0.01)
        with coord_col3:
            preset = st.selectbox(
                "Or pick a geographical landmark:",
                options=[
                    "Custom Input",
                    "Taj Mahal, Agra (27.1751° N, 78.0421° E)",
                    "Varanasi Ghats (25.3176° N, 82.9739° E)",
                    "Ladakh High Plateau (34.1526° N, 77.5771° E)",
                    "Western Ghats, Munnar (10.0889° N, 77.0595° E)",
                    "Kaziranga, Assam (26.5775° N, 93.1711° E)",
                    "Thar Desert, Jaisalmer (26.9157° N, 70.9083° E)"
                ]
            )
            if "Taj Mahal" in preset:
                custom_lat, custom_lon = 27.1751, 78.0421
            elif "Varanasi" in preset:
                custom_lat, custom_lon = 25.3176, 82.9739
            elif "Ladakh" in preset:
                custom_lat, custom_lon = 34.1526, 77.5771
            elif "Western Ghats" in preset:
                custom_lat, custom_lon = 10.0889, 77.0595
            elif "Kaziranga" in preset:
                custom_lat, custom_lon = 26.5775, 93.1711
            elif "Thar Desert" in preset:
                custom_lat, custom_lon = 26.9157, 70.9083

        target_lat = custom_lat
        target_lon = custom_lon
        target_name = f"Custom Location ({target_lat:.2f}°N, {target_lon:.2f}°E)"
        target_state = "India Geospatial Grid"
        target_station = "Copernicus CAMS Virtual Grid Cell"

    # 2. Interactive Pan-India Map
    fig_map = create_india_air_quality_map(
        cities_snapshot,
        selected_city_name=target_name if mode.startswith("📍") else None
    )
    st.plotly_chart(fig_map, use_container_width=True)

    st.markdown("---")

    # 3. Live Atmospheric Query for Selected Location
    with st.spinner(f"Retrieving atmospheric intelligence for {target_name}..."):
        live_data = fetch_live_air_quality(target_lat, target_lon)

    # Location Information Header Banner
    source_badge = "🛰️ Live Copernicus Satellite/Open-Meteo" if live_data.get("Is_Live") else "🏛️ Historical Calibrated Baseline"
    st.markdown(
        f"""
        <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-left: 6px solid {live_data['Color']}; padding: 18px 22px; border-radius: 8px; margin-bottom: 20px;">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
                <div>
                    <h3 style="margin: 0; color: #0F4C81;">📍 {target_name}</h3>
                    <span style="color: #64748B; font-size: 0.9rem;">
                        State: <b>{target_state}</b> | Station: <b>{target_station}</b> | Coordinates: <b>{target_lat:.4f}°N, {target_lon:.4f}°E</b>
                    </span>
                </div>
                <div style="text-align: right;">
                    <span style="background: {live_data['Color']}; color: white; padding: 6px 14px; border-radius: 20px; font-weight: 700; font-size: 0.95rem;">
                        {live_data['AQI_Category']} Air Quality
                    </span><br>
                    <small style="color: #64748B;">Source: {source_badge}</small>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Atmospheric Metrics KPI Cards Row
    kpi1, kpi2, kpi3, kpi4, kpi5, kpi6 = st.columns(6)

    pm25_val = live_data.get("PM2.5")
    pm10_val = live_data.get("PM10")
    no2_val = live_data.get("NO2")
    so2_val = live_data.get("SO2")
    co_val = live_data.get("CO")
    o3_val = live_data.get("O3")

    with kpi1:
        st.metric(
            "PM2.5 (Fine)",
            f"{pm25_val:.1f} µg/m³" if pm25_val is not None else "N/A",
            delta=f"{pm25_val - 60.0:+.1f} vs NAAQS" if pm25_val is not None else None,
            delta_color="inverse"
        )
    with kpi2:
        st.metric(
            "PM10 (Coarse)",
            f"{pm10_val:.1f} µg/m³" if pm10_val is not None else "N/A",
            delta=f"{pm10_val - 100.0:+.1f} vs NAAQS" if pm10_val is not None else None,
            delta_color="inverse"
        )
    with kpi3:
        st.metric(
            "NO2",
            f"{no2_val:.1f} µg/m³" if no2_val is not None else "N/A",
            delta=f"{no2_val - 80.0:+.1f} vs NAAQS" if no2_val is not None else None,
            delta_color="inverse"
        )
    with kpi4:
        st.metric("SO2", f"{so2_val:.1f} µg/m³" if so2_val is not None else "N/A")
    with kpi5:
        st.metric("CO", f"{co_val:.2f} mg/m³" if co_val is not None else "N/A")
    with kpi6:
        st.metric("Ozone (O3)", f"{o3_val:.1f} µg/m³" if o3_val is not None else "N/A")

    st.markdown("---")

    # 4. Hourly 48-Hour Historical & Forecast Trajectory
    st.subheader(f"📈 48-Hour Hourly Trajectory & Forecast ({target_name})")
    st.caption("Temporal diurnal cycle: past 24 hours observed + next 24 hours forecasted")

    hourly_df = live_data.get("Hourly_Data")
    if hourly_df is not None and not hourly_df.empty:
        fig_hourly = go.Figure()

        fig_hourly.add_trace(go.Scatter(
            x=hourly_df["Timestamp"],
            y=hourly_df["PM2.5"],
            mode="lines+markers",
            name="PM2.5 (Fine Particulates)",
            line=dict(color=AERIS_PALETTE["primary"], width=2.5),
            marker=dict(size=4)
        ))

        fig_hourly.add_trace(go.Scatter(
            x=hourly_df["Timestamp"],
            y=hourly_df["PM10"],
            mode="lines",
            name="PM10 (Coarse Particulates)",
            line=dict(color=AERIS_PALETTE["secondary"], width=2, dash="dot")
        ))

        fig_hourly.add_hline(
            y=60.0,
            line_dash="dash",
            line_color=AERIS_PALETTE["danger"],
            annotation_text="NAAQS 24-hr PM2.5 Limit (60 µg/m³)",
            annotation_position="top right"
        )

        fig_hourly.update_layout(
            template="plotly_white",
            xaxis_title="Time (Local IST)",
            yaxis_title="Concentration (µg/m³)",
            hovermode="x unified",
            height=380,
            margin=dict(l=20, r=20, t=40, b=20)
        )
        st.plotly_chart(fig_hourly, use_container_width=True)

    # 5. Local Risk Advisory
    st.markdown("---")
    st.subheader("🛡️ Environmental Health Precautions & Action Advisory")

    cat = live_data["AQI_Category"]
    if cat in ["Poor", "Very Poor", "Severe"]:
        st.warning(
            f"⚠️ **Advisory for {cat} Air Quality:** Vulnerable populations (children, elderly, individuals with respiratory "
            f"or cardiac conditions) should restrict outdoor physical exertion. N95 filtration masks recommended during commute."
        )
    elif cat == "Moderate":
        st.info(
            f"ℹ️ **Advisory for Moderate Air Quality:** Air quality is acceptable; however, sensitive individuals may experience minor "
            f"breathing discomfort during prolonged high-intensity outdoor activities."
        )
    else:
        st.success(
            f"✅ **Advisory for {cat} Air Quality:** Air pollution poses little to no risk. Outdoor activities and natural ventilation "
            f"are ideal."
        )
