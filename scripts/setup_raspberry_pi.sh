#!/bin/bash

echo "Setting up Raspberry Pi for Trading Monitor..."

# Update system
echo "Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install essential packages
echo "Installing essential packages..."
sudo apt install -y \
    git \
    curl \
    wget \
    htop \
    vim \
    unzip \
    python3 \
    python3-pip \
    python3-venv \
    build-essential \
    libffi-dev \
    libssl-dev \
    libjpeg-dev \
    zlib1g-dev \
    libfreetype6-dev \
    liblcms2-dev \
    libopenjp2-7-dev \
    libtiff5-dev \
    libwebp-dev \
    libharfbuzz-dev \
    libfribidi-dev \
    libxcb1-dev

# Install Docker
echo "Installing Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
    echo "Docker installed successfully"
else
    echo "Docker already installed"
fi

# Install Docker Compose
echo "Installing Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    sudo apt install -y docker-compose-plugin
    echo "Docker Compose installed successfully"
else
    echo "Docker Compose already installed"
fi

# Create project directory
echo "Setting up project directory..."
PROJECT_DIR="/home/$USER/trading-monitor"
mkdir -p $PROJECT_DIR
cd $PROJECT_DIR

# Clone project if not exists
if [ ! -d ".git" ]; then
    echo "Cloning project repository..."
    git clone <YOUR_REPO_URL> .
else
    echo "Project already exists, pulling latest changes..."
    git pull
fi

# Set proper permissions
echo "Setting permissions..."
sudo chown -R $USER:$USER $PROJECT_DIR
chmod +x scripts/*.sh

# Create Python virtual environment
echo "Setting up Python environment..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Configure system for 24/7 operation
echo "Configuring system for 24/7 operation..."

# Disable screen saver
sudo raspi-config nonint do_blanking 1

# Set CPU governor to performance
echo 'GOVERNOR="performance"' | sudo tee -a /etc/default/cpufrequtils

# Optimize swap
echo "vm.swappiness=10" | sudo tee -a /etc/sysctl.conf

# Create systemd service for auto-start
echo "Creating systemd service..."
sudo tee /etc/systemd/system/trading-monitor.service > /dev/null <<EOF
[Unit]
Description=Trading Monitor Service
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=$PROJECT_DIR
ExecStart=/usr/bin/docker-compose -f docker-compose.raspberry-pi.yml up -d
ExecStop=/usr/bin/docker-compose -f docker-compose.raspberry-pi.yml down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF

# Enable service
sudo systemctl enable trading-monitor.service

# Configure firewall
echo "Configuring firewall..."
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw allow 3000/tcp  # Grafana
sudo ufw allow 5432/tcp  # PostgreSQL
sudo ufw allow 8086/tcp  # InfluxDB
sudo ufw allow 9090/tcp  # Prometheus
sudo ufw --force enable

# Create monitoring script
echo "Creating monitoring script..."
cat > $PROJECT_DIR/monitor_system.sh << 'EOF'
#!/bin/bash

echo "=== System Status ==="
echo "Date: $(date)"
echo "Uptime: $(uptime)"
echo "CPU Usage: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)%"
echo "Memory Usage: $(free -m | awk 'NR==2{printf "%.1f%%", $3*100/$2}')"
echo "Disk Usage: $(df -h / | awk 'NR==2{print $5}')"
echo "Temperature: $(vcgencmd measure_temp | cut -d'=' -f2)"

echo -e "\n=== Docker Status ==="
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo -e "\n=== Service Health ==="
curl -s http://localhost/health || echo "Health check failed"
EOF

chmod +x $PROJECT_DIR/monitor_system.sh

# Create cron job for system monitoring
echo "Setting up cron job for monitoring..."
(crontab -l 2>/dev/null; echo "*/5 * * * * $PROJECT_DIR/monitor_system.sh >> $PROJECT_DIR/logs/system_monitor.log 2>&1") | crontab -

# Create log directory
mkdir -p $PROJECT_DIR/logs

# Set up log rotation
sudo tee /etc/logrotate.d/trading-monitor > /dev/null <<EOF
$PROJECT_DIR/logs/*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    create 644 $USER $USER
}
EOF

# Optimize SD card for frequent writes
echo "Optimizing SD card for frequent writes..."
echo "tmpfs /tmp tmpfs defaults,noatime,nosuid,size=100m 0 0" | sudo tee -a /etc/fstab
echo "tmpfs /var/tmp tmpfs defaults,noatime,nosuid,size=100m 0 0" | sudo tee -a /etc/fstab
echo "tmpfs /var/log tmpfs defaults,noatime,nosuid,size=100m 0 0" | sudo tee -a /etc/fstab

# Create backup script
echo "Creating backup script..."
cat > $PROJECT_DIR/backup_data.sh << 'EOF'
#!/bin/bash

BACKUP_DIR="/home/$USER/backups"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

echo "Creating backup: $DATE"

# Backup PostgreSQL data
docker exec trading_postgres_pi pg_dump -U stock_user trading_monitor > $BACKUP_DIR/postgres_$DATE.sql

# Backup InfluxDB data
docker exec trading_influxdb_pi influx backup /var/lib/influxdb2/backup_$DATE

# Backup configuration files
tar -czf $BACKUP_DIR/config_$DATE.tar.gz grafana/ prometheus/ docker/

echo "Backup completed: $BACKUP_DIR"
EOF

chmod +x $PROJECT_DIR/backup_data.sh

# Create restore script
echo "Creating restore script..."
cat > $PROJECT_DIR/restore_data.sh << 'EOF'
#!/bin/bash

if [ -z "$1" ]; then
    echo "Usage: $0 <backup_date>"
    echo "Example: $0 20241201_143022"
    exit 1
fi

BACKUP_DATE=$1
BACKUP_DIR="/home/$USER/backups"

echo "Restoring from backup: $BACKUP_DATE"

# Restore PostgreSQL
if [ -f "$BACKUP_DIR/postgres_$BACKUP_DATE.sql" ]; then
    docker exec -i trading_postgres_pi psql -U stock_user trading_monitor < $BACKUP_DIR/postgres_$BACKUP_DATE.sql
    echo "PostgreSQL restored"
else
    echo "PostgreSQL backup not found"
fi

# Restore InfluxDB
if [ -d "$BACKUP_DIR/backup_$BACKUP_DATE" ]; then
    docker exec trading_influxdb_pi influx restore /var/lib/influxdb2/backup_$BACKUP_DATE
    echo "InfluxDB restored"
else
    echo "InfluxDB backup not found"
fi

echo "Restore completed"
EOF

chmod +x $PROJECT_DIR/restore_data.sh

# Final setup
echo "Finalizing setup..."

# Start services
echo "Starting trading monitor services..."
docker-compose -f docker-compose.raspberry-pi.yml up -d

# Wait for services to be ready
echo "Waiting for services to be ready..."
sleep 30

# Check service status
echo "Checking service status..."
docker ps

echo ""
echo "=== Raspberry Pi Trading Monitor Setup Complete! ==="
echo ""
echo "Services are running on:"
echo "- Grafana Dashboard: http://$(hostname -I | awk '{print $1}'):3000"
echo "- InfluxDB: http://$(hostname -I | awk '{print $1}'):8086"
echo "- Prometheus: http://$(hostname -I | awk '{print $1}'):9090"
echo ""
echo "Default credentials:"
echo "- Grafana: admin / trading123"
echo "- InfluxDB: admin / trading123"
echo ""
echo "Useful commands:"
echo "- Monitor system: ./monitor_system.sh"
echo "- Backup data: ./backup_data.sh"
echo "- Restore data: ./restore_data.sh <date>"
echo "- View logs: docker-compose -f docker-compose.raspberry-pi.yml logs"
echo ""
echo "The service will auto-start on boot!"
echo "Reboot the Pi to apply all optimizations."


