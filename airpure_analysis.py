
import pandas as pd
import numpy as np
import duckdb
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import ttest_ind
from pathlib import Path

BASE = Path("/content")
AQI_FILE = BASE /"day-wise-state-wise-air-quality-index-aqi-of-major-cities-and-towns-in-india.csv"
DISEASE_FILE = BASE /"master-data-state-district-and-disease-wise-cases-and-death-reported-due-to-outbreak-of-diseases-as-per-weekly-reports-under-idsp.csv"
VEHICLE_FILE = BASE /"master-data-state-vehicle-class-and-fuel-type-wise-total-number-of-vehicles-registered-in-each-month-in-india.csv"
POP_FILE = BASE /"population-projection-of-india-state-and-gender-wise-yearly-projected-urban-population-2011-2036.xlsx"

# 1. Load files
aqi = pd.read_csv(AQI_FILE, encoding="utf-8-sig")
disease = pd.read_csv(DISEASE_FILE, encoding="cp1252")
vehicles = pd.read_csv(VEHICLE_FILE, encoding="utf-8-sig")
population = pd.read_excel(POP_FILE)

# 2. Clean data
aqi["date"] = pd.to_datetime(aqi["date"], dayfirst=True, errors="coerce")
aqi["aqi_value"] = pd.to_numeric(aqi["aqi_value"], errors="coerce")
disease["reporting_date"] = pd.to_datetime(disease["reporting_date"], dayfirst=True, errors="coerce")
disease["cases"] = pd.to_numeric(disease["cases"], errors="coerce").fillna(0)
disease["deaths"] = pd.to_numeric(disease["deaths"], errors="coerce").fillna(0)
vehicles["value"] = pd.to_numeric(vehicles["value"], errors="coerce").fillna(0)
vehicles["fuel"] = vehicles["fuel"].astype(str).str.upper().str.strip()

# 3. Register DataFrames in DuckDB and execute SQL file
con = duckdb.connect()
con.register("aqi", aqi)
con.register("disease", disease)
con.register("vehicles", vehicles)
con.register("population", population)

sql_text = (BASE / "airpure_analysis.sql").read_text(encoding="utf-8")
# Run setup and each statement; final result of each SELECT is saved below.
statements = [s.strip() for s in sql_text.split(";") if s.strip()]
results = {}
for i, statement in enumerate(statements, start=1):
    try:
        result = con.execute(statement).fetchdf()
        if statement.upper().lstrip().startswith(("SELECT", "WITH")):
            results[f"query_{i}"] = result
            print(f"Query {i}: {result.shape}")
    except Exception as e:
        print(f"Query {i} failed: {e}")

# ============================================================
# 4. Direct Python analysis (same business logic as SQL)
# ============================================================

# Q1: top/bottom areas
q1 = (
    aqi.loc[aqi["date"].between("2024-12-01", "2025-05-31")]
       .groupby(["area", "state"], as_index=False)
       .agg(average_aqi=("aqi_value", "mean"), observations=("aqi_value", "count"))
)
top5_areas = q1.nlargest(5, "average_aqi")
bottom5_areas = q1.nsmallest(5, "average_aqi")
print("\nQ1 TOP 5\n", top5_areas)
print("\nQ1 BOTTOM 5\n", bottom5_areas)

# Q2: pollutants in southern India, 2022+
south = ["Andhra Pradesh", "Karnataka", "Kerala", "Tamil Nadu", "Telangana"]
q2 = aqi[(aqi["date"] >= "2022-01-01") & aqi["state"].isin(south)].copy()
q2["pollutant"] = q2["prominent_pollutants"].fillna("").str.split(",")
q2 = q2.explode("pollutant")
q2["pollutant"] = q2["pollutant"].str.strip()
pollutants = (q2[q2["pollutant"] != ""]
              .groupby(["state", "pollutant"]).size()
              .reset_index(name="occurrence_count"))
pollutants["top_rank"] = pollutants.groupby("state")["occurrence_count"].rank(method="first", ascending=False)
pollutants["bottom_rank"] = pollutants.groupby("state")["occurrence_count"].rank(method="first", ascending=True)
q2_result = pollutants[(pollutants["top_rank"] <= 2) | (pollutants["bottom_rank"] <= 2)]
print("\nQ2\n", q2_result.sort_values(["state", "occurrence_count"], ascending=[True, False]))

# Q3: metro weekends vs weekdays, last one year ending 2025-06-19
metros = ["Delhi", "Mumbai", "Chennai", "Kolkata", "Bengaluru", "Hyderabad", "Ahmedabad", "Pune"]
q3 = aqi[aqi["area"].isin(metros) & aqi["date"].between("2024-06-20", "2025-06-19")].copy()
q3["day_type"] = np.where(q3["date"].dt.dayofweek >= 5, "Weekend", "Weekday")
q3_result = q3.groupby(["area", "day_type"], as_index=False).agg(
    average_aqi=("aqi_value", "mean"), observations=("aqi_value", "count")
)
print("\nQ3\n", q3_result)

# Q4: top 10 states by distinct areas, then monthly AQI
top10_states = (aqi.groupby("state")["area"].nunique()
                .nlargest(10).index.tolist())
q4 = aqi[aqi["state"].isin(top10_states)].copy()
q4["month"] = q4["date"].dt.month
q4["month_name"] = q4["date"].dt.month_name()
q4_result = (q4.groupby(["month", "month_name"], as_index=False)["aqi_value"]
             .mean().rename(columns={"aqi_value": "average_aqi"})
             .sort_values("average_aqi", ascending=False))
print("\nQ4\n", q4_result)

# Q5: Bengaluru categories, Mar-May 2025
q5 = aqi[aqi["area"].eq("Bengaluru") & aqi["date"].between("2025-03-01", "2025-05-31")]
q5_result = q5.groupby("air_quality_status", as_index=False).agg(
    days_or_records=("aqi_value", "count"), average_aqi=("aqi_value", "mean")
).sort_values("days_or_records", ascending=False)
print("\nQ5\n", q5_result)

# Q6: top two diseases by cases + state AQI for same three-year period
d3 = disease[disease["reporting_date"].between("2022-06-20", "2025-06-19")].copy()
disease_totals = (d3.groupby(["state", "disease_illness_name"], as_index=False)
                  .agg(total_cases=("cases", "sum"), total_deaths=("deaths", "sum")))
disease_totals["disease_rank"] = disease_totals.groupby("state")["total_cases"].rank(
    method="first", ascending=False
)
aqi3 = aqi[aqi["date"].between("2022-06-20", "2025-06-19")]
aqi_state = aqi3.groupby("state", as_index=False)["aqi_value"].mean().rename(
    columns={"aqi_value": "average_aqi_same_period"}
)
q6_result = disease_totals[disease_totals["disease_rank"] <= 2].merge(aqi_state, on="state", how="left")
print("\nQ6\n", q6_result.sort_values(["state", "disease_rank"]))

# Q7: EV adoption vs AQI
ev = (vehicles.assign(is_ev=vehicles["fuel"].str.contains("ELECTRIC", na=False))
      .groupby("state", as_index=False)
      .agg(ev_registrations=("value", lambda s: 0)))  # placeholder overwritten below
ev_base = vehicles.groupby("state", as_index=False).agg(
    ev_registrations=("value", lambda s: s[vehicles.loc[s.index, "fuel"].str.contains("ELECTRIC", na=False)].sum()),
    all_vehicle_registrations=("value", "sum")
)
ev_base["ev_share_pct"] = 100 * ev_base["ev_registrations"] / ev_base["all_vehicle_registrations"].replace(0, np.nan)
aqi_state_all = aqi.groupby("state", as_index=False)["aqi_value"].mean().rename(columns={"aqi_value": "average_aqi"})
q7 = ev_base.merge(aqi_state_all, on="state", how="inner").sort_values("ev_registrations", ascending=False)
top5_ev = q7.head(5)
lower_ev = q7.iloc[5:]
print("\nQ7 TOP 5 EV STATES\n", top5_ev)
print("\nQ7 LOWER EV GROUP SUMMARY\n", lower_ev[["average_aqi"]].describe())

# Descriptive comparison and Welch t-test (not a causal conclusion)
higher_aqi = top5_ev["average_aqi"].dropna()
lower_aqi = lower_ev["average_aqi"].dropna()
t_stat, p_value = ttest_ind(higher_aqi, lower_aqi, equal_var=False)
print(f"\nQ7 Welch t-test: t={t_stat:.3f}, p={p_value:.4f}")
print("Interpret p-value together with sample size, coverage, and possible confounders.")

# ============================================================
# 5. VISUALIZATIONS
# ============================================================

sns.set_theme(style="whitegrid")

def save_show(filename):
    plt.tight_layout()
    plt.savefig(filename, dpi=200, bbox_inches="tight")
    plt.show()

# Chart 1: Top and bottom areas
plot_q1 = pd.concat([
    top5_areas.assign(group="Top 5 highest AQI"),
    bottom5_areas.assign(group="Bottom 5 lowest AQI")
])
plt.figure(figsize=(10, 6))
sns.barplot(data=plot_q1, x="average_aqi", y="area", hue="group", dodge=False)
plt.title("Highest and lowest average AQI areas (Dec 2024-May 2025)")
plt.xlabel("Average AQI")
plt.ylabel("Area")
save_show("q1_top_bottom_areas.png")

# Chart 2: Pollutants in southern states
plt.figure(figsize=(11, 6))
sns.barplot(data=pollutants.sort_values("occurrence_count", ascending=False),
            x="occurrence_count", y="pollutant", hue="state")
plt.title("Prominent pollutant occurrences by southern state (2022 onward)")
plt.xlabel("Number of AQI records mentioning pollutant")
plt.ylabel("Pollutant")
save_show("q2_southern_pollutants.png")

# Chart 3: Weekend vs weekday
plt.figure(figsize=(11, 6))
sns.barplot(data=q3_result, x="area", y="average_aqi", hue="day_type")
plt.title("Weekend vs weekday AQI in Indian metro cities")
plt.xlabel("City")
plt.ylabel("Average AQI")
plt.xticks(rotation=30)
save_show("q3_weekend_weekday_aqi.png")

# Chart 4: Worst months
plt.figure(figsize=(10, 5))
sns.barplot(data=q4_result, x="month_name", y="average_aqi")
plt.title("Monthly AQI across top 10 states by distinct areas")
plt.xlabel("Month")
plt.ylabel("Average AQI")
plt.xticks(rotation=30)
save_show("q4_worst_months.png")

# Chart 5: Bengaluru categories
plt.figure(figsize=(9, 5))
sns.barplot(data=q5_result, x="air_quality_status", y="days_or_records")
plt.title("Bengaluru air-quality categories (March-May 2025)")
plt.xlabel("Air quality category")
plt.ylabel("Number of records")
plt.xticks(rotation=30)
save_show("q5_bengaluru_categories.png")

# Chart 6: Disease cases by state
top_disease_plot = q6_result.sort_values("total_cases", ascending=False).copy()
top_disease_plot["label"] = top_disease_plot["state"] + " - " + top_disease_plot["disease_illness_name"]
plt.figure(figsize=(12, 8))
sns.barplot(data=top_disease_plot, x="total_cases", y="label")
plt.title("Top two reported diseases per state (past three years)")
plt.xlabel("Total reported cases")
plt.ylabel("State - disease")
save_show("q6_top_diseases.png")

# Chart 7: EV registrations and AQI relationship
plt.figure(figsize=(10, 6))
sns.scatterplot(data=q7, x="ev_registrations", y="average_aqi", s=80)
for _, row in q7.nlargest(10, "ev_registrations").iterrows():
    plt.annotate(row["state"], (row["ev_registrations"], row["average_aqi"]),
                 xytext=(5, 5), textcoords="offset points", fontsize=8)
plt.title("EV registrations vs average AQI by state")
plt.xlabel("EV registrations in available vehicle data")
plt.ylabel("Average AQI")
save_show("q7_ev_vs_aqi.png")

# Optional: export all important outputs to Excel
with pd.ExcelWriter("airpure_analysis_outputs.xlsx", engine="openpyxl") as writer:
    top5_areas.to_excel(writer, "Q1_Top5_Areas", index=False)
    bottom5_areas.to_excel(writer, "Q1_Bottom5_Areas", index=False)
    q2_result.to_excel(writer, "Q2_Pollutants", index=False)
    q3_result.to_excel(writer, "Q3_Weekend_Weekday", index=False)
    q4_result.to_excel(writer, "Q4_Monthly_AQI", index=False)
    q5_result.to_excel(writer, "Q5_Bengaluru", index=False)
    q6_result.to_excel(writer, "Q6_Diseases_AQI", index=False)
    q7.to_excel(writer, "Q7_EV_AQI", index=False)

print("\nDone. PNG charts and airpure_analysis_outputs.xlsx have been created.")

"""# New section"""