"""AERIS Dashboard - Page 5: Data Explorer & Quality Audit
Interactive Dataset Inspection, Data Quality Summaries, Multi-Criteria Filtering, and CSV Export.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from src.database import save_dataset_to_db, list_tables_in_db, load_dataset_from_db


def render_data_explorer_page(df: pd.DataFrame, summary) -> None:
    """Renders the interactive data explorer, audit summary, and export panel."""
    st.markdown("## 🔍 Data Explorer & Quality Audit")
    st.caption("Inspect cleaned observations, examine missingness and cleaning audits, and export filtered datasets")

    if df.empty:
        st.warning("⚠️ No dataset currently loaded.")
        return

    tab_data, tab_audit, tab_database = st.tabs([
        "📄 Interactive Data Records",
        "🛡️ Data Quality & Audit Summary",
        "💾 SQLite Local Persistence"
    ])

    # =========================================================================
    # TAB 1: INTERACTIVE DATA RECORDS & FILTERING
    # =========================================================================
    with tab_data:
        st.subheader("Filter and Explore Observations")

        all_cities = sorted(df["City"].dropna().unique().tolist()) if "City" in df.columns else []
        all_stations = sorted(df["Station"].dropna().unique().tolist()) if "Station" in df.columns else []

        f1, f2, f3 = st.columns([1, 1, 1])
        with f1:
            sel_cities = st.multiselect("Filter Cities:", options=all_cities, default=all_cities)
        with f2:
            sel_stations = st.multiselect("Filter Stations:", options=all_stations, default=all_stations)
        with f3:
            if "Season" in df.columns:
                all_seasons = sorted(df["Season"].dropna().unique().tolist())
                sel_seasons = st.multiselect("Filter Seasons:", options=all_seasons, default=all_seasons)
            else:
                sel_seasons = []

        filtered_df = df.copy()
        if sel_cities:
            filtered_df = filtered_df[filtered_df["City"].isin(sel_cities)]
        if sel_stations:
            filtered_df = filtered_df[filtered_df["Station"].isin(sel_stations)]
        if sel_seasons:
            filtered_df = filtered_df[filtered_df["Season"].isin(sel_seasons)]

        st.markdown(f"**Showing {len(filtered_df):,} of {len(df):,} records**")
        st.dataframe(filtered_df, use_container_width=True, height=450)

        # CSV Export Button
        csv_data = filtered_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Export Filtered Dataset as CSV",
            data=csv_data,
            file_name="AERIS_cleaned_air_quality_export.csv",
            mime="text/csv",
            help="Download the currently filtered dataset."
        )

    # =========================================================================
    # TAB 2: DATA QUALITY & AUDIT SUMMARY
    # =========================================================================
    with tab_audit:
        st.subheader("🛡️ Data Cleaning & Quality Audit Summary")
        st.caption("Verifiable audit metrics tracking deduplication, negative value removal, and completeness")

        if summary:
            audit_dict = summary.to_dict()
            q1, q2, q3, q4 = st.columns(4)
            q1.metric("Raw Observations", f"{audit_dict['Total Raw Records']:,}")
            q2.metric("Duplicates Removed", f"{audit_dict['Duplicates Removed']:,}")
            q3.metric("Negative Values Corrected", f"{audit_dict['Negative Values Corrected']:,}")
            q4.metric("Final Cleaned Records", f"{audit_dict['Cleaned Records']:,}")

            st.markdown("---")
            st.subheader("Missing Value Audit by Pollutant Column")
            st.caption("AERIS never silently fabricates or imputes arbitrary observations")

            if summary.missing_values_by_column:
                missing_df = pd.DataFrame([
                    {
                        "Column": col,
                        "Missing Observations": count,
                        "Missing Percentage (%)": summary.missing_percentage_by_column.get(col, 0.0),
                        "Valid Available Observations": len(df) - count
                    }
                    for col, count in summary.missing_values_by_column.items()
                ]).sort_values("Missing Observations", ascending=False)

                fig_miss = px.bar(
                    missing_df,
                    x="Column",
                    y="Missing Percentage (%)",
                    text_auto=".2f",
                    title="Missingness Percentage per Parameter",
                    color="Missing Percentage (%)",
                    color_continuous_scale="Teal"
                )
                fig_miss.update_layout(template="plotly_white", height=320)
                st.plotly_chart(fig_miss, use_container_width=True)

                st.dataframe(missing_df, use_container_width=True, hide_index=True)
            else:
                st.success("No missing values detected in pollutant parameters.")
        else:
            st.info("No data quality audit summary available for the active dataset.")

    # =========================================================================
    # TAB 3: SQLITE LOCAL PERSISTENCE
    # =========================================================================
    with tab_database:
        st.subheader("💾 SQLite Local Database Storage")
        st.caption("Store and retrieve cleaned environmental records in local SQLite database")

        table_name = st.text_input("SQLite Table Name:", value="cleaned_air_quality")

        s_col1, s_col2 = st.columns(2)
        with s_col1:
            if st.button("💾 Save Current Dataset to SQLite", use_container_width=True):
                success = save_dataset_to_db(df, table_name=table_name)
                if success:
                    st.success(f"Successfully saved {len(df):,} records to table '{table_name}' in SQLite!")
                else:
                    st.error("Failed to save dataset to SQLite.")

        with s_col2:
            existing_tables = list_tables_in_db()
            st.write(f"Existing tables in local database: `{existing_tables if existing_tables else 'None'}`")
