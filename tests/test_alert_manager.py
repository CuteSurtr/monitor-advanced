"""
Tests for Alert Manager module.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from decimal import Decimal
import uuid

from src.alerts.alert_manager import AlertManager
from src.utils.database import DatabaseManager
from src.utils.cache import CacheManager


class TestAlertManager:
    """Test cases for Alert Manager."""
    
    @pytest.fixture
    def mock_db_manager(self):
        """Mock database manager."""
        db_manager = Mock(spec=DatabaseManager)
        db_manager.execute_query = AsyncMock()
        db_manager.fetch_one = AsyncMock()
        db_manager.fetch_all = AsyncMock()
        return db_manager
    
    @pytest.fixture
    def mock_cache_manager(self):
        """Mock cache manager."""
        cache_manager = Mock(spec=CacheManager)
        cache_manager.get = AsyncMock()
        cache_manager.set = AsyncMock()
        cache_manager.delete = AsyncMock()
        return cache_manager
    
    @pytest.fixture
    def alert_manager(self, mock_db_manager, mock_cache_manager):
        """Alert manager instance with mocked dependencies."""
        manager = AlertManager()
        manager.db_manager = mock_db_manager
        manager.cache_manager = mock_cache_manager
        return manager
    
    @pytest.fixture
    def sample_alert_rule(self):
        """Sample alert rule data for testing."""
        return {
            'id': str(uuid.uuid4()),
            'name': 'Price Drop Alert',
            'description': 'Alert when stock price drops more than 5%',
            'alert_type': 'price_change',
            'conditions': {
                'field': 'price_change_percent',
                'operator': 'less_than',
                'value': -5.0,
                'timeframe': '5m'
            },
            'thresholds': {
                'value': -5.0,
                'timeframe': '5m'
            },
            'notification_channels': ['email', 'dashboard'],
            'is_active': True,
            'created_at': datetime.utcnow()
        }
    
    @pytest.fixture
    def sample_alert_instance(self):
        """Sample alert instance data for testing."""
        return {
            'id': str(uuid.uuid4()),
            'rule_id': str(uuid.uuid4()),
            'stock_id': 1,
            'symbol': 'AAPL',
            'severity': 'HIGH',
            'title': 'AAPL Price Drop Alert',
            'message': 'AAPL has dropped by 6.2% in the last 5 minutes',
            'data': {
                'current_price': 145.50,
                'previous_price': 154.80,
                'change_percent': -6.2
            },
            'status': 'ACTIVE',
            'triggered_at': datetime.utcnow()
        }
    
    def test_alert_manager_initialization(self, alert_manager):
        """Test alert manager initialization."""
        assert alert_manager is not None
        assert hasattr(alert_manager, 'db_manager')
        assert hasattr(alert_manager, 'cache_manager')
    
    @pytest.mark.asyncio
    async def test_create_alert_rule(self, alert_manager, sample_alert_rule):
        """Test creating an alert rule."""
        # Mock database response
        alert_manager.db_manager.execute_query.return_value = Mock(
            fetchone=Mock(return_value=sample_alert_rule)
        )
        
        result = await alert_manager.create_alert_rule(
            name=sample_alert_rule['name'],
            alert_type=sample_alert_rule['alert_type'],
            conditions=sample_alert_rule['conditions'],
            thresholds=sample_alert_rule['thresholds'],
            notification_channels=sample_alert_rule['notification_channels']
        )
        
        assert result['success'] is True
        assert result['alert_rule']['name'] == sample_alert_rule['name']
        alert_manager.db_manager.execute_query.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_alert_rule(self, alert_manager, sample_alert_rule):
        """Test getting alert rule by ID."""
        # Mock database response
        alert_manager.db_manager.fetch_one.return_value = sample_alert_rule
        
        result = await alert_manager.get_alert_rule(sample_alert_rule['id'])
        
        assert result is not None
        assert result['id'] == sample_alert_rule['id']
        assert result['name'] == sample_alert_rule['name']
    
    @pytest.mark.asyncio
    async def test_process_price_change_alert(self, alert_manager, sample_alert_rule):
        """Test processing price change alerts."""
        # Mock stock price data
        price_data = {
            'symbol': 'AAPL',
            'current_price': 145.50,
            'previous_price': 154.80,
            'change_percent': -6.2,
            'timestamp': datetime.utcnow()
        }
        
        # Mock alert rule
        alert_manager.db_manager.fetch_all.return_value = [sample_alert_rule]
        alert_manager.db_manager.execute_query.return_value = Mock(rowcount=1)
        
        result = await alert_manager.process_price_change_alerts([price_data])
        
        assert result['success'] is True
        assert result['alerts_triggered'] >= 0
    
    @pytest.mark.asyncio
    async def test_process_volume_spike_alert(self, alert_manager):
        """Test processing volume spike alerts."""
        # Mock volume data
        volume_data = {
            'symbol': 'TSLA',
            'current_volume': 50000000,
            'average_volume': 20000000,
            'volume_spike_percent': 150.0,
            'timestamp': datetime.utcnow()
        }
        
        # Mock alert rule for volume spikes
        volume_alert_rule = {
            'id': str(uuid.uuid4()),
            'name': 'Volume Spike Alert',
            'alert_type': 'volume_spike',
            'conditions': {
                'field': 'volume_spike_percent',
                'operator': 'greater_than',
                'value': 100.0
            },
            'thresholds': {'value': 100.0},
            'notification_channels': ['dashboard'],
            'is_active': True
        }
        
        alert_manager.db_manager.fetch_all.return_value = [volume_alert_rule]
        alert_manager.db_manager.execute_query.return_value = Mock(rowcount=1)
        
        result = await alert_manager.process_volume_spike_alerts([volume_data])
        
        assert result['success'] is True
        assert result['alerts_triggered'] >= 0
    
    @pytest.mark.asyncio
    async def test_trigger_alert(self, alert_manager, sample_alert_rule, sample_alert_instance):
        """Test triggering an alert."""
        # Mock database response
        alert_manager.db_manager.execute_query.return_value = Mock(
            fetchone=Mock(return_value=sample_alert_instance)
        )
        
        result = await alert_manager.trigger_alert(
            rule_id=sample_alert_rule['id'],
            stock_id=1,
            severity='HIGH',
            title=sample_alert_instance['title'],
            message=sample_alert_instance['message'],
            data=sample_alert_instance['data']
        )
        
        assert result['success'] is True
        assert result['alert']['title'] == sample_alert_instance['title']
    
    @pytest.mark.asyncio
    async def test_resolve_alert(self, alert_manager, sample_alert_instance):
        """Test resolving an alert."""
        # Mock database response
        alert_manager.db_manager.execute_query.return_value = Mock(rowcount=1)
        
        result = await alert_manager.resolve_alert(
            alert_id=sample_alert_instance['id'],
            resolution_notes="Price has recovered"
        )
        
        assert result['success'] is True
        alert_manager.db_manager.execute_query.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_acknowledge_alert(self, alert_manager, sample_alert_instance):
        """Test acknowledging an alert."""
        # Mock database response
        alert_manager.db_manager.execute_query.return_value = Mock(rowcount=1)
        
        result = await alert_manager.acknowledge_alert(
            alert_id=sample_alert_instance['id'],
            acknowledged_by="test_user"
        )
        
        assert result['success'] is True
        alert_manager.db_manager.execute_query.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_active_alerts(self, alert_manager, sample_alert_instance):
        """Test getting active alerts."""
        # Mock database response
        alert_manager.db_manager.fetch_all.return_value = [sample_alert_instance]
        
        result = await alert_manager.get_active_alerts()
        
        assert len(result) == 1
        assert result[0]['id'] == sample_alert_instance['id']
        assert result[0]['status'] == 'ACTIVE'
    
    @pytest.mark.asyncio
    async def test_get_alerts_by_symbol(self, alert_manager, sample_alert_instance):
        """Test getting alerts for specific symbol."""
        # Mock database response
        alert_manager.db_manager.fetch_all.return_value = [sample_alert_instance]
        
        result = await alert_manager.get_alerts_by_symbol('AAPL')
        
        assert len(result) == 1
        assert result[0]['symbol'] == 'AAPL'
    
    @pytest.mark.asyncio
    async def test_get_alert_statistics(self, alert_manager):
        """Test getting alert statistics."""
        # Mock database response
        stats_data = [
            {'alert_type': 'price_change', 'count': 10, 'severity': 'HIGH'},
            {'alert_type': 'volume_spike', 'count': 5, 'severity': 'MEDIUM'},
            {'alert_type': 'technical_indicator', 'count': 3, 'severity': 'LOW'}
        ]
        
        alert_manager.db_manager.fetch_all.return_value = stats_data
        
        result = await alert_manager.get_alert_statistics(
            start_date=datetime.utcnow() - timedelta(days=7)
        )
        
        assert len(result) == 3
        assert all('alert_type' in item for item in result)
        assert all('count' in item for item in result)
    
    @pytest.mark.asyncio
    async def test_send_notification(self, alert_manager, sample_alert_instance):
        """Test sending alert notifications."""
        with patch.object(alert_manager, '_send_email_notification', return_value=True) as mock_email:
            with patch.object(alert_manager, '_send_dashboard_notification', return_value=True) as mock_dashboard:
                
                result = await alert_manager.send_notification(
                    alert_instance=sample_alert_instance,
                    channels=['email', 'dashboard']
                )
                
                assert result['success'] is True
                mock_email.assert_called_once()
                mock_dashboard.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_evaluate_alert_condition(self, alert_manager):
        """Test evaluating alert conditions."""
        # Test price change condition
        condition = {
            'field': 'price_change_percent',
            'operator': 'less_than',
            'value': -5.0
        }
        
        data = {'price_change_percent': -6.2}
        
        result = alert_manager._evaluate_condition(condition, data)
        assert result is True
        
        # Test opposite condition
        data = {'price_change_percent': -3.0}
        result = alert_manager._evaluate_condition(condition, data)
        assert result is False
    
    @pytest.mark.asyncio
    async def test_alert_rate_limiting(self, alert_manager, sample_alert_rule):
        """Test alert rate limiting to prevent spam."""
        # Mock recent alert
        recent_alert = {
            'rule_id': sample_alert_rule['id'],
            'stock_id': 1,
            'triggered_at': datetime.utcnow() - timedelta(minutes=2)
        }
        
        alert_manager.db_manager.fetch_one.return_value = recent_alert
        
        # Try to trigger same alert again
        result = await alert_manager.trigger_alert(
            rule_id=sample_alert_rule['id'],
            stock_id=1,
            severity='HIGH',
            title='Test Alert',
            message='Test message',
            data={}
        )
        
        # Should be rate limited
        assert result['success'] is False
        assert 'rate_limited' in result['error']
    
    @pytest.mark.asyncio
    async def test_cleanup_old_alerts(self, alert_manager):
        """Test cleaning up old resolved alerts."""
        # Mock database response
        alert_manager.db_manager.execute_query.return_value = Mock(rowcount=15)
        
        result = await alert_manager.cleanup_old_alerts(days_to_keep=30)
        
        assert result['success'] is True
        assert result['alerts_cleaned'] == 15
    
    @pytest.mark.asyncio
    async def test_update_alert_rule(self, alert_manager, sample_alert_rule):
        """Test updating an alert rule."""
        # Mock database response
        updated_rule = sample_alert_rule.copy()
        updated_rule['name'] = 'Updated Alert Rule'
        alert_manager.db_manager.execute_query.return_value = Mock(
            fetchone=Mock(return_value=updated_rule)
        )
        
        result = await alert_manager.update_alert_rule(
            rule_id=sample_alert_rule['id'],
            name='Updated Alert Rule',
            conditions={'field': 'price_change_percent', 'operator': 'less_than', 'value': -10.0}
        )
        
        assert result['success'] is True
        assert result['alert_rule']['name'] == 'Updated Alert Rule'
    
    @pytest.mark.asyncio
    async def test_delete_alert_rule(self, alert_manager, sample_alert_rule):
        """Test deleting an alert rule."""
        # Mock database response
        alert_manager.db_manager.execute_query.return_value = Mock(rowcount=1)
        
        result = await alert_manager.delete_alert_rule(sample_alert_rule['id'])
        
        assert result['success'] is True
        alert_manager.db_manager.execute_query.assert_called_once()
    
    def test_validate_alert_conditions(self, alert_manager):
        """Test alert condition validation."""
        # Valid conditions
        valid_conditions = {
            'field': 'price_change_percent',
            'operator': 'less_than',
            'value': -5.0
        }
        
        assert alert_manager._validate_conditions(valid_conditions) is True
        
        # Invalid conditions
        invalid_conditions = {
            'field': 'invalid_field',
            'operator': 'invalid_operator',
            'value': 'not_a_number'
        }
        
        assert alert_manager._validate_conditions(invalid_conditions) is False
    
    @pytest.mark.asyncio
    async def test_bulk_alert_processing(self, alert_manager):
        """Test processing multiple alerts in bulk."""
        # Mock market data
        market_data = [
            {'symbol': 'AAPL', 'price_change_percent': -6.2},
            {'symbol': 'GOOGL', 'price_change_percent': -3.1},
            {'symbol': 'TSLA', 'volume_spike_percent': 250.0}
        ]
        
        # Mock alert rules
        alert_rules = [
            {
                'id': str(uuid.uuid4()),
                'alert_type': 'price_change',
                'conditions': {'field': 'price_change_percent', 'operator': 'less_than', 'value': -5.0},
                'is_active': True
            }
        ]
        
        alert_manager.db_manager.fetch_all.return_value = alert_rules
        alert_manager.db_manager.execute_query.return_value = Mock(rowcount=1)
        
        result = await alert_manager.process_bulk_alerts(market_data)
        
        assert result['success'] is True
        assert result['data_points_processed'] == 3
    
    @pytest.mark.asyncio
    async def test_alert_escalation(self, alert_manager, sample_alert_instance):
        """Test alert escalation for unacknowledged alerts."""
        # Mock unacknowledged alert
        old_alert = sample_alert_instance.copy()
        old_alert['triggered_at'] = datetime.utcnow() - timedelta(hours=2)
        old_alert['acknowledged_at'] = None
        
        alert_manager.db_manager.fetch_all.return_value = [old_alert]
        alert_manager.db_manager.execute_query.return_value = Mock(rowcount=1)
        
        result = await alert_manager.escalate_unacknowledged_alerts(
            escalation_threshold_hours=1
        )
        
        assert result['success'] is True
        assert result['alerts_escalated'] >= 0
    
    @pytest.mark.asyncio
    async def test_error_handling(self, alert_manager):
        """Test error handling in alert operations."""
        # Mock database error
        alert_manager.db_manager.execute_query.side_effect = Exception("Database error")
        
        result = await alert_manager.create_alert_rule(
            name="Test Alert",
            alert_type="price_change",
            conditions={'field': 'price', 'operator': 'less_than', 'value': 100},
            thresholds={'value': 100}
        )
        
        assert result['success'] is False
        assert 'error' in result