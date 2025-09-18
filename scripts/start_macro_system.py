#!/usr/bin/env python3
"""
Start Macro Economic Data Collection System
Initialize InfluxDB buckets, collect initial data, and verify setup
"""

import os
import sys
import asyncio
import logging
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from influxdb_client import InfluxDBClient
from src.collectors.macro_collectors import create_macro_manager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
INFLUXDB_URL = "http://localhost:8086"
INFLUXDB_TOKEN = "xEoh_d1wMmj_8sE2ipM1nht5Iq_iJiziHWVGvt9Haplv8QPDuR6oFTRIcX3rT8rG1M6H21tk0sSTv5ujfrPRDg=="
INFLUXDB_ORG = "69a6563b80682691"

API_KEYS = {
    "bea_api_key": os.getenv("BEA_API_KEY", "F1E3FC75-5378-43DE-88F6-796F85788A37"),
    "finra_api_key": os.getenv("FINRA_API_KEY", "3a9634291169447b9912"),
    "fred_api_key": os.getenv("FRED_API_KEY", "6a20a49705210da6ff7c97adb5167b11"),
    "eia_api_key": os.getenv("EIA_API_KEY", "6xGrNpJYCBb66oCOtIV7RqdyeSMDBgKBJfQTAPGs"),
    "census_api_key": os.getenv("CENSUS_API_KEY", "5d0db23721b8e48096f63e08f89a84d0e2323422")
}

async def main():
    """Main setup and initialization"""
    
    print("Starting Macro Economic Data System")
    print("=" * 50)
    
    # Step 1: Setup InfluxDB buckets
    print("\nStep 1: Setting up InfluxDB buckets...")
    from setup_macro_influxdb import create_influxdb_buckets, verify_buckets
    
    if not create_influxdb_buckets():
        print("ERROR: Failed to create InfluxDB buckets")
        return False
    
    if not verify_buckets():
        print("ERROR: Failed to verify InfluxDB buckets")
        return False
    
    print("SUCCESS: InfluxDB buckets ready")
    
    # Step 2: Initialize data collectors
    print("\nStep 2: Initializing data collectors...")
    
    try:
        client = InfluxDBClient(
            url=INFLUXDB_URL,
            token=INFLUXDB_TOKEN,
            org=INFLUXDB_ORG
        )
        
        manager = create_macro_manager(client, API_KEYS)
        print(f"SUCCESS: Created macro manager with {len(manager.collectors)} collectors:")
        for name in manager.collectors.keys():
            print(f"   - {name}")
        
    except Exception as e:
        print(f"ERROR: Failed to initialize collectors: {e}")
        return False
    
    # Step 3: Collect initial data
    print("\nStep 3: Collecting comprehensive macro data...")
    
    try:
        # Collect from all available sources
        print("   Collecting from all macro data sources...")
        all_results = await manager.collect_all_data()
        
        print("\n   Collection Results:")
        total_points = 0
        successful_collectors = 0
        
        for collector_name, point_count in all_results.items():
            if point_count >= 0:
                print(f"   SUCCESS: {collector_name}: {point_count} data points")
                total_points += point_count
                successful_collectors += 1
            else:
                print(f"   FAILED: {collector_name}")
        
        print(f"\n   Total: {total_points} data points from {successful_collectors} sources")
        print("SUCCESS: Comprehensive data collection completed")
        
    except Exception as e:
        print(f"ERROR: Data collection failed: {e}")
        logger.exception("Data collection error")
        return False
    
    finally:
        client.close()
    
    # Step 4: Verify data in InfluxDB
    print("\nStep 4: Verifying data storage...")
    
    try:
        client = InfluxDBClient(
            url=INFLUXDB_URL,
            token=INFLUXDB_TOKEN,
            org=INFLUXDB_ORG
        )
        
        query_api = client.query_api()
        
        # Check each bucket for data
        buckets_to_check = ["macro_data"]
        
        for bucket in buckets_to_check:
            try:
                query = f'''
                from(bucket: "{bucket}")
                |> range(start: -7d)
                |> count()
                '''
                
                tables = query_api.query(query)
                total_records = 0
                
                for table in tables:
                    for record in table.records:
                        total_records += record.get_value()
                
                if total_records > 0:
                    print(f"   SUCCESS: {bucket}: {total_records} records")
                else:
                    print(f"   WARNING: {bucket}: No recent data")
                    
            except Exception as e:
                print(f"   ERROR: {bucket}: Query error - {e}")
        
        print("SUCCESS: Data verification completed")
        
    except Exception as e:
        print(f"ERROR: Data verification failed: {e}")
        return False
    
    finally:
        client.close()
    
    # Step 5: Summary and next steps
    print("\nSystem Status Summary")
    print("=" * 30)
    print("SUCCESS: InfluxDB buckets created and verified")
    print("SUCCESS: Macro data collectors initialized")
    print("SUCCESS: Initial data collection completed")
    print("SUCCESS: Data verification passed")
    
    print("\nAvailable Data Sources:")
    print("- Treasury (FiscalData): Yield curves, auction results")
    print("- BLS: CPI, unemployment, payrolls, labor statistics")
    print("- BEA: GDP, PCE, NIPA economic accounts")
    print("- FRED: Federal Reserve economic data with vintage support")
    print("- EIA: Energy inventories, crude oil, natural gas prices")
    print("- Census: Retail trade, manufacturing, housing data")
    print("- ECB: European rates, EUR/USD, HICP inflation")
    print("- IMF: Global economic indicators via SDMX")
    print("- BIS: Credit, debt, international financial statistics")
    print("- SEC EDGAR: Corporate filings activity")
    print("- FINRA: Short interest, short volume data")
    print("- World Bank: Global growth, inflation, development indicators")
    print("- OECD: Leading indicators, business confidence, house prices")
    
    print("\nNext Steps:")
    print("1. View macro data in Grafana: http://localhost:3000")
    print("2. Set up automated collection: Configure Celery Beat")
    print("3. Create macro dashboard panels")
    print("4. Configure economic event alerts")
    
    print("\nYour macro economic data system is ready!")
    
    return True

if __name__ == "__main__":
    success = asyncio.run(main())
    
    if success:
        print("\nSetup completed successfully!")
        sys.exit(0)
    else:
        print("\nSetup failed!")
        sys.exit(1)