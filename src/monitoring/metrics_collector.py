"""
Prometheus Metrics Collector for Financial Monitoring System.
"""

import asyncio
import time
from typing import Dict, Any, Optional
from datetime import datetime
from prometheus_client import (
    CollectorRegistry,
    Gauge,
    Counter,
    Histogram,
    Summary,
    generate_latest,
    CONTENT_TYPE_LATEST,
    start_http_server,
)

from src.utils.logger import get_logger
from src.utils.database import DatabaseManager
from src.utils.cache import CacheManager


class FinancialMetricsCollector:
    """Prometheus metrics collector for financial monitoring system."""

    def __init__(
        self,
        db_manager: DatabaseManager,
        cache_manager: CacheManager,
        registry: Optional[CollectorRegistry] = None,
    ):
        self.db_manager = db_manager
        self.cache_manager = cache_manager
        self.registry = registry or CollectorRegistry()
        self.logger = get_logger(__name__)
        self.running = False

        # Portfolio P&L metrics
        self.portfolio_total_pnl = Gauge(
            "portfolio_total_pnl",
            "Total portfolio P&L in USD",
            ["portfolio_id"],
            registry=self.registry,
        )

        self.portfolio_daily_pnl = Gauge(
            "portfolio_daily_pnl",
            "Daily portfolio P&L in USD",
            ["portfolio_id"],
            registry=self.registry,
        )

        self.portfolio_unrealized_pnl = Gauge(
            "portfolio_unrealized_pnl",
            "Unrealized portfolio P&L in USD",
            ["portfolio_id"],
            registry=self.registry,
        )

        # Risk metrics
        self.portfolio_var_95 = Gauge(
            "portfolio_var_95",
            "Portfolio Value at Risk (95% confidence)",
            ["portfolio_id"],
            registry=self.registry,
        )

        self.portfolio_var_99 = Gauge(
            "portfolio_var_99",
            "Portfolio Value at Risk (99% confidence)",
            ["portfolio_id"],
            registry=self.registry,
        )

        self.portfolio_cvar_95 = Gauge(
            "portfolio_cvar_95",
            "Portfolio Conditional Value at Risk (95% confidence)",
            ["portfolio_id"],
            registry=self.registry,
        )

        self.portfolio_max_drawdown = Gauge(
            "portfolio_max_drawdown",
            "Portfolio maximum drawdown",
            ["portfolio_id"],
            registry=self.registry,
        )

        self.portfolio_sharpe_ratio = Gauge(
            "portfolio_sharpe_ratio",
            "Portfolio Sharpe ratio",
            ["portfolio_id"],
            registry=self.registry,
        )

        self.portfolio_beta = Gauge(
            "portfolio_beta",
            "Portfolio beta vs benchmark",
            ["portfolio_id", "benchmark"],
            registry=self.registry,
        )

        # Position-level metrics
        self.position_size_usd = Gauge(
            "position_size_usd",
            "Position size in USD",
            ["portfolio_id", "symbol"],
            registry=self.registry,
        )

        self.position_unrealized_pnl = Gauge(
            "position_unrealized_pnl",
            "Position unrealized P&L in USD",
            ["portfolio_id", "symbol"],
            registry=self.registry,
        )

        self.position_risk_limit_usd = Gauge(
            "position_risk_limit_usd",
            "Position risk limit in USD",
            ["portfolio_id", "symbol"],
            registry=self.registry,
        )

        # VIX and volatility metrics
        self.vix_current = Gauge(
            "vix_current", "Current VIX level", registry=self.registry
        )

        self.vix_regime = Gauge(
            "vix_regime",
            "VIX regime (0=low, 1=moderate, 2=high, 3=extreme)",
            registry=self.registry,
        )

        self.implied_volatility = Gauge(
            "implied_volatility",
            "Asset implied volatility",
            ["symbol"],
            registry=self.registry,
        )

        # Market data quality metrics
        self.last_data_update_timestamp = Gauge(
            "last_data_update_timestamp",
            "Unix timestamp of last data update",
            ["feed", "symbol"],
            registry=self.registry,
        )

        self.data_processing_latency_seconds = Histogram(
            "data_processing_latency_seconds",
            "Data processing latency in seconds",
            ["feed", "symbol"],
            buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0],
            registry=self.registry,
        )

        self.market_data_latency_seconds = Histogram(
            "market_data_latency_seconds",
            "Market data latency from source to processing",
            ["source", "symbol"],
            buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 5.0, 10.0],
            registry=self.registry,
        )

        # System performance metrics
        self.cpu_usage_percent = Gauge(
            "cpu_usage_percent", "CPU usage percentage", registry=self.registry
        )

        self.memory_usage_percent = Gauge(
            "memory_usage_percent", "Memory usage percentage", registry=self.registry
        )

        self.memory_usage_bytes = Gauge(
            "memory_usage_bytes", "Memory usage in bytes", registry=self.registry
        )

        # Cache performance metrics
        self.cache_hit_rate = Gauge(
            "cache_hit_rate",
            "Cache hit rate as a percentage",
            ["cache_type"],
            registry=self.registry,
        )

        self.cache_size = Gauge(
            "cache_size",
            "Number of items in cache",
            ["cache_type"],
            registry=self.registry,
        )

        # Trading activity metrics
        self.trading_activity = Counter(
            "trading_activity_total",
            "Total trading activity",
            ["symbol", "action"],
            registry=self.registry,
        )

        self.market_hours = Gauge(
            "market_hours",
            "Market hours indicator (1=open, 0=closed)",
            ["market"],
            registry=self.registry,
        )

        # Options metrics
        self.options_volume_ratio = Gauge(
            "options_volume_ratio",
            "Options volume ratio vs normal",
            ["symbol"],
            registry=self.registry,
        )

        self.put_call_ratio = Gauge(
            "put_call_ratio", "Put/Call ratio", ["symbol"], registry=self.registry
        )

        # Correlation metrics
        self.portfolio_max_correlation = Gauge(
            "portfolio_max_correlation",
            "Maximum pairwise correlation in portfolio",
            ["portfolio_id"],
            registry=self.registry,
        )

        self.asset_correlation = Gauge(
            "asset_correlation",
            "Correlation between two assets",
            ["asset1", "asset2"],
            registry=self.registry,
        )

        # Component VaR
        self.component_var = Gauge(
            "component_var",
            "Component VaR for portfolio positions",
            ["portfolio_id", "symbol"],
            registry=self.registry,
        )

        # Volatility regime changes
        self.volatility_regime_changes_total = Counter(
            "volatility_regime_changes_total",
            "Total volatility regime changes",
            ["symbol", "old_regime", "new_regime"],
            registry=self.registry,
        )

        # Application health metrics
        self.application_health = Gauge(
            "application_health",
            "Application health status (1=healthy, 0=unhealthy)",
            ["component"],
            registry=self.registry,
        )

    async def start_collection(self):
        """Start metrics collection."""
        self.running = True
        self.logger.info("Starting metrics collection")

        # Start HTTP server for Prometheus scraping
        start_http_server(8001, registry=self.registry)
        self.logger.info("Prometheus metrics server started on port 8001")

        # Start collection tasks
        tasks = [
            asyncio.create_task(self._collect_portfolio_metrics()),
            asyncio.create_task(self._collect_risk_metrics()),
            asyncio.create_task(self._collect_market_data_metrics()),
            asyncio.create_task(self._collect_system_metrics()),
            asyncio.create_task(self._collect_vix_metrics()),
            asyncio.create_task(self._collect_options_metrics()),
        ]

        try:
            await asyncio.gather(*tasks)
        except asyncio.CancelledError:
            self.logger.info("Metrics collection cancelled")
        except Exception as e:
            self.logger.error(f"Error in metrics collection: {e}")
        finally:
            self.running = False

    async def stop_collection(self):
        """Stop metrics collection."""
        self.running = False
        self.logger.info("Stopping metrics collection")

    async def _collect_portfolio_metrics(self):
        """Collect portfolio-level metrics."""
        while self.running:
            try:
                # This would get portfolio data from your P&L engine
                portfolios = await self._get_active_portfolios()

                for portfolio in portfolios:
                    portfolio_id = str(portfolio.get("id", 0))

                    # P&L metrics
                    self.portfolio_total_pnl.labels(portfolio_id=portfolio_id).set(
                        portfolio.get("total_pnl", 0)
                    )
                    self.portfolio_daily_pnl.labels(portfolio_id=portfolio_id).set(
                        portfolio.get("daily_pnl", 0)
                    )
                    self.portfolio_unrealized_pnl.labels(portfolio_id=portfolio_id).set(
                        portfolio.get("unrealized_pnl", 0)
                    )

                    # Performance metrics
                    self.portfolio_sharpe_ratio.labels(portfolio_id=portfolio_id).set(
                        portfolio.get("sharpe_ratio", 0)
                    )
                    self.portfolio_beta.labels(
                        portfolio_id=portfolio_id, benchmark="SPY"
                    ).set(portfolio.get("beta", 1.0))

                    # Position-level metrics
                    for position in portfolio.get("positions", []):
                        symbol = position.get("symbol", "UNKNOWN")

                        self.position_size_usd.labels(
                            portfolio_id=portfolio_id, symbol=symbol
                        ).set(position.get("market_value", 0))

                        self.position_unrealized_pnl.labels(
                            portfolio_id=portfolio_id, symbol=symbol
                        ).set(position.get("unrealized_pnl", 0))

                await asyncio.sleep(30)  # Update every 30 seconds

            except Exception as e:
                self.logger.error(f"Error collecting portfolio metrics: {e}")
                await asyncio.sleep(60)

    async def _collect_risk_metrics(self):
        """Collect risk-related metrics."""
        while self.running:
            try:
                portfolios = await self._get_active_portfolios()

                for portfolio in portfolios:
                    portfolio_id = str(portfolio.get("id", 0))

                    # Risk metrics
                    risk_data = portfolio.get("risk_metrics", {})

                    self.portfolio_var_95.labels(portfolio_id=portfolio_id).set(
                        risk_data.get("var_95", 0)
                    )
                    self.portfolio_var_99.labels(portfolio_id=portfolio_id).set(
                        risk_data.get("var_99", 0)
                    )
                    self.portfolio_cvar_95.labels(portfolio_id=portfolio_id).set(
                        risk_data.get("cvar_95", 0)
                    )
                    self.portfolio_max_drawdown.labels(portfolio_id=portfolio_id).set(
                        risk_data.get("max_drawdown", 0)
                    )

                    # Component VaR
                    for symbol, comp_var in risk_data.get("component_var", {}).items():
                        self.component_var.labels(
                            portfolio_id=portfolio_id, symbol=symbol
                        ).set(comp_var)

                    # Correlation metrics
                    self.portfolio_max_correlation.labels(
                        portfolio_id=portfolio_id
                    ).set(risk_data.get("max_correlation", 0))

                await asyncio.sleep(60)  # Update every minute

            except Exception as e:
                self.logger.error(f"Error collecting risk metrics: {e}")
                await asyncio.sleep(60)

    async def _collect_market_data_metrics(self):
        """Collect market data quality metrics."""
        while self.running:
            try:
                # Get data feed status
                feeds = ["stock", "forex", "crypto", "commodity"]

                for feed in feeds:
                    # Get latest data timestamps
                    latest_updates = await self._get_latest_data_timestamps(feed)

                    for symbol, timestamp in latest_updates.items():
                        self.last_data_update_timestamp.labels(
                            feed=feed, symbol=symbol
                        ).set(timestamp)

                # Measure processing latency
                start_time = time.time()
                await self._sample_data_processing()
                processing_time = time.time() - start_time

                self.data_processing_latency_seconds.labels(
                    feed="sample", symbol="TEST"
                ).observe(processing_time)

                await asyncio.sleep(15)  # Update every 15 seconds

            except Exception as e:
                self.logger.error(f"Error collecting market data metrics: {e}")
                await asyncio.sleep(60)

    async def _collect_system_metrics(self):
        """Collect system performance metrics."""
        while self.running:
            try:
                import psutil

                # CPU and memory usage
                cpu_percent = psutil.cpu_percent()
                memory = psutil.virtual_memory()

                self.cpu_usage_percent.set(cpu_percent)
                self.memory_usage_percent.set(memory.percent)
                self.memory_usage_bytes.set(memory.used)

                # Cache metrics
                cache_stats = await self._get_cache_stats()
                for cache_type, stats in cache_stats.items():
                    self.cache_hit_rate.labels(cache_type=cache_type).set(
                        stats.get("hit_rate", 0)
                    )
                    self.cache_size.labels(cache_type=cache_type).set(
                        stats.get("size", 0)
                    )

                # Application health
                components = ["pnl_engine", "risk_monitor", "data_collector"]
                for component in components:
                    health = await self._check_component_health(component)
                    self.application_health.labels(component=component).set(
                        1 if health else 0
                    )

                await asyncio.sleep(30)  # Update every 30 seconds

            except Exception as e:
                self.logger.error(f"Error collecting system metrics: {e}")
                await asyncio.sleep(60)

    async def _collect_vix_metrics(self):
        """Collect VIX and volatility metrics."""
        while self.running:
            try:
                # Get VIX data
                vix_data = await self._get_current_vix_data()

                if vix_data:
                    self.vix_current.set(vix_data.get("VIX", 0))

                    # VIX regime
                    vix_value = vix_data.get("VIX", 0)
                    if vix_value < 20:
                        regime = 0  # low
                    elif vix_value < 30:
                        regime = 1  # moderate
                    elif vix_value < 40:
                        regime = 2  # high
                    else:
                        regime = 3  # extreme

                    self.vix_regime.set(regime)

                # Asset implied volatilities
                symbols = ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA"]
                for symbol in symbols:
                    iv = await self._get_implied_volatility(symbol)
                    self.implied_volatility.labels(symbol=symbol).set(iv)

                await asyncio.sleep(60)  # Update every minute

            except Exception as e:
                self.logger.error(f"Error collecting VIX metrics: {e}")
                await asyncio.sleep(60)

    async def _collect_options_metrics(self):
        """Collect options-related metrics."""
        while self.running:
            try:
                symbols = ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA"]

                for symbol in symbols:
                    # Options volume ratio
                    volume_ratio = await self._get_options_volume_ratio(symbol)
                    self.options_volume_ratio.labels(symbol=symbol).set(volume_ratio)

                    # Put/call ratio
                    pc_ratio = await self._get_put_call_ratio(symbol)
                    self.put_call_ratio.labels(symbol=symbol).set(pc_ratio)

                await asyncio.sleep(300)  # Update every 5 minutes

            except Exception as e:
                self.logger.error(f"Error collecting options metrics: {e}")
                await asyncio.sleep(300)

    def get_metrics(self) -> str:
        """Get current metrics in Prometheus format."""
        return generate_latest(self.registry).decode("utf-8")

    # Helper methods (would be implemented based on your actual data sources)
    async def _get_active_portfolios(self) -> list:
        """Get active portfolios with current metrics."""
        # Mock implementation - replace with actual data
        return []

    async def _get_latest_data_timestamps(self, feed: str) -> Dict[str, float]:
        """Get latest data timestamps for a feed."""
        return {}

    async def _sample_data_processing(self):
        """Sample data processing for latency measurement."""
        await asyncio.sleep(0.001)  # Simulate processing

    async def _get_cache_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get cache statistics."""
        return {
            "redis": {"hit_rate": 85.0, "size": 10000},
            "local": {"hit_rate": 95.0, "size": 5000},
        }

    async def _check_component_health(self, component: str) -> bool:
        """Check component health."""
        return True  # Mock implementation

    async def _get_current_vix_data(self) -> Dict[str, float]:
        """Get current VIX data."""
        return {"VIX": 25.0}

    async def _get_implied_volatility(self, symbol: str) -> float:
        """Get implied volatility for symbol."""
        return 0.25  # Mock 25% IV

    async def _get_options_volume_ratio(self, symbol: str) -> float:
        """Get options volume ratio."""
        return 1.5  # 1.5x normal volume

    async def _get_put_call_ratio(self, symbol: str) -> float:
        """Get put/call ratio."""
        return 0.8  # 0.8 puts per call

    def record_data_latency(self, source: str, symbol: str, latency_seconds: float):
        """Record market data latency."""
        self.market_data_latency_seconds.labels(source=source, symbol=symbol).observe(
            latency_seconds
        )

    def record_trading_activity(self, symbol: str, action: str):
        """Record trading activity."""
        self.trading_activity.labels(symbol=symbol, action=action).inc()

    def record_volatility_regime_change(
        self, symbol: str, old_regime: str, new_regime: str
    ):
        """Record volatility regime change."""
        self.volatility_regime_changes_total.labels(
            symbol=symbol, old_regime=old_regime, new_regime=new_regime
        ).inc()

    def is_healthy(self) -> bool:
        """Check if metrics collector is healthy."""
        return self.running


# Legacy compatibility
class MetricsCollector(FinancialMetricsCollector):
    """Backward compatibility wrapper."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def collect_metrics(self):
        """Legacy method for collecting metrics."""
        return {"metrics": "collecting", "status": "active"}

    async def start(self):
        """Start the metrics collector."""
        await self.start_collection()
