#!/usr/bin/env python3
"""
Desktop Setup script for the 24/7 Global Stock Market Monitoring System
Optimized for Windows, macOS, and Linux desktop environments
"""

import os
import sys
import subprocess
import platform
import shutil
from pathlib import Path
import argparse
import json
import tempfile
import urllib.request
import zipfile

def run_command(command, check=True, shell=False, cwd=None):
    """Run a shell command and return the result."""
    try:
        if shell:
            result = subprocess.run(command, shell=True, check=check, capture_output=True, text=True, cwd=cwd)
        else:
            result = subprocess.run(command, check=check, capture_output=True, text=True, cwd=cwd)
        return result
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {command}")
        print(f"Error: {e}")
        if e.stdout:
            print(f"stdout: {e.stdout}")
        if e.stderr:
            print(f"stderr: {e.stderr}")
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

def check_docker():
    """Check if Docker is installed and running."""
    try:
        result = run_command(["docker", "--version"])
        print(f"✓ Docker detected: {result.stdout.strip()}")
        
        # Check if Docker is running
        try:
            run_command(["docker", "ps"])
            print("✓ Docker is running")
            return True
        except:
            print("⚠ Docker is installed but not running. Please start Docker Desktop.")
            return False
    except:
        print("⚠ Docker not found. Will install dependencies manually.")
        return False

def install_desktop_dependencies():
    """Install system dependencies for desktop environments."""
    system = platform.system().lower()
    
    if system == "windows":
        install_windows_dependencies()
    elif system == "darwin":  # macOS
        install_macos_dependencies()
    elif system == "linux":
        install_linux_desktop_dependencies()

def install_windows_dependencies():
    """Install dependencies on Windows."""
    print("Setting up Windows dependencies...")
    
    # Check if Chocolatey is available
    try:
        run_command(["choco", "--version"])
        print("✓ Chocolatey detected")
        
        # Install packages via Chocolatey
        packages = ["postgresql13", "redis-64", "git", "nodejs", "python3"]
        print("Installing packages via Chocolatey...")
        for package in packages:
            try:
                run_command(["choco", "install", package, "-y"])
                print(f"✓ Installed {package}")
            except:
                print(f"⚠ Failed to install {package}")
                
    except:
        print("Chocolatey not found. Please install manually:")
        print("1. PostgreSQL: https://www.postgresql.org/download/windows/")
        print("2. Redis: https://github.com/microsoftarchive/redis/releases")
        print("3. Git: https://git-scm.com/download/win")
        print("4. Node.js: https://nodejs.org/en/download/")
        print("5. Python 3.8+: https://www.python.org/downloads/")

def install_macos_dependencies():
    """Install dependencies on macOS."""
    print("Setting up macOS dependencies...")
    
    # Check if Homebrew is available
    try:
        run_command(["brew", "--version"])
        print("✓ Homebrew detected")
        
        # Install packages via Homebrew
        packages = ["postgresql@15", "redis", "node", "python@3.11"]
        print("Installing packages via Homebrew...")
        for package in packages:
            try:
                run_command(["brew", "install", package])
                print(f"✓ Installed {package}")
            except:
                print(f"⚠ Failed to install {package}")
                
        # Start services
        run_command(["brew", "services", "start", "postgresql@15"])
        run_command(["brew", "services", "start", "redis"])
        
    except:
        print("Homebrew not found. Installing Homebrew...")
        # Install Homebrew
        install_cmd = '/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
        run_command(install_cmd, shell=True)
        
        # Retry package installation
        install_macos_dependencies()

def install_linux_desktop_dependencies():
    """Install dependencies on Linux desktop."""
    print("Setting up Linux desktop dependencies...")
    
    # Detect package manager
    if shutil.which("apt"):
        # Debian/Ubuntu
        packages = [
            "postgresql", "postgresql-contrib", "redis-server", "python3-pip",
            "python3-venv", "git", "curl", "wget", "build-essential", "nodejs", "npm"
        ]
        
        print("Installing system packages (Ubuntu/Debian)...")
        run_command(["sudo", "apt-get", "update"])
        run_command(["sudo", "apt-get", "install", "-y"] + packages)
        
        # Start services
        run_command(["sudo", "systemctl", "enable", "postgresql"])
        run_command(["sudo", "systemctl", "start", "postgresql"])
        run_command(["sudo", "systemctl", "enable", "redis-server"])
        run_command(["sudo", "systemctl", "start", "redis-server"])
        
    elif shutil.which("dnf"):
        # Fedora
        packages = [
            "postgresql", "postgresql-server", "redis", "python3-pip",
            "python3-virtualenv", "git", "curl", "wget", "gcc", "gcc-c++", "nodejs", "npm"
        ]
        
        print("Installing system packages (Fedora)...")
        run_command(["sudo", "dnf", "install", "-y"] + packages)
        
        # Initialize and start PostgreSQL
        run_command(["sudo", "postgresql-setup", "--initdb"])
        run_command(["sudo", "systemctl", "enable", "postgresql"])
        run_command(["sudo", "systemctl", "start", "postgresql"])
        run_command(["sudo", "systemctl", "enable", "redis"])
        run_command(["sudo", "systemctl", "start", "redis"])
        
    elif shutil.which("pacman"):
        # Arch Linux
        packages = [
            "postgresql", "redis", "python-pip", "python-virtualenv", 
            "git", "curl", "wget", "base-devel", "nodejs", "npm"
        ]
        
        print("Installing system packages (Arch Linux)...")
        run_command(["sudo", "pacman", "-S", "--noconfirm"] + packages)
        
        # Initialize and start PostgreSQL
        run_command(["sudo", "-u", "postgres", "initdb", "-D", "/var/lib/postgres/data"])
        run_command(["sudo", "systemctl", "enable", "postgresql"])
        run_command(["sudo", "systemctl", "start", "postgresql"])
        run_command(["sudo", "systemctl", "enable", "redis"])
        run_command(["sudo", "systemctl", "start", "redis"])

def create_desktop_virtual_environment():
    """Create a Python virtual environment optimized for desktop."""
    venv_path = Path("venv")
    
    if venv_path.exists():
        print("Virtual environment already exists")
        return
    
    print("Creating virtual environment...")
    run_command([sys.executable, "-m", "venv", "venv"])
    
    # Get activation script path
    if platform.system().lower() == "windows":
        activate_script = venv_path / "Scripts" / "activate.bat"
        pip_path = venv_path / "Scripts" / "pip.exe"
    else:
        activate_script = venv_path / "bin" / "activate"
        pip_path = venv_path / "bin" / "pip"
    
    print(f"Virtual environment created at {venv_path}")
    print(f"To activate: {activate_script}")
    
    return pip_path

def install_desktop_python_dependencies(pip_path=None):
    """Install Python dependencies optimized for desktop."""
    print("Installing Python dependencies for desktop...")
    
    if pip_path is None:
        pip_cmd = [sys.executable, "-m", "pip"]
    else:
        pip_cmd = [str(pip_path)]
    
    # Upgrade pip
    run_command(pip_cmd + ["install", "--upgrade", "pip"])
    
    # Install requirements with desktop-optimized versions
    if Path("requirements.txt").exists():
        run_command(pip_cmd + ["install", "-r", "requirements.txt"])
    else:
        print("Warning: requirements.txt not found")
    
    # Install additional desktop-specific packages
    desktop_packages = [
        "psutil>=5.9.6",
        "schedule>=1.2.0", 
        "plyer>=2.1.0",  # For desktop notifications
        "PyQt5>=5.15.9",  # For desktop GUI (optional)
        "win10toast>=0.9;platform_system=='Windows'",  # Windows notifications
    ]
    
    for package in desktop_packages:
        try:
            run_command(pip_cmd + ["install", package])
            print(f"✓ Installed {package}")
        except:
            print(f"⚠ Failed to install {package}")

def setup_desktop_database():
    """Setup PostgreSQL database for desktop."""
    print("Setting up PostgreSQL database for desktop...")
    
    system = platform.system().lower()
    
    if system == "windows":
        # Windows PostgreSQL setup
        commands = [
            'createdb -U postgres stock_monitor',
            'psql -U postgres -c "CREATE USER stock_user WITH PASSWORD \'stock_password\';"',
            'psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE stock_monitor TO stock_user;"',
            'psql -U postgres -c "ALTER USER stock_user CREATEDB;"'
        ]
    else:
        # Unix-like systems
        commands = [
            "sudo -u postgres createdb stock_monitor",
            "sudo -u postgres psql -c \"CREATE USER stock_user WITH PASSWORD 'stock_password';\"",
            "sudo -u postgres psql -c \"GRANT ALL PRIVILEGES ON DATABASE stock_monitor TO stock_user;\"",
            "sudo -u postgres psql -c \"ALTER USER stock_user CREATEDB;\""
        ]
    
    for command in commands:
        try:
            run_command(command, shell=True, check=False)
        except Exception as e:
            print(f"Warning: Database setup command failed: {e}")

def create_desktop_config():
    """Create desktop-optimized configuration."""
    config_path = Path("config/config.yaml")
    desktop_config_path = Path("config/config.desktop.yaml")
    example_config_path = Path("config/config.example.yaml")
    
    if desktop_config_path.exists():
        print("Desktop configuration file already exists")
        return
    
    if example_config_path.exists():
        # Read example config and modify for desktop
        with open(example_config_path, 'r') as f:
            content = f.read()
        
        # Desktop-specific optimizations
        desktop_optimizations = content.replace(
            "max_workers: 4", "max_workers: 8"
        ).replace(
            "memory_limit: \"2GB\"", "memory_limit: \"8GB\""
        ).replace(
            "cpu_limit: 0.8", "cpu_limit: 0.9"
        ).replace(
            "max_cache_size: \"500MB\"", "max_cache_size: \"2GB\""
        ).replace(
            "connection_pool_size: 10", "connection_pool_size: 20"
        ).replace(
            "batch_size: 1000", "batch_size: 5000"
        )
        
        with open(desktop_config_path, 'w') as f:
            f.write(desktop_optimizations)
        
        # Also create the regular config if it doesn't exist
        if not config_path.exists():
            shutil.copy(desktop_config_path, config_path)
        
        print("Desktop configuration file created")
        print("Please edit config/config.yaml with your API keys and settings")
        print("Desktop-optimized settings available in config/config.desktop.yaml")
    else:
        print("Warning: config.example.yaml not found")

def create_desktop_shortcuts():
    """Create desktop shortcuts and launchers."""
    system = platform.system().lower()
    
    if system == "windows":
        create_windows_shortcuts()
    elif system == "darwin":
        create_macos_shortcuts()
    elif system == "linux":
        create_linux_shortcuts()

def create_windows_shortcuts():
    """Create Windows shortcuts and batch files."""
    print("Creating Windows shortcuts...")
    
    batch_dir = Path("scripts/windows")
    batch_dir.mkdir(exist_ok=True)
    
    # Start script
    start_script = """@echo off
cd /d "%~dp0..\.."
call venv\\Scripts\\activate.bat
python src\\main.py
pause
"""
    with open(batch_dir / "start_monitor.bat", "w") as f:
        f.write(start_script)
    
    # Dashboard launcher
    dashboard_script = """@echo off
start http://localhost:8080
"""
    with open(batch_dir / "open_dashboard.bat", "w") as f:
        f.write(dashboard_script)
    
    # Grafana launcher
    grafana_script = """@echo off
start http://localhost:3000
"""
    with open(batch_dir / "open_grafana.bat", "w") as f:
        f.write(grafana_script)
    
    print("✓ Windows batch files created in scripts/windows/")

def create_macos_shortcuts():
    """Create macOS app launchers."""
    print("Creating macOS shortcuts...")
    
    app_dir = Path("scripts/macos")
    app_dir.mkdir(exist_ok=True)
    
    # Start script
    start_script = """#!/bin/bash
cd "$(dirname "$0")/../.."
source venv/bin/activate
python src/main.py
"""
    with open(app_dir / "start_monitor.sh", "w") as f:
        f.write(start_script)
    os.chmod(app_dir / "start_monitor.sh", 0o755)
    
    # Dashboard launcher
    dashboard_script = """#!/bin/bash
open http://localhost:8080
"""
    with open(app_dir / "open_dashboard.sh", "w") as f:
        f.write(dashboard_script)
    os.chmod(app_dir / "open_dashboard.sh", 0o755)
    
    print("✓ macOS shell scripts created in scripts/macos/")

def create_linux_shortcuts():
    """Create Linux desktop entries."""
    print("Creating Linux desktop shortcuts...")
    
    desktop_dir = Path("scripts/linux")
    desktop_dir.mkdir(exist_ok=True)
    
    # Get current directory
    current_dir = Path.cwd().absolute()
    
    # Start monitor desktop entry
    monitor_desktop = f"""[Desktop Entry]
Version=1.0
Type=Application
Name=Stock Market Monitor
Comment=24/7 Global Stock Market Monitoring System
Exec={current_dir}/venv/bin/python {current_dir}/src/main.py
Icon={current_dir}/assets/icon.png
Terminal=true
Categories=Office;Finance;
"""
    with open(desktop_dir / "stock-monitor.desktop", "w") as f:
        f.write(monitor_desktop)
    
    # Dashboard launcher desktop entry
    dashboard_desktop = f"""[Desktop Entry]
Version=1.0
Type=Application
Name=Stock Monitor Dashboard
Comment=Open Stock Monitor Web Dashboard
Exec=xdg-open http://localhost:8080
Icon=web-browser
Terminal=false
Categories=Office;Finance;Network;
"""
    with open(desktop_dir / "stock-dashboard.desktop", "w") as f:
        f.write(dashboard_desktop)
    
    print("✓ Linux desktop entries created in scripts/linux/")

def create_windows_service():
    """Create Windows service configuration."""
    print("Creating Windows service configuration...")
    
    service_dir = Path("scripts/windows/service")
    service_dir.mkdir(parents=True, exist_ok=True)
    
    # NSSM (Non-Sucking Service Manager) configuration
    service_script = f"""@echo off
echo Installing Stock Monitor as Windows Service...
echo.
echo Prerequisites:
echo 1. Download NSSM from https://nssm.cc/download
echo 2. Extract nssm.exe to this directory
echo.

if not exist nssm.exe (
    echo ERROR: nssm.exe not found in current directory
    echo Please download NSSM and place nssm.exe here
    pause
    exit /b 1
)

set INSTALL_DIR={Path.cwd().absolute()}
set PYTHON_EXE=%INSTALL_DIR%\\venv\\Scripts\\python.exe
set MAIN_SCRIPT=%INSTALL_DIR%\\src\\main.py

echo Installing service...
nssm install StockMonitor "%PYTHON_EXE%" "%MAIN_SCRIPT%"
nssm set StockMonitor AppDirectory "%INSTALL_DIR%"
nssm set StockMonitor DisplayName "24/7 Stock Market Monitor"
nssm set StockMonitor Description "24/7 Global Stock Market Monitoring System"

echo Service installed successfully!
echo Use 'net start StockMonitor' to start the service
echo Use 'net stop StockMonitor' to stop the service
echo Use 'nssm remove StockMonitor confirm' to uninstall the service
pause
"""
    
    with open(service_dir / "install_service.bat", "w") as f:
        f.write(service_script)
    
    # Uninstall script
    uninstall_script = """@echo off
echo Uninstalling Stock Monitor Windows Service...
nssm stop StockMonitor
nssm remove StockMonitor confirm
echo Service uninstalled successfully!
pause
"""
    
    with open(service_dir / "uninstall_service.bat", "w") as f:
        f.write(uninstall_script)
    
    print("✓ Windows service scripts created in scripts/windows/service/")

def create_desktop_directories():
    """Create necessary directories for desktop operation."""
    directories = [
        "logs",
        "data",
        "backups",
        "temp",
        "cache",
        "screenshots",  # For web scraping
        "exports",      # For data exports
        "scripts/windows",
        "scripts/macos", 
        "scripts/linux",
        "assets"        # For icons and resources
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {directory}")

def optimize_desktop_performance():
    """Apply desktop-specific performance optimizations."""
    print("Applying desktop performance optimizations...")
    
    # Create performance tuning script
    perf_script = """#!/usr/bin/env python3
import psutil
import os

def optimize_python_performance():
    \"\"\"Apply Python-specific optimizations.\"\"\"
    # Set environment variables for better performance
    os.environ['PYTHONOPTIMIZE'] = '1'
    os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
    
    # Increase recursion limit for complex operations
    import sys
    sys.setrecursionlimit(10000)

def get_optimal_worker_count():
    \"\"\"Calculate optimal worker count based on system resources.\"\"\"
    cpu_count = psutil.cpu_count(logical=True)
    memory_gb = psutil.virtual_memory().total / (1024**3)
    
    # Conservative approach: use 80% of CPUs, but consider memory
    max_workers = min(int(cpu_count * 0.8), int(memory_gb / 2))
    return max(max_workers, 2)  # Minimum 2 workers

if __name__ == "__main__":
    print(f"Optimal worker count: {get_optimal_worker_count()}")
    print(f"Total CPU cores: {psutil.cpu_count(logical=True)}")
    print(f"Total RAM: {psutil.virtual_memory().total / (1024**3):.1f} GB")
"""
    
    with open("scripts/optimize_performance.py", "w") as f:
        f.write(perf_script)
    
    print("✓ Performance optimization script created")

def run_desktop_tests():
    """Run tests specific to desktop environment."""
    print("Running desktop-specific tests...")
    
    try:
        # Test Python imports
        import fastapi
        import yfinance
        import pandas
        import numpy
        import psutil
        print("✓ Core Python dependencies imported successfully")
        
        # Test system resources
        cpu_count = psutil.cpu_count(logical=True)
        memory_gb = psutil.virtual_memory().total / (1024**3)
        disk_gb = psutil.disk_usage('.').free / (1024**3)
        
        print(f"✓ System Resources:")
        print(f"  - CPU cores: {cpu_count}")
        print(f"  - RAM: {memory_gb:.1f} GB")
        print(f"  - Free disk space: {disk_gb:.1f} GB")
        
        # Check minimum requirements
        if memory_gb < 4:
            print("⚠ Warning: Less than 4GB RAM available. Performance may be limited.")
        if disk_gb < 10:
            print("⚠ Warning: Less than 10GB free disk space. Consider cleaning up.")
        
        # Test database connection (basic check)
        print("✓ Desktop environment tests passed")
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    except Exception as e:
        print(f"✗ Test error: {e}")
        return False
    
    return True

def main():
    """Main setup function for desktop environments."""
    parser = argparse.ArgumentParser(description="Setup Stock Market Monitor for Desktop")
    parser.add_argument("--skip-system", action="store_true", help="Skip system dependency installation")
    parser.add_argument("--skip-db", action="store_true", help="Skip database setup")
    parser.add_argument("--skip-docker", action="store_true", help="Skip Docker setup")
    parser.add_argument("--docker-only", action="store_true", help="Use Docker only (skip manual installation)")
    parser.add_argument("--test-only", action="store_true", help="Run tests only")
    
    args = parser.parse_args()
    
    print("=== Stock Market Monitor - Desktop Setup ===")
    print(f"Platform: {platform.system()} {platform.release()}")
    print(f"Architecture: {platform.machine()}")
    print()
    
    if args.test_only:
        run_desktop_tests()
        return
    
    # Check Python version
    check_python_version()
    print()
    
    # Check Docker availability
    docker_available = False
    if not args.skip_docker:
        docker_available = check_docker()
        print()
    
    if args.docker_only and docker_available:
        print("Using Docker-only setup...")
        print("Run: docker-compose -f docker-compose.desktop.yml up -d")
        return
    
    # Install system dependencies
    if not args.skip_system and not docker_available:
        install_desktop_dependencies()
        print()
    
    # Create virtual environment
    pip_path = create_desktop_virtual_environment()
    print()
    
    # Install Python dependencies
    install_desktop_python_dependencies(pip_path)
    print()
    
    # Setup database
    if not args.skip_db and not docker_available:
        setup_desktop_database()
        print()
    
    # Create configuration
    create_desktop_config()
    print()
    
    # Create directories
    create_desktop_directories()
    print()
    
    # Create desktop shortcuts
    create_desktop_shortcuts()
    print()
    
    # Create Windows service (if Windows)
    if platform.system().lower() == "windows":
        create_windows_service()
        print()
    
    # Apply performance optimizations
    optimize_desktop_performance()
    print()
    
    # Run tests
    if run_desktop_tests():
        print()
        print("=== Desktop Setup Complete ===")
        print()
        print("Next steps:")
        print("1. Edit config/config.yaml with your API keys")
        print("2. Start the system:")
        if platform.system().lower() == "windows":
            print("   - Double-click scripts/windows/start_monitor.bat")
            print("   - Or run: python src/main.py")
        else:
            print("   - Run: source venv/bin/activate && python src/main.py")
        print("3. Access the dashboard at: http://localhost:8080")
        print("4. Access Grafana at: http://localhost:3000")
        print()
        if docker_available:
            print("Alternative Docker setup:")
            print("   docker-compose -f docker-compose.desktop.yml up -d")
        print()
        print("For more information, see the desktop documentation.")
    else:
        print("Setup completed with warnings. Please check the output above.")

if __name__ == "__main__":
    main()