@echo off
REM 24/7 Global Stock Market Monitor - Windows Desktop Installer
REM This script sets up the monitoring system on Windows desktop environments

setlocal enabledelayedexpansion

echo ================================================================
echo   24/7 Global Stock Market Monitor - Windows Desktop Setup
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

REM Set installation directory
set INSTALL_DIR=%~dp0..
cd /d "%INSTALL_DIR%"

echo Installation Directory: %INSTALL_DIR%
echo.

REM Check Python installation
echo [1/8] Checking Python installation...
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: Python not found. Please install Python 3.8+ from:
    echo https://www.python.org/downloads/
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version') do set PYTHON_VERSION=%%i
echo ✓ Python %PYTHON_VERSION% detected
echo.

REM Check for Chocolatey
echo [2/8] Checking package manager...
choco --version >nul 2>&1
if %errorLevel% neq 0 (
    echo Installing Chocolatey package manager...
    powershell -Command "Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))"
    if !errorLevel! neq 0 (
        echo WARNING: Failed to install Chocolatey. You'll need to install dependencies manually.
        goto :manual_install
    )
    echo ✓ Chocolatey installed successfully
) else (
    echo ✓ Chocolatey detected
)
echo.

REM Install system dependencies
echo [3/8] Installing system dependencies...
echo Installing PostgreSQL...
choco install postgresql13 -y --params="/Password:postgres"
if !errorLevel! neq 0 (
    echo WARNING: PostgreSQL installation failed
)

echo Installing Redis...
choco install redis-64 -y
if !errorLevel! neq 0 (
    echo WARNING: Redis installation failed
)

echo Installing Git...
choco install git -y
if !errorLevel! neq 0 (
    echo WARNING: Git installation failed
)

echo Installing Node.js...
choco install nodejs -y
if !errorLevel! neq 0 (
    echo WARNING: Node.js installation failed
)

echo.

REM Check Docker
echo [4/8] Checking Docker...
docker --version >nul 2>&1
if %errorLevel% neq 0 (
    echo Docker not found. Installing Docker Desktop...
    choco install docker-desktop -y
    if !errorLevel! neq 0 (
        echo WARNING: Docker Desktop installation failed
        echo Please install manually from: https://www.docker.com/products/docker-desktop
    ) else (
        echo ✓ Docker Desktop installed. Please restart your computer and run this script again.
        pause
        exit /b 0
    )
) else (
    echo ✓ Docker detected
)
echo.

REM Create virtual environment
echo [5/8] Setting up Python environment...
if exist venv (
    echo Virtual environment already exists
) else (
    echo Creating virtual environment...
    python -m venv venv
    if !errorLevel! neq 0 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
    echo ✓ Virtual environment created
)

REM Activate virtual environment and install dependencies
echo Installing Python dependencies...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
if !errorLevel! neq 0 (
    echo ERROR: Failed to install Python dependencies
    pause
    exit /b 1
)

REM Install desktop-specific requirements
if exist requirements.desktop.txt (
    pip install -r requirements.desktop.txt
    if !errorLevel! neq 0 (
        echo WARNING: Failed to install some desktop-specific packages
    )
)
echo ✓ Python dependencies installed
echo.

REM Setup database
echo [6/8] Setting up database...
echo Starting PostgreSQL service...
sc start postgresql-x64-13 >nul 2>&1

REM Wait for PostgreSQL to start
timeout /t 5 /nobreak >nul

REM Create database and user
echo Creating database and user...
set PGPASSWORD=postgres
createdb -U postgres stock_monitor 2>nul
psql -U postgres -c "CREATE USER stock_user WITH PASSWORD 'stock_password';" 2>nul
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE stock_monitor TO stock_user;" 2>nul
psql -U postgres -c "ALTER USER stock_user CREATEDB;" 2>nul

echo Starting Redis service...
sc start Redis >nul 2>&1

echo ✓ Database setup completed
echo.

REM Create configuration
echo [7/8] Creating configuration...
if not exist config\config.yaml (
    if exist config\config.example.yaml (
        copy config\config.example.yaml config\config.yaml >nul
        echo ✓ Configuration file created from example
    ) else (
        echo WARNING: config.example.yaml not found
    )
) else (
    echo Configuration file already exists
)

REM Create desktop-specific configuration
python scripts\setup_desktop.py --skip-system --skip-db >nul 2>&1

echo.

REM Create shortcuts and launchers
echo [8/8] Creating desktop shortcuts...

REM Create shortcuts directory
if not exist scripts\windows mkdir scripts\windows

REM Create start script
echo @echo off > scripts\windows\start_monitor.bat
echo cd /d "%%~dp0..\.." >> scripts\windows\start_monitor.bat
echo call venv\Scripts\activate.bat >> scripts\windows\start_monitor.bat
echo python src\main.py >> scripts\windows\start_monitor.bat
echo pause >> scripts\windows\start_monitor.bat

REM Create dashboard launcher
echo @echo off > scripts\windows\open_dashboard.bat
echo start http://localhost:8080 >> scripts\windows\open_dashboard.bat

REM Create Grafana launcher
echo @echo off > scripts\windows\open_grafana.bat
echo start http://localhost:3000 >> scripts\windows\open_grafana.bat

REM Create Docker launcher
echo @echo off > scripts\windows\start_docker.bat
echo cd /d "%%~dp0..\.." >> scripts\windows\start_docker.bat
echo docker-compose -f docker-compose.desktop.yml up -d >> scripts\windows\start_docker.bat
echo echo Docker services started >> scripts\windows\start_docker.bat
echo echo Dashboard: http://localhost:8080 >> scripts\windows\start_docker.bat
echo echo Grafana: http://localhost:3000 >> scripts\windows\start_docker.bat
echo pause >> scripts\windows\start_docker.bat

REM Create desktop shortcuts on user's desktop
set DESKTOP=%USERPROFILE%\Desktop

REM Create shortcut to start monitor
powershell -Command "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%DESKTOP%\Stock Monitor.lnk'); $Shortcut.TargetPath = '%INSTALL_DIR%\scripts\windows\start_monitor.bat'; $Shortcut.WorkingDirectory = '%INSTALL_DIR%'; $Shortcut.Save()"

REM Create shortcut to dashboard
powershell -Command "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%DESKTOP%\Stock Dashboard.lnk'); $Shortcut.TargetPath = '%INSTALL_DIR%\scripts\windows\open_dashboard.bat'; $Shortcut.WorkingDirectory = '%INSTALL_DIR%'; $Shortcut.Save()"

echo ✓ Desktop shortcuts created
echo.

goto :success

:manual_install
echo.
echo ================================================================
echo   MANUAL INSTALLATION REQUIRED
echo ================================================================
echo.
echo Please install the following software manually:
echo.
echo 1. PostgreSQL 13+: https://www.postgresql.org/download/windows/
echo 2. Redis: https://github.com/microsoftarchive/redis/releases
echo 3. Docker Desktop: https://www.docker.com/products/docker-desktop
echo 4. Git: https://git-scm.com/download/win
echo.
echo After installing the above, run this script again.
pause
exit /b 1

:success
echo.
echo ================================================================
echo   INSTALLATION COMPLETED SUCCESSFULLY!
echo ================================================================
echo.
echo Next Steps:
echo.
echo 1. Edit configuration file with your API keys:
echo    config\config.yaml
echo.
echo 2. Start the monitoring system:
echo    - Double-click "Stock Monitor" on your desktop
echo    - Or run: scripts\windows\start_monitor.bat
echo.
echo 3. Alternative - Use Docker (recommended):
echo    - Run: scripts\windows\start_docker.bat
echo.
echo 4. Access the applications:
echo    - Main Dashboard: http://localhost:8080
echo    - Grafana Dashboard: http://localhost:3000
echo    - Prometheus: http://localhost:9090
echo.
echo 5. For help and documentation:
echo    - See README.md and docs\ folder
echo    - Desktop-specific guide: docs\DESKTOP_SETUP.md
echo.
echo Enjoy monitoring the global stock markets 24/7!
echo.
pause