#!/bin/bash

# Stock Monitor - Raspberry Pi Installation Script
# Optimized for ARM64 and ARM32 architectures

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="stock-monitor"
INSTALL_DIR="/opt/stock-monitor"
USER_DIR="$HOME/stock-monitor"

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_architecture() {
    ARCH=$(uname -m)
    log_info "Detected architecture: $ARCH"
    
    case $ARCH in
        aarch64|arm64)
            PLATFORM="linux/arm64"
            ;;
        armv7l|armv6l)
            PLATFORM="linux/arm/v7"
            ;;
        x86_64)
            PLATFORM="linux/amd64"
            log_warning "Running on x86_64, but this script is optimized for ARM"
            ;;
        *)
            log_error "Unsupported architecture: $ARCH"
            exit 1
            ;;
    esac
    
    log_info "Using platform: $PLATFORM"
}

check_memory() {
    TOTAL_MEM=$(free -m | awk 'NR==2{printf "%.0f", $2}')
    log_info "Total memory: ${TOTAL_MEM}MB"
    
    if [ "$TOTAL_MEM" -lt 1024 ]; then
        log_warning "Low memory detected (${TOTAL_MEM}MB). Using minimal configuration."
        MEMORY_PROFILE="minimal"
    elif [ "$TOTAL_MEM" -lt 2048 ]; then
        log_info "Medium memory detected (${TOTAL_MEM}MB). Using optimized configuration."
        MEMORY_PROFILE="optimized"
    else
        log_info "Sufficient memory detected (${TOTAL_MEM}MB). Using standard configuration."
        MEMORY_PROFILE="standard"
    fi
}

install_dependencies() {
    log_info "Installing system dependencies..."
    
    # Update package list
    sudo apt update
    
    # Install required packages
    sudo apt install -y \
        curl \
        wget \
        git \
        python3 \
        python3-pip \
        python3-venv \
        docker.io \
        docker-compose \
        nano \
        htop \
        ufw
    
    # Add user to docker group
    sudo usermod -aG docker $USER
    
    # Enable Docker service
    sudo systemctl enable docker
    sudo systemctl start docker
    
    log_success "Dependencies installed successfully"
}

setup_directories() {
    log_info "Setting up directories..."
    
    # Create user directory
    mkdir -p "$USER_DIR"
    cd "$USER_DIR"
    
    # Create required subdirectories
    mkdir -p {data,logs,config,grafana/provisioning/{dashboards,datasources}}
    
    log_success "Directories created"
}

download_project() {
    log_info "Setting up project files..."
    
    # Copy or download project files (adjust path as needed)
    if [ -d "/tmp/monitor-advanced" ]; then
        cp -r /tmp/monitor-advanced/* "$USER_DIR/"
    else
        log_info "Please copy your project files to $USER_DIR manually"
    fi
    
    # Make scripts executable
    find "$USER_DIR" -name "*.sh" -exec chmod +x {} \;
    
    log_success "Project files ready"
}

configure_memory_limits() {
    log_info "Configuring memory limits for $MEMORY_PROFILE profile..."
    
    case $MEMORY_PROFILE in
        minimal)
            # For Pi Zero or 512MB systems
            cat > "$USER_DIR/docker-compose.override.yml" << EOF
version: '3.8'
services:
  postgres:
    deploy:
      resources:
        limits:
          memory: 256M
        reservations:
          memory: 128M
  redis:
    command: redis-server --maxmemory 128mb --maxmemory-policy allkeys-lru
    deploy:
      resources:
        limits:
          memory: 128M
  influxdb:
    deploy:
      resources:
        limits:
          memory: 256M
        reservations:
          memory: 128M
  prometheus:
    command:
      - '--storage.tsdb.retention.time=3d'
      - '--config.file=/etc/prometheus/prometheus.yml'
    deploy:
      resources:
        limits:
          memory: 128M
  grafana:
    deploy:
      resources:
        limits:
          memory: 256M
        reservations:
          memory: 128M
EOF
            ;;
        optimized)
            # Use the existing raspberry-pi.yml limits
            log_info "Using optimized Pi configuration"
            ;;
        standard)
            # Use default limits
            log_info "Using standard configuration"
            ;;
    esac
}

setup_firewall() {
    log_info "Configuring firewall..."
    
    # Enable UFW
    sudo ufw --force enable
    
    # Allow SSH
    sudo ufw allow ssh
    
    # Allow web services
    sudo ufw allow 80/tcp
    sudo ufw allow 443/tcp
    sudo ufw allow 3000/tcp  # Grafana
    
    # Allow database access (optional, for external access)
    read -p "Allow external database access? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        sudo ufw allow 5432/tcp  # PostgreSQL
        sudo ufw allow 8086/tcp  # InfluxDB
        sudo ufw allow 9090/tcp  # Prometheus
        log_info "External database access enabled"
    fi
    
    log_success "Firewall configured"
}

setup_systemd_service() {
    log_info "Creating systemd service..."
    
    sudo tee /etc/systemd/system/stock-monitor.service > /dev/null << EOF
[Unit]
Description=Stock Monitor
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=$USER_DIR
ExecStart=/usr/bin/docker-compose -f docker-compose.raspberry-pi.yml up -d
ExecStop=/usr/bin/docker-compose -f docker-compose.raspberry-pi.yml down
TimeoutStartSec=0
User=$USER
Group=docker

[Install]
WantedBy=multi-user.target
EOF
    
    # Reload systemd and enable service
    sudo systemctl daemon-reload
    sudo systemctl enable stock-monitor.service
    
    log_success "Systemd service created"
}

create_management_scripts() {
    log_info "Creating management scripts..."
    
    # Start script
    cat > "$USER_DIR/start.sh" << 'EOF'
#!/bin/bash
echo "Starting Stock Monitor..."
docker-compose -f docker-compose.raspberry-pi.yml up -d
echo "Services started. Access Grafana at http://localhost:3000"
echo "Default login: admin/trading123"
EOF
    
    # Stop script
    cat > "$USER_DIR/stop.sh" << 'EOF'
#!/bin/bash
echo "Stopping Stock Monitor..."
docker-compose -f docker-compose.raspberry-pi.yml down
echo "Services stopped."
EOF
    
    # Status script
    cat > "$USER_DIR/status.sh" << 'EOF'
#!/bin/bash
echo "=== Stock Monitor Status ==="
docker-compose -f docker-compose.raspberry-pi.yml ps
echo ""
echo "=== System Resources ==="
echo "Memory usage:"
free -h
echo ""
echo "Disk usage:"
df -h | grep -E "(Filesystem|/dev/)"
echo ""
echo "Docker stats:"
docker stats --no-stream
EOF
    
    # Update script
    cat > "$USER_DIR/update.sh" << 'EOF'
#!/bin/bash
echo "Updating Stock Monitor..."
docker-compose -f docker-compose.raspberry-pi.yml pull
docker-compose -f docker-compose.raspberry-pi.yml up -d
echo "Update complete."
EOF
    
    # Backup script
    cat > "$USER_DIR/backup.sh" << 'EOF'
#!/bin/bash
BACKUP_DIR="$HOME/stock-monitor-backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/backup_$TIMESTAMP.tar.gz"

mkdir -p "$BACKUP_DIR"

echo "Creating backup..."
docker-compose -f docker-compose.raspberry-pi.yml exec postgres pg_dump -U stock_user trading_monitor > "$BACKUP_DIR/postgres_$TIMESTAMP.sql"
tar -czf "$BACKUP_FILE" grafana/ prometheus/ config/ logs/ "$BACKUP_DIR/postgres_$TIMESTAMP.sql"
rm "$BACKUP_DIR/postgres_$TIMESTAMP.sql"

echo "Backup created: $BACKUP_FILE"
ls -lh "$BACKUP_FILE"
EOF
    
    # Make scripts executable
    chmod +x "$USER_DIR"/*.sh
    
    log_success "Management scripts created"
}

setup_log_rotation() {
    log_info "Setting up log rotation..."
    
    sudo tee /etc/logrotate.d/stock-monitor > /dev/null << EOF
$USER_DIR/logs/*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    create 644 $USER $USER
}
EOF
    
    log_success "Log rotation configured"
}

optimize_system() {
    log_info "Applying system optimizations for Raspberry Pi..."
    
    # Increase swap if memory is low
    if [ "$TOTAL_MEM" -lt 1024 ]; then
        log_info "Increasing swap space..."
        sudo dphys-swapfile swapoff
        sudo sed -i 's/CONF_SWAPSIZE=.*/CONF_SWAPSIZE=1024/' /etc/dphys-swapfile
        sudo dphys-swapfile setup
        sudo dphys-swapfile swapon
    fi
    
    # GPU memory split (reduce GPU memory for headless operation)
    if [ -f /boot/config.txt ]; then
        if ! grep -q "gpu_mem" /boot/config.txt; then
            echo "gpu_mem=16" | sudo tee -a /boot/config.txt
            log_info "GPU memory reduced to 16MB (requires reboot)"
        fi
    fi
    
    log_success "System optimizations applied"
}

main() {
    log_info "Starting Stock Monitor installation for Raspberry Pi..."
    
    # Pre-installation checks
    check_architecture
    check_memory
    
    # Installation steps
    install_dependencies
    setup_directories
    download_project
    configure_memory_limits
    setup_firewall
    setup_systemd_service
    create_management_scripts
    setup_log_rotation
    optimize_system
    
    log_success "Installation completed successfully!"
    echo ""
    log_info "Next steps:"
    echo "1. Reboot your Raspberry Pi (recommended): sudo reboot"
    echo "2. After reboot, navigate to: cd $USER_DIR"
    echo "3. Start the services: ./start.sh"
    echo "4. Access Grafana: http://$(hostname -I | awk '{print $1}'):3000"
    echo "   Default login: admin/trading123"
    echo ""
    log_info "Management commands:"
    echo "- Start services: ./start.sh"
    echo "- Stop services: ./stop.sh"
    echo "- Check status: ./status.sh"
    echo "- Update services: ./update.sh"
    echo "- Create backup: ./backup.sh"
    echo ""
    log_info "Systemd service:"
    echo "- Enable auto-start: sudo systemctl enable stock-monitor"
    echo "- Start now: sudo systemctl start stock-monitor"
    echo "- Check status: sudo systemctl status stock-monitor"
}

# Run main function
main "$@"