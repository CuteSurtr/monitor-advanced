"""
Comprehensive Financial Monitoring System
Real-time monitoring of global markets with advanced analytics
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import yfinance as yf

from src.analytics.influxdb_sync import influx_sync, MarketData, PortfolioMetrics
from src.analytics.realtime_risk_engine import RealTimeRiskEngine
from src.analytics.options_analyzer import options_analyzer, OptionsAnalyzer
from src.utils.config import get_config
from src.utils.logger import get_logger
from src.utils.database import DatabaseManager


class GlobalFinancialMonitor:
    """Comprehensive real-time financial monitoring system."""

    def __init__(self, db_manager: DatabaseManager):
        self.config = get_config()
        self.logger = get_logger(__name__)
        self.db_manager = db_manager
        self.running = False

        # Initialize analytics engines
        self.risk_engine = RealTimeRiskEngine(db_manager)
        self.options_analyzer = options_analyzer

        # Global markets configuration
        self.global_exchanges = {
            "US": {
                "symbols": [
                    "SPY",
                    "QQQ",
                    "IWM",
                    "AAPL",
                    "MSFT",
                    "GOOGL",
                    "AMZN",
                    "TSLA",
                ],
                "timezone": "America/New_York",
                "trading_hours": {"open": "09:30", "close": "16:00"},
            },
            "EU": {
                "symbols": ["EWG", "EWU", "EWQ", "SAP.DE", "ASML.AS"],
                "timezone": "Europe/London",
                "trading_hours": {"open": "08:00", "close": "16:30"},
            },
            "ASIA": {
                "symbols": ["EWJ", "MCHI", "EEM", "7203.T", "TSM"],
                "timezone": "Asia/Tokyo",
                "trading_hours": {"open": "09:00", "close": "15:00"},
            },
        }

        # Asset classes for monitoring
        self.asset_classes = {
            "equities": ["SPY", "QQQ", "IWM", "VTI", "VXUS"],
            "commodities": ["GLD", "SLV", "USO", "UNG", "DBA"],
            "forex": ["UUP", "FXE", "FXY", "FXB", "FXA"],
            "crypto": ["BTC-USD", "ETH-USD", "ADA-USD", "SOL-USD"],
            "bonds": ["TLT", "IEF", "SHY", "TIP", "LQD"],
            "volatility": ["VIX", "VXX", "UVXY", "SVXY"],
        }

        # Monitoring intervals (seconds)
        self.monitoring_intervals = {
            "market_data": 30,  # 30 seconds
            "portfolio_metrics": 60,  # 1 minute
            "risk_analytics": 300,  # 5 minutes
            "options_analysis": 900,  # 15 minutes
            "global_scan": 1800,  # 30 minutes
        }

    async def initialize(self):
        """Initialize the financial monitoring system."""
        try:
            await influx_sync.initialize()
            await self.risk_engine.initialize()

            self.logger.info("Global Financial Monitor initialized successfully")

        except Exception as e:
            self.logger.error(f"Failed to initialize Financial Monitor: {e}")
            raise

    # =====================================================
    # REAL-TIME MARKET DATA COLLECTION
    # =====================================================

    async def collect_realtime_market_data(self):
        """Collect real-time market data from all asset classes."""
        try:
            all_symbols = []
            for asset_class, symbols in self.asset_classes.items():
                all_symbols.extend(symbols)

            # Batch collect data for performance
            market_data_batch = []

            for symbol in all_symbols:
                try:
                    ticker = yf.Ticker(symbol)
                    data = ticker.history(period="1d", interval="1m")

                    if not data.empty:
                        latest = data.iloc[-1]

                        # Determine asset type
                        asset_type = self._get_asset_type(symbol)
                        exchange = self._get_exchange(symbol)

                        market_data = MarketData(
                            symbol=symbol,
                            timestamp=datetime.now(),
                            price=float(latest["Close"]),
                            volume=float(latest["Volume"]),
                            asset_type=asset_type,
                            exchange=exchange,
                            high=float(latest["High"]),
                            low=float(latest["Low"]),
                            open=float(latest["Open"]),
                        )

                        market_data_batch.append(market_data)

                        # Sync to InfluxDB
                        await influx_sync.sync_market_data(market_data)

                except Exception as e:
                    self.logger.debug(f"Error collecting data for {symbol}: {e}")
                    continue

            # Sync global exchange data
            if market_data_batch:
                await influx_sync.sync_global_exchange_data(market_data_batch)

            self.logger.info(
                f"Collected market data for {len(market_data_batch)} symbols"
            )

        except Exception as e:
            self.logger.error(f"Failed to collect real-time market data: {e}")

    def _get_asset_type(self, symbol: str) -> str:
        """Determine asset type from symbol."""
        for asset_class, symbols in self.asset_classes.items():
            if symbol in symbols:
                if asset_class == "equities":
                    return "stock"
                elif asset_class == "crypto":
                    return "crypto"
                elif asset_class == "forex":
                    return "forex"
                elif asset_class == "commodities":
                    return "commodity"
                else:
                    return "etf"
        return "unknown"

    def _get_exchange(self, symbol: str) -> str:
        """Determine exchange from symbol."""
        if symbol.endswith(".T"):
            return "TSE"
        elif symbol.endswith(".DE"):
            return "FRA"
        elif symbol.endswith(".AS"):
            return "AMS"
        elif "-USD" in symbol:
            return "CRYPTO"
        else:
            return "US"

    # =====================================================
    # VIX AND VOLATILITY MONITORING
    # =====================================================

    async def monitor_vix_and_volatility(self):
        """Monitor VIX and volatility indicators."""
        try:
            # Get VIX data
            vix_ticker = yf.Ticker("^VIX")
            vix_data = vix_ticker.history(period="1d", interval="1m")

            if not vix_data.empty:
                current_vix = float(vix_data["Close"].iloc[-1])

                # Get VIX futures data (simplified)
                vix_futures = {}
                try:
                    # VIX futures symbols (these might need adjustment)
                    futures_symbols = ["^VIX1", "^VIX2", "^VIX3"]
                    for i, symbol in enumerate(futures_symbols):
                        try:
                            future_ticker = yf.Ticker(symbol)
                            future_data = future_ticker.history(period="1d")
                            if not future_data.empty:
                                vix_futures[f"M{i+1}"] = float(
                                    future_data["Close"].iloc[-1]
                                )
                        except:
                            continue
                except:
                    pass

                # Sync VIX data to InfluxDB
                await influx_sync.sync_vix_data(current_vix, vix_futures)

                # Get volatility metrics from risk engine
                vix_metrics = await self.risk_engine.monitor_vix_and_volatility()

                self.logger.info(f"VIX monitoring completed: {current_vix:.2f}")
                return vix_metrics

        except Exception as e:
            self.logger.error(f"Failed to monitor VIX: {e}")
            return {}

    # =====================================================
    # PORTFOLIO ANALYTICS
    # =====================================================

    async def calculate_portfolio_analytics(self, portfolio_id: str = None):
        """Calculate comprehensive portfolio analytics."""
        try:
            # Calculate real-time P&L
            pnl_metrics = await self.risk_engine.calculate_realtime_pnl(portfolio_id)

            # Calculate VaR/CVaR
            var_cvar_metrics = await self.risk_engine.calculate_portfolio_var_cvar(
                portfolio_id
            )

            # Calculate max drawdown
            drawdown_metrics = await self.risk_engine.calculate_max_drawdown(
                portfolio_id
            )

            # Check risk alerts
            risk_alerts = await self.risk_engine.check_risk_alerts(portfolio_id)

            # Combine metrics
            portfolio_analytics = {
                "pnl": pnl_metrics,
                "var_cvar": var_cvar_metrics,
                "drawdown": drawdown_metrics,
                "alerts": [
                    {
                        "type": alert.alert_type,
                        "severity": alert.severity,
                        "message": alert.message,
                        "value": alert.value,
                        "timestamp": alert.timestamp.isoformat(),
                    }
                    for alert in risk_alerts
                ],
                "timestamp": datetime.now().isoformat(),
            }

            # Create portfolio metrics for InfluxDB
            if pnl_metrics and var_cvar_metrics and drawdown_metrics:
                portfolio_metrics = PortfolioMetrics(
                    timestamp=datetime.now(),
                    total_value=pnl_metrics.get("total_market_value", 0),
                    pnl_daily=pnl_metrics.get("daily_pnl", 0),
                    pnl_total=pnl_metrics.get("total_pnl", 0),
                    var_99=var_cvar_metrics.get("var_99", {}).get("historical", 0),
                    cvar_99=var_cvar_metrics.get("var_99", {}).get("cvar", 0),
                    max_drawdown=drawdown_metrics.get("max_drawdown", 0),
                    sharpe_ratio=0.0,  # Would calculate from returns
                    beta=0.0,  # Would calculate vs benchmark
                    positions_count=pnl_metrics.get("position_count", 0),
                )

                await influx_sync.sync_portfolio_metrics(portfolio_metrics)

            self.logger.info("Portfolio analytics completed")
            return portfolio_analytics

        except Exception as e:
            self.logger.error(f"Failed to calculate portfolio analytics: {e}")
            return {}

    # =====================================================
    # OPTIONS CHAIN ANALYSIS
    # =====================================================

    async def analyze_options_chains(self):
        """Analyze options chains for key symbols."""
        try:
            options_results = {}

            # Analyze key equity options
            key_symbols = ["SPY", "QQQ", "AAPL", "MSFT", "TSLA", "NVDA"]

            for symbol in key_symbols:
                try:
                    analysis = await self.options_analyzer.analyze_options_chain(symbol)
                    if analysis:
                        options_results[symbol] = {
                            "underlying_price": analysis.underlying_price,
                            "call_put_ratio": analysis.call_put_ratio,
                            "max_pain": analysis.max_pain,
                            "gamma_exposure": analysis.gamma_exposure,
                            "dealer_positioning": analysis.dealer_positioning,
                            "timestamp": analysis.analysis_timestamp.isoformat(),
                        }

                        self.logger.info(f"Options analysis completed for {symbol}")

                except Exception as e:
                    self.logger.error(f"Failed to analyze options for {symbol}: {e}")
                    continue

            return options_results

        except Exception as e:
            self.logger.error(f"Failed to analyze options chains: {e}")
            return {}

    # =====================================================
    # COMPREHENSIVE DASHBOARD DATA
    # =====================================================

    async def get_dashboard_data(self, portfolio_id: str = None) -> Dict[str, Any]:
        """Get comprehensive dashboard data for Grafana/frontend."""
        try:
            # Get real-time data from InfluxDB
            influx_data = await influx_sync.get_realtime_dashboard_data()

            # Get portfolio analytics
            portfolio_data = await self.calculate_portfolio_analytics(portfolio_id)

            # Get VIX data
            vix_data = await self.monitor_vix_and_volatility()

            # Get options data
            options_data = await self.analyze_options_chains()

            # Combine everything
            dashboard_data = {
                "timestamp": datetime.now().isoformat(),
                "market_status": self._get_market_status(),
                "portfolio": portfolio_data,
                "vix": vix_data,
                "options": options_data,
                "influx_metrics": influx_data,
                "system_health": {
                    "influxdb_connected": True,
                    "postgres_connected": True,
                    "data_freshness": "current",
                },
            }

            return dashboard_data

        except Exception as e:
            self.logger.error(f"Failed to get dashboard data: {e}")
            return {"error": str(e), "timestamp": datetime.now().isoformat()}

    def _get_market_status(self) -> Dict[str, str]:
        """Get current market status for major exchanges."""
        now = datetime.now()
        hour = now.hour

        status = {}

        # US Markets (EST)
        if 9 <= hour < 16:
            status["US"] = "open"
        elif 4 <= hour < 9 or 16 <= hour < 20:
            status["US"] = "extended"
        else:
            status["US"] = "closed"

        # European Markets (GMT)
        if 8 <= hour < 16:
            status["EU"] = "open"
        else:
            status["EU"] = "closed"

        # Asian Markets (JST)
        if 0 <= hour < 6:  # Adjusted for timezone difference
            status["ASIA"] = "open"
        else:
            status["ASIA"] = "closed"

        return status

    # =====================================================
    # MONITORING LOOPS
    # =====================================================

    async def start_monitoring(self):
        """Start all monitoring loops."""
        self.running = True
        self.logger.info("Starting Global Financial Monitoring System")

        # Start concurrent monitoring tasks
        tasks = [
            asyncio.create_task(self._market_data_loop()),
            asyncio.create_task(self._portfolio_analytics_loop()),
            asyncio.create_task(self._risk_monitoring_loop()),
            asyncio.create_task(self._options_monitoring_loop()),
            asyncio.create_task(self._volatility_monitoring_loop()),
        ]

        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            self.logger.error(f"Error in monitoring system: {e}")
        finally:
            self.running = False

    async def _market_data_loop(self):
        """Market data collection loop."""
        while self.running:
            try:
                await self.collect_realtime_market_data()
                await asyncio.sleep(self.monitoring_intervals["market_data"])
            except Exception as e:
                self.logger.error(f"Error in market data loop: {e}")
                await asyncio.sleep(60)

    async def _portfolio_analytics_loop(self):
        """Portfolio analytics loop."""
        while self.running:
            try:
                await self.calculate_portfolio_analytics()
                await asyncio.sleep(self.monitoring_intervals["portfolio_metrics"])
            except Exception as e:
                self.logger.error(f"Error in portfolio analytics loop: {e}")
                await asyncio.sleep(120)

    async def _risk_monitoring_loop(self):
        """Risk monitoring loop."""
        while self.running:
            try:
                await self.risk_engine.check_risk_alerts()
                await asyncio.sleep(self.monitoring_intervals["risk_analytics"])
            except Exception as e:
                self.logger.error(f"Error in risk monitoring loop: {e}")
                await asyncio.sleep(300)

    async def _options_monitoring_loop(self):
        """Options monitoring loop."""
        while self.running:
            try:
                await self.analyze_options_chains()
                await asyncio.sleep(self.monitoring_intervals["options_analysis"])
            except Exception as e:
                self.logger.error(f"Error in options monitoring loop: {e}")
                await asyncio.sleep(600)

    async def _volatility_monitoring_loop(self):
        """Volatility monitoring loop."""
        while self.running:
            try:
                await self.monitor_vix_and_volatility()
                await asyncio.sleep(self.monitoring_intervals["portfolio_metrics"])
            except Exception as e:
                self.logger.error(f"Error in volatility monitoring loop: {e}")
                await asyncio.sleep(180)

    async def stop_monitoring(self):
        """Stop all monitoring."""
        self.running = False
        await self.risk_engine.stop_monitoring()
        await influx_sync.close()
        self.logger.info("Global Financial Monitor stopped")


# Global instance
financial_monitor = None
