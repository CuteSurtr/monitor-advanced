#!/usr/bin/env python3
"""
Import Macro Economic Dashboard into Grafana
"""

import requests
import json
import time

# Grafana configuration
GRAFANA_URL = "http://localhost:3000"
GRAFANA_USER = "admin"
GRAFANA_PASSWORD = "admin"

def wait_for_grafana():
    """Wait for Grafana to be ready"""
    print("Waiting for Grafana to be ready...")
    
    for i in range(30):  # Wait up to 30 seconds
        try:
            response = requests.get(f"{GRAFANA_URL}/api/health", timeout=5)
            if response.status_code == 200:
                print("SUCCESS: Grafana is ready")
                return True
        except requests.exceptions.RequestException:
            pass
        
        print(f"Waiting... ({i+1}/30)")
        time.sleep(1)
    
    print("ERROR: Grafana not responding after 30 seconds")
    return False

def test_datasource():
    """Test InfluxDB datasource connection"""
    print("Testing InfluxDB datasource...")
    
    try:
        # Test datasource by UID
        response = requests.get(
            f"{GRAFANA_URL}/api/datasources/uid/influxdb-datasource",
            auth=(GRAFANA_USER, GRAFANA_PASSWORD)
        )
        
        if response.status_code == 200:
            ds_info = response.json()
            print(f"SUCCESS: Found datasource '{ds_info['name']}'")
            print(f"  Type: {ds_info['type']}")
            print(f"  URL: {ds_info['url']}")
            return True
        else:
            print(f"ERROR: Datasource not found (HTTP {response.status_code})")
            return False
            
    except Exception as e:
        print(f"ERROR: Failed to test datasource: {e}")
        return False

def import_dashboard():
    """Import the macro economic dashboard"""
    print("Importing Macro Economic Dashboard...")
    
    try:
        # Read dashboard JSON
        with open("grafana/dashboards/macro_economic_dashboard.json", "r") as f:
            dashboard_json = json.load(f)
        
        # Prepare import payload
        payload = {
            "dashboard": dashboard_json,
            "overwrite": True,
            "inputs": [
                {
                    "name": "DS_INFLUXDB",
                    "type": "datasource",
                    "pluginId": "influxdb",
                    "value": "influxdb-datasource"
                }
            ]
        }
        
        # Import dashboard
        response = requests.post(
            f"{GRAFANA_URL}/api/dashboards/import",
            auth=(GRAFANA_USER, GRAFANA_PASSWORD),
            headers={"Content-Type": "application/json"},
            json=payload
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"SUCCESS: Dashboard imported")
            print(f"  Title: {result['title']}")
            print(f"  UID: {result['uid']}")
            print(f"  URL: {GRAFANA_URL}/d/{result['uid']}")
            return True
        else:
            print(f"ERROR: Failed to import dashboard (HTTP {response.status_code})")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"ERROR: Failed to import dashboard: {e}")
        return False

def main():
    """Main function"""
    print("Grafana Macro Dashboard Setup")
    print("=" * 30)
    
    # Wait for Grafana
    if not wait_for_grafana():
        return False
    
    # Test datasource
    if not test_datasource():
        print("WARNING: Datasource test failed, but continuing...")
    
    # Import dashboard
    if not import_dashboard():
        return False
    
    print("\nSUCCESS: Macro Economic Dashboard is ready!")
    print(f"Access at: {GRAFANA_URL}")
    print("Dashboard: 'Comprehensive Macro Economic Dashboard'")
    
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)