# Desktop Setup Guide

## 24/7 Global Stock Market Monitor - Desktop Edition

This guide covers setting up the stock market monitoring system on desktop environments (Windows, macOS, Linux). The desktop version is optimized for higher performance with enhanced features and better resource utilization.

## Table of Contents

- [System Requirements](#system-requirements)
- [Quick Start](#quick-start)
- [Installation Methods](#installation-methods)
- [Configuration](#configuration)
- [Running the System](#running-the-system)
- [Desktop Features](#desktop-features)
- [Performance Optimization](#performance-optimization)
- [Troubleshooting](#troubleshooting)
- [Advanced Setup](#advanced-setup)

## System Requirements

### Minimum Requirements
- **CPU**: Dual-core processor (2.0 GHz or higher)
- **RAM**: 4 GB
- **Storage**: 10 GB free space
- **OS**: Windows 10/11, macOS 10.15+, or Linux (Ubuntu 18.04+, Fedora 30+, etc.)
- **Internet**: Broadband connection for real-time data

### Recommended Requirements
- **CPU**: Quad-core processor (3.0 GHz or higher)
- **RAM**: 8 GB or more
- **Storage**: 50 GB free space (SSD preferred)
- **OS**: Latest version of Windows 11, macOS 12+, or Linux
- **GPU**: Optional for ML acceleration

### Software Dependencies
- Python 3.8 or higher
- Docker Desktop (optional but recommended)
- PostgreSQL 13+
- Redis 6.0+
- Git

## Quick Start

### Automated Installation

Choose your operating system and run the appropriate installer:

#### Windows
```batch
# Run as Administrator
scripts\install_windows.bat

# Or using PowerShell
PowerShell -ExecutionPolicy Bypass -File scripts\install_desktop.ps1
```

#### macOS
```bash
# Make executable and run
chmod +x scripts/install_macos.sh
./scripts/install_macos.sh
```

#### Linux
```bash
# Make executable and run
chmod +x scripts/install_linux.sh
./scripts/install_linux.sh
```

### Docker Quick Start (Recommended)

If you have Docker Desktop installed:

```bash
# Start all services
docker-compose -f docker-compose.desktop.yml up -d

# Check status
docker-compose -f docker-compose.desktop.yml ps

# View logs
docker-compose -f docker-compose.desktop.yml logs -f
```

## Installation Methods

### Method 1: Automated Script Installation

The automated scripts handle all dependencies and configuration:

1. **Download** the repository
2. **Run** the appropriate installer script
3. **Edit** configuration file with your API keys
4. **Start** the system

### Method 2: Manual Installation

For advanced users who prefer manual control:

#### Step 1: Install System Dependencies

**Windows (using Chocolatey):**
```powershell
# Install Chocolatey first
Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

# Install packages
choco install postgresql13 redis-64 git nodejs python3 -y
```

**macOS (using Homebrew):**
```bash
# Install Homebrew first
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install packages
brew install postgresql@15 redis node python@3.11
brew services start postgresql@15 redis
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib redis-server python3-pip python3-venv git nodejs npm build-essential -y
sudo systemctl enable postgresql redis-server
sudo systemctl start postgresql redis-server
```

#### Step 2: Setup Python Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate.bat
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements.desktop.txt
```

#### Step 3: Setup Database

```bash
# Create database
sudo -u postgres createdb stock_monitor
sudo -u postgres psql -c "CREATE USER stock_user WITH PASSWORD 'stock_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE stock_monitor TO stock_user;"
```

#### Step 4: Configuration

```bash
# Copy example configuration
cp config/config.example.yaml config/config.yaml

# Or use desktop-optimized config
cp config/config.desktop.yaml config/config.yaml

# Edit with your API keys
nano config/config.yaml
```

### Method 3: Docker Installation

For containerized deployment with all dependencies:

```bash
# Clone repository
git clone <repository-url>
cd monitor-advanced

# Start services
docker-compose -f docker-compose.desktop.yml up -d

# Configure (edit config/config.yaml)

# Restart services
docker-compose -f docker-compose.desktop.yml restart stock_monitor
```

## Configuration

### API Keys Required

Get API keys from these providers:

1. **Alpha Vantage**: [alphavantage.co](https://www.alphavantage.co/support/#api-key)
2. **Polygon.io**: [polygon.io](https://polygon.io/)
3. **Finnhub**: [finnhub.io](https://finnhub.io/)
4. **News API**: [newsapi.org](https://newsapi.org/)

### Configuration Files

- `config/config.yaml` - Main configuration
- `config/config.desktop.yaml` - Desktop-optimized settings

### Key Desktop Optimizations

```yaml
performance:
  max_workers: 12          # More workers for desktop
  memory_limit: "8GB"      # Higher memory limit
  cpu_limit: 0.9           # Use 90% of CPU
  cache_ttl: 180           # 3-minute cache
  max_cache_size: "2GB"    # Larger cache
  batch_size: 5000         # Larger batch processing

data_collection:
  stock_data_interval: 30  # Faster updates
  max_requests_per_minute: 200
  max_concurrent_requests: 20

desktop:
  system_tray:
    enabled: true
  hotkeys:
    enabled: true
  widgets:
    enabled: true
```

## Running the System

### Option 1: Direct Python Execution

```bash
# Activate environment
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate.bat  # Windows

# Start system
python src/main.py
```

### Option 2: Desktop Shortcuts

After installation, use the created shortcuts:

**Windows:**
- Double-click "Stock Monitor" on desktop
- Or run `scripts\windows\start_monitor.bat`

**macOS:**
- Run `./scripts/macos/start_monitor.sh`
- Or use terminal alias: `stock-monitor`

**Linux:**
- Launch from Applications menu
- Or run `./scripts/linux/start_monitor.sh`
- Or use terminal alias: `stock-monitor`

### Option 3: Docker

```bash
# Start all services
docker-compose -f docker-compose.desktop.yml up -d

# Stop services
docker-compose -f docker-compose.desktop.yml down

# Update and restart
docker-compose -f docker-compose.desktop.yml pull
docker-compose -f docker-compose.desktop.yml up -d
```

### Option 4: Background Service

**Windows Service:**
```batch
# Install service (requires NSSM)
scripts\windows\service\install_service.bat

# Start/stop service
net start StockMonitor
net stop StockMonitor
```

**Linux Systemd:**
```bash
# Enable user service
systemctl --user enable stock-monitor
systemctl --user start stock-monitor

# Check status
systemctl --user status stock-monitor
```

## Desktop Features

### Enhanced Dashboard

Access the enhanced dashboard at: http://localhost:8080

Features:
- Real-time portfolio tracking
- Advanced technical analysis
- Market sentiment analysis
- Economic calendar integration
- Custom screeners
- Backtesting capabilities

### System Tray Integration

The desktop version includes system tray functionality:
- Quick access to dashboard
- Real-time alert notifications
- System status monitoring
- Quick portfolio overview

### Desktop Notifications

Configure notifications in `config.yaml`:

```yaml
alerts:
  desktop:
    enabled: true
    notification_level: "important"
    sound_enabled: true
    popup_duration: 10
```

### Keyboard Shortcuts

Default shortcuts (configurable):
- `Ctrl+Shift+D`: Toggle dashboard
- `Ctrl+Shift+P`: Quick portfolio view
- `Ctrl+Shift+X`: Emergency stop

### Additional Services

The desktop version includes additional services:

- **Jupyter Lab**: http://localhost:8888 (data analysis)
- **pgAdmin**: http://localhost:5050 (database management)
- **Redis Commander**: http://localhost:8081 (cache management)
- **Flower**: http://localhost:5555 (task monitoring)
- **Kibana**: http://localhost:5601 (log analysis)

## Performance Optimization

### Automatic Optimization

The desktop setup automatically optimizes settings based on your system:

```bash
# Check optimal settings
python scripts/optimize_performance.py
```

### Manual Optimization

#### CPU Optimization
```yaml
performance:
  max_workers: 8  # Set to 80% of CPU cores
  async_enabled: true
  max_concurrent_tasks: 50
```

#### Memory Optimization
```yaml
performance:
  memory_limit: "8GB"
  max_cache_size: "2GB"
  batch_size: 5000
```

#### Database Optimization
```yaml
database:
  pool_size: 20
  max_overflow: 50
  connection_pool_size: 25
```

### GPU Acceleration (Optional)

For systems with compatible GPUs:

```yaml
advanced:
  ml_models:
    gpu_acceleration: true
```

## Troubleshooting

### Common Issues

#### Port Already in Use
```bash
# Check what's using the port
netstat -ano | findstr :8080  # Windows
lsof -i :8080                 # macOS/Linux

# Kill process if needed
taskkill /PID <PID> /F        # Windows
kill -9 <PID>                 # macOS/Linux
```

#### Database Connection Issues
```bash
# Check PostgreSQL status
# Windows:
sc query postgresql-x64-13

# Linux:
systemctl status postgresql

# Restart if needed
sudo systemctl restart postgresql
```

#### Python Dependencies
```bash
# Reinstall requirements
pip install --force-reinstall -r requirements.txt
```

#### Docker Issues
```bash
# Reset Docker environment
docker-compose -f docker-compose.desktop.yml down -v
docker-compose -f docker-compose.desktop.yml up -d
```

### Log Files

Check these locations for logs:
- Application logs: `logs/stock_monitor.log`
- Docker logs: `docker-compose logs`
- System logs: OS-specific locations

### Performance Issues

#### High CPU Usage
1. Reduce `max_workers` in configuration
2. Increase data collection intervals
3. Disable unnecessary features

#### High Memory Usage
1. Reduce `max_cache_size`
2. Lower `batch_size`
3. Reduce `max_concurrent_requests`

#### Slow API Responses
1. Check internet connection
2. Verify API key limits
3. Enable intelligent caching

## Advanced Setup

### Custom Docker Images

Build custom images with additional packages:

```dockerfile
FROM python:3.11-slim

# Add custom packages
RUN apt-get update && apt-get install -y your-package

# Continue with standard setup
COPY requirements.txt .
RUN pip install -r requirements.txt
```

### SSL/HTTPS Setup

Configure SSL for secure access:

```yaml
dashboard:
  ssl:
    enabled: true
    cert_file: "/path/to/cert.pem"
    key_file: "/path/to/key.pem"
```

### Multi-Instance Setup

Run multiple instances for different portfolios:

```bash
# Copy configuration
cp config/config.yaml config/config.portfolio1.yaml

# Start with different config
CONFIG_PATH=config/config.portfolio1.yaml python src/main.py
```

### Cloud Integration

Configure cloud backups:

```yaml
advanced:
  export:
    cloud_backup: true
    aws_s3:
      bucket: "your-bucket"
      region: "us-east-1"
```

### Professional Features

Enable professional features:

```yaml
advanced:
  security:
    encryption_at_rest: true
    audit_logging: true
  ml_models:
    enabled: true
    auto_training: true
  api_optimization:
    intelligent_caching: true
    load_balancing: true
```

## Support

For support and questions:

1. Check the troubleshooting section
2. Review log files
3. Create an issue in the repository
4. Join the community discussions

## License

This project is licensed under the MIT License. See the LICENSE file for details.