"""
Real-Time Portfolio Risk Analytics Engine
Advanced risk calculations, P&L monitoring, and automated alerts
"""

import asyncio
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import logging
from scipy import stats
import yfinance as yf

from src.analytics.influxdb_sync import influx_sync, MarketData, PortfolioMetrics
from src.utils.config import get_config
from src.utils.logger import get_logger
from src.utils.database import DatabaseManager


@dataclass
class Position:
    """Portfolio position data."""

    symbol: str
    asset_type: str
    quantity: float
    cost_basis: float
    current_price: float
    market_value: float
    pnl: float
    weight: float


@dataclass
class RiskAlert:
    """Risk alert data structure."""

    alert_id: str
    alert_type: str
    severity: str
    message: str
    value: float
    threshold: float
    timestamp: datetime


class RealTimeRiskEngine:
    """Advanced real-time portfolio risk analytics engine."""

    def __init__(self, db_manager: DatabaseManager):
        self.config = get_config()
        self.logger = get_logger(__name__)
        self.db_manager = db_manager
        self.running = False

        # Risk parameters
        self.var_confidence_levels = [0.95, 0.99, 0.999]
        self.lookback_periods = {"short": 30, "medium": 90, "long": 252}

        # Alert thresholds
        self.alert_thresholds = {
            "max_drawdown": 0.05,  # 5%
            "daily_var_99": 10000,  # $10k
            "portfolio_concentration": 0.3,  # 30% in single position
            "vix_spike": 30.0,
            "correlation_breakdown": 0.8,
        }

        # Cache for performance
        self.positions_cache = {}
        self.market_data_cache = {}
        self.risk_metrics_cache = {}

    async def initialize(self):
        """Initialize the risk engine."""
        try:
            await influx_sync.initialize()
            self.logger.info("Real-Time Risk Engine initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize Risk Engine: {e}")
            raise

    # =====================================================
    # REAL-TIME P&L MONITORING
    # =====================================================

    async def calculate_realtime_pnl(
        self, portfolio_id: str = None
    ) -> Dict[str, float]:
        """Calculate comprehensive real-time P&L metrics."""
        try:
            # Get current positions
            positions = await self._get_portfolio_positions(portfolio_id)

            if not positions:
                return self._empty_pnl_metrics()

            # Get current market prices
            current_prices = await self._get_current_prices(
                [p.symbol for p in positions]
            )

            # Calculate P&L metrics
            total_market_value = 0.0
            total_cost_basis = 0.0
            unrealized_pnl = 0.0

            position_pnls = []

            for position in positions:
                current_price = current_prices.get(
                    position.symbol, position.current_price
                )
                market_value = position.quantity * current_price
                position_pnl = market_value - (position.quantity * position.cost_basis)

                total_market_value += market_value
                total_cost_basis += position.quantity * position.cost_basis
                unrealized_pnl += position_pnl

                position_pnls.append(
                    {
                        "symbol": position.symbol,
                        "pnl": position_pnl,
                        "pnl_percent": (
                            (position_pnl / (position.quantity * position.cost_basis))
                            * 100
                            if position.cost_basis > 0
                            else 0
                        ),
                    }
                )

            # Calculate daily P&L (from previous close)
            daily_pnl = await self._calculate_daily_pnl(positions, current_prices)

            # Get realized P&L from trades
            realized_pnl = await self._get_realized_pnl(portfolio_id)

            total_pnl = unrealized_pnl + realized_pnl
            total_return = (
                (total_pnl / total_cost_basis) * 100 if total_cost_basis > 0 else 0
            )

            pnl_metrics = {
                "total_market_value": total_market_value,
                "total_cost_basis": total_cost_basis,
                "unrealized_pnl": unrealized_pnl,
                "realized_pnl": realized_pnl,
                "total_pnl": total_pnl,
                "daily_pnl": daily_pnl,
                "total_return_percent": total_return,
                "daily_return_percent": (
                    (daily_pnl / total_cost_basis) * 100 if total_cost_basis > 0 else 0
                ),
                "position_count": len(positions),
                "top_gainers": sorted(
                    position_pnls, key=lambda x: x["pnl"], reverse=True
                )[:5],
                "top_losers": sorted(position_pnls, key=lambda x: x["pnl"])[:5],
            }

            # Sync to InfluxDB
            await self._sync_pnl_to_influxdb(pnl_metrics)

            return pnl_metrics

        except Exception as e:
            self.logger.error(f"Failed to calculate real-time P&L: {e}")
            return self._empty_pnl_metrics()

    async def _calculate_daily_pnl(
        self, positions: List[Position], current_prices: Dict[str, float]
    ) -> float:
        """Calculate P&L since previous market close."""
        daily_pnl = 0.0

        for position in positions:
            # Get previous close price
            prev_close = await self._get_previous_close_price(position.symbol)
            current_price = current_prices.get(position.symbol, position.current_price)

            if prev_close:
                price_change = current_price - prev_close
                position_daily_pnl = position.quantity * price_change
                daily_pnl += position_daily_pnl

        return daily_pnl

    # =====================================================
    # VAR/CVAR RISK CALCULATIONS
    # =====================================================

    async def calculate_portfolio_var_cvar(
        self, portfolio_id: str = None, confidence_levels: List[float] = None
    ) -> Dict[str, Any]:
        """Calculate Value at Risk and Conditional VaR for portfolio."""
        try:
            if confidence_levels is None:
                confidence_levels = self.var_confidence_levels

            positions = await self._get_portfolio_positions(portfolio_id)
            if not positions:
                return {}

            # Get historical returns data
            symbols = [p.symbol for p in positions]
            weights = np.array([p.weight for p in positions])

            returns_data = await self._get_historical_returns(
                symbols, self.lookback_periods["medium"]
            )

            if returns_data.empty:
                return {}

            # Calculate portfolio returns
            portfolio_returns = (returns_data * weights).sum(axis=1)

            # Get current portfolio value
            portfolio_value = sum(p.market_value for p in positions)

            var_cvar_results = {}

            for confidence in confidence_levels:
                # Parametric VaR (assuming normal distribution)
                var_parametric = self._calculate_parametric_var(
                    portfolio_returns, confidence, portfolio_value
                )

                # Historical VaR
                var_historical = self._calculate_historical_var(
                    portfolio_returns, confidence, portfolio_value
                )

                # Monte Carlo VaR
                var_monte_carlo = await self._calculate_monte_carlo_var(
                    returns_data, weights, confidence, portfolio_value
                )

                # CVaR (Expected Shortfall)
                cvar = self._calculate_cvar(
                    portfolio_returns, confidence, portfolio_value
                )

                var_cvar_results[f"var_{int(confidence*100)}"] = {
                    "parametric": var_parametric,
                    "historical": var_historical,
                    "monte_carlo": var_monte_carlo,
                    "cvar": cvar,
                    "confidence": confidence,
                }

            # Sync to InfluxDB
            await self._sync_var_cvar_to_influxdb(var_cvar_results, portfolio_value)

            return var_cvar_results

        except Exception as e:
            self.logger.error(f"Failed to calculate VaR/CVaR: {e}")
            return {}

    def _calculate_parametric_var(
        self, returns: pd.Series, confidence: float, portfolio_value: float
    ) -> float:
        """Calculate parametric VaR assuming normal distribution."""
        mean_return = returns.mean()
        std_return = returns.std()
        z_score = stats.norm.ppf(1 - confidence)
        var = portfolio_value * (mean_return + z_score * std_return)
        return abs(var)

    def _calculate_historical_var(
        self, returns: pd.Series, confidence: float, portfolio_value: float
    ) -> float:
        """Calculate historical VaR using empirical distribution."""
        percentile = (1 - confidence) * 100
        var_return = np.percentile(returns, percentile)
        var = portfolio_value * var_return
        return abs(var)

    async def _calculate_monte_carlo_var(
        self,
        returns_data: pd.DataFrame,
        weights: np.ndarray,
        confidence: float,
        portfolio_value: float,
        n_simulations: int = 10000,
    ) -> float:
        """Calculate Monte Carlo VaR using simulated returns."""
        try:
            # Calculate covariance matrix
            cov_matrix = returns_data.cov().values
            mean_returns = returns_data.mean().values

            # Generate random scenarios
            simulated_returns = np.random.multivariate_normal(
                mean_returns, cov_matrix, n_simulations
            )

            # Calculate portfolio returns for each scenario
            portfolio_returns = np.dot(simulated_returns, weights)

            # Calculate VaR
            percentile = (1 - confidence) * 100
            var_return = np.percentile(portfolio_returns, percentile)
            var = portfolio_value * var_return

            return abs(var)

        except Exception as e:
            self.logger.error(f"Monte Carlo VaR calculation failed: {e}")
            return 0.0

    def _calculate_cvar(
        self, returns: pd.Series, confidence: float, portfolio_value: float
    ) -> float:
        """Calculate Conditional VaR (Expected Shortfall)."""
        percentile = (1 - confidence) * 100
        var_threshold = np.percentile(returns, percentile)
        cvar_return = returns[returns <= var_threshold].mean()
        cvar = portfolio_value * cvar_return
        return abs(cvar)

    # =====================================================
    # MAX DRAWDOWN CALCULATION
    # =====================================================

    async def calculate_max_drawdown(
        self, portfolio_id: str = None, lookback_days: int = None
    ) -> Dict[str, float]:
        """Calculate maximum drawdown metrics."""
        try:
            if lookback_days is None:
                lookback_days = self.lookback_periods["long"]

            # Get portfolio value history
            portfolio_values = await self._get_portfolio_value_history(
                portfolio_id, lookback_days
            )

            if len(portfolio_values) < 2:
                return {"max_drawdown": 0.0, "current_drawdown": 0.0}

            # Convert to numpy array
            values = np.array(portfolio_values)

            # Calculate running maximum
            cumulative_max = np.maximum.accumulate(values)

            # Calculate drawdown
            drawdown = (values - cumulative_max) / cumulative_max

            # Find maximum drawdown
            max_drawdown = np.min(drawdown)
            current_drawdown = drawdown[-1]

            # Find drawdown periods
            drawdown_periods = self._find_drawdown_periods(values, cumulative_max)

            drawdown_metrics = {
                "max_drawdown": abs(max_drawdown),
                "max_drawdown_percent": abs(max_drawdown) * 100,
                "current_drawdown": abs(current_drawdown),
                "current_drawdown_percent": abs(current_drawdown) * 100,
                "drawdown_periods": len(drawdown_periods),
                "longest_drawdown_days": (
                    max([p["duration"] for p in drawdown_periods])
                    if drawdown_periods
                    else 0
                ),
                "recovery_factor": (
                    abs(max_drawdown) / np.std(np.diff(values) / values[:-1])
                    if len(values) > 1
                    else 0
                ),
            }

            # Sync to InfluxDB
            await self._sync_drawdown_to_influxdb(drawdown_metrics)

            return drawdown_metrics

        except Exception as e:
            self.logger.error(f"Failed to calculate max drawdown: {e}")
            return {"max_drawdown": 0.0, "current_drawdown": 0.0}

    def _find_drawdown_periods(
        self, values: np.ndarray, cumulative_max: np.ndarray
    ) -> List[Dict[str, Any]]:
        """Find distinct drawdown periods."""
        drawdown_periods = []
        in_drawdown = False
        start_idx = 0

        for i, (value, max_val) in enumerate(zip(values, cumulative_max)):
            if value < max_val and not in_drawdown:
                # Start of drawdown
                in_drawdown = True
                start_idx = i
            elif value == max_val and in_drawdown:
                # End of drawdown
                in_drawdown = False
                period = {
                    "start_idx": start_idx,
                    "end_idx": i,
                    "duration": i - start_idx,
                    "depth": (
                        cumulative_max[start_idx] - values[start_idx : i + 1].min()
                    )
                    / cumulative_max[start_idx],
                }
                drawdown_periods.append(period)

        return drawdown_periods

    # =====================================================
    # VIX MONITORING AND VOLATILITY ANALYSIS
    # =====================================================

    async def monitor_vix_and_volatility(self) -> Dict[str, Any]:
        """Monitor VIX and calculate volatility metrics."""
        try:
            # Get current VIX data
            vix_data = await self._get_current_vix_data()

            if not vix_data:
                return {}

            current_vix = vix_data["value"]

            # Get VIX historical data for analysis
            vix_history = await self._get_vix_history(90)

            # Calculate VIX metrics
            vix_metrics = {
                "current_vix": current_vix,
                "vix_percentile_30d": self._calculate_percentile(
                    vix_history[-30:], current_vix
                ),
                "vix_percentile_90d": self._calculate_percentile(
                    vix_history, current_vix
                ),
                "vix_ma_5": (
                    np.mean(vix_history[-5:]) if len(vix_history) >= 5 else current_vix
                ),
                "vix_ma_20": (
                    np.mean(vix_history[-20:])
                    if len(vix_history) >= 20
                    else current_vix
                ),
                "volatility_regime": self._classify_volatility_regime(current_vix),
                "vix_spike_alert": current_vix > self.alert_thresholds["vix_spike"],
            }

            # Calculate implied vs realized volatility
            realized_vol = await self._calculate_realized_volatility()
            if realized_vol:
                vix_metrics["implied_vs_realized"] = current_vix / realized_vol
                vix_metrics["vol_risk_premium"] = current_vix - realized_vol

            # Sync to InfluxDB
            await influx_sync.sync_vix_data(current_vix)

            return vix_metrics

        except Exception as e:
            self.logger.error(f"Failed to monitor VIX: {e}")
            return {}

    def _classify_volatility_regime(self, vix_value: float) -> str:
        """Classify volatility regime based on VIX level."""
        if vix_value < 15:
            return "low"
        elif vix_value < 20:
            return "normal"
        elif vix_value < 30:
            return "elevated"
        elif vix_value < 40:
            return "high"
        else:
            return "extreme"

    async def _calculate_realized_volatility(
        self, symbol: str = "SPY", window: int = 20
    ) -> Optional[float]:
        """Calculate realized volatility for comparison with VIX."""
        try:
            # Get recent price data
            prices = await self._get_historical_prices(symbol, window + 5)
            if len(prices) < window:
                return None

            # Calculate returns and realized volatility
            returns = np.log(prices[1:] / prices[:-1])
            realized_vol = np.std(returns) * np.sqrt(252) * 100  # Annualized percentage

            return realized_vol

        except Exception as e:
            self.logger.error(f"Failed to calculate realized volatility: {e}")
            return None

    # =====================================================
    # AUTOMATED RISK ALERTS
    # =====================================================

    async def check_risk_alerts(self, portfolio_id: str = None) -> List[RiskAlert]:
        """Check for risk threshold breaches and generate alerts."""
        alerts = []

        try:
            # Get current metrics
            pnl_metrics = await self.calculate_realtime_pnl(portfolio_id)
            var_cvar = await self.calculate_portfolio_var_cvar(portfolio_id)
            drawdown_metrics = await self.calculate_max_drawdown(portfolio_id)
            vix_metrics = await self.monitor_vix_and_volatility()

            # Check P&L alerts
            if pnl_metrics.get("daily_pnl", 0) < -self.alert_thresholds["daily_var_99"]:
                alerts.append(
                    RiskAlert(
                        alert_id=f"daily_loss_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                        alert_type="daily_loss",
                        severity="high",
                        message=f"Daily P&L loss exceeds threshold: ${pnl_metrics['daily_pnl']:,.2f}",
                        value=pnl_metrics["daily_pnl"],
                        threshold=-self.alert_thresholds["daily_var_99"],
                        timestamp=datetime.now(),
                    )
                )

            # Check VaR alerts
            if var_cvar and "var_99" in var_cvar:
                var_99 = var_cvar["var_99"].get("historical", 0)
                if var_99 > self.alert_thresholds["daily_var_99"]:
                    alerts.append(
                        RiskAlert(
                            alert_id=f"var_breach_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                            alert_type="var_breach",
                            severity="medium",
                            message=f"99% VaR exceeds threshold: ${var_99:,.2f}",
                            value=var_99,
                            threshold=self.alert_thresholds["daily_var_99"],
                            timestamp=datetime.now(),
                        )
                    )

            # Check drawdown alerts
            if (
                drawdown_metrics.get("current_drawdown", 0)
                > self.alert_thresholds["max_drawdown"]
            ):
                alerts.append(
                    RiskAlert(
                        alert_id=f"drawdown_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                        alert_type="max_drawdown",
                        severity="high",
                        message=f"Current drawdown exceeds threshold: {drawdown_metrics['current_drawdown_percent']:.2f}%",
                        value=drawdown_metrics["current_drawdown"],
                        threshold=self.alert_thresholds["max_drawdown"],
                        timestamp=datetime.now(),
                    )
                )

            # Check VIX alerts
            if vix_metrics.get("vix_spike_alert", False):
                alerts.append(
                    RiskAlert(
                        alert_id=f"vix_spike_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                        alert_type="vix_spike",
                        severity="medium",
                        message=f"VIX spike detected: {vix_metrics['current_vix']:.2f}",
                        value=vix_metrics["current_vix"],
                        threshold=self.alert_thresholds["vix_spike"],
                        timestamp=datetime.now(),
                    )
                )

            # Store alerts in InfluxDB
            for alert in alerts:
                await self._store_alert_in_influxdb(alert)

            return alerts

        except Exception as e:
            self.logger.error(f"Failed to check risk alerts: {e}")
            return []

    # =====================================================
    # UTILITY METHODS
    # =====================================================

    async def _get_portfolio_positions(
        self, portfolio_id: str = None
    ) -> List[Position]:
        """Get current portfolio positions from PostgreSQL."""
        # This would integrate with your actual portfolio data
        # For now, returning mock data
        return [
            Position("AAPL", "stock", 100, 150.0, 175.0, 17500.0, 2500.0, 0.35),
            Position("GOOGL", "stock", 50, 2800.0, 2950.0, 147500.0, 7500.0, 0.30),
            Position("BTC", "crypto", 2, 45000.0, 47000.0, 94000.0, 4000.0, 0.20),
            Position("EUR/USD", "forex", 10000, 1.0850, 1.0920, 10920.0, 700.0, 0.15),
        ]

    async def _get_current_prices(self, symbols: List[str]) -> Dict[str, float]:
        """Get current market prices from InfluxDB or live feeds."""
        # Implementation would query InfluxDB or external APIs
        return {symbol: 100.0 for symbol in symbols}  # Mock data

    def _empty_pnl_metrics(self) -> Dict[str, float]:
        """Return empty P&L metrics structure."""
        return {
            "total_market_value": 0.0,
            "total_cost_basis": 0.0,
            "unrealized_pnl": 0.0,
            "realized_pnl": 0.0,
            "total_pnl": 0.0,
            "daily_pnl": 0.0,
            "total_return_percent": 0.0,
            "daily_return_percent": 0.0,
            "position_count": 0,
        }

    async def _sync_pnl_to_influxdb(self, pnl_metrics: Dict[str, Any]):
        """Sync P&L metrics to InfluxDB."""
        portfolio_metrics = PortfolioMetrics(
            timestamp=datetime.now(),
            total_value=pnl_metrics["total_market_value"],
            pnl_daily=pnl_metrics["daily_pnl"],
            pnl_total=pnl_metrics["total_pnl"],
            var_99=0.0,  # Would be calculated
            cvar_99=0.0,  # Would be calculated
            max_drawdown=0.0,  # Would be calculated
            sharpe_ratio=0.0,  # Would be calculated
            beta=0.0,  # Would be calculated
            positions_count=pnl_metrics["position_count"],
        )

        await influx_sync.sync_portfolio_metrics(portfolio_metrics)

    def _calculate_percentile(self, data: List[float], value: float) -> float:
        """Calculate percentile rank of value in data."""
        return (np.sum(np.array(data) <= value) / len(data)) * 100

    async def start_monitoring(self):
        """Start the real-time risk monitoring loop."""
        self.running = True
        self.logger.info("Starting real-time risk monitoring")

        while self.running:
            try:
                # Run risk calculations every 30 seconds
                await self.calculate_realtime_pnl()
                await self.calculate_portfolio_var_cvar()
                await self.calculate_max_drawdown()
                await self.monitor_vix_and_volatility()
                await self.check_risk_alerts()

                await asyncio.sleep(30)

            except Exception as e:
                self.logger.error(f"Error in risk monitoring loop: {e}")
                await asyncio.sleep(60)

    async def stop_monitoring(self):
        """Stop the risk monitoring."""
        self.running = False
        self.logger.info("Stopped real-time risk monitoring")


# Global instance
risk_engine = None

