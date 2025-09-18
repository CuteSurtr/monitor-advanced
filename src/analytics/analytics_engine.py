"""
Comprehensive Analytics Engine with advanced risk metrics including VaR/CVaR calculations.
"""

import asyncio
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime, timedelta
from scipy import stats
from scipy.optimize import minimize
import warnings

warnings.filterwarnings("ignore")

from src.utils.logger import get_logger


class AnalyticsEngine:
    """Advanced analytics engine with VaR/CVaR and portfolio risk analysis."""

    def __init__(self, db_manager, cache_manager, config=None):
        self.db_manager = db_manager
        self.cache_manager = cache_manager
        self.config = config
        self.logger = get_logger(__name__)
        self.running = False

        # Risk calculation parameters
        self.confidence_levels = [0.90, 0.95, 0.99]  # 90%, 95%, 99% confidence
        self.lookback_days = 252  # 1 year of trading days
        self.monte_carlo_simulations = 10000

        # Volatility models
        self.volatility_models = ["historical", "ewma", "garch"]

    async def start(self):
        """Start the analytics engine background tasks."""
        self.running = True
        self.logger.info("Starting analytics engine")

        try:
            while self.running:
                await self._run_analytics_cycle()
                await asyncio.sleep(300)  # Run every 5 minutes

        except asyncio.CancelledError:
            self.logger.info("Analytics engine cancelled")
        except Exception as e:
            self.logger.error(f"Error in analytics engine: {e}")
        finally:
            self.running = False

    async def stop(self):
        """Stop the analytics engine."""
        self.running = False
        self.logger.info("Stopping analytics engine")

    async def _run_analytics_cycle(self):
        """Run a complete analytics cycle."""
        try:
            # Get active portfolios from database
            portfolios = await self._get_active_portfolios()

            for portfolio in portfolios:
                await self._analyze_portfolio_risk(portfolio)
                await asyncio.sleep(1)  # Small delay between portfolios

        except Exception as e:
            self.logger.error(f"Error in analytics cycle: {e}")

    async def calculate_var_cvar(
        self,
        returns: np.ndarray,
        confidence_level: float = 0.95,
        method: str = "historical",
    ) -> Dict[str, float]:
        """
        Calculate Value at Risk (VaR) and Conditional Value at Risk (CVaR).

        Args:
            returns: Array of portfolio returns
            confidence_level: Confidence level (0.90, 0.95, 0.99)
            method: 'historical', 'parametric', 'monte_carlo'

        Returns:
            Dictionary with VaR and CVaR values
        """
        if len(returns) < 30:
            return {
                "var": 0,
                "cvar": 0,
                "method": method,
                "confidence": confidence_level,
            }

        try:
            if method == "historical":
                var, cvar = self._historical_var_cvar(returns, confidence_level)
            elif method == "parametric":
                var, cvar = self._parametric_var_cvar(returns, confidence_level)
            elif method == "monte_carlo":
                var, cvar = self._monte_carlo_var_cvar(returns, confidence_level)
            else:
                var, cvar = self._historical_var_cvar(returns, confidence_level)

            return {
                "var": float(var),
                "cvar": float(cvar),
                "method": method,
                "confidence": confidence_level,
                "observations": len(returns),
            }

        except Exception as e:
            self.logger.error(f"Error calculating VaR/CVaR: {e}")
            return {
                "var": 0,
                "cvar": 0,
                "method": method,
                "confidence": confidence_level,
            }

    def _historical_var_cvar(
        self, returns: np.ndarray, confidence_level: float
    ) -> Tuple[float, float]:
        """Calculate VaR and CVaR using historical simulation."""
        alpha = 1 - confidence_level
        sorted_returns = np.sort(returns)

        # VaR is the percentile
        var_index = int(np.ceil(alpha * len(sorted_returns))) - 1
        var = sorted_returns[var_index] if var_index >= 0 else sorted_returns[0]

        # CVaR is the mean of losses beyond VaR
        tail_losses = sorted_returns[sorted_returns <= var]
        cvar = np.mean(tail_losses) if len(tail_losses) > 0 else var

        return abs(var), abs(cvar)

    def _parametric_var_cvar(
        self, returns: np.ndarray, confidence_level: float
    ) -> Tuple[float, float]:
        """Calculate VaR and CVaR using parametric (normal distribution) method."""
        mean_return = np.mean(returns)
        std_return = np.std(returns)

        # Z-score for confidence level
        z_score = stats.norm.ppf(1 - confidence_level)

        # VaR assuming normal distribution
        var = abs(mean_return + z_score * std_return)

        # CVaR for normal distribution
        cvar = abs(
            mean_return - std_return * stats.norm.pdf(z_score) / (1 - confidence_level)
        )

        return var, cvar

    def _monte_carlo_var_cvar(
        self, returns: np.ndarray, confidence_level: float
    ) -> Tuple[float, float]:
        """Calculate VaR and CVaR using Monte Carlo simulation."""
        mean_return = np.mean(returns)
        std_return = np.std(returns)

        # Generate random scenarios
        simulated_returns = np.random.normal(
            mean_return, std_return, self.monte_carlo_simulations
        )

        # Calculate VaR and CVaR from simulated returns
        return self._historical_var_cvar(simulated_returns, confidence_level)

    async def calculate_portfolio_volatility(
        self, portfolio_returns: pd.DataFrame, method: str = "historical"
    ) -> Dict[str, float]:
        """
        Calculate portfolio volatility using different methods.

        Args:
            portfolio_returns: DataFrame with portfolio returns
            method: 'historical', 'ewma', 'garch'

        Returns:
            Volatility metrics
        """
        if portfolio_returns.empty:
            return {"volatility": 0, "method": method}

        try:
            returns = portfolio_returns.values.flatten()

            if method == "historical":
                volatility = np.std(returns) * np.sqrt(252)  # Annualized
            elif method == "ewma":
                volatility = self._ewma_volatility(returns)
            elif method == "garch":
                volatility = self._garch_volatility(returns)
            else:
                volatility = np.std(returns) * np.sqrt(252)

            return {
                "volatility": float(volatility),
                "daily_volatility": float(np.std(returns)),
                "method": method,
                "observations": len(returns),
            }

        except Exception as e:
            self.logger.error(f"Error calculating volatility: {e}")
            return {"volatility": 0, "method": method}

    def _ewma_volatility(
        self, returns: np.ndarray, lambda_param: float = 0.94
    ) -> float:
        """Calculate EWMA (Exponentially Weighted Moving Average) volatility."""
        squared_returns = returns**2
        weights = np.array([(lambda_param**i) for i in range(len(returns))][::-1])
        weights = weights / weights.sum()

        ewma_variance = np.sum(weights * squared_returns)
        return np.sqrt(ewma_variance * 252)  # Annualized

    def _garch_volatility(self, returns: np.ndarray) -> float:
        """Simple GARCH(1,1) volatility estimation."""
        try:
            # Simple GARCH(1,1) parameters (in practice, use arch library)
            # This is a simplified version
            mean_return = np.mean(returns)
            squared_residuals = (returns - mean_return) ** 2

            # Long-term variance
            long_term_var = np.mean(squared_residuals)

            # GARCH parameters (simplified)
            alpha = 0.1  # ARCH term
            beta = 0.85  # GARCH term
            omega = long_term_var * (1 - alpha - beta)

            # Calculate conditional variance
            conditional_var = np.zeros(len(returns))
            conditional_var[0] = long_term_var

            for i in range(1, len(returns)):
                conditional_var[i] = (
                    omega
                    + alpha * squared_residuals[i - 1]
                    + beta * conditional_var[i - 1]
                )

            return np.sqrt(conditional_var[-1] * 252)  # Annualized current volatility

        except Exception:
            # Fallback to historical volatility
            return np.std(returns) * np.sqrt(252)

    async def calculate_portfolio_beta(
        self, portfolio_returns: pd.DataFrame, market_returns: pd.DataFrame
    ) -> float:
        """Calculate portfolio beta relative to market."""
        try:
            if portfolio_returns.empty or market_returns.empty:
                return 1.0

            # Align data
            common_index = portfolio_returns.index.intersection(market_returns.index)
            if len(common_index) < 30:
                return 1.0

            port_ret = portfolio_returns.loc[common_index].values.flatten()
            market_ret = market_returns.loc[common_index].values.flatten()

            # Calculate beta using covariance
            covariance = np.cov(port_ret, market_ret)[0, 1]
            market_variance = np.var(market_ret)

            beta = covariance / market_variance if market_variance != 0 else 1.0
            return float(beta)

        except Exception as e:
            self.logger.error(f"Error calculating beta: {e}")
            return 1.0

    async def calculate_sharpe_ratio(
        self, portfolio_returns: pd.DataFrame, risk_free_rate: float = 0.02
    ) -> float:
        """Calculate Sharpe ratio."""
        try:
            if portfolio_returns.empty:
                return 0.0

            returns = portfolio_returns.values.flatten()
            mean_return = np.mean(returns) * 252  # Annualized
            volatility = np.std(returns) * np.sqrt(252)  # Annualized

            sharpe_ratio = (
                (mean_return - risk_free_rate) / volatility if volatility != 0 else 0
            )
            return float(sharpe_ratio)

        except Exception as e:
            self.logger.error(f"Error calculating Sharpe ratio: {e}")
            return 0.0

    async def calculate_max_drawdown(
        self, portfolio_values: pd.Series
    ) -> Dict[str, Any]:
        """Calculate maximum drawdown and related metrics."""
        try:
            if portfolio_values.empty:
                return {"max_drawdown": 0, "current_drawdown": 0, "recovery_days": 0}

            # Calculate running maximum (peak)
            running_max = portfolio_values.expanding().max()

            # Calculate drawdown
            drawdown = (portfolio_values - running_max) / running_max

            # Maximum drawdown
            max_drawdown = drawdown.min()

            # Current drawdown
            current_drawdown = drawdown.iloc[-1]

            # Days to recovery (simplified)
            max_dd_date = drawdown.idxmin()
            recovery_days = 0
            if max_dd_date in drawdown.index:
                recovery_mask = drawdown.loc[max_dd_date:] >= 0
                if recovery_mask.any():
                    recovery_date = drawdown.loc[max_dd_date:][recovery_mask].index[0]
                    recovery_days = (recovery_date - max_dd_date).days

            return {
                "max_drawdown": float(abs(max_drawdown)),
                "current_drawdown": float(abs(current_drawdown)),
                "max_drawdown_date": (
                    max_dd_date.isoformat()
                    if hasattr(max_dd_date, "isoformat")
                    else str(max_dd_date)
                ),
                "recovery_days": int(recovery_days),
            }

        except Exception as e:
            self.logger.error(f"Error calculating max drawdown: {e}")
            return {"max_drawdown": 0, "current_drawdown": 0, "recovery_days": 0}

    async def calculate_correlation_matrix(
        self, asset_returns: Dict[str, pd.Series]
    ) -> pd.DataFrame:
        """Calculate correlation matrix between assets."""
        try:
            if not asset_returns:
                return pd.DataFrame()

            # Create DataFrame from asset returns
            returns_df = pd.DataFrame(asset_returns)

            # Calculate correlation matrix
            correlation_matrix = returns_df.corr()

            return correlation_matrix

        except Exception as e:
            self.logger.error(f"Error calculating correlation matrix: {e}")
            return pd.DataFrame()

    async def calculate_component_var(
        self,
        portfolio_weights: Dict[str, float],
        asset_returns: Dict[str, pd.Series],
        confidence_level: float = 0.95,
    ) -> Dict[str, float]:
        """Calculate component VaR for portfolio positions."""
        try:
            if not portfolio_weights or not asset_returns:
                return {}

            # Create returns matrix
            returns_df = pd.DataFrame(asset_returns)

            # Portfolio returns
            weights_array = np.array(
                [portfolio_weights.get(asset, 0) for asset in returns_df.columns]
            )
            portfolio_returns = returns_df.dot(weights_array)

            # Calculate portfolio VaR
            portfolio_var = await self.calculate_var_cvar(
                portfolio_returns.values, confidence_level
            )
            portfolio_var_value = portfolio_var["var"]

            # Calculate marginal VaR for each asset
            component_vars = {}
            for asset in returns_df.columns:
                if asset in portfolio_weights:
                    # Calculate marginal contribution
                    marginal_var = self._calculate_marginal_var(
                        returns_df, weights_array, asset, confidence_level
                    )
                    component_var = portfolio_weights[asset] * marginal_var
                    component_vars[asset] = float(component_var)

            return component_vars

        except Exception as e:
            self.logger.error(f"Error calculating component VaR: {e}")
            return {}

    def _calculate_marginal_var(
        self,
        returns_df: pd.DataFrame,
        weights: np.ndarray,
        asset: str,
        confidence_level: float,
    ) -> float:
        """Calculate marginal VaR for a specific asset."""
        try:
            # This is a simplified marginal VaR calculation
            # In practice, you'd use more sophisticated numerical methods

            asset_index = list(returns_df.columns).index(asset)
            portfolio_returns = returns_df.dot(weights)
            asset_returns = returns_df[asset]

            # Calculate correlation with portfolio
            correlation = portfolio_returns.corr(asset_returns)

            # Marginal VaR approximation
            portfolio_volatility = portfolio_returns.std()
            asset_volatility = asset_returns.std()

            # Z-score for confidence level
            z_score = abs(stats.norm.ppf(1 - confidence_level))

            marginal_var = z_score * correlation * asset_volatility

            return float(marginal_var)

        except Exception:
            return 0.0

    async def _analyze_portfolio_risk(self, portfolio: Dict[str, Any]):
        """Analyze risk for a specific portfolio."""
        try:
            portfolio_id = portfolio.get("id")
            if not portfolio_id:
                return

            # Get portfolio data
            positions = await self._get_portfolio_positions(portfolio_id)
            if not positions:
                return

            # Get historical returns
            asset_returns = await self._get_portfolio_returns(positions)
            if not asset_returns:
                return

            # Calculate portfolio weights
            weights = await self._calculate_portfolio_weights(positions)

            # Calculate portfolio returns
            portfolio_returns = await self._calculate_portfolio_returns(
                asset_returns, weights
            )

            # Calculate risk metrics
            risk_metrics = await self._calculate_comprehensive_risk_metrics(
                portfolio_returns, asset_returns, weights
            )

            # Cache results
            await self.cache_manager.set(
                f"portfolio_risk:{portfolio_id}", risk_metrics, ttl=300  # 5 minutes
            )

            self.logger.debug(f"Analyzed risk for portfolio {portfolio_id}")

        except Exception as e:
            self.logger.error(f"Error analyzing portfolio risk: {e}")

    async def _calculate_comprehensive_risk_metrics(
        self,
        portfolio_returns: pd.Series,
        asset_returns: Dict[str, pd.Series],
        weights: Dict[str, float],
    ) -> Dict[str, Any]:
        """Calculate comprehensive risk metrics for a portfolio."""
        metrics = {}

        try:
            # VaR and CVaR at multiple confidence levels
            for conf_level in self.confidence_levels:
                for method in ["historical", "parametric", "monte_carlo"]:
                    var_cvar = await self.calculate_var_cvar(
                        portfolio_returns.values, conf_level, method
                    )
                    metrics[f"var_{int(conf_level*100)}_{method}"] = var_cvar["var"]
                    metrics[f"cvar_{int(conf_level*100)}_{method}"] = var_cvar["cvar"]

            # Volatility metrics
            for method in self.volatility_models:
                vol_metrics = await self.calculate_portfolio_volatility(
                    portfolio_returns.to_frame(), method
                )
                metrics[f"volatility_{method}"] = vol_metrics["volatility"]

            # Sharpe ratio
            metrics["sharpe_ratio"] = await self.calculate_sharpe_ratio(
                portfolio_returns.to_frame()
            )

            # Maximum drawdown
            portfolio_values = (1 + portfolio_returns).cumprod()
            drawdown_metrics = await self.calculate_max_drawdown(portfolio_values)
            metrics.update(drawdown_metrics)

            # Component VaR
            component_vars = await self.calculate_component_var(weights, asset_returns)
            metrics["component_var"] = component_vars

            # Correlation analysis
            correlation_matrix = await self.calculate_correlation_matrix(asset_returns)
            metrics["correlation_matrix"] = (
                correlation_matrix.to_dict() if not correlation_matrix.empty else {}
            )

            # Additional metrics
            metrics["portfolio_return_mean"] = float(portfolio_returns.mean())
            metrics["portfolio_return_std"] = float(portfolio_returns.std())
            metrics["skewness"] = (
                float(portfolio_returns.skew()) if len(portfolio_returns) > 3 else 0
            )
            metrics["kurtosis"] = (
                float(portfolio_returns.kurtosis()) if len(portfolio_returns) > 4 else 0
            )
            metrics["calculation_timestamp"] = datetime.now().isoformat()

            return metrics

        except Exception as e:
            self.logger.error(f"Error calculating comprehensive risk metrics: {e}")
            return metrics

    async def _get_active_portfolios(self) -> List[Dict[str, Any]]:
        """Get active portfolios from database."""
        try:
            # This would query your portfolio table
            # For now, return empty list as portfolio structure needs to be established
            return []
        except Exception as e:
            self.logger.error(f"Error getting active portfolios: {e}")
            return []

    async def _get_portfolio_positions(self, portfolio_id: int) -> List[Dict[str, Any]]:
        """Get positions for a portfolio."""
        try:
            # This would query your portfolio positions
            return []
        except Exception as e:
            self.logger.error(f"Error getting portfolio positions: {e}")
            return []

    async def _get_portfolio_returns(
        self, positions: List[Dict[str, Any]]
    ) -> Dict[str, pd.Series]:
        """Get historical returns for portfolio assets."""
        try:
            asset_returns = {}
            end_time = datetime.now()
            start_time = end_time - timedelta(days=self.lookback_days)

            for position in positions:
                symbol = position.get("symbol")
                if symbol:
                    # Get historical data from database
                    data = await self.db_manager.get_stock_data(
                        symbol, start_time, end_time
                    )
                    if data:
                        df = pd.DataFrame(data)
                        df["timestamp"] = pd.to_datetime(df["timestamp"])
                        df.set_index("timestamp", inplace=True)

                        # Calculate returns
                        returns = df["close"].pct_change().dropna()
                        asset_returns[symbol] = returns

            return asset_returns

        except Exception as e:
            self.logger.error(f"Error getting portfolio returns: {e}")
            return {}

    async def _calculate_portfolio_weights(
        self, positions: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """Calculate portfolio weights from positions."""
        try:
            weights = {}
            total_value = sum(pos.get("market_value", 0) for pos in positions)

            if total_value > 0:
                for position in positions:
                    symbol = position.get("symbol")
                    market_value = position.get("market_value", 0)
                    weights[symbol] = market_value / total_value

            return weights

        except Exception as e:
            self.logger.error(f"Error calculating portfolio weights: {e}")
            return {}

    async def _calculate_portfolio_returns(
        self, asset_returns: Dict[str, pd.Series], weights: Dict[str, float]
    ) -> pd.Series:
        """Calculate portfolio returns from asset returns and weights."""
        try:
            if not asset_returns or not weights:
                return pd.Series()

            # Create returns DataFrame
            returns_df = pd.DataFrame(asset_returns)

            # Create weights array
            weights_array = np.array(
                [weights.get(asset, 0) for asset in returns_df.columns]
            )

            # Calculate portfolio returns
            portfolio_returns = returns_df.dot(weights_array)

            return portfolio_returns

        except Exception as e:
            self.logger.error(f"Error calculating portfolio returns: {e}")
            return pd.Series()

    def analyze(self, data):
        """Legacy method for backward compatibility."""
        return {"analysis": "comprehensive_risk", "result": "use async methods"}

    def is_healthy(self) -> bool:
        """Check if the analytics engine is healthy."""
        return self.running
