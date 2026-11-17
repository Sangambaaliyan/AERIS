"""AERIS Dashboard - Page 4: Risk Analysis & Insights
Pollution Hotspots, Cumulative Exposure Indicator (CEI), Statistical Anomaly Detection,
and Dynamic Environmental Evidence Reporting.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from src.risk_analysis import (
    calculate_cumulative_exposure_indicator,
    identify_pollution_hotspots,
    detect_unusual_observations,
    calculate_frequency_analysis,
    generate_data_driven_insights,
    ExposureIndicatorMetadata,
    DEFAULT_POLLUTANT_WEIGHTS,
)
from src.analysis import AERIS_PALETTE
from src.preprocessing import NAAQS_STANDARDS


def render_risk_analysis_page(df: pd.DataFrame) -> None:
    """Renders the environmental risk intelligence, hotspot, and anomaly detection dashboard."""
    st.markdown("## ⚠️ Environmental Risk Intelligence & Hotspots")
    st.caption("Identify chronic pollution hotspots, detect extreme episodic anomalies, and evaluate cumulative exposure")

    if df.empty:
        st.warning("⚠️ No valid records available for risk intelligence modeling.")
        return

    available_pollutants = [p for p in NAAQS_STANDARDS.keys() if p in df.columns]

    # Tabs for distinct analytical angles
    tab_hotspots, tab_cei, tab_anomalies, tab_frequency, tab_insights = st.tabs([
        "🔥 Hotspot Identification",
        "📐 Cumulative Exposure (CEI)",
        "⚡ Anomaly Detection",
        "📊 Exceedance Frequencies",
        "📝 Automated Intelligence Report"
    ])

    # =========================================================================
    # TAB 1: HOTSPOT IDENTIFICATION
    # =========================================================================
    with tab_hotspots:
        st.subheader("🔥 Urban Pollution Hotspot Ranking")
        st.caption("Ranking based on multi-year chronic concentration and 24-hr regulatory exceedance frequency")

        h_pollutant = st.selectbox(
            "Primary Pollutant for Hotspot Modeling:",
            options=available_pollutants,
            index=0 if "PM2.5" in available_pollutants else 0,
            key="hotspot_pollutant"
        )

        hotspot_df = identify_pollution_hotspots(df, primary_pollutant=h_pollutant, group_by="City")

        if not hotspot_df.empty:
            c1, c2 = st.columns([3, 2])

            with c1:
                fig_hotspot = px.bar(
                    hotspot_df,
                    x="City",
                    y="Hotspot Score",
                    color="Hotspot Status",
                    text_auto=".1f",
                    color_discrete_map={
                        "Critical Hotspot": AERIS_PALETTE["danger"],
                        "Moderate Hotspot": AERIS_PALETTE["warning"],
                        "Low Risk Area": AERIS_PALETTE["accent"]
                    },
                    title=f"AERIS Hotspot Score by City ({h_pollutant})",
                    labels={"Hotspot Score": "Hotspot Index (0-100)"}
                )
                fig_hotspot.update_layout(template="plotly_white", height=380)
                st.plotly_chart(fig_hotspot, use_container_width=True)

            with c2:
                st.markdown("#### Top Ranked Hotspots")
                for _, row in hotspot_df.head(3).iterrows():
                    color = (
                        AERIS_PALETTE["danger"] if row["Hotspot Status"] == "Critical Hotspot"
                        else AERIS_PALETTE["warning"] if row["Hotspot Status"] == "Moderate Hotspot"
                        else AERIS_PALETTE["accent"]
                    )
                    st.markdown(
                        f"""
                        <div style="border-left: 4px solid {color}; padding: 8px 12px; margin-bottom: 8px; background: #f8fafc; border-radius: 4px;">
                            <strong style="font-size: 1.05rem;">#{row['Rank']} {row['City']}</strong> &nbsp;
                            <span style="color: {color}; font-weight: bold;">{row['Hotspot Status']}</span><br>
                            <small>Hotspot Score: <b>{row['Hotspot Score']}/100</b> | Exceedance Rate: <b>{row['Exceedance Rate (%)']}%</b></small><br>
                            <small>Mean {h_pollutant}: <b>{row[f'Mean {h_pollutant}']}</b> | 90th Pct: <b>{row['90th Percentile']}</b></small>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

            st.markdown("---")
            st.subheader("📋 Comprehensive Hotspot Diagnostic Leaderboard")
            st.dataframe(hotspot_df, use_container_width=True, hide_index=True)

    # =========================================================================
    # TAB 2: CUMULATIVE EXPOSURE INDICATOR (CEI)
    # =========================================================================
    with tab_cei:
        st.subheader("📐 Cumulative Exposure Indicator (CEI)")
        st.caption("Research-grade normalized aggregate multi-pollutant exposure assessment")

        cei_df, metadata = calculate_cumulative_exposure_indicator(df, group_by="City")

        # Mathematical Transparency Card
        with st.expander("📖 Mathematical Formulation & Weighting Rationale (Click to Expand)", expanded=True):
            st.markdown(
                f"""
                **Mathematical Formula:**
                $$CEI = \\left[ \\sum_{{i \\in P}} w_i \\times \\frac{{\\bar{{C}}_i}}{{NAAQS_i}} \\right] \\times 100 \\times \\left( \\frac{{N_{{obs}}}}{{N_{{total}}}} \\right)^{{\\gamma}}$$
                
                - **Where:**
                  - $P$: Set of available pollutants monitored at the airshed.
                  - $\\bar{{C}}_i$: Mean concentration of pollutant $i$.
                  - $NAAQS_i$: CPCB 24-hr standard benchmark (PM2.5: 60, PM10: 100, NO2: 80, SO2: 80, CO: 2.0, O3: 100).
                  - $w_i$: Health hazard weights normalized to $\\sum w_i = 1.0$ (PM2.5: 0.40, PM10: 0.25, NO2: 0.15, SO2: 0.10, CO: 0.05, O3: 0.05).
                  - $\\left( \\frac{{N_{{obs}}}}{{N_{{total}}}} \\right)^{{\\gamma}}$: Data completeness adjustment factor (penalizes sparse monitoring networks, default $\\gamma = 0.5$).
                
                > **Important Distinction from Official AQI:**  
                > {metadata.distinction_from_aqi}
                
                > **Medical & Diagnostic Disclaimer:**  
                > {metadata.medical_disclaimer}
                """
            )

        if not cei_df.empty:
            st.markdown("### Cumulative Exposure Standings")
            st.caption("A CEI score of 100 represents exact cumulative alignment with NAAQS benchmark thresholds.")

            col_chart, col_table = st.columns([3, 2])

            with col_chart:
                fig_cei = px.bar(
                    cei_df,
                    x="City",
                    y="AERIS CEI Score",
                    color="Risk Tier",
                    text_auto=".1f",
                    color_discrete_map={
                        "Severe Risk": "#EF4444",
                        "High Risk": "#F97316",
                        "Moderate Risk": "#F59E0B",
                        "Standard Compliant": "#0D9488",
                        "Low Exposure": "#10B981"
                    },
                    title="AERIS Cumulative Exposure Indicator (CEI) by Airshed",
                    labels={"AERIS CEI Score": "CEI Score (100 = NAAQS Benchmark)"}
                )
                fig_cei.add_hline(y=100, line_dash="dash", line_color="#334155", annotation_text="NAAQS Baseline (100)")
                fig_cei.update_layout(template="plotly_white", height=380)
                st.plotly_chart(fig_cei, use_container_width=True)

            with col_table:
                st.markdown("#### Risk Tier Summary")
                for _, r in cei_df.iterrows():
                    st.markdown(
                        f"""
                        <div style="padding: 6px 10px; margin-bottom: 6px; border-left: 3px solid {r['Color Code']}; background: #f8fafc;">
                            <b>#{r['Exposure Rank']} {r['City']}</b> — <span style="color: {r['Color Code']}; font-weight: 600;">{r['Risk Tier']}</span><br>
                            <small>CEI Score: <b>{r['AERIS CEI Score']}</b> | Observational Completeness: <b>{r['Data Completeness (%)']}%</b></small>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

            st.markdown("---")
            st.subheader("📋 Multi-Pollutant Normalization Breakdown")
            display_cols = [c for c in cei_df.columns if c not in ["Color Code"]]
            st.dataframe(cei_df[display_cols], use_container_width=True, hide_index=True)

    # =========================================================================
    # TAB 3: STATISTICAL ANOMALY DETECTION
    # =========================================================================
    with tab_anomalies:
        st.subheader("⚡ Statistical Anomaly & Extreme Event Detection")
        st.caption("Detect episodic spikes, crop burning surges, festival emission peaks, and unusual weather events")

        a_col1, a_col2, a_col3 = st.columns([1, 1, 1])

        with a_col1:
            anomaly_pollutant = st.selectbox("Anomaly Pollutant:", options=available_pollutants, index=0)

        with a_col2:
            detect_method = st.radio("Detection Methodology:", options=["IQR Method", "Modified Z-Score (MAD)"], horizontal=True)
            method_key = "iqr" if "IQR" in detect_method else "modified_z"

        with a_col3:
            if method_key == "iqr":
                threshold_param = st.slider("IQR Multiplier:", min_value=1.0, max_value=3.5, value=1.5, step=0.25)
            else:
                threshold_param = st.slider("Modified Z Threshold:", min_value=2.0, max_value=5.0, value=3.0, step=0.5)

        anomalies_df = detect_unusual_observations(
            df,
            pollutant=anomaly_pollutant,
            method=method_key,
            iqr_multiplier=threshold_param if method_key == "iqr" else 1.5,
            z_threshold=threshold_param if method_key == "modified_z" else 3.0
        )

        st.metric(
            label="Total Unusual Observations Detected",
            value=f"{len(anomalies_df)} Events",
            help="Number of daily readings statistically exceeding normal baseline bounds."
        )

        if not anomalies_df.empty:
            # Anomaly Timeline Scatter Chart
            fig_anom = px.scatter(
                anomalies_df,
                x="Date",
                y=anomaly_pollutant,
                color="City",
                size="Anomaly Magnitude (x Baseline)",
                hover_data=["Station", "City Median", "Threshold", "Season"],
                title=f"Detected {anomaly_pollutant} Anomalous Peak Events Over Time"
            )
            fig_anom.update_layout(template="plotly_white", height=380)
            st.plotly_chart(fig_anom, use_container_width=True)

            st.markdown("#### 📋 Detected Anomaly Event Log")
            st.dataframe(anomalies_df, use_container_width=True, hide_index=True)
        else:
            st.success(f"No statistical anomalies detected for {anomaly_pollutant} at current sensitivity thresholds.")

    # =========================================================================
    # TAB 4: EXCEEDANCE FREQUENCY ANALYSIS
    # =========================================================================
    with tab_frequency:
        st.subheader("📊 Regulatory Exceedance Frequency Analysis")
        st.caption("Categorization of observations into standard regulatory risk bands")

        freq_pollutant = st.selectbox("Select Pollutant for Frequency Analysis:", options=available_pollutants, index=0, key="freq_pol")
        freq_df = calculate_frequency_analysis(df, pollutant=freq_pollutant)

        if not freq_df.empty:
            f1, f2 = st.columns([3, 2])

            with f1:
                fig_freq = px.bar(
                    freq_df,
                    x="Air Quality Tier",
                    y="Percentage of Observations (%)",
                    text_auto=".1f",
                    color="Air Quality Tier",
                    color_discrete_sequence=["#10B981", "#0D9488", "#F59E0B", "#F97316", "#EF4444"],
                    title=f"Frequency Breakdown of {freq_pollutant} Readings"
                )
                fig_freq.update_layout(template="plotly_white", showlegend=False, height=380)
                st.plotly_chart(fig_freq, use_container_width=True)

            with f2:
                fig_pie = px.pie(
                    freq_df,
                    names="Air Quality Tier",
                    values="Day Count",
                    color="Air Quality Tier",
                    color_discrete_sequence=["#10B981", "#0D9488", "#F59E0B", "#F97316", "#EF4444"],
                    title="Proportion of Monitored Days",
                    hole=0.4
                )
                fig_pie.update_layout(height=380, margin=dict(l=20, r=20, t=40, b=20))
                st.plotly_chart(fig_pie, use_container_width=True)

            st.dataframe(freq_df, use_container_width=True, hide_index=True)

    # =========================================================================
    # TAB 5: AUTOMATED INTELLIGENCE REPORT
    # =========================================================================
    with tab_insights:
        st.subheader("📝 Dynamic Environmental Intelligence Findings")
        st.caption("Evidence-based findings generated from quantitative calculations on the active dataset")

        p_for_insights = st.selectbox("Generate Findings For:", options=available_pollutants, index=0, key="insights_pol")
        insights_list = generate_data_driven_insights(df, primary_pollutant=p_for_insights)

        for ins in insights_list:
            st.markdown(f"- {ins}")

        # Download findings report as markdown
        st.markdown("---")
        report_text = f"# AERIS Environmental Intelligence Report\n\n"
        report_text += f"Target Pollutant: {p_for_insights}\n"
        report_text += f"Date of Generation: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        report_text += "## Quantitative Findings:\n\n"
        for idx, ins in enumerate(insights_list, 1):
            clean_line = ins.replace("**", "")
            report_text += f"{idx}. {clean_line}\n"

        st.download_button(
            label="📥 Download Analytical Findings Report (.txt)",
            data=report_text,
            file_name=f"AERIS_Intelligence_Report_{p_for_insights}.txt",
            mime="text/plain"
        )
