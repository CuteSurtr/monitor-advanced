"""
Multi-Exchange Data Collection Manager - US, European, and Asian market support.
"""

import asyncio
import pytz
from typing import Dict, List, Any, Optional, Set
from datetime import datetime, time, timedelta
from dataclasses import dataclass
from enum import Enum

from src.utils.logger import get_logger
from src.utils.database import DatabaseManager
from src.utils.cache import CacheManager


class ExchangeRegion(Enum):
    """Exchange regions."""

    US = "us"
    EUROPE = "europe"
    ASIA = "asia"


@dataclass
class ExchangeInfo:
    """Exchange information structure."""

    code: str
    name: str
    region: ExchangeRegion
    timezone: str
    market_open: time
    market_close: time
    currency: str
    active: bool = True


@dataclass
class TradingHours:
    """Trading hours for an exchange."""

    exchange_code: str
    is_open: bool
    next_open: Optional[datetime] = None
    next_close: Optional[datetime] = None
    session_type: str = "regular"  # regular, pre_market, after_hours


class MultiExchangeManager:
    """Manager for multi-exchange data collection across global markets."""

    def __init__(
        self, db_manager: DatabaseManager, cache_manager: CacheManager, config=None
    ):
        self.db_manager = db_manager
        self.cache_manager = cache_manager
        self.config = config
        self.logger = get_logger(__name__)
        self.running = False

        # Exchange definitions
        self.exchanges = {
            # US Exchanges
            "NYSE": ExchangeInfo(
                code="NYSE",
                name="New York Stock Exchange",
                region=ExchangeRegion.US,
                timezone="America/New_York",
                market_open=time(9, 30),
                market_close=time(16, 0),
                currency="USD",
            ),
            "NASDAQ": ExchangeInfo(
                code="NASDAQ",
                name="NASDAQ Stock Market",
                region=ExchangeRegion.US,
                timezone="America/New_York",
                market_open=time(9, 30),
                market_close=time(16, 0),
                currency="USD",
            ),
            "CBOE": ExchangeInfo(
                code="CBOE",
                name="Chicago Board Options Exchange",
                region=ExchangeRegion.US,
                timezone="America/Chicago",
                market_open=time(8, 30),
                market_close=time(15, 0),
                currency="USD",
            ),
            # European Exchanges
            "LSE": ExchangeInfo(
                code="LSE",
                name="London Stock Exchange",
                region=ExchangeRegion.EUROPE,
                timezone="Europe/London",
                market_open=time(8, 0),
                market_close=time(16, 30),
                currency="GBP",
            ),
            "XETRA": ExchangeInfo(
                code="XETRA",
                name="Frankfurt Stock Exchange",
                region=ExchangeRegion.EUROPE,
                timezone="Europe/Berlin",
                market_open=time(9, 0),
                market_close=time(17, 30),
                currency="EUR",
            ),
            "EURONEXT": ExchangeInfo(
                code="EURONEXT",
                name="Euronext",
                region=ExchangeRegion.EUROPE,
                timezone="Europe/Paris",
                market_open=time(9, 0),
                market_close=time(17, 30),
                currency="EUR",
            ),
            "SIX": ExchangeInfo(
                code="SIX",
                name="SIX Swiss Exchange",
                region=ExchangeRegion.EUROPE,
                timezone="Europe/Zurich",
                market_open=time(9, 0),
                market_close=time(17, 30),
                currency="CHF",
            ),
            # Asian Exchanges
            "TSE": ExchangeInfo(
                code="TSE",
                name="Tokyo Stock Exchange",
                region=ExchangeRegion.ASIA,
                timezone="Asia/Tokyo",
                market_open=time(9, 0),
                market_close=time(15, 0),
                currency="JPY",
            ),
            "SSE": ExchangeInfo(
                code="SSE",
                name="Shanghai Stock Exchange",
                region=ExchangeRegion.ASIA,
                timezone="Asia/Shanghai",
                market_open=time(9, 30),
                market_close=time(15, 0),
                currency="CNY",
            ),
            "SZSE": ExchangeInfo(
                code="SZSE",
                name="Shenzhen Stock Exchange",
                region=ExchangeRegion.ASIA,
                timezone="Asia/Shanghai",
                market_open=time(9, 30),
                market_close=time(15, 0),
                currency="CNY",
            ),
            "HKEX": ExchangeInfo(
                code="HKEX",
                name="Hong Kong Stock Exchange",
                region=ExchangeRegion.ASIA,
                timezone="Asia/Hong_Kong",
                market_open=time(9, 30),
                market_close=time(16, 0),
                currency="HKD",
            ),
            "KRX": ExchangeInfo(
                code="KRX",
                name="Korea Exchange",
                region=ExchangeRegion.ASIA,
                timezone="Asia/Seoul",
                market_open=time(9, 0),
                market_close=time(15, 30),
                currency="KRW",
            ),
            "BSE": ExchangeInfo(
                code="BSE",
                name="Bombay Stock Exchange",
                region=ExchangeRegion.ASIA,
                timezone="Asia/Kolkata",
                market_open=time(9, 15),
                market_close=time(15, 30),
                currency="INR",
            ),
            "NSE": ExchangeInfo(
                code="NSE",
                name="National Stock Exchange of India",
                region=ExchangeRegion.ASIA,
                timezone="Asia/Kolkata",
                market_open=time(9, 15),
                market_close=time(15, 30),
                currency="INR",
            ),
            "ASX": ExchangeInfo(
                code="ASX",
                name="Australian Securities Exchange",
                region=ExchangeRegion.ASIA,  # Grouped with Asia-Pacific
                timezone="Australia/Sydney",
                market_open=time(10, 0),
                market_close=time(16, 0),
                currency="AUD",
            ),
        }

        # Active data collectors per exchange
        self.active_collectors = {}

        # Market hours cache
        self.trading_hours_cache = {}

        # Collection intervals by region
        self.collection_intervals = {
            ExchangeRegion.US: 1,  # 1 second for US markets
            ExchangeRegion.EUROPE: 2,  # 2 seconds for European markets
            ExchangeRegion.ASIA: 3,  # 3 seconds for Asian markets
        }

    async def start(self):
        """Start the multi-exchange manager."""
        self.running = True
        self.logger.info("Starting multi-exchange data collection manager")

        try:
            # Start monitoring tasks
            tasks = [
                asyncio.create_task(self._monitor_trading_hours()),
                asyncio.create_task(self._coordinate_data_collection()),
                asyncio.create_task(self._monitor_exchange_connectivity()),
            ]

            await asyncio.gather(*tasks)

        except asyncio.CancelledError:
            self.logger.info("Multi-exchange manager cancelled")
        except Exception as e:
            self.logger.error(f"Error in multi-exchange manager: {e}")
        finally:
            self.running = False

    async def stop(self):
        """Stop the multi-exchange manager."""
        self.running = False

        # Stop all active collectors
        for exchange_code, collector in self.active_collectors.items():
            try:
                await collector.stop()
                self.logger.info(f"Stopped collector for {exchange_code}")
            except Exception as e:
                self.logger.error(f"Error stopping collector for {exchange_code}: {e}")

        self.active_collectors.clear()
        self.logger.info("Multi-exchange manager stopped")

    async def get_trading_hours(self, exchange_code: str) -> TradingHours:
        """
        Get current trading hours for an exchange.

        Args:
            exchange_code: Exchange code (e.g., 'NYSE', 'LSE', 'TSE')

        Returns:
            TradingHours object with current status
        """
        try:
            if exchange_code not in self.exchanges:
                raise ValueError(f"Unknown exchange: {exchange_code}")

            # Check cache first
            cache_key = f"trading_hours:{exchange_code}"
            cached_hours = await self.cache_manager.get(cache_key)

            if cached_hours:
                return TradingHours(**cached_hours)

            exchange = self.exchanges[exchange_code]
            exchange_tz = pytz.timezone(exchange.timezone)
            current_time = datetime.now(exchange_tz)

            # Calculate if market is open
            is_open = self._is_market_open(exchange, current_time)

            # Calculate next open/close times
            next_open, next_close = self._calculate_next_session_times(
                exchange, current_time
            )

            trading_hours = TradingHours(
                exchange_code=exchange_code,
                is_open=is_open,
                next_open=next_open,
                next_close=next_close,
                session_type=self._get_session_type(exchange, current_time),
            )

            # Cache for 1 minute
            await self.cache_manager.set(cache_key, trading_hours.__dict__, ttl=60)

            return trading_hours

        except Exception as e:
            self.logger.error(f"Error getting trading hours for {exchange_code}: {e}")
            return TradingHours(exchange_code=exchange_code, is_open=False)

    async def get_active_exchanges(self) -> List[str]:
        """Get list of currently active exchanges."""
        active_exchanges = []

        for exchange_code in self.exchanges.keys():
            trading_hours = await self.get_trading_hours(exchange_code)
            if trading_hours.is_open:
                active_exchanges.append(exchange_code)

        return active_exchanges

    async def get_global_market_status(self) -> Dict[str, Any]:
        """Get global market status across all regions."""
        try:
            status = {
                "timestamp": datetime.now().isoformat(),
                "regions": {},
                "active_exchanges": [],
                "total_exchanges": len(self.exchanges),
                "collection_stats": {},
            }

            # Group by region
            by_region = {}
            for exchange_code, exchange in self.exchanges.items():
                region = exchange.region.value
                if region not in by_region:
                    by_region[region] = []
                by_region[region].append(exchange_code)

            # Get status for each region
            for region, exchange_codes in by_region.items():
                region_status = {
                    "exchanges": {},
                    "open_count": 0,
                    "total_count": len(exchange_codes),
                }

                for exchange_code in exchange_codes:
                    trading_hours = await self.get_trading_hours(exchange_code)

                    region_status["exchanges"][exchange_code] = {
                        "is_open": trading_hours.is_open,
                        "next_open": (
                            trading_hours.next_open.isoformat()
                            if trading_hours.next_open
                            else None
                        ),
                        "next_close": (
                            trading_hours.next_close.isoformat()
                            if trading_hours.next_close
                            else None
                        ),
                        "session_type": trading_hours.session_type,
                        "currency": self.exchanges[exchange_code].currency,
                    }

                    if trading_hours.is_open:
                        region_status["open_count"] += 1
                        status["active_exchanges"].append(exchange_code)

                status["regions"][region] = region_status

            # Add collection statistics
            status["collection_stats"] = await self._get_collection_stats()

            return status

        except Exception as e:
            self.logger.error(f"Error getting global market status: {e}")
            return {"error": str(e)}

    async def get_exchange_symbols(self, exchange_code: str) -> List[str]:
        """Get symbols traded on a specific exchange."""
        # This would be implemented based on your symbol mapping
        symbol_mapping = {
            "NYSE": ["AAPL", "MSFT", "JNJ", "WMT", "PG"],
            "NASDAQ": ["GOOGL", "AMZN", "TSLA", "NVDA", "META"],
            "LSE": ["VODL", "AZN", "RIO", "BP", "SHEL"],
            "XETRA": ["SAP", "SIEGY", "BASF", "BMW", "MBG"],
            "TSE": ["7203", "9984", "6758", "8306", "9432"],
            "HKEX": ["0700", "9988", "0941", "1299", "0005"],
            "ASX": ["CBA", "BHP", "CSL", "WBC", "ANZ"],
        }

        return symbol_mapping.get(exchange_code, [])

    async def _monitor_trading_hours(self):
        """Monitor trading hours for all exchanges."""
        while self.running:
            try:
                for exchange_code in self.exchanges.keys():
                    # Update trading hours cache
                    await self.get_trading_hours(exchange_code)

                await asyncio.sleep(60)  # Check every minute

            except Exception as e:
                self.logger.error(f"Error monitoring trading hours: {e}")
                await asyncio.sleep(60)

    async def _coordinate_data_collection(self):
        """Coordinate data collection across exchanges."""
        while self.running:
            try:
                active_exchanges = await self.get_active_exchanges()

                # Start collectors for active exchanges
                for exchange_code in active_exchanges:
                    if exchange_code not in self.active_collectors:
                        await self._start_exchange_collector(exchange_code)

                # Stop collectors for inactive exchanges
                inactive_collectors = set(self.active_collectors.keys()) - set(
                    active_exchanges
                )
                for exchange_code in inactive_collectors:
                    await self._stop_exchange_collector(exchange_code)

                await asyncio.sleep(30)  # Check every 30 seconds

            except Exception as e:
                self.logger.error(f"Error coordinating data collection: {e}")
                await asyncio.sleep(60)

    async def _monitor_exchange_connectivity(self):
        """Monitor connectivity to all exchanges."""
        while self.running:
            try:
                connectivity_status = {}

                for exchange_code in self.exchanges.keys():
                    # Test connectivity (mock implementation)
                    is_connected = await self._test_exchange_connectivity(exchange_code)
                    connectivity_status[exchange_code] = is_connected

                    if not is_connected:
                        self.logger.warning(
                            f"Connectivity issue detected for {exchange_code}"
                        )

                # Cache connectivity status
                await self.cache_manager.set(
                    "exchange_connectivity", connectivity_status, ttl=300
                )

                await asyncio.sleep(120)  # Check every 2 minutes

            except Exception as e:
                self.logger.error(f"Error monitoring exchange connectivity: {e}")
                await asyncio.sleep(120)

    def _is_market_open(self, exchange: ExchangeInfo, current_time: datetime) -> bool:
        """Check if market is currently open."""
        # Simplified - doesn't account for holidays, half-days, etc.
        if current_time.weekday() >= 5:  # Weekend
            return False

        current_time_only = current_time.time()

        # Handle exchanges that close next day (like some Asian markets)
        if exchange.market_close < exchange.market_open:
            return (
                current_time_only >= exchange.market_open
                or current_time_only <= exchange.market_close
            )
        else:
            return exchange.market_open <= current_time_only <= exchange.market_close

    def _calculate_next_session_times(
        self, exchange: ExchangeInfo, current_time: datetime
    ) -> tuple:
        """Calculate next open and close times."""
        # Simplified implementation
        current_date = current_time.date()
        exchange_tz = pytz.timezone(exchange.timezone)

        # Next open
        next_open_dt = datetime.combine(current_date, exchange.market_open)
        next_open = exchange_tz.localize(next_open_dt)

        if next_open <= current_time:
            # Market opens tomorrow
            next_open_dt = datetime.combine(
                current_date + timedelta(days=1), exchange.market_open
            )
            next_open = exchange_tz.localize(next_open_dt)

        # Next close
        next_close_dt = datetime.combine(current_date, exchange.market_close)
        next_close = exchange_tz.localize(next_close_dt)

        if next_close <= current_time:
            # Market closes tomorrow
            next_close_dt = datetime.combine(
                current_date + timedelta(days=1), exchange.market_close
            )
            next_close = exchange_tz.localize(next_close_dt)

        return next_open, next_close

    def _get_session_type(self, exchange: ExchangeInfo, current_time: datetime) -> str:
        """Determine session type (regular, pre_market, after_hours)."""
        # Simplified - always return regular for now
        return "regular"

    async def _start_exchange_collector(self, exchange_code: str):
        """Start data collector for an exchange."""
        try:
            exchange = self.exchanges[exchange_code]
            symbols = await self.get_exchange_symbols(exchange_code)

            # Create appropriate collector based on exchange region
            if exchange.region == ExchangeRegion.US:
                from src.collectors.stock_collector import StockDataCollector

                collector = StockDataCollector(
                    self.db_manager, self.cache_manager, symbols=symbols
                )
            else:
                # Use generic international collector
                collector = await self._create_international_collector(
                    exchange_code, symbols
                )

            # Start the collector
            collector_task = asyncio.create_task(collector.start())
            self.active_collectors[exchange_code] = {
                "collector": collector,
                "task": collector_task,
                "started_at": datetime.now(),
            }

            self.logger.info(f"Started data collector for {exchange_code}")

        except Exception as e:
            self.logger.error(f"Error starting collector for {exchange_code}: {e}")

    async def _stop_exchange_collector(self, exchange_code: str):
        """Stop data collector for an exchange."""
        try:
            if exchange_code in self.active_collectors:
                collector_info = self.active_collectors[exchange_code]

                # Stop the collector
                await collector_info["collector"].stop()

                # Cancel the task
                if not collector_info["task"].done():
                    collector_info["task"].cancel()

                del self.active_collectors[exchange_code]
                self.logger.info(f"Stopped data collector for {exchange_code}")

        except Exception as e:
            self.logger.error(f"Error stopping collector for {exchange_code}: {e}")

    async def _create_international_collector(
        self, exchange_code: str, symbols: List[str]
    ):
        """Create international data collector."""
        # Mock implementation - would create appropriate collector
        from src.collectors.stock_collector import StockDataCollector

        return StockDataCollector(self.db_manager, self.cache_manager, symbols=symbols)

    async def _test_exchange_connectivity(self, exchange_code: str) -> bool:
        """Test connectivity to an exchange."""
        # Mock implementation - would test actual connectivity
        return True

    async def _get_collection_stats(self) -> Dict[str, Any]:
        """Get data collection statistics."""
        stats = {"active_collectors": len(self.active_collectors), "collectors": {}}

        for exchange_code, collector_info in self.active_collectors.items():
            stats["collectors"][exchange_code] = {
                "started_at": collector_info["started_at"].isoformat(),
                "uptime_seconds": (
                    datetime.now() - collector_info["started_at"]
                ).total_seconds(),
                "status": "active",
            }

        return stats

    def is_healthy(self) -> bool:
        """Check if the multi-exchange manager is healthy."""
        return self.running
