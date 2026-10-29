-- ============================================================
-- World Bank AWS Analytics Pipeline
-- Example Analytical Queries
-- ============================================================


-- ============================================================
-- 1. Preview historical analytical dataset
-- ============================================================

SELECT *
FROM worldbank_analytics.vw_country_indicators
LIMIT 20;

-- ============================================================
-- 2. Top countries by latest GDP per capita
-- ============================================================

SELECT
    country_name,
    region,
    year,
    value AS gdp_per_capita

FROM worldbank_analytics.vw_latest_country_indicators

WHERE short_name = 'gdp_per_capita'

ORDER BY value DESC

LIMIT 10;

-- ============================================================
-- 3. Highest unemployment rates
-- ============================================================

SELECT
    country_name,
    region,
    year,
    value AS unemployment_rate

FROM worldbank_analytics.vw_latest_country_indicators

WHERE short_name = 'unemployment'

ORDER BY value DESC

LIMIT 10;

-- ============================================================
-- 4. Average GDP per capita by region
-- ============================================================

SELECT
    region,
    year,
    avg_value AS average_gdp_per_capita

FROM worldbank_analytics.vw_regional_indicator_summary

WHERE short_name = 'gdp_per_capita'

ORDER BY
    year DESC,
    avg_value DESC;


    -- ============================================================
-- 5. GDP per capita and internet usage analysis
-- ============================================================

SELECT
    country_name,
    region,
    income_level,
    year,
    gdp_per_capita,
    internet_usage

FROM worldbank_analytics.vw_country_year_metrics

WHERE
    year = 2023
    AND gdp_per_capita IS NOT NULL
    AND internet_usage IS NOT NULL

ORDER BY gdp_per_capita DESC;

-- ============================================================
-- 6. GDP per capita and life expectancy
-- ============================================================

SELECT
    country_name,
    region,
    income_level,
    year,
    gdp_per_capita,
    life_expectancy

FROM worldbank_analytics.vw_country_year_metrics

WHERE
    year = 2023
    AND gdp_per_capita IS NOT NULL
    AND life_expectancy IS NOT NULL

ORDER BY gdp_per_capita DESC;


-- ============================================================
-- 7. Observation coverage by year
-- ============================================================

SELECT
    year,
    COUNT(*) AS total_observations

FROM worldbank_analytics.fact_indicators

GROUP BY year

ORDER BY year;

-- ============================================================
-- 8. Observation coverage by indicator
-- ============================================================

SELECT
    i.indicator_name,
    i.short_name,
    COUNT(*) AS total_observations

FROM worldbank_analytics.fact_indicators f

JOIN worldbank_analytics.dim_indicator i
    ON f.indicator_code = i.indicator_code

GROUP BY
    i.indicator_name,
    i.short_name

ORDER BY total_observations DESC;