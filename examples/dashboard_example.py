#!/usr/bin/env python3
"""
Dashboard Example Script

This script demonstrates how to use the dashboard functionality
of the stock monitoring system.
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent / "src"))

from src.utils.config import Config
from src.utils.logger import setup_logging
from src.utils.database import DatabaseManager
from src.utils.cache import CacheManager
from src.analytics.analytics_engine import AnalyticsEngine
from src.portfolio.portfolio_manager import PortfolioManager
from src.alerts.alert_manager import AlertManager
from src.dashboard.dashboard_manager import DashboardManager


async def main():
    """Main function to demonstrate dashboard functionality."""
    print("Ä Starting Dashboard Example")
    print("=" * 50)
    
    try:
        # Initialize configuration
        config = Config()
        logger = setup_logging(config)
        
        print("ã Initializing system components...")
        
        # Initialize database
        db_manager = DatabaseManager(config)
        await db_manager.initialize()
        print("Database initialized")
        
        # Initialize cache
        cache_manager = CacheManager(config)
        await cache_manager.initialize()
        print("Cache initialized")
        
        # Initialize analytics engine
        analytics_engine = AnalyticsEngine(db_manager, cache_manager)
        print("Analytics engine initialized")
        
        # Initialize portfolio manager
        portfolio_manager = PortfolioManager(config, db_manager)
        print("Portfolio manager initialized")
        
        # Initialize alert manager
        alert_manager = AlertManager(db_manager, cache_manager, analytics_engine, config.dict())
        print("Alert manager initialized")
        
        # Initialize dashboard manager
        dashboard_manager = DashboardManager(
            db_manager,
            cache_manager,
            analytics_engine,
            portfolio_manager,
            alert_manager
        )
        print("Dashboard manager initialized")
        
        print("\nä Dashboard Functionality Demo")
        print("=" * 50)
        
        # Demo 1: Market Overview
        print("\n1. à Market Overview")
        print("-" * 30)
        try:
            market_data = await dashboard_manager.get_market_overview()
            print(f"Total Symbols: {market_data['total_symbols']}")
            print(f"Gainers: {market_data['gainers']}")
            print(f"Losers: {market_data['losers']}")
            print(f"Active Alerts: {market_data['active_alerts']}")
            print(f"Top Movers: {len(market_data['top_movers'])} stocks")
        except Exception as e:
            print(f"Error getting market overview: {e}")
        
        # Demo 2: Portfolio Data
        print("\n2. º Portfolio Data")
        print("-" * 30)
        try:
            portfolio_data = await dashboard_manager.get_portfolio_data()
            summary = portfolio_data['summary']
            print(f"Total Value: ${summary['total_value']:,.2f}")
            print(f"Total P&L: ${summary['total_pnl']:,.2f}")
            print(f"P&L %: {summary['total_pnl_percent']:.2f}%")
            print(f"Positions: {summary['positions_count']}")
        except Exception as e:
            print(f"Error getting portfolio data: {e}")
        
        # Demo 3: Available Symbols
        print("\n3. ã Available Symbols")
        print("-" * 30)
        try:
            symbols = await dashboard_manager.get_available_symbols()
            print(f"Available symbols: {len(symbols)}")
            print(f"Sample symbols: {symbols[:5]}")
        except Exception as e:
            print(f"Error getting symbols: {e}")
        
        # Demo 4: Technical Analysis
        print("\n4. ä Technical Analysis")
        print("-" * 30)
        try:
            symbol = "AAPL"
            indicator = "rsi"
            analysis = await dashboard_manager.get_technical_analysis(symbol, indicator, period=30)
            print(f"Symbol: {analysis['symbol']}")
            print(f"Indicator: {analysis['indicator']}")
            print(f"Data points: {len(analysis['values'])}")
            print(f"Signals: {analysis['signals']}")
        except Exception as e:
            print(f"Error getting technical analysis: {e}")
        
        # Demo 5: Alerts Data
        print("\n5. î Alerts Data")
        print("-" * 30)
        try:
            alerts_data = await dashboard_manager.get_alerts_data()
            stats = alerts_data['stats']
            print(f"Total Alerts: {stats['total_alerts']}")
            print(f"Active Alerts: {stats['active_alerts']}")
            print(f"Triggered Today: {stats['triggered_today']}")
            print(f"Recent Alerts: {len(alerts_data['recent_alerts'])}")
        except Exception as e:
            print(f"Error getting alerts data: {e}")
        
        # Demo 6: Market Heatmap
        print("\n6. ∫Market Heatmap")
        print("-" * 30)
        try:
            heatmap_data = await dashboard_manager.get_market_heatmap()
            print(f"Symbols: {len(heatmap_data['symbols'])}")
            print(f"Metrics: {len(heatmap_data['metrics'])}")
            print(f"Data matrix: {len(heatmap_data['values'])}x{len(heatmap_data['values'][0]) if heatmap_data['values'] else 0}")
        except Exception as e:
            print(f"Error getting market heatmap: {e}")
        
        # Demo 7: Real-time Data
        print("\n7. Real-time Data")
        print("-" * 30)
        try:
            symbol = "AAPL"
            realtime_data = await dashboard_manager.get_real_time_data(symbol)
            print(f"Symbol: {realtime_data['symbol']}")
            print(f"Price: ${realtime_data['price']:.2f}")
            print(f"Change: {realtime_data['change']:.2f}")
            print(f"Change %: {realtime_data['change_percent']:.2f}%")
            print(f"Volume: {realtime_data['volume']:,}")
            print(f"Timestamp: {realtime_data['timestamp']}")
        except Exception as e:
            print(f"Error getting real-time data: {e}")
        
        print("\nâ Dashboard demo completed successfully!")
        print("\n° To access the web dashboard:")
        print("   1. Start the main application: python src/main.py")
        print("   2. Open your browser to: http://localhost:8000/api/dashboard/")
        print("   3. Navigate through the different sections")
        
    except Exception as e:
        print(f"Error in dashboard demo: {e}")
        raise
    finally:
        # Cleanup
        try:
            await db_manager.close()
            await cache_manager.close()
            print("\nπ Cleanup completed")
        except:
            pass


if __name__ == "__main__":
    asyncio.run(main()) 