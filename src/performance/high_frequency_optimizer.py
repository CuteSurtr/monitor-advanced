"""
High-Frequency Data Processing Optimizer - Sub-second latency optimization for 500+ concurrent streams.
"""

import asyncio
import time
import numpy as np
from typing import Dict, List, Any, Optional, Callable, Coroutine
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import deque, defaultdict
import threading
from concurrent.futures import ThreadPoolExecutor
import multiprocessing as mp
import uvloop
import aioredis
import msgpack
import lz4.frame
import weakref

from src.utils.logger import get_logger


@dataclass
class StreamMetrics:
    """Metrics for a data stream."""

    symbol: str
    message_count: int = 0
    bytes_processed: int = 0
    avg_latency_ms: float = 0.0
    max_latency_ms: float = 0.0
    last_update: datetime = field(default_factory=datetime.now)
    error_count: int = 0


@dataclass
class SystemMetrics:
    """System-wide performance metrics."""

    total_streams: int = 0
    active_connections: int = 0
    messages_per_second: float = 0.0
    cpu_usage: float = 0.0
    memory_usage_mb: float = 0.0
    network_latency_ms: float = 0.0
    cache_hit_rate: float = 0.0
    database_latency_ms: float = 0.0


class CircularBuffer:
    """High-performance circular buffer for streaming data."""

    def __init__(self, size: int):
        self.size = size
        self.buffer = np.empty(size, dtype=object)
        self.head = 0
        self.count = 0
        self.lock = threading.RLock()

    def append(self, item: Any) -> None:
        """Thread-safe append to circular buffer."""
        with self.lock:
            self.buffer[self.head] = item
            self.head = (self.head + 1) % self.size
            if self.count < self.size:
                self.count += 1

    def get_latest(self, n: int = 1) -> List[Any]:
        """Get latest n items from buffer."""
        with self.lock:
            if self.count == 0:
                return []

            items = []
            for i in range(min(n, self.count)):
                idx = (self.head - 1 - i) % self.size
                items.append(self.buffer[idx])

            return items

    def get_all(self) -> List[Any]:
        """Get all items in buffer."""
        return self.get_latest(self.count)


class HighFrequencyOptimizer:
    """Performance optimizer for high-frequency data processing."""

    def __init__(self, config=None):
        self.config = config
        self.logger = get_logger(__name__)

        # Performance settings
        self.max_concurrent_streams = 500
        self.target_latency_ms = 1000  # Sub-second target
        self.buffer_size = 1000
        self.batch_size = 100
        self.flush_interval = 0.1  # 100ms

        # Stream management
        self.active_streams = {}
        self.stream_metrics = {}
        self.message_queues = {}
        self.processing_pools = {}

        # Performance monitoring
        self.system_metrics = SystemMetrics()
        self.performance_history = deque(maxlen=3600)  # 1 hour of metrics

        # Optimization components
        self.redis_pool = None
        self.thread_pool = ThreadPoolExecutor(max_workers=mp.cpu_count() * 2)
        self.event_loop = None

        # Message compression and serialization
        self.use_compression = True
        self.compression_threshold = 1024  # Compress messages > 1KB

        # Caching
        self.local_cache = {}
        self.cache_ttl = 60  # 1 minute
        self.max_cache_size = 10000

    async def initialize(self):
        """Initialize the optimizer with high-performance configurations."""
        try:
            # Set up uvloop for better async performance
            if hasattr(asyncio, "set_event_loop_policy"):
                asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

            self.event_loop = asyncio.get_event_loop()

            # Configure Redis connection pool for high throughput
            self.redis_pool = aioredis.ConnectionPool.from_url(
                "redis://localhost:6379",
                max_connections=100,
                socket_connect_timeout=1,
                socket_timeout=1,
                health_check_interval=30,
            )

            # Optimize garbage collection
            import gc

            gc.set_threshold(700, 10, 10)

            # Initialize monitoring
            asyncio.create_task(self._monitor_performance())

            self.logger.info("High-frequency optimizer initialized")

        except Exception as e:
            self.logger.error(f"Error initializing optimizer: {e}")
            raise

    async def register_stream(
        self, symbol: str, callback: Callable[[Dict], Coroutine]
    ) -> bool:
        """
        Register a new high-frequency data stream.

        Args:
            symbol: Asset symbol
            callback: Async callback function for processing data

        Returns:
            True if registered successfully
        """
        try:
            if len(self.active_streams) >= self.max_concurrent_streams:
                self.logger.warning(
                    f"Maximum concurrent streams ({self.max_concurrent_streams}) reached"
                )
                return False

            # Create stream components
            message_queue = CircularBuffer(self.buffer_size)
            metrics = StreamMetrics(symbol=symbol)

            self.active_streams[symbol] = {
                "callback": callback,
                "queue": message_queue,
                "last_processed": time.time(),
                "batch_buffer": [],
                "processing_task": None,
            }

            self.stream_metrics[symbol] = metrics

            # Start processing task
            task = asyncio.create_task(self._process_stream(symbol))
            self.active_streams[symbol]["processing_task"] = task

            self.system_metrics.total_streams += 1
            self.logger.info(f"Registered stream for {symbol}")

            return True

        except Exception as e:
            self.logger.error(f"Error registering stream {symbol}: {e}")
            return False

    async def unregister_stream(self, symbol: str) -> bool:
        """
        Unregister a data stream.

        Args:
            symbol: Asset symbol

        Returns:
            True if unregistered successfully
        """
        try:
            if symbol in self.active_streams:
                # Cancel processing task
                task = self.active_streams[symbol].get("processing_task")
                if task and not task.done():
                    task.cancel()

                # Clean up
                del self.active_streams[symbol]
                del self.stream_metrics[symbol]

                self.system_metrics.total_streams -= 1
                self.logger.info(f"Unregistered stream for {symbol}")

                return True

            return False

        except Exception as e:
            self.logger.error(f"Error unregistering stream {symbol}: {e}")
            return False

    async def process_message(self, symbol: str, message: Dict[str, Any]) -> bool:
        """
        Process a high-frequency message with optimizations.

        Args:
            symbol: Asset symbol
            message: Message data

        Returns:
            True if processed successfully
        """
        try:
            start_time = time.perf_counter()

            if symbol not in self.active_streams:
                return False

            stream = self.active_streams[symbol]
            metrics = self.stream_metrics[symbol]

            # Add timestamp for latency calculation
            message["_received_at"] = start_time

            # Compress message if needed
            if self.use_compression:
                message = await self._compress_message(message)

            # Add to queue
            stream["queue"].append(message)

            # Update metrics
            metrics.message_count += 1
            metrics.bytes_processed += len(str(message))
            metrics.last_update = datetime.now()

            # Calculate latency
            processing_time = (time.perf_counter() - start_time) * 1000
            metrics.avg_latency_ms = (
                metrics.avg_latency_ms * 0.9 + processing_time * 0.1
            )
            metrics.max_latency_ms = max(metrics.max_latency_ms, processing_time)

            return True

        except Exception as e:
            self.logger.error(f"Error processing message for {symbol}: {e}")
            if symbol in self.stream_metrics:
                self.stream_metrics[symbol].error_count += 1
            return False

    async def _process_stream(self, symbol: str):
        """Process messages for a specific stream."""
        try:
            stream = self.active_streams[symbol]

            while symbol in self.active_streams:
                try:
                    # Get messages from queue
                    messages = stream["queue"].get_latest(self.batch_size)

                    if messages:
                        # Process in batch for efficiency
                        await self._process_message_batch(symbol, messages)

                    # Adaptive sleep based on message volume
                    if len(messages) < self.batch_size:
                        await asyncio.sleep(self.flush_interval)
                    else:
                        await asyncio.sleep(0.001)  # Minimal sleep for high volume

                except asyncio.CancelledError:
                    break
                except Exception as e:
                    self.logger.error(f"Error in stream processing for {symbol}: {e}")
                    await asyncio.sleep(0.1)

        except Exception as e:
            self.logger.error(f"Fatal error in stream processing for {symbol}: {e}")

    async def _process_message_batch(self, symbol: str, messages: List[Dict[str, Any]]):
        """Process a batch of messages efficiently."""
        try:
            stream = self.active_streams[symbol]
            callback = stream["callback"]

            # Decompress messages if needed
            if self.use_compression:
                messages = [await self._decompress_message(msg) for msg in messages]

            # Process messages concurrently
            tasks = [callback(msg) for msg in messages]

            # Use gather with return_exceptions to handle failures gracefully
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Count errors
            error_count = sum(1 for result in results if isinstance(result, Exception))
            if error_count > 0:
                self.stream_metrics[symbol].error_count += error_count

        except Exception as e:
            self.logger.error(f"Error processing message batch for {symbol}: {e}")

    async def _monitor_performance(self):
        """Monitor system performance continuously."""
        while True:
            try:
                await asyncio.sleep(1)  # Monitor every second

                # Calculate system metrics
                await self._update_system_metrics()

                # Store metrics history
                self.performance_history.append(
                    {
                        "timestamp": datetime.now(),
                        "metrics": dict(self.system_metrics.__dict__),
                    }
                )

                # Perform optimizations if needed
                await self._optimize_performance()

            except Exception as e:
                self.logger.error(f"Error in performance monitoring: {e}")

    async def _update_system_metrics(self):
        """Update system-wide performance metrics."""
        try:
            import psutil

            # CPU and memory usage
            self.system_metrics.cpu_usage = psutil.cpu_percent()
            memory = psutil.virtual_memory()
            self.system_metrics.memory_usage_mb = memory.used / 1024 / 1024

            # Stream metrics
            self.system_metrics.active_connections = len(self.active_streams)

            # Calculate messages per second
            total_messages = sum(m.message_count for m in self.stream_metrics.values())
            if len(self.performance_history) > 0:
                prev_total = sum(
                    m["metrics"].get("total_messages", 0)
                    for m in self.performance_history[-60:]
                )
                self.system_metrics.messages_per_second = (
                    total_messages - prev_total
                ) / 60

            # Cache hit rate
            await self._calculate_cache_metrics()

        except Exception as e:
            self.logger.error(f"Error updating system metrics: {e}")

    async def _optimize_performance(self):
        """Perform dynamic performance optimizations."""
        try:
            # Adjust batch size based on load
            avg_latency = np.mean(
                [m.avg_latency_ms for m in self.stream_metrics.values()]
            )

            if avg_latency > self.target_latency_ms:
                # Increase batch size to reduce per-message overhead
                self.batch_size = min(self.batch_size + 10, 500)
                self.flush_interval = max(self.flush_interval - 0.01, 0.01)
            elif avg_latency < self.target_latency_ms * 0.5:
                # Decrease batch size for lower latency
                self.batch_size = max(self.batch_size - 5, 10)
                self.flush_interval = min(self.flush_interval + 0.01, 0.5)

            # Clean up local cache if too large
            if len(self.local_cache) > self.max_cache_size:
                # Remove oldest entries
                items = list(self.local_cache.items())
                for key, _ in items[: -self.max_cache_size // 2]:
                    del self.local_cache[key]

            # Garbage collection optimization
            if self.system_metrics.memory_usage_mb > 1000:  # > 1GB
                import gc

                gc.collect()

        except Exception as e:
            self.logger.error(f"Error in performance optimization: {e}")

    async def _compress_message(self, message: Dict[str, Any]) -> bytes:
        """Compress message if beneficial."""
        try:
            # Serialize with msgpack (faster than JSON)
            serialized = msgpack.packb(message)

            if len(serialized) > self.compression_threshold:
                # Use LZ4 for fast compression
                compressed = lz4.frame.compress(serialized)
                return {"_compressed": True, "_data": compressed}
            else:
                return {"_compressed": False, "_data": serialized}

        except Exception as e:
            self.logger.error(f"Error compressing message: {e}")
            return message

    async def _decompress_message(self, message: Any) -> Dict[str, Any]:
        """Decompress message if needed."""
        try:
            if isinstance(message, dict) and message.get("_compressed"):
                if message["_compressed"]:
                    decompressed = lz4.frame.decompress(message["_data"])
                    return msgpack.unpackb(decompressed)
                else:
                    return msgpack.unpackb(message["_data"])
            else:
                return message

        except Exception as e:
            self.logger.error(f"Error decompressing message: {e}")
            return message if isinstance(message, dict) else {}

    async def _calculate_cache_metrics(self):
        """Calculate cache performance metrics."""
        try:
            if self.redis_pool:
                redis = aioredis.Redis(connection_pool=self.redis_pool)
                info = await redis.info("stats")

                hits = info.get("keyspace_hits", 0)
                misses = info.get("keyspace_misses", 0)
                total = hits + misses

                self.system_metrics.cache_hit_rate = (
                    (hits / total * 100) if total > 0 else 0
                )

        except Exception as e:
            self.logger.error(f"Error calculating cache metrics: {e}")

    async def get_performance_stats(self) -> Dict[str, Any]:
        """Get current performance statistics."""
        try:
            # Stream-level stats
            stream_stats = {}
            for symbol, metrics in self.stream_metrics.items():
                stream_stats[symbol] = {
                    "message_count": metrics.message_count,
                    "avg_latency_ms": metrics.avg_latency_ms,
                    "max_latency_ms": metrics.max_latency_ms,
                    "error_count": metrics.error_count,
                    "last_update": metrics.last_update.isoformat(),
                }

            # System-level stats
            system_stats = {
                "total_streams": self.system_metrics.total_streams,
                "active_connections": self.system_metrics.active_connections,
                "messages_per_second": self.system_metrics.messages_per_second,
                "cpu_usage": self.system_metrics.cpu_usage,
                "memory_usage_mb": self.system_metrics.memory_usage_mb,
                "cache_hit_rate": self.system_metrics.cache_hit_rate,
            }

            # Performance history (last 5 minutes)
            recent_history = list(self.performance_history)[-300:]  # Last 5 minutes

            return {
                "timestamp": datetime.now().isoformat(),
                "stream_stats": stream_stats,
                "system_stats": system_stats,
                "performance_history": recent_history,
                "optimization_settings": {
                    "batch_size": self.batch_size,
                    "flush_interval": self.flush_interval,
                    "buffer_size": self.buffer_size,
                    "max_concurrent_streams": self.max_concurrent_streams,
                    "target_latency_ms": self.target_latency_ms,
                },
            }

        except Exception as e:
            self.logger.error(f"Error getting performance stats: {e}")
            return {}

    async def optimize_for_latency(self):
        """Optimize system configuration for minimum latency."""
        try:
            self.batch_size = 10  # Smaller batches
            self.flush_interval = 0.001  # Process immediately
            self.buffer_size = 100  # Smaller buffers
            self.target_latency_ms = 100  # 100ms target

            self.logger.info("Optimized for low latency")

        except Exception as e:
            self.logger.error(f"Error optimizing for latency: {e}")

    async def optimize_for_throughput(self):
        """Optimize system configuration for maximum throughput."""
        try:
            self.batch_size = 500  # Larger batches
            self.flush_interval = 0.1  # Batch processing
            self.buffer_size = 5000  # Larger buffers
            self.target_latency_ms = 5000  # 5s acceptable

            self.logger.info("Optimized for high throughput")

        except Exception as e:
            self.logger.error(f"Error optimizing for throughput: {e}")

    async def shutdown(self):
        """Gracefully shutdown the optimizer."""
        try:
            # Cancel all stream processing tasks
            for symbol in list(self.active_streams.keys()):
                await self.unregister_stream(symbol)

            # Close Redis connections
            if self.redis_pool:
                await self.redis_pool.disconnect()

            # Shutdown thread pool
            self.thread_pool.shutdown(wait=True)

            self.logger.info("High-frequency optimizer shut down")

        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")

    def is_healthy(self) -> bool:
        """Check if the optimizer is healthy."""
        try:
            # Check if performance is within acceptable limits
            avg_latency = np.mean(
                [m.avg_latency_ms for m in self.stream_metrics.values()]
            )
            error_rate = sum(m.error_count for m in self.stream_metrics.values()) / max(
                sum(m.message_count for m in self.stream_metrics.values()), 1
            )

            return (
                avg_latency < self.target_latency_ms * 2
                and error_rate < 0.01  # Less than 1% error rate
                and self.system_metrics.cpu_usage < 90
                and self.system_metrics.memory_usage_mb < 2048  # Less than 2GB
            )

        except Exception:
            return False
