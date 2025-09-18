#!/usr/bin/env python3
"""
Populate comprehensive historical macro economic data
Creates rich time series data for the past 2+ years across all dashboard measurements
"""

import requests
from datetime import datetime, timedelta
import random
import math

INFLUXDB_URL = "http://localhost:8086"
TOKEN = "macro_dashboard_token_2025"
ORG = "stock_monitor"
BUCKET = "macro_data"

def create_realistic_trends():
    """Create realistic economic trend patterns"""
    
    # Base economic parameters with realistic trends
    base_data = {
        # Treasury yields (inverted curve scenario)
        "2y_yield": {"base": 4.8, "trend": -0.001, "volatility": 0.15, "cycle_days": 60},
        "10y_yield": {"base": 4.2, "trend": -0.0008, "volatility": 0.12, "cycle_days": 90}, 
        "30y_yield": {"base": 4.5, "trend": -0.0005, "volatility": 0.10, "cycle_days": 120},
        
        # Economic indicators
        "cpi": {"base": 3.2, "trend": -0.0015, "volatility": 0.08, "cycle_days": 30},
        "core_cpi": {"base": 3.1, "trend": -0.001, "volatility": 0.06, "cycle_days": 30},
        "unemployment": {"base": 3.8, "trend": 0.0008, "volatility": 0.05, "cycle_days": 45},
        
        # Fed and market data
        "fed_funds": {"base": 5.25, "trend": -0.001, "volatility": 0.05, "cycle_days": 30},
        "vix": {"base": 16.0, "trend": 0.002, "volatility": 2.5, "cycle_days": 15},
        
        # Growth indicators
        "gdp_growth": {"base": 2.1, "trend": -0.0005, "volatility": 0.3, "cycle_days": 90},
        "pce_growth": {"base": 2.0, "trend": -0.0008, "volatility": 0.2, "cycle_days": 60},
        
        # Energy
        "crude_oil": {"base": 80.0, "trend": 0.01, "volatility": 3.0, "cycle_days": 20},
        "natural_gas": {"base": 3.5, "trend": -0.005, "volatility": 0.2, "cycle_days": 25},
        
        # Economic activity
        "retail_sales": {"base": 1.5, "trend": -0.002, "volatility": 1.0, "cycle_days": 30},
        "housing_starts": {"base": 1400000, "trend": -200, "volatility": 50000, "cycle_days": 45},
        
        # Market structure
        "short_ratio": {"base": 3.5, "trend": 0.003, "volatility": 0.5, "cycle_days": 10},
        "margin_debt": {"base": 800.0, "trend": -0.5, "volatility": 20.0, "cycle_days": 30},
    }
    
    return base_data

def generate_realistic_value(base_config, day_offset):
    """Generate a realistic value based on trend, cycle, and volatility"""
    
    base = base_config["base"]
    trend = base_config["trend"] * day_offset
    volatility = base_config["volatility"]
    cycle_days = base_config["cycle_days"]
    
    # Add cyclical component
    cycle = 0.3 * volatility * math.sin(2 * math.pi * day_offset / cycle_days)
    
    # Add random noise
    noise = random.uniform(-volatility, volatility)
    
    return base + trend + cycle + noise

def write_comprehensive_data():
    """Write comprehensive historical data"""
    
    headers = {
        "Authorization": f"Token {TOKEN}",
        "Content-Type": "text/plain; charset=utf-8"
    }
    
    # Generate data for the past 2 years (730 days)
    base_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    trends = create_realistic_trends()
    
    print("Generating comprehensive historical data...")
    print("Time range: 2 years (730 days)")
    print("Data points per day: ~17")
    print("Total estimated data points: ~12,400")
    
    batch_size = 100  # Write in batches
    total_points = 0
    
    for batch_start in range(0, 730, batch_size):
        data_lines = []
        batch_end = min(batch_start + batch_size, 730)
        
        print(f"Processing days {batch_start+1}-{batch_end} of 730...")
        
        for i in range(batch_start, batch_end):
            timestamp = int((base_time - timedelta(days=i)).timestamp())
            
            # Generate realistic values for this day
            values = {}
            for key, config in trends.items():
                values[key] = generate_realistic_value(config, i)
            
            # 1. Treasury yield curve data
            data_lines.extend([
                f"treasury_yield_curve,maturity=2Y yield={values['2y_yield']:.3f} {timestamp}",
                f"treasury_yield_curve,maturity=10Y yield={values['10y_yield']:.3f} {timestamp}",
                f"treasury_yield_curve,maturity=30Y yield={values['30y_yield']:.3f} {timestamp}",
            ])
            
            # 2. Treasury curve metrics
            spread_10y_2y = values['10y_yield'] - values['2y_yield']
            data_lines.append(f"treasury_curve_metrics,metric=10y_2y_spread spread={spread_10y_2y:.3f} {timestamp}")
            
            # 3. BLS economic data
            data_lines.extend([
                f"bls_economic_data,indicator=cpi value={values['cpi']:.2f} {timestamp}",
                f"bls_economic_data,indicator=core_cpi value={values['core_cpi']:.2f} {timestamp}",
                f"bls_economic_data,indicator=unemployment_rate value={values['unemployment']:.2f} {timestamp}",
            ])
            
            # 4. FRED economic data
            data_lines.extend([
                f"fred_economic_data,indicator=fed_funds_rate value={values['fed_funds']:.2f} {timestamp}",
                f"fred_economic_data,indicator=vix value={values['vix']:.1f} {timestamp}",
            ])
            
            # 5. BEA economic data
            data_lines.extend([
                f"bea_economic_data,indicator=gdp_growth value={values['gdp_growth']:.2f} {timestamp}",
                f"bea_economic_data,indicator=pce_growth value={values['pce_growth']:.2f} {timestamp}",
            ])
            
            # 6. EIA energy data
            data_lines.extend([
                f"eia_energy_data,commodity=crude_oil value={values['crude_oil']:.1f} {timestamp}",
                f"eia_energy_data,commodity=natural_gas value={values['natural_gas']:.2f} {timestamp}",
            ])
            
            # 7. Census economic data
            data_lines.extend([
                f"census_economic_data,indicator=retail_sales value={values['retail_sales']:.2f} {timestamp}",
                f"census_economic_data,indicator=housing_starts value={values['housing_starts']:.0f} {timestamp}",
            ])
            
            # 8. FINRA data
            data_lines.extend([
                f"finra_short_interest,market=nyse short_ratio={values['short_ratio']:.2f} {timestamp}",
                f"finra_margin_debt,market=nyse debt_billions={values['margin_debt']:.1f} {timestamp}",
            ])
        
        # Write this batch
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
                batch_points = len(data_lines)
                total_points += batch_points
                print(f"   Wrote {batch_points} points (Total: {total_points})")
            else:
                print(f"   Batch failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"   Error writing batch: {e}")
            return False
    
    print(f"\nSUCCESS! Wrote {total_points} comprehensive data points")
    return True

def verify_data_coverage():
    """Verify we have good data coverage across all measurements"""
    
    headers = {
        "Authorization": f"Token {TOKEN}",
        "Content-Type": "application/vnd.flux"
    }
    
    measurements_to_check = [
        "treasury_yield_curve",
        "treasury_curve_metrics", 
        "bls_economic_data",
        "fred_economic_data",
        "bea_economic_data",
        "eia_energy_data",
        "census_economic_data",
        "finra_short_interest",
        "finra_margin_debt"
    ]
    
    print("\\nVerifying data coverage...")
    
    for measurement in measurements_to_check:
        query = f'''
        from(bucket: "{BUCKET}")
          |> range(start: -730d)
          |> filter(fn: (r) => r["_measurement"] == "{measurement}")
          |> count()
        '''
        
        try:
            response = requests.post(
                f"{INFLUXDB_URL}/api/v2/query",
                params={"org": ORG},
                headers=headers,
                data=query,
                timeout=10
            )
            
            if response.status_code == 200:
                # Count data points in response
                point_count = response.text.count('_result')
                print(f"   {measurement}: {point_count} data series")
            else:
                print(f"   {measurement}: Query failed")
                
        except Exception as e:
            print(f"   {measurement}: Error - {e}")

def main():
    print("Comprehensive Historical Macro Economic Data Population")
    print("=" * 65)
    print("Creating 2 years of realistic historical data")
    print("across all macro economic indicators for your dashboard.\n")
    
    # Write comprehensive data
    if write_comprehensive_data():
        print("\\n Data population completed successfully!")
        
        # Verify coverage
        verify_data_coverage()
        
        print("\\n Your macro economic dashboard now has rich historical data!")
        print("\\n Dashboard features now available:")
        print("  • 2+ years of treasury yield curves")
        print("  • Historical inflation and unemployment trends")
        print("  • Fed funds rate evolution")
        print("  • Market volatility (VIX) history")
        print("  • GDP and PCE growth patterns")
        print("  • Energy commodity price movements")
        print("  • Economic activity indicators")
        print("  • Market structure metrics")
        
        print("\\n Go to http://localhost:3000 and explore your data!")
        print("   Try different time ranges and zoom into interesting periods.")
        
    else:
        print("\\n Data population failed")

if __name__ == "__main__":
    main()