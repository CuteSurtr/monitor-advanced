#!/usr/bin/env python3
"""
Simple Macro Data Setup - Just create the macro_data bucket
"""

import sys
import os
from influxdb_client import InfluxDBClient

# Configuration
INFLUXDB_URL = "http://localhost:8086"
INFLUXDB_TOKEN = "xEoh_d1wMmj_8sE2ipM1nht5Iq_iJiziHWVGvt9Haplv8QPDuR6oFTRIcX3rT8rG1M6H21tk0sSTv5ujfrPRDg=="
INFLUXDB_ORG = "69a6563b80682691"

def main():
    print("Simple Macro Data Setup")
    print("=" * 25)
    
    try:
        print("Connecting to InfluxDB...")
        client = InfluxDBClient(
            url=INFLUXDB_URL,
            token=INFLUXDB_TOKEN,
            org=INFLUXDB_ORG
        )
        
        print("Testing connection...")
        health = client.health()
        print(f"InfluxDB Status: {health.status}")
        
        # Get buckets API
        buckets_api = client.buckets_api()
        
        # List existing buckets
        print("\nExisting buckets:")
        existing_buckets = buckets_api.find_buckets()
        for bucket in existing_buckets.buckets:
            print(f"  - {bucket.name}")
        
        # Check if macro_data bucket exists
        macro_bucket_exists = any(b.name == "macro_data" for b in existing_buckets.buckets)
        
        if not macro_bucket_exists:
            print("\nCreating macro_data bucket...")
            bucket = buckets_api.create_bucket(
                bucket_name="macro_data",
                description="Macro economic data",
                org=INFLUXDB_ORG,
                retention_rules=[{
                    "type": "expire", 
                    "everySeconds": 86400 * 365 * 2  # 2 years
                }]
            )
            print(f"SUCCESS: Created bucket 'macro_data' with ID: {bucket.id}")
        else:
            print("SUCCESS: macro_data bucket already exists")
        
        # Test write to bucket
        print("\nTesting write to macro_data bucket...")
        write_api = client.write_api()
        
        from influxdb_client import Point
        test_point = Point("test_measurement") \
            .tag("source", "setup_test") \
            .field("value", 1.0)
        
        write_api.write(bucket="macro_data", record=test_point)
        print("SUCCESS: Test write completed")
        
        # Test query from bucket
        print("Testing query from macro_data bucket...")
        query_api = client.query_api()
        
        query = '''
        from(bucket: "macro_data")
        |> range(start: -1h)
        |> filter(fn: (r) => r["_measurement"] == "test_measurement")
        |> count()
        '''
        
        result = query_api.query(query)
        print("SUCCESS: Test query completed")
        
        client.close()
        
        print("\nSETUP COMPLETE!")
        print("- InfluxDB connection: OK")
        print("- macro_data bucket: OK") 
        print("- Write permission: OK")
        print("- Query permission: OK")
        print("\nReady to collect macro data!")
        
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)