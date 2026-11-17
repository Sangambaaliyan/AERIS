# AERIS Environmental Risk & Air Quality Analytics Report
**Air & Environmental Risk Intelligence System (AERIS)**  
*Academic Mini-Project — Semester 5 Computer Science & Data Analytics*

---

## 1. Executive Summary
This report presents an empirical analysis of historical ambient air quality observations across seven major Indian metropolitan airsheds (Delhi, Mumbai, Bengaluru, Kolkata, Chennai, Hyderabad, and Lucknow) over the four-year monitoring period (2020–2023).

Using validated data from Continuous Ambient Air Quality Monitoring Stations (CAAQMS) governed by the Central Pollution Control Board (CPCB), the AERIS analytical engine evaluated particulate matter ($PM_{2.5}, PM_{10}$) and critical gaseous criteria pollutants ($NO_2, SO_2, CO, O_3$).

---

## 2. Key Analytical Findings

### 2.1 Urban Hotspot Standings
A composite **Hotspot Score (0–100)** was calculated by combining multi-year chronic concentration ratios and regulatory exceedance frequencies against National Ambient Air Quality Standards (NAAQS 24-hr benchmarks):

| Rank | Urban Airshed | Mean $PM_{2.5}$ ($\mu\text{g/m}^3$) | 90th Percentile | NAAQS Exceedance Rate (%) | Hotspot Score | Classification |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: |
| **1** | **Delhi** | 108.4 | 192.5 | 68.3% | **83.2 / 100** | **Critical Hotspot** |
| **2** | **Lucknow** | 94.6 | 170.8 | 62.1% | **76.2 / 100** | **Critical Hotspot** |
| **3** | **Kolkata** | 79.8 | 148.2 | 53.4% | **65.4 / 100** | **Moderate Hotspot** |
| **4** | **Hyderabad** | 56.9 | 94.1 | 38.6% | **48.1 / 100** | **Moderate Hotspot** |
| **5** | **Mumbai** | 52.8 | 88.7 | 34.2% | **44.9 / 100** | **Moderate Hotspot** |
| **6** | **Chennai** | 42.5 | 71.4 | 24.8% | **36.5 / 100** | **Low Risk Area** |
| **7** | **Bengaluru** | 36.4 | 60.8 | 17.5% | **31.2 / 100** | **Low Risk Area** |

*Note: NAAQS 24-hour permissible benchmark for $PM_{2.5}$ is $60.0\ \mu\text{g/m}^3$.*

---

### 2.2 Seasonal Dynamics (IMD Classification)
Atmospheric particulate concentrations demonstrated severe cyclical seasonal oscillations driven by meteorological boundary layer physics:

1. **Winter (Dec–Feb):** Severe concentration surge ($PM_{2.5}$ mean: $142.0\ \mu\text{g/m}^3$). Low ambient temperatures and nocturnal radiation induce persistent thermal inversion layers, capping vertical atmospheric dispersion.
2. **Post-Monsoon (Oct–Nov):** Elevated episodic peaks ($PM_{2.5}$ mean: $128.5\ \mu\text{g/m}^3$), exacerbated by regional agricultural residue burning and stagnant wind fields.
3. **Summer (Mar–May):** Moderate particulates ($PM_{2.5}$ mean: $62.3\ \mu\text{g/m}^3$) accompanied by elevated ground-level Ozone ($O_3$) caused by intense solar insolation and photochemical reactions.
4. **Monsoon (Jun–Sep):** Lowest annual particulate burden ($PM_{2.5}$ mean: $19.0\ \mu\text{g/m}^3$), driven by intensive precipitation scavenging (wet deposition).

---

### 2.3 Cumulative Exposure Indicator (CEI) Evaluation
The **AERIS Cumulative Exposure Indicator (CEI)** normalizes multi-pollutant exposures against regulatory benchmarks with observational completeness weighting:

$$\text{CEI} = \left[ \sum_{i \in P} w_i \times \frac{\bar{C}_i}{\text{NAAQS}_i} \right] \times 100 \times \left( \frac{N_{\text{obs}}}{N_{\text{total}}} \right)^{\gamma}$$

- **Delhi:** $\text{CEI} = 206.9$ (Severe Cumulative Exposure Tier)
- **Lucknow:** $\text{CEI} = 174.5$ (High Risk Tier)
- **Kolkata:** $\text{CEI} = 139.7$ (Moderate Risk Tier)
- **Bengaluru:** $\text{CEI} = 68.2$ (Standard Compliant Tier)

---

## 3. Methodological Transparency & Limitations
1. **Scope of Indicator:** The CEI is an atmospheric engineering index designed for comparative spatial risk intelligence. It is **not** an individual clinical diagnostic score.
2. **Data Sparsity:** Although CAAQMS provides high temporal frequency, regional rural representation is absent in municipal station networks.
3. **Future Enhancements:** Integration of satellite aerosol optical depth (AOD) and meteorological wind vector modeling.

---
*Report compiled automatically by the AERIS Environmental Risk Intelligence System.*
