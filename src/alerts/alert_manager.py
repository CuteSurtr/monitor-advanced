"""
Alert Manager Module

This module provides comprehensive alert management for the stock monitoring system,
including price alerts, technical indicator alerts, anomaly alerts, and portfolio alerts.
"""

import asyncio
import json
import smtplib
import requests
from typing import Dict, List, Optional, Union, Any, Callable
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import pandas as pd
from src.utils.logger import get_logger
from src.utils.database import DatabaseManager
from src.utils.cache import CacheManager
from src.analytics.analytics_engine import AnalyticsEngine

logger = get_logger(__name__)


class AlertType(Enum):
    """Types of alerts supported by the system"""
    PRICE_THRESHOLD = "price_threshold"
    PRICE_CHANGE = "price_change"
    TECHNICAL_INDICATOR = "technical_indicator"
    VOLUME_SPIKE = "volume_spike"
    ANOMALY_DETECTED = "anomaly_detected"
    CORRELATION_CHANGE = "correlation_change"
    VOLATILITY_SPIKE = "volatility_spike"
    PORTFOLIO_ALERT = "portfolio_alert"
    NEWS_ALERT = "news_alert"
    ECONOMIC_EVENT = "economic_event"


class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class NotificationMethod(Enum):
    """Notification methods"""
    EMAIL = "email"
    SMS = "sms"
    WEBHOOK = "webhook"
    PUSH_NOTIFICATION = "push_notification"
    TELEGRAM = "telegram"
    SLACK = "slack"


@dataclass
class AlertCondition:
    """Alert condition configuration"""
    symbol: str
    alert_type: AlertType
    condition: str  # e.g., "price > 100", "rsi < 30"
    threshold: float
    severity: AlertSeverity
    enabled: bool = True
    cooldown_minutes: int = 30
    notification_methods: List[NotificationMethod] = None
    custom_message: Optional[str] = None
    created_at: datetime = None
    
    def __post_init__(self):
        if self.notification_methods is None:
            self.notification_methods = [NotificationMethod.EMAIL]
        if self.created_at is None:
            self.created_at = datetime.now()


@dataclass
class AlertEvent:
    """Alert event that has been triggered"""
    id: str
    condition_id: str
    symbol: str
    alert_type: AlertType
    severity: AlertSeverity
    message: str
    triggered_at: datetime
    data: Dict[str, Any]
    acknowledged: bool = False
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None


class AlertManager:
    """
    Comprehensive alert management system
    
    Handles alert conditions, monitoring, triggering, and notifications
    for various types of market events and conditions.
    """
    
    def __init__(self, db_manager: DatabaseManager, cache_manager: CacheManager,
                 analytics_engine: AnalyticsEngine, config: Dict[str, Any]):
        self.logger = logger
        self.db_manager = db_manager
        self.cache_manager = cache_manager
        self.analytics_engine = analytics_engine
        self.config = config
        
        # Alert storage
        self.alert_conditions: Dict[str, AlertCondition] = {}
        self.alert_events: Dict[str, AlertEvent] = {}
        self.last_triggered: Dict[str, datetime] = {}
        
        # Notification settings
        self.notification_config = config.get('notifications', {})
        self.email_config = self.notification_config.get('email', {})
        self.webhook_config = self.notification_config.get('webhook', {})
        self.telegram_config = self.notification_config.get('telegram', {})
        self.slack_config = self.notification_config.get('slack', {})
        
        # Monitoring state
        self.is_monitoring = False
        self.monitoring_task = None
        
        # Load existing alerts
        self._load_alert_conditions()
    
    def add_alert_condition(self, condition: AlertCondition) -> str:
        """
        Add a new alert condition
        
        Args:
            condition: AlertCondition object
            
        Returns:
            Condition ID
        """
        try:
            condition_id = f"{condition.symbol}_{condition.alert_type.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Validate condition
            self._validate_condition(condition)
            
            # Store condition
            self.alert_conditions[condition_id] = condition
            
            # Save to database
            asyncio.create_task(self._save_alert_condition(condition_id, condition))
            
            self.logger.info(f"Added alert condition: {condition_id}")
            return condition_id
            
        except Exception as e:
            self.logger.error(f"Error adding alert condition: {e}")
            raise
    
    def remove_alert_condition(self, condition_id: str) -> bool:
        """
        Remove an alert condition
        
        Args:
            condition_id: ID of the condition to remove
            
        Returns:
            True if removed successfully
        """
        try:
            if condition_id in self.alert_conditions:
                del self.alert_conditions[condition_id]
                asyncio.create_task(self._delete_alert_condition(condition_id))
                self.logger.info(f"Removed alert condition: {condition_id}")
                return True
            return False
            
        except Exception as e:
            self.logger.error(f"Error removing alert condition: {e}")
            return False
    
    def update_alert_condition(self, condition_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update an existing alert condition
        
        Args:
            condition_id: ID of the condition to update
            updates: Dictionary of fields to update
            
        Returns:
            True if updated successfully
        """
        try:
            if condition_id not in self.alert_conditions:
                return False
            
            condition = self.alert_conditions[condition_id]
            
            # Update fields
            for field, value in updates.items():
                if hasattr(condition, field):
                    setattr(condition, field, value)
            
            # Save to database
            asyncio.create_task(self._save_alert_condition(condition_id, condition))
            
            self.logger.info(f"Updated alert condition: {condition_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating alert condition: {e}")
            return False
    
    def get_alert_conditions(self, symbol: Optional[str] = None) -> List[AlertCondition]:
        """
        Get alert conditions, optionally filtered by symbol
        
        Args:
            symbol: Optional symbol filter
            
        Returns:
            List of AlertCondition objects
        """
        conditions = list(self.alert_conditions.values())
        
        if symbol:
            conditions = [c for c in conditions if c.symbol == symbol]
        
        return conditions
    
    def get_alert_events(self, symbol: Optional[str] = None, 
                        start_date: Optional[datetime] = None,
                        end_date: Optional[datetime] = None) -> List[AlertEvent]:
        """
        Get alert events with optional filtering
        
        Args:
            symbol: Optional symbol filter
            start_date: Optional start date filter
            end_date: Optional end date filter
            
        Returns:
            List of AlertEvent objects
        """
        events = list(self.alert_events.values())
        
        if symbol:
            events = [e for e in events if e.symbol == symbol]
        
        if start_date:
            events = [e for e in events if e.triggered_at >= start_date]
        
        if end_date:
            events = [e for e in events if e.triggered_at <= end_date]
        
        return sorted(events, key=lambda x: x.triggered_at, reverse=True)
    
    async def start_monitoring(self) -> None:
        """Start the alert monitoring process"""
        if self.is_monitoring:
            self.logger.warning("Alert monitoring is already running")
            return
        
        self.is_monitoring = True
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        self.logger.info("Started alert monitoring")
    
    async def stop_monitoring(self) -> None:
        """Stop the alert monitoring process"""
        if not self.is_monitoring:
            return
        
        self.is_monitoring = False
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("Stopped alert monitoring")
    
    async def check_price_alerts(self, symbol: str, current_price: float) -> List[AlertEvent]:
        """
        Check price-based alerts for a symbol
        
        Args:
            symbol: Stock symbol
            current_price: Current price
            
        Returns:
            List of triggered AlertEvent objects
        """
        triggered_events = []
        
        try:
            # Get price-related conditions for this symbol
            price_conditions = [
                c for c in self.alert_conditions.values()
                if c.symbol == symbol and c.enabled and
                c.alert_type in [AlertType.PRICE_THRESHOLD, AlertType.PRICE_CHANGE]
            ]
            
            for condition in price_conditions:
                # Check cooldown
                if not self._check_cooldown(condition):
                    continue
                
                # Check condition
                if condition.alert_type == AlertType.PRICE_THRESHOLD:
                    if self._evaluate_price_threshold(current_price, condition):
                        event = await self._create_alert_event(condition, {
                            'current_price': current_price,
                            'threshold': condition.threshold
                        })
                        triggered_events.append(event)
                
                elif condition.alert_type == AlertType.PRICE_CHANGE:
                    # Get previous price for change calculation
                    previous_price = await self._get_previous_price(symbol)
                    if previous_price:
                        price_change = ((current_price - previous_price) / previous_price) * 100
                        if self._evaluate_price_change(price_change, condition):
                            event = await self._create_alert_event(condition, {
                                'current_price': current_price,
                                'previous_price': previous_price,
                                'price_change_percent': price_change
                            })
                            triggered_events.append(event)
            
        except Exception as e:
            self.logger.error(f"Error checking price alerts for {symbol}: {e}")
        
        return triggered_events
    
    async def check_technical_alerts(self, symbol: str, analytics_result: Any) -> List[AlertEvent]:
        """
        Check technical indicator alerts
        
        Args:
            symbol: Stock symbol
            analytics_result: Analytics result from AnalyticsEngine
            
        Returns:
            List of triggered AlertEvent objects
        """
        triggered_events = []
        
        try:
            # Get technical indicator conditions
            tech_conditions = [
                c for c in self.alert_conditions.values()
                if c.symbol == symbol and c.enabled and
                c.alert_type == AlertType.TECHNICAL_INDICATOR
            ]
            
            for condition in tech_conditions:
                # Check cooldown
                if not self._check_cooldown(condition):
                    continue
                
                # Evaluate technical condition
                if self._evaluate_technical_condition(condition, analytics_result):
                    event = await self._create_alert_event(condition, {
                        'analytics_result': analytics_result
                    })
                    triggered_events.append(event)
            
        except Exception as e:
            self.logger.error(f"Error checking technical alerts for {symbol}: {e}")
        
        return triggered_events
    
    async def check_anomaly_alerts(self, symbol: str, anomaly_result: Any) -> List[AlertEvent]:
        """
        Check anomaly detection alerts
        
        Args:
            symbol: Stock symbol
            anomaly_result: Anomaly detection result
            
        Returns:
            List of triggered AlertEvent objects
        """
        triggered_events = []
        
        try:
            # Get anomaly conditions
            anomaly_conditions = [
                c for c in self.alert_conditions.values()
                if c.symbol == symbol and c.enabled and
                c.alert_type == AlertType.ANOMALY_DETECTED
            ]
            
            for condition in anomaly_conditions:
                # Check cooldown
                if not self._check_cooldown(condition):
                    continue
                
                # Check if anomaly is detected
                if self._evaluate_anomaly_condition(condition, anomaly_result):
                    event = await self._create_alert_event(condition, {
                        'anomaly_result': anomaly_result
                    })
                    triggered_events.append(event)
            
        except Exception as e:
            self.logger.error(f"Error checking anomaly alerts for {symbol}: {e}")
        
        return triggered_events
    
    async def check_volume_alerts(self, symbol: str, current_volume: int, 
                                 avg_volume: float) -> List[AlertEvent]:
        """
        Check volume spike alerts
        
        Args:
            symbol: Stock symbol
            current_volume: Current volume
            avg_volume: Average volume
            
        Returns:
            List of triggered AlertEvent objects
        """
        triggered_events = []
        
        try:
            # Get volume conditions
            volume_conditions = [
                c for c in self.alert_conditions.values()
                if c.symbol == symbol and c.enabled and
                c.alert_type == AlertType.VOLUME_SPIKE
            ]
            
            for condition in volume_conditions:
                # Check cooldown
                if not self._check_cooldown(condition):
                    continue
                
                # Calculate volume ratio
                volume_ratio = current_volume / avg_volume if avg_volume > 0 else 0
                
                if self._evaluate_volume_condition(volume_ratio, condition):
                    event = await self._create_alert_event(condition, {
                        'current_volume': current_volume,
                        'average_volume': avg_volume,
                        'volume_ratio': volume_ratio
                    })
                    triggered_events.append(event)
            
        except Exception as e:
            self.logger.error(f"Error checking volume alerts for {symbol}: {e}")
        
        return triggered_events
    
    async def acknowledge_alert(self, event_id: str, acknowledged_by: str) -> bool:
        """
        Acknowledge an alert event
        
        Args:
            event_id: ID of the alert event
            acknowledged_by: User who acknowledged the alert
            
        Returns:
            True if acknowledged successfully
        """
        try:
            if event_id in self.alert_events:
                event = self.alert_events[event_id]
                event.acknowledged = True
                event.acknowledged_at = datetime.now()
                event.acknowledged_by = acknowledged_by
                
                # Save to database
                await self._save_alert_event(event_id, event)
                
                self.logger.info(f"Alert {event_id} acknowledged by {acknowledged_by}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error acknowledging alert {event_id}: {e}")
            return False
    
    async def send_notifications(self, event: AlertEvent) -> bool:
        """
        Send notifications for an alert event
        
        Args:
            event: AlertEvent to notify about
            
        Returns:
            True if notifications sent successfully
        """
        try:
            condition = self.alert_conditions.get(event.condition_id)
            if not condition:
                return False
            
            success = True
            
            for method in condition.notification_methods:
                try:
                    if method == NotificationMethod.EMAIL:
                        await self._send_email_notification(event, condition)
                    elif method == NotificationMethod.WEBHOOK:
                        await self._send_webhook_notification(event, condition)
                    elif method == NotificationMethod.TELEGRAM:
                        await self._send_telegram_notification(event, condition)
                    elif method == NotificationMethod.SLACK:
                        await self._send_slack_notification(event, condition)
                    else:
                        self.logger.warning(f"Unsupported notification method: {method}")
                        
                except Exception as e:
                    self.logger.error(f"Error sending {method.value} notification: {e}")
                    success = False
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error sending notifications: {e}")
            return False
    
    def _validate_condition(self, condition: AlertCondition) -> None:
        """Validate alert condition"""
        if not condition.symbol:
            raise ValueError("Symbol is required")
        
        if not condition.condition:
            raise ValueError("Condition is required")
        
        if condition.threshold is None:
            raise ValueError("Threshold is required")
        
        if condition.severity not in AlertSeverity:
            raise ValueError("Invalid severity level")
    
    def _check_cooldown(self, condition: AlertCondition) -> bool:
        """Check if enough time has passed since last trigger"""
        condition_id = f"{condition.symbol}_{condition.alert_type.value}"
        
        if condition_id in self.last_triggered:
            last_time = self.last_triggered[condition_id]
            cooldown_time = timedelta(minutes=condition.cooldown_minutes)
            
            if datetime.now() - last_time < cooldown_time:
                return False
        
        return True
    
    def _evaluate_price_threshold(self, current_price: float, condition: AlertCondition) -> bool:
        """Evaluate price threshold condition"""
        try:
            # Parse condition (e.g., "price > 100")
            if ">" in condition.condition:
                return current_price > condition.threshold
            elif "<" in condition.condition:
                return current_price < condition.threshold
            elif ">=" in condition.condition:
                return current_price >= condition.threshold
            elif "<=" in condition.condition:
                return current_price <= condition.threshold
            elif "==" in condition.condition:
                return abs(current_price - condition.threshold) < 0.01
            else:
                return False
        except Exception as e:
            self.logger.error(f"Error evaluating price threshold: {e}")
            return False
    
    def _evaluate_price_change(self, price_change: float, condition: AlertCondition) -> bool:
        """Evaluate price change condition"""
        try:
            if ">" in condition.condition:
                return price_change > condition.threshold
            elif "<" in condition.condition:
                return price_change < condition.threshold
            elif ">=" in condition.condition:
                return price_change >= condition.threshold
            elif "<=" in condition.condition:
                return price_change <= condition.threshold
            else:
                return False
        except Exception as e:
            self.logger.error(f"Error evaluating price change: {e}")
            return False
    
    def _evaluate_technical_condition(self, condition: AlertCondition, analytics_result: Any) -> bool:
        """Evaluate technical indicator condition"""
        try:
            # This is a simplified implementation
            # In practice, you would parse the condition and check specific indicators
            if "rsi" in condition.condition.lower():
                if "rsi" in analytics_result.technical_indicators:
                    rsi_value = analytics_result.technical_indicators["rsi"].values.iloc[-1]
                    if ">" in condition.condition:
                        return rsi_value > condition.threshold
                    elif "<" in condition.condition:
                        return rsi_value < condition.threshold
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error evaluating technical condition: {e}")
            return False
    
    def _evaluate_anomaly_condition(self, condition: AlertCondition, anomaly_result: Any) -> bool:
        """Evaluate anomaly condition"""
        try:
            # Check if any anomalies are detected
            if hasattr(anomaly_result, 'anomalies'):
                return anomaly_result.anomalies.iloc[-1] if len(anomaly_result.anomalies) > 0 else False
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error evaluating anomaly condition: {e}")
            return False
    
    def _evaluate_volume_condition(self, volume_ratio: float, condition: AlertCondition) -> bool:
        """Evaluate volume condition"""
        try:
            if ">" in condition.condition:
                return volume_ratio > condition.threshold
            elif "<" in condition.condition:
                return volume_ratio < condition.threshold
            else:
                return False
        except Exception as e:
            self.logger.error(f"Error evaluating volume condition: {e}")
            return False
    
    async def _create_alert_event(self, condition: AlertCondition, data: Dict[str, Any]) -> AlertEvent:
        """Create an alert event"""
        event_id = f"event_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        # Generate message
        message = condition.custom_message or self._generate_alert_message(condition, data)
        
        event = AlertEvent(
            id=event_id,
            condition_id=f"{condition.symbol}_{condition.alert_type.value}",
            symbol=condition.symbol,
            alert_type=condition.alert_type,
            severity=condition.severity,
            message=message,
            triggered_at=datetime.now(),
            data=data
        )
        
        # Store event
        self.alert_events[event_id] = event
        
        # Update last triggered time
        condition_id = f"{condition.symbol}_{condition.alert_type.value}"
        self.last_triggered[condition_id] = datetime.now()
        
        # Save to database
        await self._save_alert_event(event_id, event)
        
        return event
    
    def _generate_alert_message(self, condition: AlertCondition, data: Dict[str, Any]) -> str:
        """Generate alert message"""
        if condition.alert_type == AlertType.PRICE_THRESHOLD:
            return f"Price alert for {condition.symbol}: ${data.get('current_price', 0):.2f} {condition.condition} {condition.threshold}"
        
        elif condition.alert_type == AlertType.PRICE_CHANGE:
            change = data.get('price_change_percent', 0)
            return f"Price change alert for {condition.symbol}: {change:.2f}% change"
        
        elif condition.alert_type == AlertType.VOLUME_SPIKE:
            ratio = data.get('volume_ratio', 0)
            return f"Volume spike alert for {condition.symbol}: {ratio:.2f}x average volume"
        
        elif condition.alert_type == AlertType.ANOMALY_DETECTED:
            return f"Anomaly detected for {condition.symbol}"
        
        else:
            return f"Alert for {condition.symbol}: {condition.condition}"
    
    async def _get_previous_price(self, symbol: str) -> Optional[float]:
        """Get previous price for change calculation"""
        try:
            # Get from cache first
            cached_data = await self.cache_manager.get_stock_data(symbol)
            if cached_data and len(cached_data) > 1:
                return cached_data.iloc[-2]['close']
            
            # Get from database
            stock_data = await self.db_manager.get_stock_data(symbol, limit=2)
            if stock_data and len(stock_data) > 1:
                return stock_data.iloc[-2]['close']
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting previous price for {symbol}: {e}")
            return None
    
    async def _monitoring_loop(self) -> None:
        """Main monitoring loop"""
        while self.is_monitoring:
            try:
                # Get all enabled conditions
                enabled_conditions = [c for c in self.alert_conditions.values() if c.enabled]
                
                # Group by symbol for efficiency
                symbols = list(set(c.symbol for c in enabled_conditions))
                
                for symbol in symbols:
                    try:
                        # Get current data
                        current_data = await self.cache_manager.get_stock_data(symbol)
                        if current_data is None or current_data.empty:
                            continue
                        
                        latest_data = current_data.iloc[-1]
                        current_price = latest_data['close']
                        current_volume = latest_data['volume']
                        
                        # Check price alerts
                        price_events = await self.check_price_alerts(symbol, current_price)
                        
                        # Check volume alerts
                        avg_volume = current_data['volume'].rolling(20).mean().iloc[-1]
                        volume_events = await self.check_volume_alerts(symbol, current_volume, avg_volume)
                        
                        # Check technical alerts (if analytics available)
                        analytics_result = await self.cache_manager.get_analytics_result(symbol)
                        if analytics_result:
                            tech_events = await self.check_technical_alerts(symbol, analytics_result)
                        else:
                            tech_events = []
                        
                        # Check anomaly alerts
                        anomaly_result = await self.cache_manager.get_anomaly_result(symbol)
                        if anomaly_result:
                            anomaly_events = await self.check_anomaly_alerts(symbol, anomaly_result)
                        else:
                            anomaly_events = []
                        
                        # Send notifications for all triggered events
                        all_events = price_events + volume_events + tech_events + anomaly_events
                        for event in all_events:
                            await self.send_notifications(event)
                    
                    except Exception as e:
                        self.logger.error(f"Error monitoring {symbol}: {e}")
                
                # Wait before next check
                await asyncio.sleep(60)  # Check every minute
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(60)
    
    async def _send_email_notification(self, event: AlertEvent, condition: AlertCondition) -> None:
        """Send email notification"""
        try:
            if not self.email_config:
                return
            
            msg = MIMEMultipart()
            msg['From'] = self.email_config.get('from_email')
            msg['To'] = self.email_config.get('to_email')
            msg['Subject'] = f"Stock Alert: {event.symbol} - {event.severity.value.upper()}"
            
            body = f"""
            Alert Details:
            Symbol: {event.symbol}
            Type: {event.alert_type.value}
            Severity: {event.severity.value}
            Message: {event.message}
            Triggered: {event.triggered_at}
            
            Data: {json.dumps(event.data, indent=2)}
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            with smtplib.SMTP(self.email_config.get('smtp_server'), self.email_config.get('smtp_port')) as server:
                if self.email_config.get('use_tls'):
                    server.starttls()
                server.login(self.email_config.get('username'), self.email_config.get('password'))
                server.send_message(msg)
            
            self.logger.info(f"Email notification sent for {event.symbol}")
            
        except Exception as e:
            self.logger.error(f"Error sending email notification: {e}")
    
    async def _send_webhook_notification(self, event: AlertEvent, condition: AlertCondition) -> None:
        """Send webhook notification"""
        try:
            if not self.webhook_config.get('url'):
                return
            
            payload = {
                'symbol': event.symbol,
                'alert_type': event.alert_type.value,
                'severity': event.severity.value,
                'message': event.message,
                'triggered_at': event.triggered_at.isoformat(),
                'data': event.data
            }
            
            response = requests.post(
                self.webhook_config['url'],
                json=payload,
                headers=self.webhook_config.get('headers', {}),
                timeout=10
            )
            
            if response.status_code == 200:
                self.logger.info(f"Webhook notification sent for {event.symbol}")
            else:
                self.logger.warning(f"Webhook notification failed: {response.status_code}")
            
        except Exception as e:
            self.logger.error(f"Error sending webhook notification: {e}")
    
    async def _send_telegram_notification(self, event: AlertEvent, condition: AlertCondition) -> None:
        """Send Telegram notification"""
        try:
            if not self.telegram_config.get('bot_token') or not self.telegram_config.get('chat_id'):
                return
            
            message = f"""
🚨 Stock Alert: {event.symbol}
Type: {event.alert_type.value}
Severity: {event.severity.value}
Message: {event.message}
Time: {event.triggered_at}
            """
            
            url = f"https://api.telegram.org/bot{self.telegram_config['bot_token']}/sendMessage"
            payload = {
                'chat_id': self.telegram_config['chat_id'],
                'text': message,
                'parse_mode': 'HTML'
            }
            
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                self.logger.info(f"Telegram notification sent for {event.symbol}")
            else:
                self.logger.warning(f"Telegram notification failed: {response.status_code}")
            
        except Exception as e:
            self.logger.error(f"Error sending Telegram notification: {e}")
    
    async def _send_slack_notification(self, event: AlertEvent, condition: AlertCondition) -> None:
        """Send Slack notification"""
        try:
            if not self.slack_config.get('webhook_url'):
                return
            
            # Determine color based on severity
            color_map = {
                AlertSeverity.INFO: "#36a64f",
                AlertSeverity.WARNING: "#ff9500",
                AlertSeverity.CRITICAL: "#ff0000"
            }
            color = color_map.get(event.severity, "#36a64f")
            
            payload = {
                "attachments": [{
                    "color": color,
                    "title": f"Stock Alert: {event.symbol}",
                    "fields": [
                        {"title": "Type", "value": event.alert_type.value, "short": True},
                        {"title": "Severity", "value": event.severity.value, "short": True},
                        {"title": "Message", "value": event.message, "short": False},
                        {"title": "Time", "value": event.triggered_at.strftime('%Y-%m-%d %H:%M:%S'), "short": True}
                    ]
                }]
            }
            
            response = requests.post(self.slack_config['webhook_url'], json=payload, timeout=10)
            
            if response.status_code == 200:
                self.logger.info(f"Slack notification sent for {event.symbol}")
            else:
                self.logger.warning(f"Slack notification failed: {response.status_code}")
            
        except Exception as e:
            self.logger.error(f"Error sending Slack notification: {e}")
    
    async def _load_alert_conditions(self) -> None:
        """Load alert conditions from database"""
        try:
            conditions = await self.db_manager.get_alert_conditions()
            for condition_data in conditions:
                condition = AlertCondition(**condition_data)
                condition_id = f"{condition.symbol}_{condition.alert_type.value}_{condition.created_at.strftime('%Y%m%d_%H%M%S')}"
                self.alert_conditions[condition_id] = condition
            
            self.logger.info(f"Loaded {len(self.alert_conditions)} alert conditions")
            
        except Exception as e:
            self.logger.error(f"Error loading alert conditions: {e}")
    
    async def _save_alert_condition(self, condition_id: str, condition: AlertCondition) -> None:
        """Save alert condition to database"""
        try:
            await self.db_manager.save_alert_condition(condition_id, asdict(condition))
        except Exception as e:
            self.logger.error(f"Error saving alert condition: {e}")
    
    async def _delete_alert_condition(self, condition_id: str) -> None:
        """Delete alert condition from database"""
        try:
            await self.db_manager.delete_alert_condition(condition_id)
        except Exception as e:
            self.logger.error(f"Error deleting alert condition: {e}")
    
    async def _save_alert_event(self, event_id: str, event: AlertEvent) -> None:
        """Save alert event to database"""
        try:
            await self.db_manager.save_alert_event(event_id, asdict(event))
        except Exception as e:
            self.logger.error(f"Error saving alert event: {e}")
    
    def get_alert_statistics(self) -> Dict[str, Any]:
        """Get alert statistics"""
        try:
            total_conditions = len(self.alert_conditions)
            enabled_conditions = len([c for c in self.alert_conditions.values() if c.enabled])
            total_events = len(self.alert_events)
            acknowledged_events = len([e for e in self.alert_events.values() if e.acknowledged])
            
            # Group by severity
            severity_counts = {}
            for event in self.alert_events.values():
                severity = event.severity.value
                severity_counts[severity] = severity_counts.get(severity, 0) + 1
            
            # Group by type
            type_counts = {}
            for event in self.alert_events.values():
                alert_type = event.alert_type.value
                type_counts[alert_type] = type_counts.get(alert_type, 0) + 1
            
            return {
                'total_conditions': total_conditions,
                'enabled_conditions': enabled_conditions,
                'total_events': total_events,
                'acknowledged_events': acknowledged_events,
                'pending_events': total_events - acknowledged_events,
                'severity_distribution': severity_counts,
                'type_distribution': type_counts,
                'monitoring_active': self.is_monitoring
            }
            
        except Exception as e:
            self.logger.error(f"Error getting alert statistics: {e}")
            return {} 