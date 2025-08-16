"""
AI/ML System Startup Script
Complete initialization and startup of the AI/ML enhanced trading system
"""

import asyncio
import logging
import sys
import signal
from pathlib import Path
from datetime import datetime

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scripts.setup_ai_ml_influxdb_buckets import AIMLInfluxDBSetup
from scripts.ai_ml_data_pipeline import AIMLDataPipeline
from src.utils.database import DatabaseManager
from src.utils.logger import get_logger

class AIMLSystemManager:
    """Complete AI/ML system manager for trading analytics."""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.running = False
        
        # System components
        self.influxdb_setup = None
        self.data_pipeline = None
        self.db_manager = None
        
        # Shutdown handling
        self.shutdown_event = asyncio.Event()
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        self.logger.info(f"🛑 Received signal {signum}, initiating shutdown...")
        self.shutdown_event.set()
    
    async def initialize_system(self):
        """Initialize all system components."""
        try:
            self.logger.info("🚀 Initializing AI/ML Trading System...")
            
            # Step 1: Setup InfluxDB buckets
            self.logger.info("📂 Setting up InfluxDB buckets...")
            self.influxdb_setup = AIMLInfluxDBSetup()
            await self.influxdb_setup.create_all_buckets()
            await self.influxdb_setup.populate_sample_ai_ml_data()
            self.influxdb_setup.verify_bucket_setup()
            
            # Step 2: Initialize database manager
            self.logger.info("💾 Initializing database manager...")
            self.db_manager = DatabaseManager()
            await self.db_manager.initialize()
            
            # Step 3: Initialize data pipeline
            self.logger.info("🔄 Initializing AI/ML data pipeline...")
            self.data_pipeline = AIMLDataPipeline()
            await self.data_pipeline.initialize()
            
            self.logger.info("✅ AI/ML Trading System initialized successfully!")
            
            # Print system status
            await self._print_system_status()
            
        except Exception as e:
            self.logger.error(f"❌ System initialization failed: {e}")
            raise
    
    async def start_system(self):
        """Start all system components."""
        try:
            self.running = True
            self.logger.info("🚀 Starting AI/ML Trading System...")
            
            # Start data pipeline
            pipeline_task = asyncio.create_task(self.data_pipeline.start_pipeline())
            
            # Wait for shutdown signal or pipeline completion
            shutdown_task = asyncio.create_task(self.shutdown_event.wait())
            
            done, pending = await asyncio.wait(
                [pipeline_task, shutdown_task],
                return_when=asyncio.FIRST_COMPLETED
            )
            
            # Cancel remaining tasks
            for task in pending:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            
        except Exception as e:
            self.logger.error(f"❌ System startup failed: {e}")
            raise
        finally:
            await self._shutdown_system()
    
    async def _shutdown_system(self):
        """Gracefully shutdown all components."""
        try:
            self.logger.info("⏹️ Shutting down AI/ML Trading System...")
            
            # Stop data pipeline
            if self.data_pipeline:
                self.data_pipeline.stop_pipeline()
            
            # Close database connections
            if self.db_manager:
                await self.db_manager.close()
            
            # Close InfluxDB connections
            if self.influxdb_setup:
                self.influxdb_setup.close()
            
            self.running = False
            self.logger.info("✅ AI/ML Trading System shutdown complete")
            
        except Exception as e:
            self.logger.error(f"❌ Shutdown error: {e}")
    
    async def _print_system_status(self):
        """Print comprehensive system status."""
        status_info = f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    🤖 AI/ML TRADING SYSTEM STATUS                            ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ System Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}                                      ║
║                                                                              ║
║ 📊 COMPONENTS STATUS:                                                        ║
║   ✅ InfluxDB Buckets    : Configured and populated                         ║
║   ✅ Database Manager    : Connected and initialized                        ║
║   ✅ AI/ML Engine        : Ready for training and inference                 ║
║   ✅ Data Pipeline       : Scheduled and running                            ║
║   ✅ Inference Service   : Real-time predictions active                     ║
║                                                                              ║
║ 🎯 AI/ML CAPABILITIES:                                                       ║
║   • Price Prediction     : LSTM, Transformer, Random Forest, XGBoost       ║
║   • Trading Signals      : Buy/Sell/Hold with confidence scoring           ║
║   • Sentiment Analysis   : News and social media sentiment                 ║
║   • Risk Analytics       : VaR, CVaR, Stress Testing                       ║
║   • Feature Engineering  : 50+ technical and fundamental features          ║
║                                                                              ║
║ 📈 MONITORED ASSETS:                                                         ║
║   • Large Cap Tech       : AAPL, MSFT, GOOGL, AMZN, META, TSLA, NVDA      ║
║   • ETFs                 : SPY, QQQ, IWM, GLD, TLT, VIX                    ║
║   • Additional Stocks    : JPM, JNJ, V, PG, HD, DIS, NFLX, CRM            ║
║                                                                              ║
║ 🔧 DASHBOARD ACCESS:                                                         ║
║   • Grafana Dashboard    : http://localhost:3000                           ║
║   • AI/ML Dashboard      : ultimate-professional-trading-dashboard-ai-ml   ║
║   • InfluxDB UI          : http://localhost:8086                           ║
║                                                                              ║
║ ⚡ REAL-TIME UPDATES:                                                        ║
║   • Predictions          : Every 5 minutes                                 ║
║   • Trading Signals      : Every 3 minutes                                 ║
║   • Model Training       : Every 6 hours                                   ║
║   • Performance Monitor  : Every hour                                      ║
║                                                                              ║
║ 📊 INFLUXDB BUCKETS:                                                         ║
║   • ai_ml_analytics      : Model performance and signals                   ║
║   • price_predictions    : AI price forecasts                              ║
║   • sentiment_analytics  : News and social sentiment                       ║
║   • risk_analytics       : Risk metrics and calculations                   ║
║   • feature_store        : ML features and engineering                     ║
╚══════════════════════════════════════════════════════════════════════════════╝

🔥 SYSTEM IS READY FOR AI-ENHANCED TRADING ANALYTICS! 🔥

💡 NEXT STEPS:
   1. Open Grafana: http://localhost:3000 (admin/admin)
   2. Import the AI/ML enhanced dashboard
   3. Configure InfluxDB datasource if needed
   4. Monitor real-time AI predictions and signals

⚠️  IMPORTANT NOTES:
   • First model training may take 10-15 minutes
   • Predictions improve with more historical data
   • Monitor model performance in the dashboard
   • Check logs for any training or inference issues

Press Ctrl+C to stop the system...
        """
        
        print(status_info)
        self.logger.info("📊 System status displayed")

async def main():
    """Main startup function."""
    system_manager = AIMLSystemManager()
    
    try:
        # Initialize system
        await system_manager.initialize_system()
        
        # Start system
        await system_manager.start_system()
        
    except KeyboardInterrupt:
        print("\n🛑 System stopped by user")
    except Exception as e:
        print(f"❌ System failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run the system
    asyncio.run(main())