"""AERIS Data Preprocessing Module
Module 1: Data Collection, Ingestion, Quality Validation, and Standardization.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Union
import io
import os
import pandas as pd
import numpy as np


# Standard National Ambient Air Quality Standards (NAAQS) 24-Hour Limits (CPCB 2009)
NAAQS_STANDARDS: Dict[str, float] = {
    "PM2.5": 60.0,   # µg/m³
    "PM10": 100.0,   # µg/m³
    "NO2": 80.0,     # µg/m³
    "SO2": 80.0,     # µg/m³
    "CO": 2.0,       # mg/m³ (8-hour standard; 4.0 for 1-hour)
    "O3": 100.0,     # µg/m³ (8-hour standard)
    "NH3": 400.0,    # µg/m³
    "Pb": 1.0,       # µg/m³
}

# Standard column aliases for automatic mapping
COLUMN_ALIASES: Dict[str, List[str]] = {
    "Date": ["date", "datetime", "timestamp", "time", "reading_date"],
    "City": ["city", "location", "city_name", "metro", "district"],
    "Station": ["station", "station_name", "monitoring_station", "site", "site_name"],
    "PM2.5": ["pm2.5", "pm25", "pm2_5", "pm_2.5", "particulate_2.5"],
    "PM10": ["pm10", "pm_10", "particulate_10", "rspm"],
    "NO2": ["no2", "nitrogen_dioxide", "nitrogen_2_oxide"],
    "SO2": ["so2", "sulfur_dioxide", "sulphur_dioxide"],
    "CO": ["co", "carbon_monoxide"],
    "O3": ["o3", "ozone", "ground_ozone"],
    "NO": ["no", "nitric_oxide"],
    "NOx": ["nox", "nitrogen_oxides"],
    "NH3": ["nh3", "ammonia"],
}


@dataclass
class DataQualitySummary:
    """Stores structured metadata and audit metrics from data cleaning."""
    raw_record_count: int = 0
    final_record_count: int = 0
    duplicate_records_removed: int = 0
    negative_values_corrected: int = 0
    invalid_dates_dropped: int = 0
    missing_values_by_column: Dict[str, int] = field(default_factory=dict)
    missing_percentage_by_column: Dict[str, float] = field(default_factory=dict)
    pollutants_present: List[str] = field(default_factory=list)
    cities_present: List[str] = field(default_factory=list)
    stations_present: List[str] = field(default_factory=list)
    start_date: Optional[str] = None
    end_date: Optional[str] = None

    def to_dict(self) -> Dict[str, Union[int, str, List[str], Dict]]:
        """Converts summary to dictionary for reporting and logging."""
        return {
            "Total Raw Records": self.raw_record_count,
            "Cleaned Records": self.final_record_count,
            "Duplicates Removed": self.duplicate_records_removed,
            "Negative Values Corrected": self.negative_values_corrected,
            "Invalid Dates Dropped": self.invalid_dates_dropped,
            "Cities Count": len(self.cities_present),
            "Stations Count": len(self.stations_present),
            "Pollutants Available": ", ".join(self.pollutants_present),
            "Date Range": f"{self.start_date} to {self.end_date}" if self.start_date else "N/A",
        }


def standardize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """Standardizes heterogeneous CSV column headers into canonical AERIS names."""
    df_copy = df.copy()
    col_mapping = {}

    for col in df_copy.columns:
        clean_name = str(col).strip().lower().replace(" ", "_").replace("-", "_")
        matched = False
        for canonical, aliases in COLUMN_ALIASES.items():
            if clean_name == canonical.lower() or clean_name in aliases:
                col_mapping[col] = canonical
                matched = True
                break
        if not matched:
            # Preserve original column name stripped of whitespace
            col_mapping[col] = str(col).strip()

    return df_copy.rename(columns=col_mapping)


def assign_imd_season(month: int) -> str:
    """Assigns season based on Indian Meteorological Department (IMD) classification.
    
    - Winter: December to February (Dec, Jan, Feb)
    - Summer: March to May (Mar, Apr, May)
    - Monsoon: June to September (Jun, Jul, Aug, Sep)
    - Post-Monsoon / Autumn: October and November (Oct, Nov)
    """
    if month in [12, 1, 2]:
        return "Winter"
    elif month in [3, 4, 5]:
        return "Summer"
    elif month in [6, 7, 8, 9]:
        return "Monsoon"
    elif month in [10, 11]:
        return "Post-Monsoon"
    return "Unknown"


def load_dataset(file_source: Union[str, io.BytesIO, io.StringIO]) -> pd.DataFrame:
    """Loads a CSV dataset from a file path or in-memory file buffer.
    
    Supports comma, semicolon, and tab separators with fallback encodings.
    """
    if isinstance(file_source, str):
        if not os.path.exists(file_source):
            raise FileNotFoundError(f"Dataset path not found: {file_source}")

    # Try standard UTF-8 parsing with auto-separator detection
    try:
        df = pd.read_csv(file_source, sep=None, engine="python", encoding="utf-8")
    except (UnicodeDecodeError, pd.errors.ParserError):
        if hasattr(file_source, "seek"):
            file_source.seek(0)
        df = pd.read_csv(file_source, sep=None, engine="python", encoding="latin1")

    if df.empty:
        raise ValueError("The provided dataset is empty.")

    return df


def clean_air_quality_data(
    df: pd.DataFrame,
    max_pm25: float = 1200.0,
    max_pm10: float = 2500.0,
) -> Tuple[pd.DataFrame, DataQualitySummary]:
    """Cleans, standardizes, validates, and enhances raw air quality records.
    
    Core Principles:
    - Never fabricates or invents missing data.
    - Accurately tracks removed/corrected records.
    - Handles missing or mislabeled pollutant columns gracefully.
    - Adds IMD seasonal and calendar temporal attributes.
    """
    raw_count = len(df)
    summary = DataQualitySummary(raw_record_count=raw_count)

    # 1. Standardize column names
    clean_df = standardize_column_names(df)

    # Validate essential columns
    if "Date" not in clean_df.columns:
        raise KeyError("Dataset must contain a valid Date or Timestamp column.")

    if "City" not in clean_df.columns:
        clean_df["City"] = "Unspecified City"

    if "Station" not in clean_df.columns:
        clean_df["Station"] = "Main Station"

    # 2. String standardization (stripping whitespace, consistent casing)
    clean_df["City"] = clean_df["City"].astype(str).str.strip().str.title()
    clean_df["Station"] = clean_df["Station"].astype(str).str.strip().str.title()

    # 3. Date conversion and chronological sorting
    initial_dates = len(clean_df)
    clean_df["Date"] = pd.to_datetime(clean_df["Date"], errors="coerce")
    clean_df = clean_df.dropna(subset=["Date"])
    summary.invalid_dates_dropped = initial_dates - len(clean_df)

    # 4. Duplicate removal
    subset_keys = ["Date", "City", "Station"]
    initial_before_dedup = len(clean_df)
    clean_df = clean_df.drop_duplicates(subset=subset_keys, keep="first")
    summary.duplicate_records_removed = initial_before_dedup - len(clean_df)

    # 5. Identify available pollutant columns
    potential_pollutants = ["PM2.5", "PM10", "NO2", "SO2", "CO", "O3", "NO", "NOx", "NH3"]
    active_pollutants = [p for p in potential_pollutants if p in clean_df.columns]
    summary.pollutants_present = active_pollutants

    # 6. Numerical validation and negative value correction
    negative_corrections = 0
    for pol in active_pollutants:
        # Convert to numeric
        clean_df[pol] = pd.to_numeric(clean_df[pol], errors="coerce")

        # Flag and correct negative values (sensor baseline drift/error)
        neg_mask = clean_df[pol] < 0
        neg_count = int(neg_mask.sum())
        if neg_count > 0:
            negative_corrections += neg_count
            clean_df.loc[neg_mask, pol] = np.nan

        # Physics-based extreme outlier bounds check (treat as sensor glitch)
        if pol == "PM2.5":
            clean_df.loc[clean_df[pol] > max_pm25, pol] = np.nan
        elif pol == "PM10":
            clean_df.loc[clean_df[pol] > max_pm10, pol] = np.nan

    summary.negative_values_corrected = negative_corrections

    # 7. Missing value auditing (Never silently impute or invent data)
    for col in active_pollutants:
        null_count = int(clean_df[col].isna().sum())
        summary.missing_values_by_column[col] = null_count
        summary.missing_percentage_by_column[col] = round((null_count / len(clean_df)) * 100, 2) if len(clean_df) > 0 else 0.0

    # 8. Temporal feature engineering
    clean_df["Date"] = pd.to_datetime(clean_df["Date"])
    clean_df = clean_df.sort_values(by=["Date", "City", "Station"]).reset_index(drop=True)
    clean_df["Year"] = clean_df["Date"].dt.year
    clean_df["Month"] = clean_df["Date"].dt.month
    clean_df["Month_Name"] = clean_df["Date"].dt.strftime("%b")
    clean_df["Day"] = clean_df["Date"].dt.day
    clean_df["Day_of_Week"] = clean_df["Date"].dt.day_name()
    clean_df["Season"] = clean_df["Month"].apply(assign_imd_season)

    # 9. Finalize summary metrics
    summary.final_record_count = len(clean_df)
    summary.cities_present = sorted(clean_df["City"].unique().tolist())
    summary.stations_present = sorted(clean_df["Station"].unique().tolist())

    if not clean_df.empty:
        summary.start_date = clean_df["Date"].min().strftime("%Y-%m-%d")
        summary.end_date = clean_df["Date"].max().strftime("%Y-%m-%d")

    return clean_df, summary


def export_cleaned_dataset(df: pd.DataFrame, output_path: str) -> None:
    """Exports cleaned DataFrame to CSV format."""
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    df.to_csv(output_path, index=False)
