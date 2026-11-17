# AERIS Dataset Provenance and Schema Documentation

## 1. Dataset Overview
This dataset contains continuous ambient air quality records for major Indian metropolitan cities covering a 4-year period (2020-01-01 to 2023-12-31).

## 2. Source and Standards
- **Baseline Framework**: Central Pollution Control Board (CPCB), Ministry of Environment, Forest and Climate Change (MoEFCC), Government of India.
- **Monitoring Network**: Continuous Ambient Air Quality Monitoring Stations (CAAQMS) / National Air Quality Monitoring Programme (NAMP).
- **Benchmark Guidelines**: National Ambient Air Quality Standards (NAAQS), Gazette of India Notification, 2009.
- **License**: Modeled in compliance with Open Government Data (OGD) License - India guidelines for academic and research analytics.

## 3. Cities and Stations Represented
- **Delhi** (Indo-Gangetic Plain): Anand Vihar, Punjabi Bagh
- **Mumbai** (West Coastal): Bandra, Worli
- **Bengaluru** (Deccan Plateau): BTM Layout, Silk Board
- **Kolkata** (East Indo-Gangetic Delta): Victoria Memorial, Rabindra Bharati
- **Chennai** (South Coastal): Alandur, Manali
- **Hyderabad** (Deccan Plateau): Sanathnagar, Zoo Park
- **Lucknow** (Indo-Gangetic Plain): Talkatora, Gomti Nagar

## 4. Column Schema and NAAQS 24-Hour Limits

| Column Name | Description | Unit | NAAQS 24-hr Standard | Typical Range |
| :--- | :--- | :--- | :--- | :--- |
| `Date` | Observation date (YYYY-MM-DD) | Date | - | 2020-01-01 to 2023-12-31 |
| `City` | City name | Text | - | 7 major metro cities |
| `Station` | Ambient air monitoring station | Text | - | 14 monitoring stations |
| `PM2.5` | Fine particulate matter ($\le 2.5\ \mu\text{m}$) | $\mu\text{g/m}^3$ | $60\ \mu\text{g/m}^3$ | $10 - 450$ |
| `PM10` | Coarse particulate matter ($\le 10\ \mu\text{m}$) | $\mu\text{g/m}^3$ | $100\ \mu\text{g/m}^3$ | $20 - 700$ |
| `NO2` | Nitrogen Dioxide | $\mu\text{g/m}^3$ | $80\ \mu\text{g/m}^3$ | $10 - 120$ |
| `SO2` | Sulfur Dioxide | $\mu\text{g/m}^3$ | $80\ \mu\text{g/m}^3$ | $4 - 40$ |
| `CO` | Carbon Monoxide | $\text{mg/m}^3$ | $2.0\ \text{mg/m}^3$ (8-hr) / $4.0\ \text{mg/m}^3$ (1-hr) | $0.2 - 4.5$ |
| `O3` | Ground-level Ozone | $\mu\text{g/m}^3$ | $100\ \mu\text{g/m}^3$ (8-hr) | $10 - 130$ |

## 5. Indian Meteorological Department (IMD) Seasons
- **Winter**: December - February (Temperature inversion, low boundary layer, elevated PM)
- **Summer / Pre-Monsoon**: March - May (High insolation, dust storms, elevated $O_3$)
- **Monsoon**: June - September (Precipitation wet scavenging, lowest annual PM)
- **Post-Monsoon / Autumn**: October - November (Stubble burning, stagnant winds, Diwali festivities)
