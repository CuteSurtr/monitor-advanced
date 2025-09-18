"""
Populate more recent data for AI/ML dashboard testing
"""

import asyncio
from datetime import datetime, timedelta
from influxdb_client import InfluxDBClient, Point, WriteOptions
from influxdb_client.client.write_api import SYNCHRONOUS
import numpy as np

# Configuration
INFLUXDB_URL = "http://localhost:8086"
INFLUXDB_TOKEN = "xEoh_d1wMmj_8sE2ipM1nht5Iq_iJiziHWVGvt9Haplv8QPDuR6oFTRIcX3rT8rG1M6H21tk0sSTv5ujfrPRDg=="
INFLUXDB_ORG = "stock_monitor"

def populate_recent_data():
    """Populate recent data for better dashboard visualization."""
    
    client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)
    write_api = client.write_api(write_options=SYNCHRONOUS)
    
    print("Populating recent AI/ML data...")
    
    # Current time
    now = datetime.now()
    
    # Populate recent feature importance data
    points = []
    features = [
        'rsi_14', 'macd_signal', 'bollinger_position', 'volume_sma_ratio',
        'price_momentum', 'volatility_rank', 'sentiment_score', 'vix_level',
        'sector_rotation', 'market_breadth', 'options_flow', 'insider_activity'
    ]
    
    # Add data for last 6 hours
    for i in range(72):  # Every 5 minutes for 6 hours
        timestamp = now - timedelta(minutes=i*5)
        
        # Feature importance (total = 100%)
        importance_scores = np.random.dirichlet(np.ones(len(features))) * 100
        
        for feature, score in zip(features, importance_scores):
            point = Point("feature_importance") \
                .tag("feature_name", feature) \
                .field("importance_score", float(score)) \
                .field("stability_score", np.random.uniform(0.7, 0.95)) \
                .time(timestamp)
            points.append(point)
    
    write_api.write(bucket="ai_ml_analytics", record=points)
    print(f"Added {len(points)} feature importance points")
    
    # Populate recent ML signals
    points = []
    symbols = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'NVDA', 'SPY', 'QQQ']
    models = ['lstm', 'transformer', 'random_forest', 'ensemble']
    
    for i in range(60):  # Every 3 minutes for 3 hours
        timestamp = now - timedelta(minutes=i*3)
        
        for symbol in symbols:
            for model in models:
                signal_strength = np.random.uniform(0.1, 1.0)
                signal_type = "buy" if np.random.random() > 0.4 else "sell"
                
                point = Point("ml_signals") \
                    .tag("symbol", symbol) \
                    .tag("model_name", model) \
                    .tag("signal_type", signal_type) \
                    .field("signal_strength", signal_strength) \
                    .field("confidence", np.random.uniform(0.5, 0.95)) \
                    .field("expected_return", np.random.normal(0.02, 0.05)) \
                    .time(timestamp)
                points.append(point)
    
    write_api.write(bucket="ai_ml_analytics", record=points)
    print(f"Added {len(points)} ML signals points")
    
    # Populate price predictions
    points = []
    symbols = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'NVDA']
    
    for i in range(72):  # Every 5 minutes for 6 hours
        timestamp = now - timedelta(minutes=i*5)
        
        for symbol in symbols:
            # Simulate realistic stock prices
            base_prices = {'AAPL': 175, 'GOOGL': 140, 'MSFT': 340, 'TSLA': 250, 'NVDA': 450}
            base_price = base_prices.get(symbol, 150)
            
            # Add some trend and noise
            trend = (72 - i) * 0.05  # Slight upward trend
            noise = np.random.normal(0, base_price * 0.01)
            predicted_price = base_price + trend + noise
            
            # Confidence intervals
            confidence_range = base_price * 0.03
            
            point = Point("price_predictions") \
                .tag("symbol", symbol) \
                .field("predicted_price", predicted_price) \
                .field("confidence_upper", predicted_price + confidence_range) \
                .field("confidence_lower", predicted_price - confidence_range) \
                .field("prediction_horizon", 24) \
                .field("model_confidence", np.random.uniform(0.7, 0.9)) \
                .time(timestamp)
            points.append(point)
    
    write_api.write(bucket="price_predictions", record=points)
    print(f"Added {len(points)} price prediction points")
    
    # Populate sentiment data
    points = []
    
    for i in range(36):  # Every 10 minutes for 6 hours
        timestamp = now - timedelta(minutes=i*10)
        
        # Overall market sentiment
        overall_sentiment = np.random.normal(0.1, 0.3)  # Slightly bullish
        overall_sentiment = max(-1, min(1, overall_sentiment))
        
        point = Point("sentiment_analysis") \
            .field("overall_sentiment", overall_sentiment) \
            .field("news_sentiment", np.random.normal(0, 0.4)) \
            .field("social_sentiment", np.random.normal(0, 0.5)) \
            .field("options_sentiment", np.random.normal(0, 0.3)) \
            .time(timestamp)
        points.append(point)
    
    write_api.write(bucket="sentiment_analytics", record=points)
    print(f"Added {len(points)} sentiment analysis points")
    
    client.close()
    print("Data population completed!")
    print("\nNext steps:")
    print("1. Open Grafana: http://localhost:3000")
    print("2. Import: comprehensive-professional-trading-dashboard-ai-ml-enhanced-fixed.json")
    print("3. Configure InfluxDB datasource with your token if needed")

if __name__ == "__main__":
    populate_recent_data()