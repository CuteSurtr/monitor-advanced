#!/usr/bin/env python3
"""
Comprehensive Macro Economic Data Population Script
Gathers 1+ years of historical data from real APIs and synthetic backfill
for the Comprehensive Economic Dashboard
"""

import requests
import json
import asyncio
import aiohttp
from datetime import datetime, timedelta
import random
import pandas as pd
import numpy as np
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

# InfluxDB configuration
INFLUXDB_URL = "http://localhost:8086"
ORG = "stock_monitor"
BUCKET = "macro_data"
TOKEN = os.getenv("INFLUXDB_TOKEN", "your_influxdb_token")

class ComprehensiveDataPopulator:
    def __init__(self):
        self.client = InfluxDBClient(url=INFLUXDB_URL, token=TOKEN, org=ORG)
        self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
        
        # API Keys (using free tiers)
        self.fred_api_key = os.getenv("FRED_API_KEY", "your_fred_api_key")
        
        # Date ranges for historical data
        self.end_date = datetime.now()
        self.start_date = self.end_date - timedelta(days=365)  # 1 year of data
        
    def write_point(self, measurement, tags, fields, timestamp):
        """Write a single data point to InfluxDB"""
        try:
            point = Point(measurement)
            for tag_key, tag_value in tags.items():
                point = point.tag(tag_key, tag_value)
            for field_key, field_value in fields.items():
                point = point.field(field_key, field_value)
            point = point.time(timestamp)
            
            self.write_api.write(bucket=BUCKET, record=point)
            return True
        except Exception as e:
            print(f"Error writing point: {e}")
            return False

    async def fetch_fred_data(self, series_id, description, indicator_name):
        """Fetch real data from FRED API"""
        print(f"[DATA] Fetching FRED data for {description}...")
        
        url = "https://api.stlouisfed.org/fred/series/observations"
        params = {
            "series_id": series_id,
            "api_key": self.fred_api_key,
            "file_type": "json",
            "observation_start": self.start_date.strftime("%Y-%m-%d"),
            "observation_end": self.end_date.strftime("%Y-%m-%d")
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        points_written = 0
                        
                        for obs in data.get("observations", []):
                            if obs.get("value") != ".":
                                try:
                                    timestamp = datetime.strptime(obs["date"], "%Y-%m-%d")
                                    value = float(obs["value"])
                                    
                                    # Determine category based on series
                                    if "UNRATE" in series_id:
                                        category = "labor"
                                    elif "CPI" in series_id:
                                        category = "inflation"
                                    elif "FEDFUNDS" in series_id:
                                        category = "monetary_policy"
                                    elif "VIX" in series_id:
                                        category = "volatility"
                                    else:
                                        category = "economic"
                                    
                                    success = self.write_point(
                                        "fred_economic_data",
                                        {"indicator": indicator_name, "category": category, "series_id": series_id},
                                        {"value": value},
                                        timestamp
                                    )
                                    if success:
                                        points_written += 1
                                except (ValueError, KeyError):
                                    continue
                        
                        print(f"[SUCCESS] Wrote {points_written} {description} data points")
                        return points_written
                    else:
                        print(f"[ERROR] FRED API error for {series_id}: {response.status}")
                        return 0
        except Exception as e:
            print(f"[ERROR] Error fetching FRED data for {series_id}: {e}")
            return 0

    async def fetch_treasury_data(self):
        """Fetch real Treasury yield curve data"""
        print("[DATA] Fetching Treasury yield curve data...")
        
        url = "https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v1/accounting/od/daily_treasury_yield_curve"
        
        # Get data in chunks (Treasury API has date limits)
        total_points = 0
        current_date = self.start_date
        
        while current_date < self.end_date:
            chunk_end = min(current_date + timedelta(days=90), self.end_date)
            
            params = {
                "filter": f"record_date:gte:{current_date.strftime('%Y-%m-%d')},record_date:lte:{chunk_end.strftime('%Y-%m-%d')}",
                "sort": "-record_date",
                "format": "json",
                "page[size]": "1000"
            }
            
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, params=params) as response:
                        if response.status == 200:
                            data = await response.json()
                            
                            for item in data.get("data", []):
                                timestamp = datetime.strptime(item["record_date"], "%Y-%m-%d")
                                
                                # Map all available tenors
                                tenor_mapping = {
                                    "1_mo": "1M", "2_mo": "2M", "3_mo": "3M", "6_mo": "6M",
                                    "1_yr": "1Y", "2_yr": "2Y", "3_yr": "3Y", "5_yr": "5Y",
                                    "7_yr": "7Y", "10_yr": "10Y", "20_yr": "20Y", "30_yr": "30Y"
                                }
                                
                                for api_tenor, display_tenor in tenor_mapping.items():
                                    yield_value = item.get(api_tenor)
                                    if yield_value and yield_value != "":
                                        try:
                                            yield_float = float(yield_value)
                                            success = self.write_point(
                                                "treasury_yield_curve",
                                                {"maturity": display_tenor, "security_type": "treasury"},
                                                {"yield": yield_float},
                                                timestamp
                                            )
                                            if success:
                                                total_points += 1
                                        except ValueError:
                                            continue
                                
                                # Calculate yield curve spreads
                                try:
                                    y10 = float(item.get("10_yr", 0))
                                    y2 = float(item.get("2_yr", 0))
                                    if y10 > 0 and y2 > 0:
                                        spread = y10 - y2
                                        success = self.write_point(
                                            "treasury_curve_metrics",
                                            {"metric": "10y_2y_spread"},
                                            {"spread": spread},
                                            timestamp
                                        )
                                        if success:
                                            total_points += 1
                                except (ValueError, TypeError):
                                    pass
                        
                        await asyncio.sleep(0.2)  # Rate limiting
                        
            except Exception as e:
                print(f"[ERROR] Error fetching Treasury data chunk: {e}")
            
            current_date = chunk_end
        
        print(f"[SUCCESS] Wrote {total_points} Treasury data points")
        return total_points

    def generate_enhanced_synthetic_data(self):
        """Generate enhanced synthetic data with realistic patterns"""
        print("[DATA] Generating enhanced synthetic economic data...")
        
        total_points = 0
        
        # Generate daily data for the past year
        current_date = self.start_date
        while current_date <= self.end_date:
            
            # Enhanced BLS Labor Market Data
            base_unemployment = 3.8
            unemployment_trend = 0.1 * np.sin(2 * np.pi * (current_date - self.start_date).days / 365)
            unemployment = base_unemployment + unemployment_trend + random.uniform(-0.1, 0.1)
            
            success = self.write_point(
                "bls_economic_data",
                {"indicator": "unemployment_rate", "category": "labor"},
                {"value": round(unemployment, 2)},
                current_date
            )
            if success:
                total_points += 1
            
            # Nonfarm payrolls (monthly data, but simulate daily)
            if current_date.day == 1:  # Monthly
                payrolls = 150 + random.uniform(-20, 30)  # thousands
                success = self.write_point(
                    "bls_economic_data",
                    {"indicator": "nonfarm_payrolls", "category": "labor"},
                    {"value": round(payrolls, 0)},
                    current_date
                )
                if success:
                    total_points += 1
            
            # CPI with seasonal patterns
            base_cpi = 3.2
            seasonal_component = 0.3 * np.sin(2 * np.pi * current_date.timetuple().tm_yday / 365)
            trend_component = 0.001 * (current_date - self.start_date).days
            cpi = base_cpi + seasonal_component + trend_component + random.uniform(-0.1, 0.1)
            
            success = self.write_point(
                "bls_economic_data",
                {"indicator": "cpi", "category": "inflation"},
                {"value": round(cpi, 2)},
                current_date
            )
            if success:
                total_points += 1
            
            # Core CPI (less volatile)
            core_cpi = cpi * 0.95 + random.uniform(-0.05, 0.05)
            success = self.write_point(
                "bls_economic_data",
                {"indicator": "core_cpi", "category": "inflation"},
                {"value": round(core_cpi, 2)},
                current_date
            )
            if success:
                total_points += 1
            
            # BEA Economic Activity Data
            # GDP growth (quarterly pattern)
            if current_date.day == 1 and current_date.month % 3 == 1:  # Quarterly
                base_gdp = 2.1
                cycle_component = 0.5 * np.sin(2 * np.pi * (current_date - self.start_date).days / (365 * 2))
                gdp_growth = base_gdp + cycle_component + random.uniform(-0.3, 0.3)
                
                success = self.write_point(
                    "bea_economic_data",
                    {"indicator": "gdp_growth", "category": "economic_activity"},
                    {"value": round(gdp_growth, 2)},
                    current_date
                )
                if success:
                    total_points += 1
            
            # PCE growth
            pce_growth = cpi * 0.8 + random.uniform(-0.2, 0.2)
            success = self.write_point(
                "bea_economic_data",
                {"indicator": "pce_growth", "category": "consumption"},
                {"value": round(pce_growth, 2)},
                current_date
            )
            if success:
                total_points += 1
            
            # Energy Data with volatility
            # Crude oil with realistic volatility and trends
            base_oil = 75.0
            volatility = 8.0 * random.gauss(0, 1)
            seasonal_oil = 5.0 * np.sin(2 * np.pi * current_date.timetuple().tm_yday / 365)
            oil_price = base_oil + volatility + seasonal_oil
            oil_price = max(20, oil_price)  # Floor price
            
            success = self.write_point(
                "eia_energy_data",
                {"commodity": "crude_oil", "unit": "usd_per_barrel"},
                {"value": round(oil_price, 2)},
                current_date
            )
            if success:
                total_points += 1
            
            # Natural gas with winter seasonal patterns
            base_gas = 3.2
            winter_premium = 1.0 if current_date.month in [11, 12, 1, 2] else 0
            gas_volatility = 0.4 * random.gauss(0, 1)
            gas_price = base_gas + winter_premium + gas_volatility
            gas_price = max(1.0, gas_price)
            
            success = self.write_point(
                "eia_energy_data",
                {"commodity": "natural_gas", "unit": "usd_per_mmbtu"},
                {"value": round(gas_price, 2)},
                current_date
            )
            if success:
                total_points += 1
            
            # Census Economic Data
            # Retail sales with consumer spending patterns
            base_retail = 100.0  # Index
            holiday_boost = 15.0 if current_date.month == 12 else 0
            retail_sales = base_retail + holiday_boost + random.uniform(-5, 5)
            
            success = self.write_point(
                "census_economic_data",
                {"indicator": "retail_sales", "category": "consumption"},
                {"value": round(retail_sales, 1)},
                current_date
            )
            if success:
                total_points += 1
            
            # Housing starts with building season patterns
            base_housing = 1.4  # millions annually
            building_season = 0.3 if current_date.month in [4, 5, 6, 7, 8, 9] else -0.1
            housing_starts = base_housing + building_season + random.uniform(-0.2, 0.2)
            housing_starts = max(0.5, housing_starts)
            
            success = self.write_point(
                "census_economic_data",
                {"indicator": "housing_starts", "category": "construction"},
                {"value": round(housing_starts, 2)},
                current_date
            )
            if success:
                total_points += 1
            
            # FINRA Market Data
            # Short interest metrics
            base_short_ratio = 0.25
            market_stress = 0.1 * np.sin(2 * np.pi * (current_date - self.start_date).days / 90)  # Quarterly cycle
            short_ratio = base_short_ratio + market_stress + random.uniform(-0.05, 0.05)
            short_ratio = max(0.1, min(0.5, short_ratio))
            
            success = self.write_point(
                "finra_short_interest",
                {"category": "short_interest", "market": "nyse"},
                {"short_ratio": round(short_ratio, 3)},
                current_date
            )
            if success:
                total_points += 1
            
            # Margin debt
            base_margin = 800.0  # billions
            market_cycle = 50.0 * np.sin(2 * np.pi * (current_date - self.start_date).days / 365)
            margin_debt = base_margin + market_cycle + random.uniform(-20, 20)
            
            success = self.write_point(
                "finra_margin_debt",
                {"category": "margin_debt", "market": "nyse"},
                {"debt_billions": round(margin_debt, 1)},
                current_date
            )
            if success:
                total_points += 1
            
            current_date += timedelta(days=1)
        
        print(f"[SUCCESS] Generated {total_points} synthetic data points")
        return total_points

    async def run_comprehensive_collection(self):
        """Run the complete data collection process"""
        print("[START] Starting comprehensive macro economic data collection...")
        print(f"[INFO] Date range: {self.start_date.strftime('%Y-%m-%d')} to {self.end_date.strftime('%Y-%m-%d')}")
        print("=" * 60)
        
        total_points = 0
        
        # 1. Fetch real data from FRED (free tier)
        fred_series = [
            ("UNRATE", "Unemployment Rate", "unemployment_rate"),
            ("CPIAUCSL", "Consumer Price Index", "cpi"),
            ("FEDFUNDS", "Federal Funds Rate", "fed_funds_rate"),
            ("VIXCLS", "VIX Volatility Index", "vix"),
            ("DGS10", "10-Year Treasury Rate", "treasury_10y"),
            ("DGS2", "2-Year Treasury Rate", "treasury_2y"),
        ]
        
        for series_id, description, indicator in fred_series:
            points = await self.fetch_fred_data(series_id, description, indicator)
            total_points += points
            await asyncio.sleep(1)  # Rate limiting for free tier
        
        # 2. Fetch Treasury yield curve data
        treasury_points = await self.fetch_treasury_data()
        total_points += treasury_points
        
        # 3. Generate enhanced synthetic data for other indicators
        synthetic_points = self.generate_enhanced_synthetic_data()
        total_points += synthetic_points
        
        print("=" * 60)
        print(f"[COMPLETE] COLLECTION COMPLETE!")
        print(f"[STATS] Total data points written: {total_points:,}")
        print(f"[SUCCESS] Your Comprehensive Economic Dashboard should now show rich time series!")
        print(f"[INFO] Access dashboard at: http://localhost:3000/d/macro-economic-dashboard")
        
        return total_points

async def main():
    """Main execution function"""
    try:
        populator = ComprehensiveDataPopulator()
        await populator.run_comprehensive_collection()
    except Exception as e:
        print(f"[ERROR] Error during data collection: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())