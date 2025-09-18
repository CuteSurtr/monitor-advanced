#!/usr/bin/env python3
"""
Sample Data Population Script for Multi-Asset Trading System
Populates tables with sample data for testing dashboards
"""

import psycopg2
import logging
import os
from datetime import datetime, timedelta
import random

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'postgres'),  # Use Docker service name
    'port': int(os.getenv('DB_PORT', '5432')),
    'database': os.getenv('DB_NAME', 'stock_monitor'),
    'user': os.getenv('DB_USER', 'stock_user'),
    'password': os.getenv('DB_PASSWORD', 'stock_password')
}

def populate_tick_data():
    """Populate tick_data table with sample data"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        logger.info("Populating tick_data table with sample data...")
        
        # Get asset IDs from master tables
        cursor.execute("SELECT id, symbol FROM market_data.stocks LIMIT 5")
        stocks = cursor.fetchall()
        
        cursor.execute("SELECT id, symbol FROM market_data.cryptocurrencies LIMIT 3")
        cryptos = cursor.fetchall()
        
        cursor.execute("SELECT id, symbol FROM market_data.forex_pairs LIMIT 3")
        forex = cursor.fetchall()
        
        cursor.execute("SELECT id, symbol FROM market_data.commodities LIMIT 3")
        commodities = cursor.fetchall()
        
        # Combine all assets
        all_assets = []
        for stock_id, symbol in stocks:
            all_assets.append(('stock', stock_id, symbol))
        for crypto_id, symbol in cryptos:
            all_assets.append(('crypto', crypto_id, symbol))
        for forex_id, symbol in forex:
            all_assets.append(('forex', forex_id, symbol))
        for commodity_id, symbol in commodities:
            all_assets.append(('commodity', commodity_id, symbol))
        
        # Generate sample tick data for the last 4 hours
        base_time = datetime.utcnow() - timedelta(hours=4)
        
        for asset_type, asset_id, symbol in all_assets:
            logger.info(f"Generating data for {asset_type}: {symbol}")
            
            # Generate data points every 30 seconds for 4 hours
            for i in range(480):  # 4 hours * 60 minutes * 2 (30-second intervals)
                timestamp = base_time + timedelta(seconds=i * 30)
                
                # Generate realistic price data
                base_price = random.uniform(50, 500)
                price_change = random.uniform(-0.02, 0.02)  # ±2% change
                current_price = base_price * (1 + price_change)
                
                bid_price = current_price * 0.9995  # Slightly lower bid
                ask_price = current_price * 1.0005  # Slightly higher ask
                volume = random.uniform(1000, 100000)
                trade_count = random.randint(1, 50)
                
                cursor.execute("""
                    INSERT INTO market_data.tick_data 
                    (timestamp, asset_id, asset_type, bid_price, ask_price, last_price, volume, trade_count)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (timestamp, asset_id, asset_type, bid_price, ask_price, current_price, volume, trade_count))
        
        conn.commit()
        logger.info("tick_data table populated successfully!")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        logger.error(f"Error populating tick_data: {e}")
        raise

def populate_microstructure_features():
    """Populate microstructure_features table with sample data"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        logger.info("Populating microstructure_features table with sample data...")
        
        # Get asset IDs from master tables
        cursor.execute("SELECT id, symbol FROM market_data.stocks LIMIT 5")
        stocks = cursor.fetchall()
        
        cursor.execute("SELECT id, symbol FROM market_data.cryptocurrencies LIMIT 3")
        cryptos = cursor.fetchall()
        
        cursor.execute("SELECT id, symbol FROM market_data.forex_pairs LIMIT 3")
        forex = cursor.fetchall()
        
        cursor.execute("SELECT id, symbol FROM market_data.commodities LIMIT 3")
        commodities = cursor.fetchall()
        
        # Combine all assets
        all_assets = []
        for stock_id, symbol in stocks:
            all_assets.append(('stock', stock_id, symbol))
        for crypto_id, symbol in cryptos:
            all_assets.append(('crypto', crypto_id, symbol))
        for forex_id, symbol in forex:
            all_assets.append(('forex', forex_id, symbol))
        for commodity_id, symbol in commodities:
            all_assets.append(('commodity', commodity_id, symbol))
        
        # Generate sample microstructure data for the last 4 hours
        base_time = datetime.utcnow() - timedelta(hours=4)
        
        for asset_type, asset_id, symbol in all_assets:
            logger.info(f"Generating microstructure data for {asset_type}: {symbol}")
            
            # Generate data points every 5 minutes for 4 hours
            for i in range(48):  # 4 hours * 12 (5-minute intervals)
                timestamp = base_time + timedelta(minutes=i * 5)
                
                                            # Generate realistic microstructure metrics
                            bid_ask_spread = random.uniform(0.001, 0.05)  # 0.1% to 5% spread
                            mid_price = random.uniform(50, 500)
                            price_impact = random.uniform(0.0001, 0.01)  # 0.01% to 1% impact
                            realized_volatility = random.uniform(0.1, 0.5)  # 10% to 50% volatility
                            trade_intensity = random.uniform(0.1, 2.0)  # 0.1 to 2.0 intensity
                            order_flow_imbalance = random.uniform(-0.3, 0.3)  # -30% to +30% imbalance
                            liquidity_score = random.uniform(0.1, 1.0)  # 0.1 to 1.0 score
                
                                            cursor.execute("""
                                INSERT INTO analytics.microstructure_features 
                                (timestamp, asset_id, asset_type, bid_ask_spread, mid_price, price_impact, 
                                 realized_volatility, trade_intensity, order_flow_imbalance, liquidity_score)
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            """, (timestamp, asset_id, asset_type, bid_ask_spread, mid_price, price_impact,
                                  realized_volatility, trade_intensity, order_flow_imbalance, liquidity_score))
        
        conn.commit()
        logger.info("microstructure_features table populated successfully!")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        logger.error(f"Error populating microstructure_features: {e}")
        raise

def populate_market_regime():
    """Populate market_regime table with sample data"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        logger.info("Populating market_regime table with sample data...")
        
        # Generate sample market regime data for the last 24 hours
        base_time = datetime.utcnow() - timedelta(hours=24)
        
        regime_types = ['bull_market', 'bear_market', 'sideways', 'volatile', 'trending']
        volatility_regimes = ['low', 'medium', 'high', 'extreme']
        correlation_regimes = ['low', 'medium', 'high', 'decorrelated']
        
        for i in range(24):  # 24 hours
            timestamp = base_time + timedelta(hours=i)
            
            regime_type = random.choice(regime_types)
            confidence_score = random.uniform(0.6, 0.95)
            volatility_regime = random.choice(volatility_regimes)
            correlation_regime = random.choice(correlation_regimes)
            trend_strength = random.uniform(0.1, 0.9)
            
            cursor.execute("""
                INSERT INTO analytics.market_regime 
                (timestamp, regime_type, confidence_score, volatility_regime, correlation_regime, trend_strength)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (timestamp, regime_type, confidence_score, volatility_regime, correlation_regime, trend_strength))
        
        conn.commit()
        logger.info("market_regime table populated successfully!")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        logger.error(f"Error populating market_regime: {e}")
        raise

def main():
    """Main function to populate all tables with sample data"""
    try:
        logger.info("� Starting Sample Data Population for Multi-Asset Trading System")
        logger.info("=" * 60)
        
        # Populate tick data
        populate_tick_data()
        
        # Populate microstructure features
        populate_microstructure_features()
        
        # Populate market regime
        populate_market_regime()
        
        logger.info("\n" + "=" * 60)
        logger.info("� Sample Data Population Completed Successfully!")
        logger.info("\n� Tables populated:")
        logger.info("   market_data.tick_data")
        logger.info("   analytics.microstructure_features")
        logger.info("   analytics.market_regime")
        logger.info("\n� Next Steps:")
        logger.info("   1. The PostgreSQL HFT Analytics dashboard should now show data")
        logger.info("   2. Access Grafana at http://localhost:3000")
        logger.info("   3. Import the 'postgresql-hft-analytics-fixed.json' dashboard")
        logger.info("   4. Configure the PostgreSQL data source if needed")
        
        return True
        
    except Exception as e:
        logger.error(f"Sample data population failed: {e}")
        raise

if __name__ == "__main__":
    main()
