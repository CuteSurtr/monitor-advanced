#!/usr/bin/env python3
"""
Simple script to populate InfluxDB macro_data bucket with sample economic data
"""

import subprocess
import time
from datetime import datetime, timedelta

# InfluxDB configuration
CONTAINER = "influxdb"
BUCKET = "macro_data"
ORG = "stock_monitor"
TOKEN = "xEoh_d1w_9u4rUmgZLCUqckVK5qGnF1FNs2_hzrrzfXQCXLJRRYPh5oqcE_T0nYmF7jqsJ-O6r2OEUVDWV-kew=="

def run_influx_command(cmd):
    """Run an influx command in the container"""
    full_cmd = f"docker exec {CONTAINER} influx {cmd}"
    try:
        result = subprocess.run(full_cmd, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Error: {result.stderr}")
            return False
        return True
    except Exception as e:
        print(f"Exception: {e}")
        return False

def write_data_point(measurement, tags, fields):
    """Write a data point to InfluxDB"""
    # Build the line protocol string
    tag_str = ",".join([f"{k}={v}" for k, v in tags.items()])
    field_str = ",".join([f"{k}={v}" for k, v in fields.items()])
    line = f"{measurement},{tag_str} {field_str}"
    
    cmd = f'write --bucket {BUCKET} --org {ORG} --token {TOKEN} "{line}"'
    return run_influx_command(cmd)

def main():
    print("Populating InfluxDB macro_data bucket with sample economic data...")
    print(f"Container: {CONTAINER}")
    print(f"Bucket: {BUCKET}")
    print(f"Organization: {ORG}")
    print()
    
    # Generate data for the last 30 days
    base_date = datetime.now() - timedelta(days=30)
    
    print("Generating Treasury yield curve data...")
    for i in range(30):
        current_date = base_date + timedelta(days=i)
        
        # Treasury yields with realistic variations
        yield_10y = 4.2 + (i * 0.01)  # Gradual increase
        yield_2y = 4.8 + (i * 0.015)   # Slightly faster increase
        yield_30y = 4.5 + (i * 0.008)  # Slower increase
        
        # Write Treasury data
        write_data_point(
            "treasury_yield_curve",
            {"maturity": "10Y", "security_type": "treasury"},
            {"yield": yield_10y}
        )
        
        write_data_point(
            "treasury_yield_curve", 
            {"maturity": "2Y", "security_type": "treasury"},
            {"yield": yield_2y}
        )
        
        write_data_point(
            "treasury_yield_curve",
            {"maturity": "30Y", "security_type": "treasury"}, 
            {"yield": yield_30y}
        )
        
        if i % 5 == 0:
            print(f"  Day {i+1}/30: 10Y={yield_10y:.2f}%, 2Y={yield_2y:.2f}%, 30Y={yield_30y:.2f}%")
    
    print("\nGenerating economic indicators...")
    
    # CPI data
    for i in range(30):
        cpi_value = 3.2 + (i * 0.01)  # Gradual inflation increase
        write_data_point(
            "bls_economic_data",
            {"indicator": "cpi", "category": "inflation"},
            {"value": cpi_value}
        )
    
    # Unemployment data
    for i in range(30):
        unemployment_value = 3.8 + (i * 0.005)  # Very gradual increase
        write_data_point(
            "bls_economic_data",
            {"indicator": "unemployment_rate", "category": "labor"},
            {"value": unemployment_value}
        )
    
    print("  Generated CPI and unemployment data")
    
    print("\nGenerating energy data...")
    
    # Oil price data
    for i in range(30):
        oil_price = 75.0 + (i * 0.5)  # Gradual price increase
        write_data_point(
            "eia_energy_data",
            {"commodity": "crude_oil", "unit": "usd_per_barrel"},
            {"value": oil_price}
        )
    
    # Natural gas data
    for i in range(30):
        gas_price = 2.5 + (i * 0.1)  # Gradual price increase
        write_data_point(
            "eia_energy_data",
            {"commodity": "natural_gas", "unit": "usd_per_mmbtu"},
            {"value": gas_price}
        )
    
    print("  Generated oil and natural gas data")
    
    print("\nGenerating financial market data...")
    
    # VIX data
    for i in range(30):
        vix_value = 20.0 + (i * 0.3)  # Gradual volatility increase
        write_data_point(
            "fred_economic_data",
            {"indicator": "vix", "category": "volatility"},
            {"value": vix_value}
        )
    
    # Fed funds rate data (constant for now)
    for i in range(30):
        write_data_point(
            "fred_economic_data",
            {"indicator": "fed_funds_rate", "category": "monetary_policy"},
            {"value": 5.25}
        )
    
    print("  Generated VIX and Fed funds rate data")
    
    print("\nGenerating Treasury curve metrics...")
    
    # Treasury curve spread data
    for i in range(30):
        spread_10y_2y = (i * 0.02)  # Spread increases over time
        write_data_point(
            "treasury_curve_metrics",
            {"metric": "10y_2y_spread"},
            {"spread": spread_10y_2y}
        )
    
    print("  Generated Treasury curve spread data")
    
    print("\n=== Sample data population complete! ===")
    print(f"Bucket: {BUCKET}")
    print(f"Organization: {ORG}")
    print(f"Container: {CONTAINER}")
    print()
    print("Your Comprehensive Economic Dashboard should now work.")
    print("Check Grafana to see the data.")

if __name__ == "__main__":
    main()

