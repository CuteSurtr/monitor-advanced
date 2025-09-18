"""
Commodity data collector for real-time commodity prices from multiple sources.
"""

import asyncio
import aiohttp
import yfinance as yf
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import pytz
from ratelimit import limits, sleep_and_retry

from src.utils.logger import get_logger, log_api_request
from src.utils.cache import CacheManager


class CommodityDataCollector:
    """Collects real-time commodity data from multiple sources."""

    def __init__(self, config, db_manager, cache_manager: CacheManager):
        self.config = config
        self.db_manager = db_manager
        self.cache_manager = cache_manager
        self.logger = get_logger(__name__)
        self.running = False
        self.session = None

        # API keys
        self.alpha_vantage_key = config.api_keys.alpha_vantage
        self.polygon_key = config.api_keys.polygon
        self.quandl_key = getattr(config.api_keys, "quandl", None)

        # Commodity symbols (using Yahoo Finance format)
        self.commodities = {
            # Precious Metals
            "metals": {
                "GC=F": "Gold",
                "SI=F": "Silver",
                "PL=F": "Platinum",
                "PA=F": "Palladium",
                "HG=F": "Copper",
            },
            # Energy
            "energy": {
                "CL=F": "Crude Oil WTI",
                "BZ=F": "Brent Crude Oil",
                "NG=F": "Natural Gas",
                "RB=F": "Gasoline",
                "HO=F": "Heating Oil",
            },
            # Agriculture
            "agriculture": {
                "ZC=F": "Corn",
                "ZS=F": "Soybeans",
                "ZW=F": "Wheat",
                "KC=F": "Coffee",
                "SB=F": "Sugar",
                "CT=F": "Cotton",
                "CC=F": "Cocoa",
                "LBS=F": "Lumber",
                "ZO=F": "Oats",
                "ZR=F": "Rice",
            },
            # Livestock
            "livestock": {
                "LE=F": "Live Cattle",
                "GF=F": "Feeder Cattle",
                "HE=F": "Lean Hogs",
            },
        }

        # Flatten all symbols
        self.all_symbols = []
        for category in self.commodities.values():
            self.all_symbols.extend(category.keys())

        # Trading hours (most commodities trade during US market hours)
        self.market_hours = {
            "open": "09:30",
            "close": "16:15",
            "timezone": "America/New_York",
        }

    async def start(self):
        """Start the commodity data collection process."""
        self.running = True
        self.logger.info("Starting commodity data collector")

        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(timeout=timeout)

        try:
            while self.running:
                await self._collect_data()
                await asyncio.sleep(
                    self.config.data_collection.commodity_data_interval or 300
                )

        except asyncio.CancelledError:
            self.logger.info("Commodity data collector cancelled")
        except Exception as e:
            self.logger.error(f"Error in commodity data collector: {e}")
        finally:
            if self.session:
                await self.session.close()

    async def stop(self):
        """Stop the commodity data collection process."""
        self.running = False
        self.logger.info("Stopping commodity data collector")

    async def _collect_data(self):
        """Collect commodity data from all sources."""
        try:
            # Check if commodity markets are open
            if not self._is_market_open():
                self.logger.debug("Commodity markets closed")
                return

            # Collect data in batches
            batch_size = 8
            for i in range(0, len(self.all_symbols), batch_size):
                batch = self.all_symbols[i : i + batch_size]
                await self._collect_batch_data(batch)
                await asyncio.sleep(2)  # Rate limiting

        except Exception as e:
            self.logger.error(f"Error collecting commodity data: {e}")

    def _is_market_open(self) -> bool:
        """Check if commodity markets are open."""
        now = datetime.now(pytz.UTC)
        ny_tz = pytz.timezone(self.market_hours["timezone"])
        ny_time = now.astimezone(ny_tz)

        # Weekend check
        if ny_time.weekday() >= 5:
            return False

        # Market hours check
        open_time = datetime.strptime(self.market_hours["open"], "%H:%M").time()
        close_time = datetime.strptime(self.market_hours["close"], "%H:%M").time()

        return open_time <= ny_time.time() <= close_time

    async def _collect_batch_data(self, symbols: List[str]):
        """Collect data for a batch of commodity symbols."""
        tasks = []
        for symbol in symbols:
            task = asyncio.create_task(self._collect_symbol_data(symbol))
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.error(f"Error collecting data for {symbols[i]}: {result}")

    @log_api_request(get_logger(__name__), "yfinance", "commodity_data")
    async def _collect_symbol_data(self, symbol: str):
        """Collect data for a single commodity symbol."""
        try:
            # Check cache first
            cached_data = await self.cache_manager.get_cached_commodity_data(symbol)
            if cached_data:
                cache_time = datetime.fromisoformat(cached_data.get("timestamp", ""))
                if datetime.now() - cache_time < timedelta(minutes=5):
                    return

            # Fetch fresh data
            data = await self._fetch_commodity_data(symbol)
            if data:
                # Save to database
                await self.db_manager.save_commodity_data(data)

                # Cache the data
                await self.cache_manager.cache_commodity_data(symbol, data)

                self.logger.debug(
                    f"Collected commodity data for {symbol}: ${data.get('price', 'N/A')}"
                )

        except Exception as e:
            self.logger.error(f"Error collecting data for {symbol}: {e}")

    async def _fetch_commodity_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Fetch commodity data from multiple sources."""
        sources = [self._fetch_from_yfinance, self._fetch_from_alpha_vantage]

        for source_func in sources:
            try:
                data = await source_func(symbol)
                if data:
                    return data
            except Exception as e:
                self.logger.debug(
                    f"Source {source_func.__name__} failed for {symbol}: {e}"
                )
                continue

        return None

    @sleep_and_retry
    @limits(calls=50, period=60)
    async def _fetch_from_yfinance(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Fetch commodity data from Yahoo Finance."""
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="1d", interval="1m")

            if hist.empty:
                return None

            latest = hist.iloc[-1]
            info = ticker.info

            # Get commodity name and category
            commodity_name = self._get_commodity_name(symbol)
            category = self._get_commodity_category(symbol)

            data = {
                "symbol": symbol,
                "name": commodity_name,
                "category": category,
                "timestamp": datetime.now(),
                "price": float(latest["Close"]),
                "open": float(latest["Open"]),
                "high": float(latest["High"]),
                "low": float(latest["Low"]),
                "volume": int(latest["Volume"]) if latest["Volume"] > 0 else 0,
                "currency": info.get("currency", "USD"),
                "exchange": info.get("exchange", "CME"),
                "change": 0,  # Calculate from previous close
                "change_percent": 0,
                "contract_month": self._get_contract_month(symbol),
                "source": "yfinance",
            }

            return data

        except Exception as e:
            self.logger.error(f"Error fetching from Yahoo Finance for {symbol}: {e}")
            return None

    @sleep_and_retry
    @limits(calls=5, period=60)
    async def _fetch_from_alpha_vantage(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Fetch commodity data from Alpha Vantage."""
        if not self.alpha_vantage_key:
            return None

        # Alpha Vantage has limited commodity support, mainly for WTI crude oil
        commodity_map = {"CL=F": "WTI", "BZ=F": "BRENT"}

        av_symbol = commodity_map.get(symbol)
        if not av_symbol:
            return None

        try:
            url = "https://www.alphavantage.co/query"
            params = {
                "function": "WTI" if av_symbol == "WTI" else "BRENT",
                "interval": "monthly",
                "apikey": self.alpha_vantage_key,
            }

            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()

                    if "data" in data and data["data"]:
                        latest = data["data"][0]
                        price = float(latest.get("value", 0))

                        return {
                            "symbol": symbol,
                            "name": self._get_commodity_name(symbol),
                            "category": "energy",
                            "timestamp": datetime.now(),
                            "price": price,
                            "open": price,
                            "high": price,
                            "low": price,
                            "volume": 0,
                            "currency": "USD",
                            "exchange": "NYMEX",
                            "change": 0,
                            "change_percent": 0,
                            "contract_month": self._get_contract_month(symbol),
                            "source": "alpha_vantage",
                        }

                return None

        except Exception as e:
            self.logger.error(f"Error fetching from Alpha Vantage for {symbol}: {e}")
            return None

    def _get_commodity_name(self, symbol: str) -> str:
        """Get commodity name from symbol."""
        for category in self.commodities.values():
            if symbol in category:
                return category[symbol]
        return symbol

    def _get_commodity_category(self, symbol: str) -> str:
        """Get commodity category from symbol."""
        for category_name, commodities in self.commodities.items():
            if symbol in commodities:
                return category_name
        return "other"

    def _get_contract_month(self, symbol: str) -> str:
        """Get contract month for futures (simplified)."""
        # Most symbols ending in =F are front month contracts
        return "Front Month"

    def fetch(self):
        """Legacy method for backward compatibility."""
        return []

    async def get_latest_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get latest data for a commodity symbol."""
        try:
            cached_data = await self.cache_manager.get_cached_commodity_data(symbol)
            if cached_data:
                return cached_data

            # Fallback to database
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=1)

            data_list = await self.db_manager.get_commodity_data(
                symbol, start_time, end_time
            )
            if data_list:
                return data_list[-1]

            return None

        except Exception as e:
            self.logger.error(f"Error getting latest data for {symbol}: {e}")
            return None

    async def get_historical_data(
        self, symbol: str, start_date: datetime, end_date: datetime
    ) -> List[Dict[str, Any]]:
        """Get historical data for a commodity symbol."""
        try:
            return await self.db_manager.get_commodity_data(
                symbol, start_date, end_date
            )
        except Exception as e:
            self.logger.error(f"Error getting historical data for {symbol}: {e}")
            return []

    def is_healthy(self) -> bool:
        """Check if the collector is healthy."""
        return self.running and self.session is not None

    async def get_metals(self) -> Dict[str, str]:
        """Get precious metals commodities."""
        return self.commodities["metals"].copy()

    async def get_energy(self) -> Dict[str, str]:
        """Get energy commodities."""
        return self.commodities["energy"].copy()

    async def get_agriculture(self) -> Dict[str, str]:
        """Get agricultural commodities."""
        return self.commodities["agriculture"].copy()

    async def get_livestock(self) -> Dict[str, str]:
        """Get livestock commodities."""
        return self.commodities["livestock"].copy()

    async def get_all_commodities(self) -> Dict[str, Dict[str, str]]:
        """Get all tracked commodities by category."""
        return self.commodities.copy()

    async def get_all_symbols(self) -> List[str]:
        """Get all tracked commodity symbols."""
        return self.all_symbols.copy()
