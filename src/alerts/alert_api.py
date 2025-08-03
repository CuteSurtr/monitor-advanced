"""
Alert API Module

This module provides FastAPI routes for alert management, including
creating, updating, and monitoring alert conditions and events.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
from enum import Enum
import asyncio

from src.alerts.alert_manager import (
    AlertManager, AlertCondition, AlertEvent, AlertType, 
    AlertSeverity, NotificationMethod
)
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Pydantic models for API requests/responses
class AlertTypeEnum(str, Enum):
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


class AlertSeverityEnum(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class NotificationMethodEnum(str, Enum):
    EMAIL = "email"
    SMS = "sms"
    WEBHOOK = "webhook"
    PUSH_NOTIFICATION = "push_notification"
    TELEGRAM = "telegram"
    SLACK = "slack"


class AlertConditionCreate(BaseModel):
    symbol: str = Field(..., description="Stock symbol")
    alert_type: AlertTypeEnum = Field(..., description="Type of alert")
    condition: str = Field(..., description="Alert condition (e.g., 'price > 100')")
    threshold: float = Field(..., description="Threshold value")
    severity: AlertSeverityEnum = Field(..., description="Alert severity")
    enabled: bool = Field(True, description="Whether alert is enabled")
    cooldown_minutes: int = Field(30, description="Cooldown period in minutes")
    notification_methods: List[NotificationMethodEnum] = Field(
        [NotificationMethodEnum.EMAIL], 
        description="Notification methods"
    )
    custom_message: Optional[str] = Field(None, description="Custom alert message")


class AlertConditionUpdate(BaseModel):
    condition: Optional[str] = None
    threshold: Optional[float] = None
    severity: Optional[AlertSeverityEnum] = None
    enabled: Optional[bool] = None
    cooldown_minutes: Optional[int] = None
    notification_methods: Optional[List[NotificationMethodEnum]] = None
    custom_message: Optional[str] = None


class AlertConditionResponse(BaseModel):
    id: str
    symbol: str
    alert_type: AlertTypeEnum
    condition: str
    threshold: float
    severity: AlertSeverityEnum
    enabled: bool
    cooldown_minutes: int
    notification_methods: List[NotificationMethodEnum]
    custom_message: Optional[str]
    created_at: datetime


class AlertEventResponse(BaseModel):
    id: str
    condition_id: str
    symbol: str
    alert_type: AlertTypeEnum
    severity: AlertSeverityEnum
    message: str
    triggered_at: datetime
    data: Dict[str, Any]
    acknowledged: bool
    acknowledged_at: Optional[datetime]
    acknowledged_by: Optional[str]


class AlertStatisticsResponse(BaseModel):
    total_conditions: int
    enabled_conditions: int
    total_events: int
    acknowledged_events: int
    pending_events: int
    severity_distribution: Dict[str, int]
    type_distribution: Dict[str, int]
    monitoring_active: bool


class AlertAcknowledgeRequest(BaseModel):
    acknowledged_by: str = Field(..., description="User acknowledging the alert")


# Router
router = APIRouter(prefix="/alerts", tags=["alerts"])


def get_alert_manager() -> AlertManager:
    """Dependency to get AlertManager instance"""
    # This would be injected from the main app
    # For now, we'll use a global instance
    from src.main import alert_manager
    return alert_manager


@router.post("/conditions", response_model=AlertConditionResponse)
async def create_alert_condition(
    condition: AlertConditionCreate,
    alert_manager: AlertManager = Depends(get_alert_manager)
):
    """
    Create a new alert condition
    """
    try:
        # Convert to AlertCondition object
        alert_condition = AlertCondition(
            symbol=condition.symbol,
            alert_type=AlertType(condition.alert_type.value),
            condition=condition.condition,
            threshold=condition.threshold,
            severity=AlertSeverity(condition.severity.value),
            enabled=condition.enabled,
            cooldown_minutes=condition.cooldown_minutes,
            notification_methods=[NotificationMethod(m.value) for m in condition.notification_methods],
            custom_message=condition.custom_message
        )
        
        # Add condition
        condition_id = alert_manager.add_alert_condition(alert_condition)
        
        # Return response
        return AlertConditionResponse(
            id=condition_id,
            symbol=alert_condition.symbol,
            alert_type=AlertTypeEnum(alert_condition.alert_type.value),
            condition=alert_condition.condition,
            threshold=alert_condition.threshold,
            severity=AlertSeverityEnum(alert_condition.severity.value),
            enabled=alert_condition.enabled,
            cooldown_minutes=alert_condition.cooldown_minutes,
            notification_methods=[NotificationMethodEnum(m.value) for m in alert_condition.notification_methods],
            custom_message=alert_condition.custom_message,
            created_at=alert_condition.created_at
        )
        
    except Exception as e:
        logger.error(f"Error creating alert condition: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/conditions", response_model=List[AlertConditionResponse])
async def get_alert_conditions(
    symbol: Optional[str] = Query(None, description="Filter by symbol"),
    alert_manager: AlertManager = Depends(get_alert_manager)
):
    """
    Get alert conditions, optionally filtered by symbol
    """
    try:
        conditions = alert_manager.get_alert_conditions(symbol)
        
        responses = []
        for condition in conditions:
            # Find the condition ID
            condition_id = None
            for cid, c in alert_manager.alert_conditions.items():
                if c == condition:
                    condition_id = cid
                    break
            
            if condition_id:
                responses.append(AlertConditionResponse(
                    id=condition_id,
                    symbol=condition.symbol,
                    alert_type=AlertTypeEnum(condition.alert_type.value),
                    condition=condition.condition,
                    threshold=condition.threshold,
                    severity=AlertSeverityEnum(condition.severity.value),
                    enabled=condition.enabled,
                    cooldown_minutes=condition.cooldown_minutes,
                    notification_methods=[NotificationMethodEnum(m.value) for m in condition.notification_methods],
                    custom_message=condition.custom_message,
                    created_at=condition.created_at
                ))
        
        return responses
        
    except Exception as e:
        logger.error(f"Error getting alert conditions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conditions/{condition_id}", response_model=AlertConditionResponse)
async def get_alert_condition(
    condition_id: str,
    alert_manager: AlertManager = Depends(get_alert_manager)
):
    """
    Get a specific alert condition by ID
    """
    try:
        if condition_id not in alert_manager.alert_conditions:
            raise HTTPException(status_code=404, detail="Alert condition not found")
        
        condition = alert_manager.alert_conditions[condition_id]
        
        return AlertConditionResponse(
            id=condition_id,
            symbol=condition.symbol,
            alert_type=AlertTypeEnum(condition.alert_type.value),
            condition=condition.condition,
            threshold=condition.threshold,
            severity=AlertSeverityEnum(condition.severity.value),
            enabled=condition.enabled,
            cooldown_minutes=condition.cooldown_minutes,
            notification_methods=[NotificationMethodEnum(m.value) for m in condition.notification_methods],
            custom_message=condition.custom_message,
            created_at=condition.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting alert condition: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/conditions/{condition_id}", response_model=AlertConditionResponse)
async def update_alert_condition(
    condition_id: str,
    updates: AlertConditionUpdate,
    alert_manager: AlertManager = Depends(get_alert_manager)
):
    """
    Update an alert condition
    """
    try:
        # Convert updates to dict
        update_dict = {}
        if updates.condition is not None:
            update_dict['condition'] = updates.condition
        if updates.threshold is not None:
            update_dict['threshold'] = updates.threshold
        if updates.severity is not None:
            update_dict['severity'] = AlertSeverity(updates.severity.value)
        if updates.enabled is not None:
            update_dict['enabled'] = updates.enabled
        if updates.cooldown_minutes is not None:
            update_dict['cooldown_minutes'] = updates.cooldown_minutes
        if updates.notification_methods is not None:
            update_dict['notification_methods'] = [NotificationMethod(m.value) for m in updates.notification_methods]
        if updates.custom_message is not None:
            update_dict['custom_message'] = updates.custom_message
        
        # Update condition
        success = alert_manager.update_alert_condition(condition_id, update_dict)
        if not success:
            raise HTTPException(status_code=404, detail="Alert condition not found")
        
        # Return updated condition
        condition = alert_manager.alert_conditions[condition_id]
        return AlertConditionResponse(
            id=condition_id,
            symbol=condition.symbol,
            alert_type=AlertTypeEnum(condition.alert_type.value),
            condition=condition.condition,
            threshold=condition.threshold,
            severity=AlertSeverityEnum(condition.severity.value),
            enabled=condition.enabled,
            cooldown_minutes=condition.cooldown_minutes,
            notification_methods=[NotificationMethodEnum(m.value) for m in condition.notification_methods],
            custom_message=condition.custom_message,
            created_at=condition.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating alert condition: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/conditions/{condition_id}")
async def delete_alert_condition(
    condition_id: str,
    alert_manager: AlertManager = Depends(get_alert_manager)
):
    """
    Delete an alert condition
    """
    try:
        success = alert_manager.remove_alert_condition(condition_id)
        if not success:
            raise HTTPException(status_code=404, detail="Alert condition not found")
        
        return {"message": "Alert condition deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting alert condition: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/events", response_model=List[AlertEventResponse])
async def get_alert_events(
    symbol: Optional[str] = Query(None, description="Filter by symbol"),
    start_date: Optional[datetime] = Query(None, description="Start date filter"),
    end_date: Optional[datetime] = Query(None, description="End date filter"),
    limit: int = Query(100, description="Maximum number of events to return"),
    alert_manager: AlertManager = Depends(get_alert_manager)
):
    """
    Get alert events with optional filtering
    """
    try:
        events = alert_manager.get_alert_events(symbol, start_date, end_date)
        
        # Limit results
        events = events[:limit]
        
        responses = []
        for event in events:
            responses.append(AlertEventResponse(
                id=event.id,
                condition_id=event.condition_id,
                symbol=event.symbol,
                alert_type=AlertTypeEnum(event.alert_type.value),
                severity=AlertSeverityEnum(event.severity.value),
                message=event.message,
                triggered_at=event.triggered_at,
                data=event.data,
                acknowledged=event.acknowledged,
                acknowledged_at=event.acknowledged_at,
                acknowledged_by=event.acknowledged_by
            ))
        
        return responses
        
    except Exception as e:
        logger.error(f"Error getting alert events: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/events/{event_id}", response_model=AlertEventResponse)
async def get_alert_event(
    event_id: str,
    alert_manager: AlertManager = Depends(get_alert_manager)
):
    """
    Get a specific alert event by ID
    """
    try:
        if event_id not in alert_manager.alert_events:
            raise HTTPException(status_code=404, detail="Alert event not found")
        
        event = alert_manager.alert_events[event_id]
        
        return AlertEventResponse(
            id=event.id,
            condition_id=event.condition_id,
            symbol=event.symbol,
            alert_type=AlertTypeEnum(event.alert_type.value),
            severity=AlertSeverityEnum(event.severity.value),
            message=event.message,
            triggered_at=event.triggered_at,
            data=event.data,
            acknowledged=event.acknowledged,
            acknowledged_at=event.acknowledged_at,
            acknowledged_by=event.acknowledged_by
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting alert event: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/events/{event_id}/acknowledge")
async def acknowledge_alert_event(
    event_id: str,
    request: AlertAcknowledgeRequest,
    alert_manager: AlertManager = Depends(get_alert_manager)
):
    """
    Acknowledge an alert event
    """
    try:
        success = await alert_manager.acknowledge_alert(event_id, request.acknowledged_by)
        if not success:
            raise HTTPException(status_code=404, detail="Alert event not found")
        
        return {"message": "Alert event acknowledged successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error acknowledging alert event: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics", response_model=AlertStatisticsResponse)
async def get_alert_statistics(
    alert_manager: AlertManager = Depends(get_alert_manager)
):
    """
    Get alert statistics
    """
    try:
        stats = alert_manager.get_alert_statistics()
        return AlertStatisticsResponse(**stats)
        
    except Exception as e:
        logger.error(f"Error getting alert statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/monitoring/start")
async def start_alert_monitoring(
    alert_manager: AlertManager = Depends(get_alert_manager)
):
    """
    Start alert monitoring
    """
    try:
        await alert_manager.start_monitoring()
        return {"message": "Alert monitoring started successfully"}
        
    except Exception as e:
        logger.error(f"Error starting alert monitoring: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/monitoring/stop")
async def stop_alert_monitoring(
    alert_manager: AlertManager = Depends(get_alert_manager)
):
    """
    Stop alert monitoring
    """
    try:
        await alert_manager.stop_monitoring()
        return {"message": "Alert monitoring stopped successfully"}
        
    except Exception as e:
        logger.error(f"Error stopping alert monitoring: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/monitoring/status")
async def get_monitoring_status(
    alert_manager: AlertManager = Depends(get_alert_manager)
):
    """
    Get alert monitoring status
    """
    try:
        return {
            "is_monitoring": alert_manager.is_monitoring,
            "active_conditions": len([c for c in alert_manager.alert_conditions.values() if c.enabled]),
            "total_conditions": len(alert_manager.alert_conditions)
        }
        
    except Exception as e:
        logger.error(f"Error getting monitoring status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test-notification")
async def test_notification(
    symbol: str = Query(..., description="Symbol to test"),
    alert_type: AlertTypeEnum = Query(..., description="Alert type to test"),
    notification_method: NotificationMethodEnum = Query(..., description="Notification method to test"),
    alert_manager: AlertManager = Depends(get_alert_manager)
):
    """
    Test notification delivery
    """
    try:
        # Create a test alert event
        test_event = AlertEvent(
            id="test_event",
            condition_id="test_condition",
            symbol=symbol,
            alert_type=AlertType(alert_type.value),
            severity=AlertSeverity.INFO,
            message=f"Test alert for {symbol}",
            triggered_at=datetime.now(),
            data={"test": True}
        )
        
        # Create a test condition
        test_condition = AlertCondition(
            symbol=symbol,
            alert_type=AlertType(alert_type.value),
            condition="test",
            threshold=0.0,
            severity=AlertSeverity.INFO,
            notification_methods=[NotificationMethod(notification_method.value)]
        )
        
        # Send test notification
        success = await alert_manager.send_notifications(test_event)
        
        if success:
            return {"message": "Test notification sent successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to send test notification")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending test notification: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/types", response_model=List[str])
async def get_alert_types():
    """
    Get available alert types
    """
    return [alert_type.value for alert_type in AlertType]


@router.get("/severities", response_model=List[str])
async def get_alert_severities():
    """
    Get available alert severities
    """
    return [severity.value for severity in AlertSeverity]


@router.get("/notification-methods", response_model=List[str])
async def get_notification_methods():
    """
    Get available notification methods
    """
    return [method.value for method in NotificationMethod] 