#!/usr/bin/env python3
"""
System startup script for Stock Market Monitor.
Orchestrates the startup of all system components.
"""

import os
import sys
import asyncio
import signal
import subprocess
import time
from pathlib import Path
from typing import List, Dict, Any
import json
import yaml

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from src.utils.structured_logger import get_logger, setup_logging
from src.utils.config import get_config
from src.utils.database import get_database_manager
from src.utils.cache import get_cache_manager
from src.monitoring.health_checker import HealthChecker
from src.monitoring.prometheus_client import initialize_prometheus

logger = get_logger(__name__)


class SystemManager:
    """Manages the startup and shutdown of all system components."""
    
    def __init__(self):
        """Initialize system manager."""
        self.config = get_config()
        self.processes: Dict[str, subprocess.Popen] = {}
        self.running = False
        self.startup_complete = False
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info("Received shutdown signal", signal=signum)
        asyncio.create_task(self.shutdown())
        
    async def start(self):
        """Start all system components."""
        logger.info("Starting Stock Market Monitor system")
        
        try:
            # Setup logging
            setup_logging()
            logger.info("Logging system initialized")
            
            # Initialize database
            await self._initialize_database()
            
            # Initialize cache
            await self._initialize_cache()
            
            # Start monitoring
            await self._start_monitoring()
            
            # Start background workers
            await self._start_workers()
            
            # Start web server
            await self._start_web_server()
            
            # Start data collection
            await self._start_data_collection()
            
            # Perform health check
            await self._perform_health_check()
            
            self.running = True
            self.startup_complete = True
            
            logger.info("System startup completed successfully")
            
            # Keep running
            await self._run_main_loop()
            
        except Exception as e:
            logger.error("System startup failed", error=str(e), exc_info=True)
            await self.shutdown()
            sys.exit(1)
            
    async def _initialize_database(self):
        """Initialize database connection."""
        logger.info("Initializing database connection")
        
        try:
            db_manager = get_database_manager()
            await db_manager.initialize()
            
            # Test connection
            result = await db_manager.execute_query("SELECT 1")
            if result:
                logger.info("Database connection established")
            else:
                raise Exception("Database connection test failed")
                
        except Exception as e:
            logger.error("Database initialization failed", error=str(e))
            raise
            
    async def _initialize_cache(self):
        """Initialize cache connection."""
        logger.info("Initializing cache connection")
        
        try:
            cache_manager = get_cache_manager()
            await cache_manager.initialize()
            
            # Test cache
            test_key = "system_startup_test"
            await cache_manager.set(test_key, "test_value", ttl=10)
            result = await cache_manager.get(test_key)
            
            if result == "test_value":
                logger.info("Cache connection established")
                await cache_manager.delete(test_key)
            else:
                raise Exception("Cache connection test failed")
                
        except Exception as e:
            logger.error("Cache initialization failed", error=str(e))
            raise
            
    async def _start_monitoring(self):
        """Start monitoring services."""
        logger.info("Starting monitoring services")
        
        try:
            # Initialize Prometheus
            prometheus_client = initialize_prometheus(
                port=self.config.prometheus.get('port', 8000)
            )
            logger.info("Prometheus metrics server started", 
                       port=self.config.prometheus.get('port', 8000))
            
        except Exception as e:
            logger.error("Monitoring initialization failed", error=str(e))
            raise
            
    async def _start_workers(self):
        """Start background worker processes."""
        logger.info("Starting background workers")
        
        try:
            # Start Celery worker
            if self.config.get('celery', {}).get('enabled', True):
                worker_cmd = [
                    sys.executable, '-m', 'celery',
                    '-A', 'src.celery_app',
                    'worker',
                    '--loglevel=info',
                    f'--concurrency={self.config.performance.get("max_workers", 4)}',
                    '--prefetch-multiplier=1'
                ]
                
                worker_process = subprocess.Popen(
                    worker_cmd,
                    cwd=Path.cwd(),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                
                self.processes['celery_worker'] = worker_process
                logger.info("Celery worker started", pid=worker_process.pid)
                
                # Start Celery beat scheduler
                beat_cmd = [
                    sys.executable, '-m', 'celery',
                    '-A', 'src.celery_app',
                    'beat',
                    '--loglevel=info'
                ]
                
                beat_process = subprocess.Popen(
                    beat_cmd,
                    cwd=Path.cwd(),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                
                self.processes['celery_beat'] = beat_process
                logger.info("Celery beat started", pid=beat_process.pid)
                
        except Exception as e:
            logger.error("Worker startup failed", error=str(e))
            raise
            
    async def _start_web_server(self):
        """Start the web server."""
        logger.info("Starting web server")
        
        try:
            # Start FastAPI server
            server_cmd = [
                sys.executable, '-m', 'uvicorn',
                'src.main:app',
                '--host', self.config.dashboard.get('host', '0.0.0.0'),
                '--port', str(self.config.dashboard.get('port', 8080)),
                '--workers', str(self.config.performance.get('max_workers', 4))
            ]
            
            if self.config.dashboard.get('reload', False):
                server_cmd.append('--reload')
                
            server_process = subprocess.Popen(
                server_cmd,
                cwd=Path.cwd(),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            self.processes['web_server'] = server_process
            logger.info("Web server started", 
                       pid=server_process.pid,
                       host=self.config.dashboard.get('host', '0.0.0.0'),
                       port=self.config.dashboard.get('port', 8080))
            
            # Wait a moment for server to start
            await asyncio.sleep(2)
            
        except Exception as e:
            logger.error("Web server startup failed", error=str(e))
            raise
            
    async def _start_data_collection(self):
        """Start data collection processes."""
        logger.info("Starting data collection")
        
        try:
            # This would trigger initial data collection tasks
            # For now, just log that it's started
            logger.info("Data collection services initialized")
            
        except Exception as e:
            logger.error("Data collection startup failed", error=str(e))
            raise
            
    async def _perform_health_check(self):
        """Perform initial system health check."""
        logger.info("Performing system health check")
        
        try:
            health_checker = HealthChecker(
                get_database_manager(),
                get_cache_manager()
            )
            
            health_result = await health_checker.check_all_health()
            
            if health_result['overall_status'] == 'healthy':
                logger.info("System health check passed")
            else:
                logger.warning("System health check shows issues", 
                             status=health_result['overall_status'],
                             issues=health_result.get('unhealthy_checks', 0))
                             
        except Exception as e:
            logger.error("Health check failed", error=str(e))
            # Don't raise - this is not critical for startup
            
    async def _run_main_loop(self):
        """Run the main system loop."""
        logger.info("System is running")
        
        try:
            while self.running:
                # Check process health
                await self._check_process_health()
                
                # Sleep for a bit
                await asyncio.sleep(30)
                
        except Exception as e:
            logger.error("Main loop error", error=str(e))
            await self.shutdown()
            
    async def _check_process_health(self):
        """Check health of spawned processes."""
        for name, process in list(self.processes.items()):
            if process.poll() is not None:
                # Process has terminated
                logger.error("Process terminated unexpectedly", 
                           process_name=name, 
                           return_code=process.returncode)
                
                # Remove from processes dict
                del self.processes[name]
                
                # Optionally restart critical processes
                if name in ['web_server']:
                    logger.info("Attempting to restart critical process", 
                              process_name=name)
                    # Restart logic would go here
                    
    async def shutdown(self):
        """Shutdown all system components gracefully."""
        if not self.running:
            return
            
        logger.info("Starting system shutdown")
        self.running = False
        
        try:
            # Stop all processes
            for name, process in self.processes.items():
                logger.info("Stopping process", process_name=name, pid=process.pid)
                
                try:
                    # Send SIGTERM first
                    process.terminate()
                    
                    # Wait for graceful shutdown
                    try:
                        process.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        # Force kill if necessary
                        logger.warning("Force killing process", process_name=name)
                        process.kill()
                        process.wait()
                        
                    logger.info("Process stopped", process_name=name)
                    
                except Exception as e:
                    logger.error("Error stopping process", 
                               process_name=name, error=str(e))
                    
            # Close database connections
            try:
                db_manager = get_database_manager()
                await db_manager.close()
                logger.info("Database connections closed")
            except Exception as e:
                logger.error("Error closing database", error=str(e))
                
            # Close cache connections
            try:
                cache_manager = get_cache_manager()
                await cache_manager.close()
                logger.info("Cache connections closed")
            except Exception as e:
                logger.error("Error closing cache", error=str(e))
                
            logger.info("System shutdown completed")
            
        except Exception as e:
            logger.error("Error during shutdown", error=str(e))
            
    def get_status(self) -> Dict[str, Any]:
        """Get current system status."""
        return {
            'running': self.running,
            'startup_complete': self.startup_complete,
            'processes': {
                name: {
                    'pid': process.pid,
                    'running': process.poll() is None
                }
                for name, process in self.processes.items()
            },
            'timestamp': time.time()
        }


async def main():
    """Main entry point."""
    print("Stock Market Monitor - Starting System...")
    
    try:
        system_manager = SystemManager()
        await system_manager.start()
        
    except KeyboardInterrupt:
        print("\nReceived interrupt signal")
    except Exception as e:
        print(f"System startup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Run the system
    asyncio.run(main())