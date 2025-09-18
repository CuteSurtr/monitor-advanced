@echo off
echo Reloading all Grafana dashboards...
echo This will restart Grafana service to load all provisioned dashboards.

REM Check if Docker Compose is available
docker-compose --version >nul 2>&1
if %errorLevel% neq 0 (
    echo Error: docker-compose not found!
    pause
    exit /b 1
)

REM Check if we're in the right directory
if not exist "docker-compose.raspberry-pi.yml" (
    echo Error: Please run this script from the project root directory.
    pause
    exit /b 1
)

echo Stopping Grafana service...
docker-compose -f docker-compose.raspberry-pi.yml stop grafana

echo Removing Grafana container to ensure clean reload...
docker-compose -f docker-compose.raspberry-pi.yml rm -f grafana

echo Starting Grafana with all dashboards...
docker-compose -f docker-compose.raspberry-pi.yml up -d grafana

echo Waiting for Grafana to start...
timeout /t 15 /nobreak >nul

REM Check if Grafana is running
docker-compose -f docker-compose.raspberry-pi.yml ps grafana | findstr "Up" >nul
if %errorLevel% equ 0 (
    echo SUCCESS: Grafana is running!
    echo.
    echo Dashboard Access:
    echo    URL: http://localhost:3000
    echo    Login: admin / trading123
    echo.
    echo Available Dashboard Folders:
    echo    - Core Analytics - Main financial dashboards
    echo    - Advanced Analytics - Technical indicators ^& ML
    echo    - Economic Data - Macro economic analysis
    echo    - Professional Suite - Professional tier dashboards
    echo    - Specialized Views - Custom and specialized dashboards
    echo.
    echo All dashboards should now be visible in Grafana!
) else (
    echo ERROR: Grafana failed to start properly.
    echo Check logs with: docker-compose -f docker-compose.raspberry-pi.yml logs grafana
)

pause