#!/usr/bin/env python3
"""
Alert System Example

This script demonstrates how to use the alert system to create
various types of alerts and monitor them.
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent / "src"))

from src.alerts.alert_manager import (
    AlertManager, AlertCondition, AlertType, AlertSeverity, NotificationMethod
)
from src.utils.config import Config
from src.utils.database import DatabaseManager
from src.utils.cache import CacheManager
from src.analytics.analytics_engine import AnalyticsEngine


async def main():
    """Main example function."""
    print("® Alert System Example")
    print("=" * 50)
    
    try:
        # Initialize components
        config = Config()
        db_manager = DatabaseManager(config)
        await db_manager.initialize()
        
        cache_manager = CacheManager(config)
        await cache_manager.initialize()
        
        analytics_engine = AnalyticsEngine(db_manager, cache_manager)
        
        # Create alert manager
        alert_manager = AlertManager(
            db_manager, cache_manager, analytics_engine, config.dict()
        )
        
        print("Alert manager initialized")
        
        # Example 1: Create a price threshold alert
        print("\nà Example 1: Price Threshold Alert")
        price_alert = AlertCondition(
            symbol="AAPL",
            alert_type=AlertType.PRICE_THRESHOLD,
            condition="price > 150",
            threshold=150.0,
            severity=AlertSeverity.WARNING,
            cooldown_minutes=30,
            notification_methods=[NotificationMethod.EMAIL],
            custom_message="AAPL has reached $150!"
        )
        
        condition_id = alert_manager.add_alert_condition(price_alert)
        print(f"Created price alert: {condition_id}")
        
        # Example 2: Create a price change alert
        print("\nä Example 2: Price Change Alert")
        change_alert = AlertCondition(
            symbol="TSLA",
            alert_type=AlertType.PRICE_CHANGE,
            condition="change > 5",
            threshold=5.0,
            severity=AlertSeverity.CRITICAL,
            cooldown_minutes=15,
            notification_methods=[NotificationMethod.EMAIL, NotificationMethod.TELEGRAM],
            custom_message="TSLA has moved more than 5%!"
        )
        
        condition_id2 = alert_manager.add_alert_condition(change_alert)
        print(f"Created change alert: {condition_id2}")
        
        # Example 3: Create a volume spike alert
        print("\nà Example 3: Volume Spike Alert")
        volume_alert = AlertCondition(
            symbol="MSFT",
            alert_type=AlertType.VOLUME_SPIKE,
            condition="volume > 2",
            threshold=2.0,
            severity=AlertSeverity.INFO,
            cooldown_minutes=60,
            notification_methods=[NotificationMethod.EMAIL],
            custom_message="MSFT volume is 2x above average"
        )
        
        condition_id3 = alert_manager.add_alert_condition(volume_alert)
        print(f"Created volume alert: {condition_id3}")
        
        # Example 4: Create a technical indicator alert
        print("\nä Example 4: Technical Indicator Alert")
        rsi_alert = AlertCondition(
            symbol="GOOGL",
            alert_type=AlertType.TECHNICAL_INDICATOR,
            condition="rsi < 30",
            threshold=30.0,
            severity=AlertSeverity.WARNING,
            cooldown_minutes=120,
            notification_methods=[NotificationMethod.EMAIL],
            custom_message="GOOGL RSI indicates oversold condition"
        )
        
        condition_id4 = alert_manager.add_alert_condition(rsi_alert)
        print(f"Created RSI alert: {condition_id4}")
        
        # Example 5: Create an anomaly detection alert
        print("\nç Example 5: Anomaly Detection Alert")
        anomaly_alert = AlertCondition(
            symbol="AMZN",
            alert_type=AlertType.ANOMALY_DETECTED,
            condition="anomaly_detected",
            threshold=0.0,
            severity=AlertSeverity.CRITICAL,
            cooldown_minutes=30,
            notification_methods=[NotificationMethod.EMAIL, NotificationMethod.SLACK],
            custom_message="Anomaly detected in AMZN trading pattern"
        )
        
        condition_id5 = alert_manager.add_alert_condition(anomaly_alert)
        print(f"Created anomaly alert: {condition_id5}")
        
        # List all alert conditions
        print("\nã Current Alert Conditions:")
        conditions = alert_manager.get_alert_conditions()
        for i, condition in enumerate(conditions, 1):
            print(f"  {i}. {condition.symbol} - {condition.alert_type.value} - {condition.condition}")
        
        # Get alert statistics
        print("\nä Alert Statistics:")
        stats = alert_manager.get_alert_statistics()
        print(f"  Total Conditions: {stats['total_conditions']}")
        print(f"  Enabled Conditions: {stats['enabled_conditions']}")
        print(f"  Total Events: {stats['total_events']}")
        print(f"  Monitoring Active: {stats['monitoring_active']}")
        
        # Example 6: Update an alert condition
        print("\nExample 6: Update Alert Condition")
        updates = {
            'threshold': 160.0,
            'severity': AlertSeverity.CRITICAL,
            'custom_message': 'AAPL has reached $160!'
        }
        
        success = alert_manager.update_alert_condition(condition_id, updates)
        if success:
            print("Updated price alert threshold to $160")
        else:
            print("Failed to update alert condition")
        
        # Example 7: Disable an alert condition
        print("\nExample 7: Disable Alert Condition")
        disable_updates = {'enabled': False}
        success = alert_manager.update_alert_condition(condition_id2, disable_updates)
        if success:
            print("Disabled TSLA change alert")
        else:
            print("Failed to disable alert condition")
        
        # Example 8: Remove an alert condition
        print("\nëExample 8: Remove Alert Condition")
        success = alert_manager.remove_alert_condition(condition_id5)
        if success:
            print("Removed AMZN anomaly alert")
        else:
            print("Failed to remove alert condition")
        
        # Final statistics
        print("\nä Final Alert Statistics:")
        stats = alert_manager.get_alert_statistics()
        print(f"  Total Conditions: {stats['total_conditions']}")
        print(f"  Enabled Conditions: {stats['enabled_conditions']}")
        print(f"  Total Events: {stats['total_events']}")
        
        # Example 9: Start monitoring (in real scenario)
        print("\nÄ Example 9: Start Alert Monitoring")
        print("Note: In a real scenario, this would start monitoring market data")
        print("and trigger alerts when conditions are met.")
        
        # await alert_manager.start_monitoring()
        # print("Alert monitoring started")
        
        # Wait a bit to simulate monitoring
        # await asyncio.sleep(5)
        
        # await alert_manager.stop_monitoring()
        # print("Alert monitoring stopped")
        
        print("\nAlert system example completed successfully!")
        
    except Exception as e:
        print(f"Error in alert example: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        if 'db_manager' in locals():
            await db_manager.close()
        if 'cache_manager' in locals():
            await cache_manager.close()


if __name__ == "__main__":
    asyncio.run(main()) 