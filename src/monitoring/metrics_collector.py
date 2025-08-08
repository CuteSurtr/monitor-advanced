"""
Metrics collector for gathering various system and application metrics.
"""

import time
import logging
import psutil
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from collections import defaultdict, deque
import threading
import json

from ..utils.database import DatabaseManager
from ..utils.cache import CacheManager
from .prometheus_client import get_prometheus_client

logger = logging.getLogger(__name__)


@dataclass
class MetricPoint:
    """A single metric data point."""
    timestamp: datetime
    name: str
    value: float
    labels: Dict[str, str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'timestamp': self.timestamp.isoformat(),
            'name': self.name,
            'value': self.value,
            'labels': self.labels
        }


class MetricsCollector:
    """Collects and aggregates various system and application metrics."""
    
    def __init__(self, db_manager: DatabaseManager, cache_manager: CacheManager):
        """
        Initialize metrics collector.
        
        Args:
            db_manager: Database manager instance
            cache_manager: Cache manager instance
        """
        self.db_manager = db_manager
        self.cache_manager = cache_manager
        self.prometheus_client = get_prometheus_client()
        
        # Metric storage
        self.metrics_buffer = deque(maxlen=10000)
        self.metric_aggregates = defaultdict(list)
        
        # Collection settings
        self.collection_interval = 30  # seconds
        self.retention_days = 90
        
        # Background collection
        self._collection_thread = None
        self._stop_collection = threading.Event()
        self._is_collecting = False
        
        # Metric definitions
        self.system_metrics = [
            'cpu_usage', 'memory_usage', 'disk_usage', 'network_io',
            'process_count', 'load_average'
        ]
        
        self.application_metrics = [
            'active_connections', 'request_rate', 'response_time',
            'error_rate', 'cache_hit_rate', 'queue_size'
        ]
        
        self.business_metrics = [
            'portfolio_value', 'total_alerts', 'api_calls',
            'data_points_collected', 'prediction_accuracy'
        ]
        
    async def start_collection(self):
        """Start metrics collection."""
        if not self._is_collecting:
            self._is_collecting = True
            self._stop_collection.clear()
            
            self._collection_thread = threading.Thread(
                target=self._collection_loop,
                daemon=True
            )
            self._collection_thread.start()
            
            logger.info("Metrics collection started")
            
    def stop_collection(self):
        """Stop metrics collection."""
        if self._is_collecting:
            self._stop_collection.set()
            if self._collection_thread:
                self._collection_thread.join(timeout=10)
            self._is_collecting = False
            logger.info("Metrics collection stopped")
            
    def _collection_loop(self):
        """Main collection loop."""
        while not self._stop_collection.is_set():
            try:
                start_time = time.time()
                
                # Collect all metrics
                self._collect_system_metrics()
                self._collect_application_metrics()
                self._collect_business_metrics()
                
                # Store metrics
                self._store_metrics()
                
                # Update aggregates
                self._update_aggregates()
                
                collection_time = time.time() - start_time
                logger.debug(f"Metrics collection completed in {collection_time:.2f}s")
                
                # Wait for next collection
                time.sleep(max(0, self.collection_interval - collection_time))
                
            except Exception as e:
                logger.error(f"Error in metrics collection: {e}")
                time.sleep(self.collection_interval)
                
    def _collect_system_metrics(self):
        """Collect system-level metrics."""
        timestamp = datetime.utcnow()
        
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=None)
            self._add_metric('system_cpu_usage', cpu_percent, timestamp)
            
            # Memory metrics
            memory = psutil.virtual_memory()
            self._add_metric('system_memory_usage', memory.percent, timestamp)
            self._add_metric('system_memory_available', memory.available, timestamp)
            
            # Disk metrics
            for disk in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(disk.mountpoint)
                    self._add_metric(
                        'system_disk_usage',
                        usage.percent,
                        timestamp,
                        {'mountpoint': disk.mountpoint}
                    )
                except PermissionError:
                    continue
                    
            # Network metrics
            net_io = psutil.net_io_counters()
            self._add_metric('system_network_bytes_sent', net_io.bytes_sent, timestamp)
            self._add_metric('system_network_bytes_recv', net_io.bytes_recv, timestamp)
            
            # Process metrics
            process_count = len(psutil.pids())
            self._add_metric('system_process_count', process_count, timestamp)
            
            # Load average (Unix-like systems)
            try:
                load_avg = psutil.getloadavg()
                self._add_metric('system_load_1m', load_avg[0], timestamp)
                self._add_metric('system_load_5m', load_avg[1], timestamp)
                self._add_metric('system_load_15m', load_avg[2], timestamp)
            except AttributeError:
                # Windows doesn't have load average
                pass
                
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            
    def _collect_application_metrics(self):
        """Collect application-level metrics."""
        timestamp = datetime.utcnow()
        
        try:
            # Database connection metrics
            db_stats = self.db_manager.get_connection_stats()
            if db_stats:
                self._add_metric('app_db_connections_active', db_stats.get('active', 0), timestamp)
                self._add_metric('app_db_connections_idle', db_stats.get('idle', 0), timestamp)
                
            # Cache metrics
            cache_stats = self.cache_manager.get_stats()
            if cache_stats:
                self._add_metric('app_cache_hit_rate', cache_stats.get('hit_rate', 0), timestamp)
                self._add_metric('app_cache_memory_usage', cache_stats.get('memory_usage', 0), timestamp)
                self._add_metric('app_cache_key_count', cache_stats.get('key_count', 0), timestamp)
                
            # Application process metrics
            current_process = psutil.Process()
            self._add_metric('app_cpu_usage', current_process.cpu_percent(), timestamp)
            self._add_metric('app_memory_usage', current_process.memory_info().rss, timestamp)
            self._add_metric('app_thread_count', current_process.num_threads(), timestamp)
            
        except Exception as e:
            logger.error(f"Error collecting application metrics: {e}")
            
    def _collect_business_metrics(self):
        """Collect business-specific metrics."""
        timestamp = datetime.utcnow()
        
        try:
            # Get business metrics from cache or database
            metrics_data = self.cache_manager.get('business_metrics')
            if not metrics_data:
                metrics_data = self._fetch_business_metrics_from_db()
                if metrics_data:
                    self.cache_manager.set('business_metrics', metrics_data, ttl=300)
                    
            if metrics_data:
                for metric_name, value in metrics_data.items():
                    self._add_metric(f'business_{metric_name}', value, timestamp)
                    
        except Exception as e:
            logger.error(f"Error collecting business metrics: {e}")
            
    def _fetch_business_metrics_from_db(self) -> Optional[Dict[str, float]]:
        """Fetch business metrics from database."""
        try:
            # This would be implemented based on your actual database schema
            # For now, return placeholder metrics
            return {
                'total_portfolios': 0,
                'total_alerts_today': 0,
                'api_calls_today': 0,
                'data_points_collected_today': 0
            }
        except Exception as e:
            logger.error(f"Error fetching business metrics: {e}")
            return None
            
    def _add_metric(self, name: str, value: float, timestamp: datetime, labels: Optional[Dict[str, str]] = None):
        """Add a metric point."""
        if labels is None:
            labels = {}
            
        metric_point = MetricPoint(
            timestamp=timestamp,
            name=name,
            value=value,
            labels=labels
        )
        
        self.metrics_buffer.append(metric_point)
        
        # Update Prometheus
        if hasattr(self.prometheus_client, 'record_custom_metric'):
            self.prometheus_client.record_custom_metric(name, value, labels)
            
    def _store_metrics(self):
        """Store metrics to database."""
        if not self.metrics_buffer:
            return
            
        try:
            # Convert metrics to storage format
            metrics_to_store = []
            while self.metrics_buffer:
                metric = self.metrics_buffer.popleft()
                metrics_to_store.append(metric.to_dict())
                
            # Batch insert to database
            if metrics_to_store:
                self._batch_insert_metrics(metrics_to_store)
                
        except Exception as e:
            logger.error(f"Error storing metrics: {e}")
            
    def _batch_insert_metrics(self, metrics: List[Dict[str, Any]]):
        """Batch insert metrics to database."""
        try:
            # This would be implemented based on your database schema
            # For now, just log the metrics
            logger.debug(f"Would store {len(metrics)} metrics to database")
        except Exception as e:
            logger.error(f"Error in batch insert: {e}")
            
    def _update_aggregates(self):
        """Update metric aggregates."""
        try:
            # Calculate hourly, daily, and weekly aggregates
            # This is a simplified implementation
            current_time = datetime.utcnow()
            
            # Clear old aggregates
            cutoff_time = current_time - timedelta(days=self.retention_days)
            for key in list(self.metric_aggregates.keys()):
                self.metric_aggregates[key] = [
                    point for point in self.metric_aggregates[key]
                    if point['timestamp'] > cutoff_time
                ]
                
        except Exception as e:
            logger.error(f"Error updating aggregates: {e}")
            
    def get_metric_summary(self, metric_name: str, time_range: str = '1h') -> Dict[str, Any]:
        """Get metric summary for a time range."""
        try:
            # Parse time range
            if time_range == '1h':
                start_time = datetime.utcnow() - timedelta(hours=1)
            elif time_range == '24h':
                start_time = datetime.utcnow() - timedelta(days=1)
            elif time_range == '7d':
                start_time = datetime.utcnow() - timedelta(days=7)
            else:
                start_time = datetime.utcnow() - timedelta(hours=1)
                
            # Get metrics from cache/database
            # This would be implemented based on your storage
            return {
                'metric_name': metric_name,
                'time_range': time_range,
                'start_time': start_time.isoformat(),
                'summary': 'Not implemented yet'
            }
            
        except Exception as e:
            logger.error(f"Error getting metric summary: {e}")
            return {'error': str(e)}
            
    def get_health_status(self) -> Dict[str, Any]:
        """Get collector health status."""
        return {
            'is_collecting': self._is_collecting,
            'collection_interval': self.collection_interval,
            'buffer_size': len(self.metrics_buffer),
            'last_collection': datetime.utcnow().isoformat() if self._is_collecting else None
        }
        
    def export_metrics(self, format_type: str = 'json') -> str:
        """Export current metrics."""
        try:
            if format_type == 'json':
                metrics_data = []
                for metric in list(self.metrics_buffer):
                    metrics_data.append(metric.to_dict())
                return json.dumps(metrics_data, indent=2)
            else:
                return "Unsupported format"
        except Exception as e:
            logger.error(f"Error exporting metrics: {e}")
            return json.dumps({'error': str(e)})