#!/usr/bin/env python3
"""
Check actual InfluxDB data structure to fix missing panels
"""

import requests

INFLUXDB_URL = "http://localhost:8086"
TOKEN = "macro_dashboard_token_2025"
ORG = "stock_monitor"
BUCKET = "macro_data"

def check_measurements():
    """Check all measurements in the bucket"""
    
    headers = {
        "Authorization": f"Token {TOKEN}",
        "Content-Type": "application/vnd.flux"
    }
    
    # Get all measurements
    query = f'''
import "influxdata/influxdb/schema"
schema.measurements(bucket: "{BUCKET}")
'''
    
    try:
        response = requests.post(
            f"{INFLUXDB_URL}/api/v2/query",
            params={"org": ORG},
            headers=headers,
            data=query,
            timeout=30
        )
        
        if response.status_code == 200:
            print("=== MEASUREMENTS IN BUCKET ===")
            print(response.text)
        else:
            print(f"Failed to get measurements: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"Error checking measurements: {e}")

def check_indicators_by_measurement():
    """Check indicators for each known measurement"""
    
    headers = {
        "Authorization": f"Token {TOKEN}",
        "Content-Type": "application/vnd.flux"
    }
    
    measurements = [
        "bls_economic_data",
        "bea_economic_data", 
        "housing_data",
        "commodity_data",
        "fred_rates",
        "market_data",
        "banking_data",
        "trade_data",
        "business_confidence",
        "consumer_data",
        "treasury_yield_curve",
        "advanced_financial",
        "global_indicators",
        "census_economic_data",
        "corporate_data"
    ]
    
    for measurement in measurements:
        query = f'''
from(bucket: "{BUCKET}")
  |> range(start: -30d)
  |> filter(fn: (r) => r._measurement == "{measurement}")
  |> keep(columns: ["indicator", "rate_type", "maturity"])
  |> distinct()
  |> limit(n: 20)
'''
        
        try:
            response = requests.post(
                f"{INFLUXDB_URL}/api/v2/query",
                params={"org": ORG},
                headers=headers,
                data=query,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.text.strip()
                if result and len(result) > 100:  # Has actual data
                    print(f"\n=== {measurement.upper()} ===")
                    print(result[:500] + "..." if len(result) > 500 else result)
            else:
                print(f"Failed to query {measurement}: {response.status_code}")
                
        except Exception as e:
            print(f"Error checking {measurement}: {e}")

def check_sample_data():
    """Check sample data from different measurements"""
    
    headers = {
        "Authorization": f"Token {TOKEN}",
        "Content-Type": "application/vnd.flux"
    }
    
    # Check what data actually exists
    query = f'''
from(bucket: "{BUCKET}")
  |> range(start: -7d)
  |> limit(n: 50)
'''
    
    try:
        response = requests.post(
            f"{INFLUXDB_URL}/api/v2/query",
            params={"org": ORG},
            headers=headers,
            data=query,
            timeout=30
        )
        
        if response.status_code == 200:
            print("\n=== SAMPLE DATA (Last 7 days) ===")
            print(response.text)
        else:
            print(f"Failed to get sample data: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"Error checking sample data: {e}")

def main():
    print("Checking InfluxDB Data Structure")
    print("=" * 40)
    
    check_measurements()
    check_indicators_by_measurement() 
    check_sample_data()

if __name__ == "__main__":
    main()