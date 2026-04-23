#!/bin/bash

echo "Fixing InfluxDB Authentication Issues..."

# Check if InfluxDB container is running
if ! docker ps | grep -q "stock_monitor_influxdb"; then
    echo "Error: InfluxDB container is not running!"
    echo "Please start your services first: docker-compose up -d"
    exit 1
fi

echo "Step 1: Stopping InfluxDB container..."
docker stop stock_monitor_influxdb

echo "Step 2: Removing InfluxDB container..."
docker rm stock_monitor_influxdb

echo "Step 3: Starting InfluxDB with proper credentials..."
docker run -d \
  --name stock_monitor_influxdb \
  --network stock_monitor_default \
  -p 8086:8086 \
  -e DOCKER_INFLUXDB_INIT_MODE=setup \
  -e DOCKER_INFLUXDB_INIT_USERNAME=admin \
  -e DOCKER_INFLUXDB_INIT_PASSWORD=your_admin_password \
  -e DOCKER_INFLUXDB_INIT_ORG=stock_monitor \
  -e DOCKER_INFLUXDB_INIT_BUCKET=market_data \
  -e DOCKER_INFLUXDB_INIT_ADMIN_TOKEN=your_influxdb_token_here \
  -v influxdb_data:/var/lib/influxdb2 \
  influxdb:2.7-alpine

echo "Step 4: Waiting for InfluxDB to start..."
sleep 30

echo "Step 5: Testing InfluxDB connection..."
if curl -s http://localhost:8086/health > /dev/null; then
    echo " InfluxDB is responding"
else
    echo " InfluxDB is not responding"
    exit 1
fi

echo "Step 6: Testing authentication..."
if docker exec stock_monitor_influxdb influx org list --token your_influxdb_token_here > /dev/null 2>&1; then
    echo " Authentication successful"
else
    echo " Authentication failed"
    exit 1
fi

echo "Step 7: Listing organizations..."
docker exec stock_monitor_influxdb influx org list --token your_influxdb_token_here

echo "Step 8: Listing buckets..."
docker exec stock_monitor_influxdb influx bucket list --token your_influxdb_token_here

echo ""
echo "=== InfluxDB Authentication Fixed! ==="
echo ""
echo "New Credentials:"
echo "- Username: admin"
echo "- Password: your_admin_password"
echo "- Organization: stock_monitor"
echo "- Token: your_influxdb_token_here"
echo "- Default Bucket: market_data"
echo ""
echo "Next Steps:"
echo "1. Update your Grafana data source configuration"
echo "2. Use the new token: your_influxdb_token_here"
echo "3. Test the connection in Grafana"
echo ""
echo "Your InfluxDB is now properly configured!"
