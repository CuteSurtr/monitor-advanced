@echo off
echo Launching Macro Economic Dashboard System
echo ==========================================

echo.
echo Step 1: Testing API connections...
py scripts\test_macro_apis.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo SUCCESS: API tests passed! Proceeding with data collection...
    echo.
    
    echo Step 2: Setting up InfluxDB buckets...
    py scripts\setup_macro_influxdb.py
    
    echo.
    echo Step 3: Collecting comprehensive macro data...
    py scripts\start_macro_system.py
    
    echo.
    echo Dashboard Ready!
    echo ==================
    echo.
    echo Access your Macro Economic Dashboard:
    echo    Grafana: http://localhost:3000
    echo    Login: admin / admin
    echo.
    echo Data Sources Active:
    echo    - Treasury yield curves and auctions
    echo    - Federal Reserve economic data (FRED)
    echo    - Bureau of Labor Statistics (BLS)
    echo    - Bureau of Economic Analysis (BEA)
    echo    - Energy Information Administration (EIA)
    echo    - Census Bureau economic indicators
    echo    - European Central Bank (ECB)
    echo    - International Monetary Fund (IMF)
    echo    - Bank for International Settlements (BIS)
    echo    - SEC EDGAR filings
    echo    - FINRA short interest data
    echo    - World Bank development indicators
    echo    - OECD leading indicators
    echo.
    echo SUCCESS: Your comprehensive macro dashboard is ready!
    echo.
    pause
) else (
    echo.
    echo ERROR: API tests failed. Please check your internet connection
    echo    and API key configuration.
    echo.
    pause
    exit /b 1
)