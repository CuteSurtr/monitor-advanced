"""
Real-Time Data Populator for PostgreSQL Dashboards
Generates realistic market data to populate all dashboard panels
"""

import asyncio
import random
import logging
from datetime import datetime, timedelta
from typing import Dict, List
import numpy as np
import pandas as pd

from src.utils.config import get_config
from src.utils.logger import get_logger
from src.utils.database import DatabaseManager


class MarketDataPopulator:
    """Populates database with realistic market data for dashboard testing."""

    def __init__(self):
        self.config = get_config()
        self.logger = get_logger(__name__)
        self.db_manager = None
        self.running = False

        # Market hours simulation
        self.market_sessions = {
            "US": {"open": 9.5, "close": 16.0},  # 9:30 AM - 4:00 PM ET
            "EU": {"open": 8.0, "close": 16.5},  # 8:00 AM - 4:30 PM GMT
            "ASIA": {"open": 9.0, "close": 15.0},  # 9:00 AM - 3:00 PM JST
        }

        # Base prices for realistic movement
        self.base_prices = {
            "AAPL": 175.0,
            "MSFT": 335.0,
            "GOOGL": 2850.0,
            "AMZN": 3250.0,
            "TSLA": 240.0,
            "META": 485.0,
            "NVDA": 875.0,
            "JPM": 148.0,
            "JNJ": 162.0,
            "SPY": 445.0,
            "BTC": 67000.0,
            "ETH": 3800.0,
            "USDT": 1.0,
            "BNB": 610.0,
            "USDC": 1.0,
            "EUR/USD": 1.0850,
            "GBP/USD": 1.2750,
            "USD/JPY": 150.25,
            "USD/CHF": 0.9180,
            "XAU/USD": 2650.0,
            "XAG/USD": 31.50,
            "WTI": 82.50,
            "BRENT": 85.75,
        }

        # Current prices (will evolve)
        self.current_prices = self.base_prices.copy()

    async def initialize(self):
        """Initialize database connection."""
        try:
            self.db_manager = DatabaseManager(self.config)
            await self.db_manager.initialize()
            self.logger.info("Market Data Populator initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize: {e}")
            raise

    async def populate_stock_prices(self):
        """Generate realistic stock price data."""
        try:
            # Get all stocks from database
            query = "SELECT id, symbol FROM market_data.stocks"

            if hasattr(self.db_manager, "session"):
                # Use sync connection for this example
                import psycopg2

                conn = psycopg2.connect(
                    host=self.config.database.host,
                    port=self.config.database.port,
                    database=self.config.database.name,
                    user=self.config.database.user,
                    password=self.config.database.password,
                )

                with conn.cursor() as cursor:
                    cursor.execute(query)
                    stocks = cursor.fetchall()

                    for stock_id, symbol in stocks:
                        if symbol in self.current_prices:
                            # Generate realistic price movement
                            current_price = self.current_prices[symbol]
                            price_change = random.gauss(
                                0, current_price * 0.01
                            )  # 1% volatility
                            new_price = max(
                                current_price + price_change, current_price * 0.95
                            )  # Don't drop below 95%
                            self.current_prices[symbol] = new_price

                            # Generate OHLC data
                            high_price = new_price * (1 + random.uniform(0, 0.005))
                            low_price = new_price * (1 - random.uniform(0, 0.005))
                            open_price = current_price
                            volume = random.randint(1000000, 50000000)

                            # Insert price data
                            insert_query = """
                            INSERT INTO market_data.stock_prices 
                            (stock_id, timestamp, open_price, high_price, low_price, close_price, volume)
                            VALUES (%s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT (stock_id, timestamp) DO UPDATE SET
                            close_price = EXCLUDED.close_price,
                            high_price = EXCLUDED.high_price,
                            low_price = EXCLUDED.low_price,
                            volume = EXCLUDED.volume
                            """

                            cursor.execute(
                                insert_query,
                                (
                                    stock_id,
                                    datetime.now().replace(microsecond=0),
                                    open_price,
                                    high_price,
                                    low_price,
                                    new_price,
                                    volume,
                                ),
                            )

                    conn.commit()

                conn.close()

        except Exception as e:
            self.logger.error(f"Failed to populate stock prices: {e}")

    async def populate_hft_data(self):
        """Generate high-frequency trading data."""
        try:
            import psycopg2

            conn = psycopg2.connect(
                host=self.config.database.host,
                port=self.config.database.port,
                database=self.config.database.name,
                user=self.config.database.user,
                password=self.config.database.password,
            )

            with conn.cursor() as cursor:
                # Get stock IDs
                cursor.execute("SELECT id, symbol FROM market_data.stocks LIMIT 5")
                stocks = cursor.fetchall()

                for stock_id, symbol in stocks:
                    if symbol in self.current_prices:
                        base_price = self.current_prices[symbol]

                        # Generate tick data (trades)
                        for _ in range(random.randint(5, 20)):  # 5-20 trades per cycle
                            price = base_price * (
                                1 + random.gauss(0, 0.001)
                            )  # Small price variation
                            volume = random.uniform(100, 10000)
                            aggressor_side = random.choice(["BUY", "SELL"])

                            tick_query = """
                            INSERT INTO market_data.tick_data 
                            (asset_id, asset_type, timestamp, price, volume, aggressor_side)
                            VALUES (%s, %s, %s, %s, %s, %s)
                            """

                            cursor.execute(
                                tick_query,
                                (
                                    stock_id,
                                    "stock",
                                    datetime.now(),
                                    price,
                                    volume,
                                    aggressor_side,
                                ),
                            )

                        # Generate order book data
                        for side in ["BID", "ASK"]:
                            for level in range(1, 6):  # 5 levels deep
                                if side == "BID":
                                    price_level = base_price * (
                                        1 - level * 0.0001
                                    )  # Slightly below
                                else:
                                    price_level = base_price * (
                                        1 + level * 0.0001
                                    )  # Slightly above

                                size = random.uniform(1000, 50000)

                                ob_query = """
                                INSERT INTO market_data.order_book_level2 
                                (asset_id, asset_type, timestamp, side, price_level, size)
                                VALUES (%s, %s, %s, %s, %s, %s)
                                ON CONFLICT (asset_id, asset_type, timestamp, side, price_level) 
                                DO UPDATE SET size = EXCLUDED.size
                                """

                                cursor.execute(
                                    ob_query,
                                    (
                                        stock_id,
                                        "stock",
                                        datetime.now(),
                                        side,
                                        price_level,
                                        size,
                                    ),
                                )

                        # Generate microstructure features
                        bid_ask_spread = base_price * random.uniform(
                            0.0001, 0.001
                        )  # 1-10 bps
                        order_flow_imbalance = random.gauss(0, 0.1)  # Balanced around 0
                        trade_intensity = random.uniform(10, 100)  # Trades per minute

                        micro_query = """
                        INSERT INTO analytics.microstructure_features 
                        (asset_id, asset_type, timestamp, bid_ask_spread, order_flow_imbalance, trade_intensity)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        ON CONFLICT (asset_id, asset_type, timestamp) 
                        DO UPDATE SET 
                        bid_ask_spread = EXCLUDED.bid_ask_spread,
                        order_flow_imbalance = EXCLUDED.order_flow_imbalance,
                        trade_intensity = EXCLUDED.trade_intensity
                        """

                        cursor.execute(
                            micro_query,
                            (
                                stock_id,
                                "stock",
                                datetime.now(),
                                bid_ask_spread,
                                order_flow_imbalance,
                                trade_intensity,
                            ),
                        )

                conn.commit()

            conn.close()

        except Exception as e:
            self.logger.error(f"Failed to populate HFT data: {e}")

    async def populate_portfolio_activity(self):
        """Generate trading activity and update portfolio metrics."""
        try:
            import psycopg2

            conn = psycopg2.connect(
                host=self.config.database.host,
                port=self.config.database.port,
                database=self.config.database.name,
                user=self.config.database.user,
                password=self.config.database.password,
            )

            with conn.cursor() as cursor:
                # Simulate some trading activity
                if random.random() < 0.3:  # 30% chance of trade
                    stock_id = random.choice([87, 88, 89, 90, 91])  # Our sample stocks
                    transaction_type = random.choice(["BUY", "SELL"])
                    quantity = random.randint(10, 100)

                    # Get current price
                    cursor.execute(
                        "SELECT symbol FROM market_data.stocks WHERE id = %s",
                        (stock_id,),
                    )
                    symbol = cursor.fetchone()[0]
                    price = self.current_prices.get(symbol, 100.0)

                    # Insert transaction
                    trans_query = """
                    INSERT INTO portfolio.transactions 
                    (portfolio_id, stock_id, transaction_type, quantity, price, total_amount, transaction_date)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """

                    cursor.execute(
                        trans_query,
                        (
                            "00000000-0000-0000-0000-000000000001",
                            stock_id,
                            transaction_type,
                            quantity,
                            price,
                            quantity * price,
                            datetime.now(),
                        ),
                    )

                    # Update position (simplified)
                    cursor.execute(
                        """
                        UPDATE portfolio.positions 
                        SET market_value = quantity * %s,
                            unrealized_pnl = (quantity * %s) - (quantity * average_cost)
                        WHERE portfolio_id = %s AND stock_id = %s
                    """,
                        (
                            price,
                            price,
                            "00000000-0000-0000-0000-000000000001",
                            stock_id,
                        ),
                    )

                conn.commit()

            conn.close()

        except Exception as e:
            self.logger.error(f"Failed to populate portfolio activity: {e}")

    async def generate_risk_alerts(self):
        """Generate sample risk alerts."""
        try:
            import psycopg2

            conn = psycopg2.connect(
                host=self.config.database.host,
                port=self.config.database.port,
                database=self.config.database.name,
                user=self.config.database.user,
                password=self.config.database.password,
            )

            with conn.cursor() as cursor:
                # Check if we should generate an alert
                if random.random() < 0.1:  # 10% chance
                    alert_types = [
                        (
                            "Portfolio Loss Alert",
                            "HIGH",
                            "Daily P&L exceeded -5% threshold",
                        ),
                        (
                            "Volatility Spike",
                            "MEDIUM",
                            "Market volatility increased significantly",
                        ),
                        (
                            "Position Concentration",
                            "LOW",
                            "Single position exceeds 30% of portfolio",
                        ),
                        ("Volume Anomaly", "MEDIUM", "Unusual trading volume detected"),
                    ]

                    title, severity, message = random.choice(alert_types)

                    alert_query = """
                    INSERT INTO alerts.alert_instances 
                    (title, severity, message, status, triggered_at)
                    VALUES (%s, %s, %s, 'ACTIVE', %s)
                    """

                    cursor.execute(
                        alert_query, (title, severity, message, datetime.now())
                    )

                conn.commit()

            conn.close()

        except Exception as e:
            self.logger.error(f"Failed to generate risk alerts: {e}")

    async def populate_technical_indicators(self):
        """Generate technical indicators."""
        try:
            import psycopg2

            conn = psycopg2.connect(
                host=self.config.database.host,
                port=self.config.database.port,
                database=self.config.database.name,
                user=self.config.database.user,
                password=self.config.database.password,
            )

            with conn.cursor() as cursor:
                cursor.execute("SELECT id, symbol FROM market_data.stocks")
                stocks = cursor.fetchall()

                for stock_id, symbol in stocks:
                    if symbol in self.current_prices:
                        price = self.current_prices[symbol]

                        # Generate realistic technical indicators
                        indicators = {
                            "SMA_20": price * random.uniform(0.98, 1.02),
                            "SMA_50": price * random.uniform(0.95, 1.05),
                            "RSI": random.uniform(20, 80),
                            "MACD": random.gauss(0, 2),
                            "BB_UPPER": price * 1.02,
                            "BB_LOWER": price * 0.98,
                        }

                        for indicator_name, value in indicators.items():
                            cursor.execute(
                                """
                                INSERT INTO market_data.technical_indicators 
                                (stock_id, indicator_name, value, timestamp)
                                VALUES (%s, %s, %s, %s)
                                ON CONFLICT (stock_id, indicator_name, timestamp)
                                DO UPDATE SET value = EXCLUDED.value
                            """,
                                (
                                    stock_id,
                                    indicator_name,
                                    value,
                                    datetime.now().replace(microsecond=0),
                                ),
                            )

                conn.commit()

            conn.close()

        except Exception as e:
            self.logger.error(f"Failed to populate technical indicators: {e}")

    async def run_data_population_cycle(self):
        """Run one complete data population cycle."""
        self.logger.info("Starting data population cycle...")

        tasks = [
            self.populate_stock_prices(),
            self.populate_hft_data(),
            self.populate_portfolio_activity(),
            self.generate_risk_alerts(),
            self.populate_technical_indicators(),
        ]

        try:
            await asyncio.gather(*tasks)
            self.logger.info("Data population cycle completed successfully")
        except Exception as e:
            self.logger.error(f"Error in data population cycle: {e}")

    async def start_continuous_population(self):
        """Start continuous data population."""
        self.running = True
        self.logger.info(" Starting continuous market data population...")

        cycle_count = 0
        while self.running:
            try:
                cycle_count += 1
                self.logger.info(f" Running data cycle #{cycle_count}")

                await self.run_data_population_cycle()

                # Wait before next cycle (every 30 seconds)
                await asyncio.sleep(30)

            except Exception as e:
                self.logger.error(f"Error in continuous population: {e}")
                await asyncio.sleep(60)  # Wait longer on error

    async def stop(self):
        """Stop data population."""
        self.running = False
        if self.db_manager:
            await self.db_manager.close()
        self.logger.info("Market Data Populator stopped")


async def main():
    """Main function to run the data populator."""
    populator = MarketDataPopulator()

    try:
        await populator.initialize()

        # Run a few initial cycles to populate data immediately
        populator.logger.info("Running initial data population...")
        for i in range(3):
            await populator.run_data_population_cycle()
            await asyncio.sleep(5)

        # Start continuous population
        await populator.start_continuous_population()

    except KeyboardInterrupt:
        populator.logger.info("Data population stopped by user")
    except Exception as e:
        populator.logger.error(f"Critical error: {e}")
    finally:
        await populator.stop()


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    print(" Starting PostgreSQL Dashboard Data Populator")
    print("Generating real-time market data for Grafana dashboards")

    asyncio.run(main())
