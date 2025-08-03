#!/usr/bin/env python3
"""
24/7 Global Stock Market Monitoring System
Main application entry point
"""

import asyncio
import signal
import sys
import logging
from pathlib import Path
from typing import Dict, Any

import uvicorn
from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

# Add src to path for imports
sys.path.append(str(Path(__file__).parent))

from src.utils.config import Config
from src.utils.logger import setup_logging
from src.utils.database import DatabaseManager
from src.utils.cache import CacheManager

from src.collectors.stock_collector import StockDataCollector
from src.collectors.commodity_collector import CommodityDataCollector
from src.collectors.news_collector import NewsCollector

from src.analytics.technical_indicators import TechnicalAnalyzer
from src.analytics.sentiment_analyzer import SentimentAnalyzer
from src.analytics.correlation_analyzer import CorrelationAnalyzer
from src.analytics.anomaly_detector import AnomalyDetector
from src.analytics.analytics_engine import AnalyticsEngine

from src.portfolio.portfolio_manager import PortfolioManager
from src.alerts.alert_manager import AlertManager
from src.dashboard.api import create_dashboard_app, set_dashboard_manager
from src.dashboard.dashboard_manager import DashboardManager
from src.monitoring.metrics_collector import MetricsCollector

class StockMonitorSystem:
    """Main system orchestrator for the stock monitoring system."""
    
    def __init__(self):
        self.config = Config()
        self.logger = setup_logging(self.config)
        self.app = FastAPI(
            title="Stock Market Monitor",
            description="24/7 Global Stock Market Monitoring System",
            version="1.0.0"
        )
        
        # Initialize components
        self.db_manager = None
        self.cache_manager = None
        self.collectors = {}
        self.analyzers = {}
        self.portfolio_manager = None
        self.alert_manager = None
        self.dashboard_manager = None
        self.metrics_collector = None
        
        # Background tasks
        self.tasks = []
        self.running = False
        
    async def initialize(self):
        """Initialize all system components."""
        self.logger.info("Initializing Stock Monitor System...")
        
        try:
            # Initialize database
            self.db_manager = DatabaseManager(self.config)
            await self.db_manager.initialize()
            
            # Initialize cache
            self.cache_manager = CacheManager(self.config)
            await self.cache_manager.initialize()
            
            # Initialize data collectors
            self.collectors = {
                'stock': StockDataCollector(self.config, self.db_manager, self.cache_manager),
                'commodity': CommodityDataCollector(self.config, self.db_manager, self.cache_manager),
                'news': NewsCollector(self.config, self.db_manager, self.cache_manager)
            }
            
            # Initialize analytics engine
            self.analytics_engine = AnalyticsEngine(self.db_manager, self.cache_manager)
            
            # Initialize analyzers
            self.analyzers = {
                'technical': TechnicalAnalyzer(self.config, self.db_manager),
                'sentiment': SentimentAnalyzer(self.config, self.db_manager),
                'correlation': CorrelationAnalyzer(self.config, self.db_manager),
                'anomaly': AnomalyDetector(self.config, self.db_manager)
            }
            
            # Initialize portfolio manager
            self.portfolio_manager = PortfolioManager(self.db_manager, self.cache_manager, self.analytics_engine)
            
            # Initialize alert manager
            self.alert_manager = AlertManager(self.db_manager, self.cache_manager, self.analytics_engine, self.config.dict())
            
            # Initialize dashboard manager
            self.dashboard_manager = DashboardManager(
                self.db_manager,
                self.cache_manager,
                self.analytics_engine,
                self.portfolio_manager,
                self.alert_manager
            )
            
            # Set dashboard manager in API
            set_dashboard_manager(self.dashboard_manager)
            
            # Initialize metrics collector
            self.metrics_collector = MetricsCollector(self.config)
            
            # Setup FastAPI routes
            await self.setup_routes()
            
            # Setup Prometheus metrics
            if self.config.prometheus.enabled:
                Instrumentator().instrument(self.app).expose(self.app)
            
            self.logger.info("System initialization completed successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize system: {e}")
            raise
    
    async def setup_routes(self):
        """Setup FastAPI routes and middleware."""
        from src.dashboard.api import router as dashboard_router
        from src.portfolio.portfolio_api import portfolio_router
        from src.alerts.alert_api import alerts_router
        from src.analytics.api import router as analytics_router
        
        # Set portfolio manager for API
        from src.portfolio.portfolio_api import set_portfolio_manager
        set_portfolio_manager(self.portfolio_manager)
        
        # Include routers
        self.app.include_router(dashboard_router, prefix="/api/dashboard", tags=["dashboard"])
        self.app.include_router(portfolio_router, prefix="/api/portfolio", tags=["portfolio"])
        self.app.include_router(alerts_router, prefix="/api/alerts", tags=["alerts"])
        self.app.include_router(analytics_router, prefix="/api/analytics", tags=["analytics"])
        
        # Health check endpoint
        @self.app.get("/health")
        async def health_check():
            return {
                "status": "healthy",
                "components": {
                    "database": await self.db_manager.is_healthy(),
                    "cache": await self.cache_manager.is_healthy(),
                    "collectors": {name: collector.is_healthy() for name, collector in self.collectors.items()}
                }
            }
    
    async def start_background_tasks(self):
        """Start all background data collection and analysis tasks."""
        self.logger.info("Starting background tasks...")
        
        # Start data collectors
        for name, collector in self.collectors.items():
            task = asyncio.create_task(collector.start())
            self.tasks.append(task)
            self.logger.info(f"Started {name} collector")
        
        # Start analyzers
        for name, analyzer in self.analyzers.items():
            task = asyncio.create_task(analyzer.start())
            self.tasks.append(task)
            self.logger.info(f"Started {name} analyzer")
        
        # Portfolio manager doesn't need background task - it's stateless
        self.logger.info("Portfolio manager initialized")
        
        # Start alert manager monitoring
        await self.alert_manager.start_monitoring()
        
        # Start metrics collector
        metrics_task = asyncio.create_task(self.metrics_collector.start())
        self.tasks.append(metrics_task)
        
        self.running = True
        self.logger.info("All background tasks started")
    
    async def stop_background_tasks(self):
        """Stop all background tasks gracefully."""
        self.logger.info("Stopping background tasks...")
        self.running = False
        
        # Stop alert monitoring
        if self.alert_manager:
            await self.alert_manager.stop_monitoring()
        
        # Cancel all tasks
        for task in self.tasks:
            task.cancel()
        
        # Wait for tasks to complete
        if self.tasks:
            await asyncio.gather(*self.tasks, return_exceptions=True)
        
        self.tasks.clear()
        self.logger.info("All background tasks stopped")
    
    async def shutdown(self):
        """Shutdown the system gracefully."""
        self.logger.info("Shutting down Stock Monitor System...")
        
        await self.stop_background_tasks()
        
        # Close database connections
        if self.db_manager:
            await self.db_manager.close()
        
        # Close cache connections
        if self.cache_manager:
            await self.cache_manager.close()
        
        self.logger.info("System shutdown completed")
    
    def run(self):
        """Run the application."""
        async def main():
            await self.initialize()
            await self.start_background_tasks()
            
            # Setup signal handlers
            def signal_handler(signum, frame):
                self.logger.info(f"Received signal {signum}")
                asyncio.create_task(self.shutdown())
            
            signal.signal(signal.SIGINT, signal_handler)
            signal.signal(signal.SIGTERM, signal_handler)
            
            # Start FastAPI server
            config = uvicorn.Config(
                self.app,
                host=self.config.dashboard.host,
                port=self.config.dashboard.port,
                log_level="info"
            )
            server = uvicorn.Server(config)
            await server.serve()
        
        try:
            asyncio.run(main())
        except KeyboardInterrupt:
            self.logger.info("Received keyboard interrupt")
        except Exception as e:
            self.logger.error(f"Application error: {e}")
            sys.exit(1)

def main():
    """Main entry point."""
    system = StockMonitorSystem()
    system.run()

if __name__ == "__main__":
    main() 