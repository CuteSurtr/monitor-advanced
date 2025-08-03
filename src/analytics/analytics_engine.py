"""
Analytics Engine Module

This module serves as the main orchestrator for all analytics components,
including technical indicators, correlation analysis, volatility analysis,
and anomaly detection.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Union, Any
from dataclasses import dataclass
import logging
import asyncio
from datetime import datetime, timedelta
from src.utils.logger import get_logger
from src.utils.database import DatabaseManager
from src.utils.cache import CacheManager
from .technical_indicators import TechnicalIndicators, IndicatorResult
from .correlation_analyzer import CorrelationAnalyzer, CorrelationResult
from .volatility_analyzer import VolatilityAnalyzer, VolatilityResult, RiskMetrics
from .anomaly_detector import AnomalyDetector, AnomalyResult

logger = get_logger(__name__)


@dataclass
class AnalyticsResult:
    """Container for comprehensive analytics results"""
    technical_indicators: Dict[str, IndicatorResult]
    correlation_analysis: Dict[str, CorrelationResult]
    volatility_analysis: Dict[str, VolatilityResult]
    risk_metrics: Dict[str, RiskMetrics]
    anomaly_detection: Dict[str, AnomalyResult]
    trading_signals: Dict[str, Dict[str, str]]
    metadata: Dict[str, Any]


class AnalyticsEngine:
    """
    Main analytics engine that orchestrates all analytics components
    
    Provides comprehensive analysis including technical indicators,
    correlation analysis, volatility analysis, and anomaly detection.
    """
    
    def __init__(self, db_manager: DatabaseManager, cache_manager: CacheManager):
        self.logger = logger
        self.db_manager = db_manager
        self.cache_manager = cache_manager
        
        # Initialize analytics components
        self.technical_indicators = TechnicalIndicators()
        self.correlation_analyzer = CorrelationAnalyzer()
        self.volatility_analyzer = VolatilityAnalyzer()
        self.anomaly_detector = AnomalyDetector()
    
    async def analyze_stock(self, symbol: str, 
                          start_date: Optional[str] = None,
                          end_date: Optional[str] = None,
                          include_anomaly_detection: bool = True) -> AnalyticsResult:
        """
        Perform comprehensive analysis for a single stock
        
        Args:
            symbol: Stock symbol
            start_date: Start date for analysis (optional)
            end_date: End date for analysis (optional)
            include_anomaly_detection: Whether to include anomaly detection
            
        Returns:
            AnalyticsResult with all analysis components
        """
        try:
            self.logger.info(f"Starting comprehensive analysis for {symbol}")
            
            # Get stock data
            stock_data = await self._get_stock_data(symbol, start_date, end_date)
            
            if stock_data.empty:
                self.logger.warning(f"No data available for {symbol}")
                return self._create_empty_result()
            
            # Perform all analyses
            results = await self._perform_comprehensive_analysis(
                stock_data, symbol, include_anomaly_detection
            )
            
            # Cache results
            await self._cache_analytics_results(symbol, results)
            
            self.logger.info(f"Completed analysis for {symbol}")
            return results
            
        except Exception as e:
            self.logger.error(f"Error analyzing stock {symbol}: {e}")
            return self._create_empty_result()
    
    async def analyze_portfolio(self, symbols: List[str],
                              start_date: Optional[str] = None,
                              end_date: Optional[str] = None) -> Dict[str, AnalyticsResult]:
        """
        Perform analysis for multiple stocks (portfolio)
        
        Args:
            symbols: List of stock symbols
            start_date: Start date for analysis (optional)
            end_date: End date for analysis (optional)
            
        Returns:
            Dictionary of AnalyticsResult for each symbol
        """
        try:
            self.logger.info(f"Starting portfolio analysis for {len(symbols)} symbols")
            
            results = {}
            
            # Analyze each symbol
            for symbol in symbols:
                try:
                    result = await self.analyze_stock(
                        symbol, start_date, end_date, include_anomaly_detection=True
                    )
                    results[symbol] = result
                except Exception as e:
                    self.logger.error(f"Error analyzing {symbol}: {e}")
                    results[symbol] = self._create_empty_result()
            
            # Perform portfolio-level correlation analysis
            portfolio_correlation = await self._analyze_portfolio_correlations(
                symbols, start_date, end_date
            )
            
            # Add portfolio correlation to each result
            for symbol in results:
                results[symbol].correlation_analysis['portfolio'] = portfolio_correlation
            
            self.logger.info(f"Completed portfolio analysis")
            return results
            
        except Exception as e:
            self.logger.error(f"Error in portfolio analysis: {e}")
            return {}
    
    async def analyze_market_sectors(self, sector_mapping: Dict[str, str],
                                   start_date: Optional[str] = None,
                                   end_date: Optional[str] = None) -> Dict[str, Dict]:
        """
        Perform sector-level analysis
        
        Args:
            sector_mapping: Dictionary mapping symbols to sectors
            start_date: Start date for analysis (optional)
            end_date: End date for analysis (optional)
            
        Returns:
            Dictionary of sector analysis results
        """
        try:
            self.logger.info("Starting sector analysis")
            
            # Group symbols by sector
            sector_groups = {}
            for symbol, sector in sector_mapping.items():
                if sector not in sector_groups:
                    sector_groups[sector] = []
                sector_groups[sector].append(symbol)
            
            sector_results = {}
            
            # Analyze each sector
            for sector, symbols in sector_groups.items():
                try:
                    # Get sector data
                    sector_data = await self._get_sector_data(symbols, start_date, end_date)
                    
                    if not sector_data.empty:
                        # Perform sector analysis
                        sector_analysis = await self._analyze_sector_data(sector_data, sector)
                        sector_results[sector] = sector_analysis
                    
                except Exception as e:
                    self.logger.error(f"Error analyzing sector {sector}: {e}")
            
            self.logger.info(f"Completed sector analysis for {len(sector_results)} sectors")
            return sector_results
            
        except Exception as e:
            self.logger.error(f"Error in sector analysis: {e}")
            return {}
    
    async def generate_market_report(self, symbols: List[str],
                                   start_date: Optional[str] = None,
                                   end_date: Optional[str] = None) -> str:
        """
        Generate comprehensive market analysis report
        
        Args:
            symbols: List of symbols to analyze
            start_date: Start date for analysis (optional)
            end_date: End date for analysis (optional)
            
        Returns:
            Formatted report string
        """
        try:
            self.logger.info("Generating market report")
            
            report = []
            report.append("=" * 80)
            report.append("COMPREHENSIVE MARKET ANALYSIS REPORT")
            report.append("=" * 80)
            report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            report.append(f"Symbols Analyzed: {len(symbols)}")
            report.append(f"Date Range: {start_date or 'All available'} to {end_date or 'Latest'}")
            report.append("")
            
            # Analyze portfolio
            portfolio_results = await self.analyze_portfolio(symbols, start_date, end_date)
            
            # Market overview
            report.append("MARKET OVERVIEW")
            report.append("-" * 40)
            
            # Calculate market statistics
            market_stats = await self._calculate_market_statistics(portfolio_results)
            report.append(f"Average Volatility: {market_stats['avg_volatility']:.4f}")
            report.append(f"Market Correlation: {market_stats['avg_correlation']:.4f}")
            report.append(f"Total Anomalies Detected: {market_stats['total_anomalies']}")
            report.append("")
            
            # Individual stock analysis
            report.append("INDIVIDUAL STOCK ANALYSIS")
            report.append("-" * 40)
            
            for symbol, result in portfolio_results.items():
                if result.technical_indicators:
                    report.append(f"\n{symbol}:")
                    
                    # Trading signals
                    if result.trading_signals:
                        signals = result.trading_signals
                        report.append(f"  Overall Signal: {signals.get('overall_signal', 'neutral')}")
                        report.append(f"  Confidence: {signals.get('confidence', 0):.2f}")
                    
                    # Risk metrics
                    if symbol in result.risk_metrics:
                        risk = result.risk_metrics[symbol]
                        report.append(f"  Sharpe Ratio: {risk.sharpe_ratio:.3f}")
                        report.append(f"  VaR (95%): {risk.var_95:.4f}")
                        report.append(f"  Max Drawdown: {risk.max_drawdown:.4f}")
            
            # Sector analysis
            if len(symbols) > 5:  # Only for larger portfolios
                report.append("\nSECTOR ANALYSIS")
                report.append("-" * 40)
                
                # Create simple sector mapping
                sector_mapping = {symbol: "General" for symbol in symbols}
                sector_results = await self.analyze_market_sectors(
                    sector_mapping, start_date, end_date
                )
                
                for sector, analysis in sector_results.items():
                    report.append(f"\n{sector}:")
                    if 'correlation' in analysis:
                        report.append(f"  Sector Correlation: {analysis['correlation']:.3f}")
            
            # Anomaly summary
            report.append("\nANOMALY SUMMARY")
            report.append("-" * 40)
            
            total_anomalies = 0
            for symbol, result in portfolio_results.items():
                if result.anomaly_detection:
                    for anomaly_type, anomaly_result in result.anomaly_detection.items():
                        if anomaly_result.anomalies.any():
                            count = anomaly_result.anomalies.sum()
                            total_anomalies += count
                            report.append(f"  {symbol} ({anomaly_type}): {count} anomalies")
            
            report.append(f"\nTotal Anomalies: {total_anomalies}")
            
            # Recommendations
            report.append("\nRECOMMENDATIONS")
            report.append("-" * 40)
            
            recommendations = await self._generate_recommendations(portfolio_results)
            for rec in recommendations:
                report.append(f"  - {rec}")
            
            report.append("\n" + "=" * 80)
            
            return "\n".join(report)
            
        except Exception as e:
            self.logger.error(f"Error generating market report: {e}")
            return f"Error generating report: {e}"
    
    async def _get_stock_data(self, symbol: str,
                            start_date: Optional[str] = None,
                            end_date: Optional[str] = None) -> pd.DataFrame:
        """Get stock data from database or cache"""
        try:
            # Try cache first
            cache_key = f"stock_data_{symbol}_{start_date}_{end_date}"
            cached_data = await self.cache_manager.get(cache_key)
            
            if cached_data is not None:
                return pd.DataFrame(cached_data)
            
            # Get from database
            data = await self.db_manager.get_stock_data(symbol, start_date, end_date)
            
            if not data.empty:
                # Cache the data
                await self.cache_manager.set(cache_key, data.to_dict(), expire=3600)
            
            return data
            
        except Exception as e:
            self.logger.error(f"Error getting stock data for {symbol}: {e}")
            return pd.DataFrame()
    
    async def _perform_comprehensive_analysis(self, data: pd.DataFrame,
                                           symbol: str,
                                           include_anomaly_detection: bool) -> AnalyticsResult:
        """Perform all analytics components"""
        try:
            # Technical indicators
            technical_indicators = self.technical_indicators.calculate_all_indicators(data)
            trading_signals = self.technical_indicators.generate_trading_signals(technical_indicators)
            
            # Volatility analysis
            volatility_analysis = {}
            risk_metrics = {}
            
            # Historical volatility
            hist_vol = self.volatility_analyzer.calculate_historical_volatility(data['close'])
            volatility_analysis['historical'] = VolatilityResult(
                historical_volatility=hist_vol,
                rolling_volatility=hist_vol
            )
            
            # EWMA volatility
            ewma_vol = self.volatility_analyzer.calculate_ewma_volatility(data['close'])
            volatility_analysis['ewma'] = VolatilityResult(
                historical_volatility=ewma_vol,
                rolling_volatility=ewma_vol
            )
            
            # Risk metrics
            risk_metrics[symbol] = self.volatility_analyzer.calculate_comprehensive_risk_metrics(
                data['close']
            )
            
            # Correlation analysis (single stock - limited)
            correlation_analysis = {}
            
            # Anomaly detection
            anomaly_detection = {}
            if include_anomaly_detection:
                anomaly_detection['price'] = self.anomaly_detector.detect_price_anomalies(data)
                anomaly_detection['volume'] = self.anomaly_detector.detect_volume_anomalies(data)
                anomaly_detection['pattern'] = self.anomaly_detector.detect_pattern_anomalies(data)
            
            metadata = {
                'symbol': symbol,
                'analysis_date': datetime.now().isoformat(),
                'data_points': len(data),
                'date_range': f"{data.index[0]} to {data.index[-1]}"
            }
            
            return AnalyticsResult(
                technical_indicators=technical_indicators,
                correlation_analysis=correlation_analysis,
                volatility_analysis=volatility_analysis,
                risk_metrics=risk_metrics,
                anomaly_detection=anomaly_detection,
                trading_signals=trading_signals,
                metadata=metadata
            )
            
        except Exception as e:
            self.logger.error(f"Error in comprehensive analysis: {e}")
            return self._create_empty_result()
    
    async def _analyze_portfolio_correlations(self, symbols: List[str],
                                           start_date: Optional[str],
                                           end_date: Optional[str]) -> CorrelationResult:
        """Analyze correlations between portfolio components"""
        try:
            # Get data for all symbols
            portfolio_data = pd.DataFrame()
            
            for symbol in symbols:
                data = await self._get_stock_data(symbol, start_date, end_date)
                if not data.empty:
                    portfolio_data[symbol] = data['close']
            
            if len(portfolio_data.columns) < 2:
                return CorrelationResult(
                    correlation_matrix=pd.DataFrame(),
                    significant_correlations=pd.DataFrame()
                )
            
            # Calculate correlations
            return self.correlation_analyzer.calculate_correlation_matrix(portfolio_data)
            
        except Exception as e:
            self.logger.error(f"Error analyzing portfolio correlations: {e}")
            return CorrelationResult(
                correlation_matrix=pd.DataFrame(),
                significant_correlations=pd.DataFrame()
            )
    
    async def _get_sector_data(self, symbols: List[str],
                             start_date: Optional[str],
                             end_date: Optional[str]) -> pd.DataFrame:
        """Get aggregated sector data"""
        try:
            sector_data = pd.DataFrame()
            
            for symbol in symbols:
                data = await self._get_stock_data(symbol, start_date, end_date)
                if not data.empty:
                    sector_data[symbol] = data['close']
            
            return sector_data
            
        except Exception as e:
            self.logger.error(f"Error getting sector data: {e}")
            return pd.DataFrame()
    
    async def _analyze_sector_data(self, sector_data: pd.DataFrame, sector: str) -> Dict:
        """Analyze sector-level data"""
        try:
            analysis = {}
            
            # Calculate sector average
            sector_avg = sector_data.mean(axis=1)
            
            # Sector volatility
            sector_vol = self.volatility_analyzer.calculate_historical_volatility(sector_avg)
            analysis['volatility'] = sector_vol.iloc[-1] if not sector_vol.empty else 0
            
            # Sector correlation
            if len(sector_data.columns) > 1:
                corr_result = self.correlation_analyzer.calculate_correlation_matrix(sector_data)
                analysis['correlation'] = corr_result.correlation_matrix.mean().mean()
            else:
                analysis['correlation'] = 0
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing sector data: {e}")
            return {}
    
    async def _calculate_market_statistics(self, portfolio_results: Dict[str, AnalyticsResult]) -> Dict:
        """Calculate market-wide statistics"""
        try:
            stats = {
                'avg_volatility': 0,
                'avg_correlation': 0,
                'total_anomalies': 0
            }
            
            volatilities = []
            correlations = []
            
            for symbol, result in portfolio_results.items():
                # Volatility
                if symbol in result.risk_metrics:
                    volatilities.append(result.risk_metrics[symbol].volatility)
                
                # Anomalies
                for anomaly_result in result.anomaly_detection.values():
                    if anomaly_result.anomalies.any():
                        stats['total_anomalies'] += anomaly_result.anomalies.sum()
            
            if volatilities:
                stats['avg_volatility'] = np.mean(volatilities)
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Error calculating market statistics: {e}")
            return {'avg_volatility': 0, 'avg_correlation': 0, 'total_anomalies': 0}
    
    async def _generate_recommendations(self, portfolio_results: Dict[str, AnalyticsResult]) -> List[str]:
        """Generate trading recommendations based on analysis"""
        try:
            recommendations = []
            
            # Analyze overall market sentiment
            bullish_count = 0
            bearish_count = 0
            
            for symbol, result in portfolio_results.items():
                if result.trading_signals:
                    signal = result.trading_signals.get('overall_signal', 'neutral')
                    if signal == 'bullish':
                        bullish_count += 1
                    elif signal == 'bearish':
                        bearish_count += 1
            
            # Market sentiment recommendation
            if bullish_count > bearish_count:
                recommendations.append("Overall market sentiment is bullish")
            elif bearish_count > bullish_count:
                recommendations.append("Overall market sentiment is bearish")
            else:
                recommendations.append("Market sentiment is mixed")
            
            # Risk management recommendations
            high_risk_symbols = []
            for symbol, result in portfolio_results.items():
                if symbol in result.risk_metrics:
                    risk = result.risk_metrics[symbol]
                    if risk.volatility > 0.3:  # High volatility threshold
                        high_risk_symbols.append(symbol)
            
            if high_risk_symbols:
                recommendations.append(f"Consider risk management for high volatility symbols: {', '.join(high_risk_symbols)}")
            
            # Anomaly recommendations
            anomaly_symbols = []
            for symbol, result in portfolio_results.items():
                for anomaly_type, anomaly_result in result.anomaly_detection.items():
                    if anomaly_result.anomalies.any():
                        recent_anomalies = anomaly_result.anomalies.tail(5)
                        if recent_anomalies.any():
                            anomaly_symbols.append(symbol)
                            break
            
            if anomaly_symbols:
                recommendations.append(f"Monitor symbols with recent anomalies: {', '.join(anomaly_symbols)}")
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Error generating recommendations: {e}")
            return ["Unable to generate recommendations due to analysis errors"]
    
    async def _cache_analytics_results(self, symbol: str, results: AnalyticsResult) -> None:
        """Cache analytics results"""
        try:
            cache_key = f"analytics_{symbol}_{datetime.now().strftime('%Y%m%d')}"
            
            # Convert results to cacheable format
            cache_data = {
                'symbol': symbol,
                'analysis_date': results.metadata.get('analysis_date'),
                'trading_signals': results.trading_signals,
                'risk_metrics': {
                    symbol: {
                        'volatility': risk.volatility,
                        'sharpe_ratio': risk.sharpe_ratio,
                        'var_95': risk.var_95,
                        'max_drawdown': risk.max_drawdown
                    } for symbol, risk in results.risk_metrics.items()
                }
            }
            
            await self.cache_manager.set(cache_key, cache_data, expire=7200)  # 2 hours
            
        except Exception as e:
            self.logger.error(f"Error caching analytics results: {e}")
    
    def _create_empty_result(self) -> AnalyticsResult:
        """Create empty analytics result"""
        return AnalyticsResult(
            technical_indicators={},
            correlation_analysis={},
            volatility_analysis={},
            risk_metrics={},
            anomaly_detection={},
            trading_signals={},
            metadata={}
        )
    
    async def export_analytics_data(self, results: Dict[str, AnalyticsResult],
                                  output_dir: str = "data/analytics") -> None:
        """
        Export analytics results to files
        
        Args:
            results: Dictionary of analytics results
            output_dir: Output directory for files
        """
        try:
            import os
            os.makedirs(output_dir, exist_ok=True)
            
            for symbol, result in results.items():
                symbol_dir = f"{output_dir}/{symbol}"
                os.makedirs(symbol_dir, exist_ok=True)
                
                # Export trading signals
                if result.trading_signals:
                    import json
                    with open(f"{symbol_dir}/trading_signals.json", 'w') as f:
                        json.dump(result.trading_signals, f, indent=2)
                
                # Export risk metrics
                if result.risk_metrics:
                    risk_data = {}
                    for sym, risk in result.risk_metrics.items():
                        risk_data[sym] = {
                            'volatility': risk.volatility,
                            'sharpe_ratio': risk.sharpe_ratio,
                            'sortino_ratio': risk.sortino_ratio,
                            'var_95': risk.var_95,
                            'var_99': risk.var_99,
                            'cvar_95': risk.cvar_95,
                            'cvar_99': risk.cvar_99,
                            'max_drawdown': risk.max_drawdown,
                            'beta': risk.beta
                        }
                    
                    with open(f"{symbol_dir}/risk_metrics.json", 'w') as f:
                        json.dump(risk_data, f, indent=2)
                
                # Export anomaly data
                if result.anomaly_detection:
                    for anomaly_type, anomaly_result in result.anomaly_detection.items():
                        if not anomaly_result.anomalies.empty:
                            anomaly_result.anomalies.to_csv(
                                f"{symbol_dir}/{anomaly_type}_anomalies.csv"
                            )
                        if not anomaly_result.anomaly_scores.empty:
                            anomaly_result.anomaly_scores.to_csv(
                                f"{symbol_dir}/{anomaly_type}_scores.csv"
                            )
                
                # Export metadata
                if result.metadata:
                    with open(f"{symbol_dir}/metadata.json", 'w') as f:
                        json.dump(result.metadata, f, indent=2)
            
            self.logger.info(f"Analytics data exported to {output_dir}")
            
        except Exception as e:
            self.logger.error(f"Error exporting analytics data: {e}") 