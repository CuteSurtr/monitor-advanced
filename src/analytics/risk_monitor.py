"""
Real-time Risk Monitoring Service - Continuous risk assessment and alerting.
"""

import asyncio
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

from src.utils.logger import get_logger
from src.analytics.risk_analytics import RiskAnalytics, RiskMetrics
from src.alerts.alert_manager import AlertManager


@dataclass
class RiskThresholds:
    """Risk monitoring thresholds."""

    var_95_threshold: float = 0.05  # 5% daily VaR
    var_99_threshold: float = 0.08  # 8% daily VaR
    volatility_threshold: float = 0.30  # 30% annual volatility
    drawdown_warning: float = 0.05  # 5% drawdown warning
    drawdown_critical: float = 0.10  # 10% drawdown critical
    sharpe_ratio_minimum: float = 0.5  # Minimum acceptable Sharpe ratio
    correlation_threshold: float = 0.8  # High correlation warning
    component_var_threshold: float = 0.30  # 30% of portfolio VaR from single asset


class RiskMonitor:
    """Real-time risk monitoring service."""

    def __init__(self, db_manager, cache_manager, config=None):
        self.db_manager = db_manager
        self.cache_manager = cache_manager
        self.config = config
        self.logger = get_logger(__name__)
        self.risk_analytics = RiskAnalytics(db_manager, cache_manager, config)
        self.running = False

        # Risk thresholds
        self.thresholds = RiskThresholds()

        # Alert manager
        try:
            self.alert_manager = AlertManager(config, db_manager)
        except:
            self.alert_manager = None
            self.logger.warning("Alert manager not available")

        # Monitoring intervals
        self.portfolio_check_interval = 300  # 5 minutes
        self.market_risk_check_interval = 60  # 1 minute
        self.correlation_check_interval = 900  # 15 minutes

        # Risk history for trend analysis
        self.risk_history = {}

    async def start(self):
        """Start the risk monitoring service."""
        self.running = True
        self.logger.info("Starting risk monitoring service")

        try:
            # Start monitoring tasks
            tasks = [
                asyncio.create_task(self._monitor_portfolio_risk()),
                asyncio.create_task(self._monitor_market_risk()),
                asyncio.create_task(self._monitor_correlations()),
                asyncio.create_task(self._monitor_risk_trends()),
            ]

            await asyncio.gather(*tasks)

        except asyncio.CancelledError:
            self.logger.info("Risk monitor cancelled")
        except Exception as e:
            self.logger.error(f"Error in risk monitor: {e}")
        finally:
            self.running = False

    async def stop(self):
        """Stop the risk monitoring service."""
        self.running = False
        self.logger.info("Stopping risk monitoring service")

    async def _monitor_portfolio_risk(self):
        """Monitor individual portfolio risk metrics."""
        while self.running:
            try:
                # Get active portfolios
                portfolios = await self._get_active_portfolios()

                for portfolio in portfolios:
                    portfolio_id = portfolio.get("id")
                    if portfolio_id:
                        await self._check_portfolio_risk(portfolio_id)
                        await asyncio.sleep(1)  # Small delay between portfolios

                await asyncio.sleep(self.portfolio_check_interval)

            except Exception as e:
                self.logger.error(f"Error in portfolio risk monitoring: {e}")
                await asyncio.sleep(60)  # Wait 1 minute on error

    async def _monitor_market_risk(self):
        """Monitor market-wide risk indicators."""
        while self.running:
            try:
                # Monitor key market indicators
                await self._check_market_volatility()
                await self._check_vix_levels()
                await self._check_sector_performance()

                await asyncio.sleep(self.market_risk_check_interval)

            except Exception as e:
                self.logger.error(f"Error in market risk monitoring: {e}")
                await asyncio.sleep(60)

    async def _monitor_correlations(self):
        """Monitor correlation changes and concentration risk."""
        while self.running:
            try:
                portfolios = await self._get_active_portfolios()

                for portfolio in portfolios:
                    portfolio_id = portfolio.get("id")
                    if portfolio_id:
                        await self._check_correlation_risk(portfolio_id)
                        await asyncio.sleep(2)

                await asyncio.sleep(self.correlation_check_interval)

            except Exception as e:
                self.logger.error(f"Error in correlation monitoring: {e}")
                await asyncio.sleep(120)

    async def _monitor_risk_trends(self):
        """Monitor risk metric trends and changes."""
        while self.running:
            try:
                portfolios = await self._get_active_portfolios()

                for portfolio in portfolios:
                    portfolio_id = portfolio.get("id")
                    if portfolio_id:
                        await self._analyze_risk_trends(portfolio_id)

                await asyncio.sleep(1800)  # Check trends every 30 minutes

            except Exception as e:
                self.logger.error(f"Error in trend monitoring: {e}")
                await asyncio.sleep(300)

    async def _check_portfolio_risk(self, portfolio_id: int):
        """Check risk metrics for a specific portfolio."""
        try:
            # Calculate current risk metrics
            risk_metrics = await self.risk_analytics.calculate_portfolio_risk(
                portfolio_id
            )

            # Store in history for trend analysis
            self._store_risk_history(portfolio_id, risk_metrics)

            # Check VaR thresholds
            await self._check_var_thresholds(portfolio_id, risk_metrics)

            # Check volatility thresholds
            await self._check_volatility_thresholds(portfolio_id, risk_metrics)

            # Check drawdown thresholds
            await self._check_drawdown_thresholds(portfolio_id, risk_metrics)

            # Check Sharpe ratio
            await self._check_sharpe_ratio(portfolio_id, risk_metrics)

            # Check component VaR concentration
            await self._check_component_var_concentration(portfolio_id, risk_metrics)

        except Exception as e:
            self.logger.error(f"Error checking portfolio {portfolio_id} risk: {e}")

    async def _check_var_thresholds(self, portfolio_id: int, risk_metrics: RiskMetrics):
        """Check VaR threshold breaches."""
        try:
            # Check 95% VaR
            if risk_metrics.var_95_historical > self.thresholds.var_95_threshold:
                await self._send_risk_alert(
                    portfolio_id=portfolio_id,
                    alert_type="high_var_95",
                    level="warning",
                    message=f"Portfolio {portfolio_id} VaR (95%) exceeded threshold: {risk_metrics.var_95_historical:.2%}",
                    current_value=risk_metrics.var_95_historical,
                    threshold=self.thresholds.var_95_threshold,
                )

            # Check 99% VaR
            if risk_metrics.var_99_historical > self.thresholds.var_99_threshold:
                await self._send_risk_alert(
                    portfolio_id=portfolio_id,
                    alert_type="high_var_99",
                    level="critical",
                    message=f"Portfolio {portfolio_id} VaR (99%) exceeded threshold: {risk_metrics.var_99_historical:.2%}",
                    current_value=risk_metrics.var_99_historical,
                    threshold=self.thresholds.var_99_threshold,
                )

        except Exception as e:
            self.logger.error(f"Error checking VaR thresholds: {e}")

    async def _check_volatility_thresholds(
        self, portfolio_id: int, risk_metrics: RiskMetrics
    ):
        """Check volatility threshold breaches."""
        try:
            if risk_metrics.volatility > self.thresholds.volatility_threshold:
                await self._send_risk_alert(
                    portfolio_id=portfolio_id,
                    alert_type="high_volatility",
                    level="warning",
                    message=f"Portfolio {portfolio_id} volatility exceeded threshold: {risk_metrics.volatility:.2%}",
                    current_value=risk_metrics.volatility,
                    threshold=self.thresholds.volatility_threshold,
                )
        except Exception as e:
            self.logger.error(f"Error checking volatility thresholds: {e}")

    async def _check_drawdown_thresholds(
        self, portfolio_id: int, risk_metrics: RiskMetrics
    ):
        """Check drawdown threshold breaches."""
        try:
            if risk_metrics.current_drawdown > self.thresholds.drawdown_critical:
                await self._send_risk_alert(
                    portfolio_id=portfolio_id,
                    alert_type="critical_drawdown",
                    level="critical",
                    message=f"Portfolio {portfolio_id} critical drawdown: {risk_metrics.current_drawdown:.2%}",
                    current_value=risk_metrics.current_drawdown,
                    threshold=self.thresholds.drawdown_critical,
                )
            elif risk_metrics.current_drawdown > self.thresholds.drawdown_warning:
                await self._send_risk_alert(
                    portfolio_id=portfolio_id,
                    alert_type="warning_drawdown",
                    level="warning",
                    message=f"Portfolio {portfolio_id} drawdown warning: {risk_metrics.current_drawdown:.2%}",
                    current_value=risk_metrics.current_drawdown,
                    threshold=self.thresholds.drawdown_warning,
                )
        except Exception as e:
            self.logger.error(f"Error checking drawdown thresholds: {e}")

    async def _check_sharpe_ratio(self, portfolio_id: int, risk_metrics: RiskMetrics):
        """Check Sharpe ratio thresholds."""
        try:
            if risk_metrics.sharpe_ratio < self.thresholds.sharpe_ratio_minimum:
                await self._send_risk_alert(
                    portfolio_id=portfolio_id,
                    alert_type="low_sharpe_ratio",
                    level="info",
                    message=f"Portfolio {portfolio_id} low Sharpe ratio: {risk_metrics.sharpe_ratio:.2f}",
                    current_value=risk_metrics.sharpe_ratio,
                    threshold=self.thresholds.sharpe_ratio_minimum,
                )
        except Exception as e:
            self.logger.error(f"Error checking Sharpe ratio: {e}")

    async def _check_component_var_concentration(
        self, portfolio_id: int, risk_metrics: RiskMetrics
    ):
        """Check for concentration risk in component VaR."""
        try:
            if not risk_metrics.component_var:
                return

            # Find assets contributing more than threshold to portfolio VaR
            total_component_var = sum(
                abs(v) for v in risk_metrics.component_var.values()
            )

            for asset, component_var in risk_metrics.component_var.items():
                if total_component_var > 0:
                    contribution_pct = abs(component_var) / total_component_var

                    if contribution_pct > self.thresholds.component_var_threshold:
                        await self._send_risk_alert(
                            portfolio_id=portfolio_id,
                            alert_type="concentration_risk",
                            level="warning",
                            message=f"Portfolio {portfolio_id} concentration risk - {asset} contributes {contribution_pct:.1%} to VaR",
                            current_value=contribution_pct,
                            threshold=self.thresholds.component_var_threshold,
                            asset=asset,
                        )
        except Exception as e:
            self.logger.error(f"Error checking component VaR concentration: {e}")

    async def _check_correlation_risk(self, portfolio_id: int):
        """Check for high correlation risk."""
        try:
            correlation_matrix = (
                await self.risk_analytics.calculate_portfolio_correlation_matrix(
                    portfolio_id
                )
            )

            if correlation_matrix.empty:
                return

            # Find high correlations (excluding diagonal)
            high_correlations = []
            for i, asset1 in enumerate(correlation_matrix.index):
                for j, asset2 in enumerate(correlation_matrix.columns):
                    if i < j:  # Avoid duplicates and diagonal
                        correlation = correlation_matrix.iloc[i, j]
                        if abs(correlation) > self.thresholds.correlation_threshold:
                            high_correlations.append(
                                {
                                    "asset1": asset1,
                                    "asset2": asset2,
                                    "correlation": correlation,
                                }
                            )

            if high_correlations:
                for corr_pair in high_correlations:
                    await self._send_risk_alert(
                        portfolio_id=portfolio_id,
                        alert_type="high_correlation",
                        level="warning",
                        message=f"High correlation detected: {corr_pair['asset1']} - {corr_pair['asset2']}: {corr_pair['correlation']:.2f}",
                        current_value=abs(corr_pair["correlation"]),
                        threshold=self.thresholds.correlation_threshold,
                        asset=f"{corr_pair['asset1']}-{corr_pair['asset2']}",
                    )
        except Exception as e:
            self.logger.error(f"Error checking correlation risk: {e}")

    async def _analyze_risk_trends(self, portfolio_id: int):
        """Analyze risk metric trends for early warning."""
        try:
            history = self.risk_history.get(portfolio_id, [])

            if len(history) < 5:  # Need at least 5 data points
                return

            # Get recent history
            recent_history = history[-10:]  # Last 10 measurements

            # Analyze VaR trend
            var_values = [h["var_95_historical"] for h in recent_history]
            var_trend = self._calculate_trend(var_values)

            if var_trend > 0.02:  # VaR increasing by more than 2% per measurement
                await self._send_risk_alert(
                    portfolio_id=portfolio_id,
                    alert_type="increasing_var_trend",
                    level="info",
                    message=f"Portfolio {portfolio_id} VaR showing increasing trend",
                    current_value=var_trend,
                    threshold=0.02,
                )

            # Analyze volatility trend
            vol_values = [h["volatility"] for h in recent_history]
            vol_trend = self._calculate_trend(vol_values)

            if (
                vol_trend > 0.05
            ):  # Volatility increasing by more than 5% per measurement
                await self._send_risk_alert(
                    portfolio_id=portfolio_id,
                    alert_type="increasing_volatility_trend",
                    level="info",
                    message=f"Portfolio {portfolio_id} volatility showing increasing trend",
                    current_value=vol_trend,
                    threshold=0.05,
                )
        except Exception as e:
            self.logger.error(f"Error analyzing risk trends: {e}")

    def _calculate_trend(self, values: List[float]) -> float:
        """Calculate trend slope using simple linear regression."""
        if len(values) < 2:
            return 0.0

        try:
            x = np.arange(len(values))
            y = np.array(values)

            # Simple linear regression
            n = len(values)
            slope = (n * np.sum(x * y) - np.sum(x) * np.sum(y)) / (
                n * np.sum(x**2) - np.sum(x) ** 2
            )

            return slope
        except:
            return 0.0

    async def _check_market_volatility(self):
        """Check overall market volatility indicators."""
        try:
            # This would monitor major market indices like SPY, QQQ, etc.
            # For now, we'll implement basic framework
            pass
        except Exception as e:
            self.logger.error(f"Error checking market volatility: {e}")

    async def _check_vix_levels(self):
        """Monitor VIX levels for market fear indicators."""
        try:
            # Get VIX data and check thresholds
            # VIX > 20: Market concern
            # VIX > 30: High fear
            # VIX > 40: Extreme fear
            pass
        except Exception as e:
            self.logger.error(f"Error checking VIX levels: {e}")

    async def _check_sector_performance(self):
        """Monitor sector performance for concentration risk."""
        try:
            # Monitor sector-specific performance and correlations
            pass
        except Exception as e:
            self.logger.error(f"Error checking sector performance: {e}")

    def _store_risk_history(self, portfolio_id: int, risk_metrics: RiskMetrics):
        """Store risk metrics in history for trend analysis."""
        try:
            if portfolio_id not in self.risk_history:
                self.risk_history[portfolio_id] = []

            history_entry = {
                "timestamp": risk_metrics.timestamp.isoformat(),
                "var_95_historical": risk_metrics.var_95_historical,
                "var_99_historical": risk_metrics.var_99_historical,
                "volatility": risk_metrics.volatility,
                "sharpe_ratio": risk_metrics.sharpe_ratio,
                "max_drawdown": risk_metrics.max_drawdown,
                "current_drawdown": risk_metrics.current_drawdown,
            }

            self.risk_history[portfolio_id].append(history_entry)

            # Keep only last 100 entries to manage memory
            if len(self.risk_history[portfolio_id]) > 100:
                self.risk_history[portfolio_id] = self.risk_history[portfolio_id][-100:]

        except Exception as e:
            self.logger.error(f"Error storing risk history: {e}")

    async def _send_risk_alert(
        self,
        portfolio_id: int,
        alert_type: str,
        level: str,
        message: str,
        current_value: float,
        threshold: float,
        asset: str = None,
    ):
        """Send risk-related alert."""
        try:
            if self.alert_manager:
                alert_data = {
                    "portfolio_id": portfolio_id,
                    "alert_type": alert_type,
                    "level": level,
                    "message": message,
                    "current_value": current_value,
                    "threshold": threshold,
                    "timestamp": datetime.now(),
                    "asset": asset,
                }

                await self.alert_manager.create_alert(**alert_data)

            # Also log the alert
            log_level = getattr(self.logger, level.lower(), self.logger.info)
            log_level(f"Risk Alert - {message}")

        except Exception as e:
            self.logger.error(f"Error sending risk alert: {e}")

    async def _get_active_portfolios(self) -> List[Dict[str, Any]]:
        """Get active portfolios for monitoring."""
        try:
            # This would query your portfolios table
            # For now, return empty list
            return []
        except Exception as e:
            self.logger.error(f"Error getting active portfolios: {e}")
            return []

    def is_healthy(self) -> bool:
        """Check if the risk monitor is healthy."""
        return self.running

    async def get_monitoring_status(self) -> Dict[str, Any]:
        """Get current monitoring status."""
        return {
            "running": self.running,
            "portfolios_monitored": len(self.risk_history),
            "thresholds": {
                "var_95_threshold": self.thresholds.var_95_threshold,
                "var_99_threshold": self.thresholds.var_99_threshold,
                "volatility_threshold": self.thresholds.volatility_threshold,
                "drawdown_warning": self.thresholds.drawdown_warning,
                "drawdown_critical": self.thresholds.drawdown_critical,
            },
            "last_check": datetime.now().isoformat(),
        }
