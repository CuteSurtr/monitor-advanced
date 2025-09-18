#!/usr/bin/env python3
"""
Risk Analytics Demo - Demonstrates VaR/CVaR calculations and risk monitoring.
"""

import asyncio
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add parent directory to path for imports
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from src.analytics.analytics_engine import AnalyticsEngine
from src.analytics.risk_analytics import RiskAnalytics, RiskMetrics


class MockDatabaseManager:
    """Mock database manager for demonstration."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Generate sample historical data
        self.sample_data = self._generate_sample_data()
    
    def _generate_sample_data(self):
        """Generate sample stock price data."""
        np.random.seed(42)  # For reproducible results
        
        # Simulate 1 year of daily stock prices for 5 assets
        n_days = 252
        assets = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'NVDA']
        
        # Starting prices
        initial_prices = {'AAPL': 150, 'GOOGL': 2500, 'MSFT': 300, 'TSLA': 800, 'NVDA': 200}
        
        data = {}
        
        for asset in assets:
            prices = [initial_prices[asset]]
            
            # Generate returns with different volatilities
            if asset == 'TSLA':
                vol = 0.35  # High volatility
            elif asset == 'NVDA':
                vol = 0.30  # High volatility
            else:
                vol = 0.25  # Moderate volatility
            
            daily_returns = np.random.normal(0.0005, vol/np.sqrt(252), n_days-1)  # Slight positive drift
            
            # Generate price series
            for i, ret in enumerate(daily_returns):
                new_price = prices[-1] * (1 + ret)
                prices.append(new_price)
            
            # Create data records
            dates = [datetime.now() - timedelta(days=n_days-1-i) for i in range(n_days)]
            
            asset_data = []
            for i, (date, price) in enumerate(zip(dates, prices)):
                if i == 0:
                    continue  # Skip first day for open/high/low
                
                # Generate OHLC data
                open_price = prices[i-1]
                high_price = max(open_price, price) * (1 + np.random.uniform(0, 0.02))
                low_price = min(open_price, price) * (1 - np.random.uniform(0, 0.02))
                
                asset_data.append({
                    'symbol': asset,
                    'timestamp': date,
                    'open': open_price,
                    'high': high_price,
                    'low': low_price,
                    'close': price,
                    'volume': np.random.randint(1000000, 10000000)
                })
            
            data[asset] = asset_data
        
        return data
    
    async def get_stock_data(self, symbol, start_time, end_time):
        """Mock get stock data method."""
        if symbol in self.sample_data:
            # Filter by date range
            filtered_data = []
            for record in self.sample_data[symbol]:
                if start_time <= record['timestamp'] <= end_time:
                    filtered_data.append(record)
            return filtered_data
        return []


class MockCacheManager:
    """Mock cache manager for demonstration."""
    
    def __init__(self):
        self._cache = {}
    
    async def get(self, key, default=None):
        return self._cache.get(key, default)
    
    async def set(self, key, value, ttl=None):
        self._cache[key] = value
        return True


async def demonstrate_var_cvar_calculations():
    """Demonstrate VaR and CVaR calculations."""
    logger.info("=== VaR/CVaR Calculation Demonstration ===")
    
    # Setup mock components
    db_manager = MockDatabaseManager()
    cache_manager = MockCacheManager()
    
    # Initialize analytics engine
    analytics_engine = AnalyticsEngine(db_manager, cache_manager)
    
    # Initialize risk analytics
    risk_analytics = RiskAnalytics(db_manager, cache_manager)
    
    # Get sample data for one asset
    symbol = 'AAPL'
    end_time = datetime.now()
    start_time = end_time - timedelta(days=252)
    
    data = await db_manager.get_stock_data(symbol, start_time, end_time)
    
    if not data:
        logger.error("No data available for demonstration")
        return
    
    # Convert to DataFrame and calculate returns
    df = pd.DataFrame(data)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df.set_index('timestamp', inplace=True)
    
    # Calculate returns
    returns = df['close'].pct_change().dropna()
    
    logger.info(f"Analyzing {len(returns)} days of returns for {symbol}")
    logger.info(f"Mean return: {returns.mean():.4f}")
    logger.info(f"Standard deviation: {returns.std():.4f}")
    logger.info(f"Annualized volatility: {returns.std() * np.sqrt(252):.2%}")
    
    # Calculate VaR and CVaR using different methods
    confidence_levels = [0.90, 0.95, 0.99]
    methods = ['historical', 'parametric', 'monte_carlo']
    
    logger.info("\n--- VaR and CVaR Results ---")
    
    for conf_level in confidence_levels:
        logger.info(f"\nConfidence Level: {conf_level:.0%}")
        logger.info("-" * 40)
        
        for method in methods:
            var_cvar = await analytics_engine.calculate_var_cvar(
                returns.values, conf_level, method
            )
            
            logger.info(f"{method.capitalize():12} - VaR: {var_cvar['var']:.2%}, CVaR: {var_cvar['cvar']:.2%}")


async def demonstrate_portfolio_risk():
    """Demonstrate portfolio risk calculations."""
    logger.info("\n=== Portfolio Risk Demonstration ===")
    
    # Setup mock components
    db_manager = MockDatabaseManager()
    cache_manager = MockCacheManager()
    
    # Initialize risk analytics
    risk_analytics = RiskAnalytics(db_manager, cache_manager)
    
    # Create a mock portfolio with returns
    assets = ['AAPL', 'GOOGL', 'MSFT']
    weights = {'AAPL': 0.4, 'GOOGL': 0.35, 'MSFT': 0.25}
    
    # Get historical data for all assets
    end_time = datetime.now()
    start_time = end_time - timedelta(days=252)
    
    asset_returns = {}
    
    for asset in assets:
        data = await db_manager.get_stock_data(asset, start_time, end_time)
        if data:
            df = pd.DataFrame(data)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df.set_index('timestamp', inplace=True)
            
            returns = df['close'].pct_change().dropna()
            asset_returns[asset] = returns
    
    if not asset_returns:
        logger.error("No portfolio data available")
        return
    
    # Calculate portfolio returns
    returns_df = pd.DataFrame(asset_returns)
    weights_array = np.array([weights[asset] for asset in returns_df.columns])
    portfolio_returns = returns_df.dot(weights_array)
    
    logger.info(f"Portfolio composition: {weights}")
    logger.info(f"Portfolio mean return: {portfolio_returns.mean():.4f}")
    logger.info(f"Portfolio volatility: {portfolio_returns.std() * np.sqrt(252):.2%}")
    
    # Calculate comprehensive risk metrics
    analytics_engine = AnalyticsEngine(db_manager, cache_manager)
    
    # VaR/CVaR for portfolio
    var_95 = await analytics_engine.calculate_var_cvar(portfolio_returns.values, 0.95)
    var_99 = await analytics_engine.calculate_var_cvar(portfolio_returns.values, 0.99)
    
    logger.info(f"\nPortfolio VaR (95%): {var_95['var']:.2%}")
    logger.info(f"Portfolio CVaR (95%): {var_95['cvar']:.2%}")
    logger.info(f"Portfolio VaR (99%): {var_99['var']:.2%}")
    logger.info(f"Portfolio CVaR (99%): {var_99['cvar']:.2%}")
    
    # Sharpe ratio
    sharpe = await analytics_engine.calculate_sharpe_ratio(portfolio_returns.to_frame())
    logger.info(f"Sharpe Ratio: {sharpe:.2f}")
    
    # Maximum drawdown
    portfolio_values = (1 + portfolio_returns).cumprod()
    drawdown_metrics = await analytics_engine.calculate_max_drawdown(portfolio_values)
    logger.info(f"Maximum Drawdown: {drawdown_metrics['max_drawdown']:.2%}")
    logger.info(f"Current Drawdown: {drawdown_metrics['current_drawdown']:.2%}")
    
    # Correlation matrix
    correlation_matrix = await analytics_engine.calculate_correlation_matrix(asset_returns)
    logger.info(f"\nCorrelation Matrix:")
    logger.info(correlation_matrix.round(3).to_string())
    
    # Component VaR
    component_vars = await analytics_engine.calculate_component_var(weights, asset_returns)
    logger.info(f"\nComponent VaR:")
    for asset, comp_var in component_vars.items():
        logger.info(f"{asset}: {comp_var:.4f}")


async def demonstrate_stress_testing():
    """Demonstrate stress testing capabilities."""
    logger.info("\n=== Stress Testing Demonstration ===")
    
    # Mock portfolio positions
    positions = [
        {'symbol': 'AAPL', 'market_value': 40000},
        {'symbol': 'GOOGL', 'market_value': 35000},
        {'symbol': 'MSFT', 'market_value': 25000}
    ]
    
    # Define stress scenarios
    stress_scenarios = {
        'Market Crash': {'AAPL': -0.20, 'GOOGL': -0.25, 'MSFT': -0.18},
        'Tech Selloff': {'AAPL': -0.15, 'GOOGL': -0.30, 'MSFT': -0.12},
        'Mild Correction': {'AAPL': -0.10, 'GOOGL': -0.12, 'MSFT': -0.08}
    }
    
    original_value = sum(pos['market_value'] for pos in positions)
    logger.info(f"Original Portfolio Value: ${original_value:,.2f}")
    
    for scenario_name, shocks in stress_scenarios.items():
        logger.info(f"\n--- {scenario_name} Scenario ---")
        
        stressed_value = 0
        detailed_impacts = {}
        
        for position in positions:
            symbol = position['symbol']
            position_value = position['market_value']
            
            if symbol in shocks:
                shock = shocks[symbol]
                stressed_position_value = position_value * (1 + shock)
                impact = stressed_position_value - position_value
                
                detailed_impacts[symbol] = {
                    'original_value': position_value,
                    'shocked_value': stressed_position_value,
                    'impact': impact,
                    'shock_applied': shock
                }
                
                logger.info(f"{symbol}: ${position_value:,.2f} -> ${stressed_position_value:,.2f} (Impact: ${impact:,.2f}, {shock:.1%})")
            else:
                stressed_position_value = position_value
                detailed_impacts[symbol] = {
                    'original_value': position_value,
                    'shocked_value': stressed_position_value,
                    'impact': 0,
                    'shock_applied': 0
                }
            
            stressed_value += stressed_position_value
        
        total_impact = stressed_value - original_value
        impact_percentage = total_impact / original_value
        
        logger.info(f"Stressed Portfolio Value: ${stressed_value:,.2f}")
        logger.info(f"Total Impact: ${total_impact:,.2f} ({impact_percentage:.2%})")


async def demonstrate_volatility_models():
    """Demonstrate different volatility calculation methods."""
    logger.info("\n=== Volatility Models Demonstration ===")
    
    # Setup mock components
    db_manager = MockDatabaseManager()
    cache_manager = MockCacheManager()
    analytics_engine = AnalyticsEngine(db_manager, cache_manager)
    
    symbol = 'TSLA'  # High volatility stock
    end_time = datetime.now()
    start_time = end_time - timedelta(days=252)
    
    data = await db_manager.get_stock_data(symbol, start_time, end_time)
    
    if not data:
        logger.error("No data available for volatility demonstration")
        return
    
    # Convert to returns
    df = pd.DataFrame(data)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df.set_index('timestamp', inplace=True)
    returns = df['close'].pct_change().dropna()
    
    logger.info(f"Analyzing volatility for {symbol}")
    
    # Calculate volatility using different methods
    methods = ['historical', 'ewma', 'garch']
    
    for method in methods:
        vol_metrics = await analytics_engine.calculate_portfolio_volatility(
            returns.to_frame(), method
        )
        
        logger.info(f"{method.upper()} Volatility: {vol_metrics['volatility']:.2%}")


async def main():
    """Main demonstration function."""
    logger.info("Starting Risk Analytics Demonstration")
    logger.info("=" * 60)
    
    try:
        # Run all demonstrations
        await demonstrate_var_cvar_calculations()
        await demonstrate_portfolio_risk()
        await demonstrate_stress_testing()
        await demonstrate_volatility_models()
        
        logger.info("\n" + "=" * 60)
        logger.info("Risk Analytics Demonstration Complete")
        
        # Summary of capabilities
        logger.info("\n--- System Capabilities Summary ---")
        logger.info("[COMPLETE] VaR/CVaR calculation (Historical, Parametric, Monte Carlo)")
        logger.info("[COMPLETE] Multiple volatility models (Historical, EWMA, GARCH)")
        logger.info("[COMPLETE] Portfolio risk metrics (Sharpe ratio, Beta, Drawdown)")
        logger.info("[COMPLETE] Correlation and concentration risk analysis")
        logger.info("[COMPLETE] Component VaR for portfolio optimization")
        logger.info("[COMPLETE] Stress testing with custom scenarios")
        logger.info("[COMPLETE] Real-time risk monitoring and alerting")
        logger.info("[COMPLETE] Multi-asset support (Equities, Forex, Crypto, Commodities)")
        
    except Exception as e:
        logger.error(f"Error in demonstration: {e}", exc_info=True)


if __name__ == "__main__":
    # Run the demonstration
    asyncio.run(main())