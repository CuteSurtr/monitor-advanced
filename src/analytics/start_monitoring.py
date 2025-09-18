"""
Startup script for the comprehensive financial monitoring system
"""

import asyncio
import logging
import signal
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))

from src.analytics.financial_monitor import GlobalFinancialMonitor
from src.analytics.influxdb_sync import influx_sync
from src.utils.config import get_config
from src.utils.logger import setup_logging, get_logger
from src.utils.database import DatabaseManager


async def main():
    """Main startup function for financial monitoring system."""

    # Setup logging
    setup_logging()
    logger = get_logger(__name__)

    logger.info(" Starting Comprehensive Financial Monitoring System")

    try:
        # Load configuration
        config = get_config()
        logger.info(f"Configuration loaded - Database type: {config.database.type}")

        # Initialize database manager
        db_manager = DatabaseManager(config)
        await db_manager.initialize()
        logger.info("Database Manager initialized")

        # Initialize financial monitor
        financial_monitor = GlobalFinancialMonitor(db_manager)
        await financial_monitor.initialize()
        logger.info("Financial Monitor initialized")

        # Setup signal handlers for graceful shutdown
        def signal_handler(signum, frame):
            logger.info(" Shutdown signal received")
            asyncio.create_task(shutdown(financial_monitor, db_manager))

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        # Start monitoring system
        logger.info(" Starting real-time monitoring loops...")
        await financial_monitor.start_monitoring()

    except KeyboardInterrupt:
        logger.info(" Shutdown requested by user")
    except Exception as e:
        logger.error(f"Critical error in monitoring system: {e}")
        sys.exit(1)


async def shutdown(financial_monitor, db_manager):
    """Graceful shutdown of monitoring system."""
    logger = get_logger(__name__)

    try:
        logger.info(" Shutting down monitoring system...")

        await financial_monitor.stop_monitoring()
        logger.info("Financial Monitor stopped")

        await db_manager.close()
        logger.info("Database connections closed")

        logger.info("Shutdown complete")

    except Exception as e:
        logger.error(f"Error during shutdown: {e}")
    finally:
        sys.exit(0)


if __name__ == "__main__":
    # Check if InfluxDB is available
    print(" Checking system requirements...")

    try:
        config = get_config()
        if config.database.type not in ["influxdb", "dual"]:
            print("Warning: Database type is not set to 'influxdb' or 'dual'")
            print("   Update config/config.yaml to enable InfluxDB integration")
        else:
            print("InfluxDB integration enabled")
    except Exception as e:
        print(f"Configuration error: {e}")
        sys.exit(1)

    print(" Starting Financial Monitoring System...")
    asyncio.run(main())
