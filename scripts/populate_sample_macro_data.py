#!/usr/bin/env python3
"""
Populate sample macro economic data into InfluxDB
"""

import requests
import json
from datetime import datetime, timedelta
import random

INFLUXDB_URL = "http://localhost:8086"
TOKEN = "macro_dashboard_token_2025"
ORG = "stock_monitor"
BUCKET = "market_data"

def write_data_points(measurement, data_points):
    """Write data points to InfluxDB"""
    
    headers = {
        "Authorization": f"Token {TOKEN}",
        "Content-Type": "text/plain; charset=utf-8"
    }
    
    # Convert data points to line protocol
    lines = []
    for point in data_points:
        timestamp = point["timestamp"]
        tags = ",".join([f"{k}={v}" for k, v in point.get("tags", {}).items()])
        fields = ",".join([f"{k}={v}" for k, v in point["fields"].items()])
        
        line = f"{measurement}"
        if tags:
            line += f",{tags}"
        line += f" {fields} {timestamp}"
        lines.append(line)
    
    line_protocol = "\n".join(lines)
    
    try:
        response = requests.post(
            f"{INFLUXDB_URL}/api/v2/write",
            params={"org": ORG, "bucket": BUCKET, "precision": "s"},
            headers=headers,
            data=line_protocol,
            timeout=10
        )
        
        if response.status_code == 204:
            print(f"Wrote {len(data_points)} points for {measurement}")
            return True
        else:
            print(f"Failed to write {measurement}: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"Error writing {measurement}: {e}")
        return False

def generate_sample_data():
    """Generate sample macro economic data"""
    
    print("Generating sample macro economic data...")
    
    # Generate data for the last 30 days
    base_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    # 1. Treasury Yield Curve Data
    treasury_data = []
    for i in range(30):
        timestamp = int((base_time - timedelta(days=i)).timestamp())
        
        # Sample yield curve (inverted scenario)
        yields = {
            "3m": 5.3 + random.uniform(-0.1, 0.1),
            "2y": 4.8 + random.uniform(-0.1, 0.1), 
            "10y": 4.2 + random.uniform(-0.1, 0.1),
            "30y": 4.5 + random.uniform(-0.1, 0.1)
        }
        
        for maturity, rate in yields.items():
            treasury_data.append({
                "timestamp": timestamp,
                "tags": {"maturity": maturity, "country": "US"},
                "fields": {"yield": rate}
            })
    
    write_data_points("treasury_yields", treasury_data)
    
    # 2. Economic Indicators
    economic_data = []
    for i in range(30):
        timestamp = int((base_time - timedelta(days=i)).timestamp())
        
        # Sample economic indicators
        economic_data.extend([
            {
                "timestamp": timestamp,
                "tags": {"indicator": "CPI", "period": "monthly"},
                "fields": {"value": 3.2 + random.uniform(-0.2, 0.2), "yoy_change": 3.1}
            },
            {
                "timestamp": timestamp,
                "tags": {"indicator": "unemployment", "period": "monthly"},
                "fields": {"value": 3.8 + random.uniform(-0.1, 0.1), "change": -0.1}
            },
            {
                "timestamp": timestamp,
                "tags": {"indicator": "GDP", "period": "quarterly"},
                "fields": {"value": 2.1 + random.uniform(-0.2, 0.2), "annualized": 2.0}
            }
        ])
    
    write_data_points("economic_indicators", economic_data)
    
    # 3. Market Sentiment Data
    sentiment_data = []
    for i in range(30):
        timestamp = int((base_time - timedelta(days=i)).timestamp())
        
        sentiment_data.extend([
            {
                "timestamp": timestamp,
                "tags": {"indicator": "VIX", "market": "equity"},
                "fields": {"value": 15.0 + random.uniform(-3.0, 8.0)}
            },
            {
                "timestamp": timestamp,
                "tags": {"indicator": "DXY", "market": "currency"},
                "fields": {"value": 104.0 + random.uniform(-2.0, 2.0)}
            },
            {
                "timestamp": timestamp,
                "tags": {"indicator": "gold", "market": "commodity"},
                "fields": {"value": 2020.0 + random.uniform(-50.0, 50.0)}
            }
        ])
    
    write_data_points("market_sentiment", sentiment_data)
    
    # 4. Central Bank Data
    cb_data = []
    for i in range(30):
        timestamp = int((base_time - timedelta(days=i)).timestamp())
        
        cb_data.extend([
            {
                "timestamp": timestamp,
                "tags": {"bank": "FED", "rate_type": "fed_funds"},
                "fields": {"rate": 5.25 + random.uniform(-0.05, 0.05)}
            },
            {
                "timestamp": timestamp,
                "tags": {"bank": "ECB", "rate_type": "deposit"},
                "fields": {"rate": 4.0 + random.uniform(-0.05, 0.05)}
            }
        ])
    
    write_data_points("central_bank_rates", cb_data)

def main():
    print("Populating InfluxDB with sample macro economic data")
    print("=" * 50)
    
    # Test connection first
    try:
        response = requests.get(
            f"{INFLUXDB_URL}/api/v2/orgs",
            headers={"Authorization": f"Token {TOKEN}"},
            timeout=5
        )
        
        if response.status_code == 200:
            print("InfluxDB connection successful")
        else:
            print(f"InfluxDB connection failed: {response.status_code}")
            return
            
    except Exception as e:
        print(f"Connection error: {e}")
        return
    
    # Generate and write sample data
    generate_sample_data()
    
    print("\nSample macro economic data populated!")
    print("\nNext steps:")
    print("1. Open Grafana: http://localhost:3000")
    print("2. Check the InfluxDB datasource connection")
    print("3. View your macro economic dashboard")

if __name__ == "__main__":
    main()