# AirPure Innovations – AQI Analytics & Market Research

## 📌 Project Overview

AirPure Innovations is a data analytics project focused on understanding air quality trends, pollution patterns, health impacts, and electric vehicle adoption across India.

The objective of this project is to analyze AQI (Air Quality Index) data and supporting datasets to generate actionable business insights for an air purifier startup.

The analysis helps answer critical questions such as:

- Which cities and areas experience the worst air quality?
- What pollutants are most prominent across Southern Indian states?
- Does air quality improve during weekends compared to weekdays?
- Which months consistently show poor air quality?
- What are the major reported diseases across Indian states?
- Is there any relationship between EV adoption and AQI levels?

This project was developed as part of the Codebasics Data Analytics Challenge – AirPure Innovations Market Research Analytics.

---

## 🎯 Business Problem Statement

AirPure Innovations is a startup operating in the consumer appliances market, specifically focusing on air purifier development.

Before investing in product development and R&D, the company needs data-driven insights to understand:

1. Which pollutants and particles should the air purifier target?
2. What features should be incorporated into the product?
3. Which cities have the highest potential demand for air purifiers?
4. How can product R&D be aligned with localized pollution patterns?

The analysis focuses primarily on AQI severity mapping, health impact correlation, and environmental factors influencing air quality.

---

# 📊 Project Objectives

The primary objective is to perform data analysis using SQL and Python to answer seven business questions.

### Primary Analysis Questions

1. List the top 5 and bottom 5 areas with the highest average AQI between December 2024 and May 2025.

2. Identify the top 2 and bottom 2 prominent pollutants for each state in Southern India using AQI data from 2022 onwards.

3. Analyze whether AQI improves on weekends compared to weekdays in major Indian metro cities.

4. Identify the months that consistently show the worst air quality across the top 10 Indian states based on the number of distinct areas.

5. Analyze the number of days falling under each air quality category in Bengaluru between March and May 2025.

6. Identify the top two most reported diseases in each state over the past three years and compare them with the corresponding average AQI.

7. Identify the top five states with high EV adoption and analyze their average AQI compared to states with lower EV adoption.

---

# 🗂️ Dataset Description

The project uses four datasets.

| Dataset | Description |
|---|---|
| AQI Dataset | Day-wise AQI records for major cities and towns across India |
| Disease Dataset | State, district, disease-wise reported cases and deaths |
| Vehicle Dataset | State, vehicle class, and fuel type-wise vehicle registrations |
| Population Dataset | State and gender-wise projected urban population data |

### Data Coverage

| Dataset | Time Period |
|---|---|
| AQI | 2022 – 2025 |
| Disease | 2022 – 2025 |
| Vehicle | 2022 – 2025 |
| Population | 2011 – 2036 projections |

---

# 🛠️ Tools & Technologies Used

- Python
- SQL
- DuckDB
- Pandas
- NumPy
- Matplotlib
- Seaborn
- SciPy
- OpenPyXL
- Jupyter Notebook / VS Code

# 🧹 Data Cleaning Process

The following preprocessing steps were performed:
- Converted date columns into proper datetime format.
- Converted AQI values into numeric format.
- Converted disease cases and deaths into numeric values.
- Converted vehicle registration values into numeric format.
- Removed invalid or missing AQI records where necessary.
- Standardized state and city names.
- Extracted individual pollutants from comma-separated pollutant fields.
- Created additional calculated columns such as:
- Average AQI
- EV Adoption Percentage
- Weekend/Weekday Classification
- Disease Ranking

# SQL Analysis

The SQL queries are written using DuckDB.The SQL file contains complete queries for all seven primary analysis questions.
## Query Categories
Query	Analysis
Q1	Top and Bottom AQI Areas
Q2	Prominent Pollutants in Southern India
Q3	Weekend vs Weekday AQI
Q4	Worst AQI Months
Q5	Bengaluru Air Quality Categories
Q6	Disease and AQI Correlation
Q7	EV Adoption vs AQI

# 💡 Key Business Insights Framework

The analysis is designed to support three strategic dimensions.

# 1. Severity Mapping

Identify cities and states experiencing persistent or worsening air quality.
Business Use:
- Prioritize target cities.
- Identify potential markets for air purifiers.
- Understand regional pollution severity.

# 2. Health Impact Correlation

Analyze reported disease patterns alongside AQI data.
Business Use:
- Understand potential health-related market demand.
- Identify regions where air quality may be a major consumer concern.
- Support health-focused product positioning.

# 3. Demand Triggers

Explore relationships between pollution levels and environmental or transportation patterns.
Business Use:
- Understand when demand for air purifiers may increase.
- Identify seasonal product demand opportunities.
- Align product features with localized pollution conditions.

# ⚠️ Limitations
- AQI data availability may vary across cities and states.
- Disease reporting may not directly represent pollution-caused illnesses.
- EV adoption alone cannot explain changes in AQI.
- Population data is projected data and may not exactly represent actual population figures.
- Statistical relationships should not be interpreted as causal relationships without additional research.

# 📌 Conclusion

This project demonstrates an end-to-end data analytics workflow using SQL and Python to solve a real-world business problem.
The analysis combines environmental, health, transportation, and demographic datasets to generate insights for air purifier market strategy.
The project showcases practical skills in:
- Data Cleaning
- SQL Analytics
- Python Data Analysis
- Statistical Testing
- Data Visualization
- Business Problem Solving
- Market Research Analytics
