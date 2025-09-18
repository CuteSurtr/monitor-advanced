#!/usr/bin/env python3
"""
Check specific energy data indicators in InfluxDB
"""

import requests

INFLUXDB_URL = "http://localhost:8086"
TOKEN = "macro_dashboard_token_2025"
ORG = "stock_monitor"
BUCKET = "macro_data"

def check_energy_measurements():
    """Check all energy-related measurements"""
    
    headers = {
        "Authorization": f"Token {TOKEN}",
        "Content-Type": "application/vnd.flux"
    }
    
    energy_measurements = [
        "eia_energy_data",
        "energy_commodities_extended",
        "commodity_data"
    ]
    
    for measurement in energy_measurements:
        query = f'''
from(bucket: "{BUCKET}")
  |> range(start: -7d)
  |> filter(fn: (r) => r._measurement == "{measurement}")
  |> distinct(column: "indicator")
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
                if result and len(result) > 100:
                    print(f"\n=== {measurement.upper()} INDICATORS ===")
                    print(result)
                else:
                    print(f"\n{measurement}: No data found")
            else:
                print(f"\nFailed to query {measurement}: {response.status_code}")
                
        except Exception as e:
            print(f"\nError checking {measurement}: {e}")

def check_sample_energy_data():
    """Check sample energy data"""
    
    headers = {
        "Authorization": f"Token {TOKEN}",
        "Content-Type": "application/vnd.flux"
    }
    
    query = f'''
from(bucket: "{BUCKET}")
  |> range(start: -7d)
  |> filter(fn: (r) => r._measurement =~ /.*energy.*/ or r._measurement =~ /.*commodity.*/)
  |> limit(n: 30)
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
            print("\n=== SAMPLE ENERGY/COMMODITY DATA ===")
            print(response.text)
        else:
            print(f"\nFailed to get sample energy data: {response.status_code}")
            
    except Exception as e:
        print(f"\nError checking sample energy data: {e}")

def main():
    print("Checking Energy Data in InfluxDB")
    print("=" * 35)
    
    check_energy_measurements()
    check_sample_energy_data()

if __name__ == "__main__":
    main()