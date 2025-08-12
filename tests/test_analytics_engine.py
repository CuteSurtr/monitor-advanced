"""
Test script for the Analytics Engine

This script demonstrates the functionality of the analytics engine
and validates its components.
"""

import asyncio
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from analytics.analytics_engine import AnalyticsEngine
from analytics.technical_indicators import TechnicalAnalyzer
from analytics.correlation_analyzer import CorrelationAnalyzer
from analytics.volatility_analyzer import VolatilityAnalyzer
from analytics.anomaly_detector import AnomalyDetector
from utils.logger import get_logger

logger = get_logger(__name__)


def generate_sample_data(symbol: str, days: int = 252) -> pd.DataFrame:
    """
    Generate sample stock data for testing
    
    Args:
        symbol: Stock symbol
        days: Number of days of data to generate
        
    Returns:
        DataFrame with OHLCV data
    """
    # Generate dates
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    dates = pd.date_range(start=start_date, end=end_date, freq='D')
    
    # Generate price data with some realistic patterns
    np.random.seed(42)  # For reproducible results
    
    # Start with a base price
    base_price = 100.0
    
    # Generate daily returns with some trend and volatility
    returns = np.random.normal(0.0005, 0.02, len(dates))  # Small positive trend
    
    # Add some market cycles
    cycle = np.sin(np.arange(len(dates)) * 2 * np.pi / 252) * 0.01
    returns += cycle
    
    # Calculate prices
    prices = [base_price]
    for ret in returns[1:]:
        prices.append(prices[-1] * (1 + ret))
    
    prices = np.array(prices)
    
    # Generate OHLC data
    data = pd.DataFrame(index=dates)
    data['open'] = prices * (1 + np.random.normal(0, 0.005, len(dates)))
    data['high'] = np.maximum(data['open'], prices) * (1 + np.abs(np.random.normal(0, 0.01, len(dates))))
    data['low'] = np.minimum(data['open'], prices) * (1 - np.abs(np.random.normal(0, 0.01, len(dates))))
    data['close'] = prices
    data['volume'] = np.random.lognormal(10, 0.5, len(dates))
    
    # Ensure OHLC relationships are maintained
    data['high'] = np.maximum(data['high'], np.maximum(data['open'], data['close']))
    data['low'] = np.minimum(data['low'], np.minimum(data['open'], data['close']))
    
    return data


class MockDatabaseManager:
    """Mock database manager for testing"""
    
    async def get_stock_data(self, symbol: str, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """Mock method to return sample data"""
        return generate_sample_data(symbol)


class MockCacheManager:
    """Mock cache manager for testing"""
    
    def __init__(self):
        self.cache = {}
    
    async def get(self, key: str):
        """Mock get method"""
        return self.cache.get(key)
    
    async def set(self, key: str, value, expire: int = None):
        """Mock set method"""
        self.cache[key] = value


async def test_technical_indicators():
    """Test technical indicators calculation"""
    logger.info("Testing Technical Indicators...")
    
    # Generate sample data
    data = generate_sample_data("AAPL", days=100)
    
    # Initialize technical indicators
    ti = TechnicalAnalyzer()
    
    # Test individual indicators
    rsi_result = ti.calculate_rsi(data['close'])
    logger.info(f"RSI calculation successful: {len(rsi_result.values)} values")
    
    macd_result = ti.calculate_macd(data['close'])
    logger.info(f"MACD calculation successful: {len(macd_result.values)} values")
    
    bb_result = ti.calculate_bollinger_bands(data['close'])
    logger.info(f"Bollinger Bands calculation successful: {len(bb_result.values)} values")
    
    # Test all indicators
    all_indicators = ti.calculate_all_indicators(data)
    logger.info(f"All indicators calculated: {len(all_indicators)} indicators")
    
    # Test trading signals
    signals = ti.generate_trading_signals(all_indicators)
    logger.info(f"Trading signals generated: {signals}")
    
    return True


async def test_correlation_analyzer():
    """Test correlation analysis"""
    logger.info("Testing Correlation Analyzer...")
    
    # Generate sample data for multiple symbols
    symbols = ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA"]
    data_dict = {}
    
    for symbol in symbols:
        data_dict[symbol] = generate_sample_data(symbol, days=100)['close']
    
    # Create DataFrame
    data = pd.DataFrame(data_dict)
    
    # Initialize correlation analyzer
    ca = CorrelationAnalyzer()
    
    # Test correlation matrix
    corr_result = ca.calculate_correlation_matrix(data)
    logger.info(f"Correlation matrix calculated: {corr_result.correlation_matrix.shape}")
    
    # Test significant correlations
    if not corr_result.significant_correlations.empty:
        logger.info(f"Found {len(corr_result.significant_correlations)} significant correlations")
    
    # Test rolling correlations
    rolling_corr = ca.analyze_rolling_correlations(data, window=30)
    logger.info(f"Rolling correlations calculated: {len(rolling_corr)} pairs")
    
    return True


async def test_volatility_analyzer():
    """Test volatility analysis"""
    logger.info("Testing Volatility Analyzer...")
    
    # Generate sample data
    data = generate_sample_data("AAPL", days=100)
    
    # Initialize volatility analyzer
    va = VolatilityAnalyzer()
    
    # Test historical volatility
    hist_vol = va.calculate_historical_volatility(data['close'])
    logger.info(f"Historical volatility calculated: {len(hist_vol)} values")
    
    # Test EWMA volatility
    ewma_vol = va.calculate_ewma_volatility(data['close'])
    logger.info(f"EWMA volatility calculated: {len(ewma_vol)} values")
    
    # Test risk metrics
    risk_metrics = va.calculate_comprehensive_risk_metrics(data['close'])
    logger.info(f"Risk metrics calculated: Sharpe={risk_metrics.sharpe_ratio:.3f}, VaR={risk_metrics.var_95:.4f}")
    
    # Test volatility regime analysis
    regime_analysis = va.analyze_volatility_regime(data['close'])
    logger.info(f"Volatility regime analysis completed: {len(regime_analysis)} components")
    
    return True


async def test_anomaly_detector():
    """Test anomaly detection"""
    logger.info("Testing Anomaly Detector...")
    
    # Generate sample data
    data = generate_sample_data("AAPL", days=100)
    
    # Initialize anomaly detector
    ad = AnomalyDetector()
    
    # Test price anomalies
    price_anomalies = ad.detect_price_anomalies(data)
    logger.info(f"Price anomalies detected: {price_anomalies.model_info.get('n_anomalies', 0)}")
    
    # Test volume anomalies
    volume_anomalies = ad.detect_volume_anomalies(data)
    logger.info(f"Volume anomalies detected: {volume_anomalies.model_info.get('n_anomalies', 0)}")
    
    # Test pattern anomalies
    pattern_anomalies = ad.detect_pattern_anomalies(data)
    logger.info(f"Pattern anomalies detected: {pattern_anomalies.model_info.get('n_anomalies', 0)}")
    
    return True


async def test_analytics_engine():
    """Test the main analytics engine"""
    logger.info("Testing Analytics Engine...")
    
    # Initialize mock managers
    db_manager = MockDatabaseManager()
    cache_manager = MockCacheManager()
    
    # Initialize analytics engine
    engine = AnalyticsEngine(db_manager, cache_manager)
    
    # Test single stock analysis
    result = await engine.analyze_stock("AAPL", include_anomaly_detection=True)
    logger.info(f"Single stock analysis completed: {len(result.technical_indicators)} indicators")
    
    # Test portfolio analysis
    symbols = ["AAPL", "GOOGL", "MSFT"]
    portfolio_results = await engine.analyze_portfolio(symbols)
    logger.info(f"Portfolio analysis completed: {len(portfolio_results)} symbols")
    
    # Test market report generation
    report = await engine.generate_market_report(symbols)
    logger.info(f"Market report generated: {len(report)} characters")
    
    return True


async def run_comprehensive_test():
    """Run all tests"""
    logger.info("Starting comprehensive analytics engine test...")
    
    try:
        # Test individual components
        await test_technical_indicators()
        await test_correlation_analyzer()
        await test_volatility_analyzer()
        await test_anomaly_detector()
        
        # Test main engine
        await test_analytics_engine()
        
        logger.info("All tests completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        return False


def main():
    """Main function to run tests"""
    print("=" * 60)
    print("ANALYTICS ENGINE TEST SUITE")
    print("=" * 60)
    
    # Run the tests
    success = asyncio.run(run_comprehensive_test())
    
    if success:
        print("\n✅ All tests passed successfully!")
        print("\nAnalytics Engine Features Tested:")
        print("  • Technical Indicators (RSI, MACD, Bollinger Bands, etc.)")
        print("  • Correlation Analysis")
        print("  • Volatility Analysis and Risk Metrics")
        print("  • Anomaly Detection")
        print("  • Portfolio Analysis")
        print("  • Market Report Generation")
    else:
        print("\n❌ Some tests failed. Check the logs for details.")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main() 