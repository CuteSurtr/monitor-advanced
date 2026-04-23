-- Economic Indicators Multi-Period Analysis with Distance-to-Target
-- Following the FRED specification with proper deviation calculations

WITH base_data AS (
  -- Get latest data for each series
  SELECT DISTINCT ON (series_id) 
    series_id, 
    observation_date, 
    value
  FROM economic_data.fred_data 
  WHERE observation_date <= CURRENT_DATE
  ORDER BY series_id, observation_date DESC
),

-- Calculate YoY metrics and deviations
cpi_metrics AS (
  SELECT 
    d1.observation_date,
    -- CPI YoY calculation
    100 * (d1.value / d12.value - 1) as cpi_yoy,
    -- CPI deviation from 2.0% target
    ABS(100 * (d1.value / d12.value - 1) - 2.0) as cpi_dev
  FROM economic_data.fred_data d1
  JOIN economic_data.fred_data d12 ON 
    d1.series_id = d12.series_id AND 
    d12.observation_date = d1.observation_date - INTERVAL '12 months'
  WHERE d1.series_id = 'CPIAUCSL'
    AND d1.observation_date >= '2020-01-01'
),

core_pce_metrics AS (
  SELECT 
    d1.observation_date,
    100 * (d1.value / d12.value - 1) as core_pce_yoy
  FROM economic_data.fred_data d1
  JOIN economic_data.fred_data d12 ON 
    d1.series_id = d12.series_id AND 
    d12.observation_date = d1.observation_date - INTERVAL '12 months'
  WHERE d1.series_id = 'PCEPILFE'
    AND d1.observation_date >= '2020-01-01'
),

fed_funds_metrics AS (
  SELECT 
    observation_date,
    value as fed_funds_level
  FROM economic_data.fred_data 
  WHERE series_id = 'FEDFUNDS'
    AND observation_date >= '2020-01-01'
),

combined_metrics AS (
  SELECT 
    c.observation_date,
    c.cpi_yoy,
    c.cpi_dev,
    p.core_pce_yoy,
    f.fed_funds_level,
    -- Real Fed Funds Rate = Nominal - Core PCE
    f.fed_funds_level - p.core_pce_yoy as real_ffr,
    -- Real FFR deviation from 1.0% target
    ABS(f.fed_funds_level - p.core_pce_yoy - 1.0) as rffr_dev
  FROM cpi_metrics c
  JOIN core_pce_metrics p ON c.observation_date = p.observation_date
  JOIN fed_funds_metrics f ON c.observation_date = f.observation_date
),

unemployment_metrics AS (
  SELECT 
    observation_date,
    value as unemployment_rate,
    -- Unemployment deviation from 4.0% target
    ABS(value - 4.0) as u3_dev
  FROM economic_data.fred_data 
  WHERE series_id = 'UNRATE'
    AND observation_date >= '2020-01-01'
),

gdp_metrics AS (
  SELECT 
    observation_date,
    value as gdp_yoy,
    -- GDP deviation from 2.0% target
    ABS(value - 2.0) as gdp_dev
  FROM economic_data.fred_data 
  WHERE series_id = 'A191RL1Q225SBEA'
    AND observation_date >= '2020-01-01'
),

-- Calculate trailing averages for each metric
cpi_periods AS (
  SELECT 
    'CPI Inflation YoY' as indicator,
    ROUND(AVG(cpi_yoy) FILTER (WHERE observation_date >= CURRENT_DATE - INTERVAL '1 month'), 2) as value_1m,
    ROUND(AVG(cpi_yoy) FILTER (WHERE observation_date >= CURRENT_DATE - INTERVAL '6 months'), 2) as value_6m,
    ROUND(AVG(cpi_yoy) FILTER (WHERE observation_date >= CURRENT_DATE - INTERVAL '12 months'), 2) as value_12m,
    ROUND(AVG(cpi_yoy) FILTER (WHERE observation_date >= CURRENT_DATE - INTERVAL '3 years'), 2) as value_3y,
    ROUND(AVG(cpi_yoy) FILTER (WHERE observation_date >= CURRENT_DATE - INTERVAL '5 years'), 2) as value_5y,
    ROUND(AVG(cpi_yoy) FILTER (WHERE observation_date >= CURRENT_DATE - INTERVAL '10 years'), 2) as value_10y,
    -- Deviation averages
    ROUND(AVG(cpi_dev) FILTER (WHERE observation_date >= CURRENT_DATE - INTERVAL '1 month'), 2) as dev_1m,
    ROUND(AVG(cpi_dev) FILTER (WHERE observation_date >= CURRENT_DATE - INTERVAL '6 months'), 2) as dev_6m,
    ROUND(AVG(cpi_dev) FILTER (WHERE observation_date >= CURRENT_DATE - INTERVAL '12 months'), 2) as dev_12m,
    ROUND(AVG(cpi_dev) FILTER (WHERE observation_date >= CURRENT_DATE - INTERVAL '3 years'), 2) as dev_3y,
    ROUND(AVG(cpi_dev) FILTER (WHERE observation_date >= CURRENT_DATE - INTERVAL '5 years'), 2) as dev_5y,
    ROUND(AVG(cpi_dev) FILTER (WHERE observation_date >= CURRENT_DATE - INTERVAL '10 years'), 2) as dev_10y
  FROM combined_metrics
),

rffr_periods AS (
  SELECT 
    'Real Fed Funds Rate' as indicator,
    ROUND(AVG(real_ffr) FILTER (WHERE observation_date >= CURRENT_DATE - INTERVAL '1 month'), 2) as value_1m,
    ROUND(AVG(real_ffr) FILTER (WHERE observation_date >= CURRENT_DATE - INTERVAL '6 months'), 2) as value_6m,
    ROUND(AVG(real_ffr) FILTER (WHERE observation_date >= CURRENT_DATE - INTERVAL '12 months'), 2) as value_12m,
    ROUND(AVG(real_ffr) FILTER (WHERE observation_date >= CURRENT_DATE - INTERVAL '3 years'), 2) as value_3y,
    ROUND(AVG(real_ffr) FILTER (WHERE observation_date >= CURRENT_DATE - INTERVAL '5 years'), 2) as value_5y,
    ROUND(AVG(real_ffr) FILTER (WHERE observation_date >= CURRENT_DATE - INTERVAL '10 years'), 2) as value_10y,
    -- Deviation averages  
    ROUND(AVG(rffr_dev) FILTER (WHERE observation_date >= CURRENT_DATE - INTERVAL '1 month'), 2) as dev_1m,
    ROUND(AVG(rffr_dev) FILTER (WHERE observation_date >= CURRENT_DATE - INTERVAL '6 months'), 2) as dev_6m,
    ROUND(AVG(rffr_dev) FILTER (WHERE observation_date >= CURRENT_DATE - INTERVAL '12 months'), 2) as dev_12m,
    ROUND(AVG(rffr_dev) FILTER (WHERE observation_date >= CURRENT_DATE - INTERVAL '3 years'), 2) as dev_3y,
    ROUND(AVG(rffr_dev) FILTER (WHERE observation_date >= CURRENT_DATE - INTERVAL '5 years'), 2) as dev_5y,
    ROUND(AVG(rffr_dev) FILTER (WHERE observation_date >= CURRENT_DATE - INTERVAL '10 years'), 2) as dev_10y
  FROM combined_metrics
),

unemployment_periods AS (
  SELECT 
    'Unemployment Rate (U-3)' as indicator,
    ROUND(AVG(unemployment_rate) FILTER (WHERE observation_date >= CURRENT_DATE - INTERVAL '1 month'), 2) as value_1m,
    ROUND(AVG(unemployment_rate) FILTER (WHERE observation_date >= CURRENT_DATE - INTERVAL '6 months'), 2) as value_6m,
    ROUND(AVG(unemployment_rate) FILTER (WHERE observation_date >= CURRENT_DATE - INTERVAL '12 months'), 2) as value_12m,
    ROUND(AVG(unemployment_rate) FILTER (WHERE observation_date >= CURRENT_DATE - INTERVAL '3 years'), 2) as value_3y,
    ROUND(AVG(unemployment_rate) FILTER (WHERE observation_date >= CURRENT_DATE - INTERVAL '5 years'), 2) as value_5y,
    ROUND(AVG(unemployment_rate) FILTER (WHERE observation_date >= CURRENT_DATE - INTERVAL '10 years'), 2) as value_10y,
    -- Deviation averages
    ROUND(AVG(u3_dev) FILTER (WHERE observation_date >= CURRENT_DATE - INTERVAL '1 month'), 2) as dev_1m,
    ROUND(AVG(u3_dev) FILTER (WHERE observation_date >= CURRENT_DATE - INTERVAL '6 months'), 2) as dev_6m,
    ROUND(AVG(u3_dev) FILTER (WHERE observation_date >= CURRENT_DATE - INTERVAL '12 months'), 2) as dev_12m,
    ROUND(AVG(u3_dev) FILTER (WHERE observation_date >= CURRENT_DATE - INTERVAL '3 years'), 2) as dev_3y,
    ROUND(AVG(u3_dev) FILTER (WHERE observation_date >= CURRENT_DATE - INTERVAL '5 years'), 2) as dev_5y,
    ROUND(AVG(u3_dev) FILTER (WHERE observation_date >= CURRENT_DATE - INTERVAL '10 years'), 2) as dev_10y
  FROM unemployment_metrics
),

gdp_periods AS (
  SELECT 
    'GDP Growth YoY' as indicator,
    ROUND(AVG(gdp_yoy) FILTER (WHERE observation_date >= CURRENT_DATE - INTERVAL '3 months'), 2) as value_1m,  -- 1q
    ROUND(AVG(gdp_yoy) FILTER (WHERE observation_date >= CURRENT_DATE - INTERVAL '6 months'), 2) as value_6m,  -- 2q
    ROUND(AVG(gdp_yoy) FILTER (WHERE observation_date >= CURRENT_DATE - INTERVAL '12 months'), 2) as value_12m, -- 4q
    ROUND(AVG(gdp_yoy) FILTER (WHERE observation_date >= CURRENT_DATE - INTERVAL '3 years'), 2) as value_3y,   -- 12q
    ROUND(AVG(gdp_yoy) FILTER (WHERE observation_date >= CURRENT_DATE - INTERVAL '5 years'), 2) as value_5y,   -- 20q
    ROUND(AVG(gdp_yoy) FILTER (WHERE observation_date >= CURRENT_DATE - INTERVAL '10 years'), 2) as value_10y, -- 40q
    -- Deviation averages
    ROUND(AVG(gdp_dev) FILTER (WHERE observation_date >= CURRENT_DATE - INTERVAL '3 months'), 2) as dev_1m,
    ROUND(AVG(gdp_dev) FILTER (WHERE observation_date >= CURRENT_DATE - INTERVAL '6 months'), 2) as dev_6m,
    ROUND(AVG(gdp_dev) FILTER (WHERE observation_date >= CURRENT_DATE - INTERVAL '12 months'), 2) as dev_12m,
    ROUND(AVG(gdp_dev) FILTER (WHERE observation_date >= CURRENT_DATE - INTERVAL '3 years'), 2) as dev_3y,
    ROUND(AVG(gdp_dev) FILTER (WHERE observation_date >= CURRENT_DATE - INTERVAL '5 years'), 2) as dev_5y,
    ROUND(AVG(gdp_dev) FILTER (WHERE observation_date >= CURRENT_DATE - INTERVAL '10 years'), 2) as dev_10y
  FROM gdp_metrics
)

-- Combine all indicators
SELECT indicator, value_1m, value_6m, value_12m, value_3y, value_5y, value_10y,
       dev_1m, dev_6m, dev_12m, dev_3y, dev_5y, dev_10y
FROM cpi_periods
UNION ALL
SELECT indicator, value_1m, value_6m, value_12m, value_3y, value_5y, value_10y,
       dev_1m, dev_6m, dev_12m, dev_3y, dev_5y, dev_10y  
FROM rffr_periods
UNION ALL
SELECT indicator, value_1m, value_6m, value_12m, value_3y, value_5y, value_10y,
       dev_1m, dev_6m, dev_12m, dev_3y, dev_5y, dev_10y
FROM unemployment_periods  
UNION ALL
SELECT indicator, value_1m, value_6m, value_12m, value_3y, value_5y, value_10y,
       dev_1m, dev_6m, dev_12m, dev_3y, dev_5y, dev_10y
FROM gdp_periods
ORDER BY indicator;