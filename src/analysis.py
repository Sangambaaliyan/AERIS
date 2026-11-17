"""AERIS Exploratory and Statistical Analysis Module
Module 2: Descriptive Statistics, Temporal Aggregations, Seasonal Dynamics,
Correlation Analysis, and Interactive Visualizations.
"""

from typing import Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd
from scipy import stats
import plotly.express as px
import plotly.graph_objects as go
from src.preprocessing import NAAQS_STANDARDS


# Theme color palette (Green, Blue, Neutral)
AERIS_PALETTE = {
    "primary": "#0F4C81",       # Deep Ocean Blue
    "secondary": "#0D9488",     # Teal
    "accent": "#10B981",        # Emerald Green
    "warning": "#F59E0B",       # Amber
    "danger": "#EF4444",        # Crimson Alert
    "neutral_dark": "#1E293B",  # Slate Dark
    "neutral_light": "#F8FAFC", # Slate Light
    "grid": "#E2E8F0",
}

CITY_COLOR_SEQUENCE = [
    "#0F4C81", "#0D9488", "#10B981", "#6366F1", "#EC4899", "#8B5CF6", "#F59E0B", "#14B8A6"
]


def calculate_descriptive_statistics(
    df: pd.DataFrame,
    pollutants: Optional[List[str]] = None,
    group_by: Optional[str] = None
) -> pd.DataFrame:
    """Calculates comprehensive parametric and non-parametric summary statistics."""
    if pollutants is None:
        pollutants = [p for p in NAAQS_STANDARDS.keys() if p in df.columns]

    if not pollutants:
        return pd.DataFrame()

    records = []

    def compute_stats(series: pd.Series, prefix_dict: Dict) -> Dict:
        clean_s = series.dropna()
        if len(clean_s) == 0:
            return {
                **prefix_dict,
                "Count": 0, "Mean": np.nan, "Median": np.nan, "Std Dev": np.nan,
                "Min": np.nan, "Q1 (25%)": np.nan, "Q3 (75%)": np.nan, "IQR": np.nan,
                "Max": np.nan, "Skewness": np.nan, "Kurtosis": np.nan,
                "NAAQS Standard": prefix_dict.get("NAAQS Standard", np.nan),
                "Exceedance Rate (%)": np.nan
            }

        q1 = clean_s.quantile(0.25)
        q3 = clean_s.quantile(0.75)
        iqr = q3 - q1
        std_val = clean_s.std() if len(clean_s) > 1 else 0.0
        skew_val = stats.skew(clean_s, nan_policy="omit") if len(clean_s) > 2 else 0.0
        kurt_val = stats.kurtosis(clean_s, nan_policy="omit") if len(clean_s) > 3 else 0.0

        pol_name = prefix_dict.get("Pollutant", "")
        naaqs_limit = NAAQS_STANDARDS.get(pol_name, np.nan)
        exceed_pct = (clean_s > naaqs_limit).mean() * 100.0 if not np.isnan(naaqs_limit) else np.nan

        return {
            **prefix_dict,
            "Count": int(len(clean_s)),
            "Mean": round(clean_s.mean(), 2),
            "Median": round(clean_s.median(), 2),
            "Std Dev": round(std_val, 2),
            "Min": round(clean_s.min(), 2),
            "Q1 (25%)": round(q1, 2),
            "Q3 (75%)": round(q3, 2),
            "IQR": round(iqr, 2),
            "Max": round(clean_s.max(), 2),
            "Skewness": round(float(skew_val), 2),
            "Kurtosis": round(float(kurt_val), 2),
            "NAAQS Standard": naaqs_limit,
            "Exceedance Rate (%)": round(exceed_pct, 1) if not np.isnan(exceed_pct) else np.nan,
        }

    if group_by and group_by in df.columns:
        for group_val, grp_df in df.groupby(group_by):
            for pol in pollutants:
                if pol in grp_df.columns:
                    pref = {group_by: group_val, "Pollutant": pol, "NAAQS Standard": NAAQS_STANDARDS.get(pol, np.nan)}
                    records.append(compute_stats(grp_df[pol], pref))
    else:
        for pol in pollutants:
            if pol in df.columns:
                pref = {"Pollutant": pol, "NAAQS Standard": NAAQS_STANDARDS.get(pol, np.nan)}
                records.append(compute_stats(df[pol], pref))

    return pd.DataFrame(records)


def compute_correlation_matrix(
    df: pd.DataFrame,
    pollutants: Optional[List[str]] = None,
    method: str = "pearson"
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Computes correlation coefficients and corresponding two-tailed p-values."""
    if pollutants is None:
        pollutants = [p for p in NAAQS_STANDARDS.keys() if p in df.columns]

    valid_pollutants = [p for p in pollutants if p in df.columns and df[p].notna().sum() > 2]
    if len(valid_pollutants) < 2:
        return pd.DataFrame(), pd.DataFrame()

    corr_df = df[valid_pollutants].corr(method=method)
    p_values = pd.DataFrame(index=valid_pollutants, columns=valid_pollutants, dtype=float)

    for col1 in valid_pollutants:
        for col2 in valid_pollutants:
            if col1 == col2:
                p_values.loc[col1, col2] = 0.0
            else:
                subset = df[[col1, col2]].dropna()
                if len(subset) > 2:
                    if method == "spearman":
                        _, p_val = stats.spearmanr(subset[col1], subset[col2])
                    else:
                        _, p_val = stats.pearsonr(subset[col1], subset[col2])
                    p_values.loc[col1, col2] = p_val
                else:
                    p_values.loc[col1, col2] = np.nan

    return corr_df, p_values


def get_temporal_trends(
    df: pd.DataFrame,
    pollutant: str,
    freq: str = "ME",
    cities: Optional[List[str]] = None
) -> pd.DataFrame:
    """Aggregates time-series data at Month, Year, or Season level."""
    if pollutant not in df.columns or "Date" not in df.columns:
        return pd.DataFrame()

    filtered = df.copy()
    if cities:
        filtered = filtered[filtered["City"].isin(cities)]

    filtered = filtered.dropna(subset=[pollutant, "Date"])
    if filtered.empty:
        return pd.DataFrame()

    if freq == "Season":
        res = filtered.groupby(["Year", "Season", "City"])[pollutant].agg(
            Mean="mean", Median="median", Std="std", Count="count"
        ).reset_index()
    elif freq == "Year":
        res = filtered.groupby(["Year", "City"])[pollutant].agg(
            Mean="mean", Median="median", Std="std", Count="count"
        ).reset_index()
    else:  # Monthly
        filtered["Period"] = filtered["Date"].dt.to_period("M").dt.to_timestamp()
        res = filtered.groupby(["Period", "City"])[pollutant].agg(
            Mean="mean", Median="median", Std="std", Count="count"
        ).reset_index()

    return res


# ==============================================================================
# PLOTLY INTERACTIVE VISUALIZATIONS
# ==============================================================================

def plot_temporal_trend(
    df: pd.DataFrame,
    pollutant: str,
    cities: Optional[List[str]] = None,
    rolling_window: int = 7,
    show_naaqs: bool = True
) -> go.Figure:
    """Generates an interactive multi-city time series chart with rolling trendlines."""
    fig = go.Figure()

    if pollutant not in df.columns or df.empty:
        fig.add_annotation(text="No data available for selected pollutant", showarrow=False)
        return fig

    target_cities = cities if cities else sorted(df["City"].dropna().unique().tolist())

    for idx, city in enumerate(target_cities):
        city_data = df[df["City"] == city].sort_values("Date")
        if city_data.empty:
            continue

        color = CITY_COLOR_SEQUENCE[idx % len(CITY_COLOR_SEQUENCE)]

        # Raw Daily Readings (Subtle / Semi-transparent)
        fig.add_trace(go.Scatter(
            x=city_data["Date"],
            y=city_data[pollutant],
            mode="lines",
            name=f"{city} (Daily)",
            line=dict(width=1, color=color),
            opacity=0.3,
            hoverinfo="skip"
        ))

        # Smoothed Rolling Average
        if rolling_window > 1:
            city_data["Smoothed"] = city_data[pollutant].rolling(rolling_window, min_periods=1).mean()
            fig.add_trace(go.Scatter(
                x=city_data["Date"],
                y=city_data["Smoothed"],
                mode="lines",
                name=f"{city} ({rolling_window}-Day MA)",
                line=dict(width=2.5, color=color),
                hovertemplate=f"<b>{city}</b><br>Date: %{{x|%b %d, %Y}}<br>{pollutant}: %{{y:.1f}} µg/m³<extra></extra>"
            ))

    # Add NAAQS Reference Line
    if show_naaqs and pollutant in NAAQS_STANDARDS:
        limit = NAAQS_STANDARDS[pollutant]
        unit = "mg/m³" if pollutant == "CO" else "µg/m³"
        fig.add_hline(
            y=limit,
            line_dash="dash",
            line_color=AERIS_PALETTE["danger"],
            line_width=2,
            annotation_text=f"NAAQS 24-hr Safe Limit ({limit} {unit})",
            annotation_position="top right",
            annotation_font=dict(color=AERIS_PALETTE["danger"], size=11)
        )

    fig.update_layout(
        title=f"Historical {pollutant} Concentration Trends",
        xaxis_title="Date",
        yaxis_title=f"{pollutant} Concentration ({'mg/m³' if pollutant == 'CO' else 'µg/m³'})",
        template="plotly_white",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=40, r=40, t=80, b=40)
    )
    return fig


def plot_city_comparison_bar(
    df: pd.DataFrame,
    pollutant: str,
    metric: str = "Mean"
) -> go.Figure:
    """Generates an interactive comparative bar chart of cities with NAAQS benchmark."""
    fig = go.Figure()
    if pollutant not in df.columns or df.empty:
        return fig

    grouped = df.groupby("City")[pollutant].agg(["mean", "median", "max", "std"]).reset_index()
    grouped = grouped.sort_values(metric.lower(), ascending=True)

    unit = "mg/m³" if pollutant == "CO" else "µg/m³"
    y_vals = grouped[metric.lower()]

    # Color bars based on NAAQS threshold exceedance
    limit = NAAQS_STANDARDS.get(pollutant, np.nan)
    colors = [
        AERIS_PALETTE["danger"] if not np.isnan(limit) and val > limit else AERIS_PALETTE["primary"]
        for val in y_vals
    ]

    fig.add_trace(go.Bar(
        x=y_vals,
        y=grouped["City"],
        orientation="h",
        marker=dict(color=colors, line=dict(color="#334155", width=1)),
        text=[f"{v:.1f} {unit}" for v in y_vals],
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>" + f"{metric} {pollutant}: " + "%{x:.1f} " + unit + "<extra></extra>"
    ))

    if not np.isnan(limit):
        fig.add_vline(
            x=limit,
            line_dash="dot",
            line_color=AERIS_PALETTE["warning"],
            line_width=2,
            annotation_text=f"NAAQS Limit ({limit})",
            annotation_position="top",
            annotation_font=dict(color=AERIS_PALETTE["warning"], size=11)
        )

    fig.update_layout(
        title=f"City Comparison: {metric} {pollutant} Levels",
        xaxis_title=f"{metric} {pollutant} ({unit})",
        yaxis_title="City",
        template="plotly_white",
        margin=dict(l=40, r=40, t=60, b=40)
    )
    return fig


def plot_correlation_heatmap(corr_df: pd.DataFrame) -> go.Figure:
    """Renders an interactive correlation matrix heatmap with coefficients."""
    if corr_df.empty:
        fig = go.Figure()
        fig.add_annotation(text="Insufficient pollutant data for correlation matrix", showarrow=False)
        return fig

    fig = px.imshow(
        corr_df,
        text_auto=".2f",
        aspect="auto",
        color_continuous_scale="RdBu_r",
        zmin=-1.0,
        zmax=1.0,
        labels=dict(color="Correlation (r)")
    )
    fig.update_layout(
        title="Inter-Pollutant Correlation Matrix",
        template="plotly_white",
        margin=dict(l=40, r=40, t=60, b=40)
    )
    return fig


def plot_distribution_boxplot(
    df: pd.DataFrame,
    pollutant: str,
    group_by: str = "City"
) -> go.Figure:
    """Generates an interactive box plot displaying distribution, quartiles, and outliers."""
    fig = go.Figure()
    if pollutant not in df.columns or df.empty:
        return fig

    groups = sorted(df[group_by].dropna().unique())
    unit = "mg/m³" if pollutant == "CO" else "µg/m³"

    for idx, grp in enumerate(groups):
        subset = df[df[group_by] == grp][pollutant].dropna()
        color = CITY_COLOR_SEQUENCE[idx % len(CITY_COLOR_SEQUENCE)]
        fig.add_trace(go.Box(
            y=subset,
            name=str(grp),
            marker=dict(color=color),
            boxmean=True  # Display dashed mean line
        ))

    limit = NAAQS_STANDARDS.get(pollutant, np.nan)
    if not np.isnan(limit):
        fig.add_hline(
            y=limit,
            line_dash="dash",
            line_color=AERIS_PALETTE["danger"],
            annotation_text=f"NAAQS Standard ({limit} {unit})",
            annotation_position="bottom right"
        )

    fig.update_layout(
        title=f"{pollutant} Distribution Across {group_by} (Box Plot with Mean & Outliers)",
        yaxis_title=f"{pollutant} ({unit})",
        xaxis_title=group_by,
        template="plotly_white",
        margin=dict(l=40, r=40, t=60, b=40)
    )
    return fig


def plot_monthly_seasonal_patterns(
    df: pd.DataFrame,
    pollutant: str,
    city: Optional[str] = None
) -> go.Figure:
    """Visualizes monthly cyclical pollution dynamics grouped by year or season."""
    if pollutant not in df.columns or df.empty:
        return go.Figure()

    filtered = df[df["City"] == city] if city else df
    month_order = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

    monthly = filtered.groupby(["Year", "Month_Name", "Month"])[pollutant].mean().reset_index()
    monthly = monthly.sort_values("Month")

    fig = px.line(
        monthly,
        x="Month_Name",
        y=pollutant,
        color="Year",
        markers=True,
        category_orders={"Month_Name": month_order},
        labels={"Month_Name": "Month", pollutant: f"Mean {pollutant} (µg/m³)"},
        title=f"Monthly Cyclical {pollutant} Patterns ({city if city else 'All Cities'})"
    )

    limit = NAAQS_STANDARDS.get(pollutant, np.nan)
    if not np.isnan(limit):
        fig.add_hline(
            y=limit,
            line_dash="dot",
            line_color=AERIS_PALETTE["danger"],
            annotation_text=f"NAAQS Limit ({limit})",
            annotation_position="top right"
        )

    fig.update_layout(template="plotly_white", margin=dict(l=40, r=40, t=60, b=40))
    return fig
