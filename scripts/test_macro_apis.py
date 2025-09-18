#!/usr/bin/env python3
"""
Test Macro Economic API Keys and Data Collection
Verify that all API keys work and can collect data
"""

import asyncio
import sys
import os
import logging
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from influxdb_client import InfluxDBClient
from src.collectors.macro_collectors import (
    BEACollector, FINRACollector, FREDCollector, 
    EIACollector, CensusCollector, TreasuryCollector,
    BLSCollector, ECBCollector, WorldBankCollector,
    SECCollector, IMFCollector, BISCollector, OECDCollector
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Your API Keys
API_KEYS = {
    "bea_api_key": "F1E3FC75-5378-43DE-88F6-796F85788A37",
    "finra_api_key": "3a9634291169447b9912",
    "fred_api_key": "6a20a49705210da6ff7c97adb5167b11", 
    "eia_api_key": "6xGrNpJYCBb66oCOtIV7RqdyeSMDBgKBJfQTAPGs",
    "census_api_key": "5d0db23721b8e48096f63e08f89a84d0e2323422"
}

INFLUXDB_CONFIG = {
    "url": "http://localhost:8086",
    "token": "xEoh_d1wMmj_8sE2ipM1nht5Iq_iJiziHWVGvt9Haplv8QPDuR6oFTRIcX3rT8rG1M6H21tk0sSTv5ujfrPRDg==",
    "org": "69a6563b80682691"
}

async def test_api_collector(collector_class, name, *args):
    """Test a specific API collector"""
    try:
        logger.info(f"Testing {name} collector...")
        
        # Create fake InfluxDB client for testing (won't actually write data)
        client = InfluxDBClient(**INFLUXDB_CONFIG)
        
        collector = collector_class(client, *args)
        data_points = await collector.collect_data()
        
        if data_points and len(data_points) > 0:
            logger.info(f"SUCCESS {name}: Collected {len(data_points)} data points")
            
            # Show sample data
            sample = data_points[0]
            logger.info(f"   Sample: {sample.measurement} - {sample.tags} - {sample.fields}")
            return True
        else:
            logger.warning(f"WARNING {name}: No data returned (may be rate limited or API issue)")
            return False
            
    except Exception as e:
        logger.error(f"ERROR {name}: Failed - {e}")
        return False

async def test_all_apis():
    """Test all macro economic APIs"""
    logger.info("Testing All Macro Economic API Keys")
    logger.info("=" * 50)
    
    results = {}
    
    # Test APIs that require keys
    logger.info("\nTesting APIs with Keys:")
    
    # BEA - Bureau of Economic Analysis
    results["BEA"] = await test_api_collector(
        BEACollector, "BEA (Bureau of Economic Analysis)", 
        API_KEYS["bea_api_key"]
    )
    
    # FINRA - Financial Industry Regulatory Authority  
    results["FINRA"] = await test_api_collector(
        FINRACollector, "FINRA (Short Interest)",
        API_KEYS["finra_api_key"]
    )
    
    # FRED - Federal Reserve Economic Data
    results["FRED"] = await test_api_collector(
        FREDCollector, "FRED (Federal Reserve)",
        API_KEYS["fred_api_key"]
    )
    
    # EIA - Energy Information Administration
    results["EIA"] = await test_api_collector(
        EIACollector, "EIA (Energy Information Admin)",
        API_KEYS["eia_api_key"]
    )
    
    # Census - US Census Bureau
    results["Census"] = await test_api_collector(
        CensusCollector, "Census Bureau",
        API_KEYS["census_api_key"]
    )
    
    # Test APIs that don't require keys
    logger.info("\nTesting APIs without Keys:")
    
    # Treasury - No API key required
    results["Treasury"] = await test_api_collector(
        TreasuryCollector, "Treasury (FiscalData)"
    )
    
    # BLS - No API key required
    results["BLS"] = await test_api_collector(
        BLSCollector, "BLS (Labor Statistics)"
    )
    
    # ECB - No API key required
    results["ECB"] = await test_api_collector(
        ECBCollector, "ECB (European Central Bank)"
    )
    
    # World Bank - No API key required
    results["WorldBank"] = await test_api_collector(
        WorldBankCollector, "World Bank"
    )
    
    # SEC - No API key required
    results["SEC"] = await test_api_collector(
        SECCollector, "SEC EDGAR"
    )
    
    # IMF - No API key required  
    results["IMF"] = await test_api_collector(
        IMFCollector, "IMF (International Monetary Fund)"
    )
    
    # BIS - No API key required
    results["BIS"] = await test_api_collector(
        BISCollector, "BIS (Bank for International Settlements)"
    )
    
    # OECD - No API key required
    results["OECD"] = await test_api_collector(
        OECDCollector, "OECD"
    )
    
    # Summary
    logger.info("\nAPI Test Results Summary:")
    logger.info("=" * 30)
    
    successful = sum(1 for success in results.values() if success)
    total = len(results)
    
    for api_name, success in results.items():
        status = "WORKING" if success else "FAILED"
        logger.info(f"   {api_name}: {status}")
    
    logger.info(f"\nOverall Success Rate: {successful}/{total} ({successful/total*100:.1f}%)")
    
    if successful >= total * 0.8:  # 80% success rate
        logger.info("Excellent! Most APIs are working correctly.")
    elif successful >= total * 0.6:  # 60% success rate
        logger.info("Good! Most APIs working, some may need attention.")
    else:
        logger.info("Several APIs need troubleshooting.")
    
    logger.info("\nNext Steps:")
    logger.info("1. Run full collection: py scripts/start_macro_system.py")
    logger.info("2. View data in Grafana: http://localhost:3000")
    logger.info("3. Monitor logs for any issues")
    
    return successful, total

async def main():
    """Main test function"""
    try:
        successful, total = await test_all_apis()
        
        if successful == total:
            logger.info("\nAll APIs tested successfully! Your macro system is ready.")
            sys.exit(0)
        else:
            logger.warning(f"\n{total - successful} APIs had issues. Check logs above.")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())