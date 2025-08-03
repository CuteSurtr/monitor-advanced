"""
Portfolio API Module

Provides FastAPI routes for enhanced portfolio management including
transaction tracking, P&L calculation, performance analysis, rebalancing,
and tax optimization.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel, Field
import logging

from src.portfolio.portfolio_manager import (
    PortfolioManager, Transaction, TransactionType, Position, 
    PerformanceMetrics, RebalancingSuggestion, TaxOptimization
)
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Create router
portfolio_router = APIRouter(prefix="/api/portfolio", tags=["portfolio"])

# Global portfolio manager instance
portfolio_manager = None

def set_portfolio_manager(manager: PortfolioManager):
    """Set the portfolio manager instance."""
    global portfolio_manager
    portfolio_manager = manager

async def get_portfolio_manager() -> PortfolioManager:
    """Get portfolio manager from the main application."""
    if portfolio_manager is None:
        raise HTTPException(status_code=500, detail="Portfolio manager not initialized")
    return portfolio_manager


# Pydantic models for API requests/responses
class TransactionCreate(BaseModel):
    """Request model for creating a transaction."""
    symbol: str = Field(..., description="Stock symbol")
    transaction_type: TransactionType = Field(..., description="Type of transaction")
    quantity: Decimal = Field(..., gt=0, description="Number of shares")
    price: Decimal = Field(..., gt=0, description="Price per share")
    commission: Decimal = Field(0, ge=0, description="Commission/fees")
    timestamp: Optional[datetime] = Field(None, description="Transaction timestamp")
    tax_lot_id: Optional[str] = Field(None, description="Tax lot identifier")
    notes: Optional[str] = Field("", description="Transaction notes")

class TransactionResponse(BaseModel):
    """Response model for transaction data."""
    id: int
    symbol: str
    transaction_type: TransactionType
    quantity: Decimal
    price: Decimal
    commission: Decimal
    timestamp: datetime
    tax_lot_id: Optional[str]
    notes: str

class PositionResponse(BaseModel):
    """Response model for position data."""
    symbol: str
    quantity: Decimal
    average_cost: Decimal
    current_price: Decimal
    market_value: Decimal
    unrealized_pnl: Decimal
    realized_pnl: Decimal
    total_pnl: Decimal
    cost_basis: Decimal
    last_updated: datetime

class PerformanceResponse(BaseModel):
    """Response model for performance metrics."""
    total_value: Decimal
    total_cost: Decimal
    total_pnl: Decimal
    total_return_percent: float
    daily_pnl: Decimal
    daily_return_percent: float
    weekly_pnl: Decimal
    weekly_return_percent: float
    monthly_pnl: Decimal
    monthly_return_percent: float
    sharpe_ratio: float
    max_drawdown: float
    volatility: float
    beta: float

class RebalancingResponse(BaseModel):
    """Response model for rebalancing suggestions."""
    symbol: str
    current_allocation: float
    target_allocation: float
    suggested_action: str
    suggested_quantity: Decimal
    suggested_value: Decimal
    priority: str

class TaxOptimizationResponse(BaseModel):
    """Response model for tax optimization data."""
    short_term_gains: Decimal
    long_term_gains: Decimal
    short_term_losses: Decimal
    long_term_losses: Decimal
    net_capital_gains: Decimal
    tax_liability: Decimal
    tax_rate: float
    harvesting_opportunities: List[Dict[str, Any]]

class PortfolioSummaryResponse(BaseModel):
    """Response model for portfolio summary."""
    total_positions: int
    total_value: Decimal
    total_pnl: Decimal
    total_return_percent: float
    top_gainers: List[Dict[str, Any]]
    top_losers: List[Dict[str, Any]]
    recent_transactions: List[TransactionResponse]


# Transaction endpoints
@portfolio_router.post("/transactions", response_model=Dict[str, Any])
async def create_transaction(
    transaction: TransactionCreate,
    manager: PortfolioManager = Depends(get_portfolio_manager)
):
    """Create a new portfolio transaction."""
    try:
        # Convert to Transaction object
        tx = Transaction(
            symbol=transaction.symbol,
            transaction_type=transaction.transaction_type,
            quantity=transaction.quantity,
            price=transaction.price,
            commission=transaction.commission,
            timestamp=transaction.timestamp or datetime.now(),
            tax_lot_id=transaction.tax_lot_id,
            notes=transaction.notes
        )
        
        transaction_id = await manager.add_transaction(tx)
        
        return {
            "message": "Transaction created successfully",
            "transaction_id": transaction_id,
            "transaction": TransactionResponse(
                id=transaction_id,
                symbol=tx.symbol,
                transaction_type=tx.transaction_type,
                quantity=tx.quantity,
                price=tx.price,
                commission=tx.commission,
                timestamp=tx.timestamp,
                tax_lot_id=tx.tax_lot_id,
                notes=tx.notes
            )
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating transaction: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@portfolio_router.get("/transactions", response_model=List[TransactionResponse])
async def get_transactions(
    symbol: Optional[str] = Query(None, description="Filter by symbol"),
    start_date: Optional[datetime] = Query(None, description="Start date filter"),
    end_date: Optional[datetime] = Query(None, description="End date filter"),
    limit: int = Query(100, le=1000, description="Maximum number of transactions"),
    manager: PortfolioManager = Depends(get_portfolio_manager)
):
    """Get portfolio transactions with optional filtering."""
    try:
        transactions = await manager.get_transactions(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )
        
        return [
            TransactionResponse(
                id=tx.id,
                symbol=tx.symbol,
                transaction_type=tx.transaction_type,
                quantity=tx.quantity,
                price=tx.price,
                commission=tx.commission,
                timestamp=tx.timestamp,
                tax_lot_id=tx.tax_lot_id,
                notes=tx.notes
            )
            for tx in transactions
        ]
        
    except Exception as e:
        logger.error(f"Error getting transactions: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Position endpoints
@portfolio_router.get("/positions", response_model=List[PositionResponse])
async def get_positions(
    manager: PortfolioManager = Depends(get_portfolio_manager)
):
    """Get current portfolio positions."""
    try:
        positions = await manager.get_positions()
        
        return [
            PositionResponse(
                symbol=pos.symbol,
                quantity=pos.quantity,
                average_cost=pos.average_cost,
                current_price=pos.current_price,
                market_value=pos.market_value,
                unrealized_pnl=pos.unrealized_pnl,
                realized_pnl=pos.realized_pnl,
                total_pnl=pos.total_pnl,
                cost_basis=pos.cost_basis,
                last_updated=pos.last_updated
            )
            for pos in positions
        ]
        
    except Exception as e:
        logger.error(f"Error getting positions: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@portfolio_router.get("/positions/{symbol}", response_model=PositionResponse)
async def get_position(
    symbol: str,
    manager: PortfolioManager = Depends(get_portfolio_manager)
):
    """Get a specific portfolio position."""
    try:
        positions = await manager.get_positions()
        
        for pos in positions:
            if pos.symbol.upper() == symbol.upper():
                return PositionResponse(
                    symbol=pos.symbol,
                    quantity=pos.quantity,
                    average_cost=pos.average_cost,
                    current_price=pos.current_price,
                    market_value=pos.market_value,
                    unrealized_pnl=pos.unrealized_pnl,
                    realized_pnl=pos.realized_pnl,
                    total_pnl=pos.total_pnl,
                    cost_basis=pos.cost_basis,
                    last_updated=pos.last_updated
                )
        
        raise HTTPException(status_code=404, detail=f"Position for {symbol} not found")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting position for {symbol}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Performance endpoints
@portfolio_router.get("/performance", response_model=PerformanceResponse)
async def get_performance(
    period: str = Query("all", description="Performance period"),
    manager: PortfolioManager = Depends(get_portfolio_manager)
):
    """Get portfolio performance metrics."""
    try:
        metrics = await manager.get_performance_metrics(period=period)
        
        return PerformanceResponse(
            total_value=metrics.total_value,
            total_cost=metrics.total_cost,
            total_pnl=metrics.total_pnl,
            total_return_percent=metrics.total_return_percent,
            daily_pnl=metrics.daily_pnl,
            daily_return_percent=metrics.daily_return_percent,
            weekly_pnl=metrics.weekly_pnl,
            weekly_return_percent=metrics.weekly_return_percent,
            monthly_pnl=metrics.monthly_pnl,
            monthly_return_percent=metrics.monthly_return_percent,
            sharpe_ratio=metrics.sharpe_ratio,
            max_drawdown=metrics.max_drawdown,
            volatility=metrics.volatility,
            beta=metrics.beta
        )
        
    except Exception as e:
        logger.error(f"Error getting performance metrics: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Rebalancing endpoints
@portfolio_router.get("/rebalancing", response_model=List[RebalancingResponse])
async def get_rebalancing_suggestions(
    tolerance: float = Query(0.05, ge=0.01, le=0.20, description="Rebalancing tolerance"),
    manager: PortfolioManager = Depends(get_portfolio_manager)
):
    """Get portfolio rebalancing suggestions."""
    try:
        suggestions = await manager.get_rebalancing_suggestions(tolerance=tolerance)
        
        return [
            RebalancingResponse(
                symbol=sug.symbol,
                current_allocation=sug.current_allocation,
                target_allocation=sug.target_allocation,
                suggested_action=sug.suggested_action,
                suggested_quantity=sug.suggested_quantity,
                suggested_value=sug.suggested_value,
                priority=sug.priority
            )
            for sug in suggestions
        ]
        
    except Exception as e:
        logger.error(f"Error getting rebalancing suggestions: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Tax optimization endpoints
@portfolio_router.get("/tax-optimization", response_model=TaxOptimizationResponse)
async def get_tax_optimization(
    manager: PortfolioManager = Depends(get_portfolio_manager)
):
    """Get tax optimization calculations and opportunities."""
    try:
        tax_opt = await manager.get_tax_optimization()
        
        return TaxOptimizationResponse(
            short_term_gains=tax_opt.short_term_gains,
            long_term_gains=tax_opt.long_term_gains,
            short_term_losses=tax_opt.short_term_losses,
            long_term_losses=tax_opt.long_term_losses,
            net_capital_gains=tax_opt.net_capital_gains,
            tax_liability=tax_opt.tax_liability,
            tax_rate=tax_opt.tax_rate,
            harvesting_opportunities=tax_opt.harvesting_opportunities
        )
        
    except Exception as e:
        logger.error(f"Error getting tax optimization: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Portfolio summary endpoint
@portfolio_router.get("/summary", response_model=PortfolioSummaryResponse)
async def get_portfolio_summary(
    manager: PortfolioManager = Depends(get_portfolio_manager)
):
    """Get portfolio summary with key metrics."""
    try:
        positions = await manager.get_positions()
        transactions = await manager.get_transactions(limit=10)
        performance = await manager.get_performance_metrics()
        
        # Calculate summary metrics
        total_positions = len(positions)
        total_value = performance.total_value
        total_pnl = performance.total_pnl
        total_return_percent = performance.total_return_percent
        
        # Get top gainers and losers
        sorted_positions = sorted(positions, key=lambda p: p.total_pnl, reverse=True)
        top_gainers = [
            {
                "symbol": pos.symbol,
                "pnl": float(pos.total_pnl),
                "return_percent": float((pos.total_pnl / pos.cost_basis * 100) if pos.cost_basis > 0 else 0)
            }
            for pos in sorted_positions[:5] if pos.total_pnl > 0
        ]
        
        top_losers = [
            {
                "symbol": pos.symbol,
                "pnl": float(pos.total_pnl),
                "return_percent": float((pos.total_pnl / pos.cost_basis * 100) if pos.cost_basis > 0 else 0)
            }
            for pos in sorted_positions[-5:] if pos.total_pnl < 0
        ]
        
        # Get recent transactions
        recent_transactions = [
            TransactionResponse(
                id=tx.id,
                symbol=tx.symbol,
                transaction_type=tx.transaction_type,
                quantity=tx.quantity,
                price=tx.price,
                commission=tx.commission,
                timestamp=tx.timestamp,
                tax_lot_id=tx.tax_lot_id,
                notes=tx.notes
            )
            for tx in transactions
        ]
        
        return PortfolioSummaryResponse(
            total_positions=total_positions,
            total_value=total_value,
            total_pnl=total_pnl,
            total_return_percent=total_return_percent,
            top_gainers=top_gainers,
            top_losers=top_losers,
            recent_transactions=recent_transactions
        )
        
    except Exception as e:
        logger.error(f"Error getting portfolio summary: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Configuration endpoints
@portfolio_router.get("/target-allocations")
async def get_target_allocations(
    manager: PortfolioManager = Depends(get_portfolio_manager)
):
    """Get current target allocations."""
    try:
        return {
            "target_allocations": manager.target_allocations,
            "message": "Target allocations retrieved successfully"
        }
        
    except Exception as e:
        logger.error(f"Error getting target allocations: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@portfolio_router.put("/target-allocations")
async def update_target_allocations(
    allocations: Dict[str, float],
    manager: PortfolioManager = Depends(get_portfolio_manager)
):
    """Update target allocations."""
    try:
        # Validate allocations
        total_allocation = sum(allocations.values())
        if abs(total_allocation - 1.0) > 0.01:
            raise ValueError("Target allocations must sum to 1.0 (100%)")
        
        # Update allocations
        manager.target_allocations = allocations
        
        # Invalidate rebalancing cache
        await manager.cache_manager.delete_pattern(f"{manager.cache_keys['rebalancing']}:*")
        
        return {
            "message": "Target allocations updated successfully",
            "target_allocations": manager.target_allocations
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating target allocations: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@portfolio_router.get("/tax-settings")
async def get_tax_settings(
    manager: PortfolioManager = Depends(get_portfolio_manager)
):
    """Get current tax settings."""
    try:
        return {
            "tax_settings": {
                "short_term_rate": manager.tax_settings['short_term_rate'],
                "long_term_rate": manager.tax_settings['long_term_rate'],
                "tax_lot_method": manager.tax_settings['tax_lot_method'].value,
                "wash_sale_window": manager.tax_settings['wash_sale_window']
            },
            "message": "Tax settings retrieved successfully"
        }
        
    except Exception as e:
        logger.error(f"Error getting tax settings: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@portfolio_router.put("/tax-settings")
async def update_tax_settings(
    short_term_rate: float = Query(..., ge=0, le=1, description="Short-term capital gains rate"),
    long_term_rate: float = Query(..., ge=0, le=1, description="Long-term capital gains rate"),
    tax_lot_method: str = Query(..., description="Tax lot identification method"),
    wash_sale_window: int = Query(..., ge=1, le=365, description="Wash sale window in days"),
    manager: PortfolioManager = Depends(get_portfolio_manager)
):
    """Update tax settings."""
    try:
        # Validate tax lot method
        try:
            tax_lot_enum = TaxLotMethod(tax_lot_method)
        except ValueError:
            raise ValueError("Invalid tax lot method. Must be one of: fifo, lifo, specific, average")
        
        # Update settings
        manager.tax_settings.update({
            'short_term_rate': short_term_rate,
            'long_term_rate': long_term_rate,
            'tax_lot_method': tax_lot_enum,
            'wash_sale_window': wash_sale_window
        })
        
        # Invalidate tax optimization cache
        await manager.cache_manager.delete(manager.cache_keys['tax_optimization'])
        
        return {
            "message": "Tax settings updated successfully",
            "tax_settings": {
                "short_term_rate": short_term_rate,
                "long_term_rate": long_term_rate,
                "tax_lot_method": tax_lot_method,
                "wash_sale_window": wash_sale_window
            }
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating tax settings: {e}")
        raise HTTPException(status_code=500, detail="Internal server error") 