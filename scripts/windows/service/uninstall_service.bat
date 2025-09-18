@echo off
REM Stock Monitor Windows Service Uninstaller
REM This script removes the Stock Monitor Windows service

setlocal enabledelayedexpansion

echo ================================================================
echo   Stock Monitor - Windows Service Uninstaller
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

set SCRIPT_DIR=%~dp0
set SERVICE_NAME=StockMonitor

echo Service Name: %SERVICE_NAME%
echo.

REM Check if NSSM exists
if not exist "%SCRIPT_DIR%nssm.exe" (
    echo ERROR: NSSM not found at: %SCRIPT_DIR%nssm.exe
    echo.
    echo The service may have been installed with NSSM, but NSSM is missing.
    echo Please download NSSM from: https://nssm.cc/download
    echo.
    echo Alternatively, try to remove the service manually:
    echo sc delete %SERVICE_NAME%
    echo.
    pause
    exit /b 1
)

REM Check if service exists
sc query "%SERVICE_NAME%" >nul 2>&1
if %errorLevel% neq 0 (
    echo Service '%SERVICE_NAME%' is not installed.
    echo Nothing to uninstall.
    pause
    exit /b 0
)

echo ✓ Service found
echo.

REM Stop the service if running
echo Stopping service...
"%SCRIPT_DIR%nssm.exe" stop "%SERVICE_NAME%" >nul 2>&1
if %errorLevel% equ 0 (
    echo ✓ Service stopped
) else (
    echo ⚠ Service was not running or failed to stop
)

REM Wait a moment for service to fully stop
timeout /t 3 /nobreak >nul

echo.

REM Remove the service
echo Removing service...
"%SCRIPT_DIR%nssm.exe" remove "%SERVICE_NAME%" confirm

if %errorLevel% equ 0 (
    echo ✓ Service removed successfully
) else (
    echo ERROR: Failed to remove service
    echo.
    echo Try manual removal:
    echo sc delete %SERVICE_NAME%
    pause
    exit /b 1
)

echo.

REM Clean up any remaining registry entries (optional)
echo Cleaning up registry entries...
reg delete "HKLM\SYSTEM\CurrentControlSet\Services\%SERVICE_NAME%" /f >nul 2>&1
if %errorLevel% equ 0 (
    echo ✓ Registry entries cleaned
) else (
    echo ⚠ No additional registry entries found
)

echo.

REM Check if service is completely removed
sc query "%SERVICE_NAME%" >nul 2>&1
if %errorLevel% neq 0 (
    echo ✓ Service completely removed
else
    echo ⚠ Service may still exist in registry
    echo Try rebooting the system
)

echo.
echo ================================================================
echo   SERVICE UNINSTALLATION COMPLETED
echo ================================================================
echo.
echo The Stock Monitor service has been removed from your system.
echo.
echo The application files and configuration remain intact.
echo You can still run the application manually or reinstall the service.
echo.
echo To run manually:
echo   1. Open Command Prompt in the application directory
echo   2. Run: venv\Scripts\activate.bat
echo   3. Run: python src\main.py
echo.
echo To reinstall the service:
echo   Run: scripts\windows\service\install_service.bat
echo.
pause