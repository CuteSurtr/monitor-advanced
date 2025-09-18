#!/usr/bin/env python3
"""
Setup InfluxDB buckets for macro economic data
Creates buckets with appropriate retention policies for different data types
"""

import os
import sys
import logging
from influxdb_client import InfluxDBClient
from influxdb_client.rest import ApiException

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# InfluxDB configuration
INFLUXDB_URL = "http://localhost:8086"
INFLUXDB_TOKEN = "xEoh_d1wMmj_8sE2ipM1nht5Iq_iJiziHWVGvt9Haplv8QPDuR6oFTRIcX3rT8rG1M6H21tk0sSTv5ujfrPRDg=="
INFLUXDB_ORG = "69a6563b80682691"

# Macro data buckets with retention policies
MACRO_BUCKETS = {
    "macro_data": {
        "description": "General macro economic data",
        "retention_period": 86400 * 365 * 2,  # 2 years in seconds
        "data_types": ["BEA GDP/PCE", "BLS CPI/Employment", "Treasury yields"]
    },
    "treasury_data": {
        "description": "Treasury yield curves and auction results",
        "retention_period": 86400 * 365 * 5,  # 5 years in seconds
        "data_types": ["Yield curves", "Auction results", "Curve metrics"]
    },
    "finra_data": {
        "description": "FINRA short interest and volume data",
        "retention_period": 86400 * 365,  # 1 year in seconds
        "data_types": ["Short interest", "Short volume", "Short ratios"]
    },
    "economic_indicators": {
        "description": "Key economic indicators and derived metrics",
        "retention_period": 86400 * 365 * 10,  # 10 years in seconds
        "data_types": ["GDP", "CPI", "Employment", "YoY changes", "Recession signals"]
    },
    "market_regime": {
        "description": "Market regime classification based on macro data",
        "retention_period": 86400 * 365 * 3,  # 3 years in seconds
        "data_types": ["Regime states", "Confidence scores", "Transition signals"]
    },
    "correlation_macro": {
        "description": "Correlation between macro indicators and markets",
        "retention_period": 86400 * 365,  # 1 year in seconds
        "data_types": ["Macro-market correlations", "Lead-lag analysis", "Factor loadings"]
    }
}

def create_influxdb_buckets():
    """Create InfluxDB buckets for macro economic data"""
    
    try:
        # Initialize InfluxDB client
        client = InfluxDBClient(
            url=INFLUXDB_URL,
            token=INFLUXDB_TOKEN,
            org=INFLUXDB_ORG
        )
        
        # Get buckets API
        buckets_api = client.buckets_api()
        
        # Get organization
        orgs_api = client.organizations_api()
        org = orgs_api.find_organizations(org=INFLUXDB_ORG)[0]
        
        logger.info(f"Setting up macro data buckets for organization: {org.name}")
        
        # Check existing buckets
        existing_buckets = buckets_api.find_buckets().buckets
        existing_bucket_names = [b.name for b in existing_buckets] if existing_buckets else []
        
        # Create each macro bucket
        created_count = 0
        for bucket_name, config in MACRO_BUCKETS.items():
            try:
                if bucket_name in existing_bucket_names:
                    logger.info(f"Bucket '{bucket_name}' already exists")
                    continue
                    
                # Create bucket with retention policy
                bucket = buckets_api.create_bucket(
                    bucket_name=bucket_name,
                    description=config["description"],
                    org_id=org.id,
                    retention_rules=[{
                        "type": "expire",
                        "everySeconds": config["retention_period"]
                    }]
                )
                
                logger.info(f"Created bucket '{bucket_name}' with {config['retention_period']//86400} day retention")
                logger.info(f"   Data types: {', '.join(config['data_types'])}")
                created_count += 1
                
            except ApiException as e:
                if "already exists" in str(e):
                    logger.info(f"Bucket '{bucket_name}' already exists")
                else:
                    logger.error(f"Error creating bucket '{bucket_name}': {e}")
                    
            except Exception as e:
                logger.error(f"Unexpected error creating bucket '{bucket_name}': {e}")
        
        logger.info(f"\nä Macro data buckets setup complete!")
        logger.info(f"   Created: {created_count} new buckets")
        logger.info(f"   Total macro buckets: {len(MACRO_BUCKETS)}")
        
        # Display bucket summary
        logger.info(f"\nã Macro Data Bucket Summary:")
        for bucket_name, config in MACRO_BUCKETS.items():
            retention_days = config["retention_period"] // 86400
            logger.info(f"   ‚Ä¢ {bucket_name}: {retention_days} days retention")
            
        return True
        
    except Exception as e:
        logger.error(f"Failed to setup macro buckets: {e}")
        return False
    
    finally:
        try:
            client.close()
        except:
            pass

def verify_buckets():
    """Verify that all macro buckets exist and are accessible"""
    
    try:
        client = InfluxDBClient(
            url=INFLUXDB_URL,
            token=INFLUXDB_TOKEN,
            org=INFLUXDB_ORG
        )
        
        buckets_api = client.buckets_api()
        existing_buckets = buckets_api.find_buckets().buckets
        existing_bucket_names = [b.name for b in existing_buckets] if existing_buckets else []
        
        logger.info(f"\nç Verifying macro data buckets...")
        
        all_exist = True
        for bucket_name in MACRO_BUCKETS.keys():
            if bucket_name in existing_bucket_names:
                logger.info(f"   {bucket_name}")
            else:
                logger.error(f"   {bucket_name} - MISSING")
                all_exist = False
                
        if all_exist:
            logger.info(f"\nAll macro data buckets verified successfully!")
        else:
            logger.error(f"\nSome macro data buckets are missing!")
            
        return all_exist
        
    except Exception as e:
        logger.error(f"Error verifying buckets: {e}")
        return False
    
    finally:
        try:
            client.close()
        except:
            pass

def main():
    """Main setup function"""
    
    logger.info("Ä Setting up InfluxDB for Macro Economic Data")
    logger.info("=" * 60)
    
    # Create buckets
    if create_influxdb_buckets():
        logger.info("Bucket creation completed")
    else:
        logger.error("Bucket creation failed")
        sys.exit(1)
    
    # Verify buckets
    if verify_buckets():
        logger.info("Bucket verification completed")
    else:
        logger.error("Bucket verification failed")
        sys.exit(1)
    
    logger.info("\nØ Next Steps:")
    logger.info("1. Run macro data collection: python -m src.tasks.macro_collection")
    logger.info("2. View data in Grafana: http://localhost:3000")
    logger.info("3. Configure alerts for economic events")
    logger.info("4. Set up automated data collection schedule")
    
    logger.info("\nä Your macro economic data infrastructure is ready!")

if __name__ == "__main__":
    main()