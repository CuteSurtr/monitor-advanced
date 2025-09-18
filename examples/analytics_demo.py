"""
Analytics Engine Demo

This script demonstrates how to use the analytics engine for real-world
stock market analysis scenarios.
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
from analytics.technical_indicators import TechnicalIndicators
from analytics.correlation_analyzer import CorrelationAnalyzer
from analytics.volatility_analyzer import VolatilityAnalyzer
from analytics.anomaly_detector import AnomalyDetector
from utils.logger import get_logger

logger = get_logger(__name__)


def generate_realistic_data(symbol: str, days: int = 252) -> pd.DataFrame:
    """
    Generate realistic stock data with market patterns
    
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
    
    # Different patterns for different symbols
    if symbol == "AAPL":
        # Apple-like pattern: steady growth with some volatility
        base_price = 150.0
        trend = 0.0003  # Slight upward trend
        volatility = 0.015
    elif symbol == "TSLA":
        # Tesla-like pattern: high volatility
        base_price = 200.0
        trend = 0.0001
        volatility = 0.035
    elif symbol == "MSFT":
        # Microsoft-like pattern: stable growth
        base_price = 300.0
        trend = 0.0004
        volatility = 0.012
    else:
        # Generic pattern
        base_price = 100.0
        trend = 0.0002
        volatility = 0.02
    
    np.random.seed(hash(symbol) % 1000)  # Different seed for each symbol
    
    # Generate returns with trend and volatility
    returns = np.random.normal(trend, volatility, len(dates))
    
    # Add market cycles
    cycle = np.sin(np.arange(len(dates)) * 2 * np.pi / 252) * 0.005
    returns += cycle
    
    # Add some random jumps (market events)
    jump_days = np.random.choice(len(dates), size=len(dates)//50, replace=False)
    returns[jump_days] += np.random.normal(0, 0.05, len(jump_days))
    
    # Calculate prices
    prices = [base_price]
    for ret in returns[1:]:
        prices.append(prices[-1] * (1 + ret))
    
    prices = np.array(prices)
    
    # Generate OHLC data
    data = pd.DataFrame(index=dates)
    data['open'] = prices * (1 + np.random.normal(0, 0.003, len(dates)))
    data['high'] = np.maximum(data['open'], prices) * (1 + np.abs(np.random.normal(0, 0.008, len(dates))))
    data['low'] = np.minimum(data['open'], prices) * (1 - np.abs(np.random.normal(0, 0.008, len(dates))))
    data['close'] = prices
    data['volume'] = np.random.lognormal(12, 0.6, len(dates))
    
    # Ensure OHLC relationships
    data['high'] = np.maximum(data['high'], np.maximum(data['open'], data['close']))
    data['low'] = np.minimum(data['low'], np.minimum(data['open'], data['close']))
    
    return data


class MockDatabaseManager:
    """Mock database manager for demo"""
    
    async def get_stock_data(self, symbol: str, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """Return realistic sample data"""
        return generate_realistic_data(symbol)


class MockCacheManager:
    """Mock cache manager for demo"""
    
    def __init__(self):
        self.cache = {}
    
    async def get(self, key: str):
        return self.cache.get(key)
    
    async def set(self, key: str, value, expire: int = None):
        self.cache[key] = value


async def demo_single_stock_analysis():
    """Demonstrate single stock analysis"""
    print("\n" + "="*60)
    print("SINGLE STOCK ANALYSIS DEMO")
    print("="*60)
    
    # Initialize components
    db_manager = MockDatabaseManager()
    cache_manager = MockCacheManager()
    engine = AnalyticsEngine(db_manager, cache_manager)
    
    # Analyze Apple stock
    print("Analyzing AAPL stock...")
    result = await engine.analyze_stock("AAPL", include_anomaly_detection=True)
    
    # Display results
    print(f"\nAnalysis Results for AAPL:")
    print(f"  • Data points analyzed: {result.metadata.get('data_points', 0)}")
    print(f"  • Technical indicators calculated: {len(result.technical_indicators)}")
    print(f"  • Anomaly types detected: {len(result.anomaly_detection)}")
    
    # Trading signals
    if result.trading_signals:
        print(f"\nTrading Signals:")
        for signal_type, signal in result.trading_signals.items():
            print(f"  • {signal_type}: {signal}")
    
    # Risk metrics
    if "AAPL" in result.risk_metrics:
        risk = result.risk_metrics["AAPL"]
        print(f"\nRisk Metrics:")
        print(f"  • Volatility: {risk.volatility:.4f}")
        print(f"  • Sharpe Ratio: {risk.sharpe_ratio:.3f}")
        print(f"  • VaR (95%): {risk.var_95:.4f}")
        print(f"  • Max Drawdown: {risk.max_drawdown:.4f}")
    
    # Anomalies
    total_anomalies = 0
    for anomaly_type, anomaly_result in result.anomaly_detection.items():
        if anomaly_result.anomalies.any():
            count = anomaly_result.anomalies.sum()
            total_anomalies += count
            print(f"  • {anomaly_type} anomalies: {count}")
    
    print(f"  • Total anomalies: {total_anomalies}")


async def demo_portfolio_analysis():
    """Demonstrate portfolio analysis"""
    print("\n" + "="*60)
    print("PORTFOLIO ANALYSIS DEMO")
    print("="*60)
    
    # Initialize components
    db_manager = MockDatabaseManager()
    cache_manager = MockCacheManager()
    engine = AnalyticsEngine(db_manager, cache_manager)
    
    # Portfolio of tech stocks
    portfolio = ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA"]
    print(f"Analyzing portfolio: {', '.join(portfolio)}")
    
    # Analyze portfolio
    results = await engine.analyze_portfolio(portfolio)
    
    print(f"\nPortfolio Analysis Results:")
    print(f"  • Stocks analyzed: {len(results)}")
    
    # Portfolio summary
    total_anomalies = 0
    bullish_count = 0
    bearish_count = 0
    
    for symbol, result in results.items():
        # Count trading signals
        if result.trading_signals:
            signal = result.trading_signals.get('overall_signal', 'neutral')
            if signal == 'bullish':
                bullish_count += 1
            elif signal == 'bearish':
                bearish_count += 1
        
        # Count anomalies
        for anomaly_result in result.anomaly_detection.values():
            if anomaly_result.anomalies.any():
                total_anomalies += anomaly_result.anomalies.sum()
    
    print(f"  • Bullish signals: {bullish_count}")
    print(f"  • Bearish signals: {bearish_count}")
    print(f"  • Total anomalies detected: {total_anomalies}")
    
    # Portfolio correlation
    if results and any(r.correlation_analysis for r in results.values()):
        print(f"  • Portfolio correlation analysis completed")


async def demo_market_report():
    """Demonstrate market report generation"""
    print("\n" + "="*60)
    print("MARKET REPORT GENERATION DEMO")
    print("="*60)
    
    # Initialize components
    db_manager = MockDatabaseManager()
    cache_manager = MockCacheManager()
    engine = AnalyticsEngine(db_manager, cache_manager)
    
    # Generate report for a diverse portfolio
    symbols = ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA", "JPM", "JNJ", "PG"]
    print(f"Generating market report for {len(symbols)} symbols...")
    
    # Generate report
    report = await engine.generate_market_report(symbols)
    
    print(f"\nReport generated successfully!")
    print(f"Report length: {len(report)} characters")
    
    # Show a preview of the report
    print(f"\nReport Preview:")
    print("-" * 40)
    lines = report.split('\n')[:20]  # Show first 20 lines
    for line in lines:
        print(line)
    print("...")


async def demo_technical_indicators():
    """Demonstrate technical indicators"""
    print("\n" + "="*60)
    print("TECHNICAL INDICATORS DEMO")
    print("="*60)
    
    # Generate data
    data = generate_realistic_data("AAPL", days=100)
    
    # Initialize technical indicators
    ti = TechnicalIndicators()
    
    # Calculate all indicators
    indicators = ti.calculate_all_indicators(data)
    
    print(f"Calculated {len(indicators)} technical indicators:")
    
    # Show some key indicators
    key_indicators = ['rsi', 'macd', 'bollinger_bands', 'sma_20', 'ema_20']
    
    for indicator_name in key_indicators:
        if indicator_name in indicators:
            indicator = indicators[indicator_name]
            latest_value = indicator.values.iloc[-1] if not indicator.values.empty else "N/A"
            print(f"  • {indicator_name.upper()}: {latest_value}")
    
    # Generate trading signals
    signals = ti.generate_trading_signals(indicators)
    print(f"\nTrading Signals:")
    for signal_type, signal in signals.items():
        print(f"  • {signal_type}: {signal}")


async def demo_anomaly_detection():
    """Demonstrate anomaly detection"""
    print("\n" + "="*60)
    print("ANOMALY DETECTION DEMO")
    print("="*60)
    
    # Generate data with some anomalies
    data = generate_realistic_data("TSLA", days=100)
    
    # Add some artificial anomalies
    # Price spike
    data.loc[data.index[50], 'close'] *= 1.15
    data.loc[data.index[50], 'high'] *= 1.15
    
    # Volume spike
    data.loc[data.index[75], 'volume'] *= 3.0
    
    # Initialize anomaly detector
    ad = AnomalyDetector()
    
    # Detect different types of anomalies
    price_anomalies = ad.detect_price_anomalies(data)
    volume_anomalies = ad.detect_volume_anomalies(data)
    pattern_anomalies = ad.detect_pattern_anomalies(data)
    
    print(f"Anomaly Detection Results:")
    print(f"  • Price anomalies: {price_anomalies.model_info.get('n_anomalies', 0)}")
    print(f"  • Volume anomalies: {volume_anomalies.model_info.get('n_anomalies', 0)}")
    print(f"  • Pattern anomalies: {pattern_anomalies.model_info.get('n_anomalies', 0)}")
    
    # Show recent anomalies
    for anomaly_type, anomaly_result in [('Price', price_anomalies), 
                                        ('Volume', volume_anomalies), 
                                        ('Pattern', pattern_anomalies)]:
        if anomaly_result.anomalies.any():
            recent_anomalies = anomaly_result.anomalies.tail(10)
            if recent_anomalies.any():
                print(f"\nRecent {anomaly_type} Anomalies:")
                for date, is_anomaly in recent_anomalies.items():
                    if is_anomaly:
                        score = anomaly_result.anomaly_scores.get(date, 0)
                        print(f"  • {date.strftime('%Y-%m-%d')}: Score = {score:.3f}")


async def run_demo():
    """Run all demos"""
    print("="*80)
    print("ANALYTICS ENGINE DEMONSTRATION")
    print("="*80)
    print("This demo showcases the comprehensive analytics capabilities")
    print("of the stock monitoring system's analytics engine.")
    print("="*80)
    
    try:
        # Run individual demos
        await demo_technical_indicators()
        await demo_anomaly_detection()
        await demo_single_stock_analysis()
        await demo_portfolio_analysis()
        await demo_market_report()
        
        print("\n" + "="*80)
        print("DEMO COMPLETED SUCCESSFULLY!")
        print("="*80)
        print("\nKey Features Demonstrated:")
        print("  Technical Indicators (RSI, MACD, Bollinger Bands, etc.)")
        print("  Anomaly Detection (Price, Volume, Pattern)")
        print("  Single Stock Analysis")
        print("  Portfolio Analysis")
        print("  Market Report Generation")
        print("  Risk Metrics and Volatility Analysis")
        print("  Trading Signal Generation")
        print("\nThe analytics engine is ready for production use!")
        
    except Exception as e:
        print(f"\nDemo failed: {e}")
        logger.error(f"Demo error: {e}")


def main():
    """Main function"""
    asyncio.run(run_demo())


if __name__ == "__main__":
    main() 