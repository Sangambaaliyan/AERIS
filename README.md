# 🌿 AERIS: Air & Environmental Risk Intelligence System
> **An Environmental Data Analytics Platform for Urban Air Quality, Hotspot Ranking, and Cumulative Atmospheric Risk Assessment**  
> *Developed as a Semester 5 College Mini Project by a Team of Five Students.*

---

## 📌 1. Project Introduction
**AERIS (Air & Environmental Risk Intelligence System)** is an environmental data analytics platform engineered to transform raw, heterogeneous air-quality datasets from major Indian metropolitan airsheds into actionable atmospheric intelligence.

By combining robust data cleaning pipelines, parametric/non-parametric exploratory statistical analysis, statistical anomaly detection, and interactive geospatial/temporal dashboards, AERIS enables environmental researchers, policy analysts, and citizens to analyze historical pollution trends, benchmark urban airsheds against official National Ambient Air Quality Standards (NAAQS), and assess cumulative atmospheric exposure.

---

## 🎯 2. Problem Statement & Objectives

### Problem Statement
Rapid urbanization and industrialization in India have created severe atmospheric challenges. However, raw air-quality monitoring data from monitoring stations is often fragmented, noisy, contains negative sensor drift values, and lacks accessible tools for multi-pollutant cumulative exposure evaluation. Existing tools either provide raw tabular dumps or simple real-time AQI numbers that obscure long-term chronic exposure trends.

### Key Objectives
1. **Automated Preprocessing & Data Validation:** Standardize heterogeneous column headers, handle missing values transparently without fabrication, remove duplicate records, and correct negative sensor anomalies.
2. **Exploratory & Statistical Analysis:** Quantify central tendencies, dispersion, skewness, and inter-pollutant correlations across Indian cities and Indian Meteorological Department (IMD) seasons.
3. **Environmental Risk & Hotspot Identification:** Compute a multi-criteria Hotspot Score (0–100) to isolate critical urban pollution centers.
4. **Transparent Cumulative Exposure Indicator (CEI):** Formulate a mathematically documented, multi-pollutant exposure metric normalized against CPCB NAAQS benchmarks.
5. **Interactive Analytical Dashboard:** Deliver a modern, professional, 5-page Streamlit application with interactive Plotly visualizations.

---

## 🛠️ 3. Technology Stack

AERIS is built using a clean, modern Python data analytics stack:

- **Core Language:** Python 3 (Tested on 3.10+)
- **Data Ingestion & Processing:** Pandas, NumPy
- **Statistical Analytics & Distribution Modeling:** SciPy (`stats.skew`, `stats.kurtosis`, `stats.pearsonr`, `stats.median_abs_deviation`)
- **Interactive Visualizations:** Plotly (Plotly Express & Graph Objects)
- **Dashboard Interface:** Streamlit (Multi-page modular layout, responsive CSS)
- **Local Persistence:** SQLite (Built-in standard library `sqlite3`)
- **Exploratory Notebooks:** Matplotlib, Seaborn, Jupyter

---

## 📂 4. Project Architecture

The AERIS repository adheres to clean software engineering practices by strictly decoupling core analytical algorithms from the presentation dashboard:

```
AERIS/
│
├── app.py                      # Main Streamlit application entry point & router
├── requirements.txt            # Project dependencies
├── README.md                   # Comprehensive documentation & setup guide
├── .gitignore                  # Git ignore rules
│
├── data/
│   ├── raw/                    # Raw air quality datasets & provenance documentation
│   │   ├── india_city_air_quality.csv
│   │   └── README.md
│   └── processed/              # Cleaned datasets and local SQLite storage
│       └── aeris_local_storage.db
│
├── src/                        # Core backend analytical modules
│   ├── __init__.py
│   ├── preprocessing.py        # Data ingestion, header standardization & quality audit
│   ├── analysis.py             # Descriptive stats, temporal aggregation & Plotly charts
│   ├── risk_analysis.py        # Hotspot scoring, CEI index & anomaly detection
│   ├── geospatial.py           # Pan-India mapping & live satellite API query engine
│   └── database.py             # SQLite persistence & audit logging
│
├── dashboard/                  # Multi-page Streamlit presentation components
│   ├── __init__.py
│   ├── overview.py             # Executive overview & regulatory standards
│   ├── geospatial_map.py       # Interactive Pan-India map & live coordinates query
│   ├── city_comparison.py      # Cross-city comparative benchmarking
│   ├── temporal_analysis.py    # Monthly, annual & IMD seasonal dynamics
│   ├── risk_dashboard.py       # Hotspots, CEI mathematical model & anomalies
│   └── data_explorer.py        # Interactive records table, audit summary & CSV export
│
├── notebooks/                  # Reproducible Jupyter data science notebook
│   └── exploratory_analysis.ipynb
│
├── reports/                    # Generated analytical intelligence reports
│   └── sample_summary_report.md
│
└── tests/                      # Automated unit and integration test suite
    └── test_aeris.py
```

---

## 📊 5. Core Analytical Modules & Mathematical Formulations

### Module 1: Preprocessing & Quality Auditing (`src/preprocessing.py`)
- Standardizes messy column variations (`pm25`, `PM2_5`, `particulate_2.5` $\to$ `PM2.5`).
- Drops unparseable dates and duplicate entries based on `[Date, City, Station]`.
- Corrects negative sensor values ($< 0$) by converting them to `NaN` with audit counting.
- Enforces strict scientific integrity: **never silently fabricates or imputes arbitrary values**.
- Classifies calendar dates into official **IMD Seasons**:
  - **Winter:** December – February
  - **Summer:** March – May
  - **Monsoon:** June – September
  - **Post-Monsoon:** October – November

### Module 2: Exploratory & Statistical Profiling (`src/analysis.py`)
- Parametric metrics: Mean, Standard Deviation, Year-over-Year Percentage Change.
- Non-parametric metrics: Median, 25th percentile ($Q_1$), 75th percentile ($Q_3$), Interquartile Range ($IQR$).
- Distribution geometry: Fisher-Pearson standardized skewness and kurtosis.
- Inter-pollutant correlation matrices with two-tailed p-values ($p < 0.05$).

### Module 3: Cumulative Exposure Indicator (CEI) & Hotspots (`src/risk_analysis.py`)

#### 1. Cumulative Exposure Indicator (CEI) Formula
$$\text{CEI} = \left[ \sum_{i \in P} w_i \times \frac{\bar{C}_i}{\text{NAAQS}_i} \right] \times 100 \times \left( \frac{N_{\text{obs}}}{N_{\text{total}}} \right)^{\gamma}$$

- $\bar{C}_i$: Monitored mean concentration of pollutant $i$.
- $\text{NAAQS}_i$: CPCB 24-hr standard benchmark ($PM_{2.5}: 60$, $PM_{10}: 100$, $NO_2: 80$, $SO_2: 80$, $CO: 2.0$, $O_3: 100$).
- $w_i$: Health hazard weightings ($PM_{2.5}: 0.40$, $PM_{10}: 0.25$, $NO_2: 0.15$, $SO_2: 0.10$, $CO: 0.05$, $O_3: 0.05$).
- $\left( \frac{N_{\text{obs}}}{N_{\text{total}}} \right)^{\gamma}$: Observational completeness factor ($\gamma = 0.5$) adjusting for monitoring continuity.

> ⚠️ **Distinction from Official AQI:**  
> Official CPCB AQI is a daily public advisory index determined by the worst single pollutant sub-index ($\max$). In contrast, AERIS CEI is a multi-pollutant cumulative metric for multi-year spatial comparative risk analytics. It is an environmental index, **not a clinical diagnostic score**.

#### 2. Composite Hotspot Score ($0 - 100$)
$$\text{Hotspot Score} = 0.50 \times \min\left(100, \frac{\bar{C}}{\text{NAAQS} \times 2.5} \times 100\right) + 0.50 \times \text{Exceedance Rate (\%)} $$

#### 3. Statistical Anomaly Detection
- **IQR Method:** Flags readings exceeding $Q_3 + (1.5 \times IQR)$.
- **Modified Z-Score:** Detects episodic surges where $Z_{\text{mod}} = 0.6745 \times \frac{|X - \text{Median}|}{\text{MAD}} > 3.0$.

---

## 🚀 6. Installation & Execution Guide

### Prerequisites
- Python 3.10, 3.11, 3.12, 3.13, or 3.14
- Git (optional)

### Step 1: Clone or Navigate to the Project Directory
```bash
cd AERIS
```

### Step 2: Create and Activate a Virtual Environment
```bash
# Windows
python -m venv .venv
.\.venv\Scripts\activate

# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
```

### Step 3: Install Required Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Run the Interactive Streamlit Dashboard
```bash
streamlit run app.py
```
The application will launch automatically at `http://localhost:8501`.

### Step 5: Run Automated Unit Tests
```bash
python -m unittest tests/test_aeris.py
```

---

## 🖥️ 7. Dashboard Walkthrough & Features

The AERIS Streamlit dashboard features five dedicated analytical pages:

1. **Overview Page (`dashboard/overview.py`):**
   - High-level KPI metric cards (Total records, monitored cities, station count, particulate delta vs NAAQS).
   - Side-by-side grouped bar charts of fine vs coarse particulates.
   - 30-day smoothed moving average temporal trajectory across airsheds.
   - CPCB NAAQS 2009 Gazette standards reference table.

2. **Geospatial Risk Map Page (`dashboard/geospatial_map.py`):**
   - Interactive Pan-India Mapbox/Scattergeo map displaying 44+ CPCB monitoring stations across all Indian zones (North, South, East, West, Central, North-East).
   - Click-to-inspect or search any city to retrieve complete atmospheric diagnostics.
   - **Live Anywhere in India Query:** Enter custom geographic coordinates ($\text{Lat: } 8^{\circ}\text{N}-37^{\circ}\text{N}, \text{Lon: } 68^{\circ}\text{E}-97^{\circ}\text{E}$) to query real live Copernicus CAMS & Open-Meteo atmospheric feeds.
   - 48-Hour Hourly Trajectory Chart (past 24h observed + next 24h forecast) and CPCB National AQI health advisory badges.

3. **City Comparison Page (`dashboard/city_comparison.py`):**
   - Multi-city selector filter with instant reactive chart updates.
   - Ranked comparative bar charts with customizable metrics (Mean, Median, Max, Std Dev).
   - Box plot dispersion comparisons highlighting median lines and extreme outliers.
   - Adjustable moving average smoothing slider (1–60 days).

3. **Temporal Analysis Page (`dashboard/temporal_analysis.py`):**
   - Date range selector and city-specific drill-down.
   - IMD seasonal breakdown (Winter, Summer, Monsoon, Post-Monsoon).
   - Multi-year monthly cyclical pattern charts (Jan–Dec).
   - Year $\times$ Month heatmap matrix.
   - Inter-pollutant correlation heatmaps with Pearson/Spearman p-value matrices.

4. **Risk Analysis Page (`dashboard/risk_dashboard.py`):**
   - Urban Pollution Hotspot leaderboard with status classification (Critical, Moderate, Low Risk).
   - Cumulative Exposure Indicator (CEI) with complete mathematical transparency.
   - Statistical anomaly detector with adjustable sensitivity (IQR multiplier or Modified Z threshold).
   - Exceedance frequency distributions across risk tiers.
   - Automated evidence-based intelligence report generator with one-click `.txt` download.

5. **Data Explorer Page (`dashboard/data_explorer.py`):**
   - Full interactive dataset viewer with multi-criteria filtering (City, Station, Season).
   - Comprehensive data quality audit summary cards.
   - Missingness distribution bar chart.
   - Filtered dataset export as CSV.
   - Local SQLite database persistence interface.

---

## 👥 8. Team Contribution Section (Semester 5 Mini-Project)

Developed by a collaborative four-member student engineering team:

| Team Member | Primary Role | Core Contributions |
| :--- | :--- | :--- |
| **Student 1** | **Project Lead & Data Pipeline Architect** | Designed system architecture; implemented Module 1 (`preprocessing.py`) and Module 4 (`database.py`); built column standardization, deduplication, negative sensor validation, and SQLite persistence. |
| **Student 2** | **Statistical Analyst & Math Modeler** | Implemented Module 2 (`analysis.py`); calculated central tendencies, dispersion, skewness, and inter-pollutant correlation matrices with two-tailed p-values; authored the Jupyter notebook (`exploratory_analysis.ipynb`). |
| **Student 3** | **Environmental Risk Intelligence Engineer** | Implemented Module 3 (`risk_analysis.py`); formulated the Cumulative Exposure Indicator (CEI), composite Hotspot Score, IQR/MAD statistical anomaly detection algorithms, and dynamic insight generator. |
| **Student 4** | **UI/UX Designer & Streamlit Frontend Engineer** | Architected the multi-page Streamlit dashboard (`dashboard/`); implemented custom CSS theme (palette: Deep Blue, Teal, Emerald Green), Plotly interactive visual styling, KPI cards, and CSV export utilities. |

---

## ⚖️ 9. Ethical Scope, Limitations & Future Enhancements

### Scientific & Ethical Transparency
- **No Direct Medical Causation:** AERIS calculates ambient environmental exposure indicators and statistical associations. In strict adherence to scientific guidelines, it does not diagnose medical pathology or assert direct clinical causation without biological exposure biomarkers.
- **No Data Fabrication:** Missing values are audited and preserved; arbitrary imputation is avoided.

### Limitations
- **Station Spatial Sparsity:** Current CAAQMS stations are predominantly municipal and urban, lacking rural hinterland coverage.
- **Meteorological Co-variates:** Does not yet incorporate real-time planetary boundary layer height (PBLH) sounding data or wind vector reanalysis.

### Future Enhancements
- Integration of ISRO/NASA satellite Aerosol Optical Depth (AOD) retrievals.
- Machine Learning-based 24-hour predictive forecast using seasonal autoregressive models (SARIMAX / Prophet).
- Expansion of station network data ingestion via automated CPCB open-data web endpoints.

---

## 📜 10. License & Citations
- **Standards:** National Ambient Air Quality Standards (NAAQS), Central Pollution Control Board (CPCB), Gazette of India (2009).
- **License:** Open Academic & Educational Use (MIT License).
