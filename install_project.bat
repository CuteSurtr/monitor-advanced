@echo off
echo Installing Stock Market Monitor in development mode...
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.8+ and try again
    pause
    exit /b 1
)

REM Check if pip is available
pip --version >nul 2>&1
if errorlevel 1 (
    echo Error: pip is not available
    echo Please ensure pip is installed with Python
    pause
    exit /b 1
)

echo Installing project in development mode...
pip install -e .

if errorlevel 1 (
    echo.
    echo Error: Failed to install project
    echo Please check the error messages above
    pause
    exit /b 1
)

echo.
echo Project installed successfully!
echo.
echo You can now run tests with:
echo   pytest -q
echo.
echo Or run the application with:
echo   python -m src.main
echo.
echo Press any key to exit...
pause >nul
