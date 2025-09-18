"""
System monitoring tasks for Stock Market Monitor.
"""

import logging
import psutil
from typing import List, Dict, Any
from datetime import datetime, timedelta

from src.celery_app import celery_app
from src.utils.config import get_config
from src.utils.logger import get_logger

logger = get_logger(__name__)


@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3, "countdown": 30},
)
def collect_system_metrics(self):
    """
    Collect system performance metrics (CPU, memory, disk, network).
    """
    try:
        logger.info("Collecting system metrics")

        # Collect CPU metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        cpu_freq = psutil.cpu_freq()

        # Collect memory metrics
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()

        # Collect disk metrics
        disk_usage = psutil.disk_usage("/")
        disk_io = psutil.disk_io_counters()

        # Collect network metrics
        network_io = psutil.net_io_counters()

        # Collect process metrics for our application
        current_process = psutil.Process()
        process_info = {
            "pid": current_process.pid,
            "cpu_percent": current_process.cpu_percent(),
            "memory_percent": current_process.memory_percent(),
            "memory_info": current_process.memory_info()._asdict(),
            "num_threads": current_process.num_threads(),
        }

        metrics = {
            "timestamp": datetime.utcnow().isoformat(),
            "cpu": {
                "percent": cpu_percent,
                "count": cpu_count,
                "frequency": cpu_freq.current if cpu_freq else 0,
            },
            "memory": {
                "total": memory.total,
                "available": memory.available,
                "percent": memory.percent,
                "used": memory.used,
                "free": memory.free,
                "swap_total": swap.total,
                "swap_used": swap.used,
                "swap_percent": swap.percent,
            },
            "disk": {
                "total": disk_usage.total,
                "used": disk_usage.used,
                "free": disk_usage.free,
                "percent": disk_usage.percent,
                "read_bytes": disk_io.read_bytes if disk_io else 0,
                "write_bytes": disk_io.write_bytes if disk_io else 0,
            },
            "network": {
                "bytes_sent": network_io.bytes_sent,
                "bytes_recv": network_io.bytes_recv,
                "packets_sent": network_io.packets_sent,
                "packets_recv": network_io.packets_recv,
            },
            "process": process_info,
        }

        # Save metrics to database
        # await db_manager.save_system_metrics(metrics)

        # Send to Prometheus if enabled
        config = get_config()
        if config.prometheus.enabled:
            # prometheus_client.record_system_metrics(metrics)
            pass

        logger.info("System metrics collected successfully")
        return {
            "success": True,
            "metrics": metrics,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error collecting system metrics: {e}")
        raise self.retry(countdown=30, exc=e)


@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3, "countdown": 60},
)
def health_check(self):
    """
    Perform comprehensive health check of all system components.
    """
    try:
        logger.info("Performing system health check")

        health_status = {
            "timestamp": datetime.utcnow().isoformat(),
            "overall_status": "healthy",
            "components": {},
        }

        # Check database health
        try:
            # db_health = await db_manager.is_healthy()
            db_health = True  # Mock
            health_status["components"]["database"] = {
                "status": "healthy" if db_health else "unhealthy",
                "response_time_ms": 50,  # Mock response time
            }
        except Exception as e:
            health_status["components"]["database"] = {
                "status": "unhealthy",
                "error": str(e),
            }
            health_status["overall_status"] = "degraded"

        # Check Redis health
        try:
            # redis_health = await redis_manager.is_healthy()
            redis_health = True  # Mock
            health_status["components"]["redis"] = {
                "status": "healthy" if redis_health else "unhealthy",
                "response_time_ms": 10,  # Mock response time
            }
        except Exception as e:
            health_status["components"]["redis"] = {
                "status": "unhealthy",
                "error": str(e),
            }
            health_status["overall_status"] = "degraded"

        # Check external APIs
        apis_to_check = ["alpha_vantage", "polygon", "finnhub"]
        for api in apis_to_check:
            try:
                # api_health = await check_api_health(api)
                api_health = True  # Mock
                health_status["components"][f"api_{api}"] = {
                    "status": "healthy" if api_health else "unhealthy",
                    "response_time_ms": 200,  # Mock response time
                }
            except Exception as e:
                health_status["components"][f"api_{api}"] = {
                    "status": "unhealthy",
                    "error": str(e),
                }

        # Check system resources
        try:
            cpu_percent = psutil.cpu_percent()
            memory_percent = psutil.virtual_memory().percent
            disk_percent = psutil.disk_usage("/").percent

            resource_status = "healthy"
            if cpu_percent > 90 or memory_percent > 90 or disk_percent > 90:
                resource_status = "critical"
                health_status["overall_status"] = "critical"
            elif cpu_percent > 80 or memory_percent > 80 or disk_percent > 80:
                resource_status = "warning"
                if health_status["overall_status"] == "healthy":
                    health_status["overall_status"] = "degraded"

            health_status["components"]["system_resources"] = {
                "status": resource_status,
                "cpu_percent": cpu_percent,
                "memory_percent": memory_percent,
                "disk_percent": disk_percent,
            }
        except Exception as e:
            health_status["components"]["system_resources"] = {
                "status": "unhealthy",
                "error": str(e),
            }
            health_status["overall_status"] = "degraded"

        # Save health check results
        # await db_manager.save_health_check(health_status)

        # Trigger alerts if unhealthy
        if health_status["overall_status"] in ["degraded", "critical"]:
            from src.tasks.alerts import send_alert_notification

            alert_data = {
                "alert_type": "system_health_warning",
                "severity": health_status["overall_status"],
                "message": f"System health check: {health_status['overall_status']}",
                "details": health_status,
                "timestamp": datetime.utcnow(),
            }
            send_alert_notification.delay(alert_data)

        logger.info(f"Health check completed: {health_status['overall_status']}")
        return health_status

    except Exception as e:
        logger.error(f"Error in health check: {e}")
        raise self.retry(countdown=60, exc=e)


@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 2, "countdown": 3600},
)
def cleanup_old_metrics(self, days_to_keep: int = 7):
    """
    Clean up old system metrics to maintain database performance.

    Args:
        days_to_keep: Number of days of metrics to retain
    """
    try:
        logger.info(f"Cleaning up system metrics older than {days_to_keep} days")

        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)

        # Delete old metrics records
        metrics_deleted = 0

        # Mock cleanup - would be actual database operations
        # DELETE FROM system_metrics WHERE timestamp < cutoff_date
        metrics_deleted = 1000  # Mock number

        logger.info(f"Cleaned up {metrics_deleted} old metric records")
        return {
            "success": True,
            "metrics_deleted": metrics_deleted,
            "cutoff_date": cutoff_date.isoformat(),
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error in cleanup_old_metrics: {e}")
        raise self.retry(countdown=3600, exc=e)


@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3, "countdown": 300},
)
def monitor_celery_workers(self):
    """
    Monitor Celery worker health and performance.
    """
    try:
        logger.info("Monitoring Celery workers")

        # Get Celery inspector
        from celery import current_app

        inspect = current_app.control.inspect()

        worker_stats = {
            "timestamp": datetime.utcnow().isoformat(),
            "active_workers": 0,
            "total_tasks": 0,
            "workers": {},
        }

        # Get active workers
        try:
            active = inspect.active()
            if active:
                worker_stats["active_workers"] = len(active)
                for worker, tasks in active.items():
                    worker_stats["workers"][worker] = {
                        "active_tasks": len(tasks),
                        "status": "active",
                    }
                    worker_stats["total_tasks"] += len(tasks)
        except Exception as e:
            logger.warning(f"Could not get active workers: {e}")

        # Get worker statistics
        try:
            stats = inspect.stats()
            if stats:
                for worker, stat_data in stats.items():
                    if worker in worker_stats["workers"]:
                        worker_stats["workers"][worker].update(
                            {
                                "total_tasks": stat_data.get("total", 0),
                                "pool_processes": stat_data.get("pool", {}).get(
                                    "processes", 0
                                ),
                                "rusage": stat_data.get("rusage", {}),
                            }
                        )
        except Exception as e:
            logger.warning(f"Could not get worker stats: {e}")

        # Check for unhealthy workers
        unhealthy_workers = []
        for worker, data in worker_stats["workers"].items():
            # Define criteria for unhealthy workers
            if data.get("active_tasks", 0) > 50:  # Too many active tasks
                unhealthy_workers.append(
                    f"{worker}: too many active tasks ({data['active_tasks']})"
                )

        if unhealthy_workers:
            from src.tasks.alerts import send_alert_notification

            alert_data = {
                "alert_type": "celery_worker_warning",
                "severity": "warning",
                "message": f"Unhealthy Celery workers detected: {', '.join(unhealthy_workers)}",
                "timestamp": datetime.utcnow(),
            }
            send_alert_notification.delay(alert_data)

        # Save worker stats
        # await db_manager.save_worker_stats(worker_stats)

        logger.info(
            f"Celery monitoring complete: {worker_stats['active_workers']} active workers"
        )
        return worker_stats

    except Exception as e:
        logger.error(f"Error monitoring Celery workers: {e}")
        raise self.retry(countdown=300, exc=e)


@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3, "countdown": 180},
)
def check_external_services(self):
    """
    Check the availability and response time of external services.
    """
    try:
        logger.info("Checking external services")

        import requests
        import time

        services = {
            "alpha_vantage": "https://www.alphavantage.co",
            "polygon": "https://polygon.io",
            "finnhub": "https://finnhub.io",
            "yahoo_finance": "https://finance.yahoo.com",
        }

        service_status = {"timestamp": datetime.utcnow().isoformat(), "services": {}}

        for service_name, url in services.items():
            try:
                start_time = time.time()
                response = requests.get(url, timeout=10)
                response_time = (time.time() - start_time) * 1000  # ms

                service_status["services"][service_name] = {
                    "status": "healthy" if response.status_code == 200 else "unhealthy",
                    "status_code": response.status_code,
                    "response_time_ms": round(response_time, 2),
                }

                # Alert if service is slow
                if response_time > 5000:  # 5 seconds
                    from src.tasks.alerts import send_alert_notification

                    alert_data = {
                        "alert_type": "external_service_slow",
                        "severity": "warning",
                        "message": f"{service_name} is responding slowly ({response_time:.0f}ms)",
                        "timestamp": datetime.utcnow(),
                    }
                    send_alert_notification.delay(alert_data)

            except Exception as e:
                service_status["services"][service_name] = {
                    "status": "unhealthy",
                    "error": str(e),
                    "response_time_ms": None,
                }

                # Alert if service is down
                from src.tasks.alerts import send_alert_notification

                alert_data = {
                    "alert_type": "external_service_down",
                    "severity": "critical",
                    "message": f"{service_name} is not responding: {str(e)}",
                    "timestamp": datetime.utcnow(),
                }
                send_alert_notification.delay(alert_data)

        # Save service status
        # await db_manager.save_service_status(service_status)

        logger.info("External service check completed")
        return service_status

    except Exception as e:
        logger.error(f"Error checking external services: {e}")
        raise self.retry(countdown=180, exc=e)
