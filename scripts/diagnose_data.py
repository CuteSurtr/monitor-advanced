"""
Diagnose InfluxDB data issues for dashboard
"""
import requests
import json
import os

# Configuration
INFLUXDB_URL = "http://localhost:8086"
INFLUXDB_TOKEN = os.getenv("INFLUXDB_TOKEN", "xEoh_d1wMmj_8sE2ipM1nht5Iq_iJiziHWVGvt9Haplv8QPDuR6oFTRIcX3rT8rG1M6H21tk0ssTv5ujfrPRDg==")
INFLUXDB_ORG = "stock_monitor"

def test_connection():
    """Test basic InfluxDB connection."""
    try:
        headers = {
            'Authorization': f'Token {INFLUXDB_TOKEN}',
        }
        response = requests.get(f"{INFLUXDB_URL}/health", headers=headers)
        print(f"InfluxDB Health Check: {response.status_code}")
        if response.status_code == 200:
            print("[SUCCESS] InfluxDB is running")
            return True
        else:
            print(f"[ERROR] InfluxDB health check failed: {response.text}")
            return False
    except Exception as e:
        print(f"[ERROR] Connection error: {e}")
        return False

def check_buckets():
    """Check available buckets."""
    headers = {
        'Authorization': f'Token {INFLUXDB_TOKEN}',
    }
    
    try:
        response = requests.get(f"{INFLUXDB_URL}/api/v2/buckets?org={INFLUXDB_ORG}", headers=headers)
        if response.status_code == 200:
            buckets = response.json()['buckets']
            print(f"\n[SUCCESS] Found {len(buckets)} buckets:")
            for bucket in buckets:
                print(f"  - {bucket['name']} (ID: {bucket['id']})")
            return True
        else:
            print(f"[ERROR] Failed to get buckets: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"[ERROR] Error checking buckets: {e}")
        return False

def test_simple_query():
    """Test a very simple query."""
    headers = {
        'Authorization': f'Token {INFLUXDB_TOKEN}',
        'Content-Type': 'application/vnd.flux'
    }
    
    # Very basic query
    query = 'buckets() |> limit(n: 5)'
    
    try:
        response = requests.post(
            f"{INFLUXDB_URL}/api/v2/query?org={INFLUXDB_ORG}",
            headers=headers,
            data=query
        )
        
        if response.status_code == 200:
            print("\n[SUCCESS] Basic Flux query works")
            lines = response.text.strip().split('\n')
            data_lines = [line for line in lines if line and not line.startswith('#')]
            print(f"  Found {len(data_lines)} data lines")
            return True
        else:
            print(f"\n[ERROR] Basic query failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"\n[ERROR] Query error: {e}")
        return False

def check_bucket_data(bucket_name):
    """Check if a specific bucket has data."""
    headers = {
        'Authorization': f'Token {INFLUXDB_TOKEN}',
        'Content-Type': 'application/vnd.flux'
    }
    
    query = f'''
    from(bucket: "{bucket_name}")
    |> range(start: -24h)
    |> limit(n: 5)
    '''
    
    try:
        response = requests.post(
            f"{INFLUXDB_URL}/api/v2/query?org={INFLUXDB_ORG}",
            headers=headers,
            data=query
        )
        
        if response.status_code == 200:
            lines = response.text.strip().split('\n')
            data_lines = [line for line in lines if line and not line.startswith('#') and ',' in line]
            
            print(f"\n[SUCCESS] {bucket_name}: {len(data_lines)} data points found")
            if data_lines:
                print(f"  Sample: {data_lines[0][:100]}...")
            return len(data_lines) > 0
        else:
            print(f"\n[ERROR] {bucket_name}: Query failed - {response.status_code}")
            print(f"  Error: {response.text}")
            return False
    except Exception as e:
        print(f"\n[ERROR] {bucket_name}: Error - {e}")
        return False

def check_measurements(bucket_name):
    """Check what measurements exist in a bucket."""
    headers = {
        'Authorization': f'Token {INFLUXDB_TOKEN}',
        'Content-Type': 'application/vnd.flux'
    }
    
    query = f'''
    import "influxdata/influxdb/schema"
    schema.measurements(bucket: "{bucket_name}")
    |> limit(n: 10)
    '''
    
    try:
        response = requests.post(
            f"{INFLUXDB_URL}/api/v2/query?org={INFLUXDB_ORG}",
            headers=headers,
            data=query
        )
        
        if response.status_code == 200:
            lines = response.text.strip().split('\n')
            measurements = []
            for line in lines:
                if line and not line.startswith('#') and ',' in line:
                    parts = line.split(',')
                    if len(parts) > 1:
                        # Extract measurement name from CSV
                        measurement = parts[-1].strip().strip('"')
                        if measurement and measurement != '_value':
                            measurements.append(measurement)
            
            print(f"\n[SUCCESS] {bucket_name} measurements: {list(set(measurements))}")
            return list(set(measurements))
        else:
            print(f"\n[ERROR] {bucket_name}: Failed to get measurements - {response.status_code}")
            return []
    except Exception as e:
        print(f"\n[ERROR] {bucket_name}: Error getting measurements - {e}")
        return []

def main():
    """Run all diagnostics."""
    print("=== InfluxDB Dashboard Diagnostics ===\n")
    
    # Test connection
    if not test_connection():
        return
    
    # Check buckets
    if not check_buckets():
        return
    
    # Test basic query
    if not test_simple_query():
        return
    
    # Check each bucket for data
    buckets_to_check = ["ai_ml_analytics", "price_predictions", "sentiment_analytics"]
    
    for bucket in buckets_to_check:
        has_data = check_bucket_data(bucket)
        if has_data:
            measurements = check_measurements(bucket)
    
    print("\n=== Summary ===")
    print("If you see data above, the issue is likely in the dashboard queries.")
    print("If no data is found, we need to repopulate the buckets.")
    print("\nNext steps:")
    print("1. If data exists: Check Grafana datasource configuration")
    print("2. If no data: Run populate_more_data.py again")
    print("3. Check Grafana logs for query errors")

if __name__ == "__main__":
    main()