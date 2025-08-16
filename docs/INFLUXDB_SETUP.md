# InfluxDB Setup Guide for Financial Analytics Dashboard

## Quick Setup Instructions

### 1. Install InfluxDB (if not already installed)
```bash
# Download and install InfluxDB v2.x from:
# https://docs.influxdata.com/influxdb/v2.0/install/
```

### 2. Start InfluxDB and Get Your Token
1. Start InfluxDB service
2. Go to http://localhost:8086
3. Create an organization (e.g., "financial-org")  
4. Create a bucket called `financial_data`
5. Generate an API token and copy it

### 3. Option A: Manual Bucket Creation (Quick)
1. In InfluxDB UI, create a bucket named: `financial_data`
2. Use the simple dashboard: `influxdb-simple-financial.json`
3. The dashboard will show "No Data" until you populate it

### 4. Option B: Automated Setup with Sample Data (Recommended)

#### Update the Python script:
Edit `scripts/setup_influxdb_buckets.py`:
```python
INFLUXDB_URL = "http://localhost:8086"
INFLUXDB_TOKEN = "your-actual-token-here"  # Replace with your token
INFLUXDB_ORG = "your-actual-org"           # Replace with your org name
```

#### Install Python dependencies:
```bash
pip install influxdb-client
```

#### Run the setup script:
```bash
cd scripts
python setup_influxdb_buckets.py
```

This will create:
- ✅ `financial_data` bucket
- 📈 72 hours of stock price data (AAPL, MSFT, GOOGL, etc.)
- 💰 Portfolio performance metrics
- ⚡ High-frequency tick data
- 📊 Market metrics (volatility, RSI)

### 5. Configure Grafana InfluxDB Datasource

1. Go to Grafana → Configuration → Data Sources
2. Add InfluxDB datasource with:
   - **URL**: `http://localhost:8086`
   - **Organization**: `your-org`
   - **Token**: `your-token`
   - **Default Bucket**: `financial_data`

### 6. Import the Dashboard

Choose one of these dashboards:

#### Simple Dashboard (Recommended for testing):
- File: `influxdb-simple-financial.json`
- Basic queries that work immediately
- Shows: Stock prices, volume, volatility, portfolio metrics

#### Advanced Dashboard (Full features):
- File: `influxdb-financial-analytics.json`  
- Complex analytics and joins
- Shows: VWAP, anomaly detection, advanced metrics

## Sample Data Structure

The setup script creates these measurements:

### `stock_prices`
- **Tags**: `symbol` (AAPL, MSFT, etc.)
- **Fields**: `open`, `high`, `low`, `close`, `volume`
- **Frequency**: Every minute

### `market_metrics`  
- **Tags**: `symbol`
- **Fields**: `volatility`, `price_change`, `rsi`
- **Frequency**: Every minute

### `portfolio_performance`
- **Tags**: `portfolio_id`
- **Fields**: `total_value`, `total_return`, `daily_return`, `cash_position`
- **Frequency**: Every 5 minutes

### `portfolio_holdings`
- **Tags**: `portfolio_id`, `asset_class`
- **Fields**: `market_value`, `weight`
- **Frequency**: Every 5 minutes

### `tick_data`
- **Tags**: `symbol`  
- **Fields**: `price`, `volume`, `bid`, `ask`
- **Frequency**: Every 10 seconds (high-frequency)

## Troubleshooting

### No Data Showing?
1. Check InfluxDB connection in Grafana
2. Verify bucket name is `financial_data`
3. Check if data exists: `influx query 'from(bucket:"financial_data") |> range(start:-1h) |> limit(n:10)'`

### Permission Errors?
1. Verify your InfluxDB token has read/write access
2. Check organization name matches exactly

### Want More Data?
Edit the Python script and modify:
```python
generate_stock_prices(client, hours_back=168)  # 1 week of data
```

## Next Steps

1. ✅ Import the simple dashboard first to verify connection
2. 🔧 Customize queries for your specific needs
3. 📊 Add more measurements for additional financial metrics
4. ⚡ Set up real-time data ingestion pipelines

## Advanced Features Available

- 📈 **Window Functions**: Rolling averages, volatility calculations
- 🔗 **Cross-Measurement Joins**: Correlate volume with volatility  
- 🎯 **Anomaly Detection**: Z-score based outlier detection
- ⚡ **High-Frequency Analytics**: Tick-by-tick analysis
- 📊 **Portfolio Analytics**: Real-time performance tracking