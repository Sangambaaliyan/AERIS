"""Unit and Integration Test Suite for AERIS
Tests data preprocessing, analytical calculations, risk algorithms, database storage, and edge cases.
"""

import unittest
import numpy as np
import pandas as pd
from src.preprocessing import (
    standardize_column_names,
    assign_imd_season,
    clean_air_quality_data,
    NAAQS_STANDARDS,
    DataQualitySummary,
)
from src.analysis import (
    calculate_descriptive_statistics,
    compute_correlation_matrix,
    get_temporal_trends,
)
from src.risk_analysis import (
    calculate_cumulative_exposure_indicator,
    identify_pollution_hotspots,
    detect_unusual_observations,
    calculate_frequency_analysis,
    generate_data_driven_insights,
)
from src.database import save_dataset_to_db, load_dataset_from_db
from src.geospatial import classify_cpcb_aqi, INDIAN_CITIES_GEO, fetch_live_air_quality


class TestAERISPreprocessing(unittest.TestCase):
    """Test suite for Module 1: Data Collection & Preprocessing."""

    def setUp(self):
        self.sample_raw_df = pd.DataFrame({
            "datetime": ["2023-01-01", "2023-01-02", "2023-01-02", "2023-01-03", "invalid-date"],
            "city_name": [" delhi ", "Delhi", "Delhi", "Mumbai", "Delhi"],
            "site": ["Anand Vihar", "Anand Vihar", "Anand Vihar", "Bandra", "Anand Vihar"],
            "pm25": [120.5, 95.0, 95.0, -10.0, 80.0],  # Includes duplicate and negative value
            "pm10": [220.0, 180.0, 180.0, 45.0, 150.0],
            "no2": [45.0, 40.0, 40.0, 25.0, 30.0],
        })

    def test_column_standardization(self):
        std_df = standardize_column_names(self.sample_raw_df)
        self.assertIn("Date", std_df.columns)
        self.assertIn("City", std_df.columns)
        self.assertIn("Station", std_df.columns)
        self.assertIn("PM2.5", std_df.columns)
        self.assertIn("PM10", std_df.columns)
        self.assertIn("NO2", std_df.columns)

    def test_season_assignment(self):
        self.assertEqual(assign_imd_season(1), "Winter")
        self.assertEqual(assign_imd_season(4), "Summer")
        self.assertEqual(assign_imd_season(7), "Monsoon")
        self.assertEqual(assign_imd_season(10), "Post-Monsoon")

    def test_clean_air_quality_data(self):
        clean_df, summary = clean_air_quality_data(self.sample_raw_df)
        # Should drop invalid date and duplicate
        self.assertEqual(summary.invalid_dates_dropped, 1)
        self.assertEqual(summary.duplicate_records_removed, 1)
        # Negative value (-10.0) should be converted to NaN
        self.assertEqual(summary.negative_values_corrected, 1)
        self.assertTrue(clean_df["PM2.5"].isna().any())
        # City name should be capitalized and trimmed
        self.assertIn("Delhi", clean_df["City"].values)
        self.assertNotIn(" delhi ", clean_df["City"].values)
        # Seasonal column added
        self.assertIn("Season", clean_df.columns)
        self.assertEqual(clean_df["Season"].iloc[0], "Winter")


class TestAERISAnalysis(unittest.TestCase):
    """Test suite for Module 2: Exploratory & Statistical Analysis."""

    def setUp(self):
        dates = pd.date_range("2023-01-01", periods=10, freq="D")
        self.df = pd.DataFrame({
            "Date": dates,
            "City": ["Delhi"] * 5 + ["Mumbai"] * 5,
            "Station": ["Station A"] * 10,
            "PM2.5": [100.0, 120.0, 80.0, 150.0, 110.0, 40.0, 50.0, 45.0, 60.0, 55.0],
            "PM10": [200.0, 240.0, 160.0, 300.0, 220.0, 80.0, 100.0, 90.0, 120.0, 110.0],
            "NO2": [50.0, 55.0, 45.0, 65.0, 52.0, 30.0, 35.0, 32.0, 38.0, 36.0],
            "Season": ["Winter"] * 10,
            "Year": [2023] * 10,
            "Month": [1] * 10,
            "Month_Name": ["Jan"] * 10
        })

    def test_descriptive_statistics(self):
        stats_df = calculate_descriptive_statistics(self.df, pollutants=["PM2.5"])
        self.assertEqual(len(stats_df), 1)
        self.assertAlmostEqual(stats_df["Mean"].iloc[0], 81.0, places=1)
        self.assertAlmostEqual(stats_df["Min"].iloc[0], 40.0, places=1)
        self.assertAlmostEqual(stats_df["Max"].iloc[0], 150.0, places=1)

    def test_grouped_statistics(self):
        grouped_stats = calculate_descriptive_statistics(self.df, pollutants=["PM2.5"], group_by="City")
        self.assertEqual(len(grouped_stats), 2)
        delhi_row = grouped_stats[grouped_stats["City"] == "Delhi"].iloc[0]
        self.assertAlmostEqual(delhi_row["Mean"], 112.0, places=1)

    def test_correlations(self):
        corr_df, p_vals = compute_correlation_matrix(self.df, pollutants=["PM2.5", "PM10"])
        self.assertAlmostEqual(corr_df.loc["PM2.5", "PM10"], 1.0, places=2)
        self.assertLess(p_vals.loc["PM2.5", "PM10"], 0.05)


class TestAERISRiskAnalysis(unittest.TestCase):
    """Test suite for Module 3: Environmental Risk & Insights."""

    def setUp(self):
        dates = pd.date_range("2023-01-01", periods=20, freq="D")
        # Delhi high pollution, Bengaluru low pollution
        delhi_pm = [150.0 + i for i in range(10)] + [450.0]  # One clear spike for anomaly
        bengaluru_pm = [30.0 + i for i in range(10)]
        self.df = pd.DataFrame({
            "Date": list(dates[:11]) + list(dates[:10]),
            "City": ["Delhi"] * 11 + ["Bengaluru"] * 10,
            "Station": ["Station 1"] * 21,
            "PM2.5": delhi_pm + bengaluru_pm,
            "PM10": [p * 2.0 for p in (delhi_pm + bengaluru_pm)],
            "NO2": [40.0] * 21,
            "Season": ["Winter"] * 21
        })

    def test_hotspot_ranking(self):
        hotspots = identify_pollution_hotspots(self.df, primary_pollutant="PM2.5")
        self.assertEqual(hotspots["City"].iloc[0], "Delhi")
        self.assertGreater(hotspots["Hotspot Score"].iloc[0], hotspots["Hotspot Score"].iloc[1])

    def test_cei_calculation(self):
        cei_df, meta = calculate_cumulative_exposure_indicator(self.df, group_by="City")
        self.assertEqual(cei_df["City"].iloc[0], "Delhi")
        self.assertGreater(cei_df["AERIS CEI Score"].iloc[0], cei_df["AERIS CEI Score"].iloc[1])
        self.assertIn("CEI =", meta.formula)

    def test_anomaly_detection(self):
        anomalies = detect_unusual_observations(self.df, pollutant="PM2.5", method="iqr")
        # The 450.0 spike should be detected
        self.assertTrue((anomalies["PM2.5"] == 450.0).any())

    def test_frequency_analysis(self):
        freq = calculate_frequency_analysis(self.df, pollutant="PM2.5")
        self.assertEqual(len(freq), 5)
        self.assertAlmostEqual(freq["Percentage of Observations (%)"].sum(), 100.0, places=0)

    def test_insights_generation(self):
        insights = generate_data_driven_insights(self.df, primary_pollutant="PM2.5")
        self.assertGreaterEqual(len(insights), 3)
        self.assertTrue(any("Delhi" in ins for ins in insights))


class TestAERISDatabase(unittest.TestCase):
    """Test suite for Module 4: Database."""

    def test_save_and_load_sqlite(self):
        test_df = pd.DataFrame({
            "Date": pd.to_datetime(["2023-01-01", "2023-01-02"]),
            "City": ["Delhi", "Mumbai"],
            "PM2.5": [120.0, 45.0]
        })
        test_db = "C:/Users/SangamBaliyan/.gemini/antigravity/scratch/AERIS/data/processed/test_db.sqlite"
        saved = save_dataset_to_db(test_df, table_name="test_table", db_path=test_db)
        self.assertTrue(saved)

        loaded = load_dataset_from_db(table_name="test_table", db_path=test_db)
        self.assertIsNotNone(loaded)
        self.assertEqual(len(loaded), 2)
        self.assertIn("City", loaded.columns)

        # Cleanup test db
        import os
        if os.path.exists(test_db):
            os.remove(test_db)


class TestAERISGeospatial(unittest.TestCase):
    """Test suite for Geospatial Intelligence & Pan-India Mapping."""

    def test_cpcb_aqi_classification(self):
        cat, color = classify_cpcb_aqi(25.0)
        self.assertEqual(cat, "Good")
        cat, color = classify_cpcb_aqi(55.0)
        self.assertEqual(cat, "Satisfactory")
        cat, color = classify_cpcb_aqi(85.0)
        self.assertEqual(cat, "Moderate")
        cat, color = classify_cpcb_aqi(110.0)
        self.assertEqual(cat, "Poor")
        cat, color = classify_cpcb_aqi(220.0)
        self.assertEqual(cat, "Very Poor")
        cat, color = classify_cpcb_aqi(350.0)
        self.assertEqual(cat, "Severe")

    def test_indian_cities_directory(self):
        self.assertGreaterEqual(len(INDIAN_CITIES_GEO), 30)
        delhi = next((c for c in INDIAN_CITIES_GEO if c["City"] == "Delhi"), None)
        self.assertIsNotNone(delhi)
        self.assertAlmostEqual(delhi["Lat"], 28.61, places=1)

    def test_fetch_air_quality_structure(self):
        # Test query (falls back cleanly if offline)
        res = fetch_live_air_quality(28.6139, 77.2090)
        self.assertIn("PM2.5", res)
        self.assertIn("AQI_Category", res)
        self.assertIn("Hourly_Data", res)
        self.assertGreater(len(res["Hourly_Data"]), 0)


if __name__ == "__main__":
    unittest.main()
