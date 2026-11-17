"""AERIS Environmental Risk and Analytical Insights Module
Module 3: Hotspot Identification, Statistical Anomaly Detection,
Cumulative Exposure Indicator (CEI), and Dynamic Environmental Insights.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd
from scipy import stats
import plotly.express as px
import plotly.graph_objects as go
from src.preprocessing import NAAQS_STANDARDS


# Default toxicological and health hazard weighting based on epidemiological literature
# (Fine particulate matter PM2.5 carries highest pulmonary penetration risk)
DEFAULT_POLLUTANT_WEIGHTS: Dict[str, float] = {
    "PM2.5": 0.40,
    "PM10": 0.25,
    "NO2": 0.15,
    "SO2": 0.10,
    "CO": 0.05,
    "O3": 0.05,
}


@dataclass
class ExposureIndicatorMetadata:
    """Documentation and parameter definitions for the Cumulative Exposure Indicator (CEI)."""
    formula: str = (
        "CEI = [ Sum_i ( w_i * ( Mean_Concentration_i / NAAQS_Benchmark_i ) ) ] * 100 * ( N_obs / N_total )^gamma"
    )
    rationale: str = (
        "Normalizes multi-pollutant concentrations against official Indian National Ambient Air Quality "
        "Standards (NAAQS 24-hr benchmarks) and computes a weighted cumulative index, weighted by particulate "
        "and gaseous health hazard coefficients. It applies an observational completeness factor to account for "
        "station temporal coverage."
    )
    distinction_from_aqi: str = (
        "CRITICAL DISTINCTION: Official CPCB AQI is a daily public advisory metric calculated using a "
        "piecewise-linear sub-index method where the overall AQI is solely determined by the single worst pollutant "
        "(max sub-index). In contrast, AERIS CEI is a research-grade aggregate multi-pollutant exposure metric "
        "designed for long-term historical comparative risk analysis across cities and monitoring stations."
    )
    medical_disclaimer: str = (
        "DISCLAIMER: The Cumulative Exposure Indicator is an environmental engineering index designed for "
        "comparative atmospheric risk intelligence. It is NOT an official clinical diagnostic score and does not "
        "infer direct individual medical pathology."
    )


def calculate_cumulative_exposure_indicator(
    df: pd.DataFrame,
    group_by: str = "City",
    completeness_gamma: float = 0.5
) -> Tuple[pd.DataFrame, ExposureIndicatorMetadata]:
    """Calculates the transparent multi-pollutant Cumulative Exposure Indicator (CEI).
    
    Formula:
        CEI = [ Sum_i ( w_i * ( C_i / NAAQS_i ) ) ] * 100 * ( N_obs / N_total )^gamma
    """
    metadata = ExposureIndicatorMetadata()

    if df.empty or group_by not in df.columns:
        return pd.DataFrame(), metadata

    # Determine present pollutants
    available_pollutants = [p for p in DEFAULT_POLLUTANT_WEIGHTS.keys() if p in df.columns]
    if not available_pollutants:
        return pd.DataFrame(), metadata

    # Dynamically re-normalize weights to sum to 1.0 for present pollutants
    raw_weights = {p: DEFAULT_POLLUTANT_WEIGHTS[p] for p in available_pollutants}
    total_raw_weight = sum(raw_weights.values())
    normalized_weights = {p: w / total_raw_weight for p, w in raw_weights.items()}

    results = []
    # Maximum possible observation count across groups for relative completeness
    max_group_obs = df.groupby(group_by)["Date"].count().max() if "Date" in df.columns else len(df)

    for grp_val, grp_df in df.groupby(group_by):
        n_obs = len(grp_df)
        completeness_ratio = (n_obs / max_group_obs) if max_group_obs > 0 else 1.0
        completeness_factor = completeness_ratio ** completeness_gamma

        weighted_exposure_sum = 0.0
        pollutant_details = {}

        for pol in available_pollutants:
            pol_mean = grp_df[pol].dropna().mean()
            naaqs_limit = NAAQS_STANDARDS.get(pol, 100.0)
            if not np.isnan(pol_mean) and naaqs_limit > 0:
                pol_ratio = pol_mean / naaqs_limit
                weighted_exposure_sum += normalized_weights[pol] * pol_ratio
                pollutant_details[f"{pol}_Mean"] = round(pol_mean, 2)
                pollutant_details[f"{pol}_Exceedance_Ratio"] = round(pol_ratio, 2)
            else:
                pollutant_details[f"{pol}_Mean"] = np.nan
                pollutant_details[f"{pol}_Exceedance_Ratio"] = np.nan

        # Unadjusted and Completeness-Adjusted CEI (100 represents exact NAAQS aggregate compliance)
        raw_cei = round(weighted_exposure_sum * 100.0, 1)
        adjusted_cei = round(raw_cei * completeness_factor, 1)

        # Categorize Exposure Level
        if adjusted_cei <= 50:
            category = "Low Exposure"
            color_code = "#10B981"  # Emerald
        elif adjusted_cei <= 100:
            category = "Standard Compliant"
            color_code = "#0D9488"  # Teal
        elif adjusted_cei <= 150:
            category = "Moderate Risk"
            color_code = "#F59E0B"  # Amber
        elif adjusted_cei <= 250:
            category = "High Risk"
            color_code = "#F97316"  # Orange
        else:
            category = "Severe Risk"
            color_code = "#EF4444"  # Red

        results.append({
            group_by: grp_val,
            "Observations": n_obs,
            "Data Completeness (%)": round(completeness_ratio * 100, 1),
            "Raw Cumulative Exposure": raw_cei,
            "AERIS CEI Score": adjusted_cei,
            "Risk Tier": category,
            "Color Code": color_code,
            **pollutant_details
        })

    res_df = pd.DataFrame(results).sort_values("AERIS CEI Score", ascending=False).reset_index(drop=True)
    res_df["Exposure Rank"] = range(1, len(res_df) + 1)
    return res_df, metadata


def identify_pollution_hotspots(
    df: pd.DataFrame,
    primary_pollutant: str = "PM2.5",
    group_by: str = "City"
) -> pd.DataFrame:
    """Identifies and ranks pollution hotspots based on chronic concentration and exceedance frequency."""
    if df.empty or primary_pollutant not in df.columns or group_by not in df.columns:
        return pd.DataFrame()

    naaqs_limit = NAAQS_STANDARDS.get(primary_pollutant, 60.0)

    hotspot_records = []
    for grp_val, grp_df in df.groupby(group_by):
        s = grp_df[primary_pollutant].dropna()
        if len(s) == 0:
            continue

        mean_val = s.mean()
        median_val = s.median()
        p90_val = s.quantile(0.90)
        max_val = s.max()
        exceed_days = (s > naaqs_limit).sum()
        exceed_pct = (exceed_days / len(s)) * 100.0

        # Composite Hotspot Score (0 - 100 Scale):
        # 50% weight to concentration ratio relative to standard + 50% weight to exceedance percentage
        conc_score = min(100.0, (mean_val / (naaqs_limit * 2.5)) * 100.0)
        composite_score = round(0.50 * conc_score + 0.50 * exceed_pct, 1)

        if composite_score >= 70:
            status = "Critical Hotspot"
        elif composite_score >= 45:
            status = "Moderate Hotspot"
        else:
            status = "Low Risk Area"

        hotspot_records.append({
            group_by: grp_val,
            "Total Monitored Days": int(len(s)),
            f"Mean {primary_pollutant}": round(mean_val, 1),
            f"Median {primary_pollutant}": round(median_val, 1),
            f"90th Percentile": round(p90_val, 1),
            f"Max {primary_pollutant}": round(max_val, 1),
            "Exceedance Days": int(exceed_days),
            "Exceedance Rate (%)": round(exceed_pct, 1),
            "Hotspot Score": composite_score,
            "Hotspot Status": status,
        })

    res = pd.DataFrame(hotspot_records).sort_values("Hotspot Score", ascending=False).reset_index(drop=True)
    res["Rank"] = range(1, len(res) + 1)
    return res


def detect_unusual_observations(
    df: pd.DataFrame,
    pollutant: str = "PM2.5",
    method: str = "iqr",
    iqr_multiplier: float = 1.5,
    z_threshold: float = 3.0
) -> pd.DataFrame:
    """Detects statistically unusual atmospheric pollution spikes (anomalies).
    
    Supports:
    1. IQR Method: Values > Q3 + (multiplier * IQR)
    2. Modified Z-Score: Robust MAD-based Z-score > z_threshold
    """
    if pollutant not in df.columns or df.empty:
        return pd.DataFrame()

    valid_df = df.dropna(subset=[pollutant]).copy()
    if len(valid_df) < 5:
        return pd.DataFrame()

    anomalies = []

    # Detect anomalies independently per city to account for local baseline variations
    for city_val, city_df in valid_df.groupby("City"):
        series = city_df[pollutant]
        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)
        iqr = q3 - q1
        median_val = series.median()
        mad = stats.median_abs_deviation(series, nan_policy="omit")

        if method == "iqr":
            cutoff = q3 + (iqr_multiplier * iqr)
            anomaly_mask = series > cutoff
        else:  # modified_z
            if mad == 0:
                cutoff = median_val + z_threshold * (series.std() if series.std() > 0 else 1.0)
                anomaly_mask = series > cutoff
            else:
                mod_z = 0.6745 * (series - median_val) / mad
                anomaly_mask = mod_z > z_threshold
                cutoff = median_val + (z_threshold * mad / 0.6745)

        detected = city_df[anomaly_mask].copy()
        if not detected.empty:
            detected["Threshold"] = round(cutoff, 1)
            detected["City Median"] = round(median_val, 1)
            detected["Anomaly Magnitude (x Baseline)"] = round(detected[pollutant] / (median_val if median_val > 0 else 1.0), 2)
            detected["Pollutant"] = pollutant
            anomalies.append(detected)

    if not anomalies:
        return pd.DataFrame()

    result = pd.concat(anomalies, ignore_index=True)
    display_cols = [
        "Date", "City", "Station", "Pollutant", pollutant, "City Median", "Threshold",
        "Anomaly Magnitude (x Baseline)", "Season"
    ]
    present_display = [c for c in display_cols if c in result.columns]
    return result[present_display].sort_values(pollutant, ascending=False).reset_index(drop=True)


def calculate_frequency_analysis(
    df: pd.DataFrame,
    pollutant: str = "PM2.5"
) -> pd.DataFrame:
    """Computes distribution frequency of observations across CPCB/NAAQS guideline bands."""
    if pollutant not in df.columns or df.empty:
        return pd.DataFrame()

    standard = NAAQS_STANDARDS.get(pollutant, 60.0)
    clean_s = df[pollutant].dropna()
    total_obs = len(clean_s)
    if total_obs == 0:
        return pd.DataFrame()

    # Define standardized health risk bins relative to NAAQS 24-hr Standard
    bins = [
        0.0,
        standard * 0.5,   # Good (< 50% NAAQS)
        standard * 1.0,   # Satisfactory (50-100% NAAQS)
        standard * 1.5,   # Moderate Exceedance (100-150% NAAQS)
        standard * 2.5,   # High Exceedance (150-250% NAAQS)
        np.inf            # Severe Exceedance (> 250% NAAQS)
    ]
    labels = [
        f"Good (0 - {standard*0.5:.0f})",
        f"Satisfactory ({standard*0.5:.0f} - {standard:.0f})",
        f"Moderate Exceedance ({standard:.0f} - {standard*1.5:.0f})",
        f"High Exceedance ({standard*1.5:.0f} - {standard*2.5:.0f})",
        f"Severe Exceedance (> {standard*2.5:.0f})"
    ]

    freq_series = pd.cut(clean_s, bins=bins, labels=labels, right=True).value_counts().reindex(labels, fill_value=0)
    freq_df = pd.DataFrame({
        "Air Quality Tier": labels,
        "Day Count": freq_series.values,
        "Percentage of Observations (%)": [round((c / total_obs) * 100, 2) for c in freq_series.values]
    })
    return freq_df


def generate_data_driven_insights(
    df: pd.DataFrame,
    primary_pollutant: str = "PM2.5"
) -> List[str]:
    """Generates rigorous, evidence-based analytical insights calculated dynamically from real dataset results."""
    insights = []
    if df.empty or primary_pollutant not in df.columns:
        return ["Insufficient data available to generate automated analytical insights."]

    unit = "mg/m³" if primary_pollutant == "CO" else "µg/m³"
    naaqs_limit = NAAQS_STANDARDS.get(primary_pollutant, 60.0)

    # 1. City rankings & hotspot analysis
    city_means = df.groupby("City")[primary_pollutant].mean().sort_values(ascending=False)
    if not city_means.empty:
        worst_city = city_means.index[0]
        worst_mean = city_means.iloc[0]
        best_city = city_means.index[-1]
        best_mean = city_means.iloc[-1]
        fold_diff = round(worst_mean / best_mean, 1) if best_mean > 0 else "N/A"

        insights.append(
            f"**Geographical Disparity:** {worst_city} recorded the highest historical average {primary_pollutant} "
            f"concentration ({worst_mean:.1f} {unit}), which is {fold_diff}x higher than {best_city} "
            f"({best_mean:.1f} {unit})."
        )

    # 2. NAAQS standard exceedance rate
    valid_primary = df[primary_pollutant].dropna()
    if len(valid_primary) > 0:
        exceed_pct = (valid_primary > naaqs_limit).mean() * 100.0
        insights.append(
            f"**Regulatory Exceedance:** Overall, {exceed_pct:.1f}% of recorded daily observations exceeded "
            f"the CPCB NAAQS 24-hour benchmark limit of {naaqs_limit} {unit}."
        )

    # 3. Seasonal Dynamics (Winter vs Monsoon)
    if "Season" in df.columns:
        seasonal = df.groupby("Season")[primary_pollutant].mean()
        if "Winter" in seasonal and "Monsoon" in seasonal:
            winter_mean = seasonal["Winter"]
            monsoon_mean = seasonal["Monsoon"]
            seasonal_ratio = round(winter_mean / monsoon_mean, 1) if monsoon_mean > 0 else "N/A"
            insights.append(
                f"**Seasonal Contrast:** Winter observations averaged {winter_mean:.1f} {unit} compared to "
                f"{monsoon_mean:.1f} {unit} during the Monsoon season ({seasonal_ratio}x elevation). "
                f"This reflects the well-documented impact of thermal inversion layers, low wind velocity, "
                f"and absent precipitation scavenging."
            )

    # 4. Inter-pollutant correlation
    if "PM10" in df.columns and primary_pollutant == "PM2.5":
        subset = df[["PM2.5", "PM10"]].dropna()
        if len(subset) > 5:
            r, p = stats.pearsonr(subset["PM2.5"], subset["PM10"])
            sig_text = "statistically significant (p < 0.001)" if p < 0.001 else f"(p = {p:.3f})"
            insights.append(
                f"**Particulate Association:** A strong positive correlation (r = {r:.2f}, {sig_text}) was observed "
                f"between fine (PM2.5) and coarse (PM10) particles, corroborating shared vehicular combustion, "
                f"industrial exhaust, and secondary aerosol precursors."
            )

    # 5. Scientific & Scope Transparency Disclaimer
    insights.append(
        "**Methodological Note:** These findings represent descriptive statistical patterns and environmental risk "
        "indices derived from ambient sensor networks. They do not infer clinical causation for specific diseases."
    )

    return insights
