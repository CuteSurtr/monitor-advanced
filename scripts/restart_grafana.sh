#!/bin/bash

echo "Restarting Grafana to apply dashboard provisioning..."

# Stop Grafana
docker-compose -f docker-compose.desktop.yml stop grafana

# Remove Grafana container to ensure clean restart
docker-compose -f docker-compose.desktop.yml rm -f grafana

# Start Grafana with new provisioning
docker-compose -f docker-compose.desktop.yml up -d grafana

echo "Waiting for Grafana to start..."
sleep 10

# Check if Grafana is running
if docker ps | grep -q "stock_monitor_grafana_desktop"; then
    echo "✓ Grafana is running!"
    echo "Access Grafana at: http://localhost:3000"
    echo "Username: admin"
    echo "Password: admin"
    echo ""
    echo "Dashboards should be automatically loaded in the 'Trading & Finance' folder"
    echo "Check: Dashboards → Trading & Finance"
    echo ""
    echo "Ultimate Dashboard will be in: Dashboards → Professional Analytics"
    echo ""
    echo "If dashboards don't appear, check Grafana logs:"
    echo "docker-compose -f docker-compose.desktop.yml logs grafana"
else
    echo "✗ Grafana failed to start. Check logs with:"
    echo "docker-compose -f docker-compose.desktop.yml logs grafana"
fi
