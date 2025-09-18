#!/usr/bin/env python3
"""
Create the exact data structure that the macro dashboard expects
"""

import requests
from datetime import datetime, timedelta
import random
import os

INFLUXDB_URL = "http://localhost:8086"
TOKEN = os.getenv("INFLUXDB_TOKEN", "macro_dashboard_token_2025")
ORG = "stock_monitor"
BUCKET = "macro_data"

def write_correct_data():
    """Write data with the exact measurement names the dashboard expects"""
    
    headers = {
        "Authorization": f"Token {TOKEN}",
        "Content-Type": "text/plain; charset=utf-8"
    }
    
    base_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    data_lines = []
    
    # Generate data for the last 30 days
    for i in range(30):
        timestamp = int((base_time - timedelta(days=i)).timestamp())
        
        # 1. treasury_yield_curve (what dashboard expects)
        data_lines.extend([
            f"treasury_yield_curve,maturity=2Y yield={4.8 + random.uniform(-0.2, 0.2)} {timestamp}",
            f"treasury_yield_curve,maturity=10Y yield={4.2 + random.uniform(-0.2, 0.2)} {timestamp}",
            f"treasury_yield_curve,maturity=30Y yield={4.5 + random.uniform(-0.2, 0.2)} {timestamp}",
        ])
        
        # 2. treasury_curve_metrics
        spread_10y_2y = (4.2 + random.uniform(-0.2, 0.2)) - (4.8 + random.uniform(-0.2, 0.2))
        data_lines.append(f"treasury_curve_metrics,metric=10y_2y_spread spread={spread_10y_2y} {timestamp}")
        
        # 3. bls_economic_data
        data_lines.extend([
            f"bls_economic_data,indicator=cpi value={3.2 + random.uniform(-0.3, 0.3)} {timestamp}",
            f"bls_economic_data,indicator=core_cpi value={3.1 + random.uniform(-0.2, 0.2)} {timestamp}",
            f"bls_economic_data,indicator=unemployment_rate value={3.8 + random.uniform(-0.2, 0.2)} {timestamp}",
        ])
        
        # 4. fred_economic_data
        data_lines.extend([
            f"fred_economic_data,indicator=fed_funds_rate value={5.25 + random.uniform(-0.1, 0.1)} {timestamp}",
            f"fred_economic_data,indicator=vix value={15.0 + random.uniform(-3.0, 8.0)} {timestamp}",
        ])
        
        # 5. bea_economic_data
        data_lines.extend([
            f"bea_economic_data,indicator=gdp_growth value={2.1 + random.uniform(-0.5, 0.5)} {timestamp}",
            f"bea_economic_data,indicator=pce_growth value={2.0 + random.uniform(-0.3, 0.3)} {timestamp}",
        ])
        
        # 6. eia_energy_data
        data_lines.extend([
            f"eia_energy_data,commodity=crude_oil value={80.0 + random.uniform(-10.0, 15.0)} {timestamp}",
            f"eia_energy_data,commodity=natural_gas value={3.5 + random.uniform(-0.5, 1.0)} {timestamp}",
        ])
        
        # 7. census_economic_data
        data_lines.extend([
            f"census_economic_data,indicator=retail_sales value={random.uniform(-2.0, 4.0)} {timestamp}",
            f"census_economic_data,indicator=housing_starts value={1300000 + random.uniform(-100000, 200000)} {timestamp}",
        ])
        
        # 8. finra_short_interest and finra_margin_debt
        data_lines.extend([
            f"finra_short_interest,market=nyse short_ratio={3.5 + random.uniform(-1.0, 2.0)} {timestamp}",
            f"finra_margin_debt,market=nyse debt_billions={800.0 + random.uniform(-50.0, 100.0)} {timestamp}",
        ])
    
    # Write all data
    line_protocol = "\n".join(data_lines)
    
    try:
        response = requests.post(
            f"{INFLUXDB_URL}/api/v2/write",
            params={"org": ORG, "bucket": BUCKET, "precision": "s"},
            headers=headers,
            data=line_protocol,
            timeout=30
        )
        
        if response.status_code == 204:
            print(f"Successfully wrote {len(data_lines)} data points with correct measurement names")
            return True
        else:
            print(f"Failed to write data: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"Error writing data: {e}")
        return False

def main():
    print("Writing data with correct measurement names for dashboard")
    print("=" * 60)
    
    if write_correct_data():
        print("\nSUCCESS! Dashboard data structure is now correct.")
        print("\nThe dashboard should now show data for:")
        print("- Treasury yield curves")
        print("- Economic indicators (CPI, unemployment)")
        print("- Fed funds rate and VIX")
        print("- GDP and PCE growth")
        print("- Energy commodities")
        print("- Retail sales and housing")
        print("- FINRA short interest")
        print("\nTry refreshing your Grafana dashboard now.")
    else:
        print("Failed to write correct data")

if __name__ == "__main__":
    main()