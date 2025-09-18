#!/usr/bin/env python3
"""
Populate InfluxDB macro_data bucket with sample economic data
for the Comprehensive Economic Dashboard
"""

import requests
import json
from datetime import datetime, timedelta
import random
import os

# InfluxDB configuration
INFLUXDB_URL = "http://localhost:8086"
ORG = "stock_monitor"
BUCKET = "macro_data"
TOKEN = os.getenv("INFLUXDB_TOKEN", "trading_token_123")

def write_data(measurement, tags, fields, timestamp):
    """Write data point to InfluxDB"""
    data = {
        "measurement": measurement,
        "tags": tags,
        "fields": fields,
        "time": timestamp.isoformat()
    }
    
    url = f"{INFLUXDB_URL}/api/v2/write"
    params = {
        "org": ORG,
        "bucket": BUCKET,
        "precision": "ns"
    }
    headers = {
        "Authorization": f"Token {TOKEN}",
        "Content-Type": "application/octet-stream"
    }
    
    # Convert to InfluxDB line protocol
    line = f"{measurement}"
    for key, value in tags.items():
        line += f",{key}={value}"
    line += " "
    
    field_parts = []
    for key, value in fields.items():
        if isinstance(value, (int, float)):
            field_parts.append(f"{key}={value}")
        else:
            field_parts.append(f'{key}="{value}"')
    line += ",".join(field_parts)
    
    line += f" {int(timestamp.timestamp() * 1e9)}"
    
    response = requests.post(url, params=params, headers=headers, data=line)
    if response.status_code != 204:
        print(f"Error writing {measurement}: {response.status_code} - {response.text}")
    else:
        print(f"[SUCCESS] Wrote {measurement} data point")

def generate_treasury_data():
    """Generate sample Treasury yield curve data"""
    print("Generating Treasury yield curve data...")
    
    base_date = datetime.now() - timedelta(days=30)
    maturities = ["1M", "3M", "6M", "1Y", "2Y", "3Y", "5Y", "7Y", "10Y", "20Y", "30Y"]
    
    for day in range(31):
        current_date = base_date + timedelta(days=day)
        
        # Generate realistic yield curve
        base_yield = 4.0 + random.uniform(-0.5, 0.5)
        
        for maturity in maturities:
            # Add term premium
            if maturity in ["1M", "3M"]:
                yield_value = base_yield + random.uniform(-0.1, 0.1)
            elif maturity in ["6M", "1Y"]:
                yield_value = base_yield + random.uniform(0.1, 0.3)
            elif maturity in ["2Y", "3Y"]:
                yield_value = base_yield + random.uniform(0.3, 0.6)
            elif maturity in ["5Y", "7Y"]:
                yield_value = base_yield + random.uniform(0.6, 0.9)
            elif maturity in ["10Y", "20Y"]:
                yield_value = base_yield + random.uniform(0.9, 1.2)
            else:  # 30Y
                yield_value = base_yield + random.uniform(1.2, 1.5)
            
            write_data(
                "treasury_yield_curve",
                {"maturity": maturity, "security_type": "treasury"},
                {"yield": round(yield_value, 3)},
                current_date
            )

def generate_economic_indicators():
    """Generate sample economic indicator data"""
    print("Generating economic indicators...")
    
    base_date = datetime.now() - timedelta(days=30)
    
    # CPI data
    for day in range(31):
        current_date = base_date + timedelta(days=day)
        cpi_value = 3.2 + random.uniform(-0.1, 0.1)
        write_data(
            "bls_economic_data",
            {"indicator": "cpi", "category": "inflation"},
            {"value": round(cpi_value, 2)},
            current_date
        )
    
    # Unemployment rate
    for day in range(31):
        current_date = base_date + timedelta(days=day)
        unemployment = 3.8 + random.uniform(-0.1, 0.1)
        write_data(
            "bls_economic_data",
            {"indicator": "unemployment_rate", "category": "labor"},
            {"value": round(unemployment, 2)},
            current_date
        )
    
    # GDP growth
    for day in range(31):
        current_date = base_date + timedelta(days=day)
        gdp_growth = 2.1 + random.uniform(-0.2, 0.2)
        write_data(
            "bea_economic_data",
            {"indicator": "gdp_growth", "category": "economic_activity"},
            {"value": round(gdp_growth, 2)},
            current_date
        )

def generate_energy_data():
    """Generate sample energy data"""
    print("Generating energy data...")
    
    base_date = datetime.now() - timedelta(days=30)
    
    for day in range(31):
        current_date = base_date + timedelta(days=day)
        
        # Oil prices
        oil_price = 75.0 + random.uniform(-5, 5)
        write_data(
            "eia_energy_data",
            {"commodity": "crude_oil", "unit": "usd_per_barrel"},
            {"value": round(oil_price, 2)},
            current_date
        )
        
        # Natural gas
        gas_price = 3.2 + random.uniform(-0.3, 0.3)
        write_data(
            "eia_energy_data",
            {"commodity": "natural_gas", "unit": "usd_per_mmbtu"},
            {"value": round(gas_price, 2)},
            current_date
        )

def generate_financial_data():
    """Generate sample financial market data"""
    print("Generating financial market data...")
    
    base_date = datetime.now() - timedelta(days=30)
    
    for day in range(31):
        current_date = base_date + timedelta(days=day)
        
        # VIX index
        vix_value = 20.0 + random.uniform(-5, 10)
        write_data(
            "fred_economic_data",
            {"indicator": "vix", "category": "volatility"},
            {"value": round(vix_value, 2)},
            current_date
        )
        
        # Fed funds rate
        fed_rate = 5.25 + random.uniform(-0.1, 0.1)
        write_data(
            "fred_economic_data",
            {"indicator": "fed_funds_rate", "category": "monetary_policy"},
            {"value": round(fed_rate, 2)},
            current_date
        )

def main():
    """Main function to populate all data"""
    print("� Populating InfluxDB macro_data bucket with sample economic data...")
    print(f"Target: {INFLUXDB_URL}")
    print(f"Organization: {ORG}")
    print(f"Bucket: {BUCKET}")
    print("-" * 50)
    
    try:
        # Generate different types of economic data
        generate_treasury_data()
        generate_economic_indicators()
        generate_energy_data()
        generate_financial_data()
        
        print("-" * 50)
        print("Successfully populated macro_data bucket!")
        print("Your Comprehensive Economic Dashboard should now work.")
        
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure InfluxDB is running and accessible.")

if __name__ == "__main__":
    main()


