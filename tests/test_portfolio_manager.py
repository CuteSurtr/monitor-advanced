"""
Tests for Portfolio Manager module.
"""

import pytest
import asyncio
from decimal import Decimal
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
import uuid

from src.portfolio.portfolio_manager import PortfolioManager
from src.utils.database import DatabaseManager
from src.utils.cache import CacheManager


class TestPortfolioManager:
    """Test cases for Portfolio Manager."""

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
    def portfolio_manager(self, mock_db_manager, mock_cache_manager):
        """Portfolio manager instance with mocked dependencies."""
        manager = PortfolioManager()
        manager.db_manager = mock_db_manager
        manager.cache_manager = mock_cache_manager
        return manager

    @pytest.fixture
    def sample_portfolio_data(self):
        """Sample portfolio data for testing."""
        return {
            "id": str(uuid.uuid4()),
            "name": "Test Portfolio",
            "description": "Test portfolio for unit tests",
            "currency": "USD",
            "initial_value": Decimal("100000.00"),
            "risk_tolerance": "moderate",
        }

    @pytest.fixture
    def sample_position_data(self):
        """Sample position data for testing."""
        return {
            "portfolio_id": str(uuid.uuid4()),
            "stock_id": 1,
            "symbol": "AAPL",
            "quantity": Decimal("100.00"),
            "average_cost": Decimal("150.00"),
            "current_price": Decimal("155.00"),
            "market_value": Decimal("15500.00"),
            "unrealized_pnl": Decimal("500.00"),
        }

    def test_portfolio_manager_initialization(self, portfolio_manager):
        """Test portfolio manager initialization."""
        assert portfolio_manager is not None
        assert hasattr(portfolio_manager, "db_manager")
        assert hasattr(portfolio_manager, "cache_manager")

    @pytest.mark.asyncio
    async def test_create_portfolio(self, portfolio_manager, sample_portfolio_data):
        """Test portfolio creation."""
        # Mock database response
        portfolio_manager.db_manager.execute_query.return_value = Mock(
            fetchone=Mock(return_value=sample_portfolio_data)
        )

        result = await portfolio_manager.create_portfolio(
            name=sample_portfolio_data["name"],
            description=sample_portfolio_data["description"],
            initial_value=sample_portfolio_data["initial_value"],
            currency=sample_portfolio_data["currency"],
            risk_tolerance=sample_portfolio_data["risk_tolerance"],
        )

        assert result["success"] is True
        assert result["portfolio"]["name"] == sample_portfolio_data["name"]
        portfolio_manager.db_manager.execute_query.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_portfolio(self, portfolio_manager, sample_portfolio_data):
        """Test getting portfolio by ID."""
        # Mock database response
        portfolio_manager.db_manager.fetch_one.return_value = sample_portfolio_data

        result = await portfolio_manager.get_portfolio(sample_portfolio_data["id"])

        assert result is not None
        assert result["id"] == sample_portfolio_data["id"]
        assert result["name"] == sample_portfolio_data["name"]

    @pytest.mark.asyncio
    async def test_get_portfolio_not_found(self, portfolio_manager):
        """Test getting non-existent portfolio."""
        # Mock database response
        portfolio_manager.db_manager.fetch_one.return_value = None

        result = await portfolio_manager.get_portfolio("non-existent-id")

        assert result is None

    @pytest.mark.asyncio
    async def test_add_position(self, portfolio_manager, sample_position_data):
        """Test adding position to portfolio."""
        # Mock database response
        portfolio_manager.db_manager.execute_query.return_value = Mock(
            fetchone=Mock(return_value=sample_position_data)
        )

        result = await portfolio_manager.add_position(
            portfolio_id=sample_position_data["portfolio_id"],
            stock_id=sample_position_data["stock_id"],
            quantity=sample_position_data["quantity"],
            price=sample_position_data["average_cost"],
        )

        assert result["success"] is True
        assert result["position"]["quantity"] == sample_position_data["quantity"]
        portfolio_manager.db_manager.execute_query.assert_called_once()

    @pytest.mark.asyncio
    async def test_calculate_portfolio_value(
        self, portfolio_manager, sample_portfolio_data
    ):
        """Test portfolio value calculation."""
        # Mock positions data
        positions = [
            {
                "stock_id": 1,
                "symbol": "AAPL",
                "quantity": Decimal("100"),
                "current_price": Decimal("155.00"),
                "market_value": Decimal("15500.00"),
            },
            {
                "stock_id": 2,
                "symbol": "GOOGL",
                "quantity": Decimal("50"),
                "current_price": Decimal("2800.00"),
                "market_value": Decimal("140000.00"),
            },
        ]

        portfolio_manager.db_manager.fetch_all.return_value = positions

        result = await portfolio_manager.calculate_portfolio_value(
            sample_portfolio_data["id"]
        )

        expected_value = Decimal("155500.00")  # 15500 + 140000
        assert result["total_value"] == expected_value
        assert len(result["positions"]) == 2

    @pytest.mark.asyncio
    async def test_calculate_portfolio_metrics(
        self, portfolio_manager, sample_portfolio_data
    ):
        """Test portfolio metrics calculation."""
        # Mock historical data
        historical_values = [
            {
                "date": datetime.utcnow() - timedelta(days=i),
                "value": Decimal(f"{100000 + i * 100}"),
            }
            for i in range(30)
        ]

        portfolio_manager.db_manager.fetch_all.return_value = historical_values

        result = await portfolio_manager.calculate_portfolio_metrics(
            sample_portfolio_data["id"]
        )

        assert "total_return" in result
        assert "volatility" in result
        assert "sharpe_ratio" in result
        assert "max_drawdown" in result

    @pytest.mark.asyncio
    async def test_get_portfolio_positions(
        self, portfolio_manager, sample_portfolio_data
    ):
        """Test getting portfolio positions."""
        # Mock positions data
        positions = [
            {
                "id": str(uuid.uuid4()),
                "stock_id": 1,
                "symbol": "AAPL",
                "quantity": Decimal("100"),
                "average_cost": Decimal("150.00"),
                "current_price": Decimal("155.00"),
                "market_value": Decimal("15500.00"),
                "unrealized_pnl": Decimal("500.00"),
            }
        ]

        portfolio_manager.db_manager.fetch_all.return_value = positions

        result = await portfolio_manager.get_portfolio_positions(
            sample_portfolio_data["id"]
        )

        assert len(result) == 1
        assert result[0]["symbol"] == "AAPL"
        assert result[0]["quantity"] == Decimal("100")

    @pytest.mark.asyncio
    async def test_update_position_prices(self, portfolio_manager):
        """Test updating position prices."""
        # Mock price data
        price_updates = {"AAPL": Decimal("160.00"), "GOOGL": Decimal("2850.00")}

        portfolio_manager.db_manager.execute_query.return_value = Mock(rowcount=2)

        result = await portfolio_manager.update_position_prices(price_updates)

        assert result["success"] is True
        assert result["positions_updated"] == 2

    @pytest.mark.asyncio
    async def test_rebalance_portfolio(self, portfolio_manager, sample_portfolio_data):
        """Test portfolio rebalancing."""
        # Mock current positions
        current_positions = [
            {"symbol": "AAPL", "weight": 0.6, "target_weight": 0.5},
            {"symbol": "GOOGL", "weight": 0.4, "target_weight": 0.5},
        ]

        portfolio_manager.db_manager.fetch_all.return_value = current_positions

        result = await portfolio_manager.rebalance_portfolio(
            sample_portfolio_data["id"], target_weights={"AAPL": 0.5, "GOOGL": 0.5}
        )

        assert result["success"] is True
        assert "rebalancing_trades" in result

    @pytest.mark.asyncio
    async def test_calculate_risk_metrics(
        self, portfolio_manager, sample_portfolio_data
    ):
        """Test risk metrics calculation."""
        # Mock historical data
        returns_data = [
            {
                "date": datetime.utcnow() - timedelta(days=i),
                "return": 0.01 + (i % 5) * 0.002,
            }
            for i in range(252)  # 1 year of data
        ]

        portfolio_manager.db_manager.fetch_all.return_value = returns_data

        result = await portfolio_manager.calculate_risk_metrics(
            sample_portfolio_data["id"]
        )

        assert "var_95" in result  # Value at Risk
        assert "cvar_95" in result  # Conditional VaR
        assert "beta" in result
        assert "correlation_spy" in result

    @pytest.mark.asyncio
    async def test_get_portfolio_performance(
        self, portfolio_manager, sample_portfolio_data
    ):
        """Test getting portfolio performance over time."""
        # Mock performance data
        performance_data = [
            {
                "date": datetime.utcnow() - timedelta(days=i),
                "value": Decimal(f"{100000 + i * 100}"),
                "return": 0.001 * i,
            }
            for i in range(30)
        ]

        portfolio_manager.db_manager.fetch_all.return_value = performance_data

        result = await portfolio_manager.get_portfolio_performance(
            sample_portfolio_data["id"],
            start_date=datetime.utcnow() - timedelta(days=30),
        )

        assert len(result) == 30
        assert all("date" in item for item in result)
        assert all("value" in item for item in result)

    @pytest.mark.asyncio
    async def test_generate_portfolio_report(
        self, portfolio_manager, sample_portfolio_data
    ):
        """Test generating comprehensive portfolio report."""
        # Mock various data sources
        portfolio_manager.db_manager.fetch_one.return_value = sample_portfolio_data
        portfolio_manager.db_manager.fetch_all.side_effect = [
            [{"symbol": "AAPL", "quantity": 100, "value": 15500}],  # positions
            [{"date": datetime.utcnow(), "value": 155500}],  # performance
            [{"metric": "sharpe_ratio", "value": 1.5}],  # metrics
        ]

        result = await portfolio_manager.generate_portfolio_report(
            sample_portfolio_data["id"]
        )

        assert result["success"] is True
        assert "portfolio_summary" in result
        assert "positions" in result
        assert "performance" in result
        assert "risk_metrics" in result

    def test_validate_portfolio_data(self, portfolio_manager):
        """Test portfolio data validation."""
        # Valid data
        valid_data = {
            "name": "Test Portfolio",
            "initial_value": Decimal("100000"),
            "currency": "USD",
            "risk_tolerance": "moderate",
        }

        assert portfolio_manager._validate_portfolio_data(valid_data) is True

        # Invalid data
        invalid_data = {
            "name": "",  # Empty name
            "initial_value": Decimal("-1000"),  # Negative value
            "currency": "INVALID",  # Invalid currency
            "risk_tolerance": "unknown",  # Invalid risk tolerance
        }

        assert portfolio_manager._validate_portfolio_data(invalid_data) is False

    def test_calculate_position_weight(self, portfolio_manager):
        """Test position weight calculation."""
        position_value = Decimal("15500")
        total_portfolio_value = Decimal("155000")

        weight = portfolio_manager._calculate_position_weight(
            position_value, total_portfolio_value
        )

        expected_weight = float(position_value / total_portfolio_value)
        assert abs(weight - expected_weight) < 0.0001

    @pytest.mark.asyncio
    async def test_cache_portfolio_data(self, portfolio_manager, sample_portfolio_data):
        """Test caching portfolio data."""
        cache_key = f"portfolio:{sample_portfolio_data['id']}"

        await portfolio_manager._cache_portfolio_data(
            sample_portfolio_data["id"], sample_portfolio_data
        )

        portfolio_manager.cache_manager.set.assert_called_once_with(
            cache_key, sample_portfolio_data, ttl=300
        )

    @pytest.mark.asyncio
    async def test_get_cached_portfolio_data(
        self, portfolio_manager, sample_portfolio_data
    ):
        """Test retrieving cached portfolio data."""
        cache_key = f"portfolio:{sample_portfolio_data['id']}"
        portfolio_manager.cache_manager.get.return_value = sample_portfolio_data

        result = await portfolio_manager._get_cached_portfolio_data(
            sample_portfolio_data["id"]
        )

        assert result == sample_portfolio_data
        portfolio_manager.cache_manager.get.assert_called_once_with(cache_key)

    @pytest.mark.asyncio
    async def test_error_handling(self, portfolio_manager):
        """Test error handling in portfolio operations."""
        # Mock database error
        portfolio_manager.db_manager.execute_query.side_effect = Exception(
            "Database error"
        )

        result = await portfolio_manager.create_portfolio(
            name="Test Portfolio", initial_value=Decimal("100000")
        )

        assert result["success"] is False
        assert "error" in result

    @pytest.mark.asyncio
    async def test_concurrent_operations(
        self, portfolio_manager, sample_portfolio_data
    ):
        """Test handling concurrent portfolio operations."""
        portfolio_id = sample_portfolio_data["id"]

        # Mock successful operations
        portfolio_manager.db_manager.execute_query.return_value = Mock(rowcount=1)

        # Create multiple concurrent operations
        tasks = [
            portfolio_manager.update_position_prices({"AAPL": Decimal("160.00")}),
            portfolio_manager.calculate_portfolio_value(portfolio_id),
            portfolio_manager.get_portfolio_positions(portfolio_id),
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Check that no exceptions were raised
        assert all(not isinstance(result, Exception) for result in results)
