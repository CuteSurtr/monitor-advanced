@echo off
setlocal enabledelayedexpansion

echo Populating InfluxDB macro_data bucket with sample economic data...
echo.

REM InfluxDB configuration
set INFLUXDB_URL=http://localhost:8086
set ORG=stock_monitor
set BUCKET=macro_data
set TOKEN=trading_token_123

echo Generating Treasury yield curve data...

REM Generate sample Treasury data for the last 7 days
for /L %%i in (0,1,6) do (
    echo Writing Treasury data for day %%i...
    
    REM 10Y Treasury yield
    curl -s -X POST "%INFLUXDB_URL%/api/v2/write" -H "Authorization: Token %TOKEN%" -H "Content-Type: application/octet-stream" -d "treasury_yield_curve,maturity=10Y,security_type=treasury yield=4.2" --data-urlencode "org=%ORG%" --data-urlencode "bucket=%BUCKET%" --data-urlencode "precision=ns"
    
    REM 2Y Treasury yield
    curl -s -X POST "%INFLUXDB_URL%/api/v2/write" -H "Authorization: Token %TOKEN%" -H "Content-Type: application/octet-stream" -d "treasury_yield_curve,maturity=2Y,security_type=treasury yield=4.8" --data-urlencode "org=%ORG%" --data-urlencode "bucket=%BUCKET%" --data-urlencode "precision=ns"
    
    REM 30Y Treasury yield
    curl -s -X POST "%INFLUXDB_URL%/api/v2/write" -H "Authorization: Token %TOKEN%" -H "Content-Type: application/octet-stream" -d "treasury_yield_curve,maturity=30Y,security_type=treasury yield=4.5" --data-urlencode "org=%ORG%" --data-urlencode "bucket=%BUCKET%" --data-urlencode "precision=ns"
)

echo.
echo Generating economic indicators...

REM Generate CPI data
for /L %%i in (0,1,6) do (
    echo Writing CPI data for day %%i...
    curl -s -X POST "%INFLUXDB_URL%/api/v2/write" -H "Authorization: Token %TOKEN%" -H "Content-Type: application/octet-stream" -d "bls_economic_data,indicator=cpi,category=inflation value=3.2" --data-urlencode "org=%ORG%" --data-urlencode "bucket=%BUCKET%" --data-urlencode "precision=ns"
)

REM Generate unemployment data
for /L %%i in (0,1,6) do (
    echo Writing unemployment data for day %%i...
    curl -s -X POST "%INFLUXDB_URL%/api/v2/write" -H "Authorization: Token %TOKEN%" -H "Content-Type: application/octet-stream" -d "bls_economic_data,indicator=unemployment_rate,category=labor value=3.8" --data-urlencode "org=%ORG%" --data-urlencode "bucket=%BUCKET%" --data-urlencode "precision=ns"
)

echo.
echo Generating energy data...

REM Generate oil price data
for /L %%i in (0,1,6) do (
    echo Writing oil price data for day %%i...
    curl -s -X POST "%INFLUXDB_URL%/api/v2/write" -H "Authorization: Token %TOKEN%" -H "Content-Type: application/octet-stream" -d "eia_energy_data,commodity=crude_oil,unit=usd_per_barrel value=75.0" --data-urlencode "org=%ORG%" --data-urlencode "bucket=%BUCKET%" --data-urlencode "precision=ns"
)

echo.
echo Generating financial market data...

REM Generate VIX data
for /L %%i in (0,1,6) do (
    echo Writing VIX data for day %%i...
    curl -s -X POST "%INFLUXDB_URL%/api/v2/write" -H "Authorization: Token %TOKEN%" -H "Content-Type: application/octet-stream" -d "fred_economic_data,indicator=vix,category=volatility value=20.0" --data-urlencode "org=%ORG%" --data-urlencode "bucket=%BUCKET%" --data-urlencode "precision=ns"
)

REM Generate Fed funds rate data
for /L %%i in (0,1,6) do (
    echo Writing Fed funds rate data for day %%i...
    curl -s -X POST "%INFLUXDB_URL%/api/v2/write" -H "Authorization: Token %TOKEN%" -H "Content-Type: application/octet-stream" -d "fred_economic_data,indicator=fed_funds_rate,category=monetary_policy value=5.25" --data-urlencode "org=%ORG%" --data-urlencode "bucket=%BUCKET%" --data-urlencode "precision=ns"
)

echo.
echo === Sample data population complete! ===
echo Bucket: %BUCKET%
echo Organization: %ORG%
echo.
echo Your Comprehensive Economic Dashboard should now work.
echo Check Grafana to see the data.
echo.
pause


