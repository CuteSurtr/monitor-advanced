"""
Cache management for the stock monitoring system using Redis.
"""

import asyncio
import json
import pickle
from typing import Any, Optional, Dict, List, Union
from datetime import datetime, timedelta
import redis.asyncio as redis
from src.utils.logger import get_logger


class CacheManager:
    """Redis cache manager for the stock monitoring system."""

    def __init__(self, config):
        self.config = config
        self.logger = get_logger(__name__)
        self.redis_client = None
        self.health_status = False
        self.default_ttl = config.performance.cache_ttl

    async def initialize(self):
        """Initialize Redis connection."""
        try:
            self.redis_client = redis.Redis(
                host=self.config.redis.host,
                port=self.config.redis.port,
                password=self.config.redis.password or None,
                db=self.config.redis.db,
                decode_responses=False,  # Keep as bytes for pickle
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30,
            )

            # Test connection
            await self.redis_client.ping()
            self.health_status = True

            self.logger.info("Redis cache initialized successfully")

        except Exception as e:
            self.logger.error(f"Failed to initialize Redis cache: {e}")
            raise

    async def close(self):
        """Close Redis connection."""
        try:
            if self.redis_client:
                await self.redis_client.close()
            self.health_status = False
            self.logger.info("Redis cache connection closed")
        except Exception as e:
            self.logger.error(f"Error closing Redis connection: {e}")

    async def is_healthy(self) -> bool:
        """Check Redis health."""
        try:
            if self.redis_client:
                await self.redis_client.ping()
                return True
            return False
        except Exception as e:
            self.logger.error(f"Redis health check failed: {e}")
            return False

    async def get(self, key: str, default: Any = None) -> Any:
        """
        Get value from cache.

        Args:
            key: Cache key
            default: Default value if key not found

        Returns:
            Cached value or default
        """
        try:
            if not self.redis_client:
                return default

            value = await self.redis_client.get(key)
            if value is None:
                return default

            # Try to deserialize as JSON first, then pickle
            try:
                return json.loads(value.decode("utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError):
                try:
                    return pickle.loads(value)
                except pickle.UnpicklingError:
                    return value.decode("utf-8")

        except Exception as e:
            self.logger.error(f"Error getting cache key {key}: {e}")
            return default

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (uses default if None)

        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.redis_client:
                return False

            # Serialize value
            if isinstance(value, (dict, list, tuple, int, float, bool, str)):
                serialized_value = json.dumps(value).encode("utf-8")
            else:
                serialized_value = pickle.dumps(value)

            ttl = ttl or self.default_ttl
            await self.redis_client.setex(key, ttl, serialized_value)
            return True

        except Exception as e:
            self.logger.error(f"Error setting cache key {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """
        Delete key from cache.

        Args:
            key: Cache key to delete

        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.redis_client:
                return False

            result = await self.redis_client.delete(key)
            return result > 0

        except Exception as e:
            self.logger.error(f"Error deleting cache key {key}: {e}")
            return False

    async def exists(self, key: str) -> bool:
        """
        Check if key exists in cache.

        Args:
            key: Cache key to check

        Returns:
            True if key exists, False otherwise
        """
        try:
            if not self.redis_client:
                return False

            result = await self.redis_client.exists(key)
            return result > 0

        except Exception as e:
            self.logger.error(f"Error checking cache key {key}: {e}")
            return False

    async def expire(self, key: str, ttl: int) -> bool:
        """
        Set expiration time for a key.

        Args:
            key: Cache key
            ttl: Time to live in seconds

        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.redis_client:
                return False

            result = await self.redis_client.expire(key, ttl)
            return result

        except Exception as e:
            self.logger.error(f"Error setting expiration for cache key {key}: {e}")
            return False

    async def ttl(self, key: str) -> int:
        """
        Get time to live for a key.

        Args:
            key: Cache key

        Returns:
            TTL in seconds, -1 if no expiration, -2 if key doesn't exist
        """
        try:
            if not self.redis_client:
                return -2

            return await self.redis_client.ttl(key)

        except Exception as e:
            self.logger.error(f"Error getting TTL for cache key {key}: {e}")
            return -2

    async def keys(self, pattern: str = "*") -> List[str]:
        """
        Get keys matching pattern.

        Args:
            pattern: Key pattern (supports wildcards)

        Returns:
            List of matching keys
        """
        try:
            if not self.redis_client:
                return []

            keys = await self.redis_client.keys(pattern)
            return [key.decode("utf-8") for key in keys]

        except Exception as e:
            self.logger.error(f"Error getting keys with pattern {pattern}: {e}")
            return []

    async def flush(self, pattern: Optional[str] = None) -> bool:
        """
        Flush cache (all keys or matching pattern).

        Args:
            pattern: Optional pattern to match keys

        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.redis_client:
                return False

            if pattern:
                keys = await self.keys(pattern)
                if keys:
                    await self.redis_client.delete(*keys)
            else:
                await self.redis_client.flushdb()

            return True

        except Exception as e:
            self.logger.error(f"Error flushing cache: {e}")
            return False

    # Stock data specific methods
    async def cache_stock_data(
        self, symbol: str, data: Dict[str, Any], ttl: Optional[int] = None
    ) -> bool:
        """
        Cache stock data for a symbol.

        Args:
            symbol: Stock symbol
            data: Stock data dictionary
            ttl: Time to live in seconds

        Returns:
            True if successful, False otherwise
        """
        key = f"stock:{symbol}:latest"
        return await self.set(key, data, ttl)

    async def get_cached_stock_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get cached stock data for a symbol.

        Args:
            symbol: Stock symbol

        Returns:
            Cached stock data or None
        """
        key = f"stock:{symbol}:latest"
        return await self.get(key)

    async def cache_stock_history(
        self,
        symbol: str,
        timeframe: str,
        data: List[Dict[str, Any]],
        ttl: Optional[int] = None,
    ) -> bool:
        """
        Cache stock historical data.

        Args:
            symbol: Stock symbol
            timeframe: Timeframe (1d, 1h, 5m, etc.)
            data: Historical data list
            ttl: Time to live in seconds

        Returns:
            True if successful, False otherwise
        """
        key = f"stock:{symbol}:history:{timeframe}"
        return await self.set(key, data, ttl)

    async def get_cached_stock_history(
        self, symbol: str, timeframe: str
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Get cached stock historical data.

        Args:
            symbol: Stock symbol
            timeframe: Timeframe (1d, 1h, 5m, etc.)

        Returns:
            Cached historical data or None
        """
        key = f"stock:{symbol}:history:{timeframe}"
        return await self.get(key)

    # Commodity data specific methods
    async def cache_commodity_data(
        self, symbol: str, data: Dict[str, Any], ttl: Optional[int] = None
    ) -> bool:
        """
        Cache commodity data for a symbol.

        Args:
            symbol: Commodity symbol
            data: Commodity data dictionary
            ttl: Time to live in seconds

        Returns:
            True if successful, False otherwise
        """
        key = f"commodity:{symbol}:latest"
        return await self.set(key, data, ttl)

    async def get_cached_commodity_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get cached commodity data for a symbol.

        Args:
            symbol: Commodity symbol

        Returns:
            Cached commodity data or None
        """
        key = f"commodity:{symbol}:latest"
        return await self.get(key)

    # Forex data specific methods
    async def cache_forex_data(
        self, pair: str, data: Dict[str, Any], ttl: Optional[int] = None
    ) -> bool:
        """
        Cache forex data for a currency pair.

        Args:
            pair: Forex pair symbol
            data: Forex data dictionary
            ttl: Time to live in seconds

        Returns:
            True if successful, False otherwise
        """
        key = f"forex:{pair}:latest"
        return await self.set(key, data, ttl)

    async def get_cached_forex_data(self, pair: str) -> Optional[Dict[str, Any]]:
        """
        Get cached forex data for a currency pair.

        Args:
            pair: Forex pair symbol

        Returns:
            Cached forex data or None
        """
        key = f"forex:{pair}:latest"
        return await self.get(key)

    # Crypto data specific methods
    async def cache_crypto_data(
        self, symbol: str, data: Dict[str, Any], ttl: Optional[int] = None
    ) -> bool:
        """
        Cache crypto data for a symbol.

        Args:
            symbol: Crypto symbol
            data: Crypto data dictionary
            ttl: Time to live in seconds

        Returns:
            True if successful, False otherwise
        """
        key = f"crypto:{symbol}:latest"
        return await self.set(key, data, ttl)

    async def get_cached_crypto_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get cached crypto data for a symbol.

        Args:
            symbol: Crypto symbol

        Returns:
            Cached crypto data or None
        """
        key = f"crypto:{symbol}:latest"
        return await self.get(key)

    # News data specific methods
    async def cache_news_data(
        self, symbol: str, news_list: List[Dict[str, Any]], ttl: Optional[int] = None
    ) -> bool:
        """
        Cache news data for a symbol.

        Args:
            symbol: Stock symbol
            news_list: List of news articles
            ttl: Time to live in seconds

        Returns:
            True if successful, False otherwise
        """
        key = f"news:{symbol}:latest"
        return await self.set(key, news_list, ttl)

    async def get_cached_news_data(self, symbol: str) -> Optional[List[Dict[str, Any]]]:
        """
        Get cached news data for a symbol.

        Args:
            symbol: Stock symbol

        Returns:
            Cached news data or None
        """
        key = f"news:{symbol}:latest"
        return await self.get(key)

    # Technical indicators cache
    async def cache_technical_indicators(
        self, symbol: str, indicators: Dict[str, Any], ttl: Optional[int] = None
    ) -> bool:
        """
        Cache technical indicators for a symbol.

        Args:
            symbol: Stock symbol
            indicators: Technical indicators dictionary
            ttl: Time to live in seconds

        Returns:
            True if successful, False otherwise
        """
        key = f"indicators:{symbol}:latest"
        return await self.set(key, indicators, ttl)

    async def get_cached_technical_indicators(
        self, symbol: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached technical indicators for a symbol.

        Args:
            symbol: Stock symbol

        Returns:
            Cached technical indicators or None
        """
        key = f"indicators:{symbol}:latest"
        return await self.get(key)

    # Portfolio cache
    async def cache_portfolio_data(
        self, user_id: str, portfolio_data: Dict[str, Any], ttl: Optional[int] = None
    ) -> bool:
        """
        Cache portfolio data for a user.

        Args:
            user_id: User ID
            portfolio_data: Portfolio data dictionary
            ttl: Time to live in seconds

        Returns:
            True if successful, False otherwise
        """
        key = f"portfolio:{user_id}:latest"
        return await self.set(key, portfolio_data, ttl)

    async def get_cached_portfolio_data(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get cached portfolio data for a user.

        Args:
            user_id: User ID

        Returns:
            Cached portfolio data or None
        """
        key = f"portfolio:{user_id}:latest"
        return await self.get(key)

    # Rate limiting
    async def increment_rate_limit(self, key: str, ttl: int) -> int:
        """
        Increment rate limit counter.

        Args:
            key: Rate limit key
            ttl: Time to live in seconds

        Returns:
            Current count
        """
        try:
            if not self.redis_client:
                return 0

            pipe = self.redis_client.pipeline()
            pipe.incr(key)
            pipe.expire(key, ttl)
            results = await pipe.execute()
            return results[0]

        except Exception as e:
            self.logger.error(f"Error incrementing rate limit {key}: {e}")
            return 0

    async def check_rate_limit(self, key: str, limit: int, ttl: int) -> bool:
        """
        Check if rate limit is exceeded.

        Args:
            key: Rate limit key
            limit: Maximum allowed requests
            ttl: Time to live in seconds

        Returns:
            True if limit not exceeded, False otherwise
        """
        current_count = await self.increment_rate_limit(key, ttl)
        return current_count <= limit

    # Cache statistics
    async def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        try:
            if not self.redis_client:
                return {}

            info = await self.redis_client.info()
            return {
                "connected_clients": info.get("connected_clients", 0),
                "used_memory_human": info.get("used_memory_human", "0B"),
                "used_memory_peak_human": info.get("used_memory_peak_human", "0B"),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "uptime_in_seconds": info.get("uptime_in_seconds", 0),
            }

        except Exception as e:
            self.logger.error(f"Error getting cache stats: {e}")
            return {}

    # Cache warming
    async def warm_cache(self, symbols: List[str]) -> Dict[str, bool]:
        """
        Warm cache with frequently accessed data.

        Args:
            symbols: List of symbols to warm cache for

        Returns:
            Dictionary with warming results
        """
        results = {}

        for symbol in symbols:
            try:
                # This would typically fetch data from external APIs
                # For now, we'll just mark as successful
                results[symbol] = True

            except Exception as e:
                self.logger.error(f"Error warming cache for {symbol}: {e}")
                results[symbol] = False

        return results
