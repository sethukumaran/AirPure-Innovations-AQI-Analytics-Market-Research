-- ============================================================
-- AIRPURE INNOVATIONS: PRIMARY ANALYSIS SQL
-- SQL engine: DuckDB
-- Tables expected:
--   aqi, disease, vehicles, population
-- Dates in source are DD-MM-YYYY.
-- ============================================================

-- 0) Create cleaned views
CREATE OR REPLACE VIEW aqi_clean AS
SELECT
    TRY_STRPTIME(date, '%d-%m-%Y')::DATE AS observation_date,
    TRIM(state) AS state,
    TRIM(area) AS area,
    TRY_CAST(number_of_monitoring_stations AS DOUBLE) AS monitoring_stations,
    NULLIF(TRIM(prominent_pollutants), '') AS prominent_pollutants,
    TRY_CAST(aqi_value AS DOUBLE) AS aqi_value,
    TRIM(air_quality_status) AS air_quality_status
FROM aqi
WHERE TRY_STRPTIME(date, '%d-%m-%Y') IS NOT NULL
  AND TRY_CAST(aqi_value AS DOUBLE) IS NOT NULL;

CREATE OR REPLACE VIEW disease_clean AS
SELECT
    TRY_CAST(year AS INTEGER) AS year,
    TRY_CAST(week AS INTEGER) AS week,
    TRY_STRPTIME(outbreak_starting_date, '%d-%m-%Y')::DATE AS outbreak_starting_date,
    TRY_STRPTIME(reporting_date, '%d-%m-%Y')::DATE AS reporting_date,
    TRIM(state) AS state,
    TRIM(district) AS district,
    TRIM(disease_illness_name) AS disease_illness_name,
    TRIM(status) AS status,
    TRY_CAST(cases AS DOUBLE) AS cases,
    TRY_CAST(deaths AS DOUBLE) AS deaths
FROM disease
WHERE TRY_CAST(cases AS DOUBLE) IS NOT NULL;

CREATE OR REPLACE VIEW vehicles_clean AS
SELECT
    TRY_CAST(year AS INTEGER) AS year,
    TRIM(month) AS month,
    TRIM(state) AS state,
    TRIM(vehicle_class) AS vehicle_class,
    UPPER(TRIM(fuel)) AS fuel,
    TRY_CAST(value AS DOUBLE) AS vehicle_count
FROM vehicles
WHERE TRY_CAST(value AS DOUBLE) IS NOT NULL;

-- Q1. Top 5 and bottom 5 areas by average AQI, Dec-2024 to May-2025.
WITH area_summary AS (
    SELECT area, state, AVG(aqi_value) AS average_aqi,
           COUNT(*) AS observations
    FROM aqi_clean
    WHERE observation_date BETWEEN DATE '2024-12-01' AND DATE '2025-05-31'
    GROUP BY area, state
    HAVING COUNT(*) > 0
),
ranked AS (
    SELECT *, ROW_NUMBER() OVER (ORDER BY average_aqi DESC) AS high_rank,
              ROW_NUMBER() OVER (ORDER BY average_aqi ASC) AS low_rank
    FROM area_summary
)
SELECT 'Top 5 highest AQI' AS group_name, high_rank AS rank_no,
       area, state, average_aqi, observations
FROM ranked WHERE high_rank <= 5
UNION ALL
SELECT 'Bottom 5 lowest AQI', low_rank, area, state, average_aqi, observations
FROM ranked WHERE low_rank <= 5
ORDER BY group_name, rank_no;

-- Q2. Top 2 and bottom 2 prominent pollutants in southern states, 2022 onward.
-- Pollutant occurrence is counted once per AQI row.
WITH southern_states AS (
    SELECT * FROM (VALUES
        ('Andhra Pradesh'), ('Karnataka'), ('Kerala'),
        ('Tamil Nadu'), ('Telangana')
    ) AS t(state)
),
pollutant_counts AS (
    SELECT a.state,
           TRIM(pollutant) AS pollutant,
           COUNT(*) AS occurrence_count
    FROM aqi_clean a
    CROSS JOIN UNNEST(STRING_SPLIT(a.prominent_pollutants, ',')) AS u(pollutant)
    WHERE a.observation_date >= DATE '2022-01-01'
      AND a.state IN (SELECT state FROM southern_states)
      AND a.prominent_pollutants IS NOT NULL
    GROUP BY a.state, TRIM(pollutant)
),
ranked AS (
    SELECT *,
           ROW_NUMBER() OVER (PARTITION BY state ORDER BY occurrence_count DESC, pollutant) AS top_rank,
           ROW_NUMBER() OVER (PARTITION BY state ORDER BY occurrence_count ASC, pollutant) AS bottom_rank
    FROM pollutant_counts
)
SELECT state,
       CASE WHEN top_rank <= 2 THEN 'Top 2'
            WHEN bottom_rank <= 2 THEN 'Bottom 2' END AS group_name,
       CASE WHEN top_rank <= 2 THEN top_rank ELSE bottom_rank END AS rank_no,
       pollutant, occurrence_count
FROM ranked
WHERE top_rank <= 2 OR bottom_rank <= 2
ORDER BY state, group_name, rank_no;

-- Q3. Weekend vs weekday AQI in eight metro cities, last 1 year
WITH metros(city) AS (
    VALUES ('Delhi'), ('Mumbai'), ('Chennai'), ('Kolkata'),
           ('Bengaluru'), ('Hyderabad'), ('Ahmedabad'), ('Pune')
),
classified AS (
    SELECT area AS city,
           CASE WHEN EXTRACT(DAYOFWEEK FROM observation_date) IN (0,6)
                THEN 'Weekend' ELSE 'Weekday' END AS day_type,
           aqi_value
    FROM aqi_clean
    WHERE observation_date >= DATE '2024-06-20'
      AND observation_date <= DATE '2025-06-19'
      AND area IN (SELECT city FROM metros)
)
SELECT city, day_type, ROUND(AVG(aqi_value), 2) AS average_aqi,
       COUNT(*) AS observations
FROM classified
GROUP BY city, day_type
ORDER BY city, day_type;

-- Q4. Months with worst AQI across top 10 states by distinct areas.
WITH state_area_counts AS (
    SELECT state, COUNT(DISTINCT area) AS distinct_areas
    FROM aqi_clean
    GROUP BY state
),
top10_states AS (
    SELECT state
    FROM state_area_counts
    ORDER BY distinct_areas DESC
    LIMIT 10
),
monthly AS (
    SELECT state,
           EXTRACT(MONTH FROM observation_date) AS month_number,
           STRFTIME(observation_date, '%B') AS month_name,
           AVG(aqi_value) AS average_aqi
    FROM aqi_clean
    WHERE state IN (SELECT state FROM top10_states)
    GROUP BY state, month_number, month_name
)
SELECT month_name, month_number,
       ROUND(AVG(average_aqi), 2) AS cross_state_average_aqi,
       COUNT(DISTINCT state) AS states_present
FROM monthly
GROUP BY month_name, month_number
ORDER BY cross_state_average_aqi DESC;

-- Q5. Bengaluru air-quality categories, March-May 2025.
SELECT air_quality_status,
       COUNT(*) AS days_or_records,
       ROUND(AVG(aqi_value), 2) AS average_aqi
FROM aqi_clean
WHERE area = 'Bengaluru'
  AND observation_date BETWEEN DATE '2025-03-01' AND DATE '2025-05-31'
GROUP BY air_quality_status
ORDER BY days_or_records DESC;

-- Q6. Top 2 disease illnesses per state, with average AQI for the same 3-year period.
WITH disease_totals AS (
    SELECT state, disease_illness_name,
           SUM(cases) AS total_cases,
           SUM(deaths) AS total_deaths
    FROM disease_clean
    WHERE reporting_date BETWEEN DATE '2022-06-20' AND DATE '2025-06-19'
    GROUP BY state, disease_illness_name
),
ranked_diseases AS (
    SELECT *,
           ROW_NUMBER() OVER (PARTITION BY state ORDER BY total_cases DESC, disease_illness_name) AS disease_rank
    FROM disease_totals
),
aqi_by_state AS (
    SELECT state, AVG(aqi_value) AS average_aqi
    FROM aqi_clean
    WHERE observation_date BETWEEN DATE '2022-06-20' AND DATE '2025-06-19'
    GROUP BY state
)
SELECT d.state, d.disease_rank, d.disease_illness_name,
       d.total_cases, d.total_deaths,
       ROUND(a.average_aqi, 2) AS average_aqi_same_period
FROM ranked_diseases d
LEFT JOIN aqi_by_state a USING (state)
WHERE d.disease_rank <= 2
ORDER BY d.state, d.disease_rank;

-- Q7. EV adoption and AQI comparison.
-- EV adoption is measured as cumulative ELECTRIC vehicle registrations
-- in the available vehicle data period.
WITH ev_by_state AS (
    SELECT state,
           SUM(CASE WHEN fuel LIKE '%ELECTRIC%' THEN vehicle_count ELSE 0 END) AS ev_registrations,
           SUM(vehicle_count) AS all_vehicle_registrations
    FROM vehicles_clean
    GROUP BY state
),
aqi_by_state AS (
    SELECT state, AVG(aqi_value) AS average_aqi
    FROM aqi_clean
    GROUP BY state
),
ranked AS (
    SELECT e.*, a.average_aqi,
           ROW_NUMBER() OVER (ORDER BY ev_registrations DESC) AS ev_rank,
           NTILE(2) OVER (ORDER BY ev_registrations DESC) AS ev_group
    FROM ev_by_state e
    LEFT JOIN aqi_by_state a USING (state)
)
SELECT CASE WHEN ev_rank <= 5 THEN 'Top 5 EV states'
            WHEN ev_group = 2 THEN 'Lower EV group' END AS comparison_group,
       state, ev_registrations, all_vehicle_registrations,
       ROUND(100.0 * ev_registrations / NULLIF(all_vehicle_registrations,0), 2) AS ev_share_pct,
       ROUND(average_aqi, 2) AS average_aqi
FROM ranked
WHERE ev_rank <= 5 OR ev_group = 2
ORDER BY comparison_group, ev_registrations DESC;

-- Optional: one-row comparison for Q7.
WITH ev_by_state AS (
    SELECT state,
           SUM(CASE WHEN fuel LIKE '%ELECTRIC%' THEN vehicle_count ELSE 0 END) AS ev_registrations
    FROM vehicles_clean GROUP BY state
),
aqi_by_state AS (
    SELECT state, AVG(aqi_value) AS average_aqi
    FROM aqi_clean GROUP BY state
),
ranked AS (
    SELECT e.state, e.ev_registrations, a.average_aqi,
           NTILE(2) OVER (ORDER BY e.ev_registrations DESC) AS ev_group
    FROM ev_by_state e JOIN aqi_by_state a USING(state)
)
SELECT CASE WHEN ev_group = 1 THEN 'Higher EV group' ELSE 'Lower EV group' END AS ev_group,
       ROUND(AVG(average_aqi),2) AS mean_state_aqi,
       COUNT(*) AS states
FROM ranked
GROUP BY ev_group
ORDER BY ev_group;
