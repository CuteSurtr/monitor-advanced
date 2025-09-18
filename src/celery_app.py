"""
Celery application for background task processing in Stock Market Monitor.
"""

import os
from celery import Celery
from kombu import Queue, Exchange
from celery.schedules import crontab
from datetime import timedelta

from src.utils.config import get_config

# Get configuration
config = get_config()


# Environment override helper
def _env(k, default):
    import os

    return os.environ.get(k, default)


_default = f"redis://{config.redis.host}:{config.redis.port}/{config.redis.db}"
BROKER_URL = _env("CELERY_BROKER_URL", _default)
BACKEND_URL = _env("CELERY_RESULT_BACKEND", _default)

# Create Celery instance
celery_app = Celery("stock_monitor")

# Celery configuration
celery_app.conf.update(
    # Broker settings
    broker_url=BROKER_URL,
    result_backend=BACKEND_URL,
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Task execution settings
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes
    task_soft_time_limit=240,  # 4 minutes
    # Worker settings
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    worker_disable_rate_limits=False,
    # Result backend settings
    result_expires=3600,  # 1 hour
    # Task routing
    task_routes={
        "src.tasks.data_collection.*": {"queue": "data_collection"},
        "src.tasks.analytics.*": {"queue": "analytics"},
        "src.tasks.alerts.*": {"queue": "alerts"},
        "src.tasks.portfolio.*": {"queue": "portfolio"},
        "src.tasks.monitoring.*": {"queue": "monitoring"},
        "src.tasks.reports.*": {"queue": "reports"},
    },
    # Queue definitions
    task_default_queue="default",
    task_queues=(
        Queue("default", Exchange("default"), routing_key="default"),
        Queue(
            "data_collection",
            Exchange("data_collection"),
            routing_key="data_collection",
        ),
        Queue("analytics", Exchange("analytics"), routing_key="analytics"),
        Queue("alerts", Exchange("alerts"), routing_key="alerts"),
        Queue("portfolio", Exchange("portfolio"), routing_key="portfolio"),
        Queue("monitoring", Exchange("monitoring"), routing_key="monitoring"),
        Queue("reports", Exchange("reports"), routing_key="reports"),
        Queue("priority", Exchange("priority"), routing_key="priority"),
    ),
    # Beat schedule for periodic tasks
    beat_schedule={
        # Data collection tasks
        "collect-stock-data": {
            "task": "src.tasks.data_collection.collect_stock_data",
            "schedule": timedelta(seconds=config.data_collection.stock_data_interval),
            "options": {"queue": "data_collection"},
        },
        "collect-commodity-data": {
            "task": "src.tasks.data_collection.collect_commodity_data",
            "schedule": timedelta(
                seconds=config.data_collection.commodity_data_interval
            ),
            "options": {"queue": "data_collection"},
        },
        "collect-news-data": {
            "task": "src.tasks.data_collection.collect_news_data",
            "schedule": timedelta(seconds=config.data_collection.news_interval),
            "options": {"queue": "data_collection"},
        },
        # Analytics tasks
        "calculate-technical-indicators": {
            "task": "src.tasks.analytics.calculate_technical_indicators",
            "schedule": timedelta(minutes=5),
            "options": {"queue": "analytics"},
        },
        "run-anomaly-detection": {
            "task": "src.tasks.analytics.run_anomaly_detection",
            "schedule": timedelta(minutes=10),
            "options": {"queue": "analytics"},
        },
        "update-ml-predictions": {
            "task": "src.tasks.analytics.update_ml_predictions",
            "schedule": timedelta(minutes=15),
            "options": {"queue": "analytics"},
        },
        "analyze-sentiment": {
            "task": "src.tasks.analytics.analyze_sentiment",
            "schedule": timedelta(seconds=config.data_collection.sentiment_interval),
            "options": {"queue": "analytics"},
        },
        # Portfolio tasks
        "update-portfolio-values": {
            "task": "src.tasks.portfolio.update_portfolio_values",
            "schedule": timedelta(minutes=1),
            "options": {"queue": "portfolio"},
        },
        "calculate-portfolio-metrics": {
            "task": "src.tasks.portfolio.calculate_portfolio_metrics",
            "schedule": timedelta(minutes=5),
            "options": {"queue": "portfolio"},
        },
        "check-rebalancing-opportunities": {
            "task": "src.tasks.portfolio.check_rebalancing_opportunities",
            "schedule": crontab(minute=0, hour="9,15"),  # 9 AM and 3 PM
            "options": {"queue": "portfolio"},
        },
        # Alert tasks
        "process-alert-rules": {
            "task": "src.tasks.alerts.process_alert_rules",
            "schedule": timedelta(seconds=30),
            "options": {"queue": "alerts"},
        },
        "cleanup-old-alerts": {
            "task": "src.tasks.alerts.cleanup_old_alerts",
            "schedule": crontab(minute=0, hour=2),  # 2 AM daily
            "options": {"queue": "alerts"},
        },
        # Monitoring tasks
        "collect-system-metrics": {
            "task": "src.tasks.monitoring.collect_system_metrics",
            "schedule": timedelta(seconds=30),
            "options": {"queue": "monitoring"},
        },
        "health-check": {
            "task": "src.tasks.monitoring.health_check",
            "schedule": timedelta(minutes=1),
            "options": {"queue": "monitoring"},
        },
        "cleanup-old-metrics": {
            "task": "src.tasks.monitoring.cleanup_old_metrics",
            "schedule": crontab(minute=0, hour=3),  # 3 AM daily
            "options": {"queue": "monitoring"},
        },
        # Report tasks
        "generate-daily-reports": {
            "task": "src.tasks.reports.generate_daily_reports",
            "schedule": crontab(minute=0, hour=18),  # 6 PM daily
            "options": {"queue": "reports"},
        },
        "generate-weekly-reports": {
            "task": "src.tasks.reports.generate_weekly_reports",
            "schedule": crontab(minute=0, hour=10, day_of_week=1),  # Monday 10 AM
            "options": {"queue": "reports"},
        },
        # Maintenance tasks
        "database-maintenance": {
            "task": "src.tasks.maintenance.database_maintenance",
            "schedule": crontab(minute=0, hour=1),  # 1 AM daily
            "options": {"queue": "default"},
        },
        "cache-cleanup": {
            "task": "src.tasks.maintenance.cache_cleanup",
            "schedule": crontab(minute=30, hour="*/6"),  # Every 6 hours
            "options": {"queue": "default"},
        },
    },
    # Error handling
    task_annotations={
        "*": {
            "rate_limit": "100/m",
            "retry_policy": {
                "max_retries": 3,
                "interval_start": 0,
                "interval_step": 0.2,
                "interval_max": 0.2,
            },
        },
        "src.tasks.data_collection.*": {
            "rate_limit": "200/m",
            "retry_policy": {
                "max_retries": 5,
                "interval_start": 1,
                "interval_step": 1,
                "interval_max": 10,
            },
        },
        "src.tasks.alerts.*": {
            "rate_limit": "500/m",
            "retry_policy": {
                "max_retries": 2,
                "interval_start": 0,
                "interval_step": 0.1,
                "interval_max": 0.5,
            },
        },
    },
    # Monitoring
    worker_send_task_events=True,
    task_send_sent_event=True,
    # Security
    worker_hijack_root_logger=False,
    worker_log_color=False,
)

# Auto-discover tasks
celery_app.autodiscover_tasks(
    [
        "src.tasks.data_collection",
        "src.tasks.analytics",
        "src.tasks.portfolio",
        "src.tasks.alerts",
        "src.tasks.monitoring",
        "src.tasks.reports",
        "src.tasks.maintenance",
    ]
)


@celery_app.task(bind=True)
def debug_task(self):
    """Debug task for testing Celery setup."""
    print(f"Request: {self.request!r}")
    return "Debug task completed"


# Task failure handler
@celery_app.task(bind=True)
def task_failure_handler(self, task_id, error, traceback):
    """Handle task failures."""
    print(f"Task {task_id} failed: {error}")
    # Here you could send notifications, log to external systems, etc.


# Configure error handling
celery_app.conf.task_reject_on_worker_lost = True
celery_app.conf.task_acks_late = True


if __name__ == "__main__":
    celery_app.start()
