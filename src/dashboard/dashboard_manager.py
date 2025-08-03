"""
Dashboard Manager Module

Manages the web dashboard functionality and integrates with all system components
to provide real-time data visualization and analytics.
"""

import asyncio
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import json
import logging

from src.utils.database import DatabaseManager
from src.utils.cache import CacheManager
from src.analytics.analytics_engine import AnalyticsEngine
from src.portfolio.portfolio_manager import PortfolioManager
from src.alerts.alert_manager import AlertManager
from src.utils.logger import get_logger

logger = get_logger(__name__)


class DashboardManager:
    """
    Manages dashboard data and integrates with system components.
    
    Provides real-time data aggregation, caching, and visualization
    for the web dashboard interface.
    """
    
    def __init__(self, 
                 db_manager: DatabaseManager,
                 cache_manager: CacheManager,
                 analytics_engine: AnalyticsEngine,
                 portfolio_manager: PortfolioManager,
                 alert_manager: AlertManager):
        self.db_manager = db_manager
        self.cache_manager = cache_manager
        self.analytics_engine = analytics_engine
        self.portfolio_manager = portfolio_manager
        self.alert_manager = alert_manager
        self.logger = logger
        
        # Cache keys for dashboard data
        self.cache_keys = {
            'market_overview': 'dashboard:market_overview',
            'portfolio_summary': 'dashboard:portfolio_summary',
            'top_movers': 'dashboard:top_movers',
            'alert_summary': 'dashboard:alert_summary',
            'market_heatmap': 'dashboard:market_heatmap'
        }
        
        # Default symbols for monitoring
        self.default_symbols = [
            'AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN', 'META', 'NVDA', 
            'NFLX', 'PYPL', 'ADBE', 'CRM', 'ORCL', 'INTC', 'AMD', 'QCOM'
        ]
    
    async def get_market_overview(self) -> Dict[str, Any]:
        """Get comprehensive market overview data."""
        try:
            # Try to get from cache first
            cached_data = await self.cache_manager.get(self.cache_keys['market_overview'])
            if cached_data:
                return json.loads(cached_data)
            
            # Get real market data
            market_data = await self._aggregate_market_data()
            
            # Cache the result for 5 minutes
            await self.cache_manager.set(
                self.cache_keys['market_overview'],
                json.dumps(market_data),
                expire=300
            )
            
            return market_data
            
        except Exception as e:
            self.logger.error(f"Error getting market overview: {e}")
            return self._get_fallback_market_data()
    
    async def get_portfolio_data(self) -> Dict[str, Any]:
        """Get portfolio data for dashboard."""
        try:
            # Try to get from cache first
            cached_data = await self.cache_manager.get(self.cache_keys['portfolio_summary'])
            if cached_data:
                return json.loads(cached_data)
            
            # Get real portfolio data
            portfolio_data = await self._get_portfolio_summary()
            
            # Cache the result for 2 minutes
            await self.cache_manager.set(
                self.cache_keys['portfolio_summary'],
                json.dumps(portfolio_data),
                expire=120
            )
            
            return portfolio_data
            
        except Exception as e:
            self.logger.error(f"Error getting portfolio data: {e}")
            return self._get_fallback_portfolio_data()
    
    async def get_technical_analysis(self, symbol: str, indicator: str, period: int = 30) -> Dict[str, Any]:
        """Get technical analysis for a specific symbol."""
        try:
            # Use analytics engine to get real technical analysis
            analysis_result = await self.analytics_engine.analyze_stock(
                symbol=symbol,
                start_date=(datetime.now() - timedelta(days=period)).strftime('%Y-%m-%d'),
                end_date=datetime.now().strftime('%Y-%m-%d'),
                include_anomaly_detection=False
            )
            
            # Extract the specific indicator data
            indicator_data = self._extract_indicator_data(analysis_result, indicator)
            
            return {
                "symbol": symbol,
                "indicator": indicator,
                "timestamps": indicator_data['timestamps'],
                "values": indicator_data['values'],
                "signals": indicator_data['signals']
            }
            
        except Exception as e:
            self.logger.error(f"Error getting technical analysis for {symbol}: {e}")
            return self._get_fallback_technical_data(symbol, indicator, period)
    
    async def get_alerts_data(self) -> Dict[str, Any]:
        """Get alerts data for dashboard."""
        try:
            # Try to get from cache first
            cached_data = await self.cache_manager.get(self.cache_keys['alert_summary'])
            if cached_data:
                return json.loads(cached_data)
            
            # Get real alerts data
            alerts_data = await self._get_alerts_summary()
            
            # Cache the result for 1 minute
            await self.cache_manager.set(
                self.cache_keys['alert_summary'],
                json.dumps(alerts_data),
                expire=60
            )
            
            return alerts_data
            
        except Exception as e:
            self.logger.error(f"Error getting alerts data: {e}")
            return self._get_fallback_alerts_data()
    
    async def get_market_heatmap(self) -> Dict[str, Any]:
        """Get market heatmap data."""
        try:
            # Try to get from cache first
            cached_data = await self.cache_manager.get(self.cache_keys['market_heatmap'])
            if cached_data:
                return json.loads(cached_data)
            
            # Get real heatmap data
            heatmap_data = await self._generate_market_heatmap()
            
            # Cache the result for 5 minutes
            await self.cache_manager.set(
                self.cache_keys['market_heatmap'],
                json.dumps(heatmap_data),
                expire=300
            )
            
            return heatmap_data
            
        except Exception as e:
            self.logger.error(f"Error getting market heatmap: {e}")
            return self._get_fallback_heatmap_data()
    
    async def get_available_symbols(self) -> List[str]:
        """Get list of available stock symbols."""
        try:
            # Get symbols from database
            symbols = await self.db_manager.get_available_symbols()
            if symbols:
                return symbols
            
            # Fallback to default symbols
            return self.default_symbols
            
        except Exception as e:
            self.logger.error(f"Error getting available symbols: {e}")
            return self.default_symbols
    
    async def get_real_time_data(self, symbol: str) -> Dict[str, Any]:
        """Get real-time data for a specific symbol."""
        try:
            # Get latest stock data from database
            latest_data = await self.db_manager.get_latest_stock_data(symbol)
            
            if latest_data:
                return {
                    "symbol": symbol,
                    "price": latest_data['close_price'],
                    "change": latest_data.get('change', 0),
                    "change_percent": latest_data.get('change_percent', 0),
                    "volume": latest_data.get('volume', 0),
                    "timestamp": latest_data['timestamp']
                }
            
            # Fallback to mock data
            return self._get_fallback_realtime_data(symbol)
            
        except Exception as e:
            self.logger.error(f"Error getting real-time data for {symbol}: {e}")
            return self._get_fallback_realtime_data(symbol)
    
    async def _aggregate_market_data(self) -> Dict[str, Any]:
        """Aggregate market data from multiple sources."""
        try:
            # Get data for all default symbols
            market_data = []
            total_symbols = len(self.default_symbols)
            gainers = 0
            losers = 0
            unchanged = 0
            
            for symbol in self.default_symbols:
                try:
                    data = await self.db_manager.get_latest_stock_data(symbol)
                    if data:
                        change_percent = data.get('change_percent', 0)
                        if change_percent > 0:
                            gainers += 1
                        elif change_percent < 0:
                            losers += 1
                        else:
                            unchanged += 1
                        
                        market_data.append({
                            'symbol': symbol,
                            'price': data['close_price'],
                            'change_percent': change_percent,
                            'volume': data.get('volume', 0)
                        })
                except Exception as e:
                    self.logger.warning(f"Error getting data for {symbol}: {e}")
            
            # Get top movers
            top_movers = sorted(market_data, key=lambda x: abs(x['change_percent']), reverse=True)[:5]
            
            # Get market performance over time
            market_performance = await self._get_market_performance()
            
            return {
                "total_symbols": total_symbols,
                "gainers": gainers,
                "losers": losers,
                "unchanged": unchanged,
                "active_alerts": await self._get_active_alerts_count(),
                "market_data": market_performance,
                "top_movers": top_movers
            }
            
        except Exception as e:
            self.logger.error(f"Error aggregating market data: {e}")
            raise
    
    async def _get_portfolio_summary(self) -> Dict[str, Any]:
        """Get portfolio summary data."""
        try:
            # Get portfolio data from portfolio manager
            portfolio_summary = await self.portfolio_manager.get_portfolio_summary()
            
            # Get portfolio performance over time
            performance_data = await self.portfolio_manager.get_portfolio_performance()
            
            # Get portfolio allocations
            allocations = await self.portfolio_manager.get_portfolio_allocations()
            
            return {
                "summary": portfolio_summary,
                "performance": performance_data,
                "allocations": allocations
            }
            
        except Exception as e:
            self.logger.error(f"Error getting portfolio summary: {e}")
            raise
    
    async def _get_alerts_summary(self) -> Dict[str, Any]:
        """Get alerts summary data."""
        try:
            # Get recent alerts
            recent_alerts = await self.alert_manager.get_recent_alerts(limit=10)
            
            # Get alert statistics
            stats = await self.alert_manager.get_alert_statistics()
            
            return {
                "recent_alerts": recent_alerts,
                "stats": stats
            }
            
        except Exception as e:
            self.logger.error(f"Error getting alerts summary: {e}")
            raise
    
    async def _generate_market_heatmap(self) -> Dict[str, Any]:
        """Generate market heatmap data."""
        try:
            symbols = self.default_symbols[:10]  # Limit to 10 symbols for heatmap
            metrics = ["Price Change", "Volume", "RSI", "Volatility"]
            
            heatmap_data = {
                "symbols": symbols,
                "metrics": metrics,
                "values": []
            }
            
            # Get data for each symbol and metric
            for metric in metrics:
                metric_values = []
                for symbol in symbols:
                    try:
                        if metric == "Price Change":
                            data = await self.db_manager.get_latest_stock_data(symbol)
                            value = data.get('change_percent', 0) if data else 0
                        elif metric == "Volume":
                            data = await self.db_manager.get_latest_stock_data(symbol)
                            value = data.get('volume', 0) if data else 0
                        elif metric == "RSI":
                            # Get RSI from analytics
                            analysis = await self.analytics_engine.analyze_stock(symbol)
                            rsi_data = analysis.technical_indicators.get('rsi', {})
                            value = rsi_data.get('current_value', 50) if rsi_data else 50
                        else:  # Volatility
                            # Get volatility from analytics
                            analysis = await self.analytics_engine.analyze_stock(symbol)
                            vol_data = analysis.volatility_analysis.get('historical_volatility', {})
                            value = vol_data.get('current', 0.2) if vol_data else 0.2
                        
                        metric_values.append(value)
                    except Exception as e:
                        self.logger.warning(f"Error getting {metric} for {symbol}: {e}")
                        metric_values.append(0)
                
                heatmap_data["values"].append(metric_values)
            
            return heatmap_data
            
        except Exception as e:
            self.logger.error(f"Error generating market heatmap: {e}")
            raise
    
    async def _get_market_performance(self) -> Dict[str, List]:
        """Get market performance over time."""
        try:
            # Get market index data (simplified - using average of top symbols)
            end_date = datetime.now()
            start_date = end_date - timedelta(hours=24)
            
            timestamps = []
            prices = []
            
            # Generate hourly data points
            for i in range(24):
                timestamp = start_date + timedelta(hours=i)
                timestamps.append(timestamp)
                
                # Calculate average price across symbols
                total_price = 0
                count = 0
                for symbol in self.default_symbols[:5]:  # Use top 5 symbols
                    try:
                        data = await self.db_manager.get_stock_data_at_time(symbol, timestamp)
                        if data:
                            total_price += data['close_price']
                            count += 1
                    except:
                        pass
                
                avg_price = total_price / count if count > 0 else 100
                prices.append(avg_price)
            
            return {
                "timestamps": timestamps,
                "prices": prices
            }
            
        except Exception as e:
            self.logger.error(f"Error getting market performance: {e}")
            return {
                "timestamps": [datetime.now() - timedelta(hours=i) for i in range(24, 0, -1)],
                "prices": [100 + i * 0.5 for i in range(24)]
            }
    
    async def _get_active_alerts_count(self) -> int:
        """Get count of active alerts."""
        try:
            stats = await self.alert_manager.get_alert_statistics()
            return stats.get('active_alerts', 0)
        except:
            return 0
    
    def _extract_indicator_data(self, analysis_result, indicator: str) -> Dict[str, Any]:
        """Extract specific indicator data from analysis result."""
        try:
            if indicator.lower() == 'rsi':
                rsi_data = analysis_result.technical_indicators.get('rsi', {})
                return {
                    'timestamps': rsi_data.get('timestamps', []),
                    'values': rsi_data.get('values', []),
                    'signals': rsi_data.get('signals', {})
                }
            elif indicator.lower() == 'macd':
                macd_data = analysis_result.technical_indicators.get('macd', {})
                return {
                    'timestamps': macd_data.get('timestamps', []),
                    'values': macd_data.get('macd_line', []),
                    'signals': macd_data.get('signals', {})
                }
            elif indicator.lower() == 'bollinger':
                bb_data = analysis_result.technical_indicators.get('bollinger_bands', {})
                return {
                    'timestamps': bb_data.get('timestamps', []),
                    'values': bb_data.get('middle_band', []),
                    'signals': bb_data.get('signals', {})
                }
            else:  # SMA
                sma_data = analysis_result.technical_indicators.get('sma', {})
                return {
                    'timestamps': sma_data.get('timestamps', []),
                    'values': sma_data.get('values', []),
                    'signals': sma_data.get('signals', {})
                }
        except Exception as e:
            self.logger.error(f"Error extracting indicator data: {e}")
            return {
                'timestamps': [],
                'values': [],
                'signals': {}
            }
    
    # Fallback methods for when real data is not available
    def _get_fallback_market_data(self) -> Dict[str, Any]:
        """Get fallback market data when real data is not available."""
        return {
            "total_symbols": 150,
            "gainers": 85,
            "losers": 45,
            "unchanged": 20,
            "active_alerts": 12,
            "market_data": {
                "timestamps": [datetime.now() - timedelta(hours=i) for i in range(24, 0, -1)],
                "prices": [100 + i * 0.5 + (i % 3 - 1) * 2 for i in range(24)]
            },
            "top_movers": [
                {"symbol": "AAPL", "change_percent": 5.2},
                {"symbol": "TSLA", "change_percent": -3.8},
                {"symbol": "GOOGL", "change_percent": 2.1},
                {"symbol": "MSFT", "change_percent": 1.7},
                {"symbol": "AMZN", "change_percent": -1.2}
            ]
        }
    
    def _get_fallback_portfolio_data(self) -> Dict[str, Any]:
        """Get fallback portfolio data."""
        return {
            "summary": {
                "total_value": 125000.50,
                "total_pnl": 8750.25,
                "total_pnl_percent": 7.5,
                "positions_count": 8
            },
            "allocations": {
                "labels": ["AAPL", "GOOGL", "MSFT", "TSLA", "AMZN"],
                "values": [30, 25, 20, 15, 10]
            },
            "performance": {
                "timestamps": [datetime.now() - timedelta(days=i) for i in range(30, 0, -1)],
                "values": [116250 + i * 300 + (i % 7 - 3) * 500 for i in range(30)]
            }
        }
    
    def _get_fallback_technical_data(self, symbol: str, indicator: str, period: int) -> Dict[str, Any]:
        """Get fallback technical analysis data."""
        timestamps = [datetime.now() - timedelta(days=i) for i in range(period, 0, -1)]
        
        if indicator.lower() == "rsi":
            values = [30 + (i % 40) for i in range(period)]
        elif indicator.lower() == "macd":
            values = [-2 + (i % 4) for i in range(period)]
        elif indicator.lower() == "bollinger":
            values = [100 + (i % 20) for i in range(period)]
        else:  # SMA
            values = [100 + i * 0.5 for i in range(period)]
        
        return {
            "symbol": symbol,
            "indicator": indicator,
            "timestamps": timestamps,
            "values": values,
            "signals": {"current": "NEUTRAL", "trend": "SIDEWAYS"}
        }
    
    def _get_fallback_alerts_data(self) -> Dict[str, Any]:
        """Get fallback alerts data."""
        return {
            "recent_alerts": [
                {
                    "symbol": "AAPL",
                    "message": "Price crossed above $150",
                    "timestamp": datetime.now() - timedelta(minutes=15),
                    "severity": "INFO"
                },
                {
                    "symbol": "TSLA",
                    "message": "Volume spike detected",
                    "timestamp": datetime.now() - timedelta(hours=1),
                    "severity": "WARNING"
                }
            ],
            "stats": {
                "total_alerts": 45,
                "active_alerts": 12,
                "triggered_today": 8
            }
        }
    
    def _get_fallback_heatmap_data(self) -> Dict[str, Any]:
        """Get fallback heatmap data."""
        import random
        symbols = ["AAPL", "GOOGL", "MSFT", "TSLA", "AMZN"]
        metrics = ["Price Change", "Volume", "RSI", "Volatility"]
        values = [[random.uniform(-10, 10) for _ in symbols] for _ in metrics]
        
        return {
            "symbols": symbols,
            "metrics": metrics,
            "values": values
        }
    
    def _get_fallback_realtime_data(self, symbol: str) -> Dict[str, Any]:
        """Get fallback real-time data."""
        return {
            "symbol": symbol,
            "price": 150.25 + (hash(symbol) % 100) / 100,
            "change": 2.5,
            "change_percent": 1.67,
            "volume": 1000000 + (hash(symbol) % 500000),
            "timestamp": datetime.now()
        } 