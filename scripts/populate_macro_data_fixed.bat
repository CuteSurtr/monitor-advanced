@echo off
echo Populating InfluxDB macro_data bucket with sample economic data...
echo.

REM InfluxDB configuration - UPDATED FOR CURRENT SETUP
set ORG=stock_monitor
set BUCKET=macro_data
set TOKEN=xEoh_d1w_9u4rUmgZLCUqckVK5qGnF1FNs2_hzrrzfXQCXLJRRYPh5oqcE_T0nYmF7jqsJ-O6r2OEUVDWV-kew==
set CONTAINER=influxdb

echo Using container: %CONTAINER%
echo Using bucket: %BUCKET%
echo Using org: %ORG%
echo.

echo Generating Treasury yield curve data...

REM Generate sample Treasury data for the last 30 days with realistic variations
for /L %%i in (0,1,29) do (
    echo Writing Treasury data for day %%i...
    
    REM Calculate realistic variations
    set /a day_offset=%%i
    set /a yield_10y=42+%%i/3
    set /a yield_2y=48+%%i/2
    set /a yield_30y=45+%%i/4
    
    REM 10Y Treasury yield
    docker exec %CONTAINER% influx write --bucket %BUCKET% --org %ORG% --token %TOKEN% "treasury_yield_curve,maturity=10Y,security_type=treasury yield=%yield_10y%"
    
    REM 2Y Treasury yield
    docker exec %CONTAINER% influx write --bucket %BUCKET% --org %ORG% --token %TOKEN% "treasury_yield_curve,maturity=2Y,security_type=treasury yield=%yield_2y%"
    
    REM 30Y Treasury yield
    docker exec %CONTAINER% influx write --bucket %BUCKET% --org %ORG% --token %TOKEN% "treasury_yield_curve,maturity=30Y,security_type=treasury yield=%yield_30y%"
)

echo.
echo Generating economic indicators...

REM Generate CPI data with realistic variations
for /L %%i in (0,1,29) do (
    echo Writing CPI data for day %%i...
    set /a cpi_value=32+%%i/10
    docker exec %CONTAINER% influx write --bucket %BUCKET% --org %ORG% --token %TOKEN% "bls_economic_data,indicator=cpi,category=inflation value=%cpi_value%"
)

REM Generate unemployment data with realistic variations
for /L %%i in (0,1,29) do (
    echo Writing unemployment data for day %%i...
    set /a unemployment_value=38+%%i/20
    docker exec %CONTAINER% influx write --bucket %BUCKET% --org %ORG% --token %TOKEN% "bls_economic_data,indicator=unemployment_rate,category=labor value=%unemployment_value%"
)

echo.
echo Generating energy data...

REM Generate oil price data with realistic variations
for /L %%i in (0,1,29) do (
    echo Writing oil price data for day %%i...
    set /a oil_price=750+%%i*2
    docker exec %CONTAINER% influx write --bucket %BUCKET% --org %ORG% --token %TOKEN% "eia_energy_data,commodity=crude_oil,unit=usd_per_barrel value=%oil_price%"
)

REM Generate natural gas data
for /L %%i in (0,1,29) do (
    echo Writing natural gas data for day %%i...
    set /a gas_price=250+%%i*5
    docker exec %CONTAINER% influx write --bucket %BUCKET% --org %ORG% --token %TOKEN% "eia_energy_data,commodity=natural_gas,unit=usd_per_mmbtu value=%gas_price%"
)

echo.
echo Generating financial market data...

REM Generate VIX data with realistic variations
for /L %%i in (0,1,29) do (
    echo Writing VIX data for day %%i...
    set /a vix_value=200+%%i*3
    docker exec %CONTAINER% influx write --bucket %BUCKET% --org %ORG% --token %TOKEN% "fred_economic_data,indicator=vix,category=volatility value=%vix_value%"
)

REM Generate Fed funds rate data
for /L %%i in (0,1,29) do (
    echo Writing Fed funds rate data for day %%i...
    set /a fed_rate=525
    docker exec %CONTAINER% influx write --bucket %BUCKET% --org %ORG% --token %TOKEN% "fred_economic_data,indicator=fed_funds_rate,category=monetary_policy value=%fed_rate%"
)

echo.
echo Generating Treasury curve metrics...
for /L %%i in (0,1,29) do (
    echo Writing Treasury curve spread data for day %%i...
    set /a spread_10y_2y=%%i*2
    docker exec %CONTAINER% influx write --bucket %BUCKET% --org %ORG% --token %TOKEN% "treasury_curve_metrics,metric=10y_2y_spread spread=%spread_10y_2y%"
)

echo.
echo === Sample data population complete! ===
echo Bucket: %BUCKET%
echo Organization: %ORG%
echo Container: %CONTAINER%
echo.
echo Your Comprehensive Economic Dashboard should now work.
echo Check Grafana to see the data.
echo.
pause

