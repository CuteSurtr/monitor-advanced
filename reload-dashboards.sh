#!/bin/bash

echo "Reloading all Grafana dashboards..."
echo "This will restart Grafana service to load all provisioned dashboards."

# Check if Docker Compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "Error: docker-compose not found!"
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "docker-compose.raspberry-pi.yml" ]; then
    echo "Error: Please run this script from the project root directory."
    exit 1
fi

echo "Stopping Grafana service..."
docker-compose -f docker-compose.raspberry-pi.yml stop grafana

echo "Removing Grafana container to ensure clean reload..."
docker-compose -f docker-compose.raspberry-pi.yml rm -f grafana

echo "Starting Grafana with all dashboards..."
docker-compose -f docker-compose.raspberry-pi.yml up -d grafana

echo "Waiting for Grafana to start..."
sleep 15

# Check if Grafana is running
if docker-compose -f docker-compose.raspberry-pi.yml ps grafana | grep -q "Up"; then
    echo "✅ Grafana is running!"
    echo ""
    echo "📊 Dashboard Access:"
    echo "   URL: http://$(hostname -I | awk '{print $1}'):3000"
    echo "   Login: admin / trading123"
    echo ""
    echo "📁 Available Dashboard Folders:"
    echo "   • Core Analytics - Main financial dashboards"
    echo "   • Advanced Analytics - Technical indicators & ML"
    echo "   • Economic Data - Macro economic analysis"
    echo "   • Professional Suite - Professional tier dashboards"
    echo "   • Specialized Views - Custom and specialized dashboards"
    echo ""
    echo "🔄 All dashboards should now be visible in Grafana!"
else
    echo "❌ Error: Grafana failed to start properly."
    echo "Check logs with: docker-compose -f docker-compose.raspberry-pi.yml logs grafana"
fi