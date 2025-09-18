"""
Setup InfluxDB with working configuration and sample data
"""
import requests
import json
import os
from datetime import datetime, timedelta
import random
import time

# InfluxDB setup
INFLUXDB_URL = "http://localhost:8086"

def setup_influxdb():
    """Setup InfluxDB from scratch"""
    
    print("Setting up InfluxDB...")
    
    # Setup with basic auth
    setup_data = {
        "username": os.getenv("INFLUXDB_ADMIN_USER", "admin"),
        "password": os.getenv("INFLUXDB_ADMIN_PASSWORD", "admin123"),
        "org": "stock_monitor",
        "bucket": "ai_ml_analytics",
        "retentionPeriodSeconds": 2592000  # 30 days
    }
    
    try:
        # Try setup
        response = requests.post(f"{INFLUXDB_URL}/api/v2/setup", json=setup_data)
        if response.status_code in [201, 422]:  # 422 means already setup
            print("[SUCCESS] InfluxDB setup completed or already exists")
            
            if response.status_code == 201:
                result = response.json()
                token = result['auth']['token']
                print(f"[SUCCESS] New token created: {token}")
                return token
            else:
                # Get existing token
                return get_existing_token()
        else:
            print(f"Setup failed: {response.status_code} - {response.text}")
            return get_existing_token()
            
    except Exception as e:
        print(f"Setup error: {e}")
        return get_existing_token()

def get_existing_token():
    """Try to get existing token using basic auth"""
    try:
        # Try basic auth to get token
        auth_data = {
            "username": os.getenv("INFLUXDB_ADMIN_USER", "admin"),
            "password": os.getenv("INFLUXDB_ADMIN_PASSWORD", "admin123")
        }
        
        response = requests.post(f"{INFLUXDB_URL}/api/v2/signin", json=auth_data)
        if response.status_code == 204:
            # Get auth token from cookies or try known token
            known_token = os.getenv("INFLUXDB_TOKEN", "xEoh_d1wMmj_8sE2ipM1nht5Iq_iJiziHWVGvt9Haplv8QPDuR6oFTRIcX3rT8rG1M6H21tk0ssTv5ujfrPRDg==")
            print("[SUCCESS] Using existing token")
            return known_token
        else:
            print(f"Auth failed: {response.status_code}")
            return None
    except Exception as e:
        print(f"Auth error: {e}")
        return None

def create_buckets(token):
    """Create necessary buckets"""
    headers = {
        'Authorization': f'Token {token}',
        'Content-Type': 'application/json'
    }
    
    buckets = [
        {"name": "ai_ml_analytics", "orgID": "stock_monitor"},
        {"name": "price_predictions", "orgID": "stock_monitor"}, 
        {"name": "sentiment_analytics", "orgID": "stock_monitor"}
    ]
    
    for bucket_data in buckets:
        try:
            response = requests.post(f"{INFLUXDB_URL}/api/v2/buckets", 
                                   headers=headers, json=bucket_data)
            if response.status_code in [201, 422]:  # 422 means already exists
                print(f"[SUCCESS] Bucket '{bucket_data['name']}' ready")
            else:
                print(f"Bucket creation failed: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"Bucket creation error: {e}")

def populate_simple_data(token):
    """Populate with simple line protocol data"""
    
    headers = {
        'Authorization': f'Token {token}',
        'Content-Type': 'text/plain'
    }
    
    # Generate simple data
    now = datetime.utcnow()
    data_lines = []
    
    print("Generating sample data...")
    
    # Feature importance data
    features = ['rsi', 'macd', 'bollinger', 'volume', 'momentum']
    for i in range(50):
        timestamp = int((now - timedelta(minutes=i*5)).timestamp() * 1000000000)
        for j, feature in enumerate(features):
            importance = random.uniform(10, 30)
            line = f"feature_importance,feature_name={feature} importance_score={importance} {timestamp}"
            data_lines.append(line)
    
    # ML signals data  
    symbols = ['AAPL', 'GOOGL', 'MSFT']
    models = ['lstm', 'rf', 'xgb']
    for i in range(30):
        timestamp = int((now - timedelta(minutes=i*10)).timestamp() * 1000000000)
        for symbol in symbols:
            for model in models:
                signal_strength = random.uniform(0.3, 0.9)
                confidence = random.uniform(0.6, 0.95)
                signal_type = random.choice(['buy', 'sell'])
                
                line = f"ml_signals,symbol={symbol},model_name={model},signal_type={signal_type} signal_strength={signal_strength},confidence={confidence} {timestamp}"
                data_lines.append(line)
    
    # Price predictions
    for i in range(20):
        timestamp = int((now - timedelta(minutes=i*15)).timestamp() * 1000000000)
        for symbol in symbols:
            price = random.uniform(150, 200)
            upper = price + random.uniform(5, 15)
            lower = price - random.uniform(5, 15)
            
            line = f"price_predictions,symbol={symbol} predicted_price={price},confidence_upper={upper},confidence_lower={lower} {timestamp}"
            data_lines.append(line)
    
    # Sentiment data
    for i in range(10):
        timestamp = int((now - timedelta(minutes=i*30)).timestamp() * 1000000000)
        sentiment = random.uniform(-0.5, 0.5)
        
        line = f"sentiment_analysis overall_sentiment={sentiment},news_sentiment={sentiment*0.8},social_sentiment={sentiment*1.2} {timestamp}"
        data_lines.append(line)
    
    # Write data to each bucket
    buckets = ['ai_ml_analytics', 'price_predictions', 'sentiment_analytics']
    
    for bucket in buckets:
        bucket_data = [line for line in data_lines if bucket.split('_')[0] in line or 'sentiment' in line]
        
        if bucket == 'ai_ml_analytics':
            bucket_data = [line for line in data_lines if 'feature_importance' in line or 'ml_signals' in line]
        elif bucket == 'price_predictions':
            bucket_data = [line for line in data_lines if 'price_predictions' in line]
        elif bucket == 'sentiment_analytics':
            bucket_data = [line for line in data_lines if 'sentiment_analysis' in line]
        
        if bucket_data:
            payload = '\n'.join(bucket_data)
            try:
                response = requests.post(f"{INFLUXDB_URL}/api/v2/write?org=stock_monitor&bucket={bucket}",
                                       headers=headers, data=payload)
                if response.status_code == 204:
                    print(f"[SUCCESS] Data written to {bucket}: {len(bucket_data)} lines")
                else:
                    print(f"Write failed for {bucket}: {response.status_code} - {response.text}")
            except Exception as e:
                print(f"Write error for {bucket}: {e}")
    
    return len(data_lines)

def test_data_query(token):
    """Test if data is readable"""
    headers = {
        'Authorization': f'Token {token}',
        'Content-Type': 'application/vnd.flux'
    }
    
    query = '''
    from(bucket: "ai_ml_analytics")
    |> range(start: -1h)
    |> limit(n: 5)
    '''
    
    try:
        response = requests.post(f"{INFLUXDB_URL}/api/v2/query?org=stock_monitor",
                               headers=headers, data=query)
        
        if response.status_code == 200:
            lines = response.text.strip().split('\n')
            data_lines = [line for line in lines if line and not line.startswith('#') and ',' in line]
            print(f"[SUCCESS] Query test successful: {len(data_lines)} data points found")
            return True
        else:
            print(f"Query failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"Query error: {e}")
        return False

def main():
    """Main setup function"""
    print("=== InfluxDB Working Setup ===\n")
    
    # Setup InfluxDB
    token = setup_influxdb()
    if not token:
        print("[ERROR] Failed to get token")
        return
    
    print(f"\nToken: {token}\n")
    
    # Create buckets
    create_buckets(token)
    
    # Populate data
    data_count = populate_simple_data(token)
    print(f"\nGenerated {data_count} data points")
    
    # Test query
    if test_data_query(token):
        print("\nInfluxDB is working properly!")
        print("\nDashboard connection details:")
        print(f"URL: http://localhost:8086")
        print(f"Token: {token}")
        print(f"Org: stock_monitor")
        print(f"UID: deuydarcrp81sf")
    else:
        print("\nData query test failed")

if __name__ == "__main__":
    main()