"""AERIS Dashboard - Page 3: Temporal Analysis
Multi-Scale Temporal Profiling, Seasonal Dynamics, Cyclical Patterns, and Correlations.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from src.analysis import (
    plot_temporal_trend,
    plot_monthly_seasonal_patterns,
    compute_correlation_matrix,
    plot_correlation_heatmap,
    AERIS_PALETTE,
)
from src.preprocessing import NAAQS_STANDARDS


def render_temporal_analysis_page(df: pd.DataFrame) -> None:
    """Renders the temporal dynamics, seasonal breakdown, and correlation analytics."""
    st.markdown("## ⏳ Temporal & Seasonal Analysis")
    st.caption("Investigate annual trends, seasonal shifts, cyclical variations, and multi-pollutant correlations")

    if df.empty or "Date" not in df.columns:
        st.warning("⚠️ No valid temporal records available for trend analysis.")
        return

    # Filter Controls
    min_date = df["Date"].min().date()
    max_date = df["Date"].max().date()
    all_cities = sorted(df["City"].dropna().unique().tolist())
    available_pollutants = [p for p in NAAQS_STANDARDS.keys() if p in df.columns]

    c_col1, c_col2, c_col3 = st.columns([2, 1, 1])

    with c_col1:
        date_range = st.date_input(
            "Select Date Filter Range:",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date,
            help="Filter analysis window between start and end dates."
        )

    with c_col2:
        selected_city = st.selectbox(
            "Filter by City (Optional):",
            options=["All Cities"] + all_cities,
            index=0
        )

    with c_col3:
        selected_pollutant = st.selectbox(
            "Target Pollutant:",
            options=available_pollutants,
            index=0
        )

    # Process Date Range
    if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
        start_d, end_d = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
        filtered_df = df[(df["Date"] >= start_d) & (df["Date"] <= end_d)].copy()
    else:
        filtered_df = df.copy()

    if selected_city != "All Cities":
        filtered_df = filtered_df[filtered_df["City"] == selected_city]

    if filtered_df.empty:
        st.warning("No records match the selected date and city filters.")
        return

    unit = "mg/m³" if selected_pollutant == "CO" else "µg/m³"

    # Tabbed Temporal Views
    tab1, tab2, tab3 = st.tabs(["📅 Seasonal & Monthly Dynamics", "📊 Yearly Trajectory & Heatmap", "🔗 Inter-Pollutant Correlations"])

    with tab1:
        st.subheader(f"🍂 IMD Seasonal Pollution Contrast ({selected_pollutant})")
        st.caption("Distribution across Winter, Summer, Monsoon, and Post-Monsoon seasons")

        if "Season" in filtered_df.columns:
            s_col1, s_col2 = st.columns([1, 1])

            with s_col1:
                season_order = ["Winter", "Summer", "Monsoon", "Post-Monsoon"]
                seasonal_stats = filtered_df.groupby("Season")[selected_pollutant].agg(
                    Mean="mean", Median="median", Max="max", Std="std"
                ).reindex(season_order).reset_index()

                fig_season_bar = px.bar(
                    seasonal_stats,
                    x="Season",
                    y="Mean",
                    color="Season",
                    text_auto=".1f",
                    color_discrete_map={
                        "Winter": "#3B82F6",
                        "Summer": "#F59E0B",
                        "Monsoon": "#10B981",
                        "Post-Monsoon": "#EF4444"
                    },
                    title=f"Mean {selected_pollutant} by Season",
                    labels={"Mean": f"Mean {selected_pollutant} ({unit})"}
                )
                limit = NAAQS_STANDARDS.get(selected_pollutant, np.nan)
                if not np.isnan(limit):
                    fig_season_bar.add_hline(y=limit, line_dash="dash", line_color=AERIS_PALETTE["danger"], annotation_text="NAAQS Limit")
                fig_season_bar.update_layout(template="plotly_white", height=380, showlegend=False)
                st.plotly_chart(fig_season_bar, use_container_width=True)

            with s_col2:
                fig_season_box = px.box(
                    filtered_df,
                    x="Season",
                    y=selected_pollutant,
                    color="Season",
                    category_orders={"Season": season_order},
                    color_discrete_map={
                        "Winter": "#3B82F6",
                        "Summer": "#F59E0B",
                        "Monsoon": "#10B981",
                        "Post-Monsoon": "#EF4444"
                    },
                    title=f"{selected_pollutant} Dispersion by Season"
                )
                if not np.isnan(limit):
                    fig_season_box.add_hline(y=limit, line_dash="dash", line_color=AERIS_PALETTE["danger"])
                fig_season_box.update_layout(template="plotly_white", height=380, showlegend=False)
                st.plotly_chart(fig_season_box, use_container_width=True)

            # Monthly Cycle Plot
            st.markdown("---")
            st.subheader(f"📈 Monthly Multi-Year Cyclical Patterns ({selected_pollutant})")
            fig_cycle = plot_monthly_seasonal_patterns(
                filtered_df,
                pollutant=selected_pollutant,
                city=None if selected_city == "All Cities" else selected_city
            )
            fig_cycle.update_layout(height=400)
            st.plotly_chart(fig_cycle, use_container_width=True)

    with tab2:
        st.subheader("🗓️ Year × Month Pollution Matrix Heatmap")
        st.caption("Visual matrix illustrating annual progression and seasonal pollution peaks")

        if "Year" in filtered_df.columns and "Month" in filtered_df.columns:
            pivot_matrix = filtered_df.pivot_table(
                index="Year",
                columns="Month_Name",
                values=selected_pollutant,
                aggfunc="mean"
            )
            month_cols = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
            pivot_matrix = pivot_matrix.reindex(columns=[m for m in month_cols if m in pivot_matrix.columns])

            fig_matrix = px.imshow(
                pivot_matrix,
                text_auto=".1f",
                aspect="auto",
                color_continuous_scale="YlOrRd",
                labels=dict(color=f"{selected_pollutant} ({unit})"),
                title=f"Yearly-Monthly {selected_pollutant} Heatmap Matrix"
            )
            fig_matrix.update_layout(template="plotly_white", height=380)
            st.plotly_chart(fig_matrix, use_container_width=True)

            # Yearly Aggregates
            st.markdown("---")
            st.subheader(f"📊 Annual Trends & Year-over-Year Progression")
            annual_df = filtered_df.groupby("Year")[selected_pollutant].agg(
                Mean="mean", Median="median", Std="std", Max="max", Count="count"
            ).reset_index()
            annual_df["YoY Change (%)"] = annual_df["Mean"].pct_change() * 100.0

            st.dataframe(
                annual_df.style.format({
                    "Mean": "{:.1f}",
                    "Median": "{:.1f}",
                    "Std": "{:.1f}",
                    "Max": "{:.1f}",
                    "YoY Change (%)": "{:+.1f}%",
                    "Count": "{:,}"
                }),
                use_container_width=True
            )

    with tab3:
        st.subheader("🔗 Inter-Pollutant Correlation Matrix")
        st.caption("Statistical Pearson and Spearman correlation analysis across co-monitored pollutants")

        method = st.radio("Correlation Method:", options=["Pearson (Linear)", "Spearman (Rank-order)"], horizontal=True)
        corr_method = "pearson" if "Pearson" in method else "spearman"

        corr_df, p_vals = compute_correlation_matrix(filtered_df, pollutants=available_pollutants, method=corr_method)

        if not corr_df.empty:
            h_col1, h_col2 = st.columns([3, 2])
            with h_col1:
                fig_heatmap = plot_correlation_heatmap(corr_df)
                fig_heatmap.update_layout(height=420)
                st.plotly_chart(fig_heatmap, use_container_width=True)

            with h_col2:
                st.markdown("#### Statistical Significance (P-Values)")
                st.caption("P-values < 0.05 signify statistically significant correlations.")
                st.dataframe(
                    p_vals.style.format(lambda v: "< 0.001" if v < 0.001 else f"{v:.4f}"),
                    use_container_width=True,
                    height=360
                )
        else:
            st.info("Insufficient multi-pollutant records to compute correlation matrix.")
