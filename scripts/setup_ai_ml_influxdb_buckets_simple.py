"""
InfluxDB AI/ML Analytics Bucket Setup - Windows Compatible
Comprehensive bucket schema for AI/ML trading analytics and data storage
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from influxdb_client import InfluxDBClient, Point, WriteOptions
from influxdb_client.client.write_api import SYNCHRONOUS
import pandas as pd
import numpy as np

# Configuration
INFLUXDB_URL = "http://localhost:8086"
INFLUXDB_TOKEN = "xEoh_d1wMmj_8sE2ipM1nht5Iq_iJiziHWVGvt9Haplv8QPDuR6oFTRIcX3rT8rG1M6H21tk0sSTv5ujfrPRDg=="
INFLUXDB_ORG = "stock_monitor"

# AI/ML specific buckets and retention policies
AI_ML_BUCKETS = {
    "ai_ml_analytics": {
        "description": "Main AI/ML analytics and model performance data",
        "retention_period": "365d",
        "measurements": [
            "model_performance",
            "ml_signals",
            "feature_importance",
            "model_training",
            "prediction_accuracy",
            "ensemble_results"
        ]
    },
    "price_predictions": {
        "description": "AI price predictions and forecasting data",
        "retention_period": "90d",
        "measurements": [
            "price_predictions",
            "volatility_predictions",
            "trend_predictions",
            "confidence_intervals"
        ]
    },
    "sentiment_analytics": {
        "description": "News and social sentiment analysis data",
        "retention_period": "180d",
        "measurements": [
            "sentiment_analysis",
            "news_impact",
            "social_sentiment",
            "sentiment_scores"
        ]
    },
    "risk_analytics": {
        "description": "AI-enhanced risk metrics and calculations",
        "retention_period": "365d",
        "measurements": [
            "risk_analytics",
            "var_calculations",
            "stress_test_results",
            "correlation_analysis",
            "portfolio_optimization"
        ]
    },
    "feature_store": {
        "description": "ML feature engineering and storage",
        "retention_period": "730d",
        "measurements": [
            "technical_features",
            "fundamental_features",
            "market_microstructure",
            "alternative_data"
        ]
    }
}

class AIMLInfluxDBSetup:
    """Setup and manage InfluxDB buckets for AI/ML analytics."""
    
    def __init__(self):
        self.client = InfluxDBClient(
            url=INFLUXDB_URL, 
            token=INFLUXDB_TOKEN, 
            org=INFLUXDB_ORG
        )
        self.buckets_api = self.client.buckets_api()
        self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
        self.query_api = self.client.query_api()
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    async def create_all_buckets(self):
        """Create all AI/ML buckets with proper retention policies."""
        try:
            for bucket_name, config in AI_ML_BUCKETS.items():
                await self._create_bucket_if_not_exists(bucket_name, config)
                
            self.logger.info("SUCCESS: All AI/ML buckets created successfully")
            
        except Exception as e:
            self.logger.error(f"ERROR: Failed to create buckets: {e}")
            raise
    
    async def _create_bucket_if_not_exists(self, bucket_name: str, config: Dict[str, Any]):
        """Create bucket if it doesn't exist."""
        try:
            # Check if bucket exists
            existing_buckets = self.buckets_api.find_buckets()
            bucket_exists = any(b.name == bucket_name for b in existing_buckets.buckets)
            
            if not bucket_exists:
                # Parse retention period
                retention_seconds = self._parse_retention_period(config['retention_period'])
                
                # Create bucket
                bucket = self.buckets_api.create_bucket(
                    bucket_name=bucket_name,
                    org=INFLUXDB_ORG,
                    retention_rules=[{
                        'type': 'expire',
                        'everySeconds': retention_seconds
                    }],
                    description=config['description']
                )
                
                self.logger.info(f"SUCCESS: Created bucket: {bucket_name} with {config['retention_period']} retention")
            else:
                self.logger.info(f"INFO: Bucket {bucket_name} already exists")
                
        except Exception as e:
            self.logger.error(f"ERROR: Failed to create bucket {bucket_name}: {e}")
            raise
    
    def _parse_retention_period(self, period: str) -> int:
        """Parse retention period string to seconds."""
        if period.endswith('d'):
            return int(period[:-1]) * 24 * 3600
        elif period.endswith('h'):
            return int(period[:-1]) * 3600
        elif period.endswith('m'):
            return int(period[:-1]) * 60
        else:
            return int(period)
    
    async def populate_sample_ai_ml_data(self):
        """Populate buckets with sample AI/ML data for testing."""
        try:
            await self._populate_model_performance_data()
            await self._populate_ml_signals_data()
            await self._populate_feature_importance_data()
            await self._populate_sentiment_data()
            await self._populate_risk_analytics_data()
            await self._populate_price_predictions_data()
            
            self.logger.info("SUCCESS: Sample AI/ML data populated successfully")
            
        except Exception as e:
            self.logger.error(f"ERROR: Failed to populate sample data: {e}")
    
    async def _populate_model_performance_data(self):
        """Populate model performance metrics."""
        points = []
        models = ['lstm', 'transformer', 'random_forest', 'xgboost', 'ensemble']
        
        for i in range(100):
            timestamp = datetime.now() - timedelta(minutes=i*5)
            
            for model in models:
                # Model accuracy
                accuracy = np.random.normal(0.75, 0.1)
                accuracy = max(0.5, min(0.95, accuracy))
                
                point = Point("model_performance") \
                    .tag("model_name", model) \
                    .field("accuracy", accuracy) \
                    .field("precision", accuracy + np.random.normal(0, 0.05)) \
                    .field("recall", accuracy + np.random.normal(0, 0.05)) \
                    .field("f1_score", accuracy + np.random.normal(0, 0.03)) \
                    .field("confidence_score", np.random.uniform(0.6, 0.9)) \
                    .time(timestamp)
                points.append(point)
        
        self.write_api.write(bucket="ai_ml_analytics", record=points)
        self.logger.info("INFO: Model performance data populated")
    
    async def _populate_ml_signals_data(self):
        """Populate ML trading signals."""
        points = []
        symbols = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'NVDA', 'SPY', 'QQQ']
        models = ['lstm', 'transformer', 'random_forest', 'ensemble']
        
        for i in range(200):
            timestamp = datetime.now() - timedelta(minutes=i*2)
            
            for symbol in symbols:
                for model in models:
                    # Generate signal
                    signal_strength = np.random.uniform(0.1, 1.0)
                    signal_type = "buy" if np.random.random() > 0.5 else "sell"
                    
                    point = Point("ml_signals") \
                        .tag("symbol", symbol) \
                        .tag("model_name", model) \
                        .tag("signal_type", signal_type) \
                        .field("signal_strength", signal_strength) \
                        .field("confidence", np.random.uniform(0.5, 0.95)) \
                        .field("expected_return", np.random.normal(0.02, 0.05)) \
                        .time(timestamp)
                    points.append(point)
        
        self.write_api.write(bucket="ai_ml_analytics", record=points)
        self.logger.info("INFO: ML signals data populated")
    
    async def _populate_feature_importance_data(self):
        """Populate feature importance rankings."""
        points = []
        features = [
            'rsi_14', 'macd_signal', 'bollinger_position', 'volume_sma_ratio',
            'price_momentum', 'volatility_rank', 'sentiment_score', 'vix_level',
            'sector_rotation', 'market_breadth', 'options_flow', 'insider_activity'
        ]
        
        for i in range(50):
            timestamp = datetime.now() - timedelta(hours=i)
            
            # Shuffle feature importance
            importance_scores = np.random.dirichlet(np.ones(len(features))) * 100
            
            for feature, score in zip(features, importance_scores):
                point = Point("feature_importance") \
                    .tag("feature_name", feature) \
                    .field("importance_score", score) \
                    .field("stability_score", np.random.uniform(0.7, 0.95)) \
                    .time(timestamp)
                points.append(point)
        
        self.write_api.write(bucket="ai_ml_analytics", record=points)
        self.logger.info("INFO: Feature importance data populated")
    
    async def _populate_sentiment_data(self):
        """Populate sentiment analysis data."""
        points = []
        symbols = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'NVDA', 'SPY']
        
        for i in range(300):
            timestamp = datetime.now() - timedelta(minutes=i*10)
            
            # Overall market sentiment
            overall_sentiment = np.random.normal(0, 0.3)
            overall_sentiment = max(-1, min(1, overall_sentiment))
            
            point = Point("sentiment_analysis") \
                .field("overall_sentiment", overall_sentiment) \
                .field("news_sentiment", np.random.normal(0, 0.4)) \
                .field("social_sentiment", np.random.normal(0, 0.5)) \
                .field("options_sentiment", np.random.normal(0, 0.3)) \
                .time(timestamp)
            points.append(point)
            
            # Per-symbol sentiment
            for symbol in symbols:
                symbol_sentiment = overall_sentiment + np.random.normal(0, 0.2)
                symbol_sentiment = max(-1, min(1, symbol_sentiment))
                
                point = Point("sentiment_analysis") \
                    .tag("symbol", symbol) \
                    .field("sentiment_score", symbol_sentiment) \
                    .field("confidence", np.random.uniform(0.6, 0.9)) \
                    .field("news_volume", np.random.randint(10, 100)) \
                    .time(timestamp)
                points.append(point)
        
        self.write_api.write(bucket="sentiment_analytics", record=points)
        self.logger.info("INFO: Sentiment analysis data populated")
    
    async def _populate_risk_analytics_data(self):
        """Populate AI risk analytics."""
        points = []
        risk_metrics = ['var_95', 'var_99', 'cvar_95', 'cvar_99', 'max_drawdown', 'sharpe_ratio']
        
        for i in range(100):
            timestamp = datetime.now() - timedelta(minutes=i*15)
            
            for metric in risk_metrics:
                if 'var' in metric or 'cvar' in metric:
                    value = np.random.uniform(10000, 100000)  # VaR/CVaR in dollars
                elif metric == 'max_drawdown':
                    value = np.random.uniform(0.01, 0.15)  # Drawdown as percentage
                else:  # sharpe_ratio
                    value = np.random.normal(1.2, 0.5)
                
                point = Point("risk_analytics") \
                    .tag("metric_type", metric) \
                    .field("value", value) \
                    .field("confidence", np.random.uniform(0.8, 0.95)) \
                    .field("model_accuracy", np.random.uniform(0.75, 0.9)) \
                    .time(timestamp)
                points.append(point)
        
        self.write_api.write(bucket="ai_ml_analytics", record=points)
        self.logger.info("INFO: Risk analytics data populated")
    
    async def _populate_price_predictions_data(self):
        """Populate price prediction data."""
        points = []
        symbols = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'NVDA']
        
        for i in range(150):
            timestamp = datetime.now() - timedelta(minutes=i*5)
            
            for symbol in symbols:
                # Base price (simulate real price movement)
                base_price = 150 + (i * 0.1) + np.random.normal(0, 2)
                
                # Prediction with some accuracy
                prediction_error = np.random.normal(0, base_price * 0.02)
                predicted_price = base_price + prediction_error
                
                # Confidence intervals
                confidence_range = base_price * 0.05
                
                point = Point("price_predictions") \
                    .tag("symbol", symbol) \
                    .field("predicted_price", predicted_price) \
                    .field("confidence_upper", predicted_price + confidence_range) \
                    .field("confidence_lower", predicted_price - confidence_range) \
                    .field("prediction_horizon", 24) \
                    .field("model_confidence", np.random.uniform(0.7, 0.9)) \
                    .time(timestamp)
                points.append(point)
        
        self.write_api.write(bucket="price_predictions", record=points)
        self.logger.info("INFO: Price predictions data populated")
    
    def verify_bucket_setup(self):
        """Verify all buckets are created and accessible."""
        try:
            buckets = self.buckets_api.find_buckets()
            existing_bucket_names = [b.name for b in buckets.buckets]
            
            self.logger.info("INFO: Existing buckets:")
            for bucket_name in AI_ML_BUCKETS.keys():
                if bucket_name in existing_bucket_names:
                    self.logger.info(f"  SUCCESS: {bucket_name}")
                else:
                    self.logger.error(f"  ERROR: {bucket_name} - MISSING")
            
            # Test query on one bucket
            query = '''
                from(bucket: "ai_ml_analytics")
                |> range(start: -1h)
                |> filter(fn: (r) => r._measurement == "model_performance")
                |> limit(n: 1)
            '''
            
            result = self.query_api.query(query)
            if result:
                self.logger.info("SUCCESS: Query test successful - buckets are accessible")
            else:
                self.logger.warning("WARNING: No data found in test query")
                
        except Exception as e:
            self.logger.error(f"ERROR: Bucket verification failed: {e}")
    
    def close(self):
        """Close InfluxDB connection."""
        self.client.close()

async def main():
    """Main setup function."""
    setup = AIMLInfluxDBSetup()
    
    try:
        print("Starting AI/ML InfluxDB Setup...")
        
        # Create buckets
        print("\nCreating AI/ML buckets...")
        await setup.create_all_buckets()
        
        # Populate with sample data
        print("\nPopulating sample data...")
        await setup.populate_sample_ai_ml_data()
        
        # Verify setup
        print("\nVerifying setup...")
        setup.verify_bucket_setup()
        
        print("\nSUCCESS: AI/ML InfluxDB setup completed successfully!")
        print("\nAvailable buckets:")
        for bucket_name, config in AI_ML_BUCKETS.items():
            print(f"  • {bucket_name}: {config['description']}")
        
        print("\nDashboard Integration:")
        print("  • Import comprehensive-professional-trading-dashboard-ai-ml-enhanced.json")
        print("  • Configure InfluxDB datasource with URL: http://localhost:8086")
        print("  • Use token for authentication")
        
    except Exception as e:
        print(f"ERROR: Setup failed: {e}")
    finally:
        setup.close()

if __name__ == "__main__":
    asyncio.run(main())