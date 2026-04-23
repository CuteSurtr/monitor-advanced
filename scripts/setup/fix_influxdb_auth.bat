@echo off
setlocal enabledelayedexpansion

echo Fixing InfluxDB Authentication Issues...
echo.

REM Credentials must come from environment variables, not from source.
if "%INFLUXDB_ADMIN_PASSWORD%"=="" (
    echo ERROR: INFLUXDB_ADMIN_PASSWORD environment variable is not set.
    pause
    exit /b 1
)
if "%INFLUXDB_TOKEN%"=="" (
    echo ERROR: INFLUXDB_TOKEN environment variable is not set.
    pause
    exit /b 1
)

REM Check if InfluxDB container is running
docker ps | findstr "stock_monitor_influxdb" >nul 2>&1
if %errorLevel% neq 0 (
    echo Error: InfluxDB container is not running!
    echo Please start your services first: docker-compose up -d
    pause
    exit /b 1
)

echo Step 1: Stopping InfluxDB container...
docker stop stock_monitor_influxdb

echo Step 2: Removing InfluxDB container...
docker rm stock_monitor_influxdb

echo Step 3: Starting InfluxDB with credentials from env...
docker run -d --name stock_monitor_influxdb --network stock_monitor_default -p 8086:8086 -e DOCKER_INFLUXDB_INIT_MODE=setup -e DOCKER_INFLUXDB_INIT_USERNAME=admin -e DOCKER_INFLUXDB_INIT_PASSWORD=%INFLUXDB_ADMIN_PASSWORD% -e DOCKER_INFLUXDB_INIT_ORG=stock_monitor -e DOCKER_INFLUXDB_INIT_BUCKET=market_data -e DOCKER_INFLUXDB_INIT_ADMIN_TOKEN=%INFLUXDB_TOKEN% -v influxdb_data:/var/lib/influxdb2 influxdb:2.7-alpine

echo Step 4: Waiting for InfluxDB to start...
timeout /t 30 /nobreak >nul

echo Step 5: Testing InfluxDB connection...
curl -s http://localhost:8086/health >nul 2>&1
if %errorLevel% equ 0 (
    echo  InfluxDB is responding
) else (
    echo  InfluxDB is not responding
    pause
    exit /b 1
)

echo Step 6: Testing authentication...
docker exec stock_monitor_influxdb influx org list --token %INFLUXDB_TOKEN% >nul 2>&1
if %errorLevel% equ 0 (
    echo  Authentication successful
) else (
    echo  Authentication failed
    pause
    exit /b 1
)

echo Step 7: Listing organizations...
docker exec stock_monitor_influxdb influx org list --token %INFLUXDB_TOKEN%

echo Step 8: Listing buckets...
docker exec stock_monitor_influxdb influx bucket list --token %INFLUXDB_TOKEN%

echo.
echo === InfluxDB Authentication Fixed! ===
echo.
echo Credentials (set via environment):
echo - Username: admin
echo - Password: (INFLUXDB_ADMIN_PASSWORD)
echo - Organization: stock_monitor
echo - Token: (INFLUXDB_TOKEN)
echo - Default Bucket: market_data
echo.
echo Next Steps:
echo 1. Update your Grafana data source configuration
echo 2. Use the token from your INFLUXDB_TOKEN env var
echo 3. Test the connection in Grafana
echo.
echo Your InfluxDB is now properly configured!
echo.
pause
