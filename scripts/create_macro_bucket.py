#!/usr/bin/env python3
"""
Create the macro_data bucket and populate it with data
"""

import requests
import json
from datetime import datetime, timedelta
import random

INFLUXDB_URL = "http://localhost:8086"
TOKEN = "macro_dashboard_token_2025"
ORG = "stock_monitor"

def create_bucket(bucket_name):
    """Create a new bucket in InfluxDB"""
    
    # Get org ID first
    headers = {"Authorization": f"Token {TOKEN}"}
    
    try:
        response = requests.get(f"{INFLUXDB_URL}/api/v2/orgs", headers=headers, timeout=10)
        if response.status_code != 200:
            print(f"Failed to get orgs: {response.status_code}")
            return False
            
        orgs = response.json().get("orgs", [])
        org_id = None
        for org in orgs:
            if org.get("name") == ORG:
                org_id = org.get("id")
                break
                
        if not org_id:
            print("Could not find organization")
            return False
            
        # Create bucket
        bucket_data = {
            "name": bucket_name,
            "orgID": org_id,
            "retentionRules": [{"type": "expire", "everySeconds": 0}]  # No expiration
        }
        
        response = requests.post(f"{INFLUXDB_URL}/api/v2/buckets", 
                               json=bucket_data, headers=headers, timeout=10)
        
        if response.status_code == 201:
            print(f"Created bucket: {bucket_name}")
            return True
        elif response.status_code == 422:
            print(f"Bucket already exists: {bucket_name}")
            return True
        else:
            print(f"Failed to create bucket: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"Error creating bucket: {e}")
        return False

def populate_macro_data():
    """Populate the macro_data bucket with sample data"""
    
    headers = {
        "Authorization": f"Token {TOKEN}",
        "Content-Type": "text/plain; charset=utf-8"
    }
    
    # Generate comprehensive macro data
    base_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    data_lines = []
    
    # Generate data for the last 90 days
    for i in range(90):
        timestamp = int((base_time - timedelta(days=i)).timestamp())
        
        # Treasury yields
        data_lines.extend([
            f"treasury_yields,maturity=3M,country=US yield={5.3 + random.uniform(-0.2, 0.2)} {timestamp}",
            f"treasury_yields,maturity=2Y,country=US yield={4.8 + random.uniform(-0.2, 0.2)} {timestamp}",
            f"treasury_yields,maturity=10Y,country=US yield={4.2 + random.uniform(-0.2, 0.2)} {timestamp}",
            f"treasury_yields,maturity=30Y,country=US yield={4.5 + random.uniform(-0.2, 0.2)} {timestamp}",
        ])
        
        # Economic indicators
        data_lines.extend([
            f"economic_indicators,indicator=CPI,frequency=monthly value={3.2 + random.uniform(-0.3, 0.3)},yoy_change={3.1 + random.uniform(-0.5, 0.5)} {timestamp}",
            f"economic_indicators,indicator=unemployment,frequency=monthly value={3.8 + random.uniform(-0.2, 0.2)},change={random.uniform(-0.2, 0.2)} {timestamp}",
            f"economic_indicators,indicator=GDP,frequency=quarterly value={2.1 + random.uniform(-0.5, 0.5)},annualized={2.0 + random.uniform(-0.5, 0.5)} {timestamp}",
            f"economic_indicators,indicator=retail_sales,frequency=monthly value={random.uniform(-2.0, 4.0)},mom_change={random.uniform(-1.0, 2.0)} {timestamp}",
            f"economic_indicators,indicator=industrial_production,frequency=monthly value={random.uniform(-1.0, 3.0)},mom_change={random.uniform(-0.5, 1.0)} {timestamp}",
        ])
        
        # Market sentiment
        vix = 15.0 + random.uniform(-3.0, 8.0)
        dxy = 104.0 + random.uniform(-2.0, 2.0)
        gold = 2020.0 + random.uniform(-50.0, 50.0)
        
        data_lines.extend([
            f"market_sentiment,indicator=VIX,market=equity value={vix} {timestamp}",
            f"market_sentiment,indicator=DXY,market=currency value={dxy} {timestamp}",
            f"market_sentiment,indicator=gold,market=commodity value={gold} {timestamp}",
            f"market_sentiment,indicator=oil,market=commodity value={80.0 + random.uniform(-10.0, 15.0)} {timestamp}",
        ])
        
        # Central bank rates
        data_lines.extend([
            f"central_bank_rates,bank=FED,rate_type=fed_funds rate={5.25 + random.uniform(-0.1, 0.1)} {timestamp}",
            f"central_bank_rates,bank=ECB,rate_type=deposit rate={4.0 + random.uniform(-0.1, 0.1)} {timestamp}",
            f"central_bank_rates,bank=BOJ,rate_type=policy rate={-0.1 + random.uniform(-0.05, 0.05)} {timestamp}",
        ])
        
        # Yield curve metrics
        spread_10_2 = (4.2 + random.uniform(-0.2, 0.2)) - (4.8 + random.uniform(-0.2, 0.2))
        data_lines.append(f"yield_curve_metrics,spread=10Y-2Y value={spread_10_2} {timestamp}")
        
        # Financial conditions
        data_lines.extend([
            f"financial_conditions,indicator=credit_spreads,market=corporate value={120 + random.uniform(-20, 30)} {timestamp}",
            f"financial_conditions,indicator=term_premium,market=treasury value={0.5 + random.uniform(-0.3, 0.3)} {timestamp}",
        ])
    
    # Write all data
    line_protocol = "\n".join(data_lines)
    
    try:
        response = requests.post(
            f"{INFLUXDB_URL}/api/v2/write",
            params={"org": ORG, "bucket": "macro_data", "precision": "s"},
            headers=headers,
            data=line_protocol,
            timeout=30
        )
        
        if response.status_code == 204:
            print(f"Successfully wrote {len(data_lines)} data points to macro_data bucket")
            return True
        else:
            print(f"Failed to write data: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"Error writing data: {e}")
        return False

def main():
    print("Creating macro_data bucket and populating with data")
    print("=" * 50)
    
    # Create the bucket
    if create_bucket("macro_data"):
        print("Bucket creation successful")
    else:
        print("Bucket creation failed")
        return
        
    # Populate with data
    if populate_macro_data():
        print("\nSUCCESS: macro_data bucket is ready!")
        print("\nYour dashboard should now work. Try refreshing the Grafana dashboard.")
    else:
        print("Failed to populate data")

if __name__ == "__main__":
    main()