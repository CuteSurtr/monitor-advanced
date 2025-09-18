#!/usr/bin/env python3
"""
Get or create InfluxDB token using different methods
"""

import requests
import json
import base64
import os

INFLUXDB_URL = "http://localhost:8086"

def try_get_token_method1():
    """Method 1: Try to create token via setup endpoint reset"""
    print("Method 1: Creating fresh token...")
    
    # Force setup (this might create a new token)
    setup_data = {
        "username": os.getenv("INFLUXDB_ADMIN_USER", "admin"),
        "password": os.getenv("INFLUXDB_ADMIN_PASSWORD", "admin123"), 
        "org": "stock_monitor",
        "bucket": "market_data",
        "retentionPeriodSeconds": 0
    }
    
    try:
        response = requests.post(f"{INFLUXDB_URL}/api/v2/setup", json=setup_data, timeout=10)
        print(f"Setup response: {response.status_code}")
        
        if response.status_code == 201:
            result = response.json()
            token = result.get("auth", {}).get("token")
            print(f"SUCCESS: Got token from setup: {token}")
            return token
        elif response.status_code == 422:
            print("Already setup, trying method 2...")
            return None
        else:
            print(f"Setup failed: {response.text}")
            return None
            
    except Exception as e:
        print(f"Setup error: {e}")
        return None

def try_get_token_method2():
    """Method 2: Use basic auth to create a token"""
    print("Method 2: Using basic auth...")
    
    # Try basic auth
    auth = base64.b64encode(b"admin:admin123").decode()
    headers = {
        "Authorization": f"Basic {auth}",
        "Content-Type": "application/json"
    }
    
    # Try to get orgs first
    try:
        response = requests.get(f"{INFLUXDB_URL}/api/v2/orgs", headers=headers, timeout=10)
        print(f"Orgs response: {response.status_code}")
        
        if response.status_code == 200:
            orgs = response.json().get("orgs", [])
            print(f"Found {len(orgs)} organizations")
            
            if orgs:
                org_id = orgs[0].get("id")
                # Create token
                token_data = {
                    "description": "Grafana Access Token",
                    "orgID": org_id,
                    "permissions": [
                        {"action": "read", "resource": {"type": "buckets"}},
                        {"action": "write", "resource": {"type": "buckets"}},
                        {"action": "read", "resource": {"type": "orgs"}},
                        {"action": "read", "resource": {"type": "authorizations"}}
                    ]
                }
                
                response = requests.post(f"{INFLUXDB_URL}/api/v2/authorizations", 
                                       json=token_data, headers=headers, timeout=10)
                print(f"Token creation response: {response.status_code}")
                
                if response.status_code == 201:
                    result = response.json()
                    token = result.get("token")
                    print(f"SUCCESS: Created new token: {token}")
                    return token
                else:
                    print(f"Token creation failed: {response.text}")
        else:
            print(f"Orgs request failed: {response.text}")
            
    except Exception as e:
        print(f"Basic auth error: {e}")
        
    return None

def try_get_token_method3():
    """Method 3: Try to find existing tokens via config"""
    print("Method 3: Looking for existing config...")
    
    # Use the original token from datasource config as a test
    test_tokens = [
        "xEoh_d1w_9u4rUmgZLCUqckVK5qGnF1FNs2_hzrrzfXQCXLJRRYPh5oqcE_T0nYmF7jqsJ-O6r2OEUVDWV-kew==",
        "LruN3MmatpXFMakJ4rhApSuug29-eI60aA3DlJiYk7LwuEFZyqraujV0vI02eSFmRebAVMesawDWGUXBGeumKA=="
    ]
    
    for token in test_tokens:
        print(f"Testing token: {token[:20]}...")
        headers = {"Authorization": f"Token {token}"}
        
        try:
            response = requests.get(f"{INFLUXDB_URL}/api/v2/orgs", headers=headers, timeout=5)
            if response.status_code == 200:
                print(f"SUCCESS: Working token found: {token}")
                return token
            else:
                print(f"Token failed: {response.status_code}")
        except Exception as e:
            print(f"Token test error: {e}")
    
    return None

def main():
    print("InfluxDB Token Recovery")
    print("=" * 30)
    
    # Try different methods
    for method in [try_get_token_method3, try_get_token_method1, try_get_token_method2]:
        token = method()
        if token:
            print(f"\n*** FINAL TOKEN ***")
            print(f"{token}")
            print(f"\nUpdate your Grafana datasource:")
            print(f"1. Go to http://localhost:3000/connections/datasources")  
            print(f"2. Edit the InfluxDB datasource")
            print(f"3. Replace the token with: {token}")
            print(f"4. Save & test")
            return
    
    print("\nAll methods failed. Creating a completely fresh InfluxDB instance...")
    print("Run: docker-compose down influxdb && docker volume rm monitoradvanced_influxdb_data")

if __name__ == "__main__":
    main()