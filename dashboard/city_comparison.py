"""AERIS Dashboard - Page 2: City Comparison
Cross-City Comparative Analysis, Multi-Pollutant Standings, and Distribution Profiles.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from src.analysis import (
    calculate_descriptive_statistics,
    plot_city_comparison_bar,
    plot_distribution_boxplot,
    plot_temporal_trend,
    AERIS_PALETTE,
    CITY_COLOR_SEQUENCE,
)
from src.preprocessing import NAAQS_STANDARDS


def render_city_comparison_page(df: pd.DataFrame) -> None:
    """Renders the cross-city comparative analytics interface."""
    st.markdown("## 🏙️ Cross-City Comparative Analysis")
    st.caption("Benchmark air quality profiles, distribution spreads, and exceedance metrics across selected cities")

    if df.empty or "City" not in df.columns:
        st.warning("⚠️ No valid city records available for comparative analysis.")
        return

    # Filter Controls Row
    all_cities = sorted(df["City"].dropna().unique().tolist())
    available_pollutants = [p for p in NAAQS_STANDARDS.keys() if p in df.columns]

    if not available_pollutants:
        st.warning("No recognized pollutant columns found in the dataset.")
        return

    f_col1, f_col2, f_col3 = st.columns([2, 1, 1])

    with f_col1:
        selected_cities = st.multiselect(
            "Select Cities to Compare:",
            options=all_cities,
            default=all_cities[:min(5, len(all_cities))],
            help="Choose two or more cities to perform comparative benchmarking."
        )

    with f_col2:
        selected_pollutant = st.selectbox(
            "Primary Pollutant:",
            options=available_pollutants,
            index=0 if "PM2.5" in available_pollutants else 0,
            help="Select the air contaminant for comparison."
        )

    with f_col3:
        comparison_metric = st.selectbox(
            "Statistical Metric:",
            options=["Mean", "Median", "Max", "Std Dev"],
            index=0,
            help="Aggregation metric for ranking bars."
        )

    if not selected_cities:
        st.info("Please select at least one city from the dropdown above.")
        return

    # Filtered dataframe
    city_df = df[df["City"].isin(selected_cities)].copy()
    unit = "mg/m³" if selected_pollutant == "CO" else "µg/m³"
    limit = NAAQS_STANDARDS.get(selected_pollutant, np.nan)

    # Key Comparative Insights Callout
    city_stats = city_df.groupby("City")[selected_pollutant].agg(["mean", "median", "max", "std"]).reset_index()
    if not city_stats.empty:
        highest_row = city_stats.sort_values("mean", ascending=False).iloc[0]
        lowest_row = city_stats.sort_values("mean", ascending=True).iloc[0]
        ratio = round(highest_row["mean"] / (lowest_row["mean"] if lowest_row["mean"] > 0 else 1.0), 1)

        st.info(
            f"💡 **Comparative Insight:** Among selected cities, **{highest_row['City']}** demonstrates the highest average "
            f"{selected_pollutant} concentration (**{highest_row['mean']:.1f} {unit}**), approximately "
            f"**{ratio}x** that of **{lowest_row['City']}** (**{lowest_row['mean']:.1f} {unit}**)."
        )

    # Visualizations Row 1: Ranked Bars & Boxplots
    v_col1, v_col2 = st.columns([1, 1])

    with v_col1:
        st.subheader(f"📊 Ranked {comparison_metric} {selected_pollutant}")
        fig_bar = plot_city_comparison_bar(city_df, pollutant=selected_pollutant, metric=comparison_metric)
        fig_bar.update_layout(height=400)
        st.plotly_chart(fig_bar, use_container_width=True)

    with v_col2:
        st.subheader("📦 Dispersion & Quartile Distribution")
        fig_box = plot_distribution_boxplot(city_df, pollutant=selected_pollutant, group_by="City")
        fig_box.update_layout(height=400)
        st.plotly_chart(fig_box, use_container_width=True)

    st.markdown("---")

    # Time-Series Trajectory of Selected Cities
    st.subheader(f"📈 Comparative Time-Series Trajectory ({selected_pollutant})")
    smooth_days = st.slider("Smoothing Window (Moving Average Days):", min_value=1, max_value=60, value=14, step=1)
    fig_line = plot_temporal_trend(
        city_df,
        pollutant=selected_pollutant,
        cities=selected_cities,
        rolling_window=smooth_days,
        show_naaqs=True
    )
    fig_line.update_layout(height=420)
    st.plotly_chart(fig_line, use_container_width=True)

    st.markdown("---")

    # Detailed Statistical Breakdown Table
    st.subheader("📋 Comprehensive Statistical Profile")
    st.caption(f"Descriptive metrics for {selected_pollutant} across selected airsheds")

    table_df = calculate_descriptive_statistics(city_df, pollutants=[selected_pollutant], group_by="City")
    if not table_df.empty:
        cols_to_show = ["City", "Count", "Mean", "Median", "Std Dev", "Min", "Q1 (25%)", "Q3 (75%)", "Max", "Exceedance Rate (%)"]
        formatted_df = table_df[cols_to_show].sort_values("Mean", ascending=False).reset_index(drop=True)
        st.dataframe(
            formatted_df.style.format({
                "Mean": "{:.1f}",
                "Median": "{:.1f}",
                "Std Dev": "{:.1f}",
                "Min": "{:.1f}",
                "Q1 (25%)": "{:.1f}",
                "Q3 (75%)": "{:.1f}",
                "Max": "{:.1f}",
                "Exceedance Rate (%)": "{:.1f}%",
                "Count": "{:,}"
            }),
            use_container_width=True
        )
