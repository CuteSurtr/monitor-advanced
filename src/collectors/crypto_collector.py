"""
Cryptocurrency data collector for real-time crypto prices from multiple sources.
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


class CryptoDataCollector:
    """Collects real-time cryptocurrency data from multiple sources."""

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
        self.coinmarketcap_key = getattr(config.api_keys, "coinmarketcap", None)
        self.coingecko_key = getattr(config.api_keys, "coingecko", None)
        self.binance_key = getattr(config.api_keys, "binance", None)

        # Top cryptocurrencies by market cap
        self.crypto_symbols = [
            "BTC-USD",
            "ETH-USD",
            "BNB-USD",
            "XRP-USD",
            "ADA-USD",
            "SOL-USD",
            "DOGE-USD",
            "DOT-USD",
            "AVAX-USD",
            "SHIB-USD",
            "LTC-USD",
            "TRX-USD",
            "UNI-USD",
            "LINK-USD",
            "XLM-USD",
            "BCH-USD",
            "NEAR-USD",
            "ALGO-USD",
            "XMR-USD",
            "VET-USD",
            "FIL-USD",
            "ICP-USD",
            "FLOW-USD",
            "APE-USD",
            "MANA-USD",
            "SAND-USD",
            "CRO-USD",
            "HBAR-USD",
            "ETC-USD",
            "LRC-USD",
            "ZEC-USD",
            "KCS-USD",
        ]

        # DeFi tokens
        self.defi_tokens = [
            "AAVE-USD",
            "COMP-USD",
            "MKR-USD",
            "SNX-USD",
            "YFI-USD",
            "SUSHI-USD",
            "CRV-USD",
            "BAL-USD",
            "REN-USD",
            "KNC-USD",
            "UMA-USD",
            "BADGER-USD",
        ]

        # Stablecoins
        self.stablecoins = [
            "USDT-USD",
            "USDC-USD",
            "BUSD-USD",
            "DAI-USD",
            "TUSD-USD",
            "USDP-USD",
        ]

        # All symbols combined
        self.all_symbols = self.crypto_symbols + self.defi_tokens + self.stablecoins

        # Crypto markets are 24/7
        self.is_24_7 = True

    async def start(self):
        """Start the crypto data collection process."""
        self.running = True
        self.logger.info("Starting crypto data collector")

        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(timeout=timeout)

        try:
            while self.running:
                await self._collect_data()
                await asyncio.sleep(
                    self.config.data_collection.crypto_data_interval or 30
                )

        except asyncio.CancelledError:
            self.logger.info("Crypto data collector cancelled")
        except Exception as e:
            self.logger.error(f"Error in crypto data collector: {e}")
        finally:
            if self.session:
                await self.session.close()

    async def stop(self):
        """Stop the crypto data collection process."""
        self.running = False
        self.logger.info("Stopping crypto data collector")

    async def _collect_data(self):
        """Collect crypto data from all sources."""
        try:
            # Crypto markets are 24/7, always collect
            batch_size = 15  # Larger batches for crypto
            for i in range(0, len(self.all_symbols), batch_size):
                batch = self.all_symbols[i : i + batch_size]
                await self._collect_batch_data(batch)
                await asyncio.sleep(1)  # Shorter delay for crypto

        except Exception as e:
            self.logger.error(f"Error collecting crypto data: {e}")

    async def _collect_batch_data(self, symbols: List[str]):
        """Collect data for a batch of crypto symbols."""
        tasks = []
        for symbol in symbols:
            task = asyncio.create_task(self._collect_symbol_data(symbol))
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.error(f"Error collecting data for {symbols[i]}: {result}")

    @log_api_request(get_logger(__name__), "yfinance", "crypto_data")
    async def _collect_symbol_data(self, symbol: str):
        """Collect data for a single crypto symbol."""
        try:
            # Check cache first
            cached_data = await self.cache_manager.get_cached_crypto_data(symbol)
            if cached_data:
                cache_time = datetime.fromisoformat(cached_data.get("timestamp", ""))
                if datetime.now() - cache_time < timedelta(minutes=1):
                    return

            # Fetch fresh data
            data = await self._fetch_crypto_data(symbol)
            if data:
                # Save to database
                await self.db_manager.save_crypto_data(data)

                # Cache the data
                await self.cache_manager.cache_crypto_data(symbol, data)

                self.logger.debug(
                    f"Collected crypto data for {symbol}: ${data.get('price', 'N/A')}"
                )

        except Exception as e:
            self.logger.error(f"Error collecting data for {symbol}: {e}")

    async def _fetch_crypto_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Fetch crypto data from multiple sources."""
        sources = [
            self._fetch_from_yfinance,
            self._fetch_from_coingecko,
            self._fetch_from_binance,
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
    @limits(calls=100, period=60)
    async def _fetch_from_yfinance(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Fetch crypto data from Yahoo Finance."""
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="1d", interval="1m")

            if hist.empty:
                return None

            latest = hist.iloc[-1]
            info = ticker.info

            # Extract crypto info
            crypto_name = symbol.split("-")[0]  # BTC from BTC-USD

            data = {
                "symbol": symbol,
                "crypto": crypto_name,
                "timestamp": datetime.now(),
                "price": float(latest["Close"]),
                "open": float(latest["Open"]),
                "high": float(latest["High"]),
                "low": float(latest["Low"]),
                "volume": int(latest["Volume"]) if latest["Volume"] > 0 else 0,
                "market_cap": info.get("marketCap"),
                "currency": "USD",
                "change_24h": 0,  # Calculate from previous data
                "change_24h_percent": 0,
                "volume_24h": int(latest["Volume"]) if latest["Volume"] > 0 else 0,
                "source": "yfinance",
            }

            return data

        except Exception as e:
            self.logger.error(f"Error fetching from Yahoo Finance for {symbol}: {e}")
            return None

    @sleep_and_retry
    @limits(calls=50, period=60)
    async def _fetch_from_coingecko(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Fetch crypto data from CoinGecko."""
        try:
            # Convert symbol format (BTC-USD -> bitcoin)
            crypto_id_map = {
                "BTC-USD": "bitcoin",
                "ETH-USD": "ethereum",
                "BNB-USD": "binancecoin",
                "XRP-USD": "ripple",
                "ADA-USD": "cardano",
                "SOL-USD": "solana",
                "DOGE-USD": "dogecoin",
                "DOT-USD": "polkadot",
                "AVAX-USD": "avalanche-2",
                "SHIB-USD": "shiba-inu",
                "LTC-USD": "litecoin",
                "TRX-USD": "tron",
                "UNI-USD": "uniswap",
                "LINK-USD": "chainlink",
            }

            crypto_id = crypto_id_map.get(symbol)
            if not crypto_id:
                return None

            url = f"https://api.coingecko.com/api/v3/simple/price"
            params = {
                "ids": crypto_id,
                "vs_currencies": "usd",
                "include_market_cap": "true",
                "include_24hr_vol": "true",
                "include_24hr_change": "true",
            }

            headers = {}
            if self.coingecko_key:
                headers["X-CG-Pro-API-Key"] = self.coingecko_key

            async with self.session.get(
                url, params=params, headers=headers
            ) as response:
                if response.status == 200:
                    data = await response.json()

                    if crypto_id in data:
                        crypto_data = data[crypto_id]
                        crypto_name = symbol.split("-")[0]

                        return {
                            "symbol": symbol,
                            "crypto": crypto_name,
                            "timestamp": datetime.now(),
                            "price": float(crypto_data.get("usd", 0)),
                            "open": float(
                                crypto_data.get("usd", 0)
                            ),  # CoinGecko doesn't provide OHLC in simple API
                            "high": float(crypto_data.get("usd", 0)),
                            "low": float(crypto_data.get("usd", 0)),
                            "volume": 0,
                            "market_cap": int(crypto_data.get("usd_market_cap", 0)),
                            "currency": "USD",
                            "change_24h": float(crypto_data.get("usd_24h_change", 0)),
                            "change_24h_percent": float(
                                crypto_data.get("usd_24h_change", 0)
                            ),
                            "volume_24h": int(crypto_data.get("usd_24h_vol", 0)),
                            "source": "coingecko",
                        }

                return None

        except Exception as e:
            self.logger.error(f"Error fetching from CoinGecko for {symbol}: {e}")
            return None

    @sleep_and_retry
    @limits(calls=10, period=60)
    async def _fetch_from_binance(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Fetch crypto data from Binance."""
        try:
            # Convert to Binance format (BTC-USD -> BTCUSDT)
            binance_symbol = symbol.replace("-USD", "USDT")

            # Get 24hr ticker statistics
            url = f"https://api.binance.com/api/v3/ticker/24hr"
            params = {"symbol": binance_symbol}

            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    crypto_name = symbol.split("-")[0]

                    return {
                        "symbol": symbol,
                        "crypto": crypto_name,
                        "timestamp": datetime.now(),
                        "price": float(data.get("lastPrice", 0)),
                        "open": float(data.get("openPrice", 0)),
                        "high": float(data.get("highPrice", 0)),
                        "low": float(data.get("lowPrice", 0)),
                        "volume": int(float(data.get("volume", 0))),
                        "market_cap": 0,  # Not available in this endpoint
                        "currency": "USD",
                        "change_24h": float(data.get("priceChange", 0)),
                        "change_24h_percent": float(data.get("priceChangePercent", 0)),
                        "volume_24h": int(float(data.get("quoteVolume", 0))),
                        "source": "binance",
                    }

                return None

        except Exception as e:
            self.logger.error(f"Error fetching from Binance for {symbol}: {e}")
            return None

    async def get_latest_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get latest data for a crypto symbol."""
        try:
            cached_data = await self.cache_manager.get_cached_crypto_data(symbol)
            if cached_data:
                return cached_data

            # Fallback to database
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=1)

            data_list = await self.db_manager.get_crypto_data(
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
        """Get historical data for a crypto symbol."""
        try:
            return await self.db_manager.get_crypto_data(symbol, start_date, end_date)
        except Exception as e:
            self.logger.error(f"Error getting historical data for {symbol}: {e}")
            return []

    async def get_market_overview(self) -> Dict[str, Any]:
        """Get crypto market overview."""
        try:
            url = "https://api.coingecko.com/api/v3/global"
            headers = {}
            if self.coingecko_key:
                headers["X-CG-Pro-API-Key"] = self.coingecko_key

            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    global_data = data.get("data", {})

                    return {
                        "total_market_cap_usd": global_data.get(
                            "total_market_cap", {}
                        ).get("usd", 0),
                        "total_volume_24h_usd": global_data.get("total_volume", {}).get(
                            "usd", 0
                        ),
                        "bitcoin_dominance": global_data.get(
                            "market_cap_percentage", {}
                        ).get("btc", 0),
                        "ethereum_dominance": global_data.get(
                            "market_cap_percentage", {}
                        ).get("eth", 0),
                        "active_cryptocurrencies": global_data.get(
                            "active_cryptocurrencies", 0
                        ),
                        "markets": global_data.get("markets", 0),
                        "timestamp": datetime.now(),
                    }

            return {}

        except Exception as e:
            self.logger.error(f"Error getting market overview: {e}")
            return {}

    def is_healthy(self) -> bool:
        """Check if the collector is healthy."""
        return self.running and self.session is not None

    async def get_top_cryptos(self, limit: int = 20) -> List[str]:
        """Get top cryptocurrencies by market cap."""
        return self.crypto_symbols[:limit]

    async def get_defi_tokens(self) -> List[str]:
        """Get DeFi tokens."""
        return self.defi_tokens.copy()

    async def get_stablecoins(self) -> List[str]:
        """Get stablecoins."""
        return self.stablecoins.copy()

    async def get_all_symbols(self) -> List[str]:
        """Get all tracked crypto symbols."""
        return self.all_symbols.copy()

    async def add_symbol(self, symbol: str):
        """Add a symbol to tracking list."""
        if symbol not in self.all_symbols:
            self.all_symbols.append(symbol)
            self.logger.info(f"Added {symbol} to crypto tracking list")

    async def remove_symbol(self, symbol: str):
        """Remove a symbol from tracking list."""
        if symbol in self.all_symbols:
            self.all_symbols.remove(symbol)
            self.logger.info(f"Removed {symbol} from crypto tracking list")
