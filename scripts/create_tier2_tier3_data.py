#!/usr/bin/env python3
"""
Create Tier 2 & Tier 3 macro economic data for professional-level dashboard
Includes advanced indicators used by hedge funds, economists, and policymakers
"""

import requests
from datetime import datetime, timedelta
import random
import math
import os

INFLUXDB_URL = "http://localhost:8086"
TOKEN = os.getenv("INFLUXDB_TOKEN", "macro_dashboard_token_2025")
ORG = "stock_monitor"
BUCKET = "macro_data"

def create_tier2_tier3_trends():
    """Create realistic Tier 2 & Tier 3 economic indicator trends"""
    
    return {
        # Trade & Consumption
        "retail_sales_headline": {"base": 2.5, "trend": -0.002, "volatility": 1.2, "cycle_days": 30},
        "retail_sales_core": {"base": 1.8, "trend": -0.001, "volatility": 0.8, "cycle_days": 30},
        "pce_headline": {"base": 2.1, "trend": -0.0015, "volatility": 0.3, "cycle_days": 30},
        "pce_core": {"base": 1.9, "trend": -0.001, "volatility": 0.2, "cycle_days": 30},
        "durable_goods": {"base": 1.2, "trend": -0.003, "volatility": 2.5, "cycle_days": 45},
        "auto_sales": {"base": 15.2, "trend": -0.01, "volatility": 0.8, "cycle_days": 60},
        
        # Housing & Real Estate
        "housing_starts": {"base": 1420000, "trend": -300, "volatility": 80000, "cycle_days": 45},
        "building_permits": {"base": 1380000, "trend": -250, "volatility": 70000, "cycle_days": 45},
        "new_home_sales": {"base": 650000, "trend": -150, "volatility": 40000, "cycle_days": 60},
        "existing_home_sales": {"base": 4200000, "trend": -1000, "volatility": 200000, "cycle_days": 60},
        "case_shiller_index": {"base": 310.5, "trend": 0.05, "volatility": 3.0, "cycle_days": 90},
        "mortgage_30y": {"base": 7.2, "trend": -0.002, "volatility": 0.15, "cycle_days": 30},
        
        # Corporate & Credit
        "corporate_profits": {"base": 2.8, "trend": -0.001, "volatility": 0.5, "cycle_days": 90},
        "bankruptcy_filings": {"base": 45000, "trend": 15, "volatility": 3000, "cycle_days": 30},
        "leveraged_loans": {"base": 98.5, "trend": -0.02, "volatility": 1.5, "cycle_days": 20},
        "clo_index": {"base": 102.3, "trend": -0.01, "volatility": 0.8, "cycle_days": 25},
        
        # Banking & Liquidity
        "commercial_bank_assets": {"base": 23.5, "trend": 0.01, "volatility": 0.3, "cycle_days": 60},
        "m1_money_supply": {"base": 18.2, "trend": 0.008, "volatility": 0.5, "cycle_days": 30},
        "m2_money_supply": {"base": 20.8, "trend": 0.005, "volatility": 0.3, "cycle_days": 30},
        "sofr_rate": {"base": 5.31, "trend": -0.001, "volatility": 0.08, "cycle_days": 15},
        "repo_spread": {"base": 0.15, "trend": 0.0002, "volatility": 0.05, "cycle_days": 10},
        
        # Energy & Commodities (Enhanced)
        "oil_inventories": {"base": 450.2, "trend": -0.5, "volatility": 15.0, "cycle_days": 7},
        "gasoline_price": {"base": 3.45, "trend": 0.001, "volatility": 0.15, "cycle_days": 14},
        "diesel_price": {"base": 3.89, "trend": 0.0008, "volatility": 0.12, "cycle_days": 14},
        "natgas_storage": {"base": 2850, "trend": -5, "volatility": 80, "cycle_days": 7},
        "commodity_index": {"base": 245.8, "trend": 0.02, "volatility": 8.0, "cycle_days": 30},
        
        # Business & Confidence (Tier 3)
        "ism_manufacturing": {"base": 48.5, "trend": -0.01, "volatility": 1.2, "cycle_days": 30},
        "ism_services": {"base": 51.2, "trend": -0.008, "volatility": 1.0, "cycle_days": 30},
        "nfib_optimism": {"base": 89.5, "trend": -0.05, "volatility": 2.0, "cycle_days": 30},
        "consumer_confidence": {"base": 102.3, "trend": -0.03, "volatility": 3.5, "cycle_days": 30},
        "business_inventories": {"base": 1.2, "trend": 0.001, "volatility": 0.3, "cycle_days": 45},
        
        # Trade & Global (Tier 3)
        "current_account": {"base": -3.5, "trend": 0.002, "volatility": 0.8, "cycle_days": 90},
        "trade_balance": {"base": -68.2, "trend": 0.1, "volatility": 5.0, "cycle_days": 30},
        "exports": {"base": 265.8, "trend": 0.05, "volatility": 8.0, "cycle_days": 30},
        "imports": {"base": 334.0, "trend": -0.03, "volatility": 10.0, "cycle_days": 30},
        "fx_reserves": {"base": 135.2, "trend": 0.02, "volatility": 2.0, "cycle_days": 60},
        
        # Advanced Financial (Tier 3)
        "vix_surface_30d": {"base": 16.5, "trend": 0.002, "volatility": 2.8, "cycle_days": 15},
        "vix_surface_60d": {"base": 18.2, "trend": 0.0015, "volatility": 2.2, "cycle_days": 20},
        "credit_spread_ig": {"base": 125, "trend": 0.3, "volatility": 15, "cycle_days": 30},
        "credit_spread_hy": {"base": 485, "trend": 1.2, "volatility": 40, "cycle_days": 25},
        "equity_risk_premium": {"base": 5.8, "trend": 0.002, "volatility": 0.3, "cycle_days": 60},
    }

def generate_realistic_value(base_config, day_offset):
    """Generate realistic value with trend, cycle, and volatility"""
    
    base = base_config["base"]
    trend = base_config["trend"] * day_offset
    volatility = base_config["volatility"]
    cycle_days = base_config["cycle_days"]
    
    # Add cyclical component
    cycle = 0.3 * volatility * math.sin(2 * math.pi * day_offset / cycle_days)
    
    # Add random noise
    noise = random.uniform(-volatility, volatility)
    
    return base + trend + cycle + noise

def write_tier2_tier3_data():
    """Write comprehensive Tier 2 & Tier 3 data"""
    
    headers = {
        "Authorization": f"Token {TOKEN}",
        "Content-Type": "text/plain; charset=utf-8"
    }
    
    base_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    trends = create_tier2_tier3_trends()
    
    print("Generating Tier 2 & Tier 3 macro economic data...")
    print("Time range: 2 years (730 days)")
    print("New indicators: 35+ professional-level metrics")
    
    batch_size = 50
    total_points = 0
    
    for batch_start in range(0, 730, batch_size):
        data_lines = []
        batch_end = min(batch_start + batch_size, 730)
        
        print(f"Processing days {batch_start+1}-{batch_end} of 730...")
        
        for i in range(batch_start, batch_end):
            timestamp = int((base_time - timedelta(days=i)).timestamp())
            
            # Generate values for this day
            values = {}
            for key, config in trends.items():
                values[key] = generate_realistic_value(config, i)
            
            # === TIER 2 DATA ===
            
            # Trade & Consumption
            data_lines.extend([
                f"trade_consumption,indicator=retail_sales,type=headline value={values['retail_sales_headline']:.2f} {timestamp}",
                f"trade_consumption,indicator=retail_sales,type=core value={values['retail_sales_core']:.2f} {timestamp}",
                f"trade_consumption,indicator=pce,type=headline value={values['pce_headline']:.2f} {timestamp}",
                f"trade_consumption,indicator=pce,type=core value={values['pce_core']:.2f} {timestamp}",
                f"trade_consumption,indicator=durable_goods value={values['durable_goods']:.2f} {timestamp}",
                f"trade_consumption,indicator=auto_sales value={values['auto_sales']:.1f} {timestamp}",
            ])
            
            # Housing & Real Estate
            data_lines.extend([
                f"housing_real_estate,indicator=housing_starts value={values['housing_starts']:.0f} {timestamp}",
                f"housing_real_estate,indicator=building_permits value={values['building_permits']:.0f} {timestamp}",
                f"housing_real_estate,indicator=new_home_sales value={values['new_home_sales']:.0f} {timestamp}",
                f"housing_real_estate,indicator=existing_home_sales value={values['existing_home_sales']:.0f} {timestamp}",
                f"housing_real_estate,indicator=case_shiller_index value={values['case_shiller_index']:.1f} {timestamp}",
                f"housing_real_estate,indicator=mortgage_30y value={values['mortgage_30y']:.3f} {timestamp}",
            ])
            
            # Corporate & Credit
            data_lines.extend([
                f"corporate_credit,indicator=corporate_profits value={values['corporate_profits']:.2f} {timestamp}",
                f"corporate_credit,indicator=bankruptcy_filings value={values['bankruptcy_filings']:.0f} {timestamp}",
                f"corporate_credit,indicator=leveraged_loans value={values['leveraged_loans']:.2f} {timestamp}",
                f"corporate_credit,indicator=clo_index value={values['clo_index']:.2f} {timestamp}",
            ])
            
            # Banking & Liquidity
            data_lines.extend([
                f"banking_liquidity,indicator=commercial_bank_assets value={values['commercial_bank_assets']:.2f} {timestamp}",
                f"banking_liquidity,indicator=m1_money_supply value={values['m1_money_supply']:.2f} {timestamp}",
                f"banking_liquidity,indicator=m2_money_supply value={values['m2_money_supply']:.2f} {timestamp}",
                f"banking_liquidity,indicator=sofr_rate value={values['sofr_rate']:.3f} {timestamp}",
                f"banking_liquidity,indicator=repo_spread value={values['repo_spread']:.3f} {timestamp}",
            ])
            
            # Energy & Commodities (Enhanced)
            data_lines.extend([
                f"energy_commodities_extended,indicator=oil_inventories value={values['oil_inventories']:.1f} {timestamp}",
                f"energy_commodities_extended,indicator=gasoline_price value={values['gasoline_price']:.3f} {timestamp}",
                f"energy_commodities_extended,indicator=diesel_price value={values['diesel_price']:.3f} {timestamp}",
                f"energy_commodities_extended,indicator=natgas_storage value={values['natgas_storage']:.0f} {timestamp}",
                f"energy_commodities_extended,indicator=commodity_index value={values['commodity_index']:.1f} {timestamp}",
            ])
            
            # === TIER 3 DATA ===
            
            # Business & Confidence
            data_lines.extend([
                f"business_confidence,indicator=ism_manufacturing value={values['ism_manufacturing']:.1f} {timestamp}",
                f"business_confidence,indicator=ism_services value={values['ism_services']:.1f} {timestamp}",
                f"business_confidence,indicator=nfib_optimism value={values['nfib_optimism']:.1f} {timestamp}",
                f"business_confidence,indicator=consumer_confidence value={values['consumer_confidence']:.1f} {timestamp}",
                f"business_confidence,indicator=business_inventories value={values['business_inventories']:.2f} {timestamp}",
            ])
            
            # Trade & Global
            data_lines.extend([
                f"trade_global,indicator=current_account value={values['current_account']:.2f} {timestamp}",
                f"trade_global,indicator=trade_balance value={values['trade_balance']:.1f} {timestamp}",
                f"trade_global,indicator=exports value={values['exports']:.1f} {timestamp}",
                f"trade_global,indicator=imports value={values['imports']:.1f} {timestamp}",
                f"trade_global,indicator=fx_reserves value={values['fx_reserves']:.1f} {timestamp}",
            ])
            
            # Advanced Financial
            data_lines.extend([
                f"advanced_financial,indicator=vix_surface,term=30d value={values['vix_surface_30d']:.2f} {timestamp}",
                f"advanced_financial,indicator=vix_surface,term=60d value={values['vix_surface_60d']:.2f} {timestamp}",
                f"advanced_financial,indicator=credit_spread,grade=investment_grade value={values['credit_spread_ig']:.0f} {timestamp}",
                f"advanced_financial,indicator=credit_spread,grade=high_yield value={values['credit_spread_hy']:.0f} {timestamp}",
                f"advanced_financial,indicator=equity_risk_premium value={values['equity_risk_premium']:.2f} {timestamp}",
            ])
        
        # Write batch
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
                print(f"  Wrote {batch_points} points (Total: {total_points})")
            else:
                print(f"  Batch failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"  Error: {e}")
            return False
    
    print(f"\nSUCCESS! Added {total_points} Tier 2 & Tier 3 data points")
    return True

def verify_new_measurements():
    """Verify the new measurement categories exist"""
    
    headers = {
        "Authorization": f"Token {TOKEN}",
        "Content-Type": "application/vnd.flux"
    }
    
    new_measurements = [
        "trade_consumption",
        "housing_real_estate", 
        "corporate_credit",
        "banking_liquidity",
        "energy_commodities_extended",
        "business_confidence",
        "trade_global",
        "advanced_financial"
    ]
    
    print("\nVerifying new measurement categories...")
    
    for measurement in new_measurements:
        query = f'import "influxdata/influxdb/schema" schema.tagValues(bucket: "{BUCKET}", measurement: "{measurement}", tag: "indicator")'
        
        try:
            response = requests.post(
                f"{INFLUXDB_URL}/api/v2/query",
                params={"org": ORG},
                headers=headers,
                data=query,
                timeout=10
            )
            
            if response.status_code == 200:
                indicators = response.text.count('_result')
                print(f"  {measurement}: {indicators} indicators")
            else:
                print(f"  {measurement}: Query failed")
                
        except Exception as e:
            print(f"  {measurement}: Error - {e}")

def main():
    print("Professional Macro Dashboard - Tier 2 & Tier 3 Data")
    print("=" * 55)
    print("Adding 35+ advanced indicators used by:")
    print("• Hedge funds & institutional investors") 
    print("• Economic policymakers & central banks")
    print("• Professional macro analysts")
    print("• Risk management teams\n")
    
    if write_tier2_tier3_data():
        print("\nData population completed!")
        verify_new_measurements()
        
        print("\n=== NEW DASHBOARD CATEGORIES ===")
        print("\nTIER 2 - Extended Market & Macro:")
        print("• Trade & Consumption (retail sales, PCE, durables)")
        print("• Housing & Real Estate (starts, permits, prices)")  
        print("• Corporate & Credit (profits, bankruptcies, loans)")
        print("• Banking & Liquidity (money supply, rates, assets)")
        print("• Energy & Commodities (inventories, prices, storage)")
        
        print("\nTIER 3 - Advanced/Niche:")
        print("• Business & Confidence (ISM, NFIB, sentiment)")
        print("• Trade & Global (balance, exports/imports)")
        print("• Advanced Financial (volatility surfaces, spreads)")
        
        print("\nYour dashboard now has hedge fund-level sophistication!")
        print("Go to http://localhost:3000 to create the new panels.")
        
    else:
        print("Data population failed")

if __name__ == "__main__":
    main()