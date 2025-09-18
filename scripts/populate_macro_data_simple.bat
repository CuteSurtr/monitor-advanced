@echo off
echo Populating InfluxDB macro_data bucket with sample economic data...
echo.

REM InfluxDB configuration
set ORG_ID=0d4ca99e5255fe85
set BUCKET=macro_data
set TOKEN=trading_token_123

echo Generating Treasury yield curve data...

REM Generate sample Treasury data for the last 7 days
for /L %%i in (0,1,6) do (
    echo Writing Treasury data for day %%i...
    
    REM 10Y Treasury yield
    docker exec stock_monitor_influxdb influx write --bucket %BUCKET% --org-id %ORG_ID% --token %TOKEN% "treasury_yield_curve,maturity=10Y,security_type=treasury yield=4.2"
    
    REM 2Y Treasury yield
    docker exec stock_monitor_influxdb influx write --bucket %BUCKET% --org-id %ORG_ID% --token %TOKEN% "treasury_yield_curve,maturity=2Y,security_type=treasury yield=4.8"
    
    REM 30Y Treasury yield
    docker exec stock_monitor_influxdb influx write --bucket %BUCKET% --org-id %ORG_ID% --token %TOKEN% "treasury_yield_curve,maturity=30Y,security_type=treasury yield=4.5"
)

echo.
echo Generating economic indicators...

REM Generate CPI data
for /L %%i in (0,1,6) do (
    echo Writing CPI data for day %%i...
    docker exec stock_monitor_influxdb influx write --bucket %BUCKET% --org-id %ORG_ID% --token %TOKEN% "bls_economic_data,indicator=cpi,category=inflation value=3.2"
)

REM Generate unemployment data
for /L %%i in (0,1,6) do (
    echo Writing unemployment data for day %%i...
    docker exec stock_monitor_influxdb influx write --bucket %BUCKET% --org-id %ORG_ID% --token %TOKEN% "bls_economic_data,indicator=unemployment_rate,category=labor value=3.8"
)

echo.
echo Generating energy data...

REM Generate oil price data
for /L %%i in (0,1,6) do (
    echo Writing oil price data for day %%i...
    docker exec stock_monitor_influxdb influx write --bucket %BUCKET% --org-id %ORG_ID% --token %TOKEN% "eia_energy_data,commodity=crude_oil,unit=usd_per_barrel value=75.0"
)

echo.
echo Generating financial market data...

REM Generate VIX data
for /L %%i in (0,1,6) do (
    echo Writing VIX data for day %%i...
    docker exec stock_monitor_influxdb influx write --bucket %BUCKET% --org-id %ORG_ID% --token %TOKEN% "fred_economic_data,indicator=vix,category=volatility value=20.0"
)

REM Generate Fed funds rate data
for /L %%i in (0,1,6) do (
    echo Writing Fed funds rate data for day %%i...
    docker exec stock_monitor_influxdb influx write --bucket %BUCKET% --org-id %ORG_ID% --token %TOKEN% "fred_economic_data,indicator=fed_funds_rate,category=monetary_policy value=5.25"
)

echo.
echo === Sample data population complete! ===
echo Bucket: %BUCKET%
echo Organization ID: %ORG_ID%
echo.
echo Your Comprehensive Economic Dashboard should now work.
echo Check Grafana to see the data.
echo.
pause


