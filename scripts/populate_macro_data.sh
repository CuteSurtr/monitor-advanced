#!/bin/bash

echo "Populating InfluxDB macro_data bucket with sample economic data..."

# InfluxDB configuration
INFLUXDB_URL="http://localhost:8086"
ORG="stock_monitor"
BUCKET="macro_data"
TOKEN="trading_token_123"

# Function to write data point
write_data() {
    local measurement=$1
    local tags=$2
    local fields=$3
    local timestamp=$4
    
    local line="${measurement},${tags} ${fields} ${timestamp}"
    
    echo "Writing: $line"
    
    curl -s -X POST "${INFLUXDB_URL}/api/v2/write" \
        -H "Authorization: Token ${TOKEN}" \
        -H "Content-Type: application/octet-stream" \
        -d "$line" \
        --data-urlencode "org=${ORG}" \
        --data-urlencode "bucket=${BUCKET}" \
        --data-urlencode "precision=ns"
    
    if [ $? -eq 0 ]; then
        echo "✓ Successfully wrote ${measurement}"
    else
        echo "✗ Failed to write ${measurement}"
    fi
}

echo "Generating Treasury yield curve data..."

# Generate sample Treasury data for the last 7 days
for i in {0..6}; do
    timestamp=$(date -d "$i days ago" +%s)000000000
    
    # 10Y Treasury yield
    write_data "treasury_yield_curve" "maturity=10Y,security_type=treasury" "yield=4.2" "$timestamp"
    
    # 2Y Treasury yield
    write_data "treasury_yield_curve" "maturity=2Y,security_type=treasury" "yield=4.8" "$timestamp"
    
    # 30Y Treasury yield
    write_data "treasury_yield_curve" "maturity=30Y,security_type=treasury" "yield=4.5" "$timestamp"
done

echo "Generating economic indicators..."

# Generate CPI data
for i in {0..6}; do
    timestamp=$(date -d "$i days ago" +%s)000000000
    cpi_value=$(echo "3.2 + $RANDOM * 0.1 / 32767" | bc -l | cut -c1-4)
    write_data "bls_economic_data" "indicator=cpi,category=inflation" "value=$cpi_value" "$timestamp"
done

# Generate unemployment data
for i in {0..6}; do
    timestamp=$(date -d "$i days ago" +%s)000000000
    unemployment=$(echo "3.8 + $RANDOM * 0.1 / 32767" | bc -l | cut -c1-4)
    write_data "bls_economic_data" "indicator=unemployment_rate,category=labor" "value=$unemployment" "$timestamp"
done

echo "Generating energy data..."

# Generate oil price data
for i in {0..6}; do
    timestamp=$(date -d "$i days ago" +%s)000000000
    oil_price=$(echo "75.0 + $RANDOM * 10.0 / 32767" | bc -l | cut -c1-6)
    write_data "eia_energy_data" "commodity=crude_oil,unit=usd_per_barrel" "value=$oil_price" "$timestamp"
done

echo "Generating financial market data..."

# Generate VIX data
for i in {0..6}; do
    timestamp=$(date -d "$i days ago" +%s)000000000
    vix_value=$(echo "20.0 + $RANDOM * 15.0 / 32767" | bc -l | cut -c1-5)
    write_data "fred_economic_data" "indicator=vix,category=volatility" "value=$vix_value" "$timestamp"
done

# Generate Fed funds rate data
for i in {0..6}; do
    timestamp=$(date -d "$i days ago" +%s)000000000
    fed_rate=$(echo "5.25 + $RANDOM * 0.2 / 32767" | bc -l | cut -c1-5)
    write_data "fred_economic_data" "indicator=fed_funds_rate,category=monetary_policy" "value=$fed_rate" "$timestamp"
done

echo ""
echo "=== Sample data population complete! ==="
echo "Bucket: $BUCKET"
echo "Organization: $ORG"
echo ""
echo "Your Comprehensive Economic Dashboard should now work."
echo "Check Grafana to see the data."


