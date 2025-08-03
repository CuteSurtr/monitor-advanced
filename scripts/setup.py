#!/usr/bin/env python3
"""
Setup script for the 24/7 Global Stock Market Monitoring System
"""

import os
import sys
import subprocess
import platform
import shutil
from pathlib import Path
import argparse
import json

def run_command(command, check=True, shell=False):
    """Run a shell command and return the result."""
    try:
        if shell:
            result = subprocess.run(command, shell=True, check=check, capture_output=True, text=True)
        else:
            result = subprocess.run(command, check=check, capture_output=True, text=True)
        return result
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {command}")
        print(f"Error: {e}")
        if check:
            sys.exit(1)
        return e

def check_python_version():
    """Check if Python version is compatible."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("Error: Python 3.8 or higher is required")
        sys.exit(1)
    print(f"✓ Python {version.major}.{version.minor}.{version.micro} detected")

def install_system_dependencies():
    """Install system dependencies based on the platform."""
    system = platform.system().lower()
    
    if system == "linux":
        # For Raspberry Pi (Debian-based)
        packages = [
            "postgresql", "postgresql-contrib", "redis-server", "python3-pip",
            "python3-venv", "git", "curl", "wget", "build-essential"
        ]
        
        print("Installing system packages...")
        run_command(["sudo", "apt-get", "update"])
        run_command(["sudo", "apt-get", "install", "-y"] + packages)
        
    elif system == "darwin":  # macOS
        print("Installing Homebrew packages...")
        packages = ["postgresql", "redis", "python3"]
        
        for package in packages:
            run_command(["brew", "install", package])
            
    elif system == "windows":
        print("Please install the following manually:")
        print("- PostgreSQL: https://www.postgresql.org/download/windows/")
        print("- Redis: https://redis.io/download")
        print("- Python 3.8+: https://www.python.org/downloads/")

def create_virtual_environment():
    """Create a Python virtual environment."""
    venv_path = Path("venv")
    
    if venv_path.exists():
        print("Virtual environment already exists")
        return
    
    print("Creating virtual environment...")
    run_command([sys.executable, "-m", "venv", "venv"])
    
    # Activate virtual environment
    if platform.system().lower() == "windows":
        activate_script = venv_path / "Scripts" / "activate"
    else:
        activate_script = venv_path / "bin" / "activate"
    
    print(f"Virtual environment created at {venv_path}")
    print(f"To activate: source {activate_script}")

def install_python_dependencies():
    """Install Python dependencies."""
    print("Installing Python dependencies...")
    
    # Upgrade pip
    run_command([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
    
    # Install requirements
    if Path("requirements.txt").exists():
        run_command([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    else:
        print("Warning: requirements.txt not found")

def setup_database():
    """Setup PostgreSQL database."""
    print("Setting up PostgreSQL database...")
    
    # Create database and user
    commands = [
        "sudo -u postgres psql -c \"CREATE DATABASE stock_monitor;\"",
        "sudo -u postgres psql -c \"CREATE USER stock_user WITH PASSWORD 'stock_password';\"",
        "sudo -u postgres psql -c \"GRANT ALL PRIVILEGES ON DATABASE stock_monitor TO stock_user;\"",
        "sudo -u postgres psql -c \"ALTER USER stock_user CREATEDB;\""
    ]
    
    for command in commands:
        try:
            run_command(command, shell=True, check=False)
        except Exception as e:
            print(f"Warning: Database setup command failed: {e}")

def setup_redis():
    """Setup Redis server."""
    print("Setting up Redis...")
    
    # Start Redis service
    system = platform.system().lower()
    if system == "linux":
        run_command(["sudo", "systemctl", "enable", "redis-server"])
        run_command(["sudo", "systemctl", "start", "redis-server"])
    elif system == "darwin":
        run_command(["brew", "services", "start", "redis"])

def create_config_file():
    """Create configuration file from example."""
    config_path = Path("config/config.yaml")
    example_config_path = Path("config/config.example.yaml")
    
    if config_path.exists():
        print("Configuration file already exists")
        return
    
    if example_config_path.exists():
        shutil.copy(example_config_path, config_path)
        print("Configuration file created from example")
        print("Please edit config/config.yaml with your API keys and settings")
    else:
        print("Warning: config.example.yaml not found")

def create_directories():
    """Create necessary directories."""
    directories = [
        "logs",
        "data",
        "backups",
        "temp"
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"Created directory: {directory}")

def setup_prometheus():
    """Setup Prometheus monitoring."""
    print("Setting up Prometheus...")
    
    prometheus_dir = Path("prometheus")
    prometheus_dir.mkdir(exist_ok=True)
    
    # Create Prometheus configuration
    prometheus_config = {
        "global": {
            "scrape_interval": "15s",
            "evaluation_interval": "15s"
        },
        "rule_files": [],
        "scrape_configs": [
            {
                "job_name": "stock_monitor",
                "static_configs": [
                    {
                        "targets": ["localhost:8080"]
                    }
                ],
                "metrics_path": "/metrics"
            }
        ]
    }
    
    with open(prometheus_dir / "prometheus.yml", "w") as f:
        json.dump(prometheus_config, f, indent=2)
    
    print("Prometheus configuration created")

def setup_grafana():
    """Setup Grafana dashboards."""
    print("Setting up Grafana...")
    
    grafana_dir = Path("grafana")
    grafana_dir.mkdir(exist_ok=True)
    
    # Create dashboard directory
    dashboard_dir = grafana_dir / "dashboards"
    dashboard_dir.mkdir(exist_ok=True)
    
    print("Grafana directories created")

def create_service_files():
    """Create systemd service files for Linux."""
    if platform.system().lower() != "linux":
        return
    
    print("Creating systemd service files...")
    
    # Stock monitor service
    service_content = """[Unit]
Description=Stock Market Monitor
After=network.target postgresql.service redis-server.service

[Service]
Type=simple
User=pi
WorkingDirectory={}
ExecStart={}/venv/bin/python src/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
""".format(Path.cwd(), Path.cwd())
    
    with open("/tmp/stock-monitor.service", "w") as f:
        f.write(service_content)
    
    # Copy service file
    run_command(["sudo", "cp", "/tmp/stock-monitor.service", "/etc/systemd/system/"])
    run_command(["sudo", "systemctl", "daemon-reload"])
    run_command(["sudo", "systemctl", "enable", "stock-monitor"])
    
    print("Systemd service created")

def run_tests():
    """Run basic tests to verify installation."""
    print("Running basic tests...")
    
    try:
        # Test Python imports
        import fastapi
        import yfinance
        import pandas
        import numpy
        print("✓ Python dependencies imported successfully")
        
        # Test database connection (if configured)
        # This would require the config to be set up first
        
        print("✓ Basic tests passed")
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    
    return True

def main():
    """Main setup function."""
    parser = argparse.ArgumentParser(description="Setup Stock Market Monitor")
    parser.add_argument("--skip-system", action="store_true", help="Skip system dependency installation")
    parser.add_argument("--skip-db", action="store_true", help="Skip database setup")
    parser.add_argument("--skip-monitoring", action="store_true", help="Skip monitoring setup")
    parser.add_argument("--test-only", action="store_true", help="Run tests only")
    
    args = parser.parse_args()
    
    print("=== Stock Market Monitor Setup ===")
    print()
    
    if args.test_only:
        run_tests()
        return
    
    # Check Python version
    check_python_version()
    print()
    
    # Install system dependencies
    if not args.skip_system:
        install_system_dependencies()
        print()
    
    # Create virtual environment
    create_virtual_environment()
    print()
    
    # Install Python dependencies
    install_python_dependencies()
    print()
    
    # Setup database
    if not args.skip_db:
        setup_database()
        setup_redis()
        print()
    
    # Setup monitoring
    if not args.skip_monitoring:
        setup_prometheus()
        setup_grafana()
        print()
    
    # Create configuration
    create_config_file()
    print()
    
    # Create directories
    create_directories()
    print()
    
    # Create service files (Linux only)
    create_service_files()
    print()
    
    # Run tests
    if run_tests():
        print()
        print("=== Setup Complete ===")
        print()
        print("Next steps:")
        print("1. Edit config/config.yaml with your API keys")
        print("2. Initialize the database: python scripts/init_db.py")
        print("3. Start the system: python src/main.py")
        print("4. Access the dashboard at: http://localhost:8080")
        print()
        print("For more information, see the README.md file")
    else:
        print("Setup completed with warnings. Please check the output above.")

if __name__ == "__main__":
    main() 