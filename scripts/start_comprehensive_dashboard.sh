#!/bin/bash

echo "Starting Comprehensive Financial Dashboard on Raspberry Pi..."

# Check if we're in the right directory
if [ ! -f "docker-compose.raspberry-pi.yml" ]; then
    echo "Error: docker-compose.raspberry-pi.yml not found!"
    echo "Please run this script from the project root directory."
    exit 1
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "Error: Docker is not running!"
    echo "Please start Docker first: sudo systemctl start docker"
    exit 1
fi

# Stop any existing containers
echo "Stopping existing containers..."
docker-compose -f docker-compose.raspberry-pi.yml down

# Remove any existing volumes (optional - comment out if you want to keep data)
# echo "Removing existing volumes..."
# docker-compose -f docker-compose.raspberry-pi.yml down -v

# Start the services
echo "Starting Comprehensive Financial Dashboard services..."
docker-compose -f docker-compose.raspberry-pi.yml up -d

# Wait for services to be ready
echo "Waiting for services to be ready..."
sleep 30

# Check service status
echo "Checking service status..."
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Get Pi IP address
PI_IP=$(hostname -I | awk '{print $1}')

echo ""
echo "=== Comprehensive Financial Dashboard Started! ==="
echo ""
echo "Dashboard Access:"
echo "- Grafana: http://$PI_IP:3000"
echo "- InfluxDB: http://$PI_IP:8086"
echo "- Prometheus: http://$PI_IP:9090"
echo ""
echo "Default Credentials:"
echo "- Grafana: admin / trading123"
echo "- InfluxDB: admin / trading123"
echo ""
echo "Dashboard Features:"
echo "- Top 30 stocks, forex, crypto, commodities"
echo "- Time series graphs for all categories"
echo "- Trading volume analysis"
echo "- Average return rates"
echo "- Top movers (gainers and losers)"
echo "- VaR/CVaR analysis (5%, 95%, 99%)"
echo "- Max drawdown analysis"
echo "- Top P&L by category"
echo "- Stock correlation analysis (4x4 heatmap)"
echo "- VIX monitoring with time series"
echo "- P/E ratio monitoring"
echo "- Options chain analysis"
echo "- Enhanced market news & sentiment analysis"
echo "- Perfect 4-color coding system"
echo ""
echo "Useful Commands:"
echo "- View logs: docker-compose -f docker-compose.raspberry-pi.yml logs"
echo "- Restart services: docker-compose -f docker-compose.raspberry-pi.yml restart"
echo "- Stop services: docker-compose -f docker-compose.raspberry-pi.yml down"
echo "- Monitor system: ./monitor_system.sh"
echo ""
echo "The dashboard will be available in the 'Professional Analytics' folder in Grafana!"
echo "Navigate to: Dashboards > Professional Analytics > Comprehensive Financial Dashboard"

