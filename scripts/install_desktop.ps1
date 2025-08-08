# 24/7 Global Stock Market Monitor - PowerShell Desktop Installer
# This script sets up the monitoring system on Windows using PowerShell

param(
    [switch]$SkipSystem,
    [switch]$SkipDocker,
    [switch]$DockerOnly,
    [switch]$Force
)

# Ensure we can run scripts
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force

Write-Host "================================================================" -ForegroundColor Blue
Write-Host "  24/7 Global Stock Market Monitor - Windows Desktop Setup" -ForegroundColor Blue
Write-Host "================================================================" -ForegroundColor Blue
Write-Host ""

# Helper functions
function Write-Step {
    param($StepNumber, $Message)
    Write-Host "[$StepNumber] $Message" -ForegroundColor Cyan
}

function Write-Success {
    param($Message)
    Write-Host "✓ $Message" -ForegroundColor Green
}

function Write-Warning {
    param($Message)
    Write-Host "⚠ $Message" -ForegroundColor Yellow
}

function Write-Error {
    param($Message)
    Write-Host "✗ $Message" -ForegroundColor Red
}

function Test-Administrator {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Install-Chocolatey {
    if (Get-Command choco -ErrorAction SilentlyContinue) {
        Write-Success "Chocolatey already installed"
        return $true
    }
    
    Write-Host "Installing Chocolatey package manager..."
    try {
        Set-ExecutionPolicy Bypass -Scope Process -Force
        [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
        Invoke-Expression ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
        
        # Refresh environment variables
        $env:PATH = [System.Environment]::GetEnvironmentVariable("PATH","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("PATH","User")
        
        if (Get-Command choco -ErrorAction SilentlyContinue) {
            Write-Success "Chocolatey installed successfully"
            return $true
        } else {
            Write-Error "Chocolatey installation failed"
            return $false
        }
    } catch {
        Write-Error "Failed to install Chocolatey: $($_.Exception.Message)"
        return $false
    }
}

function Install-Package {
    param($PackageName, $DisplayName = $PackageName, $Params = "")
    
    Write-Host "Installing $DisplayName..."
    try {
        if ($Params) {
            $result = choco install $PackageName -y --params="$Params" 2>&1
        } else {
            $result = choco install $PackageName -y 2>&1
        }
        
        if ($LASTEXITCODE -eq 0) {
            Write-Success "$DisplayName installed successfully"
            return $true
        } else {
            Write-Warning "$DisplayName installation completed with warnings"
            return $true
        }
    } catch {
        Write-Error "Failed to install $DisplayName"
        return $false
    }
}

# Get installation directory
$InstallDir = Split-Path -Parent $PSScriptRoot
Set-Location $InstallDir

Write-Host "Installation Directory: $InstallDir"
Write-Host ""

# Check if running as administrator
if (-not $Force -and (Test-Administrator)) {
    Write-Warning "Running as Administrator is not recommended for this script"
    $response = Read-Host "Continue anyway? (y/N)"
    if ($response -ne "y" -and $response -ne "Y") {
        exit 1
    }
}

# Check Python installation
Write-Step "1/8" "Checking Python installation..."
try {
    $pythonVersion = python --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Python detected: $pythonVersion"
        
        # Check if version is 3.8+
        $versionCheck = python -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)" 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Python version is compatible"
        } else {
            Write-Error "Python 3.8+ required. Please install from: https://www.python.org/downloads/"
            exit 1
        }
    } else {
        throw "Python not found"
    }
} catch {
    Write-Error "Python not found. Please install Python 3.8+ from: https://www.python.org/downloads/"
    exit 1
}
Write-Host ""

# Install system dependencies
if (-not $SkipSystem) {
    Write-Step "2/8" "Installing system dependencies..."
    
    # Install Chocolatey if needed
    $chocoInstalled = Install-Chocolatey
    
    if ($chocoInstalled) {
        # Install packages
        Install-Package "postgresql13" "PostgreSQL" "/Password:postgres"
        Install-Package "redis-64" "Redis"
        Install-Package "git" "Git"
        Install-Package "nodejs" "Node.js"
        Install-Package "python3" "Python 3"
        
        Write-Success "System dependencies installation completed"
    } else {
        Write-Warning "Chocolatey installation failed. Please install dependencies manually:"
        Write-Host "1. PostgreSQL: https://www.postgresql.org/download/windows/" -ForegroundColor Yellow
        Write-Host "2. Redis: https://github.com/microsoftarchive/redis/releases" -ForegroundColor Yellow
        Write-Host "3. Git: https://git-scm.com/download/win" -ForegroundColor Yellow
        Write-Host "4. Node.js: https://nodejs.org/en/download/" -ForegroundColor Yellow
    }
} else {
    Write-Warning "Skipping system dependency installation"
}
Write-Host ""

# Check Docker
Write-Step "3/8" "Checking Docker..."
try {
    $dockerVersion = docker --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Docker detected: $dockerVersion"
        
        # Check if Docker is running
        try {
            docker ps | Out-Null
            Write-Success "Docker is running"
            $dockerRunning = $true
        } catch {
            Write-Warning "Docker is installed but not running. Please start Docker Desktop."
            $dockerRunning = $false
        }
    } else {
        throw "Docker not found"
    }
} catch {
    if (-not $SkipDocker) {
        Write-Warning "Docker not found. Installing Docker Desktop..."
        if (Install-Package "docker-desktop" "Docker Desktop") {
            Write-Host "Docker Desktop installed. Please restart your computer and run this script again." -ForegroundColor Yellow
            Read-Host "Press Enter to exit"
            exit 0
        }
    } else {
        Write-Warning "Docker not found and installation skipped"
    }
    $dockerRunning = $false
}
Write-Host ""

# If Docker-only mode and Docker is available, use Docker setup
if ($DockerOnly -and $dockerRunning) {
    Write-Host "Using Docker-only setup..." -ForegroundColor Green
    Write-Host "Run the following command to start:" -ForegroundColor Yellow
    Write-Host "docker-compose -f docker-compose.desktop.yml up -d" -ForegroundColor Cyan
    exit 0
}

# Create virtual environment
Write-Step "4/8" "Setting up Python environment..."
if (Test-Path "venv") {
    Write-Success "Virtual environment already exists"
} else {
    Write-Host "Creating virtual environment..."
    python -m venv venv
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Virtual environment created"
    } else {
        Write-Error "Failed to create virtual environment"
        exit 1
    }
}

# Activate virtual environment and install dependencies
Write-Host "Installing Python dependencies..."
& "venv\Scripts\Activate.ps1"
python -m pip install --upgrade pip

if (Test-Path "requirements.txt") {
    pip install -r requirements.txt
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Core Python dependencies installed"
    } else {
        Write-Error "Failed to install Python dependencies"
        exit 1
    }
} else {
    Write-Warning "requirements.txt not found"
}

# Install desktop-specific requirements
if (Test-Path "requirements.desktop.txt") {
    pip install -r requirements.desktop.txt
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Desktop-specific packages installed"
    } else {
        Write-Warning "Some desktop-specific packages failed to install"
    }
}
Write-Host ""

# Setup database
Write-Step "5/8" "Setting up database..."

# Start PostgreSQL service
Write-Host "Starting PostgreSQL service..."
try {
    Start-Service postgresql-x64-13 -ErrorAction SilentlyContinue
    Write-Success "PostgreSQL service started"
} catch {
    Write-Warning "Failed to start PostgreSQL service"
}

# Wait for PostgreSQL to start
Start-Sleep -Seconds 5

# Create database and user
Write-Host "Creating database and user..."
$env:PGPASSWORD = "postgres"
try {
    & createdb -U postgres stock_monitor 2>$null
    & psql -U postgres -c "CREATE USER stock_user WITH PASSWORD 'stock_password';" 2>$null
    & psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE stock_monitor TO stock_user;" 2>$null
    & psql -U postgres -c "ALTER USER stock_user CREATEDB;" 2>$null
    Write-Success "Database setup completed"
} catch {
    Write-Warning "Database setup completed with warnings"
}

# Start Redis service
Write-Host "Starting Redis service..."
try {
    Start-Service Redis -ErrorAction SilentlyContinue
    Write-Success "Redis service started"
} catch {
    Write-Warning "Failed to start Redis service"
}
Write-Host ""

# Create configuration
Write-Step "6/8" "Creating configuration..."
if (-not (Test-Path "config\config.yaml")) {
    if (Test-Path "config\config.example.yaml") {
        Copy-Item "config\config.example.yaml" "config\config.yaml"
        Write-Success "Configuration file created from example"
    } else {
        Write-Warning "config.example.yaml not found"
    }
} else {
    Write-Success "Configuration file already exists"
}

# Run desktop setup script
try {
    python scripts\setup_desktop.py --skip-system --skip-db 2>$null
} catch {
    # Ignore errors from setup script
}
Write-Host ""

# Create shortcuts and launchers
Write-Step "7/8" "Creating desktop shortcuts..."

# Create Windows scripts directory
New-Item -ItemType Directory -Force -Path "scripts\windows" | Out-Null

# Create start script
@"
@echo off
cd /d "%~dp0..\.."
call venv\Scripts\activate.bat
python src\main.py
pause
"@ | Out-File -FilePath "scripts\windows\start_monitor.bat" -Encoding ASCII

# Create dashboard launcher
@"
@echo off
start http://localhost:8080
"@ | Out-File -FilePath "scripts\windows\open_dashboard.bat" -Encoding ASCII

# Create Grafana launcher
@"
@echo off
start http://localhost:3000
"@ | Out-File -FilePath "scripts\windows\open_grafana.bat" -Encoding ASCII

# Create Docker launcher
@"
@echo off
cd /d "%~dp0..\.."
docker-compose -f docker-compose.desktop.yml up -d
echo Docker services started
echo Dashboard: http://localhost:8080
echo Grafana: http://localhost:3000
pause
"@ | Out-File -FilePath "scripts\windows\start_docker.bat" -Encoding ASCII

# Create desktop shortcuts
$WshShell = New-Object -comObject WScript.Shell
$Desktop = [System.IO.Path]::Combine([System.Environment]::GetFolderPath("Desktop"))

# Create shortcut to start monitor
$Shortcut = $WshShell.CreateShortcut("$Desktop\Stock Monitor.lnk")
$Shortcut.TargetPath = "$InstallDir\scripts\windows\start_monitor.bat"
$Shortcut.WorkingDirectory = $InstallDir
$Shortcut.Save()

# Create shortcut to dashboard
$Shortcut = $WshShell.CreateShortcut("$Desktop\Stock Dashboard.lnk")
$Shortcut.TargetPath = "$InstallDir\scripts\windows\open_dashboard.bat"
$Shortcut.WorkingDirectory = $InstallDir
$Shortcut.Save()

Write-Success "Desktop shortcuts created"
Write-Host ""

# Performance optimization
Write-Step "8/8" "Applying performance optimizations..."

# Create performance tuning script
@"
import psutil
import os

def get_optimal_settings():
    cpu_count = psutil.cpu_count(logical=True)
    memory_gb = psutil.virtual_memory().total / (1024**3)
    
    print(f"System Resources:")
    print(f"  CPU cores: {cpu_count}")
    print(f"  RAM: {memory_gb:.1f} GB")
    print(f"  Recommended workers: {min(int(cpu_count * 0.8), int(memory_gb / 2))}")

if __name__ == "__main__":
    get_optimal_settings()
"@ | Out-File -FilePath "scripts\check_performance.py" -Encoding UTF8

try {
    python scripts\check_performance.py
} catch {
    Write-Warning "Performance check failed"
}

Write-Success "Performance optimization completed"
Write-Host ""

Write-Host ""
Write-Host "================================================================" -ForegroundColor Green
Write-Host "  INSTALLATION COMPLETED SUCCESSFULLY!" -ForegroundColor Green
Write-Host "================================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. Edit configuration file with your API keys:" -ForegroundColor White
Write-Host "   config\config.yaml" -ForegroundColor Cyan
Write-Host ""
Write-Host "2. Start the monitoring system:" -ForegroundColor White
Write-Host "   - Double-click 'Stock Monitor' on your desktop" -ForegroundColor Cyan
Write-Host "   - Or run: scripts\windows\start_monitor.bat" -ForegroundColor Cyan
Write-Host ""
Write-Host "3. Alternative - Use Docker (recommended):" -ForegroundColor White
Write-Host "   - Run: scripts\windows\start_docker.bat" -ForegroundColor Cyan
Write-Host "   - Or: docker-compose -f docker-compose.desktop.yml up -d" -ForegroundColor Cyan
Write-Host ""
Write-Host "4. Access the applications:" -ForegroundColor White
Write-Host "   - Main Dashboard: http://localhost:8080" -ForegroundColor Cyan
Write-Host "   - Grafana Dashboard: http://localhost:3000" -ForegroundColor Cyan
Write-Host "   - Prometheus: http://localhost:9090" -ForegroundColor Cyan
Write-Host ""
Write-Host "5. For help and documentation:" -ForegroundColor White
Write-Host "   - See README.md and docs\ folder" -ForegroundColor Cyan
Write-Host "   - Desktop-specific guide: docs\DESKTOP_SETUP.md" -ForegroundColor Cyan
Write-Host ""
Write-Host "Enjoy monitoring the global stock markets 24/7!" -ForegroundColor Green
Write-Host ""

Read-Host "Press Enter to exit"