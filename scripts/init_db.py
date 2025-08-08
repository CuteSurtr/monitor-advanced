#!/usr/bin/env python3
"""
Database initialization script for Stock Market Monitor.
Creates database schema, indexes, and initial data.
"""

import os
import sys
import asyncio
from pathlib import Path
import yaml
import json

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from src.utils.database import get_database_manager
from src.utils.config import get_config
from src.utils.structured_logger import get_logger

logger = get_logger(__name__)


class DatabaseInitializer:
    """Handles database initialization and setup."""
    
    def __init__(self):
        """Initialize database initializer."""
        self.config = get_config()
        self.db_manager = get_database_manager()
        
    async def initialize(self):
        """Initialize the database completely."""
        logger.info("Starting database initialization")
        
        try:
            # Test connection
            await self._test_connection()
            
            # Create schemas and tables
            await self._create_schemas()
            
            # Create indexes
            await self._create_indexes()
            
            # Create functions and triggers
            await self._create_functions()
            
            # Insert initial data
            await self._insert_initial_data()
            
            # Create views
            await self._create_views()
            
            # Grant permissions
            await self._grant_permissions()
            
            logger.info("Database initialization completed successfully")
            
        except Exception as e:
            logger.error("Database initialization failed", error=str(e), exc_info=True)
            raise
            
    async def _test_connection(self):
        """Test database connection."""
        logger.info("Testing database connection")
        
        try:
            result = await self.db_manager.execute_query("SELECT version()")
            if result:
                logger.info("Database connection successful", 
                           version=result[0]['version'] if result else 'unknown')
            else:
                raise Exception("Connection test failed")
        except Exception as e:
            logger.error("Database connection failed", error=str(e))
            raise
            
    async def _create_schemas(self):
        """Create database schemas and tables."""
        logger.info("Creating database schemas and tables")
        
        # Read and execute the init SQL file
        init_sql_path = Path(__file__).parent.parent / 'docker' / 'postgres' / 'init.sql'
        
        if not init_sql_path.exists():
            logger.error("Init SQL file not found", path=str(init_sql_path))
            raise FileNotFoundError(f"Init SQL file not found: {init_sql_path}")
            
        try:
            with open(init_sql_path, 'r') as f:
                sql_content = f.read()
                
            # Split by semicolon and execute each statement
            statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
            
            for i, statement in enumerate(statements):
                if statement.upper().startswith(('CREATE', 'INSERT', 'GRANT', 'SET')):
                    try:
                        await self.db_manager.execute_query(statement)
                        logger.debug("Executed SQL statement", statement_number=i+1)
                    except Exception as e:
                        # Log but continue for non-critical errors
                        logger.warning("SQL statement failed", 
                                     statement_number=i+1, 
                                     error=str(e))
                        
            logger.info("Database schemas created successfully")
            
        except Exception as e:
            logger.error("Schema creation failed", error=str(e))
            raise
            
    async def _create_indexes(self):
        """Create additional indexes for performance."""
        logger.info("Creating additional database indexes")
        
        additional_indexes = [
            # Performance indexes for frequent queries
            """
            CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_stock_prices_symbol_timestamp 
            ON market_data.stock_prices(stock_id, timestamp DESC) 
            WHERE timestamp > NOW() - INTERVAL '1 year'
            """,
            
            """
            CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_alert_instances_triggered_recent
            ON alerts.alert_instances(triggered_at DESC, status)
            WHERE triggered_at > NOW() - INTERVAL '30 days'
            """,
            
            """
            CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_portfolio_positions_active
            ON portfolio.positions(portfolio_id, last_updated DESC)
            WHERE quantity > 0
            """,
            
            """
            CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_technical_indicators_recent
            ON market_data.technical_indicators(stock_id, indicator_name, timestamp DESC)
            WHERE timestamp > NOW() - INTERVAL '90 days'
            """,
            
            # Partial indexes for better performance
            """
            CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_transactions_recent_buys
            ON portfolio.transactions(portfolio_id, transaction_date DESC)
            WHERE transaction_type = 'BUY' AND transaction_date > NOW() - INTERVAL '1 year'
            """,
            
            """
            CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_predictions_recent_accurate
            ON analytics.predictions(stock_id, prediction_date DESC)
            WHERE prediction_date > NOW() - INTERVAL '30 days' AND confidence_score > 0.7
            """
        ]
        
        for index_sql in additional_indexes:
            try:
                await self.db_manager.execute_query(index_sql)
                logger.debug("Created index successfully")
            except Exception as e:
                logger.warning("Index creation failed", error=str(e))
                # Continue with other indexes
                
        logger.info("Additional indexes created")
        
    async def _create_functions(self):
        """Create stored functions and procedures."""
        logger.info("Creating database functions")
        
        functions = [
            # Function to get portfolio performance metrics
            """
            CREATE OR REPLACE FUNCTION get_portfolio_performance(
                p_portfolio_id UUID,
                p_start_date TIMESTAMP DEFAULT NOW() - INTERVAL '30 days',
                p_end_date TIMESTAMP DEFAULT NOW()
            )
            RETURNS TABLE(
                date DATE,
                portfolio_value DECIMAL(20,4),
                daily_return DECIMAL(10,6),
                cumulative_return DECIMAL(10,6)
            ) AS $$
            BEGIN
                RETURN QUERY
                WITH daily_values AS (
                    SELECT 
                        DATE(timestamp) as value_date,
                        AVG(market_value) as avg_value
                    FROM portfolio.positions p
                    JOIN market_data.stock_prices sp ON p.stock_id = sp.stock_id
                    WHERE p.portfolio_id = p_portfolio_id
                    AND sp.timestamp BETWEEN p_start_date AND p_end_date
                    GROUP BY DATE(timestamp)
                    ORDER BY value_date
                ),
                returns AS (
                    SELECT 
                        value_date,
                        avg_value,
                        LAG(avg_value) OVER (ORDER BY value_date) as prev_value
                    FROM daily_values
                )
                SELECT 
                    value_date::DATE,
                    avg_value,
                    CASE 
                        WHEN prev_value IS NOT NULL THEN 
                            (avg_value - prev_value) / prev_value
                        ELSE 0
                    END as daily_return,
                    (avg_value - FIRST_VALUE(avg_value) OVER (ORDER BY value_date)) / 
                    FIRST_VALUE(avg_value) OVER (ORDER BY value_date) as cumulative_return
                FROM returns
                ORDER BY value_date;
            END;
            $$ LANGUAGE plpgsql;
            """,
            
            # Function to calculate stock volatility
            """
            CREATE OR REPLACE FUNCTION calculate_stock_volatility(
                p_stock_id INTEGER,
                p_days INTEGER DEFAULT 30
            )
            RETURNS DECIMAL(10,6) AS $$
            DECLARE
                volatility DECIMAL(10,6);
            BEGIN
                WITH daily_returns AS (
                    SELECT 
                        DATE(timestamp) as trade_date,
                        (close_price - LAG(close_price) OVER (ORDER BY timestamp)) / 
                        LAG(close_price) OVER (ORDER BY timestamp) as daily_return
                    FROM market_data.stock_prices
                    WHERE stock_id = p_stock_id
                    AND timestamp > NOW() - INTERVAL '%s days'
                    ORDER BY timestamp
                )
                SELECT STDDEV(daily_return) * SQRT(252) INTO volatility
                FROM daily_returns
                WHERE daily_return IS NOT NULL;
                
                RETURN COALESCE(volatility, 0);
            END;
            $$ LANGUAGE plpgsql;
            """,
            
            # Function to get market correlation
            """
            CREATE OR REPLACE FUNCTION calculate_correlation(
                p_stock1_id INTEGER,
                p_stock2_id INTEGER,
                p_days INTEGER DEFAULT 60
            )
            RETURNS DECIMAL(5,4) AS $$
            DECLARE
                correlation DECIMAL(5,4);
            BEGIN
                WITH stock1_returns AS (
                    SELECT 
                        DATE(timestamp) as trade_date,
                        (close_price - LAG(close_price) OVER (ORDER BY timestamp)) / 
                        LAG(close_price) OVER (ORDER BY timestamp) as return1
                    FROM market_data.stock_prices
                    WHERE stock_id = p_stock1_id
                    AND timestamp > NOW() - INTERVAL '%s days'
                ),
                stock2_returns AS (
                    SELECT 
                        DATE(timestamp) as trade_date,
                        (close_price - LAG(close_price) OVER (ORDER BY timestamp)) / 
                        LAG(close_price) OVER (ORDER BY timestamp) as return2
                    FROM market_data.stock_prices
                    WHERE stock_id = p_stock2_id
                    AND timestamp > NOW() - INTERVAL '%s days'
                ),
                combined_returns AS (
                    SELECT s1.return1, s2.return2
                    FROM stock1_returns s1
                    JOIN stock2_returns s2 ON s1.trade_date = s2.trade_date
                    WHERE s1.return1 IS NOT NULL AND s2.return2 IS NOT NULL
                )
                SELECT CORR(return1, return2) INTO correlation
                FROM combined_returns;
                
                RETURN COALESCE(correlation, 0);
            END;
            $$ LANGUAGE plpgsql;
            """
        ]
        
        for function_sql in functions:
            try:
                await self.db_manager.execute_query(function_sql)
                logger.debug("Created function successfully")
            except Exception as e:
                logger.warning("Function creation failed", error=str(e))
                
        logger.info("Database functions created")
        
    async def _insert_initial_data(self):
        """Insert initial reference data."""
        logger.info("Inserting initial data")
        
        try:
            # Insert sample stocks for major exchanges
            sample_stocks = [
                # US Stocks
                ('AAPL', 1, 'Apple Inc.', 'Technology', 'Consumer Electronics'),
                ('MSFT', 1, 'Microsoft Corporation', 'Technology', 'Software'),
                ('GOOGL', 2, 'Alphabet Inc.', 'Technology', 'Internet Services'),
                ('AMZN', 2, 'Amazon.com Inc.', 'Consumer Discretionary', 'E-commerce'),
                ('TSLA', 2, 'Tesla Inc.', 'Consumer Discretionary', 'Electric Vehicles'),
                ('META', 2, 'Meta Platforms Inc.', 'Technology', 'Social Media'),
                ('NVDA', 2, 'NVIDIA Corporation', 'Technology', 'Semiconductors'),
                ('JPM', 1, 'JPMorgan Chase & Co.', 'Financial Services', 'Banking'),
                ('JNJ', 1, 'Johnson & Johnson', 'Healthcare', 'Pharmaceuticals'),
                ('V', 1, 'Visa Inc.', 'Financial Services', 'Payment Processing'),
                
                # Add some ETFs
                ('SPY', 1, 'SPDR S&P 500 ETF', 'ETF', 'Broad Market'),
                ('QQQ', 2, 'Invesco QQQ Trust', 'ETF', 'Technology'),
                ('GLD', 1, 'SPDR Gold Shares', 'ETF', 'Commodities'),
                ('VTI', 1, 'Vanguard Total Stock Market ETF', 'ETF', 'Broad Market'),
            ]
            
            for symbol, exchange_id, name, sector, industry in sample_stocks:
                insert_sql = """
                INSERT INTO market_data.stocks (symbol, exchange_id, company_name, sector, industry)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (symbol, exchange_id) DO NOTHING
                """
                await self.db_manager.execute_query(
                    insert_sql, 
                    (symbol, exchange_id, name, sector, industry)
                )
                
            logger.info("Sample stocks inserted")
            
            # Insert sample alert rules
            sample_alert_rules = [
                {
                    'name': 'Large Price Drop',
                    'alert_type': 'price_change',
                    'conditions': {'field': 'price_change_percent', 'operator': 'less_than', 'value': -5.0},
                    'thresholds': {'value': -5.0, 'timeframe': '5m'},
                    'notification_channels': ['dashboard', 'email']
                },
                {
                    'name': 'High Volume Spike',
                    'alert_type': 'volume_spike',
                    'conditions': {'field': 'volume_spike_percent', 'operator': 'greater_than', 'value': 200.0},
                    'thresholds': {'value': 200.0, 'timeframe': '15m'},
                    'notification_channels': ['dashboard']
                },
                {
                    'name': 'RSI Overbought',
                    'alert_type': 'technical_indicator',
                    'conditions': {'field': 'rsi', 'operator': 'greater_than', 'value': 80.0},
                    'thresholds': {'value': 80.0},
                    'notification_channels': ['dashboard']
                }
            ]
            
            for rule in sample_alert_rules:
                insert_sql = """
                INSERT INTO alerts.alert_rules (name, alert_type, conditions, thresholds, notification_channels)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING
                """
                await self.db_manager.execute_query(
                    insert_sql,
                    (rule['name'], rule['alert_type'], 
                     json.dumps(rule['conditions']), 
                     json.dumps(rule['thresholds']),
                     json.dumps(rule['notification_channels']))
                )
                
            logger.info("Sample alert rules inserted")
            
        except Exception as e:
            logger.error("Initial data insertion failed", error=str(e))
            raise
            
    async def _create_views(self):
        """Create database views for common queries."""
        logger.info("Creating database views")
        
        views = [
            # Latest stock prices with change calculations
            """
            CREATE OR REPLACE VIEW market_data.latest_stock_prices AS
            SELECT DISTINCT ON (s.id)
                s.id as stock_id,
                s.symbol,
                e.code as exchange,
                sp.close_price as current_price,
                sp.volume,
                sp.timestamp,
                LAG(sp.close_price) OVER (PARTITION BY s.id ORDER BY sp.timestamp) as previous_price,
                CASE 
                    WHEN LAG(sp.close_price) OVER (PARTITION BY s.id ORDER BY sp.timestamp) IS NOT NULL THEN
                        ((sp.close_price - LAG(sp.close_price) OVER (PARTITION BY s.id ORDER BY sp.timestamp)) / 
                         LAG(sp.close_price) OVER (PARTITION BY s.id ORDER BY sp.timestamp)) * 100
                    ELSE 0
                END as change_percent
            FROM market_data.stocks s
            JOIN market_data.exchanges e ON s.exchange_id = e.id
            LEFT JOIN market_data.stock_prices sp ON s.id = sp.stock_id
            WHERE s.is_active = true
            ORDER BY s.id, sp.timestamp DESC
            """,
            
            # Portfolio summary with current values
            """
            CREATE OR REPLACE VIEW portfolio.portfolio_summary_detailed AS
            SELECT 
                p.id,
                p.name,
                p.currency,
                p.initial_value,
                COALESCE(SUM(pos.market_value), 0) as current_value,
                COALESCE(SUM(pos.unrealized_pnl), 0) as unrealized_pnl,
                COALESCE(SUM(pos.realized_pnl), 0) as realized_pnl,
                CASE 
                    WHEN p.initial_value > 0 THEN
                        ((COALESCE(SUM(pos.market_value), 0) - p.initial_value) / p.initial_value) * 100
                    ELSE 0
                END as total_return_percent,
                COUNT(pos.id) as position_count,
                p.created_at,
                p.updated_at
            FROM portfolio.portfolios p
            LEFT JOIN portfolio.positions pos ON p.id = pos.portfolio_id AND pos.quantity > 0
            WHERE p.is_active = true
            GROUP BY p.id, p.name, p.currency, p.initial_value, p.created_at, p.updated_at
            """,
            
            # Active alerts summary
            """
            CREATE OR REPLACE VIEW alerts.active_alerts_summary AS
            SELECT 
                ai.id,
                ai.rule_id,
                ar.name as rule_name,
                ai.stock_id,
                s.symbol,
                ai.severity,
                ai.title,
                ai.message,
                ai.status,
                ai.triggered_at,
                EXTRACT(EPOCH FROM (NOW() - ai.triggered_at))/3600 as hours_since_triggered
            FROM alerts.alert_instances ai
            JOIN alerts.alert_rules ar ON ai.rule_id = ar.id
            LEFT JOIN market_data.stocks s ON ai.stock_id = s.id
            WHERE ai.status = 'ACTIVE'
            ORDER BY ai.triggered_at DESC
            """
        ]
        
        for view_sql in views:
            try:
                await self.db_manager.execute_query(view_sql)
                logger.debug("Created view successfully")
            except Exception as e:
                logger.warning("View creation failed", error=str(e))
                
        logger.info("Database views created")
        
    async def _grant_permissions(self):
        """Grant appropriate permissions to database users."""
        logger.info("Granting database permissions")
        
        permissions = [
            # Grant permissions to application user
            "GRANT USAGE ON ALL SEQUENCES IN SCHEMA market_data TO stock_user",
            "GRANT USAGE ON ALL SEQUENCES IN SCHEMA portfolio TO stock_user", 
            "GRANT USAGE ON ALL SEQUENCES IN SCHEMA alerts TO stock_user",
            "GRANT USAGE ON ALL SEQUENCES IN SCHEMA analytics TO stock_user",
            "GRANT USAGE ON ALL SEQUENCES IN SCHEMA monitoring TO stock_user",
            
            # Grant execute permissions on functions
            "GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO stock_user",
            
            # Grant select on views
            "GRANT SELECT ON ALL TABLES IN SCHEMA information_schema TO stock_user"
        ]
        
        for permission_sql in permissions:
            try:
                await self.db_manager.execute_query(permission_sql)
                logger.debug("Granted permission successfully")
            except Exception as e:
                logger.warning("Permission grant failed", error=str(e))
                
        logger.info("Database permissions granted")


async def main():
    """Main initialization function."""
    print("Stock Market Monitor - Database Initialization")
    print("=" * 50)
    
    try:
        initializer = DatabaseInitializer()
        await initializer.initialize()
        
        print("\n✓ Database initialization completed successfully!")
        print("\nNext steps:")
        print("1. Edit config/config.yaml with your API keys")
        print("2. Start the system: python scripts/start_system.py")
        print("3. Access dashboard: http://localhost:8080")
        
    except Exception as e:
        print(f"\n✗ Database initialization failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())