#!/usr/bin/env python3
"""
Multi-Asset Trading Database Setup Script
Creates comprehensive schemas and tables for stocks, forex, crypto, and commodities
"""

import psycopg2
import logging
from datetime import datetime, timedelta
import random

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Database configuration
DB_CONFIG = {
    'host': 'postgres',  # Use Docker service name
    'port': 5432,
    'database': 'stock_monitor',
    'user': 'stock_user',
    'password': 'stock_password'
}

def create_schemas_and_tables():
    """Create all necessary schemas and tables for multi-asset trading"""
    
    # First, drop existing tables if they exist
    drop_commands = [
        "DROP TABLE IF EXISTS analytics.performance_attribution CASCADE;",
        "DROP TABLE IF EXISTS analytics.market_regime CASCADE;",
        "DROP TABLE IF EXISTS analytics.microstructure_features CASCADE;",
        "DROP TABLE IF EXISTS market_data.tick_data CASCADE;",
        "DROP TABLE IF EXISTS market_data.stocks CASCADE;",
        "DROP TABLE IF EXISTS market_data.cryptocurrencies CASCADE;",
        "DROP TABLE IF EXISTS market_data.forex_pairs CASCADE;",
        "DROP TABLE IF EXISTS market_data.commodities CASCADE;",
        "DROP TABLE IF EXISTS market_data.exchanges CASCADE;",
    ]
    
    # SQL commands to create schemas and tables
    sql_commands = [
        # Create schemas
        "CREATE SCHEMA IF NOT EXISTS market_data;",
        "CREATE SCHEMA IF NOT EXISTS portfolio;",
        "CREATE SCHEMA IF NOT EXISTS alerts;",
        "CREATE SCHEMA IF NOT EXISTS analytics;",
        "CREATE SCHEMA IF NOT EXISTS monitoring;",
        
        # Enable required extensions
        "CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";",
        "CREATE EXTENSION IF NOT EXISTS \"pg_stat_statements\";",
        "CREATE EXTENSION IF NOT EXISTS \"pg_trgm\";",
        "CREATE EXTENSION IF NOT EXISTS \"timescaledb\";",
        
        # Create exchanges table
        """
        CREATE TABLE IF NOT EXISTS market_data.exchanges (
            id SERIAL PRIMARY KEY,
            code VARCHAR(10) UNIQUE NOT NULL,
            name VARCHAR(100) NOT NULL,
            timezone VARCHAR(50) NOT NULL,
            market_open TIME NOT NULL,
            market_close TIME NOT NULL,
            currency VARCHAR(3) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """,
        
        # Create stocks master table
        """
        CREATE TABLE IF NOT EXISTS market_data.stocks (
            id SERIAL PRIMARY KEY,
            symbol VARCHAR(20) NOT NULL,
            exchange_id INTEGER REFERENCES market_data.exchanges(id),
            company_name VARCHAR(200),
            sector VARCHAR(100),
            industry VARCHAR(100),
            market_cap BIGINT,
            currency VARCHAR(3) DEFAULT 'USD',
            is_active BOOLEAN DEFAULT true,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(symbol, exchange_id)
        );
        """,
        
        # Create cryptocurrencies master table
        """
        CREATE TABLE IF NOT EXISTS market_data.cryptocurrencies (
            id SERIAL PRIMARY KEY,
            symbol VARCHAR(20) UNIQUE NOT NULL,
            name VARCHAR(100) NOT NULL,
            market_cap BIGINT,
            circulating_supply DECIMAL(30,8),
            total_supply DECIMAL(30,8),
            max_supply DECIMAL(30,8),
            is_active BOOLEAN DEFAULT true,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """,
        
        # Create forex pairs master table
        """
        CREATE TABLE IF NOT EXISTS market_data.forex_pairs (
            id SERIAL PRIMARY KEY,
            symbol VARCHAR(10) UNIQUE NOT NULL,
            base_currency VARCHAR(3) NOT NULL,
            quote_currency VARCHAR(3) NOT NULL,
            pip_size DECIMAL(10,8) DEFAULT 0.0001,
            is_major BOOLEAN DEFAULT false,
            is_active BOOLEAN DEFAULT true,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """,
        
        # Create commodities master table
        """
        CREATE TABLE IF NOT EXISTS market_data.commodities (
            id SERIAL PRIMARY KEY,
            symbol VARCHAR(20) UNIQUE NOT NULL,
            name VARCHAR(100) NOT NULL,
            asset_class VARCHAR(50) NOT NULL,
            unit VARCHAR(20),
            contract_size DECIMAL(15,4),
            tick_size DECIMAL(10,8),
            is_active BOOLEAN DEFAULT true,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """,
        
        # Create tick data table for HFT monitoring
        """
        CREATE TABLE IF NOT EXISTS market_data.tick_data (
            timestamp TIMESTAMPTZ NOT NULL,
            asset_id INTEGER NOT NULL,
            asset_type VARCHAR(20) NOT NULL CHECK (asset_type IN ('stock', 'crypto', 'forex', 'commodity')),
            bid_price DECIMAL(15,8),
            ask_price DECIMAL(15,8),
            last_price DECIMAL(15,8),
            volume DECIMAL(20,8),
            trade_count INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (timestamp, asset_id, asset_type)
        );
        """,
        
        # Create microstructure features table
        """
        CREATE TABLE IF NOT EXISTS analytics.microstructure_features (
            timestamp TIMESTAMPTZ NOT NULL,
            asset_id INTEGER NOT NULL,
            asset_type VARCHAR(20) NOT NULL CHECK (asset_type IN ('stock', 'crypto', 'forex', 'commodity')),
            bid_ask_spread DECIMAL(15,8),
            mid_price DECIMAL(15,8),
            price_impact DECIMAL(15,8),
            realized_volatility DECIMAL(15,8),
            trade_intensity DECIMAL(15,8),
            order_flow_imbalance DECIMAL(15,8),
            liquidity_score DECIMAL(15,8),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (timestamp, asset_id, asset_type)
        );
        """,
        
        # Create market regime table
        """
        CREATE TABLE IF NOT EXISTS analytics.market_regime (
            timestamp TIMESTAMPTZ NOT NULL,
            regime_type VARCHAR(50) NOT NULL,
            confidence_score DECIMAL(5,4),
            volatility_regime VARCHAR(20),
            correlation_regime VARCHAR(20),
            trend_strength DECIMAL(5,4),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (timestamp, regime_type)
        );
        """,
        
        # Create performance attribution table
        """
        CREATE TABLE IF NOT EXISTS analytics.performance_attribution (
            timestamp TIMESTAMPTZ NOT NULL,
            portfolio_id INTEGER,  -- Remove foreign key constraint for now
            total_return DECIMAL(10,6),
            market_return DECIMAL(10,6),
            alpha DECIMAL(10,6),
            beta DECIMAL(10,6),
            sharpe_ratio DECIMAL(10,6),
            max_drawdown DECIMAL(10,6),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (timestamp, portfolio_id)
        );
        """
    ]
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        logger.info("Dropping existing tables...")
        for sql in drop_commands:
            cursor.execute(sql)
            logger.info(f"Dropped: {sql[:50]}...")
        
        logger.info("Creating schemas and tables...")
        
        for sql in sql_commands:
            cursor.execute(sql)
            logger.info(f"Executed: {sql[:50]}...")
        
        conn.commit()
        logger.info("All schemas and tables created successfully!")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        logger.error(f"Error creating schemas and tables: {e}")
        raise

def populate_master_data():
    """Populate master tables with sample data"""
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        logger.info("Populating master tables with sample data...")
        
        # Insert exchanges
        exchanges_data = [
            ('NYSE', 'New York Stock Exchange', 'America/New_York', '09:30:00', '16:00:00', 'USD'),
            ('NASDAQ', 'NASDAQ Stock Market', 'America/New_York', '09:30:00', '16:00:00', 'USD'),
            ('LSE', 'London Stock Exchange', 'Europe/London', '08:00:00', '16:30:00', 'GBP'),
            ('TSE', 'Tokyo Stock Exchange', 'Asia/Tokyo', '09:00:00', '15:30:00', 'JPY'),
            ('FOREX', 'Forex Market', 'UTC', '00:00:00', '23:59:59', 'USD'),
            ('CRYPTO', 'Cryptocurrency Market', 'UTC', '00:00:00', '23:59:59', 'USD'),
            ('COMMODITY', 'Commodity Market', 'UTC', '00:00:00', '23:59:59', 'USD')
        ]
        
        for exchange in exchanges_data:
            cursor.execute("""
                INSERT INTO market_data.exchanges (code, name, timezone, market_open, market_close, currency)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (code) DO NOTHING
            """, exchange)
        
        # Insert sample stocks
        stocks_data = [
            ('AAPL', 11, 'Apple Inc.', 'Technology', 'Consumer Electronics', 3000000000000),
            ('MSFT', 11, 'Microsoft Corporation', 'Technology', 'Software', 2800000000000),
            ('GOOGL', 12, 'Alphabet Inc.', 'Technology', 'Internet Services', 1800000000000),
            ('TSLA', 12, 'Tesla Inc.', 'Consumer Discretionary', 'Automobiles', 800000000000),
            ('AMZN', 12, 'Amazon.com Inc.', 'Consumer Discretionary', 'Internet Retail', 1500000000000)
        ]
        
        for stock in stocks_data:
            cursor.execute("""
                INSERT INTO market_data.stocks (symbol, exchange_id, company_name, sector, industry, market_cap)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (symbol, exchange_id) DO NOTHING
            """, stock)
        
        # Insert sample cryptocurrencies
        crypto_data = [
            ('BTC', 'Bitcoin', 800000000000, 19500000, 21000000, 21000000),
            ('ETH', 'Ethereum', 300000000000, 120000000, 120000000, None),
            ('USDT', 'Tether', 80000000000, 80000000000, 80000000000, None),
            ('BNB', 'Binance Coin', 40000000000, 150000000, 150000000, 200000000),
            ('ADA', 'Cardano', 15000000000, 35000000000, 45000000000, 45000000000)
        ]
        
        for crypto in crypto_data:
            cursor.execute("""
                INSERT INTO market_data.cryptocurrencies (symbol, name, market_cap, circulating_supply, total_supply, max_supply)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (symbol) DO NOTHING
            """, crypto)
        
        # Insert sample forex pairs
        forex_data = [
            ('EUR/USD', 'EUR', 'USD', 0.0001, True),
            ('GBP/USD', 'GBP', 'USD', 0.0001, True),
            ('USD/JPY', 'USD', 'JPY', 0.01, True),
            ('USD/CHF', 'USD', 'CHF', 0.0001, True),
            ('AUD/USD', 'AUD', 'USD', 0.0001, False)
        ]
        
        for forex in forex_data:
            cursor.execute("""
                INSERT INTO market_data.forex_pairs (symbol, base_currency, quote_currency, pip_size, is_major)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (symbol) DO NOTHING
            """, forex)
        
        # Insert sample commodities
        commodities_data = [
            ('XAU/USD', 'Gold', 'Metals', 'Troy Ounce', 100, 0.1),
            ('XAG/USD', 'Silver', 'Metals', 'Troy Ounce', 5000, 0.001),
            ('WTI', 'Crude Oil WTI', 'Energy', 'Barrel', 1000, 0.01),
            ('BRENT', 'Crude Oil Brent', 'Energy', 'Barrel', 1000, 0.01),
            ('CORN', 'Corn', 'Agriculture', 'Bushel', 5000, 0.25)
        ]
        
        for commodity in commodities_data:
            cursor.execute("""
                INSERT INTO market_data.commodities (symbol, name, asset_class, unit, contract_size, tick_size)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (symbol) DO NOTHING
            """, commodity)
        
        conn.commit()
        logger.info("Master tables populated successfully!")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        logger.error(f"Error populating master data: {e}")
        raise

def create_timescale_hypertables():
    """Convert time-series tables to TimescaleDB hypertables"""
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        logger.info("Creating TimescaleDB hypertables...")
        
        # Convert tick_data to hypertable
        cursor.execute("""
            SELECT create_hypertable('market_data.tick_data', 'timestamp', 
                                   if_not_exists => TRUE, 
                                   migrate_data => TRUE);
        """)
        
        # Convert microstructure_features to hypertable
        cursor.execute("""
            SELECT create_hypertable('analytics.microstructure_features', 'timestamp', 
                                   if_not_exists => TRUE, 
                                   migrate_data => TRUE);
        """)
        
        # Convert market_regime to hypertable
        cursor.execute("""
            SELECT create_hypertable('analytics.market_regime', 'timestamp', 
                                   if_not_exists => TRUE, 
                                   migrate_data => TRUE);
        """)
        
        # Convert performance_attribution to hypertable
        cursor.execute("""
            SELECT create_hypertable('analytics.performance_attribution', 'timestamp', 
                                   if_not_exists => TRUE, 
                                   migrate_data => TRUE);
        """)
        
        conn.commit()
        logger.info("TimescaleDB hypertables created successfully!")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        logger.error(f"Error creating TimescaleDB hypertables: {e}")
        raise

def main():
    """Main function to set up the complete database"""
    try:
        logger.info("Starting multi-asset trading database setup...")
        
        create_schemas_and_tables()
        populate_master_data()
        create_timescale_hypertables()
        
        logger.info("Database setup completed successfully!")
        
    except Exception as e:
        logger.error(f"Database setup failed: {e}")
        raise

if __name__ == "__main__":
    main()
