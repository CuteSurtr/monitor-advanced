#!/usr/bin/env python3
"""
Simple InfluxDB Setup for Ultimate Professional Trading Dashboard
This script creates sample data to make your dashboard work immediately
"""

import random
from datetime import datetime, timedelta

# Install required packages
try:
    from influxdb_client import InfluxDBClient, Point, WritePrecision
    from influxdb_client.client.write_api import SYNCHRONOUS
except ImportError:
    print("Installing required packages...")
    import subprocess
    subprocess.check_call(["pip", "install", "influxdb-client"])
    from influxdb_client import InfluxDBClient, Point, WritePrecision
    from influxdb_client.client.write_api import SYNCHRONOUS

def create_sample_data():
    """Create sample data for all dashboard panels"""
    
    # Configuration - UPDATED WITH YOUR CREDENTIALS
    INFLUXDB_URL = "http://localhost:8086"  # Your InfluxDB URL
    INFLUXDB_TOKEN = "xEoh_d1wMmj_8sE2ipM1nht5Iq_iJiziHWVGvt9Haplv8QPDuR6oFTRIcX3rT8rG1M6H21tk0sSTv5ujfrPRDg=="
    INFLUXDB_ORG = "deuydarcrp81sf"
    BUCKET_NAME = "trading_metrics"
    
    print("🎯 Setting up InfluxDB data for your dashboard...")
    print(f"📡 Connecting to: {INFLUXDB_URL}")
    
    # Create client
    client = InfluxDBClient(
        url=INFLUXDB_URL,
        token=INFLUXDB_TOKEN,
        org=INFLUXDB_ORG
    )
    
    try:
        # Test connection
        health = client.health()
        print(f"✅ Connected to InfluxDB: {health.message}")
        
        # Create bucket if it doesn't exist
        buckets_api = client.buckets_api()
        existing_buckets = [bucket.name for bucket in buckets_api.find_buckets()]
        
        if BUCKET_NAME not in existing_buckets:
            buckets_api.create_bucket(bucket_name=BUCKET_NAME, org=INFLUXDB_ORG)
            print(f"✅ Created bucket: {BUCKET_NAME}")
        else:
            print(f"✅ Bucket {BUCKET_NAME} already exists")
        
        # Create write API
        write_api = client.write_api(write_options=SYNCHRONOUS)
        
        # Generate 24 hours of sample data
        base_time = datetime.utcnow() - timedelta(hours=24)
        all_points = []
        
        print("📊 Generating sample data...")
        
        # Portfolio Performance Data
        for i in range(24):
            timestamp = base_time + timedelta(hours=i)
            
            all_points.append(Point("portfolio_performance")
                .tag("metric", "total_value")
                .field("value", 1000000 + random.uniform(-50000, 100000))
                .time(timestamp, WritePrecision.NS))
                
            all_points.append(Point("portfolio_performance")
                .tag("metric", "daily_pnl")
                .field("value", random.uniform(-50000, 100000))
                .time(timestamp, WritePrecision.NS))
        
        # Stock Prices
        symbols = ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA"]
        for symbol in symbols:
            base_price = random.uniform(100, 500)
            for i in range(24):
                timestamp = base_time + timedelta(hours=i)
                price_change = random.uniform(-0.02, 0.02)
                base_price *= (1 + price_change)
                
                all_points.append(Point("stock_prices")
                    .tag("symbol", symbol)
                    .field("close", base_price)
                    .field("volume", random.randint(1000000, 10000000))
                    .time(timestamp, WritePrecision.NS))
        
        # ML Metrics
        models = ["LSTM_Price", "RandomForest", "XGBoost"]
        for model in models:
            for i in range(24):
                timestamp = base_time + timedelta(hours=i)
                
                all_points.append(Point("ml_metrics")
                    .tag("model_name", model)
                    .field("accuracy", random.uniform(0.75, 0.95))
                    .field("precision", random.uniform(0.70, 0.90))
                    .field("recall", random.uniform(0.65, 0.85))
                    .field("confidence_score", random.uniform(0.60, 0.95))
                    .time(timestamp, WritePrecision.NS))
        
        # Risk Metrics
        for i in range(24):
            timestamp = base_time + timedelta(hours=i)
            
            all_points.append(Point("risk_metrics")
                .field("var_95", random.uniform(-150000, -50000))
                .field("cvar_95", random.uniform(-200000, -75000))
                .field("max_drawdown", random.uniform(-0.25, -0.05))
                .field("sharpe_ratio", random.uniform(0.5, 2.5))
                .time(timestamp, WritePrecision.NS))
        
        # Market Sentiment
        for i in range(24):
            timestamp = base_time + timedelta(hours=i)
            
            all_points.append(Point("market_sentiment")
                .field("sentiment_score", random.uniform(-1.0, 1.0))
                .field("fear_greed_index", random.uniform(0.0, 1.0))
                .field("news_sentiment", random.uniform(-0.8, 0.8))
                .time(timestamp, WritePrecision.NS))
        
        # Volatility Data
        for symbol in ["AAPL", "MSFT"]:
            for i in range(24):
                timestamp = base_time + timedelta(hours=i)
                
                all_points.append(Point("volatility")
                    .tag("symbol", symbol)
                    .field("realized_vol", random.uniform(0.15, 0.45))
                    .field("garch_forecast", random.uniform(0.20, 0.50))
                    .field("implied_vol", random.uniform(0.18, 0.48))
                    .time(timestamp, WritePrecision.NS))
        
        # HFT Metrics
        for symbol in ["AAPL", "MSFT"]:
            for i in range(24):
                timestamp = base_time + timedelta(hours=i)
                
                all_points.append(Point("hft_metrics")
                    .tag("symbol", symbol)
                    .field("bid_ask_spread", random.uniform(0.01, 0.50))
                    .field("order_flow_imbalance", random.uniform(-0.8, 0.8))
                    .field("trade_intensity", random.uniform(100, 1000))
                    .time(timestamp, WritePrecision.NS))
        
        # Correlations
        asset_pairs = ["AAPL_MSFT", "AAPL_GOOGL", "MSFT_GOOGL"]
        for pair in asset_pairs:
            timestamp = base_time + timedelta(hours=23)
            
            all_points.append(Point("correlations")
                .tag("asset_pair", pair)
                .field("correlation", random.uniform(-0.3, 0.9))
                .time(timestamp, WritePrecision.NS))
        
        # Market Regime
        for i in range(24):
            timestamp = base_time + timedelta(hours=i)
            
            all_points.append(Point("market_regime")
                .field("regime_state", random.randint(1, 4))
                .field("trend_strength", random.uniform(0.0, 1.0))
                .field("momentum_score", random.uniform(-1.0, 1.0))
                .time(timestamp, WritePrecision.NS))
        
        # Options Chain
        strikes = [150, 160, 170, 180, 190]
        for strike in strikes:
            timestamp = base_time + timedelta(hours=23)
            
            all_points.append(Point("options_chain")
                .tag("strike_price", str(strike))
                .field("delta", random.uniform(-1.0, 1.0))
                .field("gamma", random.uniform(0.0, 0.1))
                .field("theta", random.uniform(-0.5, 0.0))
                .field("vega", random.uniform(0.0, 0.3))
                .time(timestamp, WritePrecision.NS))
        
        # VIX Data
        for i in range(24):
            timestamp = base_time + timedelta(hours=i)
            
            all_points.append(Point("vix_data")
                .field("vix_value", random.uniform(15.0, 35.0))
                .field("fear_greed_index", random.uniform(0.0, 1.0))
                .field("volatility_forecast", random.uniform(18.0, 40.0))
                .time(timestamp, WritePrecision.NS))
        
        # Portfolio Allocation
        asset_classes = ["stocks", "bonds", "crypto", "commodities", "forex"]
        for asset_class in asset_classes:
            timestamp = base_time + timedelta(hours=23)
            
            all_points.append(Point("portfolio_allocation")
                .tag("asset_class", asset_class)
                .field("allocation_percentage", random.uniform(0.05, 0.40))
                .field("total_value", random.uniform(50000, 400000))
                .time(timestamp, WritePrecision.NS))
        
        # Order Flow
        for symbol in ["AAPL", "MSFT", "TSLA"]:
            for i in range(24):
                timestamp = base_time + timedelta(hours=i)
                
                all_points.append(Point("order_flow")
                    .tag("symbol", symbol)
                    .field("buy_volume", random.uniform(1000000, 5000000))
                    .field("sell_volume", random.uniform(1000000, 5000000))
                    .field("imbalance_ratio", random.uniform(-0.5, 0.5))
                    .time(timestamp, WritePrecision.NS))
        
        # Anomaly Detection
        for symbol in ["AAPL", "MSFT", "GOOGL", "TSLA"]:
            timestamp = base_time + timedelta(hours=23)
            
            all_points.append(Point("anomaly_detection")
                .tag("symbol", symbol)
                .field("anomaly_score", random.uniform(0.0, 1.0))
                .field("confidence", random.uniform(0.6, 0.95))
                .field("severity", random.choice(["low", "medium", "high"]))
                .field("alert_type", random.choice(["price_spike", "volume_surge", "correlation_break"]))
                .time(timestamp, WritePrecision.NS))
        
        # ML Performance
        models = ["LSTM_v1", "RandomForest_v2", "XGBoost_v3"]
        for model in models:
            timestamp = base_time + timedelta(hours=23)
            
            all_points.append(Point("ml_performance")
                .tag("model_name", model)
                .field("accuracy", random.uniform(0.75, 0.95))
                .field("f1_score", random.uniform(0.70, 0.90))
                .field("drift_score", random.uniform(0.0, 0.3))
                .field("data_quality", random.uniform(0.8, 1.0))
                .time(timestamp, WritePrecision.NS))
        
        # Stress Testing
        for i in range(24):
            timestamp = base_time + timedelta(hours=i)
            
            all_points.append(Point("stress_testing")
                .field("scenario_1", random.uniform(-100000, -50000))
                .field("scenario_2", random.uniform(-150000, -75000))
                .field("scenario_3", random.uniform(-200000, -100000))
                .field("worst_case", random.uniform(-300000, -150000))
                .time(timestamp, WritePrecision.NS))
        
        # Liquidity Metrics
        for symbol in ["AAPL", "MSFT", "TSLA"]:
            for i in range(24):
                timestamp = base_time + timedelta(hours=i)
                
                all_points.append(Point("liquidity_metrics")
                    .tag("symbol", symbol)
                    .field("bid_depth", random.uniform(1000000, 5000000))
                    .field("ask_depth", random.uniform(1000000, 5000000))
                    .field("spread_width", random.uniform(0.01, 0.50))
                    .field("volume_profile", random.uniform(5000000, 20000000))
                    .time(timestamp, WritePrecision.NS))
        
        # Market Timing
        for symbol in ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA"]:
            timestamp = base_time + timedelta(hours=23)
            
            all_points.append(Point("market_timing")
                .tag("symbol", symbol)
                .field("signal_strength", random.uniform(0.0, 1.0))
                .field("confidence", random.uniform(0.6, 0.95))
                .field("action", random.choice(["buy", "sell", "hold"]))
                .field("target_price", random.uniform(100, 500))
                .time(timestamp, WritePrecision.NS))
        
        # Write all data to InfluxDB
        print(f"💾 Writing {len(all_points)} data points to InfluxDB...")
        write_api.write(bucket=BUCKET_NAME, record=all_points)
        
        print("✅ All data populated successfully!")
        print("\n🎉 Your dashboard should now show data!")
        print("📋 Next steps:")
        print("1. Refresh your Grafana dashboard")
        print("2. All panels should now display sample data")
        print("3. The data will refresh every 5 seconds")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n🔧 Troubleshooting:")
        print("1. Make sure InfluxDB is running")
        print("2. Check your InfluxDB URL, token, and organization")
        print("3. Verify network connectivity")
        
    finally:
        client.close()

if __name__ == "__main__":
    print("🎯 Ultimate Professional Trading Dashboard - InfluxDB Setup")
    print("=" * 60)
    print("⚠️  IMPORTANT: Update the configuration values in this script first!")
    print("   - INFLUXDB_URL: Your InfluxDB server URL")
    print("   - INFLUXDB_TOKEN: Your InfluxDB API token")
    print("   - INFLUXDB_ORG: Your InfluxDB organization")
    print("=" * 60)
    
    # Ask user if they want to proceed
    response = input("\nHave you updated the configuration? (y/n): ")
    if response.lower() == 'y':
        create_sample_data()
    else:
        print("Please update the configuration and run again.")
