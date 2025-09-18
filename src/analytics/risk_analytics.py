"""
Risk Analytics API - Advanced risk metrics calculations for portfolio management.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from src.utils.logger import get_logger
from src.analytics.analytics_engine import AnalyticsEngine


class RiskMethod(Enum):
    """Risk calculation methods."""

    HISTORICAL = "historical"
    PARAMETRIC = "parametric"
    MONTE_CARLO = "monte_carlo"


class VolatilityMethod(Enum):
    """Volatility calculation methods."""

    HISTORICAL = "historical"
    EWMA = "ewma"
    GARCH = "garch"


@dataclass
class RiskMetrics:
    """Risk metrics data structure."""

    var_95_historical: float = 0.0
    var_95_parametric: float = 0.0
    var_95_monte_carlo: float = 0.0
    var_99_historical: float = 0.0
    var_99_parametric: float = 0.0
    var_99_monte_carlo: float = 0.0
    cvar_95_historical: float = 0.0
    cvar_95_parametric: float = 0.0
    cvar_95_monte_carlo: float = 0.0
    cvar_99_historical: float = 0.0
    cvar_99_parametric: float = 0.0
    cvar_99_monte_carlo: float = 0.0
    volatility: float = 0.0
    volatility_ewma: float = 0.0
    volatility_garch: float = 0.0
    sharpe_ratio: float = 0.0
    max_drawdown: float = 0.0
    current_drawdown: float = 0.0
    beta: float = 1.0
    correlation_matrix: Dict[str, Dict[str, float]] = None
    component_var: Dict[str, float] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.correlation_matrix is None:
            self.correlation_matrix = {}
        if self.component_var is None:
            self.component_var = {}
        if self.timestamp is None:
            self.timestamp = datetime.now()


class RiskAnalytics:
    """High-level risk analytics interface."""

    def __init__(self, db_manager, cache_manager, config=None):
        self.db_manager = db_manager
        self.cache_manager = cache_manager
        self.config = config
        self.logger = get_logger(__name__)
        self.analytics_engine = AnalyticsEngine(db_manager, cache_manager, config)

    async def calculate_portfolio_risk(
        self,
        portfolio_id: int,
        lookback_days: int = 252,
        confidence_levels: List[float] = None,
    ) -> RiskMetrics:
        """
        Calculate comprehensive risk metrics for a portfolio.

        Args:
            portfolio_id: Portfolio identifier
            lookback_days: Historical data lookback period
            confidence_levels: VaR confidence levels (default: [0.95, 0.99])

        Returns:
            RiskMetrics object with all calculated metrics
        """
        if confidence_levels is None:
            confidence_levels = [0.95, 0.99]

        try:
            # Check cache first
            cache_key = f"portfolio_risk_comprehensive:{portfolio_id}"
            cached_metrics = await self.cache_manager.get(cache_key)
            if cached_metrics:
                # Check if cache is recent (within 5 minutes)
                cache_time = datetime.fromisoformat(cached_metrics.get("timestamp", ""))
                if datetime.now() - cache_time < timedelta(minutes=5):
                    return self._dict_to_risk_metrics(cached_metrics)

            # Get portfolio data
            positions = await self._get_portfolio_positions(portfolio_id)
            if not positions:
                return RiskMetrics()

            # Get historical returns
            asset_returns = await self._get_portfolio_historical_data(
                positions, lookback_days
            )
            if not asset_returns:
                return RiskMetrics()

            # Calculate portfolio weights and returns
            weights = await self._calculate_portfolio_weights(positions)
            portfolio_returns = await self._calculate_portfolio_returns(
                asset_returns, weights
            )

            if portfolio_returns.empty:
                return RiskMetrics()

            # Calculate all risk metrics
            risk_metrics = await self._calculate_all_risk_metrics(
                portfolio_returns, asset_returns, weights, confidence_levels
            )

            # Cache results
            metrics_dict = self._risk_metrics_to_dict(risk_metrics)
            await self.cache_manager.set(cache_key, metrics_dict, ttl=300)

            return risk_metrics

        except Exception as e:
            self.logger.error(
                f"Error calculating portfolio risk for {portfolio_id}: {e}"
            )
            return RiskMetrics()

    async def calculate_asset_risk(
        self,
        symbol: str,
        lookback_days: int = 252,
        confidence_levels: List[float] = None,
    ) -> Dict[str, Any]:
        """
        Calculate risk metrics for a single asset.

        Args:
            symbol: Asset symbol
            lookback_days: Historical data lookback period
            confidence_levels: VaR confidence levels

        Returns:
            Dictionary with risk metrics
        """
        if confidence_levels is None:
            confidence_levels = [0.95, 0.99]

        try:
            # Get historical data
            end_time = datetime.now()
            start_time = end_time - timedelta(days=lookback_days)

            # Try different data sources based on symbol format
            data = None
            if symbol.endswith("=X"):  # Forex
                data = await self.db_manager.get_forex_data(
                    symbol, start_time, end_time
                )
            elif "-USD" in symbol:  # Crypto
                data = await self.db_manager.get_crypto_data(
                    symbol, start_time, end_time
                )
            elif "=F" in symbol:  # Commodities
                data = await self.db_manager.get_commodity_data(
                    symbol, start_time, end_time
                )
            else:  # Stocks
                data = await self.db_manager.get_stock_data(
                    symbol, start_time, end_time
                )

            if not data:
                return {}

            # Convert to DataFrame and calculate returns
            df = pd.DataFrame(data)
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            df.set_index("timestamp", inplace=True)

            # Get price column (different for different asset types)
            if "close" in df.columns:
                price_col = "close"
            elif "price" in df.columns:
                price_col = "price"
            elif "rate" in df.columns:
                price_col = "rate"
            else:
                return {}

            returns = df[price_col].pct_change().dropna()

            if len(returns) < 30:
                return {}

            # Calculate risk metrics
            risk_metrics = {}

            # VaR and CVaR for all confidence levels and methods
            for conf_level in confidence_levels:
                for method in ["historical", "parametric", "monte_carlo"]:
                    var_cvar = await self.analytics_engine.calculate_var_cvar(
                        returns.values, conf_level, method
                    )
                    risk_metrics[f"var_{int(conf_level*100)}_{method}"] = var_cvar[
                        "var"
                    ]
                    risk_metrics[f"cvar_{int(conf_level*100)}_{method}"] = var_cvar[
                        "cvar"
                    ]

            # Volatility metrics
            for method in ["historical", "ewma", "garch"]:
                vol_metrics = (
                    await self.analytics_engine.calculate_portfolio_volatility(
                        returns.to_frame(), method
                    )
                )
                risk_metrics[f"volatility_{method}"] = vol_metrics["volatility"]

            # Sharpe ratio
            risk_metrics["sharpe_ratio"] = (
                await self.analytics_engine.calculate_sharpe_ratio(returns.to_frame())
            )

            # Maximum drawdown
            values = (1 + returns).cumprod()
            drawdown_metrics = await self.analytics_engine.calculate_max_drawdown(
                values
            )
            risk_metrics.update(drawdown_metrics)

            # Basic statistics
            risk_metrics.update(
                {
                    "mean_return": float(returns.mean()),
                    "std_return": float(returns.std()),
                    "skewness": float(returns.skew()) if len(returns) > 3 else 0,
                    "kurtosis": float(returns.kurtosis()) if len(returns) > 4 else 0,
                    "observations": len(returns),
                    "symbol": symbol,
                    "timestamp": datetime.now().isoformat(),
                }
            )

            return risk_metrics

        except Exception as e:
            self.logger.error(f"Error calculating asset risk for {symbol}: {e}")
            return {}

    async def calculate_portfolio_correlation_matrix(
        self, portfolio_id: int, lookback_days: int = 252
    ) -> pd.DataFrame:
        """Calculate correlation matrix for portfolio assets."""
        try:
            positions = await self._get_portfolio_positions(portfolio_id)
            if not positions:
                return pd.DataFrame()

            asset_returns = await self._get_portfolio_historical_data(
                positions, lookback_days
            )

            return await self.analytics_engine.calculate_correlation_matrix(
                asset_returns
            )

        except Exception as e:
            self.logger.error(f"Error calculating correlation matrix: {e}")
            return pd.DataFrame()

    async def calculate_stress_test(
        self, portfolio_id: int, shock_scenarios: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Calculate portfolio impact under stress scenarios.

        Args:
            portfolio_id: Portfolio identifier
            shock_scenarios: Dict of asset -> shock percentage (e.g., {'AAPL': -0.20})

        Returns:
            Stress test results
        """
        try:
            positions = await self._get_portfolio_positions(portfolio_id)
            if not positions:
                return {}

            # Calculate current portfolio value
            current_value = sum(pos.get("market_value", 0) for pos in positions)

            # Apply shocks
            stressed_value = 0
            detailed_impacts = {}

            for position in positions:
                symbol = position.get("symbol")
                position_value = position.get("market_value", 0)

                if symbol in shock_scenarios:
                    shock = shock_scenarios[symbol]
                    stressed_position_value = position_value * (1 + shock)
                    detailed_impacts[symbol] = {
                        "original_value": position_value,
                        "shocked_value": stressed_position_value,
                        "impact": stressed_position_value - position_value,
                        "shock_applied": shock,
                    }
                else:
                    stressed_position_value = position_value
                    detailed_impacts[symbol] = {
                        "original_value": position_value,
                        "shocked_value": stressed_position_value,
                        "impact": 0,
                        "shock_applied": 0,
                    }

                stressed_value += stressed_position_value

            total_impact = stressed_value - current_value
            impact_percentage = (
                (total_impact / current_value) if current_value > 0 else 0
            )

            return {
                "original_portfolio_value": current_value,
                "stressed_portfolio_value": stressed_value,
                "total_impact": total_impact,
                "impact_percentage": impact_percentage,
                "detailed_impacts": detailed_impacts,
                "shock_scenarios": shock_scenarios,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            self.logger.error(f"Error calculating stress test: {e}")
            return {}

    async def get_risk_dashboard_data(self, portfolio_id: int) -> Dict[str, Any]:
        """Get comprehensive risk dashboard data for a portfolio."""
        try:
            # Get basic risk metrics
            risk_metrics = await self.calculate_portfolio_risk(portfolio_id)

            # Get correlation matrix
            correlation_matrix = await self.calculate_portfolio_correlation_matrix(
                portfolio_id
            )

            # Get positions for context
            positions = await self._get_portfolio_positions(portfolio_id)

            # Create dashboard data
            dashboard_data = {
                "portfolio_id": portfolio_id,
                "risk_metrics": self._risk_metrics_to_dict(risk_metrics),
                "correlation_matrix": (
                    correlation_matrix.to_dict() if not correlation_matrix.empty else {}
                ),
                "positions_count": len(positions),
                "total_value": sum(pos.get("market_value", 0) for pos in positions),
                "top_positions": sorted(
                    positions, key=lambda x: x.get("market_value", 0), reverse=True
                )[:10],
                "risk_alerts": await self._generate_risk_alerts(risk_metrics),
                "timestamp": datetime.now().isoformat(),
            }

            return dashboard_data

        except Exception as e:
            self.logger.error(f"Error getting risk dashboard data: {e}")
            return {}

    async def _calculate_all_risk_metrics(
        self,
        portfolio_returns: pd.Series,
        asset_returns: Dict[str, pd.Series],
        weights: Dict[str, float],
        confidence_levels: List[float],
    ) -> RiskMetrics:
        """Calculate all risk metrics and return RiskMetrics object."""
        metrics = RiskMetrics()

        try:
            # VaR and CVaR calculations
            var_cvar_95_hist = await self.analytics_engine.calculate_var_cvar(
                portfolio_returns.values, 0.95, "historical"
            )
            metrics.var_95_historical = var_cvar_95_hist["var"]
            metrics.cvar_95_historical = var_cvar_95_hist["cvar"]

            var_cvar_95_param = await self.analytics_engine.calculate_var_cvar(
                portfolio_returns.values, 0.95, "parametric"
            )
            metrics.var_95_parametric = var_cvar_95_param["var"]
            metrics.cvar_95_parametric = var_cvar_95_param["cvar"]

            var_cvar_95_mc = await self.analytics_engine.calculate_var_cvar(
                portfolio_returns.values, 0.95, "monte_carlo"
            )
            metrics.var_95_monte_carlo = var_cvar_95_mc["var"]
            metrics.cvar_95_monte_carlo = var_cvar_95_mc["cvar"]

            var_cvar_99_hist = await self.analytics_engine.calculate_var_cvar(
                portfolio_returns.values, 0.99, "historical"
            )
            metrics.var_99_historical = var_cvar_99_hist["var"]
            metrics.cvar_99_historical = var_cvar_99_hist["cvar"]

            var_cvar_99_param = await self.analytics_engine.calculate_var_cvar(
                portfolio_returns.values, 0.99, "parametric"
            )
            metrics.var_99_parametric = var_cvar_99_param["var"]
            metrics.cvar_99_parametric = var_cvar_99_param["cvar"]

            var_cvar_99_mc = await self.analytics_engine.calculate_var_cvar(
                portfolio_returns.values, 0.99, "monte_carlo"
            )
            metrics.var_99_monte_carlo = var_cvar_99_mc["var"]
            metrics.cvar_99_monte_carlo = var_cvar_99_mc["cvar"]

            # Volatility metrics
            vol_hist = await self.analytics_engine.calculate_portfolio_volatility(
                portfolio_returns.to_frame(), "historical"
            )
            metrics.volatility = vol_hist["volatility"]

            vol_ewma = await self.analytics_engine.calculate_portfolio_volatility(
                portfolio_returns.to_frame(), "ewma"
            )
            metrics.volatility_ewma = vol_ewma["volatility"]

            vol_garch = await self.analytics_engine.calculate_portfolio_volatility(
                portfolio_returns.to_frame(), "garch"
            )
            metrics.volatility_garch = vol_garch["volatility"]

            # Sharpe ratio
            metrics.sharpe_ratio = await self.analytics_engine.calculate_sharpe_ratio(
                portfolio_returns.to_frame()
            )

            # Maximum drawdown
            portfolio_values = (1 + portfolio_returns).cumprod()
            drawdown_metrics = await self.analytics_engine.calculate_max_drawdown(
                portfolio_values
            )
            metrics.max_drawdown = drawdown_metrics["max_drawdown"]
            metrics.current_drawdown = drawdown_metrics["current_drawdown"]

            # Component VaR
            metrics.component_var = await self.analytics_engine.calculate_component_var(
                weights, asset_returns
            )

            # Correlation matrix
            correlation_matrix = (
                await self.analytics_engine.calculate_correlation_matrix(asset_returns)
            )
            metrics.correlation_matrix = (
                correlation_matrix.to_dict() if not correlation_matrix.empty else {}
            )

            # Beta (if market data available)
            # metrics.beta = await self.analytics_engine.calculate_portfolio_beta(
            #     portfolio_returns.to_frame(), market_returns
            # )

            return metrics

        except Exception as e:
            self.logger.error(f"Error calculating comprehensive risk metrics: {e}")
            return metrics

    async def _generate_risk_alerts(
        self, risk_metrics: RiskMetrics
    ) -> List[Dict[str, Any]]:
        """Generate risk alerts based on thresholds."""
        alerts = []

        try:
            # VaR alerts
            if risk_metrics.var_95_historical > 0.05:  # 5% daily VaR threshold
                alerts.append(
                    {
                        "type": "high_var",
                        "level": "warning",
                        "message": f"High VaR detected: {risk_metrics.var_95_historical:.2%} (95% confidence)",
                        "value": risk_metrics.var_95_historical,
                    }
                )

            # Volatility alerts
            if risk_metrics.volatility > 0.30:  # 30% annual volatility threshold
                alerts.append(
                    {
                        "type": "high_volatility",
                        "level": "warning",
                        "message": f"High volatility detected: {risk_metrics.volatility:.2%}",
                        "value": risk_metrics.volatility,
                    }
                )

            # Drawdown alerts
            if risk_metrics.current_drawdown > 0.10:  # 10% drawdown threshold
                alerts.append(
                    {
                        "type": "high_drawdown",
                        "level": "error",
                        "message": f"High current drawdown: {risk_metrics.current_drawdown:.2%}",
                        "value": risk_metrics.current_drawdown,
                    }
                )

            # Sharpe ratio alerts
            if risk_metrics.sharpe_ratio < 0.5:
                alerts.append(
                    {
                        "type": "low_sharpe",
                        "level": "info",
                        "message": f"Low Sharpe ratio: {risk_metrics.sharpe_ratio:.2f}",
                        "value": risk_metrics.sharpe_ratio,
                    }
                )

            return alerts

        except Exception as e:
            self.logger.error(f"Error generating risk alerts: {e}")
            return []

    # Helper methods for data access (these would be implemented based on your database structure)
    async def _get_portfolio_positions(self, portfolio_id: int) -> List[Dict[str, Any]]:
        """Get portfolio positions from database."""
        try:
            # This would query your portfolio_positions table
            # For now, return empty list
            return []
        except Exception as e:
            self.logger.error(f"Error getting portfolio positions: {e}")
            return []

    async def _get_portfolio_historical_data(
        self, positions: List[Dict[str, Any]], lookback_days: int
    ) -> Dict[str, pd.Series]:
        """Get historical return data for portfolio assets."""
        return await self.analytics_engine._get_portfolio_returns(positions)

    async def _calculate_portfolio_weights(
        self, positions: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """Calculate portfolio weights from positions."""
        return await self.analytics_engine._calculate_portfolio_weights(positions)

    async def _calculate_portfolio_returns(
        self, asset_returns: Dict[str, pd.Series], weights: Dict[str, float]
    ) -> pd.Series:
        """Calculate portfolio returns from asset returns and weights."""
        return await self.analytics_engine._calculate_portfolio_returns(
            asset_returns, weights
        )

    def _risk_metrics_to_dict(self, risk_metrics: RiskMetrics) -> Dict[str, Any]:
        """Convert RiskMetrics object to dictionary."""
        return {
            "var_95_historical": risk_metrics.var_95_historical,
            "var_95_parametric": risk_metrics.var_95_parametric,
            "var_95_monte_carlo": risk_metrics.var_95_monte_carlo,
            "var_99_historical": risk_metrics.var_99_historical,
            "var_99_parametric": risk_metrics.var_99_parametric,
            "var_99_monte_carlo": risk_metrics.var_99_monte_carlo,
            "cvar_95_historical": risk_metrics.cvar_95_historical,
            "cvar_95_parametric": risk_metrics.cvar_95_parametric,
            "cvar_95_monte_carlo": risk_metrics.cvar_95_monte_carlo,
            "cvar_99_historical": risk_metrics.cvar_99_historical,
            "cvar_99_parametric": risk_metrics.cvar_99_parametric,
            "cvar_99_monte_carlo": risk_metrics.cvar_99_monte_carlo,
            "volatility": risk_metrics.volatility,
            "volatility_ewma": risk_metrics.volatility_ewma,
            "volatility_garch": risk_metrics.volatility_garch,
            "sharpe_ratio": risk_metrics.sharpe_ratio,
            "max_drawdown": risk_metrics.max_drawdown,
            "current_drawdown": risk_metrics.current_drawdown,
            "beta": risk_metrics.beta,
            "correlation_matrix": risk_metrics.correlation_matrix,
            "component_var": risk_metrics.component_var,
            "timestamp": risk_metrics.timestamp.isoformat(),
        }

    def _dict_to_risk_metrics(self, data: Dict[str, Any]) -> RiskMetrics:
        """Convert dictionary to RiskMetrics object."""
        return RiskMetrics(
            var_95_historical=data.get("var_95_historical", 0),
            var_95_parametric=data.get("var_95_parametric", 0),
            var_95_monte_carlo=data.get("var_95_monte_carlo", 0),
            var_99_historical=data.get("var_99_historical", 0),
            var_99_parametric=data.get("var_99_parametric", 0),
            var_99_monte_carlo=data.get("var_99_monte_carlo", 0),
            cvar_95_historical=data.get("cvar_95_historical", 0),
            cvar_95_parametric=data.get("cvar_95_parametric", 0),
            cvar_95_monte_carlo=data.get("cvar_95_monte_carlo", 0),
            cvar_99_historical=data.get("cvar_99_historical", 0),
            cvar_99_parametric=data.get("cvar_99_parametric", 0),
            cvar_99_monte_carlo=data.get("cvar_99_monte_carlo", 0),
            volatility=data.get("volatility", 0),
            volatility_ewma=data.get("volatility_ewma", 0),
            volatility_garch=data.get("volatility_garch", 0),
            sharpe_ratio=data.get("sharpe_ratio", 0),
            max_drawdown=data.get("max_drawdown", 0),
            current_drawdown=data.get("current_drawdown", 0),
            beta=data.get("beta", 1),
            correlation_matrix=data.get("correlation_matrix", {}),
            component_var=data.get("component_var", {}),
            timestamp=datetime.fromisoformat(
                data.get("timestamp", datetime.now().isoformat())
            ),
        )
