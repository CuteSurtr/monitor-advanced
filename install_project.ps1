#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Install Stock Market Monitor in development mode
    
.DESCRIPTION
    This script installs the Stock Market Monitor project in development mode
    so that tests can run properly and the project can be imported.
    
.EXAMPLE
    .\install_project.ps1
    
.NOTES
    Requires Python 3.8+ and pip to be installed
#>

Write-Host "Installing Stock Market Monitor in development mode..." -ForegroundColor Green
Write-Host ""

# Check if Python is available
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Found Python: $pythonVersion" -ForegroundColor Yellow
} catch {
    Write-Host "Error: Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python 3.8+ and try again" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if pip is available
try {
    $pipVersion = pip --version 2>&1
    Write-Host "Found pip: $pipVersion" -ForegroundColor Yellow
} catch {
    Write-Host "Error: pip is not available" -ForegroundColor Red
    Write-Host "Please ensure pip is installed with Python" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "Installing project in development mode..." -ForegroundColor Yellow

# Install the project
try {
    pip install -e .
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "Project installed successfully!" -ForegroundColor Green
        Write-Host ""
        Write-Host "You can now run tests with:" -ForegroundColor Cyan
        Write-Host "  pytest -q" -ForegroundColor White
        Write-Host ""
        Write-Host "Or run the application with:" -ForegroundColor Cyan
        Write-Host "  python -m src.main" -ForegroundColor White
        Write-Host ""
        Write-Host "Or test the setup with:" -ForegroundColor Cyan
        Write-Host "  python test_setup.py" -ForegroundColor White
        Write-Host ""
    } else {
        throw "pip install failed with exit code $LASTEXITCODE"
    }
} catch {
    Write-Host ""
    Write-Host "Error: Failed to install project" -ForegroundColor Red
    Write-Host "Please check the error messages above" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "Press Enter to exit..."
Read-Host
