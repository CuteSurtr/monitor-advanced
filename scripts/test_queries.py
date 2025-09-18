"""
Test InfluxDB queries to ensure dashboard will work
"""

import requests
import json
import os

# Configuration
INFLUXDB_URL = "http://localhost:8086"
INFLUXDB_TOKEN = os.getenv("INFLUXDB_TOKEN", "xEoh_d1wMmj_8sE2ipM1nht5Iq_iJiziHWVGvt9Haplv8QPDuR6oFTRIcX3rT8rG1M6H21tk0ssTv5ujfrPRDg==")
INFLUXDB_ORG = "stock_monitor"

def test_query(query, description):
    """Test a Flux query and return results."""
    print(f"\nTesting: {description}")
    print(f"Query: {query}")
    
    headers = {
        'Authorization': f'Token {INFLUXDB_TOKEN}',
        'Content-Type': 'application/vnd.flux'
    }
    
    url = f"{INFLUXDB_URL}/api/v2/query?org={INFLUXDB_ORG}"
    
    try:
        response = requests.post(url, headers=headers, data=query)
        
        if response.status_code == 200:
            # Count lines in response (rough data point count)
            lines = response.text.strip().split('\n')
            data_lines = [line for line in lines if line and not line.startswith('#') and ',' in line]
            print(f"SUCCESS: {len(data_lines)} data points found")
            return True
        else:
            print(f"ERROR: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"EXCEPTION: {e}")
        return False

def main():
    """Test all dashboard queries."""
    print("Testing InfluxDB queries for dashboard compatibility...")
    
    # Test queries that match the dashboard
    queries = [
        {
            "query": """from(bucket: "ai_ml_analytics")
|> range(start: -24h)
|> filter(fn: (r) => r._measurement == "feature_importance")
|> filter(fn: (r) => r._field == "importance_score")
|> group(columns: ["feature_name"])
|> last()""",
            "description": "Feature Importance (Pie Chart)"
        },
        {
            "query": """from(bucket: "ai_ml_analytics")
|> range(start: -6h)
|> filter(fn: (r) => r._measurement == "ml_signals")
|> filter(fn: (r) => r._field == "signal_strength")
|> group(columns: ["symbol", "signal_type", "model_name"])
|> last()
|> limit(n: 20)""",
            "description": "Trading Signals (Table)"
        },
        {
            "query": """from(bucket: "ai_ml_analytics")
|> range(start: -6h)
|> filter(fn: (r) => r._measurement == "ml_signals")
|> filter(fn: (r) => r._field == "signal_strength")
|> window(every: 10m)
|> mean()
|> duplicate(column: "_stop", as: "_time")
|> window(every: inf)""",
            "description": "Signal Strength Trends (Time Series)"
        },
        {
            "query": """from(bucket: "ai_ml_analytics")
|> range(start: -6h)
|> filter(fn: (r) => r._measurement == "ml_signals")
|> filter(fn: (r) => r._field == "confidence")
|> window(every: 10m)
|> mean()
|> duplicate(column: "_stop", as: "_time")
|> window(every: inf)""",
            "description": "Model Confidence (Time Series)"
        },
        {
            "query": """from(bucket: "price_predictions")
|> range(start: -6h)
|> filter(fn: (r) => r._measurement == "price_predictions")
|> filter(fn: (r) => r.symbol == "AAPL")
|> window(every: 30m)
|> mean()
|> duplicate(column: "_stop", as: "_time")
|> window(every: inf)""",
            "description": "Price Predictions (Time Series)"
        },
        {
            "query": """from(bucket: "sentiment_analytics")
|> range(start: -1h)
|> filter(fn: (r) => r._measurement == "sentiment_analysis")
|> filter(fn: (r) => r._field == "overall_sentiment")
|> last()""",
            "description": "Market Sentiment (Gauge)"
        },
        {
            "query": """from(bucket: "sentiment_analytics")
|> range(start: -6h)
|> filter(fn: (r) => r._measurement == "sentiment_analysis")
|> window(every: 30m)
|> mean()
|> duplicate(column: "_stop", as: "_time")
|> window(every: inf)""",
            "description": "Sentiment Trends (Time Series)"
        }
    ]
    
    print("=" * 60)
    
    success_count = 0
    total_count = len(queries)
    
    for i, test in enumerate(queries, 1):
        print(f"\n[{i}/{total_count}]", end=" ")
        if test_query(test["query"], test["description"]):
            success_count += 1
    
    print("\n" + "=" * 60)
    print(f"SUMMARY: {success_count}/{total_count} queries successful")
    
    if success_count == total_count:
        print("SUCCESS: All queries working! Dashboard should display data correctly.")
        print("\nNext steps:")
        print("1. Open Grafana: http://localhost:3000")
        print("2. Import: simple-ai-ml-dashboard.json")
        print("3. Configure InfluxDB datasource if needed")
    else:
        print("WARNING: Some queries failed. Dashboard may have compilation errors.")
        
    return success_count == total_count

if __name__ == "__main__":
    main()