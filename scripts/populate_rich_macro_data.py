#!/usr/bin/env python3
"""
Rich Macro Economic Data Population Script
Generates comprehensive time series data for dashboard visualization
"""

import requests
import json
from datetime import datetime, timedelta
import random
import numpy as np

# InfluxDB configuration
INFLUXDB_URL = "http://localhost:8086"
ORG = "stock_monitor"
BUCKET = "macro_data"
TOKEN = "trading_token_123"

def write_line_protocol(measurement, tags, fields, timestamp):
    """Write data point to InfluxDB using line protocol"""
    
    # Build line protocol string
    line = measurement
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
    
    url = f"{INFLUXDB_URL}/api/v2/write"
    params = {"org": ORG, "bucket": BUCKET, "precision": "ns"}
    headers = {
        "Authorization": f"Token {TOKEN}",
        "Content-Type": "application/octet-stream"
    }
    
    try:
        response = requests.post(url, params=params, headers=headers, data=line)
        if response.status_code == 204:
            return True
        else:
            print(f"Write error: {response.status_code} - {response.text[:200]}")
            return False
    except Exception as e:
        print(f"Connection error: {e}")
        return False

def generate_realistic_time_series(base_value, days, volatility=0.1, trend=0.0, seasonal=False):
    """Generate realistic time series with trends, volatility, and seasonality"""
    values = []
    current_value = base_value
    
    for day in range(days):
        # Add trend
        trend_component = trend * day / days
        
        # Add seasonal component (annual cycle)
        seasonal_component = 0
        if seasonal:
            seasonal_component = 0.1 * base_value * np.sin(2 * np.pi * day / 365)
        
        # Add random walk with mean reversion
        random_component = random.gauss(0, volatility * base_value)
        mean_reversion = -0.05 * (current_value - base_value)
        
        current_value += trend_component + random_component + mean_reversion
        current_value = max(current_value * 0.5, current_value)  # Prevent negative values
        
        values.append(current_value + seasonal_component)
    
    return values

def populate_treasury_data():
    """Generate comprehensive Treasury yield curve data"""
    print("[DATA] Generating Treasury yield curve data...")
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)  # 3 months of data
    
    # Treasury maturities with realistic base yields
    maturities = {
        "1M": 4.8, "3M": 5.0, "6M": 4.9, "1Y": 4.7,
        "2Y": 4.2, "3Y": 4.0, "5Y": 3.9, "7Y": 4.0,
        "10Y": 4.2, "20Y": 4.5, "30Y": 4.6
    }
    
    points_written = 0
    
    # Generate daily yield curve data
    current_date = start_date
    while current_date <= end_date:
        # Skip weekends for realism
        if current_date.weekday() < 5:  # Monday = 0, Friday = 4
            
            # Generate correlated yield movements
            market_shock = random.gauss(0, 0.05)  # Common factor
            
            for maturity, base_yield in maturities.items():
                # Add maturity-specific noise
                maturity_noise = random.gauss(0, 0.02)
                yield_value = base_yield + market_shock + maturity_noise
                yield_value = max(0.1, yield_value)  # Floor at 0.1%
                
                success = write_line_protocol(
                    "treasury_yield_curve",
                    {"maturity": maturity, "security_type": "treasury"},
                    {"yield": round(yield_value, 3)},
                    current_date
                )
                if success:
                    points_written += 1
            
            # Calculate yield spreads
            y10 = maturities["10Y"] + market_shock + random.gauss(0, 0.02)
            y2 = maturities["2Y"] + market_shock + random.gauss(0, 0.02)
            spread_10y2y = y10 - y2
            
            success = write_line_protocol(
                "treasury_curve_metrics",
                {"metric": "10y_2y_spread"},
                {"spread": round(spread_10y2y, 2)},
                current_date
            )
            if success:
                points_written += 1
        
        current_date += timedelta(days=1)
    
    print(f"[SUCCESS] Wrote {points_written} Treasury data points")
    return points_written

def populate_economic_indicators():
    """Generate comprehensive economic indicator data"""
    print("[DATA] Generating economic indicators...")
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)
    
    # Generate base time series
    days = (end_date - start_date).days + 1
    
    # CPI data (less volatile)
    cpi_values = generate_realistic_time_series(3.2, days, volatility=0.02, trend=0.1)
    core_cpi_values = generate_realistic_time_series(3.0, days, volatility=0.015, trend=0.08)
    
    # Unemployment (mean-reverting)
    unemployment_values = generate_realistic_time_series(3.8, days, volatility=0.02, trend=0.0)
    
    # Nonfarm payrolls (monthly, more volatile)
    payroll_values = generate_realistic_time_series(150, days//30 + 1, volatility=0.15, trend=0.02)
    
    # VIX (high volatility)
    vix_values = generate_realistic_time_series(20.0, days, volatility=0.3, trend=0.0)
    
    # Fed funds rate (policy-driven, less frequent changes)
    fed_rate_values = generate_realistic_time_series(5.25, days, volatility=0.01, trend=0.0)
    
    points_written = 0
    current_date = start_date
    
    for day_idx in range(days):
        # Daily indicators
        indicators = [
            ("cpi", "bls_economic_data", "inflation", cpi_values[day_idx]),
            ("core_cpi", "bls_economic_data", "inflation", core_cpi_values[day_idx]),
            ("unemployment_rate", "bls_economic_data", "labor", unemployment_values[day_idx]),
            ("vix", "fred_economic_data", "volatility", vix_values[day_idx]),
            ("fed_funds_rate", "fred_economic_data", "monetary_policy", fed_rate_values[day_idx]),
        ]
        
        for indicator, measurement, category, value in indicators:
            success = write_line_protocol(
                measurement,
                {"indicator": indicator, "category": category},
                {"value": round(value, 2)},
                current_date
            )
            if success:
                points_written += 1
        
        # Monthly indicators (first day of month)
        if current_date.day == 1:
            payroll_idx = day_idx // 30
            if payroll_idx < len(payroll_values):
                success = write_line_protocol(
                    "bls_economic_data",
                    {"indicator": "nonfarm_payrolls", "category": "labor"},
                    {"value": round(payroll_values[payroll_idx], 0)},
                    current_date
                )
                if success:
                    points_written += 1
        
        current_date += timedelta(days=1)
    
    print(f"[SUCCESS] Wrote {points_written} economic indicator points")
    return points_written

def populate_sectoral_data():
    """Generate sectoral and industry data"""
    print("[DATA] Generating sectoral economic data...")
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)
    days = (end_date - start_date).days + 1
    
    # Generate sectoral time series
    gdp_growth_values = generate_realistic_time_series(2.1, days//7, volatility=0.05, trend=0.01)  # Weekly
    pce_growth_values = generate_realistic_time_series(2.8, days, volatility=0.03, seasonal=True)
    retail_sales_values = generate_realistic_time_series(100.0, days, volatility=0.04, seasonal=True)
    housing_starts_values = generate_realistic_time_series(1.4, days, volatility=0.08, seasonal=True)
    
    # Energy data (more volatile)
    oil_price_values = generate_realistic_time_series(75.0, days, volatility=0.12, trend=0.0)
    gas_price_values = generate_realistic_time_series(3.2, days, volatility=0.15, seasonal=True)
    
    # Financial market data
    margin_debt_values = generate_realistic_time_series(800.0, days, volatility=0.05, trend=0.02)
    short_ratio_values = generate_realistic_time_series(0.25, days, volatility=0.1, trend=0.0)
    
    points_written = 0
    current_date = start_date
    
    for day_idx in range(days):
        
        # Daily sectoral data
        daily_indicators = [
            ("pce_growth", "bea_economic_data", "consumption", pce_growth_values[day_idx]),
            ("retail_sales", "census_economic_data", "consumption", retail_sales_values[day_idx]),
            ("housing_starts", "census_economic_data", "construction", housing_starts_values[day_idx]),
        ]
        
        for indicator, measurement, category, value in daily_indicators:
            success = write_line_protocol(
                measurement,
                {"indicator": indicator, "category": category},
                {"value": round(value, 2)},
                current_date
            )
            if success:
                points_written += 1
        
        # Energy data
        energy_data = [
            ("crude_oil", "eia_energy_data", "usd_per_barrel", oil_price_values[day_idx]),
            ("natural_gas", "eia_energy_data", "usd_per_mmbtu", gas_price_values[day_idx]),
        ]
        
        for commodity, measurement, unit, value in energy_data:
            success = write_line_protocol(
                measurement,
                {"commodity": commodity, "unit": unit},
                {"value": round(value, 2)},
                current_date
            )
            if success:
                points_written += 1
        
        # Financial market data
        financial_data = [
            ("finra_margin_debt", {"category": "margin_debt", "market": "nyse"}, 
             {"debt_billions": round(margin_debt_values[day_idx], 1)}),
            ("finra_short_interest", {"category": "short_interest", "market": "nyse"}, 
             {"short_ratio": round(short_ratio_values[day_idx], 3)}),
        ]
        
        for measurement, tags, fields in financial_data:
            success = write_line_protocol(measurement, tags, fields, current_date)
            if success:
                points_written += 1
        
        # Weekly GDP data (Mondays)
        if current_date.weekday() == 0:  # Monday
            week_idx = day_idx // 7
            if week_idx < len(gdp_growth_values):
                success = write_line_protocol(
                    "bea_economic_data",
                    {"indicator": "gdp_growth", "category": "economic_activity"},
                    {"value": round(gdp_growth_values[week_idx], 2)},
                    current_date
                )
                if success:
                    points_written += 1
        
        current_date += timedelta(days=1)
    
    print(f"[SUCCESS] Wrote {points_written} sectoral data points")
    return points_written

def main():
    """Main execution function"""
    print("[START] Populating comprehensive macro economic data...")
    print(f"[INFO] Target: {INFLUXDB_URL}")
    print(f"[INFO] Organization: {ORG}")
    print(f"[INFO] Bucket: {BUCKET}")
    print("=" * 50)
    
    total_points = 0
    
    try:
        # Generate different categories of data
        treasury_points = populate_treasury_data()
        total_points += treasury_points
        
        indicator_points = populate_economic_indicators()
        total_points += indicator_points
        
        sectoral_points = populate_sectoral_data()
        total_points += sectoral_points
        
        print("=" * 50)
        print(f"[COMPLETE] Data population complete!")
        print(f"[STATS] Total points written: {total_points:,}")
        print(f"[SUCCESS] Your dashboard should now show rich time series graphs!")
        print(f"[INFO] Access at: http://localhost:3000/d/macro-economic-dashboard")
        
    except Exception as e:
        print(f"[ERROR] Error during data population: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()