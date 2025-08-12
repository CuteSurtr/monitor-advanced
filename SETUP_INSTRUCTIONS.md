# Stock Market Monitor - Setup Instructions

This document provides step-by-step instructions to set up the Stock Market Monitor project for development and testing.

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- Git (for cloning the repository)

## Quick Setup (Windows)

### Option 1: Using the Batch File (Recommended)
1. Double-click `install_project.bat`
2. Follow the prompts
3. The script will automatically install the project in development mode

### Option 2: Using PowerShell
1. Right-click `install_project.ps1` and select "Run with PowerShell"
2. Follow the prompts
3. The script will automatically install the project in development mode

### Option 3: Manual Installation
1. Open Command Prompt or PowerShell
2. Navigate to the project directory
3. Run: `pip install -e .`

## Quick Setup (Linux/macOS)

1. Open Terminal
2. Navigate to the project directory
3. Run: `pip install -e .`

## What the Installation Does

The `pip install -e .` command:
- Installs the project in "editable" mode
- Adds the `src` directory to Python's module search path
- Makes all modules importable from anywhere
- Allows tests to run without `ModuleNotFoundError: No module named 'src'`

## Verifying the Installation

After installation, you can verify everything works:

```bash
# Test the setup
python test_setup.py

# Run tests
pytest -q

# Run the application
python -m src.main
```

## Alternative: Using PYTHONPATH

If you prefer not to install the project, you can set the PYTHONPATH environment variable:

### Windows (Command Prompt)
```cmd
set PYTHONPATH=src
pytest -q
```

### Windows (PowerShell)
```powershell
$env:PYTHONPATH="src"
pytest -q
```

### Linux/macOS
```bash
export PYTHONPATH=src
pytest -q
```

## Project Structure

```
monitor advanced/
├── src/                    # Source code
│   ├── __init__.py        # Package initialization
│   ├── main.py            # Main application entry point
│   ├── celery_app.py      # Celery configuration
│   ├── utils/             # Utility modules
│   ├── alerts/            # Alert system
│   ├── analytics/         # Analytics engine
│   ├── collectors/        # Data collectors
│   ├── dashboard/         # Web dashboard
│   ├── monitoring/        # System monitoring
│   ├── portfolio/         # Portfolio management
│   └── tasks/             # Background tasks
├── tests/                 # Test files
├── config/                # Configuration files
├── setup.py               # Python package setup
├── pyproject.toml         # Modern Python packaging
├── requirements.txt       # Python dependencies
└── README.md              # Project documentation
```

## Configuration

The project uses `config/config.desktop.yaml` for desktop environments. Key settings:

- **Database**: Uses service names (`postgres`, `redis`) for Docker environments
- **Celery**: Configured to use Redis as broker and result backend
- **API Keys**: Set your actual API keys in the configuration file

## Running Tests

Once installed, you can run tests with:

```bash
# Run all tests
pytest

# Run tests quietly
pytest -q

# Run specific test file
pytest tests/test_alert_manager.py

# Run with coverage
pytest --cov=src

# Run specific test
pytest tests/test_alert_manager.py::TestAlertManager::test_alert_manager_initialization
```

## Troubleshooting

### ModuleNotFoundError: No module named 'src'
**Solution**: Install the project in development mode:
```bash
pip install -e .
```

### Import errors in tests
**Solution**: Ensure the project is installed or PYTHONPATH is set:
```bash
# Option 1: Install project
pip install -e .

# Option 2: Set PYTHONPATH
export PYTHONPATH=src  # Linux/macOS
set PYTHONPATH=src     # Windows
```

### Configuration not loading
**Solution**: Check that `config/config.desktop.yaml` exists and is readable

### Celery connection errors
**Solution**: Ensure Redis is running and accessible at the configured host/port

## Development Workflow

1. **Install the project**: `pip install -e .`
2. **Make changes** to source code
3. **Run tests**: `pytest -q`
4. **Repeat** as needed

The editable installation means you don't need to reinstall after making changes - they're immediately available.

## Support

If you encounter issues:
1. Check this document first
2. Run `python test_setup.py` to diagnose problems
3. Check the error messages for specific issues
4. Ensure all prerequisites are met
