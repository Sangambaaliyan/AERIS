"""AERIS: Air & Environmental Risk Intelligence System
Main Application Entry Point (Streamlit Dashboard)

Semester 5 Mini Project - Team of Four
"""

import os
import streamlit as st
import pandas as pd
from src.preprocessing import load_dataset, clean_air_quality_data, DataQualitySummary
from src.database import init_database
from dashboard.overview import render_overview_page
from dashboard.geospatial_map import render_geospatial_map_page
from dashboard.city_comparison import render_city_comparison_page
from dashboard.temporal_analysis import render_temporal_analysis_page
from dashboard.risk_dashboard import render_risk_analysis_page
from dashboard.data_explorer import render_data_explorer_page


# Streamlit Application Configuration
st.set_page_config(
    page_title="AERIS - Air Quality Intelligence",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Professional Environmental CSS
CUSTOM_CSS = """
<style>
    /* Global Typography & Background */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    /* Clean Top Header */
    .aeris-header {
        background: linear-gradient(135deg, #0F4C81 0%, #0D9488 100%);
        padding: 22px 28px;
        border-radius: 10px;
        color: white;
        margin-bottom: 24px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .aeris-header h1 {
        margin: 0;
        font-size: 2.1rem;
        font-weight: 700;
        letter-spacing: -0.5px;
        color: #FFFFFF !important;
    }
    .aeris-header p {
        margin: 6px 0 0 0;
        font-size: 0.95rem;
        color: #E2E8F0 !important;
        opacity: 0.95;
    }
    
    /* KPI Card Styling */
    div[data-testid="stMetric"] {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        padding: 16px 20px;
        border-radius: 8px;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05);
    }
    
    /* Sidebar Polish */
    section[data-testid="stSidebar"] {
        background-color: #F8FAFC;
        border-right: 1px solid #E2E8F0;
    }
    
    /* Tabs Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 6px 6px 0 0;
        padding: 8px 16px;
        font-weight: 500;
    }
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


@st.cache_data(show_spinner=False)
def load_and_preprocess_data(file_source):
    """Loads raw CSV and performs data cleaning with caching."""
    raw_df = load_dataset(file_source)
    clean_df, summary = clean_air_quality_data(raw_df)
    return clean_df, summary


def main():
    # Initialize SQLite database
    init_database()

    # Default dataset path
    default_dataset_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "data", "raw", "india_city_air_quality.csv"
    )

    # =========================================================================
    # SIDEBAR: Data Source, Navigation & Project Metadata
    # =========================================================================
    with st.sidebar:
        st.markdown(
            """
            <div style="text-align: center; margin-bottom: 15px;">
                <h2 style="color: #0F4C81; margin: 0; font-weight: 800; letter-spacing: -0.5px;">🌿 AERIS</h2>
                <small style="color: #64748B; font-weight: 500;">Air & Environmental Risk Intelligence</small>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown("### 📂 Data Source")
        data_mode = st.radio(
            "Select Data Mode:",
            options=["Built-in Benchmark Dataset (CPCB)", "Upload Custom CSV File"],
            index=0,
            label_visibility="collapsed"
        )

        uploaded_file = None
        if data_mode == "Upload Custom CSV File":
            uploaded_file = st.file_uploader(
                "Upload Air Quality CSV:",
                type=["csv"],
                help="Upload a CSV with Date, City, Station, and Pollutant columns (PM2.5, PM10, etc.)"
            )

        st.markdown("---")
        st.markdown("### 🧭 Navigation")
        selected_page = st.radio(
            "Go to Page:",
            options=[
                "Overview",
                "Geospatial Map",
                "City Comparison",
                "Temporal Analysis",
                "Risk Analysis",
                "Data Explorer"
            ],
            index=0,
            label_visibility="collapsed"
        )

        st.markdown("---")

    # =========================================================================
    # DATA INGESTION & PIPELINE
    # =========================================================================
    clean_df = pd.DataFrame()
    summary = None

    try:
        if uploaded_file is not None:
            with st.spinner("Parsing and validating uploaded dataset..."):
                clean_df, summary = load_and_preprocess_data(uploaded_file)
        else:
            if os.path.exists(default_dataset_path):
                clean_df, summary = load_and_preprocess_data(default_dataset_path)
            else:
                st.sidebar.error("Built-in benchmark dataset not found.")
    except Exception as e:
        st.error(f"❌ Error during dataset loading and preprocessing: {str(e)}")
        st.info("Please verify that your CSV has valid Date and pollutant readings.")
        return

    # Update Sidebar dataset info pill
    if not clean_df.empty and summary is not None:
        with st.sidebar:
            st.markdown("### 📊 Active Dataset Info")
            st.markdown(
                f"""
                <div style="background: #E2E8F0; padding: 10px 14px; border-radius: 6px; font-size: 0.85rem; color: #1E293B;">
                    <b>Records:</b> {len(clean_df):,}<br>
                    <b>Cities:</b> {clean_df['City'].nunique()}<br>
                    <b>Date Range:</b> {summary.start_date} to {summary.end_date}
                </div>
                """,
                unsafe_allow_html=True
            )

            st.markdown("---")
            st.markdown(
                """
                <div style="font-size: 0.78rem; color: #64748B; text-align: center;">
                    <b>AERIS Platform v1.0.0</b><br>
                    Semester 5 College Mini Project<br>
                    Developed by Team of 4 Students<br>
                    <i>Technically sound & achievable</i>
                </div>
                """,
                unsafe_allow_html=True
            )

    # =========================================================================
    # TOP HEADER BANNER
    # =========================================================================
    st.markdown(
        """
        <div class="aeris-header">
            <h1>🌿 AERIS — Air & Environmental Risk Intelligence System</h1>
            <p>Historical air-quality analytics, regulatory compliance auditing, hotspot ranking, and cumulative exposure modeling for Indian urban airsheds.</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # =========================================================================
    # ROUTE TO SELECTED PAGE
    # =========================================================================
    if clean_df.empty:
        st.info("👉 Please select the built-in benchmark dataset or upload a CSV file in the sidebar to begin analysis.")
        return

    if selected_page == "Overview":
        render_overview_page(clean_df, summary)
    elif selected_page == "Geospatial Map":
        render_geospatial_map_page(clean_df)
    elif selected_page == "City Comparison":
        render_city_comparison_page(clean_df)
    elif selected_page == "Temporal Analysis":
        render_temporal_analysis_page(clean_df)
    elif selected_page == "Risk Analysis":
        render_risk_analysis_page(clean_df)
    elif selected_page == "Data Explorer":
        render_data_explorer_page(clean_df, summary)


if __name__ == "__main__":
    main()
