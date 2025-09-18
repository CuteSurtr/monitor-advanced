"""
Real-time P&L Calculation Engine with advanced metrics and performance tracking.
"""

import asyncio
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP

from src.utils.logger import get_logger
from src.utils.database import DatabaseManager
from src.utils.cache import CacheManager


@dataclass
class Position:
    """Position data structure."""

    symbol: str
    quantity: Decimal
    average_cost: Decimal
    current_price: Decimal = Decimal("0")
    market_value: Decimal = Decimal("0")
    unrealized_pnl: Decimal = Decimal("0")
    realized_pnl: Decimal = Decimal("0")
    day_pnl: Decimal = Decimal("0")
    total_pnl: Decimal = Decimal("0")
    cost_basis: Decimal = field(init=False)
    asset_type: str = "stock"  # stock, forex, crypto, commodity
    currency: str = "USD"

    def __post_init__(self):
        self.cost_basis = self.quantity * self.average_cost


@dataclass
class PnLSnapshot:
    """P&L snapshot for a specific timestamp."""

    timestamp: datetime
    portfolio_id: int
    total_market_value: Decimal
    total_cost_basis: Decimal
    total_unrealized_pnl: Decimal
    total_realized_pnl: Decimal
    total_day_pnl: Decimal
    total_pnl: Decimal
    positions: List[Position]
    currency: str = "USD"


class PnLEngine:
    """Real-time P&L calculation engine with multi-asset support."""

    def __init__(
        self, db_manager: DatabaseManager, cache_manager: CacheManager, config=None
    ):
        self.db_manager = db_manager
        self.cache_manager = cache_manager
        self.config = config
        self.logger = get_logger(__name__)
        self.running = False

        # P&L calculation settings
        self.calculation_interval = 30  # seconds
        self.price_precision = 4
        self.pnl_precision = 2

        # Current positions cache
        self.positions_cache = {}

        # Historical P&L cache for performance
        self.pnl_history = {}

    async def start(self):
        """Start the P&L calculation engine."""
        self.running = True
        self.logger.info("Starting P&L calculation engine")

        try:
            while self.running:
                await self._calculate_all_portfolios_pnl()
                await asyncio.sleep(self.calculation_interval)

        except asyncio.CancelledError:
            self.logger.info("P&L engine cancelled")
        except Exception as e:
            self.logger.error(f"Error in P&L engine: {e}")
        finally:
            self.running = False

    async def stop(self):
        """Stop the P&L calculation engine."""
        self.running = False
        self.logger.info("Stopping P&L calculation engine")

    async def calculate_portfolio_pnl(
        self, portfolio_id: int, calculate_historical: bool = False
    ) -> PnLSnapshot:
        """
        Calculate real-time P&L for a portfolio.

        Args:
            portfolio_id: Portfolio identifier
            calculate_historical: Whether to include historical P&L trends

        Returns:
            PnLSnapshot with current P&L metrics
        """
        try:
            # Get current positions
            positions = await self._get_portfolio_positions(portfolio_id)
            if not positions:
                return self._create_empty_snapshot(portfolio_id)

            # Get current market prices
            await self._update_position_prices(positions)

            # Calculate P&L for each position
            pnl_positions = []
            for pos_data in positions:
                position = await self._calculate_position_pnl(pos_data)
                pnl_positions.append(position)

            # Aggregate portfolio P&L
            snapshot = self._aggregate_portfolio_pnl(portfolio_id, pnl_positions)

            # Cache the snapshot
            await self._cache_pnl_snapshot(snapshot)

            # Store historical data
            if calculate_historical:
                await self._store_pnl_history(snapshot)

            return snapshot

        except Exception as e:
            self.logger.error(
                f"Error calculating P&L for portfolio {portfolio_id}: {e}"
            )
            return self._create_empty_snapshot(portfolio_id)

    async def calculate_realtime_pnl_stream(self, portfolio_id: int) -> Dict[str, Any]:
        """
        Calculate real-time P&L stream for live updates.

        Args:
            portfolio_id: Portfolio identifier

        Returns:
            Real-time P&L data for streaming
        """
        try:
            snapshot = await self.calculate_portfolio_pnl(portfolio_id)

            # Calculate additional real-time metrics
            prev_snapshot = await self._get_previous_snapshot(portfolio_id)

            pnl_change = Decimal("0")
            pnl_change_pct = Decimal("0")

            if prev_snapshot:
                pnl_change = snapshot.total_pnl - prev_snapshot.total_pnl
                if prev_snapshot.total_pnl != 0:
                    pnl_change_pct = (pnl_change / abs(prev_snapshot.total_pnl)) * 100

            return {
                "portfolio_id": portfolio_id,
                "timestamp": snapshot.timestamp.isoformat(),
                "total_market_value": float(snapshot.total_market_value),
                "total_cost_basis": float(snapshot.total_cost_basis),
                "total_unrealized_pnl": float(snapshot.total_unrealized_pnl),
                "total_realized_pnl": float(snapshot.total_realized_pnl),
                "total_day_pnl": float(snapshot.total_day_pnl),
                "total_pnl": float(snapshot.total_pnl),
                "pnl_change": float(pnl_change),
                "pnl_change_pct": float(pnl_change_pct),
                "currency": snapshot.currency,
                "positions_count": len(snapshot.positions),
                "top_gainers": self._get_top_performers(snapshot.positions, "gainers"),
                "top_losers": self._get_top_performers(snapshot.positions, "losers"),
            }

        except Exception as e:
            self.logger.error(f"Error calculating real-time P&L stream: {e}")
            return {}

    async def calculate_position_pnl_detailed(
        self, portfolio_id: int, symbol: str
    ) -> Dict[str, Any]:
        """
        Calculate detailed P&L for a specific position.

        Args:
            portfolio_id: Portfolio identifier
            symbol: Asset symbol

        Returns:
            Detailed position P&L metrics
        """
        try:
            positions = await self._get_portfolio_positions(portfolio_id)
            position_data = next((p for p in positions if p["symbol"] == symbol), None)

            if not position_data:
                return {
                    "error": f"Position {symbol} not found in portfolio {portfolio_id}"
                }

            # Update current price
            await self._update_position_prices([position_data])

            # Calculate detailed P&L
            position = await self._calculate_position_pnl(position_data)

            # Get historical performance
            historical_pnl = await self._get_position_historical_pnl(
                portfolio_id, symbol
            )

            return {
                "symbol": position.symbol,
                "quantity": float(position.quantity),
                "average_cost": float(position.average_cost),
                "current_price": float(position.current_price),
                "market_value": float(position.market_value),
                "cost_basis": float(position.cost_basis),
                "unrealized_pnl": float(position.unrealized_pnl),
                "unrealized_pnl_pct": float(
                    (position.unrealized_pnl / position.cost_basis * 100)
                    if position.cost_basis != 0
                    else 0
                ),
                "realized_pnl": float(position.realized_pnl),
                "day_pnl": float(position.day_pnl),
                "total_pnl": float(position.total_pnl),
                "asset_type": position.asset_type,
                "currency": position.currency,
                "historical_pnl": historical_pnl,
            }

        except Exception as e:
            self.logger.error(f"Error calculating position P&L for {symbol}: {e}")
            return {"error": str(e)}

    async def calculate_sector_pnl(self, portfolio_id: int) -> Dict[str, Any]:
        """
        Calculate P&L breakdown by sector/asset type.

        Args:
            portfolio_id: Portfolio identifier

        Returns:
            Sector-wise P&L breakdown
        """
        try:
            snapshot = await self.calculate_portfolio_pnl(portfolio_id)

            # Group by asset type/sector
            sector_pnl = {}

            for position in snapshot.positions:
                sector = position.asset_type

                if sector not in sector_pnl:
                    sector_pnl[sector] = {
                        "market_value": Decimal("0"),
                        "cost_basis": Decimal("0"),
                        "unrealized_pnl": Decimal("0"),
                        "realized_pnl": Decimal("0"),
                        "total_pnl": Decimal("0"),
                        "positions_count": 0,
                        "symbols": [],
                    }

                sector_data = sector_pnl[sector]
                sector_data["market_value"] += position.market_value
                sector_data["cost_basis"] += position.cost_basis
                sector_data["unrealized_pnl"] += position.unrealized_pnl
                sector_data["realized_pnl"] += position.realized_pnl
                sector_data["total_pnl"] += position.total_pnl
                sector_data["positions_count"] += 1
                sector_data["symbols"].append(position.symbol)

            # Convert to percentage allocations
            total_market_value = snapshot.total_market_value

            sector_breakdown = {}
            for sector, data in sector_pnl.items():
                allocation_pct = (
                    (data["market_value"] / total_market_value * 100)
                    if total_market_value > 0
                    else 0
                )

                sector_breakdown[sector] = {
                    "market_value": float(data["market_value"]),
                    "cost_basis": float(data["cost_basis"]),
                    "unrealized_pnl": float(data["unrealized_pnl"]),
                    "realized_pnl": float(data["realized_pnl"]),
                    "total_pnl": float(data["total_pnl"]),
                    "allocation_pct": float(allocation_pct),
                    "positions_count": data["positions_count"],
                    "symbols": data["symbols"],
                }

            return {
                "portfolio_id": portfolio_id,
                "timestamp": snapshot.timestamp.isoformat(),
                "sector_breakdown": sector_breakdown,
                "total_sectors": len(sector_breakdown),
            }

        except Exception as e:
            self.logger.error(f"Error calculating sector P&L: {e}")
            return {}

    async def calculate_performance_attribution(
        self, portfolio_id: int, benchmark_symbol: str = "SPY"
    ) -> Dict[str, Any]:
        """
        Calculate performance attribution analysis.

        Args:
            portfolio_id: Portfolio identifier
            benchmark_symbol: Benchmark symbol for comparison

        Returns:
            Performance attribution metrics
        """
        try:
            snapshot = await self.calculate_portfolio_pnl(portfolio_id)

            # Get benchmark performance
            benchmark_return = await self._get_benchmark_return(benchmark_symbol)

            # Calculate portfolio return
            portfolio_return = (
                (snapshot.total_pnl / snapshot.total_cost_basis)
                if snapshot.total_cost_basis > 0
                else Decimal("0")
            )

            # Calculate attribution metrics
            active_return = portfolio_return - Decimal(str(benchmark_return))

            # Position-level attribution
            position_attribution = []
            for position in snapshot.positions:
                position_return = (
                    (position.total_pnl / position.cost_basis)
                    if position.cost_basis > 0
                    else Decimal("0")
                )
                weight = (
                    (position.market_value / snapshot.total_market_value)
                    if snapshot.total_market_value > 0
                    else Decimal("0")
                )

                # Simplified attribution (in practice, you'd use sector weights and returns)
                contribution = weight * position_return

                position_attribution.append(
                    {
                        "symbol": position.symbol,
                        "weight": float(weight * 100),
                        "return": float(position_return * 100),
                        "contribution": float(contribution * 100),
                        "pnl": float(position.total_pnl),
                    }
                )

            return {
                "portfolio_id": portfolio_id,
                "benchmark_symbol": benchmark_symbol,
                "benchmark_return": benchmark_return,
                "portfolio_return": float(portfolio_return * 100),
                "active_return": float(active_return * 100),
                "position_attribution": sorted(
                    position_attribution, key=lambda x: x["contribution"], reverse=True
                ),
                "timestamp": snapshot.timestamp.isoformat(),
            }

        except Exception as e:
            self.logger.error(f"Error calculating performance attribution: {e}")
            return {}

    async def _calculate_all_portfolios_pnl(self):
        """Calculate P&L for all active portfolios."""
        try:
            portfolios = await self._get_active_portfolios()

            for portfolio in portfolios:
                portfolio_id = portfolio.get("id")
                if portfolio_id:
                    await self.calculate_portfolio_pnl(portfolio_id)
                    await asyncio.sleep(0.1)  # Small delay between portfolios

        except Exception as e:
            self.logger.error(f"Error calculating all portfolios P&L: {e}")

    async def _calculate_position_pnl(self, position_data: Dict[str, Any]) -> Position:
        """Calculate P&L for a single position."""
        try:
            symbol = position_data["symbol"]
            quantity = Decimal(str(position_data["quantity"]))
            average_cost = Decimal(str(position_data["average_price"]))
            current_price = Decimal(str(position_data.get("current_price", 0)))

            # Get realized P&L from database
            realized_pnl = Decimal(str(position_data.get("realized_pnl", 0)))

            # Calculate market value
            market_value = quantity * current_price
            cost_basis = quantity * average_cost

            # Calculate unrealized P&L
            unrealized_pnl = market_value - cost_basis

            # Calculate day P&L (requires previous day close)
            previous_close = await self._get_previous_close(symbol)
            day_pnl = (
                quantity * (current_price - Decimal(str(previous_close)))
                if previous_close
                else Decimal("0")
            )

            # Total P&L
            total_pnl = unrealized_pnl + realized_pnl

            # Determine asset type
            asset_type = self._determine_asset_type(symbol)

            position = Position(
                symbol=symbol,
                quantity=quantity,
                average_cost=average_cost,
                current_price=current_price,
                market_value=market_value,
                unrealized_pnl=unrealized_pnl,
                realized_pnl=realized_pnl,
                day_pnl=day_pnl,
                total_pnl=total_pnl,
                asset_type=asset_type,
                currency=position_data.get("currency", "USD"),
            )

            return position

        except Exception as e:
            self.logger.error(f"Error calculating position P&L: {e}")
            # Return empty position on error
            return Position(
                symbol=position_data.get("symbol", "UNKNOWN"),
                quantity=Decimal("0"),
                average_cost=Decimal("0"),
            )

    def _aggregate_portfolio_pnl(
        self, portfolio_id: int, positions: List[Position]
    ) -> PnLSnapshot:
        """Aggregate position P&L into portfolio snapshot."""
        total_market_value = sum(pos.market_value for pos in positions)
        total_cost_basis = sum(pos.cost_basis for pos in positions)
        total_unrealized_pnl = sum(pos.unrealized_pnl for pos in positions)
        total_realized_pnl = sum(pos.realized_pnl for pos in positions)
        total_day_pnl = sum(pos.day_pnl for pos in positions)
        total_pnl = total_unrealized_pnl + total_realized_pnl

        return PnLSnapshot(
            timestamp=datetime.now(),
            portfolio_id=portfolio_id,
            total_market_value=total_market_value,
            total_cost_basis=total_cost_basis,
            total_unrealized_pnl=total_unrealized_pnl,
            total_realized_pnl=total_realized_pnl,
            total_day_pnl=total_day_pnl,
            total_pnl=total_pnl,
            positions=positions,
        )

    async def _update_position_prices(self, positions: List[Dict[str, Any]]):
        """Update current prices for positions."""
        for position in positions:
            symbol = position["symbol"]

            try:
                # Get current price from appropriate data source
                current_price = await self._get_current_price(symbol)
                position["current_price"] = current_price

            except Exception as e:
                self.logger.error(f"Error updating price for {symbol}: {e}")
                position["current_price"] = position.get("current_price", 0)

    async def _get_current_price(self, symbol: str) -> float:
        """Get current market price for a symbol."""
        try:
            # Check cache first
            cached_price = await self.cache_manager.get(f"current_price:{symbol}")
            if cached_price:
                return float(cached_price)

            # Determine data source based on symbol format
            price = 0.0

            if symbol.endswith("=X"):  # Forex
                data = await self._get_latest_forex_price(symbol)
                price = data.get("rate", 0) if data else 0
            elif "-USD" in symbol:  # Crypto
                data = await self._get_latest_crypto_price(symbol)
                price = data.get("price", 0) if data else 0
            elif "=F" in symbol:  # Commodities
                data = await self._get_latest_commodity_price(symbol)
                price = data.get("price", 0) if data else 0
            else:  # Stocks
                data = await self._get_latest_stock_price(symbol)
                price = data.get("close", 0) if data else 0

            # Cache the price
            await self.cache_manager.set(f"current_price:{symbol}", price, ttl=60)

            return price

        except Exception as e:
            self.logger.error(f"Error getting current price for {symbol}: {e}")
            return 0.0

    async def _get_latest_stock_price(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get latest stock price from database."""
        try:
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=1)
            data = await self.db_manager.get_stock_data(symbol, start_time, end_time)
            return data[-1] if data else None
        except:
            return None

    async def _get_latest_forex_price(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get latest forex price from database."""
        try:
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=1)
            data = await self.db_manager.get_forex_data(symbol, start_time, end_time)
            return data[-1] if data else None
        except:
            return None

    async def _get_latest_crypto_price(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get latest crypto price from database."""
        try:
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=1)
            data = await self.db_manager.get_crypto_data(symbol, start_time, end_time)
            return data[-1] if data else None
        except:
            return None

    async def _get_latest_commodity_price(
        self, symbol: str
    ) -> Optional[Dict[str, Any]]:
        """Get latest commodity price from database."""
        try:
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=1)
            data = await self.db_manager.get_commodity_data(
                symbol, start_time, end_time
            )
            return data[-1] if data else None
        except:
            return None

    def _determine_asset_type(self, symbol: str) -> str:
        """Determine asset type from symbol format."""
        if symbol.endswith("=X"):
            return "forex"
        elif "-USD" in symbol or symbol.endswith("-USDT"):
            return "crypto"
        elif "=F" in symbol:
            return "commodity"
        else:
            return "stock"

    async def _get_previous_close(self, symbol: str) -> float:
        """Get previous trading day close price."""
        try:
            end_time = datetime.now() - timedelta(days=1)
            start_time = end_time - timedelta(days=2)

            # Get appropriate data based on symbol type
            if symbol.endswith("=X"):
                data = await self.db_manager.get_forex_data(
                    symbol, start_time, end_time
                )
                return data[-1]["rate"] if data else 0
            elif "-USD" in symbol:
                data = await self.db_manager.get_crypto_data(
                    symbol, start_time, end_time
                )
                return data[-1]["price"] if data else 0
            elif "=F" in symbol:
                data = await self.db_manager.get_commodity_data(
                    symbol, start_time, end_time
                )
                return data[-1]["price"] if data else 0
            else:
                data = await self.db_manager.get_stock_data(
                    symbol, start_time, end_time
                )
                return data[-1]["close"] if data else 0

        except Exception as e:
            self.logger.error(f"Error getting previous close for {symbol}: {e}")
            return 0

    def _get_top_performers(
        self,
        positions: List[Position],
        performance_type: str = "gainers",
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """Get top performing positions."""
        try:
            # Sort by unrealized P&L percentage
            sorted_positions = sorted(
                positions,
                key=lambda p: (
                    (p.unrealized_pnl / p.cost_basis) if p.cost_basis > 0 else 0
                ),
                reverse=(performance_type == "gainers"),
            )

            top_performers = []
            for position in sorted_positions[:limit]:
                pnl_pct = (
                    (position.unrealized_pnl / position.cost_basis * 100)
                    if position.cost_basis > 0
                    else 0
                )

                top_performers.append(
                    {
                        "symbol": position.symbol,
                        "unrealized_pnl": float(position.unrealized_pnl),
                        "unrealized_pnl_pct": float(pnl_pct),
                        "market_value": float(position.market_value),
                    }
                )

            return top_performers

        except Exception as e:
            self.logger.error(f"Error getting top performers: {e}")
            return []

    # Helper methods for data access
    async def _get_active_portfolios(self) -> List[Dict[str, Any]]:
        """Get active portfolios from database."""
        try:
            # This would query your portfolios table
            # For now, return empty list
            return []
        except Exception as e:
            self.logger.error(f"Error getting active portfolios: {e}")
            return []

    async def _get_portfolio_positions(self, portfolio_id: int) -> List[Dict[str, Any]]:
        """Get positions for a portfolio."""
        try:
            # This would query your portfolio_positions table
            # For now, return empty list
            return []
        except Exception as e:
            self.logger.error(f"Error getting portfolio positions: {e}")
            return []

    def _create_empty_snapshot(self, portfolio_id: int) -> PnLSnapshot:
        """Create empty P&L snapshot."""
        return PnLSnapshot(
            timestamp=datetime.now(),
            portfolio_id=portfolio_id,
            total_market_value=Decimal("0"),
            total_cost_basis=Decimal("0"),
            total_unrealized_pnl=Decimal("0"),
            total_realized_pnl=Decimal("0"),
            total_day_pnl=Decimal("0"),
            total_pnl=Decimal("0"),
            positions=[],
        )

    async def _cache_pnl_snapshot(self, snapshot: PnLSnapshot):
        """Cache P&L snapshot for quick access."""
        try:
            cache_key = f"pnl_snapshot:{snapshot.portfolio_id}"
            cache_data = {
                "timestamp": snapshot.timestamp.isoformat(),
                "total_market_value": float(snapshot.total_market_value),
                "total_pnl": float(snapshot.total_pnl),
                "positions_count": len(snapshot.positions),
            }
            await self.cache_manager.set(cache_key, cache_data, ttl=120)
        except Exception as e:
            self.logger.error(f"Error caching P&L snapshot: {e}")

    async def _store_pnl_history(self, snapshot: PnLSnapshot):
        """Store P&L history for trend analysis."""
        # This would store historical P&L data in the database
        pass

    async def _get_previous_snapshot(self, portfolio_id: int) -> Optional[PnLSnapshot]:
        """Get previous P&L snapshot for comparison."""
        # This would retrieve the previous snapshot from cache or database
        return None

    async def _get_position_historical_pnl(
        self, portfolio_id: int, symbol: str
    ) -> List[Dict[str, Any]]:
        """Get historical P&L for a position."""
        # This would return historical P&L data
        return []

    async def _get_benchmark_return(self, benchmark_symbol: str) -> float:
        """Get benchmark return for performance attribution."""
        try:
            # Get benchmark data for comparison
            end_time = datetime.now()
            start_time = end_time - timedelta(days=30)  # 30-day return

            data = await self.db_manager.get_stock_data(
                benchmark_symbol, start_time, end_time
            )
            if len(data) >= 2:
                start_price = data[0]["close"]
                end_price = data[-1]["close"]
                return (end_price - start_price) / start_price

            return 0.0

        except Exception as e:
            self.logger.error(f"Error getting benchmark return: {e}")
            return 0.0

    def is_healthy(self) -> bool:
        """Check if the P&L engine is healthy."""
        return self.running
