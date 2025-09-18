"""
Stock data collector for real-time market data from multiple sources.
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


class StockDataCollector:
    """Collects real-time stock data from multiple sources."""

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
        self.finnhub_key = config.api_keys.finnhub

        # Watchlist symbols (can be configured)
        self.watchlist = [
            "AAPL",
            "MSFT",
            "GOOGL",
            "AMZN",
            "TSLA",
            "META",
            "NVDA",
            "NFLX",
            "JPM",
            "JNJ",
            "V",
            "PG",
            "UNH",
            "HD",
            "MA",
            "DIS",
            "PYPL",
            "BAC",
            "ADBE",
            "CRM",
            "NKE",
            "KO",
            "PEP",
            "TMO",
            "ABT",
            "WMT",
            "MRK",
            "PFE",
            "TXN",
            "AVGO",
            "COST",
            "ACN",
            "DHR",
            "LLY",
            "VZ",
            "CMCSA",
        ]

        # Market hours by timezone
        self.market_hours = {
            "us": {"open": "09:30", "close": "16:00", "timezone": "America/New_York"},
            "europe": {"open": "08:00", "close": "16:30", "timezone": "Europe/London"},
            "asia": {"open": "09:00", "close": "15:00", "timezone": "Asia/Tokyo"},
        }

    async def start(self):
        """Start the stock data collection process."""
        self.running = True
        self.logger.info("Starting stock data collector")

        # Create aiohttp session
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(timeout=timeout)

        try:
            while self.running:
                await self._collect_data()
                await asyncio.sleep(self.config.data_collection.stock_data_interval)

        except asyncio.CancelledError:
            self.logger.info("Stock data collector cancelled")
        except Exception as e:
            self.logger.error(f"Error in stock data collector: {e}")
        finally:
            if self.session:
                await self.session.close()

    async def stop(self):
        """Stop the stock data collection process."""
        self.running = False
        self.logger.info("Stopping stock data collector")

    async def _collect_data(self):
        """Collect stock data from all sources."""
        try:
            # Check which markets are currently open
            active_markets = self._get_active_markets()

            if not active_markets:
                self.logger.debug("No markets currently open")
                return

            # Collect data for each active market
            for market in active_markets:
                await self._collect_market_data(market)

        except Exception as e:
            self.logger.error(f"Error collecting stock data: {e}")

    def _get_active_markets(self) -> List[str]:
        """Get list of currently active markets."""
        active_markets = []
        now = datetime.now(pytz.UTC)

        for market, hours in self.market_hours.items():
            market_tz = pytz.timezone(hours["timezone"])
            market_time = now.astimezone(market_tz)

            # Check if market is open (simplified - doesn't account for holidays)
            if self._is_market_open(market_time, hours):
                active_markets.append(market)

        return active_markets

    def _is_market_open(self, market_time: datetime, hours: Dict[str, str]) -> bool:
        """Check if market is open at given time."""
        # Simple check - can be enhanced with holiday calendars
        if market_time.weekday() >= 5:  # Weekend
            return False

        open_time = datetime.strptime(hours["open"], "%H:%M").time()
        close_time = datetime.strptime(hours["close"], "%H:%M").time()

        return open_time <= market_time.time() <= close_time

    async def _collect_market_data(self, market: str):
        """Collect data for a specific market."""
        try:
            # Get symbols for this market
            symbols = self._get_market_symbols(market)

            # Collect data in batches
            batch_size = 10
            for i in range(0, len(symbols), batch_size):
                batch = symbols[i : i + batch_size]
                await self._collect_batch_data(batch, market)
                await asyncio.sleep(1)  # Rate limiting

        except Exception as e:
            self.logger.error(f"Error collecting data for market {market}: {e}")

    def _get_market_symbols(self, market: str) -> List[str]:
        """Get symbols for a specific market."""
        # This is a simplified version - in practice, you'd have a database
        # of symbols organized by market/exchange
        if market == "us":
            return self.watchlist[:20]  # Top 20 US stocks
        elif market == "europe":
            return ["ASML", "NOVO-B.CO", "SAP.DE", "NESN.SW", "ROCHE.SW"]
        elif market == "asia":
            return ["005930.KS", "000660.KS", "7203.T", "6758.T", "0700.HK"]
        else:
            return []

    async def _collect_batch_data(self, symbols: List[str], market: str):
        """Collect data for a batch of symbols."""
        tasks = []
        for symbol in symbols:
            task = asyncio.create_task(self._collect_symbol_data(symbol, market))
            tasks.append(task)

        # Wait for all tasks to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.error(f"Error collecting data for {symbols[i]}: {result}")

    @log_api_request(get_logger(__name__), "yfinance", "stock_data")
    async def _collect_symbol_data(self, symbol: str, market: str):
        """Collect data for a single symbol."""
        try:
            # Check cache first
            cached_data = await self.cache_manager.get_cached_stock_data(symbol)
            if cached_data:
                # Use cached data if it's recent enough
                cache_time = datetime.fromisoformat(cached_data.get("timestamp", ""))
                if datetime.now() - cache_time < timedelta(minutes=5):
                    return

            # Fetch fresh data
            data = await self._fetch_stock_data(symbol)
            if data:
                # Save to database
                await self.db_manager.save_stock_data(data)

                # Cache the data
                await self.cache_manager.cache_stock_data(symbol, data)

                self.logger.debug(
                    f"Collected data for {symbol}: {data.get('close', 'N/A')}"
                )

        except Exception as e:
            self.logger.error(f"Error collecting data for {symbol}: {e}")

    async def _fetch_stock_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Fetch stock data from multiple sources."""
        # Try multiple data sources
        sources = [
            self._fetch_from_yfinance,
            self._fetch_from_alpha_vantage,
            self._fetch_from_polygon,
        ]

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
    @limits(calls=100, period=60)  # Rate limiting
    async def _fetch_from_yfinance(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Fetch data from Yahoo Finance."""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info

            # Get latest price data
            hist = ticker.history(period="1d", interval="1m")
            if hist.empty:
                return None

            latest = hist.iloc[-1]

            data = {
                "symbol": symbol,
                "timestamp": datetime.now(),
                "open": float(latest["Open"]),
                "high": float(latest["High"]),
                "low": float(latest["Low"]),
                "close": float(latest["Close"]),
                "volume": int(latest["Volume"]),
                "exchange": info.get("exchange", ""),
                "currency": info.get("currency", "USD"),
                "market_cap": info.get("marketCap"),
                "pe_ratio": info.get("trailingPE"),
                "dividend_yield": info.get("dividendYield"),
                "source": "yfinance",
            }

            return data

        except Exception as e:
            self.logger.error(f"Error fetching from Yahoo Finance for {symbol}: {e}")
            return None

    @sleep_and_retry
    @limits(calls=5, period=60)  # Alpha Vantage rate limit
    async def _fetch_from_alpha_vantage(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Fetch data from Alpha Vantage."""
        if not self.alpha_vantage_key:
            return None

        try:
            url = f"https://www.alphavantage.co/query"
            params = {
                "function": "GLOBAL_QUOTE",
                "symbol": symbol,
                "apikey": self.alpha_vantage_key,
            }

            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()

                    if "Global Quote" in data:
                        quote = data["Global Quote"]

                        return {
                            "symbol": symbol,
                            "timestamp": datetime.now(),
                            "open": float(quote.get("02. open", 0)),
                            "high": float(quote.get("03. high", 0)),
                            "low": float(quote.get("04. low", 0)),
                            "close": float(quote.get("05. price", 0)),
                            "volume": int(quote.get("06. volume", 0)),
                            "exchange": "",
                            "currency": "USD",
                            "source": "alpha_vantage",
                        }

                return None

        except Exception as e:
            self.logger.error(f"Error fetching from Alpha Vantage for {symbol}: {e}")
            return None

    @sleep_and_retry
    @limits(calls=5, period=60)  # Polygon rate limit
    async def _fetch_from_polygon(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Fetch data from Polygon.io."""
        if not self.polygon_key:
            return None

        try:
            url = f"https://api.polygon.io/v2/aggs/ticker/{symbol}/prev"
            params = {"apikey": self.polygon_key}

            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()

                    if "results" in data and data["results"]:
                        result = data["results"][0]

                        return {
                            "symbol": symbol,
                            "timestamp": datetime.fromtimestamp(result["t"] / 1000),
                            "open": float(result["o"]),
                            "high": float(result["h"]),
                            "low": float(result["l"]),
                            "close": float(result["c"]),
                            "volume": int(result["v"]),
                            "exchange": "",
                            "currency": "USD",
                            "source": "polygon",
                        }

                return None

        except Exception as e:
            self.logger.error(f"Error fetching from Polygon for {symbol}: {e}")
            return None

    async def get_latest_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get latest data for a symbol (from cache or database)."""
        try:
            # Try cache first
            cached_data = await self.cache_manager.get_cached_stock_data(symbol)
            if cached_data:
                return cached_data

            # Fallback to database
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=1)

            data_list = await self.db_manager.get_stock_data(
                symbol, start_time, end_time
            )
            if data_list:
                return data_list[-1]  # Return most recent

            return None

        except Exception as e:
            self.logger.error(f"Error getting latest data for {symbol}: {e}")
            return None

    async def get_historical_data(
        self, symbol: str, start_date: datetime, end_date: datetime
    ) -> List[Dict[str, Any]]:
        """Get historical data for a symbol."""
        try:
            return await self.db_manager.get_stock_data(symbol, start_date, end_date)
        except Exception as e:
            self.logger.error(f"Error getting historical data for {symbol}: {e}")
            return []

    def is_healthy(self) -> bool:
        """Check if the collector is healthy."""
        return self.running and self.session is not None

    async def add_to_watchlist(self, symbol: str):
        """Add a symbol to the watchlist."""
        if symbol not in self.watchlist:
            self.watchlist.append(symbol)
            self.logger.info(f"Added {symbol} to watchlist")

    async def remove_from_watchlist(self, symbol: str):
        """Remove a symbol from the watchlist."""
        if symbol in self.watchlist:
            self.watchlist.remove(symbol)
            self.logger.info(f"Removed {symbol} from watchlist")

    async def get_watchlist(self) -> List[str]:
        """Get current watchlist."""
        return self.watchlist.copy()
