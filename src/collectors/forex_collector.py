"""
Forex data collector for real-time currency exchange rates from multiple sources.
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


class ForexDataCollector:
    """Collects real-time forex data from multiple sources."""

    def __init__(self, config, db_manager, cache_manager: CacheManager):
        self.config = config
        self.db_manager = db_manager
        self.cache_manager = cache_manager
        self.logger = get_logger(__name__)
        self.running = False
        self.session = None

        # API rate limiting
        self.alpha_vantage_key = config.api_keys.alpha_vantage
        self.polygon_key = config.api_keys.polygon
        self.fixer_key = getattr(config.api_keys, "fixer", None)
        self.exchangerate_key = getattr(config.api_keys, "exchangerate", None)

        # Major forex pairs
        self.forex_pairs = [
            "EUR/USD",
            "GBP/USD",
            "USD/JPY",
            "USD/CHF",
            "AUD/USD",
            "USD/CAD",
            "NZD/USD",
            "EUR/GBP",
            "EUR/JPY",
            "GBP/JPY",
            "AUD/JPY",
            "EUR/CHF",
            "GBP/CHF",
            "CHF/JPY",
            "EUR/AUD",
            "EUR/CAD",
            "GBP/AUD",
            "GBP/CAD",
            "AUD/CAD",
            "CAD/JPY",
            "USD/CNY",
            "USD/HKD",
            "USD/SGD",
            "USD/KRW",
            "USD/INR",
            "USD/MXN",
            "EUR/NOK",
            "EUR/SEK",
            "EUR/DKK",
            "EUR/PLN",
            "USD/NOK",
            "USD/SEK",
        ]

        # Convert to yfinance format
        self.yf_pairs = [pair.replace("/", "") + "=X" for pair in self.forex_pairs]

        # Forex market hours (24/5)
        self.market_hours = {
            "sydney": {
                "open": "17:00",
                "close": "02:00",
                "timezone": "Australia/Sydney",
            },
            "tokyo": {"open": "00:00", "close": "09:00", "timezone": "Asia/Tokyo"},
            "london": {"open": "08:00", "close": "17:00", "timezone": "Europe/London"},
            "new_york": {
                "open": "13:00",
                "close": "22:00",
                "timezone": "America/New_York",
            },
        }

    async def start(self):
        """Start the forex data collection process."""
        self.running = True
        self.logger.info("Starting forex data collector")

        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(timeout=timeout)

        try:
            while self.running:
                await self._collect_data()
                await asyncio.sleep(
                    self.config.data_collection.forex_data_interval or 60
                )

        except asyncio.CancelledError:
            self.logger.info("Forex data collector cancelled")
        except Exception as e:
            self.logger.error(f"Error in forex data collector: {e}")
        finally:
            if self.session:
                await self.session.close()

    async def stop(self):
        """Stop the forex data collection process."""
        self.running = False
        self.logger.info("Stopping forex data collector")

    async def _collect_data(self):
        """Collect forex data from all sources."""
        try:
            # Forex markets trade 24/5, check if it's weekend
            if self._is_weekend():
                self.logger.debug("Forex markets closed (weekend)")
                return

            # Collect data in batches
            batch_size = 10
            for i in range(0, len(self.yf_pairs), batch_size):
                batch = self.yf_pairs[i : i + batch_size]
                await self._collect_batch_data(batch)
                await asyncio.sleep(2)  # Rate limiting

        except Exception as e:
            self.logger.error(f"Error collecting forex data: {e}")

    def _is_weekend(self) -> bool:
        """Check if it's weekend (forex markets closed)."""
        now = datetime.now(pytz.UTC)
        # Forex closes Friday 22:00 UTC, opens Sunday 22:00 UTC
        if now.weekday() == 5:  # Saturday
            return True
        if now.weekday() == 6 and now.hour < 22:  # Sunday before 22:00 UTC
            return True
        return False

    async def _collect_batch_data(self, pairs: List[str]):
        """Collect data for a batch of forex pairs."""
        tasks = []
        for pair in pairs:
            task = asyncio.create_task(self._collect_pair_data(pair))
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.error(f"Error collecting data for {pairs[i]}: {result}")

    @log_api_request(get_logger(__name__), "yfinance", "forex_data")
    async def _collect_pair_data(self, pair: str):
        """Collect data for a single forex pair."""
        try:
            # Check cache first
            cached_data = await self.cache_manager.get_cached_forex_data(pair)
            if cached_data:
                cache_time = datetime.fromisoformat(cached_data.get("timestamp", ""))
                if datetime.now() - cache_time < timedelta(minutes=1):
                    return

            # Fetch fresh data
            data = await self._fetch_forex_data(pair)
            if data:
                # Save to database
                await self.db_manager.save_forex_data(data)

                # Cache the data
                await self.cache_manager.cache_forex_data(pair, data)

                self.logger.debug(
                    f"Collected forex data for {pair}: {data.get('rate', 'N/A')}"
                )

        except Exception as e:
            self.logger.error(f"Error collecting data for {pair}: {e}")

    async def _fetch_forex_data(self, pair: str) -> Optional[Dict[str, Any]]:
        """Fetch forex data from multiple sources."""
        sources = [
            self._fetch_from_yfinance,
            self._fetch_from_alpha_vantage,
            self._fetch_from_fixer,
        ]

        for source_func in sources:
            try:
                data = await source_func(pair)
                if data:
                    return data
            except Exception as e:
                self.logger.debug(
                    f"Source {source_func.__name__} failed for {pair}: {e}"
                )
                continue

        return None

    @sleep_and_retry
    @limits(calls=100, period=60)
    async def _fetch_from_yfinance(self, pair: str) -> Optional[Dict[str, Any]]:
        """Fetch forex data from Yahoo Finance."""
        try:
            ticker = yf.Ticker(pair)
            hist = ticker.history(period="1d", interval="1m")

            if hist.empty:
                return None

            latest = hist.iloc[-1]
            info = ticker.info

            # Convert back to readable pair format
            base_quote = pair.replace("=X", "")
            if len(base_quote) == 6:
                base = base_quote[:3]
                quote = base_quote[3:]
                pair_name = f"{base}/{quote}"
            else:
                pair_name = pair

            data = {
                "pair": pair_name,
                "symbol": pair,
                "timestamp": datetime.now(),
                "rate": float(latest["Close"]),
                "bid": float(latest["Low"]),
                "ask": float(latest["High"]),
                "open": float(latest["Open"]),
                "high": float(latest["High"]),
                "low": float(latest["Low"]),
                "volume": int(latest["Volume"]) if latest["Volume"] > 0 else 0,
                "change": 0,  # Calculate from previous close
                "change_percent": 0,
                "source": "yfinance",
            }

            return data

        except Exception as e:
            self.logger.error(f"Error fetching from Yahoo Finance for {pair}: {e}")
            return None

    @sleep_and_retry
    @limits(calls=5, period=60)
    async def _fetch_from_alpha_vantage(self, pair: str) -> Optional[Dict[str, Any]]:
        """Fetch forex data from Alpha Vantage."""
        if not self.alpha_vantage_key:
            return None

        try:
            # Convert yfinance format to Alpha Vantage format
            if pair.endswith("=X"):
                base_quote = pair.replace("=X", "")
                if len(base_quote) == 6:
                    from_symbol = base_quote[:3]
                    to_symbol = base_quote[3:]
                else:
                    return None
            else:
                return None

            url = "https://www.alphavantage.co/query"
            params = {
                "function": "CURRENCY_EXCHANGE_RATE",
                "from_currency": from_symbol,
                "to_currency": to_symbol,
                "apikey": self.alpha_vantage_key,
            }

            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()

                    if "Realtime Currency Exchange Rate" in data:
                        rate_data = data["Realtime Currency Exchange Rate"]

                        return {
                            "pair": f"{from_symbol}/{to_symbol}",
                            "symbol": pair,
                            "timestamp": datetime.now(),
                            "rate": float(rate_data.get("5. Exchange Rate", 0)),
                            "bid": float(rate_data.get("8. Bid Price", 0)),
                            "ask": float(rate_data.get("9. Ask Price", 0)),
                            "open": (
                                float(rate_data.get("2. From_Currency Name", 0))
                                if rate_data.get("2. From_Currency Name", "")
                                .replace(".", "")
                                .isdigit()
                                else 0
                            ),
                            "high": float(rate_data.get("5. Exchange Rate", 0)),
                            "low": float(rate_data.get("5. Exchange Rate", 0)),
                            "volume": 0,
                            "change": 0,
                            "change_percent": 0,
                            "source": "alpha_vantage",
                        }

                return None

        except Exception as e:
            self.logger.error(f"Error fetching from Alpha Vantage for {pair}: {e}")
            return None

    @sleep_and_retry
    @limits(calls=10, period=60)
    async def _fetch_from_fixer(self, pair: str) -> Optional[Dict[str, Any]]:
        """Fetch forex data from Fixer.io."""
        if not self.fixer_key:
            return None

        try:
            # Convert yfinance format to base/quote
            if pair.endswith("=X"):
                base_quote = pair.replace("=X", "")
                if len(base_quote) == 6:
                    base = base_quote[:3]
                    quote = base_quote[3:]
                else:
                    return None
            else:
                return None

            url = f"http://data.fixer.io/api/latest"
            params = {"access_key": self.fixer_key, "base": base, "symbols": quote}

            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()

                    if data.get("success") and quote in data.get("rates", {}):
                        rate = data["rates"][quote]

                        return {
                            "pair": f"{base}/{quote}",
                            "symbol": pair,
                            "timestamp": datetime.now(),
                            "rate": float(rate),
                            "bid": float(rate) * 0.9999,  # Approximate bid
                            "ask": float(rate) * 1.0001,  # Approximate ask
                            "open": float(rate),
                            "high": float(rate),
                            "low": float(rate),
                            "volume": 0,
                            "change": 0,
                            "change_percent": 0,
                            "source": "fixer",
                        }

                return None

        except Exception as e:
            self.logger.error(f"Error fetching from Fixer for {pair}: {e}")
            return None

    async def get_latest_data(self, pair: str) -> Optional[Dict[str, Any]]:
        """Get latest data for a forex pair."""
        try:
            cached_data = await self.cache_manager.get_cached_forex_data(pair)
            if cached_data:
                return cached_data

            # Fallback to database
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=1)

            data_list = await self.db_manager.get_forex_data(pair, start_time, end_time)
            if data_list:
                return data_list[-1]

            return None

        except Exception as e:
            self.logger.error(f"Error getting latest data for {pair}: {e}")
            return None

    async def get_historical_data(
        self, pair: str, start_date: datetime, end_date: datetime
    ) -> List[Dict[str, Any]]:
        """Get historical data for a forex pair."""
        try:
            return await self.db_manager.get_forex_data(pair, start_date, end_date)
        except Exception as e:
            self.logger.error(f"Error getting historical data for {pair}: {e}")
            return []

    def is_healthy(self) -> bool:
        """Check if the collector is healthy."""
        return self.running and self.session is not None

    async def get_major_pairs(self) -> List[str]:
        """Get list of major forex pairs."""
        return self.forex_pairs[:7]  # Major pairs

    async def get_minor_pairs(self) -> List[str]:
        """Get list of minor forex pairs."""
        return self.forex_pairs[7:19]  # Cross pairs

    async def get_exotic_pairs(self) -> List[str]:
        """Get list of exotic forex pairs."""
        return self.forex_pairs[19:]  # Exotic pairs

    async def get_all_pairs(self) -> List[str]:
        """Get all tracked forex pairs."""
        return self.forex_pairs.copy()
