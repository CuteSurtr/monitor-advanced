#!/usr/bin/env python3
"""
Fix InfluxDB setup and get proper authentication token
"""

import requests
import json
import time
import os

# InfluxDB settings
INFLUXDB_URL = "http://localhost:8086"
ORG_NAME = "stock_monitor"
BUCKET_NAME = "market_data"
USERNAME = os.getenv("INFLUXDB_ADMIN_USER", "admin")
PASSWORD = os.getenv("INFLUXDB_ADMIN_PASSWORD", "admin123")

def setup_influxdb():
    """Setup InfluxDB and get authentication token"""
    
    print("Setting up InfluxDB...")
    
    # Wait for InfluxDB to be ready
    print("Waiting for InfluxDB to be ready...")
    for i in range(30):
        try:
            response = requests.get(f"{INFLUXDB_URL}/ping", timeout=5)
            if response.status_code in [200, 204]:
                print("InfluxDB is ready")
                break
        except:
            pass
        time.sleep(2)
        print(f"   Attempt {i+1}/30...")
    else:
        print("InfluxDB not ready after 60 seconds")
        return None
    
    # Setup InfluxDB
    setup_data = {
        "username": USERNAME,
        "password": PASSWORD,
        "org": ORG_NAME,
        "bucket": BUCKET_NAME,
        "retentionPeriodSeconds": 0
    }
    
    try:
        print("Performing initial setup...")
        response = requests.post(f"{INFLUXDB_URL}/api/v2/setup", json=setup_data, timeout=10)
        
        if response.status_code == 201:
            result = response.json()
            token = result.get("auth", {}).get("token")
            org_id = result.get("org", {}).get("id")
            bucket_id = result.get("bucket", {}).get("id")
            
            print(f"InfluxDB setup successful!")
            print(f"Organization: {ORG_NAME} (ID: {org_id})")
            print(f"Bucket: {BUCKET_NAME} (ID: {bucket_id})")
            print(f"Token: {token}")
            
            return token
            
        elif response.status_code == 422:
            # Already setup, get token another way
            print("InfluxDB already setup, getting existing token...")
            return get_existing_token()
            
        else:
            print(f"Setup failed: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"Setup error: {e}")
        return None

def get_existing_token():
    """Get token from existing setup using signin"""
    
    try:
        print("Signing in to get token...")
        signin_data = {
            "username": USERNAME,
            "password": PASSWORD
        }
        
        response = requests.post(f"{INFLUXDB_URL}/api/v2/signin", json=signin_data, timeout=10)
        
        if response.status_code == 204:
            # Get auth cookie/header
            auth_header = response.headers.get('Authorization')
            if auth_header:
                token = auth_header.replace('Token ', '')
                print(f"Retrieved existing token: {token}")
                return token
        
        print(f"Signin failed: {response.status_code}")
        return None
        
    except Exception as e:
        print(f"Signin error: {e}")
        return None

def create_macro_buckets(token):
    """Create additional macro data buckets"""
    
    if not token:
        return
        
    headers = {
        "Authorization": f"Token {token}",
        "Content-Type": "application/json"
    }
    
    macro_buckets = [
        "macro_data",
        "treasury_data", 
        "economic_indicators",
        "finra_data"
    ]
    
    print("Creating macro data buckets...")
    
    # Get org ID first
    try:
        response = requests.get(f"{INFLUXDB_URL}/api/v2/orgs", headers=headers, timeout=10)
        if response.status_code == 200:
            orgs = response.json().get("orgs", [])
            org_id = None
            for org in orgs:
                if org.get("name") == ORG_NAME:
                    org_id = org.get("id")
                    break
            
            if not org_id:
                print("Could not find organization")
                return
                
            # Create buckets
            for bucket_name in macro_buckets:
                bucket_data = {
                    "name": bucket_name,
                    "orgID": org_id,
                    "retentionRules": [{"type": "expire", "everySeconds": 0}]
                }
                
                try:
                    response = requests.post(f"{INFLUXDB_URL}/api/v2/buckets", 
                                           json=bucket_data, headers=headers, timeout=10)
                    if response.status_code == 201:
                        print(f"   Created bucket: {bucket_name}")
                    elif response.status_code == 422:
                        print(f"   Bucket exists: {bucket_name}")
                    else:
                        print(f"   Failed to create {bucket_name}: {response.status_code}")
                except Exception as e:
                    print(f"   Error creating {bucket_name}: {e}")
                    
    except Exception as e:
        print(f"Error getting organization: {e}")

def main():
    print("InfluxDB Setup & Token Recovery")
    print("=" * 50)
    
    # Setup InfluxDB and get token
    token = setup_influxdb()
    
    if token:
        print(f"\nSUCCESS! Your InfluxDB token is:")
        print(f"{token}")
        print(f"\nUpdate your Grafana datasource with this token:")
        print(f"   1. Go to http://localhost:3000/connections/datasources")
        print(f"   2. Click on 'InfluxDB' datasource")
        print(f"   3. Update the token field with: {token}")
        print(f"   4. Click 'Save & test'")
        
        # Create macro buckets
        create_macro_buckets(token)
        
        print(f"\nInfluxDB is ready for your macro economic dashboard!")
        
    else:
        print(f"\nFailed to get InfluxDB token")
        print(f"   Try restarting InfluxDB: docker-compose restart influxdb")

if __name__ == "__main__":
    main()