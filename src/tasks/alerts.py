"""
Alert processing tasks for Stock Market Monitor.
"""

import logging
from typing import List, Dict, Any, Optional
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
def process_alert_rules(self):
    """
    Process all active alert rules and trigger alerts when conditions are met.
    """
    try:
        config = get_config()

        logger.info("Processing alert rules")

        alerts_triggered = 0
        rules_processed = 0

        # Mock alert rules - would fetch from database
        alert_rules = [
            {
                "id": 1,
                "symbol": "AAPL",
                "rule_type": "price_change",
                "threshold": 5.0,
                "condition": "greater_than",
                "is_active": True,
            },
            {
                "id": 2,
                "symbol": "TSLA",
                "rule_type": "volume_spike",
                "threshold": 200.0,
                "condition": "greater_than",
                "is_active": True,
            },
        ]

        for rule in alert_rules:
            try:
                rules_processed += 1

                # Check if rule conditions are met
                # This would involve fetching current market data

                # Mock condition checking
                current_value = 150.0  # Would be actual market data
                threshold = rule["threshold"]

                alert_triggered = False

                if rule["rule_type"] == "price_change":
                    # Calculate price change percentage
                    price_change = 3.5  # Mock calculation
                    if price_change > threshold:
                        alert_triggered = True

                elif rule["rule_type"] == "volume_spike":
                    # Calculate volume spike
                    volume_change = 250.0  # Mock calculation
                    if volume_change > threshold:
                        alert_triggered = True

                if alert_triggered:
                    # Create alert record
                    alert_data = {
                        "rule_id": rule["id"],
                        "symbol": rule["symbol"],
                        "alert_type": rule["rule_type"],
                        "threshold": threshold,
                        "current_value": current_value,
                        "triggered_at": datetime.utcnow(),
                        "message": f"{rule['symbol']} {rule['rule_type']} alert: {current_value}",
                    }

                    # Save alert to database
                    # await db_manager.save_alert(alert_data)

                    # Send notification
                    send_alert_notification.delay(alert_data)

                    alerts_triggered += 1
                    logger.info(
                        f"Alert triggered for {rule['symbol']}: {rule['rule_type']}"
                    )

            except Exception as e:
                logger.error(f"Error processing alert rule {rule.get('id')}: {e}")
                continue

        logger.info(
            f"Processed {rules_processed} rules, triggered {alerts_triggered} alerts"
        )
        return {
            "success": True,
            "rules_processed": rules_processed,
            "alerts_triggered": alerts_triggered,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error in process_alert_rules: {e}")
        raise self.retry(countdown=30, exc=e)


@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 2, "countdown": 60},
)
def send_alert_notification(self, alert_data: Dict[str, Any]):
    """
    Send alert notification via configured channels (email, webhook, etc.).

    Args:
        alert_data: Alert data dictionary
    """
    try:
        config = get_config()

        logger.info(
            f"Sending notification for alert: {alert_data.get('symbol')} - {alert_data.get('alert_type')}"
        )

        notifications_sent = 0

        # Email notification
        if config.alerts.email.enabled:
            try:
                # Send email notification
                # await send_email_alert(alert_data)
                notifications_sent += 1
                logger.info("Email notification sent")
            except Exception as e:
                logger.error(f"Failed to send email notification: {e}")

        # Telegram notification
        if config.alerts.telegram.enabled:
            try:
                # Send Telegram notification
                # await send_telegram_alert(alert_data)
                notifications_sent += 1
                logger.info("Telegram notification sent")
            except Exception as e:
                logger.error(f"Failed to send Telegram notification: {e}")

        # Webhook notification
        if config.alerts.webhook.enabled:
            try:
                # Send webhook notification
                # await send_webhook_alert(alert_data)
                notifications_sent += 1
                logger.info("Webhook notification sent")
            except Exception as e:
                logger.error(f"Failed to send webhook notification: {e}")

        # Update alert as notification sent
        # await db_manager.update_alert_notification_status(alert_data['id'], True)

        return {
            "success": True,
            "notifications_sent": notifications_sent,
            "alert_id": alert_data.get("id"),
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error in send_alert_notification: {e}")
        raise self.retry(countdown=60, exc=e)


@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 2, "countdown": 3600},
)
def cleanup_old_alerts(self, days_to_keep: int = 30):
    """
    Clean up old alert records to maintain database performance.

    Args:
        days_to_keep: Number of days of alerts to retain
    """
    try:
        logger.info(f"Cleaning up alerts older than {days_to_keep} days")

        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)

        # Delete old alert records
        # This would be actual database cleanup
        alerts_deleted = 0

        # Mock cleanup - would be actual SQL delete
        # DELETE FROM alerts WHERE triggered_at < cutoff_date AND status = 'RESOLVED'
        alerts_deleted = 150  # Mock number

        logger.info(f"Cleaned up {alerts_deleted} old alert records")
        return {
            "success": True,
            "alerts_deleted": alerts_deleted,
            "cutoff_date": cutoff_date.isoformat(),
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error in cleanup_old_alerts: {e}")
        raise self.retry(countdown=3600, exc=e)


@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3, "countdown": 120},
)
def check_system_alerts(self):
    """
    Check for system-level alerts (database health, API limits, etc.).
    """
    try:
        logger.info("Checking system alerts")

        system_alerts_triggered = 0

        # Check database health
        try:
            # db_health = await db_manager.is_healthy()
            db_health = True  # Mock
            if not db_health:
                alert_data = {
                    "alert_type": "system_database_unhealthy",
                    "severity": "critical",
                    "message": "Database health check failed",
                    "timestamp": datetime.utcnow(),
                }
                send_alert_notification.delay(alert_data)
                system_alerts_triggered += 1
        except Exception as e:
            logger.error(f"Error checking database health: {e}")

        # Check API rate limits
        try:
            # Check if we're approaching API limits
            api_usage = {
                "alpha_vantage": 80,  # Mock percentage
                "polygon": 65,
                "finnhub": 90,
            }

            for api, usage_percent in api_usage.items():
                if usage_percent > 85:  # Alert at 85% usage
                    alert_data = {
                        "alert_type": "api_rate_limit_warning",
                        "severity": "warning",
                        "message": f"{api} API usage at {usage_percent}%",
                        "timestamp": datetime.utcnow(),
                    }
                    send_alert_notification.delay(alert_data)
                    system_alerts_triggered += 1
        except Exception as e:
            logger.error(f"Error checking API limits: {e}")

        # Check disk space
        try:
            # Check available disk space
            disk_usage = 75  # Mock percentage
            if disk_usage > 85:
                alert_data = {
                    "alert_type": "disk_space_warning",
                    "severity": "warning",
                    "message": f"Disk usage at {disk_usage}%",
                    "timestamp": datetime.utcnow(),
                }
                send_alert_notification.delay(alert_data)
                system_alerts_triggered += 1
        except Exception as e:
            logger.error(f"Error checking disk space: {e}")

        logger.info(
            f"System check complete, {system_alerts_triggered} alerts triggered"
        )
        return {
            "success": True,
            "system_alerts_triggered": system_alerts_triggered,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error in check_system_alerts: {e}")
        raise self.retry(countdown=120, exc=e)


@celery_app.task(bind=True)
def create_custom_alert(self, alert_config: Dict[str, Any]):
    """
    Create a custom alert rule.

    Args:
        alert_config: Alert configuration dictionary
    """
    try:
        logger.info(f"Creating custom alert: {alert_config.get('name')}")

        # Validate alert configuration
        required_fields = ["name", "symbol", "rule_type", "threshold", "condition"]
        for field in required_fields:
            if field not in alert_config:
                raise ValueError(f"Missing required field: {field}")

        # Save alert rule to database
        alert_rule = {
            "name": alert_config["name"],
            "symbol": alert_config["symbol"],
            "rule_type": alert_config["rule_type"],
            "threshold": alert_config["threshold"],
            "condition": alert_config["condition"],
            "is_active": alert_config.get("is_active", True),
            "created_at": datetime.utcnow(),
            "user_id": alert_config.get("user_id", "system"),
        }

        # await db_manager.save_alert_rule(alert_rule)

        logger.info(f"Created custom alert: {alert_config['name']}")
        return {
            "success": True,
            "alert_name": alert_config["name"],
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error creating custom alert: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
        }
