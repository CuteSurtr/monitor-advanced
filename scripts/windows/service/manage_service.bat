@echo off
REM Stock Monitor Windows Service Manager
REM This script provides easy management of the Stock Monitor service

setlocal enabledelayedexpansion

set SERVICE_NAME=StockMonitor
set SCRIPT_DIR=%~dp0

:menu
cls
echo ================================================================
echo   Stock Monitor - Service Management
echo ================================================================
echo.
echo Service Name: %SERVICE_NAME%
echo.

REM Check service status
sc query "%SERVICE_NAME%" >nul 2>&1
if %errorLevel% equ 0 (
    for /f "tokens=3" %%a in ('sc query "%SERVICE_NAME%" ^| find "STATE"') do set SERVICE_STATE=%%a
    echo Current Status: !SERVICE_STATE!
) else (
    echo Current Status: NOT INSTALLED
    set SERVICE_STATE=NOT_INSTALLED
)

echo.
echo Available Actions:
echo.
if "%SERVICE_STATE%" == "NOT_INSTALLED" (
    echo   [1] Install Service
    echo   [2] View Installation Guide
) else (
    if "%SERVICE_STATE%" == "RUNNING" (
        echo   [1] Stop Service
        echo   [2] Restart Service
        echo   [3] View Service Status
        echo   [4] View Logs
        echo   [5] Open Dashboard
        echo   [6] Uninstall Service
    ) else (
        echo   [1] Start Service
        echo   [2] View Service Status
        echo   [3] View Logs
        echo   [4] Uninstall Service
        echo   [5] Reinstall Service
    )
)
echo.
echo   [8] Service Configuration
echo   [9] Help
echo   [0] Exit
echo.

set /p choice=Enter your choice (0-9): 

if "%choice%" == "0" goto :exit
if "%choice%" == "1" goto :action1
if "%choice%" == "2" goto :action2
if "%choice%" == "3" goto :action3
if "%choice%" == "4" goto :action4
if "%choice%" == "5" goto :action5
if "%choice%" == "6" goto :action6
if "%choice%" == "8" goto :config
if "%choice%" == "9" goto :help

echo Invalid choice. Please try again.
pause
goto :menu

:action1
if "%SERVICE_STATE%" == "NOT_INSTALLED" (
    echo Installing service...
    call "%SCRIPT_DIR%install_service.bat"
) else if "%SERVICE_STATE%" == "RUNNING" (
    echo Stopping service...
    net stop %SERVICE_NAME%
    if %errorLevel% equ 0 (
        echo ✓ Service stopped successfully
    ) else (
        echo ✗ Failed to stop service
    )
) else (
    echo Starting service...
    net start %SERVICE_NAME%
    if %errorLevel% equ 0 (
        echo ✓ Service started successfully
        echo Dashboard available at: http://localhost:8080
    ) else (
        echo ✗ Failed to start service
        echo Check logs for details
    )
)
pause
goto :menu

:action2
if "%SERVICE_STATE%" == "NOT_INSTALLED" (
    goto :help
) else if "%SERVICE_STATE%" == "RUNNING" (
    echo Restarting service...
    net stop %SERVICE_NAME%
    timeout /t 3 /nobreak >nul
    net start %SERVICE_NAME%
    if %errorLevel% equ 0 (
        echo ✓ Service restarted successfully
    ) else (
        echo ✗ Failed to restart service
    )
) else (
    echo Displaying service status...
    sc query %SERVICE_NAME%
    echo.
    sc qc %SERVICE_NAME%
)
pause
goto :menu

:action3
if "%SERVICE_STATE%" == "NOT_INSTALLED" (
    echo Service is not installed.
) else (
    echo Displaying detailed service status...
    sc query %SERVICE_NAME%
    echo.
    sc queryex %SERVICE_NAME%
)
pause
goto :menu

:action4
if "%SERVICE_STATE%" == "NOT_INSTALLED" (
    call "%SCRIPT_DIR%uninstall_service.bat"
) else (
    echo Displaying service logs...
    echo.
    echo === Standard Output Log ===
    if exist "..\..\..\logs\service_stdout.log" (
        type "..\..\..\logs\service_stdout.log" | more
    ) else (
        echo No stdout log found
    )
    echo.
    echo === Standard Error Log ===
    if exist "..\..\..\logs\service_stderr.log" (
        type "..\..\..\logs\service_stderr.log" | more
    ) else (
        echo No stderr log found
    )
    echo.
    echo === Application Log ===
    if exist "..\..\..\logs\stock_monitor.log" (
        type "..\..\..\logs\stock_monitor.log" | more
    ) else (
        echo No application log found
    )
)
pause
goto :menu

:action5
if "%SERVICE_STATE%" == "NOT_INSTALLED" (
    echo Service is not installed.
    pause
    goto :menu
) else if "%SERVICE_STATE%" == "RUNNING" (
    echo Opening dashboard...
    start http://localhost:8080
) else (
    echo Reinstalling service...
    call "%SCRIPT_DIR%uninstall_service.bat"
    timeout /t 3 /nobreak >nul
    call "%SCRIPT_DIR%install_service.bat"
)
pause
goto :menu

:action6
if "%SERVICE_STATE%" == "NOT_INSTALLED" (
    echo Service is not installed.
) else (
    echo Uninstalling service...
    call "%SCRIPT_DIR%uninstall_service.bat"
)
pause
goto :menu

:config
cls
echo ================================================================
echo   Service Configuration
echo ================================================================
echo.
if "%SERVICE_STATE%" == "NOT_INSTALLED" (
    echo Service is not installed.
    echo Install the service first to view configuration.
) else (
    echo Current service configuration:
    echo.
    sc qc %SERVICE_NAME%
    echo.
    echo Configuration files:
    echo   Main Config: ..\..\..\config\config.yaml
    echo   Desktop Config: ..\..\..\config\config.desktop.yaml
    echo.
    echo Log files:
    echo   Stdout: ..\..\..\logs\service_stdout.log
    echo   Stderr: ..\..\..\logs\service_stderr.log
    echo   Application: ..\..\..\logs\stock_monitor.log
    echo.
    echo To modify service parameters, use:
    echo   %SCRIPT_DIR%nssm.exe edit %SERVICE_NAME%
)
pause
goto :menu

:help
cls
echo ================================================================
echo   Stock Monitor Service - Help
echo ================================================================
echo.
echo OVERVIEW:
echo   The Stock Monitor can run as a Windows service for automatic
echo   startup and background operation.
echo.
echo PREREQUISITES:
echo   - Python environment must be set up
echo   - NSSM (Non-Sucking Service Manager) required
echo   - Administrator privileges for service management
echo.
echo INSTALLATION:
echo   1. Download NSSM from: https://nssm.cc/download
echo   2. Extract nssm.exe to: %SCRIPT_DIR%
echo   3. Run install_service.bat as Administrator
echo.
echo CONFIGURATION:
echo   - Edit config\config.yaml with your API keys
echo   - Service uses config\config.yaml by default
echo   - Logs are written to logs\ directory
echo.
echo MANAGEMENT:
echo   - Use this script for easy management
echo   - Or use Windows Services console (services.msc)
echo   - Or use command line: net start/stop %SERVICE_NAME%
echo.
echo TROUBLESHOOTING:
echo   - Check logs in logs\ directory
echo   - Verify Python environment: venv\Scripts\python.exe
echo   - Ensure config file exists and is valid
echo   - Check Windows Event Viewer for system errors
echo.
echo ACCESS:
echo   - Dashboard: http://localhost:8080
echo   - Grafana: http://localhost:3000
echo   - Prometheus: http://localhost:9090
echo.
echo For more help, see docs\DESKTOP_SETUP.md
echo.
pause
goto :menu

:exit
echo.
echo Thank you for using Stock Monitor Service Manager!
exit /b 0