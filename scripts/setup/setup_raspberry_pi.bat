@echo off
setlocal enabledelayedexpansion

echo Setting up Raspberry Pi for Trading Monitor...
echo.

REM Check if running as administrator
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo This script requires administrator privileges.
    echo Please run as administrator.
    pause
    exit /b 1
)

echo Updating system packages...
echo Please run these commands on your Raspberry Pi:
echo.
echo sudo apt update ^&^& sudo apt upgrade -y
echo.
echo Installing essential packages...
echo sudo apt install -y git curl wget htop vim unzip python3 python3-pip python3-venv build-essential libffi-dev libssl-dev libjpeg-dev zlib1g-dev libfreetype6-dev liblcms2-dev libopenjp2-7-dev libtiff5-dev libwebp-dev libharfbuzz-dev libfribidi-dev libxcb1-dev
echo.

echo Installing Docker...
echo curl -fsSL https://get.docker.com -o get-docker.sh
echo sudo sh get-docker.sh
echo sudo usermod -aG docker $USER
echo rm get-docker.sh
echo.

echo Installing Docker Compose...
echo sudo apt install -y docker-compose-plugin
echo.

echo Setting up project directory...
echo mkdir -p /home/$USER/trading-monitor
echo cd /home/$USER/trading-monitor
echo.

echo Cloning project repository...
echo git clone YOUR_REPO_URL .
echo.

echo Setting permissions...
echo sudo chown -R $USER:$USER /home/$USER/trading-monitor
echo chmod +x scripts/*.sh
echo.

echo Setting up Python environment...
echo python3 -m venv venv
echo source venv/bin/activate
echo pip install --upgrade pip
echo pip install -r requirements.txt
echo.

echo Configuring system for 24/7 operation...
echo sudo raspi-config nonint do_blanking 1
echo echo 'GOVERNOR="performance"' ^| sudo tee -a /etc/default/cpufrequtils
echo echo "vm.swappiness=10" ^| sudo tee -a /etc/sysctl.conf
echo.

echo Creating systemd service...
echo sudo tee /etc/systemd/system/trading-monitor.service ^> /dev/null ^<^<EOF
echo [Unit]
echo Description=Trading Monitor Service
echo After=docker.service
echo Requires=docker.service
echo.
echo [Service]
echo Type=oneshot
echo RemainAfterExit=yes
echo WorkingDirectory=/home/$USER/trading-monitor
echo ExecStart=/usr/bin/docker-compose -f docker-compose.raspberry-pi.yml up -d
echo ExecStop=/usr/bin/docker-compose -f docker-compose.raspberry-pi.yml down
echo TimeoutStartSec=0
echo.
echo [Install]
echo WantedBy=multi-user.target
echo EOF
echo.

echo Enabling service...
echo sudo systemctl enable trading-monitor.service
echo.

echo Configuring firewall...
echo sudo ufw allow 22/tcp
echo sudo ufw allow 80/tcp
echo sudo ufw allow 443/tcp
echo sudo ufw allow 3000/tcp
echo sudo ufw allow 5432/tcp
echo sudo ufw allow 8086/tcp
echo sudo ufw allow 9090/tcp
echo sudo ufw --force enable
echo.

echo Creating monitoring script...
echo cat ^> /home/$USER/trading-monitor/monitor_system.sh ^<^< 'EOF'
echo #!/bin/bash
echo echo "=== System Status ==="
echo echo "Date: $(date)"
echo echo "Uptime: $(uptime)"
echo echo "CPU Usage: $(top -bn1 ^| grep "Cpu(s)" ^| awk '{print $2}' ^| cut -d'%%' -f1)%%"
echo echo "Memory Usage: $(free -m ^| awk 'NR==2{printf "%.1f%%", $3*100/$2}')"
echo echo "Disk Usage: $(df -h / ^| awk 'NR==2{print $5}')"
echo echo "Temperature: $(vcgencmd measure_temp ^| cut -d'=' -f2)"
echo echo.
echo echo "=== Docker Status ==="
echo docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo echo.
echo echo "=== Service Health ==="
echo curl -s http://localhost/health ^|^| echo "Health check failed"
echo EOF
echo chmod +x /home/$USER/trading-monitor/monitor_system.sh
echo.

echo Setting up cron job for monitoring...
echo (crontab -l 2^>^/dev/null; echo "*/5 * * * * /home/$USER/trading-monitor/monitor_system.sh ^>^> /home/$USER/trading-monitor/logs/system_monitor.log 2^>^&1") ^| crontab -
echo.

echo Creating log directory...
echo mkdir -p /home/$USER/trading-monitor/logs
echo.

echo Setting up log rotation...
echo sudo tee /etc/logrotate.d/trading-monitor ^> /dev/null ^<^<EOF
echo /home/$USER/trading-monitor/logs/*.log {
echo     daily
echo     missingok
echo     rotate 7
echo     compress
echo     delaycompress
echo     notifempty
echo     create 644 $USER $USER
echo }
echo EOF
echo.

echo Optimizing SD card for frequent writes...
echo echo "tmpfs /tmp tmpfs defaults,noatime,nosuid,size=100m 0 0" ^| sudo tee -a /etc/fstab
echo echo "tmpfs /var/tmp tmpfs defaults,noatime,nosuid,size=100m 0 0" ^| sudo tee -a /etc/fstab
echo echo "tmpfs /var/log tmpfs defaults,noatime,nosuid,size=100m 0 0" ^| sudo tee -a /etc/fstab
echo.

echo Creating backup script...
echo cat ^> /home/$USER/trading-monitor/backup_data.sh ^<^< 'EOF'
echo #!/bin/bash
echo BACKUP_DIR="/home/$USER/backups"
echo DATE=$(date +%%Y%%m%%d_%%H%%M%%S)
echo mkdir -p $BACKUP_DIR
echo echo "Creating backup: $DATE"
echo docker exec trading_postgres_pi pg_dump -U stock_user trading_monitor ^> $BACKUP_DIR/postgres_$DATE.sql
echo docker exec trading_influxdb_pi influx backup /var/lib/influxdb2/backup_$DATE
echo tar -czf $BACKUP_DIR/config_$DATE.tar.gz grafana/ prometheus/ docker/
echo echo "Backup completed: $BACKUP_DIR"
echo EOF
echo chmod +x /home/$USER/trading-monitor/backup_data.sh
echo.

echo Creating restore script...
echo cat ^> /home/$USER/trading-monitor/restore_data.sh ^<^< 'EOF'
echo #!/bin/bash
echo if [ -z "$1" ]; then
echo     echo "Usage: $0 ^<backup_date^>"
echo     echo "Example: $0 20241201_143022"
echo     exit 1
echo fi
echo BACKUP_DATE=$1
echo BACKUP_DIR="/home/$USER/backups"
echo echo "Restoring from backup: $BACKUP_DATE"
echo if [ -f "$BACKUP_DIR/postgres_$BACKUP_DATE.sql" ]; then
echo     docker exec -i trading_postgres_pi psql -U stock_user trading_monitor ^< $BACKUP_DIR/postgres_$BACKUP_DATE.sql
echo     echo "PostgreSQL restored"
echo else
echo     echo "PostgreSQL backup not found"
echo fi
echo if [ -d "$BACKUP_DIR/backup_$BACKUP_DATE" ]; then
echo     docker exec trading_influxdb_pi influx restore /var/lib/influxdb2/backup_$BACKUP_DATE
echo     echo "InfluxDB restored"
echo else
echo     echo "InfluxDB backup not found"
echo fi
echo echo "Restore completed"
echo EOF
echo chmod +x /home/$USER/trading-monitor/restore_data.sh
echo.

echo Starting trading monitor services...
echo docker-compose -f docker-compose.raspberry-pi.yml up -d
echo.

echo Waiting for services to be ready...
echo sleep 30
echo.

echo Checking service status...
echo docker ps
echo.

echo.
echo === Raspberry Pi Trading Monitor Setup Complete! ===
echo.
echo Services will be running on:
echo - Grafana Dashboard: http://YOUR_PI_IP:3000
echo - InfluxDB: http://YOUR_PI_IP:8086
echo - Prometheus: http://YOUR_PI_IP:9090
echo.
echo Default credentials:
echo - Grafana: admin / trading123
echo - InfluxDB: admin / trading123
echo.
echo Useful commands:
echo - Monitor system: ./monitor_system.sh
echo - Backup data: ./backup_data.sh
echo - Restore data: ./restore_data.sh ^<date^>
echo - View logs: docker-compose -f docker-compose.raspberry-pi.yml logs
echo.
echo The service will auto-start on boot!
echo Reboot the Pi to apply all optimizations.
echo.

echo Copy these commands to your Raspberry Pi terminal.
echo Make sure to replace YOUR_REPO_URL with your actual repository URL.
echo.

pause


