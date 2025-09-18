"""
Portfolio Manager - Enhanced implementation for testing
"""
from decimal import Decimal
from datetime import datetime
from typing import Dict, List, Optional, Any
import uuid


class PortfolioManager:
    def __init__(self, db_manager=None, cache_manager=None):
        self.db_manager = db_manager
        self.cache_manager = cache_manager
        self.portfolios = {}
        self.positions = {}

    async def create_portfolio(self, name: str, description: str = None, 
                             initial_value: Decimal = None, currency: str = "USD",
                             risk_tolerance: str = "moderate") -> Dict[str, Any]:
        """Create a new portfolio"""
        try:
            portfolio_id = str(uuid.uuid4())
            portfolio_data = {
                "id": portfolio_id,
                "name": name,
                "description": description,
                "initial_value": initial_value or Decimal("0"),
                "currency": currency,
                "risk_tolerance": risk_tolerance,
                "created_at": datetime.utcnow()
            }
            
            # If we have a database manager, use it
            if self.db_manager:
                await self.db_manager.execute_query(
                    "INSERT INTO portfolios (...) VALUES (...)",
                    portfolio_data
                )
            else:
                # Store in memory for testing
                self.portfolios[portfolio_id] = portfolio_data
            
            return {
                "success": True,
                "portfolio": portfolio_data
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def get_portfolio(self, portfolio_id: str) -> Optional[Dict[str, Any]]:
        """Get portfolio by ID"""
        if self.db_manager:
            return await self.db_manager.fetch_one(
                "SELECT * FROM portfolios WHERE id = %s", 
                (portfolio_id,)
            )
        else:
            return self.portfolios.get(portfolio_id)

    async def add_position(self, portfolio_id: str, stock_id: int, 
                          quantity: Decimal, price: Decimal) -> Dict[str, Any]:
        """Add position to portfolio"""
        try:
            position_data = {
                "portfolio_id": portfolio_id,
                "stock_id": stock_id,
                "quantity": quantity,
                "average_cost": price,
                "current_price": price,
                "market_value": quantity * price,
                "unrealized_pnl": Decimal("0")
            }
            
            if self.db_manager:
                await self.db_manager.execute_query(
                    "INSERT INTO positions (...) VALUES (...)",
                    position_data
                )
            else:
                position_id = str(uuid.uuid4())
                position_data["id"] = position_id
                self.positions[position_id] = position_data
            
            return {
                "success": True,
                "position": position_data
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def calculate_portfolio_value(self, portfolio_id: str) -> Dict[str, Any]:
        """Calculate total portfolio value"""
        if self.db_manager:
            positions = await self.db_manager.fetch_all(
                "SELECT * FROM positions WHERE portfolio_id = %s",
                (portfolio_id,)
            )
        else:
            positions = [p for p in self.positions.values() 
                        if p.get("portfolio_id") == portfolio_id]
        
        total_value = sum(Decimal(str(p.get("market_value", 0))) for p in positions)
        
        return {
            "total_value": total_value,
            "positions": positions,
            "position_count": len(positions)
        }

    async def calculate_portfolio_metrics(self, portfolio_id: str) -> Dict[str, Any]:
        """Calculate portfolio performance metrics"""
        # Mock implementation for testing
        return {
            "total_return": 0.15,
            "volatility": 0.12,
            "sharpe_ratio": 1.25,
            "max_drawdown": -0.08,
            "beta": 1.1
        }

    async def get_portfolio_positions(self, portfolio_id: str) -> List[Dict[str, Any]]:
        """Get all positions for a portfolio"""
        if self.db_manager:
            return await self.db_manager.fetch_all(
                "SELECT * FROM positions WHERE portfolio_id = %s",
                (portfolio_id,)
            )
        else:
            return [p for p in self.positions.values() 
                   if p.get("portfolio_id") == portfolio_id]

    async def update_position_prices(self, price_updates: Dict[str, Decimal]) -> Dict[str, Any]:
        """Update position prices"""
        updated_count = 0
        
        if self.db_manager:
            for symbol, price in price_updates.items():
                result = await self.db_manager.execute_query(
                    "UPDATE positions SET current_price = %s WHERE symbol = %s",
                    (price, symbol)
                )
                updated_count += getattr(result, 'rowcount', 1)
        else:
            # Update in-memory positions
            for position in self.positions.values():
                symbol = position.get("symbol")
                if symbol in price_updates:
                    position["current_price"] = price_updates[symbol]
                    position["market_value"] = position["quantity"] * price_updates[symbol]
                    updated_count += 1
        
        return {
            "success": True,
            "positions_updated": updated_count
        }

    async def rebalance_portfolio(self, portfolio_id: str, 
                                 target_weights: Dict[str, float]) -> Dict[str, Any]:
        """Rebalance portfolio to target weights"""
        # Mock implementation for testing
        return {
            "success": True,
            "rebalancing_trades": [
                {"symbol": "AAPL", "action": "sell", "quantity": 10},
                {"symbol": "GOOGL", "action": "buy", "quantity": 5}
            ]
        }

    async def calculate_risk_metrics(self, portfolio_id: str) -> Dict[str, Any]:
        """Calculate risk metrics for portfolio"""
        # Mock implementation for testing
        return {
            "var_95": -0.025,  # Value at Risk 95%
            "cvar_95": -0.035,  # Conditional VaR 95%
            "beta": 1.1,
            "correlation_spy": 0.85
        }

    async def get_portfolio_performance(self, portfolio_id: str, 
                                      start_date: datetime = None) -> List[Dict[str, Any]]:
        """Get portfolio performance over time"""
        # Mock implementation for testing
        from datetime import timedelta
        
        performance_data = []
        base_date = start_date or (datetime.utcnow() - timedelta(days=30))
        
        for i in range(30):
            performance_data.append({
                "date": base_date + timedelta(days=i),
                "value": Decimal(f"{100000 + i * 100}"),
                "return": 0.001 * i
            })
        
        return performance_data

    async def generate_portfolio_report(self, portfolio_id: str) -> Dict[str, Any]:
        """Generate comprehensive portfolio report"""
        try:
            portfolio = await self.get_portfolio(portfolio_id)
            positions = await self.get_portfolio_positions(portfolio_id)
            performance = await self.get_portfolio_performance(portfolio_id)
            metrics = await self.calculate_portfolio_metrics(portfolio_id)
            
            return {
                "success": True,
                "portfolio_summary": portfolio,
                "positions": positions,
                "performance": performance,
                "risk_metrics": metrics
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def _validate_portfolio_data(self, data: Dict[str, Any]) -> bool:
        """Validate portfolio data"""
        required_fields = ["name", "initial_value", "currency", "risk_tolerance"]
        
        # Check required fields
        for field in required_fields:
            if field not in data or not data[field]:
                return False
        
        # Validate specific fields
        if data["initial_value"] < 0:
            return False
        
        if data["currency"] not in ["USD", "EUR", "GBP", "JPY"]:
            return False
        
        if data["risk_tolerance"] not in ["conservative", "moderate", "aggressive"]:
            return False
        
        return True

    def _calculate_position_weight(self, position_value: Decimal, 
                                 total_portfolio_value: Decimal) -> float:
        """Calculate position weight in portfolio"""
        if total_portfolio_value == 0:
            return 0.0
        return float(position_value / total_portfolio_value)

    async def _cache_portfolio_data(self, portfolio_id: str, data: Dict[str, Any]):
        """Cache portfolio data"""
        if self.cache_manager:
            cache_key = f"portfolio:{portfolio_id}"
            await self.cache_manager.set(cache_key, data, ttl=300)

    async def _get_cached_portfolio_data(self, portfolio_id: str) -> Optional[Dict[str, Any]]:
        """Get cached portfolio data"""
        if self.cache_manager:
            cache_key = f"portfolio:{portfolio_id}"
            return await self.cache_manager.get(cache_key)
        return None