"""
InfluxDB Time-Series Data Synchronization System
Real-time sync for financial market data with advanced analytics
"""

import asyncio
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import logging

from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from influxdb_client.client.query_api import QueryApi

from src.utils.config import get_config
from src.utils.logger import get_logger


@dataclass
class MarketData:
    """Market data structure for time-series sync."""

    symbol: str
    timestamp: datetime
    price: float
    volume: float
    asset_type: str  # 'stock', 'crypto', 'forex', 'commodity'
    exchange: str
    bid: Optional[float] = None
    ask: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    open: Optional[float] = None


@dataclass
class PortfolioMetrics:
    """Portfolio metrics for real-time monitoring."""

    timestamp: datetime
    total_value: float
    pnl_daily: float
    pnl_total: float
    var_99: float
    cvar_99: float
    max_drawdown: float
    sharpe_ratio: float
    beta: float
    positions_count: int


class InfluxDBSyncManager:
    """Advanced InfluxDB synchronization for real-time financial monitoring."""

    def __init__(self):
        self.config = get_config()
        self.logger = get_logger(__name__)
        self.client = None
        self.write_api = None
        self.query_api = None
        self.running = False

        # Analytics cache for performance
        self.price_cache = {}
        self.portfolio_cache = {}

    async def initialize(self):
        """Initialize InfluxDB connection and setup buckets."""
        try:
            self.client = InfluxDBClient(
                url=self.config.database.influxdb.url,
                token=self.config.database.influxdb.token,
                org=self.config.database.influxdb.org,
            )

            self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
            self.query_api = self.client.query_api()

            # Create buckets for different data types
            await self._setup_buckets()

            self.logger.info("InfluxDB Sync Manager initialized successfully")

        except Exception as e:
            self.logger.error(f"Failed to initialize InfluxDB: {e}")
            raise

    async def _setup_buckets(self):
        """Setup InfluxDB buckets for different data types."""
        buckets_api = self.client.buckets_api()

        required_buckets = [
            ("market_data", "Real-time market data", "7d"),
            ("portfolio_metrics", "Portfolio P&L and risk metrics", "90d"),
            ("risk_analytics", "VaR, CVaR, and risk calculations", "30d"),
            ("options_data", "Options chain and Greeks", "7d"),
            ("vix_data", "VIX and volatility indicators", "30d"),
            ("global_exchanges", "Multi-exchange data", "7d"),
        ]

        for bucket_name, description, retention in required_buckets:
            try:
                buckets_api.create_bucket(
                    bucket_name=bucket_name,
                    description=description,
                    org=self.config.database.influxdb.org,
                    retention_rules=[
                        {
                            "type": "expire",
                            "everySeconds": self._parse_retention(retention),
                        }
                    ],
                )
                self.logger.info(f"Created bucket: {bucket_name}")
            except Exception as e:
                # Bucket might already exist
                self.logger.debug(f"Bucket {bucket_name} might already exist: {e}")

    def _parse_retention(self, retention_str: str) -> int:
        """Parse retention string to seconds."""
        if retention_str.endswith("d"):
            return int(retention_str[:-1]) * 24 * 3600
        elif retention_str.endswith("h"):
            return int(retention_str[:-1]) * 3600
        return 24 * 3600  # Default 1 day

    # =====================================================
    # REAL-TIME MARKET DATA SYNC
    # =====================================================

    async def sync_market_data(self, data: MarketData):
        """Sync real-time market data to InfluxDB."""
        try:
            point = (
                Point("market_data")
                .tag("symbol", data.symbol)
                .tag("asset_type", data.asset_type)
                .tag("exchange", data.exchange)
                .field("price", data.price)
                .field("volume", data.volume)
                .time(data.timestamp, WritePrecision.NS)
            )

            if data.bid:
                point = point.field("bid", data.bid)
            if data.ask:
                point = point.field("ask", data.ask)
            if data.high:
                point = point.field("high", data.high)
            if data.low:
                point = point.field("low", data.low)
            if data.open:
                point = point.field("open", data.open)

            # Calculate spread if bid/ask available
            if data.bid and data.ask:
                spread = data.ask - data.bid
                spread_bps = (spread / ((data.bid + data.ask) / 2)) * 10000
                point = point.field("spread", spread).field("spread_bps", spread_bps)

            self.write_api.write(bucket="market_data", record=point)

            # Update price cache for analytics
            self.price_cache[data.symbol] = {
                "price": data.price,
                "timestamp": data.timestamp,
                "asset_type": data.asset_type,
            }

        except Exception as e:
            self.logger.error(f"Failed to sync market data for {data.symbol}: {e}")

    async def sync_portfolio_metrics(self, metrics: PortfolioMetrics):
        """Sync real-time portfolio metrics to InfluxDB."""
        try:
            point = (
                Point("portfolio_metrics")
                .field("total_value", metrics.total_value)
                .field("pnl_daily", metrics.pnl_daily)
                .field("pnl_total", metrics.pnl_total)
                .field("var_99", metrics.var_99)
                .field("cvar_99", metrics.cvar_99)
                .field("max_drawdown", metrics.max_drawdown)
                .field("sharpe_ratio", metrics.sharpe_ratio)
                .field("beta", metrics.beta)
                .field("positions_count", metrics.positions_count)
                .time(metrics.timestamp, WritePrecision.NS)
            )

            self.write_api.write(bucket="portfolio_metrics", record=point)

        except Exception as e:
            self.logger.error(f"Failed to sync portfolio metrics: {e}")

    # =====================================================
    # REAL-TIME P&L CALCULATION
    # =====================================================

    async def calculate_realtime_pnl(self, portfolio_id: str) -> Dict[str, float]:
        """Calculate real-time P&L using InfluxDB time-series data."""
        try:
            # Query for portfolio positions from PostgreSQL (via database manager)
            # and current prices from InfluxDB

            query = f"""
            from(bucket: "market_data")
                |> range(start: -1h)
                |> filter(fn: (r) => r["_measurement"] == "market_data")
                |> filter(fn: (r) => r["_field"] == "price")
                |> group(columns: ["symbol"])
                |> last()
            """

            result = self.query_api.query(query=query)
            current_prices = {}

            for table in result:
                for record in table.records:
                    symbol = record.get_value()
                    price = record.get_field()
                    if price == "price":
                        current_prices[symbol] = record.get_value()

            # Calculate P&L (this would integrate with your portfolio data)
            total_pnl = 0.0
            daily_pnl = 0.0

            # This is a simplified example - you'd get actual positions from PostgreSQL
            for symbol, current_price in current_prices.items():
                if symbol in self.portfolio_cache:
                    position = self.portfolio_cache[symbol]
                    cost_basis = position.get("cost_basis", current_price)
                    quantity = position.get("quantity", 0)

                    position_pnl = (current_price - cost_basis) * quantity
                    total_pnl += position_pnl

            return {
                "total_pnl": total_pnl,
                "daily_pnl": daily_pnl,
                "unrealized_pnl": total_pnl,
                "realized_pnl": 0.0,  # Would come from trade history
            }

        except Exception as e:
            self.logger.error(f"Failed to calculate real-time P&L: {e}")
            return {"total_pnl": 0.0, "daily_pnl": 0.0}

    # =====================================================
    # VAR/CVAR RISK CALCULATIONS
    # =====================================================

    async def calculate_var_cvar(
        self, portfolio_symbols: List[str], confidence_level: float = 0.99
    ) -> Tuple[float, float]:
        """Calculate Value at Risk and Conditional VaR using InfluxDB time-series data."""
        try:
            # Get historical price data for portfolio symbols
            lookback_days = 252  # 1 year of trading days

            query = f"""
            from(bucket: "market_data")
                |> range(start: -{lookback_days}d)
                |> filter(fn: (r) => r["_measurement"] == "market_data")
                |> filter(fn: (r) => r["_field"] == "price")
                |> filter(fn: (r) => contains(value: r["symbol"], set: {portfolio_symbols}))
                |> aggregateWindow(every: 1d, fn: last, createEmpty: false)
                |> pivot(rowKey:["_time"], columnKey: ["symbol"], valueColumn: "_value")
            """

            result = self.query_api.query(query=query)

            # Convert to pandas DataFrame for analysis
            price_data = []
            for table in result:
                for record in table.records:
                    price_data.append(
                        {
                            "timestamp": record.get_time(),
                            "symbol": record.values.get("symbol"),
                            "price": record.get_value(),
                        }
                    )

            if not price_data:
                return 0.0, 0.0

            df = pd.DataFrame(price_data)
            df_pivot = df.pivot(index="timestamp", columns="symbol", values="price")

            # Calculate daily returns
            returns = df_pivot.pct_change().dropna()

            # Portfolio returns (equal weighted for simplicity)
            portfolio_returns = returns.mean(axis=1)

            # Calculate VaR
            var_percentile = (1 - confidence_level) * 100
            var = np.percentile(portfolio_returns, var_percentile)

            # Calculate CVaR (Expected Shortfall)
            cvar = portfolio_returns[portfolio_returns <= var].mean()

            # Convert to dollar amounts (assuming $100k portfolio)
            portfolio_value = 100000  # This should come from actual portfolio value
            var_dollar = abs(var * portfolio_value)
            cvar_dollar = abs(cvar * portfolio_value)

            # Store in InfluxDB
            await self._store_risk_metrics(var_dollar, cvar_dollar, confidence_level)

            return var_dollar, cvar_dollar

        except Exception as e:
            self.logger.error(f"Failed to calculate VaR/CVaR: {e}")
            return 0.0, 0.0

    async def _store_risk_metrics(self, var: float, cvar: float, confidence: float):
        """Store risk metrics in InfluxDB."""
        point = (
            Point("risk_metrics")
            .tag("confidence_level", str(confidence))
            .field("var", var)
            .field("cvar", cvar)
            .field("var_cvar_ratio", cvar / var if var > 0 else 0)
            .time(datetime.now(), WritePrecision.NS)
        )

        self.write_api.write(bucket="risk_analytics", record=point)

    # =====================================================
    # MAX DRAWDOWN CALCULATION
    # =====================================================

    async def calculate_max_drawdown(self, lookback_days: int = 252) -> float:
        """Calculate maximum drawdown using InfluxDB portfolio value history."""
        try:
            query = f"""
            from(bucket: "portfolio_metrics")
                |> range(start: -{lookback_days}d)
                |> filter(fn: (r) => r["_measurement"] == "portfolio_metrics")
                |> filter(fn: (r) => r["_field"] == "total_value")
                |> sort(columns: ["_time"])
            """

            result = self.query_api.query(query=query)

            portfolio_values = []
            for table in result:
                for record in table.records:
                    portfolio_values.append(record.get_value())

            if len(portfolio_values) < 2:
                return 0.0

            # Calculate running maximum and drawdown
            cumulative_max = np.maximum.accumulate(portfolio_values)
            drawdown = (portfolio_values - cumulative_max) / cumulative_max
            max_drawdown = np.min(drawdown)

            # Store in InfluxDB
            point = (
                Point("risk_metrics")
                .field("max_drawdown", abs(max_drawdown))
                .field("current_drawdown", abs(drawdown[-1]))
                .time(datetime.now(), WritePrecision.NS)
            )

            self.write_api.write(bucket="risk_analytics", record=point)

            return abs(max_drawdown)

        except Exception as e:
            self.logger.error(f"Failed to calculate max drawdown: {e}")
            return 0.0

    # =====================================================
    # VIX MONITORING SYSTEM
    # =====================================================

    async def sync_vix_data(
        self, vix_value: float, vix_futures: Dict[str, float] = None
    ):
        """Sync VIX data and calculate volatility indicators."""
        try:
            point = (
                Point("vix_data")
                .field("vix_spot", vix_value)
                .time(datetime.now(), WritePrecision.NS)
            )

            # Add VIX futures if available
            if vix_futures:
                for contract, value in vix_futures.items():
                    point = point.field(f"vix_{contract}", value)

            # Calculate VIX indicators
            volatility_regime = self._classify_volatility_regime(vix_value)
            point = point.tag("volatility_regime", volatility_regime)

            # VIX term structure
            if vix_futures and len(vix_futures) >= 2:
                term_structure = self._calculate_vix_term_structure(
                    vix_value, vix_futures
                )
                point = point.field("term_structure_slope", term_structure)

            self.write_api.write(bucket="vix_data", record=point)

            # Check for volatility alerts
            await self._check_vix_alerts(vix_value)

        except Exception as e:
            self.logger.error(f"Failed to sync VIX data: {e}")

    def _classify_volatility_regime(self, vix_value: float) -> str:
        """Classify market volatility regime based on VIX level."""
        if vix_value < 15:
            return "low"
        elif vix_value < 25:
            return "normal"
        elif vix_value < 35:
            return "elevated"
        else:
            return "high"

    def _calculate_vix_term_structure(
        self, vix_spot: float, vix_futures: Dict[str, float]
    ) -> float:
        """Calculate VIX term structure slope."""
        # Simple calculation using front month future vs spot
        if "M1" in vix_futures:
            return (vix_futures["M1"] - vix_spot) / vix_spot
        return 0.0

    async def _check_vix_alerts(self, vix_value: float):
        """Check for VIX-based alerts."""
        alerts = []

        if vix_value > 30:
            alerts.append(
                {"level": "high", "message": f"VIX elevated at {vix_value:.2f}"}
            )

        if vix_value > 40:
            alerts.append(
                {"level": "critical", "message": f"VIX critical at {vix_value:.2f}"}
            )

        # Store alerts in InfluxDB
        for alert in alerts:
            point = (
                Point("volatility_alerts")
                .tag("level", alert["level"])
                .field("vix_value", vix_value)
                .field("message", alert["message"])
                .time(datetime.now(), WritePrecision.NS)
            )

            self.write_api.write(bucket="risk_analytics", record=point)

    # =====================================================
    # GLOBAL EXCHANGE DATA SYNC
    # =====================================================

    async def sync_global_exchange_data(self, exchange_data: List[MarketData]):
        """Sync data from multiple global exchanges."""
        try:
            points = []

            for data in exchange_data:
                # Add timezone and session info
                session_type = self._get_trading_session(data.exchange, data.timestamp)

                point = (
                    Point("global_market_data")
                    .tag("symbol", data.symbol)
                    .tag("exchange", data.exchange)
                    .tag("asset_type", data.asset_type)
                    .tag("session_type", session_type)
                    .field("price", data.price)
                    .field("volume", data.volume)
                    .time(data.timestamp, WritePrecision.NS)
                )

                points.append(point)

            # Batch write for performance
            self.write_api.write(bucket="global_exchanges", record=points)

        except Exception as e:
            self.logger.error(f"Failed to sync global exchange data: {e}")

    def _get_trading_session(self, exchange: str, timestamp: datetime) -> str:
        """Determine trading session type based on exchange and time."""
        # Simplified session detection
        hour = timestamp.hour

        if exchange in ["NYSE", "NASDAQ"]:
            if 9 <= hour < 16:
                return "regular"
            elif 4 <= hour < 9 or 16 <= hour < 20:
                return "extended"
            else:
                return "closed"
        elif exchange in ["LSE", "FRA"]:
            if 8 <= hour < 16:
                return "regular"
            else:
                return "closed"
        elif exchange in ["TSE", "HKEX"]:
            if 9 <= hour < 15:
                return "regular"
            else:
                return "closed"

        return "unknown"

    # =====================================================
    # ANALYTICS QUERIES
    # =====================================================

    async def get_realtime_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive dashboard data for Grafana."""
        try:
            # Portfolio metrics
            portfolio_query = """
            from(bucket: "portfolio_metrics")
                |> range(start: -1h)
                |> filter(fn: (r) => r["_measurement"] == "portfolio_metrics")
                |> last()
            """

            # Risk metrics
            risk_query = """
            from(bucket: "risk_analytics")
                |> range(start: -1h)
                |> filter(fn: (r) => r["_measurement"] == "risk_metrics")
                |> last()
            """

            # VIX data
            vix_query = """
            from(bucket: "vix_data")
                |> range(start: -1h)
                |> filter(fn: (r) => r["_measurement"] == "vix_data")
                |> last()
            """

            portfolio_result = self.query_api.query(query=portfolio_query)
            risk_result = self.query_api.query(query=risk_query)
            vix_result = self.query_api.query(query=vix_query)

            # Process results
            dashboard_data = {
                "portfolio": self._process_query_result(portfolio_result),
                "risk": self._process_query_result(risk_result),
                "vix": self._process_query_result(vix_result),
                "timestamp": datetime.now().isoformat(),
            }

            return dashboard_data

        except Exception as e:
            self.logger.error(f"Failed to get dashboard data: {e}")
            return {}

    def _process_query_result(self, result) -> Dict[str, Any]:
        """Process InfluxDB query result into dictionary."""
        data = {}
        for table in result:
            for record in table.records:
                field = record.get_field()
                value = record.get_value()
                data[field] = value
        return data

    async def close(self):
        """Close InfluxDB connections."""
        if self.client:
            self.client.close()
            self.logger.info("InfluxDB Sync Manager closed")


# Global instance
influx_sync = InfluxDBSyncManager()
