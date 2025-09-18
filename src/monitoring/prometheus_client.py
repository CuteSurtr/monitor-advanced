"""
Prometheus metrics client for stock market monitoring system.
"""

import time
import logging
from typing import Dict, Any, Optional
from prometheus_client import Counter, Histogram, Gauge, Info, start_http_server
from prometheus_client.core import CollectorRegistry
import psutil
import threading
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class PrometheusClient:
    """Prometheus metrics client with custom metrics for stock monitoring."""

    def __init__(self, port: int = 8000, registry: Optional[CollectorRegistry] = None):
        """
        Initialize Prometheus client.

        Args:
            port: Port to serve metrics on
            registry: Custom registry (optional)
        """
        self.port = port
        self.registry = registry
        self._server_started = False

        # Stock market specific metrics
        self.stock_prices = Gauge(
            "stock_price_usd",
            "Current stock price in USD",
            ["symbol", "exchange"],
            registry=registry,
        )

        self.portfolio_value = Gauge(
            "portfolio_total_value_usd",
            "Total portfolio value in USD",
            ["portfolio_id"],
            registry=registry,
        )

        self.alert_count = Counter(
            "alerts_triggered_total",
            "Total number of alerts triggered",
            ["alert_type", "severity"],
            registry=registry,
        )

        self.api_requests = Counter(
            "api_requests_total",
            "Total API requests made",
            ["provider", "endpoint", "status"],
            registry=registry,
        )

        self.api_request_duration = Histogram(
            "api_request_duration_seconds",
            "API request duration in seconds",
            ["provider", "endpoint"],
            registry=registry,
        )

        self.data_collection_latency = Histogram(
            "data_collection_latency_seconds",
            "Data collection latency in seconds",
            ["data_type"],
            registry=registry,
        )

        self.prediction_accuracy = Gauge(
            "ml_prediction_accuracy",
            "ML model prediction accuracy",
            ["model_type", "timeframe"],
            registry=registry,
        )

        # System metrics
        self.system_cpu_usage = Gauge(
            "system_cpu_usage_percent", "System CPU usage percentage", registry=registry
        )

        self.system_memory_usage = Gauge(
            "system_memory_usage_bytes",
            "System memory usage in bytes",
            registry=registry,
        )

        self.system_disk_usage = Gauge(
            "system_disk_usage_percent",
            "System disk usage percentage",
            ["mount_point"],
            registry=registry,
        )

        self.database_connections = Gauge(
            "database_connections_active",
            "Active database connections",
            ["database"],
            registry=registry,
        )

        self.cache_hit_rate = Gauge(
            "cache_hit_rate",
            "Cache hit rate percentage",
            ["cache_type"],
            registry=registry,
        )

        # Application info
        self.app_info = Info(
            "stock_monitor_info",
            "Stock monitor application information",
            registry=registry,
        )

        # Background metrics collection
        self._metrics_thread = None
        self._stop_collection = threading.Event()

    def start_server(self):
        """Start Prometheus metrics server."""
        if not self._server_started:
            start_http_server(self.port, registry=self.registry)
            self._server_started = True
            logger.info(f"Prometheus metrics server started on port {self.port}")

            # Set application info
            self.app_info.info(
                {
                    "version": "1.0.0",
                    "environment": "production",
                    "started_at": str(time.time()),
                }
            )

    def start_background_collection(self):
        """Start background metrics collection."""
        if self._metrics_thread is None:
            self._metrics_thread = threading.Thread(
                target=self._collect_system_metrics, daemon=True
            )
            self._metrics_thread.start()
            logger.info("Background metrics collection started")

    def stop_background_collection(self):
        """Stop background metrics collection."""
        if self._metrics_thread:
            self._stop_collection.set()
            self._metrics_thread.join(timeout=5)
            self._metrics_thread = None
            logger.info("Background metrics collection stopped")

    def _collect_system_metrics(self):
        """Collect system metrics in background."""
        while not self._stop_collection.is_set():
            try:
                # CPU usage
                cpu_percent = psutil.cpu_percent(interval=1)
                self.system_cpu_usage.set(cpu_percent)

                # Memory usage
                memory = psutil.virtual_memory()
                self.system_memory_usage.set(memory.used)

                # Disk usage
                for disk in psutil.disk_partitions():
                    try:
                        usage = psutil.disk_usage(disk.mountpoint)
                        self.system_disk_usage.labels(mount_point=disk.mountpoint).set(
                            usage.percent
                        )
                    except PermissionError:
                        continue

            except Exception as e:
                logger.error(f"Error collecting system metrics: {e}")

            time.sleep(30)  # Collect every 30 seconds

    def record_stock_price(self, symbol: str, exchange: str, price: float):
        """Record stock price metric."""
        self.stock_prices.labels(symbol=symbol, exchange=exchange).set(price)

    def record_portfolio_value(self, portfolio_id: str, value: float):
        """Record portfolio value metric."""
        self.portfolio_value.labels(portfolio_id=portfolio_id).set(value)

    def record_alert(self, alert_type: str, severity: str):
        """Record alert metric."""
        self.alert_count.labels(alert_type=alert_type, severity=severity).inc()

    def record_api_request(self, provider: str, endpoint: str, status: str):
        """Record API request metric."""
        self.api_requests.labels(
            provider=provider, endpoint=endpoint, status=status
        ).inc()

    @contextmanager
    def time_api_request(self, provider: str, endpoint: str):
        """Context manager to time API requests."""
        start_time = time.time()
        try:
            yield
        finally:
            duration = time.time() - start_time
            self.api_request_duration.labels(
                provider=provider, endpoint=endpoint
            ).observe(duration)

    @contextmanager
    def time_data_collection(self, data_type: str):
        """Context manager to time data collection."""
        start_time = time.time()
        try:
            yield
        finally:
            duration = time.time() - start_time
            self.data_collection_latency.labels(data_type=data_type).observe(duration)

    def record_prediction_accuracy(
        self, model_type: str, timeframe: str, accuracy: float
    ):
        """Record ML prediction accuracy."""
        self.prediction_accuracy.labels(model_type=model_type, timeframe=timeframe).set(
            accuracy
        )

    def record_database_connections(self, database: str, count: int):
        """Record database connection count."""
        self.database_connections.labels(database=database).set(count)

    def record_cache_hit_rate(self, cache_type: str, hit_rate: float):
        """Record cache hit rate."""
        self.cache_hit_rate.labels(cache_type=cache_type).set(hit_rate)

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of current metrics."""
        try:
            return {
                "system": {
                    "cpu_usage": psutil.cpu_percent(),
                    "memory_usage": psutil.virtual_memory().percent,
                    "disk_usage": psutil.disk_usage("/").percent,
                },
                "server_status": "running" if self._server_started else "stopped",
                "collection_active": self._metrics_thread is not None
                and self._metrics_thread.is_alive(),
            }
        except Exception as e:
            logger.error(f"Error getting metrics summary: {e}")
            return {"error": str(e)}


# Global instance
_prometheus_client: Optional[PrometheusClient] = None


def get_prometheus_client() -> PrometheusClient:
    """Get global Prometheus client instance."""
    global _prometheus_client
    if _prometheus_client is None:
        _prometheus_client = PrometheusClient()
    return _prometheus_client


def initialize_prometheus(port: int = 8000) -> PrometheusClient:
    """Initialize and start Prometheus metrics collection."""
    global _prometheus_client
    _prometheus_client = PrometheusClient(port=port)
    _prometheus_client.start_server()
    _prometheus_client.start_background_collection()
    return _prometheus_client
