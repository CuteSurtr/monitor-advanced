"""
Database management for the stock monitoring system.
Supports both PostgreSQL and InfluxDB.
"""

import asyncio
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
import json

from sqlalchemy import (
    create_engine,
    text,
    MetaData,
    Table,
    Column,
    Integer,
    String,
    Float,
    DateTime,
    Boolean,
    JSON,
)
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import QueuePool
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

from src.utils.logger import get_logger

Base = declarative_base()


class StockData(Base):
    """SQLAlchemy model for stock data."""

    __tablename__ = "stock_data"

    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    open_price = Column(Float)
    high_price = Column(Float)
    low_price = Column(Float)
    close_price = Column(Float)
    volume = Column(Integer)
    exchange = Column(String(10))
    currency = Column(String(3), default="USD")
    created_at = Column(DateTime, default=datetime.utcnow)


class CommodityData(Base):
    """SQLAlchemy model for commodity data."""

    __tablename__ = "commodity_data"

    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    price = Column(Float)
    volume = Column(Integer)
    commodity_type = Column(String(20))  # metals, energy, agriculture
    created_at = Column(DateTime, default=datetime.utcnow)


class ForexData(Base):
    """SQLAlchemy model for forex data."""

    __tablename__ = "forex_data"

    id = Column(Integer, primary_key=True)
    pair = Column(String(10), nullable=False, index=True)
    symbol = Column(String(15), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    rate = Column(Float)
    bid = Column(Float)
    ask = Column(Float)
    open_rate = Column(Float)
    high_rate = Column(Float)
    low_rate = Column(Float)
    volume = Column(Integer, default=0)
    change_24h = Column(Float, default=0)
    change_24h_percent = Column(Float, default=0)
    source = Column(String(20))
    created_at = Column(DateTime, default=datetime.utcnow)


class CryptoData(Base):
    """SQLAlchemy model for cryptocurrency data."""

    __tablename__ = "crypto_data"

    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), nullable=False, index=True)
    crypto = Column(String(10), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    price = Column(Float)
    open_price = Column(Float)
    high_price = Column(Float)
    low_price = Column(Float)
    volume = Column(Integer, default=0)
    market_cap = Column(Integer, default=0)
    currency = Column(String(3), default="USD")
    change_24h = Column(Float, default=0)
    change_24h_percent = Column(Float, default=0)
    volume_24h = Column(Integer, default=0)
    source = Column(String(20))
    created_at = Column(DateTime, default=datetime.utcnow)


class NewsData(Base):
    """SQLAlchemy model for news data."""

    __tablename__ = "news_data"

    id = Column(Integer, primary_key=True)
    title = Column(String(500))
    content = Column(String(5000))
    source = Column(String(100))
    url = Column(String(500))
    published_at = Column(DateTime)
    sentiment_score = Column(Float)
    sentiment_label = Column(String(20))
    related_symbols = Column(JSON)  # List of related stock symbols
    created_at = Column(DateTime, default=datetime.utcnow)


class Portfolio(Base):
    """SQLAlchemy model for portfolio data."""

    __tablename__ = "portfolios"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    user_id = Column(String(50), nullable=False)
    total_value = Column(Float, default=0.0)
    currency = Column(String(3), default="USD")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PortfolioPosition(Base):
    """SQLAlchemy model for portfolio positions."""

    __tablename__ = "portfolio_positions"

    id = Column(Integer, primary_key=True)
    portfolio_id = Column(Integer, nullable=False, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    quantity = Column(Float, nullable=False)
    average_price = Column(Float, nullable=False)
    current_price = Column(Float)
    market_value = Column(Float)
    unrealized_pnl = Column(Float)
    realized_pnl = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Alert(Base):
    """SQLAlchemy model for alerts."""

    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), nullable=False, index=True)
    alert_type = Column(String(50), nullable=False)  # price_change, volume_spike, etc.
    threshold = Column(Float)
    current_value = Column(Float)
    triggered_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    user_id = Column(String(50))
    notification_sent = Column(Boolean, default=False)


class DatabaseManager:
    """Database manager for handling both PostgreSQL and InfluxDB."""

    def __init__(self, config):
        self.config = config
        self.logger = get_logger(__name__)
        self.engine = None
        self.session_factory = None
        self.influx_client = None
        self.write_api = None
        self.query_api = None
        self.health_status = False

    async def initialize(self):
        """Initialize database connections."""
        try:
            if self.config.database.type == "postgresql":
                await self._init_postgresql()
            elif self.config.database.type == "influxdb":
                await self._init_influxdb()
            elif self.config.database.type == "dual":
                # Initialize both databases
                await self._init_postgresql()
                await self._init_influxdb()
            else:
                raise ValueError(
                    f"Unsupported database type: {self.config.database.type}"
                )

            self.health_status = True
            self.logger.info(
                f"Database initialized successfully: {self.config.database.type}"
            )

        except Exception as e:
            self.logger.error(f"Failed to initialize database: {e}")
            raise

    async def _init_postgresql(self):
        """Initialize PostgreSQL connection."""
        # Create async engine
        database_url = self.config.get_database_url()
        self.engine = create_async_engine(
            database_url,
            poolclass=QueuePool,
            pool_size=getattr(self.config.performance, "connection_pool_size", 10),
            max_overflow=20,
            pool_pre_ping=True,
            echo=False,
        )

        # Create session factory
        self.session_factory = async_sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )

        # Create tables
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        self.logger.info("PostgreSQL connection established")

    async def _init_influxdb(self):
        """Initialize InfluxDB connection."""
        self.influx_client = InfluxDBClient(
            url=self.config.database.influxdb.url,
            token=self.config.database.influxdb.token,
            org=self.config.database.influxdb.org,
        )

        self.write_api = self.influx_client.write_api(write_options=SYNCHRONOUS)
        self.query_api = self.influx_client.query_api()

        # Test connection
        health = self.influx_client.health()
        if health.status != "pass":
            raise Exception(f"InfluxDB health check failed: {health.message}")

        self.logger.info("InfluxDB connection established")

    async def close(self):
        """Close database connections."""
        try:
            if self.engine:
                await self.engine.dispose()

            if self.influx_client:
                self.influx_client.close()

            self.health_status = False
            self.logger.info("Database connections closed")

        except Exception as e:
            self.logger.error(f"Error closing database connections: {e}")

    async def is_healthy(self) -> bool:
        """Check database health."""
        try:
            if self.config.database.type == "postgresql":
                async with self.session_factory() as session:
                    await session.execute(text("SELECT 1"))
            else:
                health = self.influx_client.health()
                return health.status == "pass"

            return True
        except Exception as e:
            self.logger.error(f"Database health check failed: {e}")
            return False

    # Stock data methods
    async def save_stock_data(self, data: Dict[str, Any]):
        """Save stock data to database."""
        try:
            if self.config.database.type == "postgresql":
                await self._save_stock_data_postgresql(data)
            elif self.config.database.type == "influxdb":
                await self._save_stock_data_influxdb(data)
            elif self.config.database.type == "dual":
                # Save to both databases
                await self._save_stock_data_postgresql(data)
                await self._save_stock_data_influxdb(data)
        except Exception as e:
            self.logger.error(f"Failed to save stock data: {e}")
            raise

    async def _save_stock_data_postgresql(self, data: Dict[str, Any]):
        """Save stock data to PostgreSQL."""
        async with self.session_factory() as session:
            stock_data = StockData(
                symbol=data["symbol"],
                timestamp=data["timestamp"],
                open_price=data.get("open"),
                high_price=data.get("high"),
                low_price=data.get("low"),
                close_price=data.get("close"),
                volume=data.get("volume"),
                exchange=data.get("exchange"),
                currency=data.get("currency", "USD"),
            )
            session.add(stock_data)
            await session.commit()

    async def _save_stock_data_influxdb(self, data: Dict[str, Any]):
        """Save stock data to InfluxDB."""
        point = (
            Point("stock_data")
            .tag("symbol", data["symbol"])
            .tag("exchange", data.get("exchange", "unknown"))
            .field("open", data.get("open", 0))
            .field("high", data.get("high", 0))
            .field("low", data.get("low", 0))
            .field("close", data.get("close", 0))
            .field("volume", data.get("volume", 0))
            .time(data["timestamp"], WritePrecision.NS)
        )

        self.write_api.write(bucket=self.config.database.influxdb.bucket, record=point)

    async def get_stock_data(
        self, symbol: str, start_time: datetime, end_time: datetime
    ) -> List[Dict[str, Any]]:
        """Get stock data for a symbol within a time range."""
        try:
            if self.config.database.type == "postgresql":
                return await self._get_stock_data_postgresql(
                    symbol, start_time, end_time
                )
            else:
                return await self._get_stock_data_influxdb(symbol, start_time, end_time)
        except Exception as e:
            self.logger.error(f"Failed to get stock data: {e}")
            raise

    async def _get_stock_data_postgresql(
        self, symbol: str, start_time: datetime, end_time: datetime
    ) -> List[Dict[str, Any]]:
        """Get stock data from PostgreSQL."""
        async with self.session_factory() as session:
            result = await session.execute(
                text(
                    """
                    SELECT symbol, timestamp, open_price, high_price, low_price, close_price, volume, exchange
                    FROM stock_data
                    WHERE symbol = :symbol AND timestamp BETWEEN :start_time AND :end_time
                    ORDER BY timestamp
                """
                ),
                {"symbol": symbol, "start_time": start_time, "end_time": end_time},
            )

            return [dict(row._mapping) for row in result.fetchall()]

    async def _get_stock_data_influxdb(
        self, symbol: str, start_time: datetime, end_time: datetime
    ) -> List[Dict[str, Any]]:
        """Get stock data from InfluxDB."""
        query = f"""
            from(bucket: "{self.config.database.influxdb.bucket}")
            |> range(start: {start_time.isoformat()}, stop: {end_time.isoformat()})
            |> filter(fn: (r) => r["_measurement"] == "stock_data" and r["symbol"] == "{symbol}")
            |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
        """

        result = self.query_api.query(query)

        data = []
        for table in result:
            for record in table.records:
                data.append(
                    {
                        "symbol": record.values.get("symbol"),
                        "timestamp": record.get_time(),
                        "open": record.values.get("open"),
                        "high": record.values.get("high"),
                        "low": record.values.get("low"),
                        "close": record.values.get("close"),
                        "volume": record.values.get("volume"),
                        "exchange": record.values.get("exchange"),
                    }
                )

        return data

    # Commodity data methods
    async def save_commodity_data(self, data: Dict[str, Any]):
        """Save commodity data to database."""
        try:
            if self.config.database.type == "postgresql":
                await self._save_commodity_data_postgresql(data)
            elif self.config.database.type == "influxdb":
                await self._save_commodity_data_influxdb(data)
            elif self.config.database.type == "dual":
                # Save to both databases
                await self._save_commodity_data_postgresql(data)
                await self._save_commodity_data_influxdb(data)
        except Exception as e:
            self.logger.error(f"Failed to save commodity data: {e}")
            raise

    async def _save_commodity_data_postgresql(self, data: Dict[str, Any]):
        """Save commodity data to PostgreSQL."""
        async with self.session_factory() as session:
            commodity_data = CommodityData(
                symbol=data["symbol"],
                timestamp=data["timestamp"],
                price=data.get("price"),
                volume=data.get("volume"),
                commodity_type=data.get("commodity_type"),
            )
            session.add(commodity_data)
            await session.commit()

    async def _save_commodity_data_influxdb(self, data: Dict[str, Any]):
        """Save commodity data to InfluxDB."""
        point = (
            Point("commodity_data")
            .tag("symbol", data["symbol"])
            .tag("commodity_type", data.get("commodity_type", "unknown"))
            .field("price", data.get("price", 0))
            .field("volume", data.get("volume", 0))
            .time(data["timestamp"], WritePrecision.NS)
        )

        self.write_api.write(bucket=self.config.database.influxdb.bucket, record=point)

    # Forex data methods
    async def save_forex_data(self, data: Dict[str, Any]):
        """Save forex data to database."""
        try:
            if self.config.database.type == "postgresql":
                await self._save_forex_data_postgresql(data)
            elif self.config.database.type == "influxdb":
                await self._save_forex_data_influxdb(data)
            elif self.config.database.type == "dual":
                # Save to both databases
                await self._save_forex_data_postgresql(data)
                await self._save_forex_data_influxdb(data)
        except Exception as e:
            self.logger.error(f"Failed to save forex data: {e}")
            raise

    async def _save_forex_data_postgresql(self, data: Dict[str, Any]):
        """Save forex data to PostgreSQL."""
        async with self.session_factory() as session:
            forex_data = ForexData(
                pair=data["pair"],
                symbol=data["symbol"],
                timestamp=data["timestamp"],
                rate=data.get("rate"),
                bid=data.get("bid"),
                ask=data.get("ask"),
                open_rate=data.get("open"),
                high_rate=data.get("high"),
                low_rate=data.get("low"),
                volume=data.get("volume", 0),
                change_24h=data.get("change", 0),
                change_24h_percent=data.get("change_percent", 0),
                source=data.get("source"),
            )
            session.add(forex_data)
            await session.commit()

    async def _save_forex_data_influxdb(self, data: Dict[str, Any]):
        """Save forex data to InfluxDB."""
        point = (
            Point("forex_data")
            .tag("pair", data["pair"])
            .tag("symbol", data["symbol"])
            .tag("source", data.get("source", "unknown"))
            .field("rate", data.get("rate", 0))
            .field("bid", data.get("bid", 0))
            .field("ask", data.get("ask", 0))
            .field("open", data.get("open", 0))
            .field("high", data.get("high", 0))
            .field("low", data.get("low", 0))
            .field("volume", data.get("volume", 0))
            .field("change_24h", data.get("change", 0))
            .field("change_24h_percent", data.get("change_percent", 0))
            .time(data["timestamp"], WritePrecision.NS)
        )

        self.write_api.write(bucket=self.config.database.influxdb.bucket, record=point)

    # Crypto data methods
    async def save_crypto_data(self, data: Dict[str, Any]):
        """Save cryptocurrency data to database."""
        try:
            if self.config.database.type == "postgresql":
                await self._save_crypto_data_postgresql(data)
            elif self.config.database.type == "influxdb":
                await self._save_crypto_data_influxdb(data)
            elif self.config.database.type == "dual":
                # Save to both databases
                await self._save_crypto_data_postgresql(data)
                await self._save_crypto_data_influxdb(data)
        except Exception as e:
            self.logger.error(f"Failed to save crypto data: {e}")
            raise

    async def _save_crypto_data_postgresql(self, data: Dict[str, Any]):
        """Save crypto data to PostgreSQL."""
        async with self.session_factory() as session:
            crypto_data = CryptoData(
                symbol=data["symbol"],
                crypto=data["crypto"],
                timestamp=data["timestamp"],
                price=data.get("price"),
                open_price=data.get("open"),
                high_price=data.get("high"),
                low_price=data.get("low"),
                volume=data.get("volume", 0),
                market_cap=data.get("market_cap", 0),
                currency=data.get("currency", "USD"),
                change_24h=data.get("change_24h", 0),
                change_24h_percent=data.get("change_24h_percent", 0),
                volume_24h=data.get("volume_24h", 0),
                source=data.get("source"),
            )
            session.add(crypto_data)
            await session.commit()

    async def _save_crypto_data_influxdb(self, data: Dict[str, Any]):
        """Save crypto data to InfluxDB."""
        point = (
            Point("crypto_data")
            .tag("symbol", data["symbol"])
            .tag("crypto", data["crypto"])
            .tag("currency", data.get("currency", "USD"))
            .tag("source", data.get("source", "unknown"))
            .field("price", data.get("price", 0))
            .field("open", data.get("open", 0))
            .field("high", data.get("high", 0))
            .field("low", data.get("low", 0))
            .field("volume", data.get("volume", 0))
            .field("market_cap", data.get("market_cap", 0))
            .field("change_24h", data.get("change_24h", 0))
            .field("change_24h_percent", data.get("change_24h_percent", 0))
            .field("volume_24h", data.get("volume_24h", 0))
            .time(data["timestamp"], WritePrecision.NS)
        )

        self.write_api.write(bucket=self.config.database.influxdb.bucket, record=point)

    async def get_forex_data(
        self, pair: str, start_time: datetime, end_time: datetime
    ) -> List[Dict[str, Any]]:
        """Get forex data for a pair within a time range."""
        try:
            if self.config.database.type == "postgresql":
                return await self._get_forex_data_postgresql(pair, start_time, end_time)
            else:
                return await self._get_forex_data_influxdb(pair, start_time, end_time)
        except Exception as e:
            self.logger.error(f"Failed to get forex data: {e}")
            return []

    async def _get_forex_data_postgresql(
        self, pair: str, start_time: datetime, end_time: datetime
    ) -> List[Dict[str, Any]]:
        """Get forex data from PostgreSQL."""
        async with self.session_factory() as session:
            result = await session.execute(
                text(
                    """
                    SELECT pair, symbol, timestamp, rate, bid, ask, open_rate, high_rate, low_rate, volume, source
                    FROM forex_data
                    WHERE pair = :pair AND timestamp BETWEEN :start_time AND :end_time
                    ORDER BY timestamp
                """
                ),
                {"pair": pair, "start_time": start_time, "end_time": end_time},
            )

            return [dict(row._mapping) for row in result.fetchall()]

    async def _get_forex_data_influxdb(
        self, pair: str, start_time: datetime, end_time: datetime
    ) -> List[Dict[str, Any]]:
        """Get forex data from InfluxDB."""
        query = f"""
            from(bucket: "{self.config.database.influxdb.bucket}")
            |> range(start: {start_time.isoformat()}, stop: {end_time.isoformat()})
            |> filter(fn: (r) => r["_measurement"] == "forex_data" and r["pair"] == "{pair}")
            |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
        """

        result = self.query_api.query(query)

        data = []
        for table in result:
            for record in table.records:
                data.append(
                    {
                        "pair": record.values.get("pair"),
                        "symbol": record.values.get("symbol"),
                        "timestamp": record.get_time(),
                        "rate": record.values.get("rate"),
                        "bid": record.values.get("bid"),
                        "ask": record.values.get("ask"),
                        "open": record.values.get("open"),
                        "high": record.values.get("high"),
                        "low": record.values.get("low"),
                        "volume": record.values.get("volume"),
                        "source": record.values.get("source"),
                    }
                )

        return data

    async def get_crypto_data(
        self, symbol: str, start_time: datetime, end_time: datetime
    ) -> List[Dict[str, Any]]:
        """Get crypto data for a symbol within a time range."""
        try:
            if self.config.database.type == "postgresql":
                return await self._get_crypto_data_postgresql(
                    symbol, start_time, end_time
                )
            else:
                return await self._get_crypto_data_influxdb(
                    symbol, start_time, end_time
                )
        except Exception as e:
            self.logger.error(f"Failed to get crypto data: {e}")
            return []

    async def _get_crypto_data_postgresql(
        self, symbol: str, start_time: datetime, end_time: datetime
    ) -> List[Dict[str, Any]]:
        """Get crypto data from PostgreSQL."""
        async with self.session_factory() as session:
            result = await session.execute(
                text(
                    """
                    SELECT symbol, crypto, timestamp, price, open_price, high_price, low_price, volume, 
                           market_cap, change_24h, change_24h_percent, volume_24h, source
                    FROM crypto_data
                    WHERE symbol = :symbol AND timestamp BETWEEN :start_time AND :end_time
                    ORDER BY timestamp
                """
                ),
                {"symbol": symbol, "start_time": start_time, "end_time": end_time},
            )

            return [dict(row._mapping) for row in result.fetchall()]

    async def _get_crypto_data_influxdb(
        self, symbol: str, start_time: datetime, end_time: datetime
    ) -> List[Dict[str, Any]]:
        """Get crypto data from InfluxDB."""
        query = f"""
            from(bucket: "{self.config.database.influxdb.bucket}")
            |> range(start: {start_time.isoformat()}, stop: {end_time.isoformat()})
            |> filter(fn: (r) => r["_measurement"] == "crypto_data" and r["symbol"] == "{symbol}")
            |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
        """

        result = self.query_api.query(query)

        data = []
        for table in result:
            for record in table.records:
                data.append(
                    {
                        "symbol": record.values.get("symbol"),
                        "crypto": record.values.get("crypto"),
                        "timestamp": record.get_time(),
                        "price": record.values.get("price"),
                        "open": record.values.get("open"),
                        "high": record.values.get("high"),
                        "low": record.values.get("low"),
                        "volume": record.values.get("volume"),
                        "market_cap": record.values.get("market_cap"),
                        "change_24h": record.values.get("change_24h"),
                        "change_24h_percent": record.values.get("change_24h_percent"),
                        "volume_24h": record.values.get("volume_24h"),
                        "source": record.values.get("source"),
                    }
                )

        return data

    async def get_commodity_data(
        self, symbol: str, start_time: datetime, end_time: datetime
    ) -> List[Dict[str, Any]]:
        """Get commodity data for a symbol within a time range."""
        try:
            if self.config.database.type == "postgresql":
                return await self._get_commodity_data_postgresql(
                    symbol, start_time, end_time
                )
            else:
                return await self._get_commodity_data_influxdb(
                    symbol, start_time, end_time
                )
        except Exception as e:
            self.logger.error(f"Failed to get commodity data: {e}")
            return []

    async def _get_commodity_data_postgresql(
        self, symbol: str, start_time: datetime, end_time: datetime
    ) -> List[Dict[str, Any]]:
        """Get commodity data from PostgreSQL."""
        async with self.session_factory() as session:
            result = await session.execute(
                text(
                    """
                    SELECT symbol, timestamp, price, volume, commodity_type
                    FROM commodity_data
                    WHERE symbol = :symbol AND timestamp BETWEEN :start_time AND :end_time
                    ORDER BY timestamp
                """
                ),
                {"symbol": symbol, "start_time": start_time, "end_time": end_time},
            )

            return [dict(row._mapping) for row in result.fetchall()]

    async def _get_commodity_data_influxdb(
        self, symbol: str, start_time: datetime, end_time: datetime
    ) -> List[Dict[str, Any]]:
        """Get commodity data from InfluxDB."""
        query = f"""
            from(bucket: "{self.config.database.influxdb.bucket}")
            |> range(start: {start_time.isoformat()}, stop: {end_time.isoformat()})
            |> filter(fn: (r) => r["_measurement"] == "commodity_data" and r["symbol"] == "{symbol}")
            |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
        """

        result = self.query_api.query(query)

        data = []
        for table in result:
            for record in table.records:
                data.append(
                    {
                        "symbol": record.values.get("symbol"),
                        "timestamp": record.get_time(),
                        "price": record.values.get("price"),
                        "volume": record.values.get("volume"),
                        "commodity_type": record.values.get("commodity_type"),
                    }
                )

        return data

    # News data methods
    async def save_news_data(self, data: Dict[str, Any]):
        """Save news data to database."""
        try:
            if self.config.database.type == "postgresql":
                await self._save_news_data_postgresql(data)
            elif self.config.database.type == "influxdb":
                await self._save_news_data_influxdb(data)
            elif self.config.database.type == "dual":
                # Save to both databases
                await self._save_news_data_postgresql(data)
                await self._save_news_data_influxdb(data)
        except Exception as e:
            self.logger.error(f"Failed to save news data: {e}")
            raise

    async def _save_news_data_postgresql(self, data: Dict[str, Any]):
        """Save news data to PostgreSQL."""
        async with self.session_factory() as session:
            news_data = NewsData(
                title=data.get("title"),
                content=data.get("content"),
                source=data.get("source"),
                url=data.get("url"),
                published_at=data.get("published_at"),
                sentiment_score=data.get("sentiment_score"),
                sentiment_label=data.get("sentiment_label"),
                related_symbols=data.get("related_symbols", []),
            )
            session.add(news_data)
            await session.commit()

    async def _save_news_data_influxdb(self, data: Dict[str, Any]):
        """Save news data to InfluxDB."""
        point = (
            Point("news_data")
            .tag("source", data.get("source", "unknown"))
            .tag("sentiment_label", data.get("sentiment_label", "neutral"))
            .field("sentiment_score", data.get("sentiment_score", 0))
            .field("title_length", len(data.get("title", "")))
            .field("content_length", len(data.get("content", "")))
            .time(data.get("published_at", datetime.utcnow()), WritePrecision.NS)
        )

        self.write_api.write(bucket=self.config.database.influxdb.bucket, record=point)

    # Portfolio methods
    async def save_portfolio(self, portfolio_data: Dict[str, Any]) -> int:
        """Save portfolio data and return portfolio ID."""
        try:
            async with self.session_factory() as session:
                portfolio = Portfolio(
                    name=portfolio_data["name"],
                    user_id=portfolio_data["user_id"],
                    total_value=portfolio_data.get("total_value", 0.0),
                    currency=portfolio_data.get("currency", "USD"),
                )
                session.add(portfolio)
                await session.commit()
                await session.refresh(portfolio)
                return portfolio.id
        except Exception as e:
            self.logger.error(f"Failed to save portfolio: {e}")
            raise

    async def save_portfolio_position(self, position_data: Dict[str, Any]):
        """Save portfolio position data."""
        try:
            async with self.session_factory() as session:
                position = PortfolioPosition(
                    portfolio_id=position_data["portfolio_id"],
                    symbol=position_data["symbol"],
                    quantity=position_data["quantity"],
                    average_price=position_data["average_price"],
                    current_price=position_data.get("current_price"),
                    market_value=position_data.get("market_value"),
                    unrealized_pnl=position_data.get("unrealized_pnl"),
                    realized_pnl=position_data.get("realized_pnl", 0.0),
                )
                session.add(position)
                await session.commit()
        except Exception as e:
            self.logger.error(f"Failed to save portfolio position: {e}")
            raise

    # Alert methods
    async def save_alert(self, alert_data: Dict[str, Any]):
        """Save alert data."""
        try:
            async with self.session_factory() as session:
                alert = Alert(
                    symbol=alert_data["symbol"],
                    alert_type=alert_data["alert_type"],
                    threshold=alert_data.get("threshold"),
                    current_value=alert_data.get("current_value"),
                    user_id=alert_data.get("user_id"),
                    notification_sent=alert_data.get("notification_sent", False),
                )
                session.add(alert)
                await session.commit()
        except Exception as e:
            self.logger.error(f"Failed to save alert: {e}")
            raise

    async def get_active_alerts(
        self, symbol: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get active alerts, optionally filtered by symbol."""
        try:
            async with self.session_factory() as session:
                query = text(
                    """
                    SELECT * FROM alerts 
                    WHERE is_active = true
                """
                )

                if symbol:
                    query = text(
                        """
                        SELECT * FROM alerts 
                        WHERE is_active = true AND symbol = :symbol
                    """
                    )
                    result = await session.execute(query, {"symbol": symbol})
                else:
                    result = await session.execute(query)

                return [dict(row._mapping) for row in result.fetchall()]
        except Exception as e:
            self.logger.error(f"Failed to get active alerts: {e}")
            raise

    # Batch operations
    async def batch_save_stock_data(self, data_list: List[Dict[str, Any]]):
        """Save multiple stock data records in batch."""
        try:
            if self.config.database.type == "postgresql":
                await self._batch_save_stock_data_postgresql(data_list)
            elif self.config.database.type == "influxdb":
                await self._batch_save_stock_data_influxdb(data_list)
            elif self.config.database.type == "dual":
                # Save to both databases
                await self._batch_save_stock_data_postgresql(data_list)
                await self._batch_save_stock_data_influxdb(data_list)
        except Exception as e:
            self.logger.error(f"Failed to batch save stock data: {e}")
            raise

    async def _batch_save_stock_data_postgresql(self, data_list: List[Dict[str, Any]]):
        """Batch save stock data to PostgreSQL."""
        async with self.session_factory() as session:
            stock_data_objects = []
            for data in data_list:
                stock_data = StockData(
                    symbol=data["symbol"],
                    timestamp=data["timestamp"],
                    open_price=data.get("open"),
                    high_price=data.get("high"),
                    low_price=data.get("low"),
                    close_price=data.get("close"),
                    volume=data.get("volume"),
                    exchange=data.get("exchange"),
                    currency=data.get("currency", "USD"),
                )
                stock_data_objects.append(stock_data)

            session.add_all(stock_data_objects)
            await session.commit()

    async def _batch_save_stock_data_influxdb(self, data_list: List[Dict[str, Any]]):
        """Batch save stock data to InfluxDB."""
        points = []
        for data in data_list:
            point = (
                Point("stock_data")
                .tag("symbol", data["symbol"])
                .tag("exchange", data.get("exchange", "unknown"))
                .field("open", data.get("open", 0))
                .field("high", data.get("high", 0))
                .field("low", data.get("low", 0))
                .field("close", data.get("close", 0))
                .field("volume", data.get("volume", 0))
                .time(data["timestamp"], WritePrecision.NS)
            )
            points.append(point)

        self.write_api.write(bucket=self.config.database.influxdb.bucket, record=points)


class SyncDatabaseManager:
    """Synchronous database manager for Celery tasks."""

    def __init__(self, config):
        self.config = config
        self.logger = get_logger(__name__)
        self.engine = None
        self.session_factory = None

    def initialize(self):
        """Initialize synchronous database connection."""
        try:
            if self.config.database.type == "postgresql":
                self._init_postgresql_sync()

            self.logger.info("Sync database initialized successfully")

        except Exception as e:
            self.logger.error(f"Failed to initialize sync database: {e}")
            raise

    def _init_postgresql_sync(self):
        """Initialize synchronous PostgreSQL connection."""
        # Use psycopg2 for synchronous connections in Celery tasks
        database_url = self.config.get_sync_database_url()
        self.engine = create_engine(
            database_url,
            poolclass=QueuePool,
            pool_size=getattr(self.config.performance, "connection_pool_size", 10),
            max_overflow=20,
            pool_pre_ping=True,
            echo=False,
        )

        # Create session factory
        self.session_factory = sessionmaker(self.engine, expire_on_commit=False)

        # Create tables
        try:
            Base.metadata.create_all(self.engine)
        except Exception as e:
            self.logger.warning(f"Could not create tables: {e}")

        self.logger.info("Sync PostgreSQL connection established")

    def get_session(self):
        """Get a database session."""
        return self.session_factory()

    def close(self):
        """Close database connections."""
        try:
            if self.engine:
                self.engine.dispose()
            self.logger.info("Sync database connections closed")
        except Exception as e:
            self.logger.error(f"Error closing sync database connections: {e}")


# Global instances
_db_manager = None
_sync_db_manager = None


def get_database_manager():
    """Get global async database manager instance."""
    global _db_manager
    if _db_manager is None:
        from src.utils.config import get_config

        config = get_config()
        _db_manager = DatabaseManager(config)
    return _db_manager


def get_sync_database_manager():
    """Get global sync database manager instance for Celery tasks."""
    global _sync_db_manager
    if _sync_db_manager is None:
        from src.utils.config import get_config

        config = get_config()
        _sync_db_manager = SyncDatabaseManager(config)
        try:
            _sync_db_manager.initialize()
        except Exception as e:
            print(f"Warning: Could not initialize sync database manager: {e}")
    return _sync_db_manager
