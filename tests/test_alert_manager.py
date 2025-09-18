"""
Tests for Alert Manager module.
"""

import pytest
from src.alerts.alert_manager import AlertManager


class TestAlertManager:
    """Test cases for Alert Manager."""

    @pytest.fixture
    def alert_manager(self):
        """Alert manager instance."""
        return AlertManager()

    def test_alert_manager_initialization(self, alert_manager):
        """Test alert manager initialization."""
        assert alert_manager is not None

    def test_get_alerts(self, alert_manager):
        """Test getting alerts."""
        result = alert_manager.get_alerts()
        assert result is not None
        assert "alerts" in result
        assert "count" in result

    @pytest.mark.asyncio
    async def test_start_monitoring(self, alert_manager):
        """Test start monitoring method."""
        # Should not raise an exception
        await alert_manager.start_monitoring()
        assert True