#!/usr/bin/env python3
"""
InfluxDB Multi-Asset Bucket Setup Script
Creates buckets for stocks, forex, crypto, and commodities data
"""

import requests
import json
import logging
from datetime import datetime, timedelta
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# InfluxDB configuration
INFLUXDB_URL = "http://influxdb:8086"  # Use Docker service name
INFLUXDB_TOKEN = "xEoh_d1wMmj_8sE2ipM1nht5Iq_iJiziHWVGvt9Haplv8QPDuR6oFTRIcX3rT8rG1M6H21tk0sSTv5ujfrPRDg=="
INFLUXDB_ORG = "stock_monitor"

def create_bucket(bucket_name, retention_days=30):
    """Create an InfluxDB bucket"""
    url = f"{INFLUXDB_URL}/api/v2/buckets"
    headers = {
        "Authorization": f"Token {INFLUXDB_TOKEN}",
        "Content-Type": "application/json"
    }
    
    data = {
        "name": bucket_name,
        "org": INFLUXDB_ORG,  # Use 'org' instead of 'orgID'
        "retentionRules": [
            {
                "type": "expire",
                "everySeconds": retention_days * 24 * 3600
            }
        ]
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 201:
            logger.info(f"Bucket '{bucket_name}' created successfully")
            return True
        elif response.status_code == 422 and "already exists" in response.text:
            logger.info(f"Bucket '{bucket_name}' already exists")
            return True
        else:
            logger.error(f"Failed to create bucket '{bucket_name}': {response.status_code} - {response.text}")
            return False
    except Exception as e:
        logger.error(f"Error creating bucket '{bucket_name}': {e}")
        return False

def create_buckets():
    """Create all necessary buckets for multi-asset trading"""
    
    buckets = [
        # Core financial data buckets
        ("financial_data", 90),           # Main bucket for all financial data
        ("stocks_data", 90),              # Stock-specific data
        ("forex_data", 90),               # Forex pair data
        ("crypto_data", 90),              # Cryptocurrency data
        ("commodities_data", 90),         # Commodity data
        
        # High-frequency trading buckets
        ("hft_tick_data", 7),             # High-frequency tick data (7 days retention)
        ("hft_orderbook", 7),             # Order book snapshots
        ("hft_trades", 7),                # Trade executions
        
        # Analytics and derived data
        ("analytics_indicators", 30),     # Technical indicators
        ("risk_metrics", 30),             # Risk calculations
        ("correlation_data", 30),         # Correlation matrices
        ("volatility_data", 30),          # Volatility calculations
        
        # Portfolio and performance
        ("portfolio_positions", 90),      # Portfolio positions
        ("performance_metrics", 90),      # Performance calculations
        ("pnl_data", 90),                 # Profit/Loss data
        
        # Market microstructure
        ("microstructure_features", 7),   # Bid-ask spreads, liquidity metrics
        ("market_regime", 30),            # Market regime classification
        ("order_flow", 7),                # Order flow analysis
        
        # News and sentiment
        ("news_data", 30),                # News articles
        ("sentiment_scores", 30),         # Sentiment analysis
        
        # System monitoring
        ("system_metrics", 7),            # System performance metrics
        ("api_latency", 7),               # API response times
        ("error_logs", 7)                 # Error logging
    ]
    
    logger.info("Creating InfluxDB buckets for multi-asset trading...")
    
    success_count = 0
    for bucket_name, retention_days in buckets:
        if create_bucket(bucket_name, retention_days):
            success_count += 1
        time.sleep(0.1)  # Small delay to avoid overwhelming the API
    
    logger.info(f"Successfully created {success_count}/{len(buckets)} buckets")
    return success_count == len(buckets)

def populate_sample_data():
    """Populate buckets with sample data for testing"""
    
    logger.info("Populating buckets with sample data...")
    
    # Sample data for different asset types
    sample_data = {
        "stocks_data": [
            {
                "measurement": "stock_price",
                "tags": {"symbol": "AAPL", "exchange": "NASDAQ", "asset_type": "stock"},
                "fields": {"price": 150.25, "volume": 1000000, "bid": 150.20, "ask": 150.30},
                "time": datetime.utcnow()
            },
            {
                "measurement": "stock_price",
                "tags": {"symbol": "MSFT", "exchange": "NASDAQ", "asset_type": "stock"},
                "fields": {"price": 280.50, "volume": 800000, "bid": 280.45, "ask": 280.55},
                "time": datetime.utcnow()
            }
        ],
        "forex_data": [
            {
                "measurement": "forex_price",
                "tags": {"symbol": "EUR/USD", "asset_type": "forex"},
                "fields": {"price": 1.0850, "bid": 1.0848, "ask": 1.0852, "spread": 0.0004},
                "time": datetime.utcnow()
            },
            {
                "measurement": "forex_price",
                "tags": {"symbol": "GBP/USD", "asset_type": "forex"},
                "fields": {"price": 1.2650, "bid": 1.2648, "ask": 1.2652, "spread": 0.0004},
                "time": datetime.utcnow()
            }
        ],
        "crypto_data": [
            {
                "measurement": "crypto_price",
                "tags": {"symbol": "BTC/USD", "asset_type": "crypto"},
                "fields": {"price": 45000.00, "volume": 5000, "bid": 44995.00, "ask": 45005.00},
                "time": datetime.utcnow()
            },
            {
                "measurement": "crypto_price",
                "tags": {"symbol": "ETH/USD", "asset_type": "crypto"},
                "fields": {"price": 2800.00, "volume": 15000, "bid": 2798.00, "ask": 2802.00},
                "time": datetime.utcnow()
            }
        ],
        "commodities_data": [
            {
                "measurement": "commodity_price",
                "tags": {"symbol": "XAU/USD", "asset_type": "commodity", "class": "metals"},
                "fields": {"price": 1950.00, "bid": 1949.50, "ask": 1950.50, "spread": 1.00},
                "time": datetime.utcnow()
            },
            {
                "measurement": "commodity_price",
                "tags": {"symbol": "WTI", "asset_type": "commodity", "class": "energy"},
                "fields": {"price": 75.50, "bid": 75.48, "ask": 75.52, "spread": 0.04},
                "time": datetime.utcnow()
            }
        ]
    }
    
    # Write sample data to buckets
    for bucket_name, data_points in sample_data.items():
        logger.info(f"Writing sample data to {bucket_name}...")
        
        # Convert to InfluxDB line protocol format
        lines = []
        for point in data_points:
            tags = ",".join([f"{k}={v}" for k, v in point["tags"].items()])
            fields = ",".join([f"{k}={v}" for k, v in point["fields"].items()])
            timestamp = int(point["time"].timestamp() * 1e9)  # Convert to nanoseconds
            
            line = f"{point['measurement']},{tags} {fields} {timestamp}"
            lines.append(line)
        
        # Write to InfluxDB
        url = f"{INFLUXDB_URL}/api/v2/write"
        headers = {
            "Authorization": f"Token {INFLUXDB_TOKEN}",
            "Content-Type": "text/plain; charset=utf-8"
        }
        params = {
            "org": INFLUXDB_ORG,
            "bucket": bucket_name
        }
        
        try:
            response = requests.post(url, headers=headers, params=params, data="\n".join(lines))
            if response.status_code == 204:
                logger.info(f"Successfully wrote {len(data_points)} data points to {bucket_name}")
            else:
                logger.error(f"Failed to write to {bucket_name}: {response.status_code} - {response.text}")
        except Exception as e:
            logger.error(f"Error writing to {bucket_name}: {e}")

def main():
    """Main function to set up InfluxDB buckets"""
    try:
        logger.info("Starting InfluxDB multi-asset bucket setup...")
        
        # Create buckets
        if create_buckets():
            logger.info("All buckets created successfully!")
            
            # Populate with sample data
            populate_sample_data()
            
            logger.info("InfluxDB setup completed successfully!")
        else:
            logger.error("Failed to create all buckets")
            
    except Exception as e:
        logger.error(f"InfluxDB setup failed: {e}")
        raise

if __name__ == "__main__":
    main()
