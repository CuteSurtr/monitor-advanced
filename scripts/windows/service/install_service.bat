@echo off
REM Stock Monitor Windows Service Installer
REM This script installs the Stock Monitor as a Windows service using NSSM

setlocal enabledelayedexpansion

echo ================================================================
echo   Stock Monitor - Windows Service Installation
echo ================================================================
echo.

REM Check if running as administrator
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: This script must be run as Administrator
    echo Right-click and select "Run as administrator"
    pause
    exit /b 1
)

REM Set paths
set SCRIPT_DIR=%~dp0
set INSTALL_DIR=%SCRIPT_DIR%..\..\..
set SERVICE_NAME=StockMonitor
set SERVICE_DISPLAY_NAME=24/7 Stock Market Monitor
set SERVICE_DESCRIPTION=24/7 Global Stock Market Monitoring System for Desktop

cd /d "%INSTALL_DIR%"

echo Installation Directory: %INSTALL_DIR%
echo Service Name: %SERVICE_NAME%
echo.

REM Check if NSSM exists
if not exist "%SCRIPT_DIR%nssm.exe" (
    echo NSSM (Non-Sucking Service Manager) not found.
    echo.
    echo Please download NSSM from: https://nssm.cc/download
    echo Extract nssm.exe to: %SCRIPT_DIR%
    echo.
    echo Steps:
    echo 1. Download NSSM from https://nssm.cc/download
    echo 2. Extract the appropriate version (win32 or win64^)
    echo 3. Copy nssm.exe to: %SCRIPT_DIR%
    echo 4. Run this script again
    echo.
    pause
    exit /b 1
)

echo ✓ NSSM found
echo.

REM Check if Python virtual environment exists
if not exist "venv\Scripts\python.exe" (
    echo ERROR: Python virtual environment not found
    echo Please run the main installation script first:
    echo scripts\install_windows.bat
    pause
    exit /b 1
)

echo ✓ Python virtual environment found
echo.

REM Check if service already exists
sc query "%SERVICE_NAME%" >nul 2>&1
if %errorLevel% equ 0 (
    echo Service already exists. Removing existing service...
    "%SCRIPT_DIR%nssm.exe" stop "%SERVICE_NAME%" >nul 2>&1
    "%SCRIPT_DIR%nssm.exe" remove "%SERVICE_NAME%" confirm >nul 2>&1
    echo ✓ Existing service removed
    echo.
)

REM Install service
echo Installing service...
"%SCRIPT_DIR%nssm.exe" install "%SERVICE_NAME%" "%INSTALL_DIR%\venv\Scripts\python.exe" "%INSTALL_DIR%\src\main.py"

if %errorLevel% neq 0 (
    echo ERROR: Failed to install service
    pause
    exit /b 1
)

echo ✓ Service installed
echo.

REM Configure service
echo Configuring service parameters...

REM Set working directory
"%SCRIPT_DIR%nssm.exe" set "%SERVICE_NAME%" AppDirectory "%INSTALL_DIR%"

REM Set display name and description
"%SCRIPT_DIR%nssm.exe" set "%SERVICE_NAME%" DisplayName "%SERVICE_DISPLAY_NAME%"
"%SCRIPT_DIR%nssm.exe" set "%SERVICE_NAME%" Description "%SERVICE_DESCRIPTION%"

REM Set startup type to automatic
"%SCRIPT_DIR%nssm.exe" set "%SERVICE_NAME%" Start SERVICE_AUTO_START

REM Set environment variables
"%SCRIPT_DIR%nssm.exe" set "%SERVICE_NAME%" AppEnvironmentExtra "PYTHONPATH=%INSTALL_DIR%" "CONFIG_PATH=%INSTALL_DIR%\config\config.yaml"

REM Set log files
"%SCRIPT_DIR%nssm.exe" set "%SERVICE_NAME%" AppStdout "%INSTALL_DIR%\logs\service_stdout.log"
"%SCRIPT_DIR%nssm.exe" set "%SERVICE_NAME%" AppStderr "%INSTALL_DIR%\logs\service_stderr.log"

REM Set log rotation
"%SCRIPT_DIR%nssm.exe" set "%SERVICE_NAME%" AppStdoutCreationDisposition 4
"%SCRIPT_DIR%nssm.exe" set "%SERVICE_NAME%" AppStderrCreationDisposition 4

REM Set restart behavior
"%SCRIPT_DIR%nssm.exe" set "%SERVICE_NAME%" AppRestartDelay 30000
"%SCRIPT_DIR%nssm.exe" set "%SERVICE_NAME%" AppThrottle 10000

REM Set failure actions
"%SCRIPT_DIR%nssm.exe" set "%SERVICE_NAME%" AppExit Default Restart
"%SCRIPT_DIR%nssm.exe" set "%SERVICE_NAME%" AppExit 0 Exit

echo ✓ Service configured
echo.

REM Create log directory if it doesn't exist
if not exist "logs" mkdir logs

REM Test configuration
echo Testing service configuration...
"%SCRIPT_DIR%nssm.exe" status "%SERVICE_NAME%" >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: Service configuration test failed
    pause
    exit /b 1
)

echo ✓ Service configuration valid
echo.

echo ================================================================
echo   SERVICE INSTALLATION COMPLETED SUCCESSFULLY!
echo ================================================================
echo.
echo Service Name: %SERVICE_NAME%
echo Display Name: %SERVICE_DISPLAY_NAME%
echo.
echo Management Commands:
echo   Start Service:    net start %SERVICE_NAME%
echo   Stop Service:     net stop %SERVICE_NAME%
echo   Restart Service:  net stop %SERVICE_NAME% ^&^& net start %SERVICE_NAME%
echo   Uninstall:        scripts\windows\service\uninstall_service.bat
echo.
echo Alternative Commands:
echo   Start:            sc start %SERVICE_NAME%
echo   Stop:             sc stop %SERVICE_NAME%
echo   Status:           sc query %SERVICE_NAME%
echo.
echo Log Files:
echo   Standard Output:  logs\service_stdout.log
echo   Standard Error:   logs\service_stderr.log
echo   Application Log:  logs\stock_monitor.log
echo.
echo Configuration:
echo   Config File:      config\config.yaml
echo   Service Manager:  services.msc
echo.
echo Next Steps:
echo 1. Edit config\config.yaml with your API keys
echo 2. Start the service: net start %SERVICE_NAME%
echo 3. Check logs for any issues
echo 4. Access dashboard at: http://localhost:8080
echo.
echo The service is configured to start automatically on system boot.
echo.
pause