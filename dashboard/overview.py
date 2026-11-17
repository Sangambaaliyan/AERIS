"""AERIS Dashboard - Page 1: Overview
Executive Summary, High-Level KPIs, Multi-City Snapshot, and Regulatory Benchmarks.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from src.analysis import (
    calculate_descriptive_statistics,
    plot_city_comparison_bar,
    plot_temporal_trend,
    AERIS_PALETTE,
)
from src.preprocessing import NAAQS_STANDARDS


def render_overview_page(df: pd.DataFrame, data_summary) -> None:
    """Renders the executive overview and system summary dashboard."""
    st.markdown("## 🌐 Executive Environmental Overview")
    st.caption("AERIS Atmospheric Intelligence Summary across monitored urban airsheds")

    if df.empty:
        st.warning("⚠️ No data available to render the overview. Please load or upload a valid dataset.")
        return

    # 1. High-Level KPI Metric Cards
    col1, col2, col3, col4, col5 = st.columns(5)

    total_records = len(df)
    num_cities = df["City"].nunique() if "City" in df.columns else 0
    num_stations = df["Station"].nunique() if "Station" in df.columns else 0

    pm25_mean = df["PM2.5"].dropna().mean() if "PM2.5" in df.columns else np.nan
    pm10_mean = df["PM10"].dropna().mean() if "PM10" in df.columns else np.nan

    with col1:
        st.metric(
            label="Total Records Analyzed",
            value=f"{total_records:,}",
            help="Total validated ambient air quality records after quality filtering."
        )

    with col2:
        st.metric(
            label="Urban Airsheds",
            value=f"{num_cities} Cities",
            help="Number of distinct municipal metropolitan areas analyzed."
        )

    with col3:
        st.metric(
            label="Monitoring Stations",
            value=f"{num_stations} Stations",
            help="Continuous Ambient Air Quality Monitoring Stations (CAAQMS)."
        )

    with col4:
        pm25_val_str = f"{pm25_mean:.1f} µg/m³" if not np.isnan(pm25_mean) else "N/A"
        pm25_delta = f"{pm25_mean - 60.0:+.1f} vs NAAQS" if not np.isnan(pm25_mean) else None
        st.metric(
            label="Avg PM2.5 Concentration",
            value=pm25_val_str,
            delta=pm25_delta,
            delta_color="inverse",
            help="NAAQS 24-hour safe threshold is 60.0 µg/m³."
        )

    with col5:
        pm10_val_str = f"{pm10_mean:.1f} µg/m³" if not np.isnan(pm10_mean) else "N/A"
        pm10_delta = f"{pm10_mean - 100.0:+.1f} vs NAAQS" if not np.isnan(pm10_mean) else None
        st.metric(
            label="Avg PM10 Concentration",
            value=pm10_val_str,
            delta=pm10_delta,
            delta_color="inverse",
            help="NAAQS 24-hour safe threshold is 100.0 µg/m³."
        )

    st.markdown("---")

    # 2. Main Visualizations Row
    left_col, right_col = st.columns([1, 1])

    with left_col:
        st.subheader("🏙️ City Particulate Concentrations")
        st.caption("Comparison of fine (PM2.5) and coarse (PM10) particulate concentrations")

        if "PM2.5" in df.columns and "City" in df.columns:
            city_pm = df.groupby("City")[["PM2.5"] + (["PM10"] if "PM10" in df.columns else [])].mean().reset_index()
            city_pm = city_pm.sort_values("PM2.5", ascending=True)

            fig_bar = go.Figure()
            fig_bar.add_trace(go.Bar(
                y=city_pm["City"],
                x=city_pm["PM2.5"],
                name="PM2.5 (Fine)",
                orientation="h",
                marker=dict(color=AERIS_PALETTE["primary"]),
                hovertemplate="<b>%{y}</b><br>PM2.5: %{x:.1f} µg/m³<extra></extra>"
            ))
            if "PM10" in city_pm.columns:
                fig_bar.add_trace(go.Bar(
                    y=city_pm["City"],
                    x=city_pm["PM10"],
                    name="PM10 (Coarse)",
                    orientation="h",
                    marker=dict(color=AERIS_PALETTE["secondary"]),
                    hovertemplate="<b>%{y}</b><br>PM10: %{x:.1f} µg/m³<extra></extra>"
                ))

            fig_bar.add_vline(x=60, line_dash="dash", line_color=AERIS_PALETTE["danger"], annotation_text="PM2.5 Safe Limit (60)")
            fig_bar.update_layout(
                barmode="group",
                xaxis_title="Concentration (µg/m³)",
                yaxis_title="City",
                template="plotly_white",
                legend=dict(orientation="h", y=1.1, x=1, xanchor="right"),
                margin=dict(l=20, r=20, t=40, b=20),
                height=380
            )
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("Particulate columns (PM2.5, PM10) are not available in current dataset.")

    with right_col:
        st.subheader("📈 Multi-Year Temporal Profile")
        st.caption("Smoothed 30-day moving average trajectory across primary airsheds")
        if "PM2.5" in df.columns and "Date" in df.columns:
            fig_trend = plot_temporal_trend(df, pollutant="PM2.5", rolling_window=30, show_naaqs=True)
            fig_trend.update_layout(height=380, margin=dict(l=20, r=20, t=40, b=20))
            st.plotly_chart(fig_trend, use_container_width=True)
        else:
            st.info("Temporal trend analysis requires Date and PM2.5 columns.")

    st.markdown("---")

    # 3. Quick Airshed Standings Table & Regulatory Standards
    bot_left, bot_right = st.columns([3, 2])

    with bot_left:
        st.subheader("📋 Airshed Compliance Summary")
        st.caption("City-wise particulate averages, standard deviations, and regulatory exceedance rates")

        summary_table = calculate_descriptive_statistics(df, pollutants=["PM2.5"], group_by="City")
        if not summary_table.empty:
            display_cols = ["City", "Mean", "Median", "Std Dev", "Max", "Exceedance Rate (%)"]
            formatted_table = summary_table[display_cols].sort_values("Mean", ascending=False).reset_index(drop=True)
            st.dataframe(
                formatted_table.style.format({
                    "Mean": "{:.1f}",
                    "Median": "{:.1f}",
                    "Std Dev": "{:.1f}",
                    "Max": "{:.1f}",
                    "Exceedance Rate (%)": "{:.1f}%"
                }),
                use_container_width=True,
                height=280
            )
        else:
            st.info("No city-level descriptive statistics calculated.")

    with bot_right:
        st.subheader("📜 CPCB NAAQS Standard Guidelines")
        st.caption("National Ambient Air Quality Standards (24-Hour Limits, 2009 Gazette)")

        standards_df = pd.DataFrame([
            {"Pollutant": "PM2.5 (Fine Particulates)", "Standard": "60 µg/m³", "Averaging Period": "24 Hours"},
            {"Pollutant": "PM10 (Coarse Particulates)", "Standard": "100 µg/m³", "Averaging Period": "24 Hours"},
            {"Pollutant": "NO2 (Nitrogen Dioxide)", "Standard": "80 µg/m³", "Averaging Period": "24 Hours"},
            {"Pollutant": "SO2 (Sulfur Dioxide)", "Standard": "80 µg/m³", "Averaging Period": "24 Hours"},
            {"Pollutant": "CO (Carbon Monoxide)", "Standard": "2.0 mg/m³", "Averaging Period": "8 Hours"},
            {"Pollutant": "O3 (Ground Ozone)", "Standard": "100 µg/m³", "Averaging Period": "8 Hours"},
        ])
        st.dataframe(standards_df, use_container_width=True, hide_index=True, height=280)
