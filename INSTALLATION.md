# Installation Guide - Financial Monitoring System

A comprehensive real-time financial market monitoring system optimized for both Raspberry Pi and desktop environments.

## Quick Start

### One-Line Installation (Raspberry Pi)

```bash
curl -sSL https://raw.githubusercontent.com/CuteSurtr/monitor-advanced-backup/main/install-pi.sh | bash
```

The automated installation script:
- Detects your Pi model and optimizes configuration
- Installs Docker and all dependencies  
- Sets up systemd service for auto-start
- Configures firewall and system optimizations
- Creates management scripts

## System Requirements

### Raspberry Pi
| Model | RAM | Performance | Notes |
|-------|-----|------------|-------|
| **Pi 4 (8GB)** | 8GB | Excellent | Recommended |
| **Pi 4 (4GB)** | 4GB | Very Good | Good choice |
| **Pi 4 (2GB)** | 2GB | Good | Basic features |
| **Pi 3B+** | 1GB | Limited | Minimal config |
| **Pi Zero 2W** | 512MB | Basic | Very limited |

### Desktop/Server
- **RAM**: 4GB minimum, 8GB+ recommended
- **Storage**: 20GB+ available space
- **OS**: Windows 10+, macOS 10.14+, Ubuntu 18.04+

## Installation Methods

### Method 1: Automated Pi Installation (Recommended)

**Single Command:**
```bash
curl -sSL https://raw.githubusercontent.com/CuteSurtr/monitor-advanced-backup/main/install-pi.sh | bash
```

**Automated Features:**
- Detects ARM architecture (ARM64/ARM32)
- Configures memory limits based on your Pi model
- Installs Docker & Docker Compose
- Sets up systemd service for auto-start on boot
- Configures UFW firewall rules
- Creates management scripts (start/stop/status/backup)
- Optimizes system for 24/7 operation

### Method 2: Manual Git Installation

```bash
# Install Git if needed
sudo apt update && sudo apt install git -y

# Clone repository
git clone https://github.com/CuteSurtr/monitor-advanced-backup.git
cd monitor-advanced-backup

# Run installer
chmod +x install-pi.sh
./install-pi.sh
```

### Method 3: Desktop Installation

#### Windows (PowerShell as Administrator)
```powershell
# Install Docker Desktop first from https://docker.com
# Then clone repository
git clone https://github.com/CuteSurtr/monitor-advanced-backup.git
cd monitor-advanced-backup

# Start services
docker-compose -f docker-compose.desktop.yml up -d
```

#### macOS
```bash
# Install Docker Desktop first
brew install docker

# Clone and start
git clone https://github.com/CuteSurtr/monitor-advanced-backup.git
cd monitor-advanced-backup
docker-compose -f docker-compose.desktop.yml up -d
```

#### Linux
```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Clone and start
git clone https://github.com/CuteSurtr/monitor-advanced-backup.git
cd monitor-advanced-backup
docker-compose -f docker-compose.yml up -d
```

### Method 4: Manual Pi Setup

```bash
# 1. Install Dependencies
sudo apt update && sudo apt upgrade -y
sudo apt install docker.io docker-compose git -y
sudo usermod -aG docker $USER

# 2. Clone Repository
git clone https://github.com/CuteSurtr/monitor-advanced-backup.git
cd monitor-advanced-backup

# 3. Choose Configuration
# For Pi 4 (4GB+): Use standard config
docker-compose -f docker-compose.raspberry-pi.yml up -d

# For Pi 3 or 2GB Pi: Create memory override
cat > docker-compose.override.yml << EOF
version: '3.8'
services:
  postgres:
    deploy:
      resources:
        limits:
          memory: 256M
  redis:
    command: redis-server --maxmemory 128mb --maxmemory-policy allkeys-lru
  influxdb:
    deploy:
      resources:
        limits:
          memory: 256M
  grafana:
    deploy:
      resources:
        limits:
          memory: 256M
EOF

# 4. Start Services
docker-compose -f docker-compose.raspberry-pi.yml up -d
```

## Access Your Dashboard

After installation, access these services:

| Service | URL | Credentials |
|---------|-----|-------------|
| **Grafana Dashboard** | `http://YOUR_PI_IP:3000` | admin / trading123 |
| **Prometheus** | `http://YOUR_PI_IP:9090` | No auth |
| **InfluxDB** | `http://YOUR_PI_IP:8086` | admin / trading123 |

**Find your Pi IP:**
```bash
hostname -I | awk '{print $1}'
```

## Management Commands

The installer creates helpful management scripts:

```bash
cd ~/stock-monitor  # or your installation directory

# Basic Operations
./start.sh          # Start all services
./stop.sh           # Stop all services  
./status.sh         # Check service status
./restart.sh        # Restart all services

# Maintenance
./update.sh         # Update to latest images
./backup.sh         # Create backup
./logs.sh           # View service logs

# System Information
free -h            # Check memory usage
df -h              # Check disk usage
docker stats       # Monitor containers
```

### Systemd Service (Auto-start)

```bash
# Enable auto-start on boot
sudo systemctl enable stock-monitor

# Manual control
sudo systemctl start stock-monitor    # Start now
sudo systemctl stop stock-monitor     # Stop now
sudo systemctl status stock-monitor   # Check status
```

## Available Dashboards

Once installed, you'll have access to:

1. **Comprehensive Financial Dashboard**
   - Real-time multi-asset monitoring
   - Top 30 stocks, crypto, forex, commodities
   - Advanced analytics and risk metrics

2. **Macro Economic Dashboard**
   - Economic indicators and trends
   - Treasury yield curves
   - Federal Reserve data

3. **System Monitoring**
   - Container health and performance
   - Resource utilization
   - Alert management

## Configuration

### Environment Variables

Create `.env` file for customization:

```bash
# Database Configuration
POSTGRES_DB=trading_monitor
POSTGRES_USER=stock_user
POSTGRES_PASSWORD=your_secure_password

# InfluxDB Configuration
INFLUXDB_USERNAME=admin
INFLUXDB_PASSWORD=your_secure_password
INFLUXDB_ORG=trading_org
INFLUXDB_BUCKET=trading_data

# Grafana Configuration
GF_SECURITY_ADMIN_PASSWORD=your_secure_password

# API Keys (optional)
ALPHA_VANTAGE_API_KEY=your_key_here
POLYGON_API_KEY=your_key_here
```

### Memory Optimization

The installer automatically optimizes based on your hardware, but you can manually adjust:

**For 1GB devices (Pi 3):**
```yaml
# docker-compose.override.yml
version: '3.8'
services:
  prometheus:
    command:
      - '--storage.tsdb.retention.time=3d'
      - '--config.file=/etc/prometheus/prometheus.yml'
    deploy:
      resources:
        limits:
          memory: 128M
```

### Network Configuration

**Ports used:**
- 3000: Grafana (Web UI)
- 5432: PostgreSQL
- 6379: Redis  
- 8086: InfluxDB
- 9090: Prometheus

**Firewall (automatically configured):**
```bash
sudo ufw allow 3000/tcp  # Grafana
sudo ufw allow 8086/tcp  # InfluxDB (if external access needed)
sudo ufw allow 9090/tcp  # Prometheus (if external access needed)
```

## Troubleshooting

### Common Issues

**1. Installation Script Fails**
```bash
# Check prerequisites
sudo apt update
sudo apt install curl wget -y

# Run with verbose output
bash -x install-pi.sh
```

**2. Services Won't Start**
```bash
# Check Docker status
sudo systemctl status docker

# Check logs
docker-compose logs

# Restart Docker
sudo systemctl restart docker
```

**3. Can't Access Dashboard**
```bash
# Check if services are running
docker ps

# Check Pi IP address
ip addr show | grep inet

# Check firewall
sudo ufw status
```

**4. Out of Memory Errors**
```bash
# Check memory usage
free -h

# Check swap
swapon --show

# Enable swap if needed
sudo dphys-swapfile swapoff
sudo sed -i 's/CONF_SWAPSIZE=.*/CONF_SWAPSIZE=1024/' /etc/dphys-swapfile
sudo dphys-swapfile setup
sudo dphys-swapfile swapon
```

**5. Performance Issues**
```bash
# Check CPU throttling
vcgencmd get_throttled

# Check temperature
vcgencmd measure_temp

# Monitor resources
htop
```

### Getting Help

1. **Check Service Logs:**
   ```bash
   docker-compose logs [service_name]
   # Example: docker-compose logs grafana
   ```

2. **System Health Check:**
   ```bash
   ./status.sh  # If using management scripts
   # Or manually:
   docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
   ```

3. **Database Connection:**
   ```bash
   # Test PostgreSQL
   docker-compose exec postgres psql -U stock_user -d trading_monitor -c "\dt"
   
   # Test InfluxDB
   curl -i http://localhost:8086/health
   ```

## Updates

### Automatic Updates
```bash
# Update all services to latest versions
./update.sh

# Or manually:
docker-compose pull
docker-compose up -d
```

### Manual Updates
```bash
# Pull latest code
git pull origin main

# Rebuild if needed
docker-compose down
docker-compose up -d --build
```

## Backup & Recovery

### Create Backup
```bash
# Using backup script
./backup.sh

# Manual backup
mkdir -p backups
docker-compose exec postgres pg_dump -U stock_user trading_monitor > backups/database_backup.sql
tar -czf backups/config_backup.tar.gz grafana/ prometheus/ docker-compose.yml
```

### Restore Backup
```bash
# Stop services
docker-compose down

# Restore database
cat backups/database_backup.sql | docker-compose exec -T postgres psql -U stock_user trading_monitor

# Restore configs
tar -xzf backups/config_backup.tar.gz

# Restart services
docker-compose up -d
```

## Security

### Change Default Passwords
Update these in your `.env` file:
- Grafana admin password
- Database passwords  
- InfluxDB credentials

### Network Security
```bash
# Restrict external access (optional)
sudo ufw deny 5432  # PostgreSQL
sudo ufw deny 6379  # Redis
sudo ufw deny 8086  # InfluxDB

# Only allow local access to Grafana
sudo ufw allow from 192.168.1.0/24 to any port 3000
```

## Next Steps

1. **Access Dashboard:** Open `http://YOUR_PI_IP:3000`
2. **Login:** Use `admin` / `trading123`
3. **Explore Dashboards:** Navigate to "Comprehensive Financial Dashboard"
4. **Customize:** Add your API keys for real-time data
5. **Monitor:** Use `./status.sh` to monitor system health

## Additional Resources

- **Repository:** https://github.com/CuteSurtr/monitor-advanced-backup
- **Issues:** Report bugs via GitHub Issues
- **Documentation:** Check the `/docs` folder for advanced topics

**Professional-grade financial monitoring system for continuous market analysis.**