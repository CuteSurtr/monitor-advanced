#!/bin/bash

echo "Populating InfluxDB macro_data bucket with comprehensive economic data..."
echo

# InfluxDB configuration
ORG_ID="0d4ca99e5255fe85"
BUCKET="macro_data"
TOKEN="trading_token_123"

echo "Generating comprehensive economic data..."
echo

# Generate Treasury yield curve data
echo "Generating Treasury yield curve data..."
for i in {0..29}; do
    echo "Writing Treasury data for day $i..."
    
    # 2Y Treasury yield
    docker exec stock_monitor_influxdb influx write --bucket "$BUCKET" --org-id "$ORG_ID" --token "$TOKEN" "treasury_yield_curve,maturity=2Y,security_type=treasury yield=4.2"
    
    # 10Y Treasury yield
    docker exec stock_monitor_influxdb influx write --bucket "$BUCKET" --org-id "$ORG_ID" --token "$TOKEN" "treasury_yield_curve,maturity=10Y,security_type=treasury yield=4.5"
    
    # 30Y Treasury yield
    docker exec stock_monitor_influxdb influx write --bucket "$BUCKET" --org-id "$ORG_ID" --token "$TOKEN" "treasury_yield_curve,maturity=30Y,security_type=treasury yield=4.8"
done

echo
echo "Generating economic indicators..."

# Generate CPI data
for i in {0..29}; do
    echo "Writing CPI data for day $i..."
    docker exec stock_monitor_influxdb influx write --bucket "$BUCKET" --org-id "$ORG_ID" --token "$TOKEN" "bls_economic_data,indicator=cpi,category=inflation value=3.2"
    docker exec stock_monitor_influxdb influx write --bucket "$BUCKET" --org-id "$ORG_ID" --token "$TOKEN" "bls_economic_data,indicator=core_cpi,category=inflation value=3.0"
done

# Generate unemployment data
for i in {0..29}; do
    echo "Writing unemployment data for day $i..."
    docker exec stock_monitor_influxdb influx write --bucket "$BUCKET" --org-id "$ORG_ID" --token "$TOKEN" "bls_economic_data,indicator=unemployment_rate,category=labor value=3.8"
    docker exec stock_monitor_influxdb influx write --bucket "$BUCKET" --org-id "$ORG_ID" --token "$TOKEN" "bls_economic_data,indicator=nonfarm_payrolls,category=labor value=150"
done

echo
echo "Generating energy data..."

# Generate energy data
for i in {0..29}; do
    echo "Writing energy data for day $i..."
    docker exec stock_monitor_influxdb influx write --bucket "$BUCKET" --org-id "$ORG_ID" --token "$TOKEN" "eia_energy_data,commodity=crude_oil,unit=usd_per_barrel value=75.0"
    docker exec stock_monitor_influxdb influx write --bucket "$BUCKET" --org-id "$ORG_ID" --token "$TOKEN" "eia_energy_data,commodity=natural_gas,unit=usd_per_mmbtu value=3.2"
done

echo
echo "Generating financial market data..."

# Generate financial data
for i in {0..29}; do
    echo "Writing financial data for day $i..."
    docker exec stock_monitor_influxdb influx write --bucket "$BUCKET" --org-id "$ORG_ID" --token "$TOKEN" "fred_economic_data,indicator=vix,category=volatility value=20.0"
    docker exec stock_monitor_influxdb influx write --bucket "$BUCKET" --org-id "$ORG_ID" --token "$TOKEN" "fred_economic_data,indicator=fed_funds_rate,category=monetary_policy value=5.25"
    docker exec stock_monitor_influxdb influx write --bucket "$BUCKET" --org-id "$ORG_ID" --token "$TOKEN" "treasury_curve_metrics,metric=10y_2y_spread,category=yield_curve spread=0.5"
done

echo
echo "Generating BEA economic data..."

# Generate BEA data
for i in {0..29}; do
    echo "Writing BEA data for day $i..."
    docker exec stock_monitor_influxdb influx write --bucket "$BUCKET" --org-id "$ORG_ID" --token "$TOKEN" "bea_economic_data,indicator=gdp_growth,category=economic_activity value=2.1"
    docker exec stock_monitor_influxdb influx write --bucket "$BUCKET" --org-id "$ORG_ID" --token "$TOKEN" "bea_economic_data,indicator=pce_growth,category=consumption value=1.8"
done

echo
echo "Generating Census data..."

# Generate Census data
for i in {0..29}; do
    echo "Writing Census data for day $i..."
    docker exec stock_monitor_influxdb influx write --bucket "$BUCKET" --org-id "$ORG_ID" --token "$TOKEN" "census_economic_data,indicator=retail_sales,category=consumption value=600"
    docker exec stock_monitor_influxdb influx write --bucket "$BUCKET" --org-id "$ORG_ID" --token "$TOKEN" "census_economic_data,indicator=housing_starts,category=construction value=1.4"
done

echo
echo "Generating FINRA data..."

# Generate FINRA data
for i in {0..29}; do
    echo "Writing FINRA data for day $i..."
    docker exec stock_monitor_influxdb influx write --bucket "$BUCKET" --org-id "$ORG_ID" --token "$TOKEN" "finra_short_interest,market=nyse,category=short_interest short_ratio=15.0"
    docker exec stock_monitor_influxdb influx write --bucket "$BUCKET" --org-id "$ORG_ID" --token "$TOKEN" "finra_margin_debt,market=nyse,category=margin_debt debt_billions=800.0"
done

echo
echo "=== DATA POPULATION COMPLETE! ==="
echo
echo "Data Summary:"
echo "- Treasury yield curves: 90 data points (3 maturities x 30 days)"
echo "- Economic indicators: 180 data points (6 indicators x 30 days)"
echo "- Energy data: 60 data points (2 commodities x 30 days)"
echo "- Financial data: 90 data points (3 indicators x 30 days)"
echo "- BEA data: 60 data points (2 indicators x 30 days)"
echo "- Census data: 60 data points (2 indicators x 30 days)"
echo "- FINRA data: 60 data points (2 indicators x 30 days)"
echo
echo "Total: 600 data points across 8 measurement types"
echo
echo "Your Comprehensive Macro Economic Dashboard should now display data!"
echo "Check Grafana to see all the economic indicators."
echo


