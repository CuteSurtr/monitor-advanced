"""
Enhanced Portfolio Manager Module

Provides comprehensive portfolio management including transaction tracking,
P&L calculation, performance analysis, rebalancing suggestions, and tax optimization.
"""

import asyncio
from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime, timedelta
from decimal import Decimal
import pandas as pd
import numpy as np
from dataclasses import dataclass
from enum import Enum
import logging

from src.utils.database import DatabaseManager
from src.utils.cache import CacheManager
from src.analytics.analytics_engine import AnalyticsEngine
from src.utils.logger import get_logger

logger = get_logger(__name__)


class TransactionType(Enum):
    """Transaction types."""
    BUY = "buy"
    SELL = "sell"
    DIVIDEND = "dividend"
    SPLIT = "split"
    MERGE = "merge"


class TaxLotMethod(Enum):
    """Tax lot identification methods."""
    FIFO = "fifo"  # First In, First Out
    LIFO = "lifo"  # Last In, First Out
    SPECIFIC = "specific"  # Specific identification
    AVERAGE = "average"  # Average cost basis


@dataclass
class Transaction:
    """Represents a portfolio transaction."""
    id: Optional[int] = None
    symbol: str = ""
    transaction_type: TransactionType = TransactionType.BUY
    quantity: Decimal = Decimal('0')
    price: Decimal = Decimal('0')
    commission: Decimal = Decimal('0')
    timestamp: datetime = None
    tax_lot_id: Optional[str] = None
    notes: str = ""

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class Position:
    """Represents a current portfolio position."""
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


@dataclass
class PerformanceMetrics:
    """Portfolio performance metrics."""
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


@dataclass
class RebalancingSuggestion:
    """Portfolio rebalancing suggestion."""
    symbol: str
    current_allocation: float
    target_allocation: float
    suggested_action: str  # "buy" or "sell"
    suggested_quantity: Decimal
    suggested_value: Decimal
    priority: str  # "high", "medium", "low"


@dataclass
class TaxOptimization:
    """Tax optimization calculations."""
    short_term_gains: Decimal
    long_term_gains: Decimal
    short_term_losses: Decimal
    long_term_losses: Decimal
    net_capital_gains: Decimal
    tax_liability: Decimal
    tax_rate: float
    harvesting_opportunities: List[Dict[str, Any]]


class PortfolioManager:
    """
    Enhanced portfolio management system.
    
    Provides comprehensive portfolio tracking, P&L calculation,
    performance analysis, rebalancing suggestions, and tax optimization.
    """
    
    def __init__(self, 
                 db_manager: DatabaseManager,
                 cache_manager: CacheManager,
                 analytics_engine: AnalyticsEngine):
        self.db_manager = db_manager
        self.cache_manager = cache_manager
        self.analytics_engine = analytics_engine
        self.logger = logger
        
        # Cache keys
        self.cache_keys = {
            'positions': 'portfolio:positions',
            'performance': 'portfolio:performance',
            'transactions': 'portfolio:transactions',
            'rebalancing': 'portfolio:rebalancing',
            'tax_optimization': 'portfolio:tax_optimization'
        }
        
        # Default target allocations (can be configured)
        self.target_allocations = {
            'AAPL': 0.15,
            'GOOGL': 0.12,
            'MSFT': 0.12,
            'TSLA': 0.10,
            'AMZN': 0.10,
            'META': 0.08,
            'NVDA': 0.08,
            'NFLX': 0.05,
            'PYPL': 0.05,
            'ADBE': 0.05,
            'CRM': 0.03,
            'ORCL': 0.02
        }
        
        # Tax settings
        self.tax_settings = {
            'short_term_rate': 0.22,  # 22% for short-term gains
            'long_term_rate': 0.15,   # 15% for long-term gains
            'tax_lot_method': TaxLotMethod.FIFO,
            'wash_sale_window': 30    # days
        }
    
    async def add_transaction(self, transaction: Transaction) -> int:
        """Add a new transaction to the portfolio."""
        try:
            # Validate transaction
            if transaction.quantity <= 0:
                raise ValueError("Quantity must be positive")
            if transaction.price <= 0:
                raise ValueError("Price must be positive")
            
            # Generate tax lot ID if not provided
            if not transaction.tax_lot_id:
                transaction.tax_lot_id = f"{transaction.symbol}_{transaction.timestamp.strftime('%Y%m%d_%H%M%S')}"
            
            # Store transaction in database
            query = """
                INSERT INTO portfolio_transactions 
                (symbol, transaction_type, quantity, price, commission, timestamp, tax_lot_id, notes)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                RETURNING id
            """
            
            result = await self.db_manager.execute_query(
                query,
                transaction.symbol,
                transaction.transaction_type.value,
                float(transaction.quantity),
                float(transaction.price),
                float(transaction.commission),
                transaction.timestamp,
                transaction.tax_lot_id,
                transaction.notes
            )
            
            transaction_id = result[0]['id']
            
            # Invalidate cache
            await self.cache_manager.delete(self.cache_keys['positions'])
            await self.cache_manager.delete(self.cache_keys['performance'])
            await self.cache_manager.delete(self.cache_keys['transactions'])
            
            self.logger.info(f"Added transaction {transaction_id} for {transaction.symbol}")
            return transaction_id
            
        except Exception as e:
            self.logger.error(f"Error adding transaction: {e}")
            raise
    
    async def get_transactions(self, 
                             symbol: Optional[str] = None,
                             start_date: Optional[datetime] = None,
                             end_date: Optional[datetime] = None,
                             limit: int = 100) -> List[Transaction]:
        """Get portfolio transactions with optional filtering."""
        try:
            # Check cache first
            cache_key = f"{self.cache_keys['transactions']}:{symbol}:{start_date}:{end_date}:{limit}"
            cached = await self.cache_manager.get(cache_key)
            if cached:
                return [Transaction(**t) for t in cached]
            
            # Build query
            query = "SELECT * FROM portfolio_transactions WHERE 1=1"
            params = []
            param_count = 0
            
            if symbol:
                param_count += 1
                query += f" AND symbol = ${param_count}"
                params.append(symbol)
            
            if start_date:
                param_count += 1
                query += f" AND timestamp >= ${param_count}"
                params.append(start_date)
            
            if end_date:
                param_count += 1
                query += f" AND timestamp <= ${param_count}"
                params.append(end_date)
            
            query += f" ORDER BY timestamp DESC LIMIT {limit}"
            
            result = await self.db_manager.execute_query(query, *params)
            
            transactions = []
            for row in result:
                transaction = Transaction(
                    id=row['id'],
                    symbol=row['symbol'],
                    transaction_type=TransactionType(row['transaction_type']),
                    quantity=Decimal(str(row['quantity'])),
                    price=Decimal(str(row['price'])),
                    commission=Decimal(str(row['commission'])),
                    timestamp=row['timestamp'],
                    tax_lot_id=row['tax_lot_id'],
                    notes=row['notes']
                )
                transactions.append(transaction)
            
            # Cache result
            await self.cache_manager.set(cache_key, [t.__dict__ for t in transactions], expire=300)
            
            return transactions
            
        except Exception as e:
            self.logger.error(f"Error getting transactions: {e}")
            raise
    
    async def get_positions(self) -> List[Position]:
        """Get current portfolio positions."""
        try:
            # Check cache first
            cached = await self.cache_manager.get(self.cache_keys['positions'])
            if cached:
                return [Position(**p) for p in cached]
            
            # Get all transactions
            transactions = await self.get_transactions(limit=1000)
            
            # Calculate positions
            positions = {}
            for transaction in transactions:
                symbol = transaction.symbol
                
                if symbol not in positions:
                    positions[symbol] = {
                        'quantity': Decimal('0'),
                        'total_cost': Decimal('0'),
                        'realized_pnl': Decimal('0')
                    }
                
                pos = positions[symbol]
                
                if transaction.transaction_type == TransactionType.BUY:
                    pos['quantity'] += transaction.quantity
                    pos['total_cost'] += (transaction.quantity * transaction.price + transaction.commission)
                elif transaction.transaction_type == TransactionType.SELL:
                    # Calculate realized P&L for this sale
                    avg_cost = pos['total_cost'] / pos['quantity'] if pos['quantity'] > 0 else Decimal('0')
                    realized_pnl = (transaction.price - avg_cost) * transaction.quantity - transaction.commission
                    pos['realized_pnl'] += realized_pnl
                    
                    pos['quantity'] -= transaction.quantity
                    # Reduce cost basis proportionally
                    if pos['quantity'] > 0:
                        cost_reduction = (transaction.quantity / (pos['quantity'] + transaction.quantity)) * pos['total_cost']
                        pos['total_cost'] -= cost_reduction
                    else:
                        pos['total_cost'] = Decimal('0')
            
            # Get current prices and calculate market values
            current_positions = []
            for symbol, pos_data in positions.items():
                if pos_data['quantity'] > 0:
                    # Get current price (this would come from your market data)
                    current_price = await self._get_current_price(symbol)
                    
                    quantity = pos_data['quantity']
                    cost_basis = pos_data['total_cost']
                    market_value = quantity * current_price
                    avg_cost = cost_basis / quantity
                    unrealized_pnl = market_value - cost_basis
                    total_pnl = unrealized_pnl + pos_data['realized_pnl']
                    
                    position = Position(
                        symbol=symbol,
                        quantity=quantity,
                        average_cost=avg_cost,
                        current_price=current_price,
                        market_value=market_value,
                        unrealized_pnl=unrealized_pnl,
                        realized_pnl=pos_data['realized_pnl'],
                        total_pnl=total_pnl,
                        cost_basis=cost_basis,
                        last_updated=datetime.now()
                    )
                    current_positions.append(position)
            
            # Cache result
            await self.cache_manager.set(self.cache_keys['positions'], 
                                       [p.__dict__ for p in current_positions], 
                                       expire=60)
            
            return current_positions
            
        except Exception as e:
            self.logger.error(f"Error getting positions: {e}")
            raise
    
    async def get_performance_metrics(self, 
                                    period: str = "all") -> PerformanceMetrics:
        """Calculate portfolio performance metrics."""
        try:
            # Check cache first
            cache_key = f"{self.cache_keys['performance']}:{period}"
            cached = await self.cache_manager.get(cache_key)
            if cached:
                return PerformanceMetrics(**cached)
            
            positions = await self.get_positions()
            
            if not positions:
                return PerformanceMetrics(
                    total_value=Decimal('0'),
                    total_cost=Decimal('0'),
                    total_pnl=Decimal('0'),
                    total_return_percent=0.0,
                    daily_pnl=Decimal('0'),
                    daily_return_percent=0.0,
                    weekly_pnl=Decimal('0'),
                    weekly_return_percent=0.0,
                    monthly_pnl=Decimal('0'),
                    monthly_return_percent=0.0,
                    sharpe_ratio=0.0,
                    max_drawdown=0.0,
                    volatility=0.0,
                    beta=0.0
                )
            
            # Calculate basic metrics
            total_value = sum(p.market_value for p in positions)
            total_cost = sum(p.cost_basis for p in positions)
            total_pnl = sum(p.total_pnl for p in positions)
            total_return_percent = float((total_pnl / total_cost * 100) if total_cost > 0 else 0)
            
            # Calculate period returns
            daily_pnl = await self._calculate_period_pnl(1)
            weekly_pnl = await self._calculate_period_pnl(7)
            monthly_pnl = await self._calculate_period_pnl(30)
            
            daily_return_percent = float((daily_pnl / total_value * 100) if total_value > 0 else 0)
            weekly_return_percent = float((weekly_pnl / total_value * 100) if total_value > 0 else 0)
            monthly_return_percent = float((monthly_pnl / total_value * 100) if total_value > 0 else 0)
            
            # Calculate advanced metrics
            sharpe_ratio = await self._calculate_sharpe_ratio()
            max_drawdown = await self._calculate_max_drawdown()
            volatility = await self._calculate_volatility()
            beta = await self._calculate_beta()
            
            metrics = PerformanceMetrics(
                total_value=total_value,
                total_cost=total_cost,
                total_pnl=total_pnl,
                total_return_percent=total_return_percent,
                daily_pnl=daily_pnl,
                daily_return_percent=daily_return_percent,
                weekly_pnl=weekly_pnl,
                weekly_return_percent=weekly_return_percent,
                monthly_pnl=monthly_pnl,
                monthly_return_percent=monthly_return_percent,
                sharpe_ratio=sharpe_ratio,
                max_drawdown=max_drawdown,
                volatility=volatility,
                beta=beta
            )
            
            # Cache result
            await self.cache_manager.set(cache_key, metrics.__dict__, expire=300)
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error calculating performance metrics: {e}")
            raise
    
    async def get_rebalancing_suggestions(self, 
                                        tolerance: float = 0.05) -> List[RebalancingSuggestion]:
        """Get portfolio rebalancing suggestions."""
        try:
            # Check cache first
            cache_key = f"{self.cache_keys['rebalancing']}:{tolerance}"
            cached = await self.cache_manager.get(cache_key)
            if cached:
                return [RebalancingSuggestion(**s) for s in cached]
            
            positions = await self.get_positions()
            if not positions:
                return []
            
            total_value = sum(p.market_value for p in positions)
            suggestions = []
            
            for position in positions:
                current_allocation = float(position.market_value / total_value)
                target_allocation = self.target_allocations.get(position.symbol, 0.0)
                
                # Check if rebalancing is needed
                allocation_diff = abs(current_allocation - target_allocation)
                if allocation_diff > tolerance:
                    if current_allocation > target_allocation:
                        # Need to sell
                        suggested_action = "sell"
                        target_value = total_value * target_allocation
                        suggested_value = position.market_value - target_value
                        suggested_quantity = suggested_value / position.current_price
                    else:
                        # Need to buy
                        suggested_action = "buy"
                        target_value = total_value * target_allocation
                        suggested_value = target_value - position.market_value
                        suggested_quantity = suggested_value / position.current_price
                    
                    # Determine priority
                    if allocation_diff > 0.10:
                        priority = "high"
                    elif allocation_diff > 0.05:
                        priority = "medium"
                    else:
                        priority = "low"
                    
                    suggestion = RebalancingSuggestion(
                        symbol=position.symbol,
                        current_allocation=current_allocation,
                        target_allocation=target_allocation,
                        suggested_action=suggested_action,
                        suggested_quantity=suggested_quantity,
                        suggested_value=suggested_value,
                        priority=priority
                    )
                    suggestions.append(suggestion)
            
            # Sort by priority and allocation difference
            suggestions.sort(key=lambda x: (x.priority == "high", abs(x.current_allocation - x.target_allocation)), reverse=True)
            
            # Cache result
            await self.cache_manager.set(cache_key, [s.__dict__ for s in suggestions], expire=300)
            
            return suggestions
            
        except Exception as e:
            self.logger.error(f"Error getting rebalancing suggestions: {e}")
            raise
    
    async def get_tax_optimization(self) -> TaxOptimization:
        """Calculate tax optimization opportunities."""
        try:
            # Check cache first
            cached = await self.cache_manager.get(self.cache_keys['tax_optimization'])
            if cached:
                return TaxOptimization(**cached)
            
            positions = await self.get_positions()
            transactions = await self.get_transactions(limit=1000)
            
            # Calculate gains/losses by holding period
            short_term_gains = Decimal('0')
            long_term_gains = Decimal('0')
            short_term_losses = Decimal('0')
            long_term_losses = Decimal('0')
            
            # Group transactions by symbol and tax lot
            tax_lots = {}
            for transaction in transactions:
                if transaction.tax_lot_id not in tax_lots:
                    tax_lots[transaction.tax_lot_id] = []
                tax_lots[transaction.tax_lot_id].append(transaction)
            
            # Calculate realized gains/losses
            for tax_lot_id, lot_transactions in tax_lots.items():
                buy_transactions = [t for t in lot_transactions if t.transaction_type == TransactionType.BUY]
                sell_transactions = [t for t in lot_transactions if t.transaction_type == TransactionType.SELL]
                
                for sell_tx in sell_transactions:
                    # Find corresponding buy transaction (simplified - would need more complex logic for partial sales)
                    if buy_transactions:
                        buy_tx = buy_transactions[0]  # Simplified - should use proper tax lot matching
                        
                        # Calculate holding period
                        holding_period = (sell_tx.timestamp - buy_tx.timestamp).days
                        
                        # Calculate gain/loss
                        gain_loss = (sell_tx.price - buy_tx.price) * sell_tx.quantity - sell_tx.commission - buy_tx.commission
                        
                        if gain_loss > 0:
                            if holding_period > 365:
                                long_term_gains += gain_loss
                            else:
                                short_term_gains += gain_loss
                        else:
                            if holding_period > 365:
                                long_term_losses += abs(gain_loss)
                            else:
                                short_term_losses += abs(gain_loss)
            
            # Calculate net capital gains and tax liability
            net_capital_gains = short_term_gains + long_term_gains - short_term_losses - long_term_losses
            
            tax_liability = (short_term_gains * self.tax_settings['short_term_rate'] + 
                           long_term_gains * self.tax_settings['long_term_rate'])
            
            # Find tax loss harvesting opportunities
            harvesting_opportunities = await self._find_tax_loss_harvesting_opportunities(positions)
            
            tax_optimization = TaxOptimization(
                short_term_gains=short_term_gains,
                long_term_gains=long_term_gains,
                short_term_losses=short_term_losses,
                long_term_losses=long_term_losses,
                net_capital_gains=net_capital_gains,
                tax_liability=tax_liability,
                tax_rate=float(tax_liability / net_capital_gains) if net_capital_gains > 0 else 0.0,
                harvesting_opportunities=harvesting_opportunities
            )
            
            # Cache result
            await self.cache_manager.set(self.cache_keys['tax_optimization'], 
                                       tax_optimization.__dict__, 
                                       expire=3600)
            
            return tax_optimization
            
        except Exception as e:
            self.logger.error(f"Error calculating tax optimization: {e}")
            raise
    
    async def _get_current_price(self, symbol: str) -> Decimal:
        """Get current price for a symbol (placeholder - integrate with market data)."""
        # This would integrate with your market data collection
        # For now, return a mock price
        mock_prices = {
            'AAPL': 150.0, 'GOOGL': 2800.0, 'MSFT': 300.0, 'TSLA': 800.0,
            'AMZN': 3300.0, 'META': 350.0, 'NVDA': 200.0, 'NFLX': 500.0,
            'PYPL': 250.0, 'ADBE': 500.0, 'CRM': 250.0, 'ORCL': 80.0
        }
        return Decimal(str(mock_prices.get(symbol, 100.0)))
    
    async def _calculate_period_pnl(self, days: int) -> Decimal:
        """Calculate P&L for a specific period."""
        # This would calculate actual P&L based on historical data
        # For now, return a mock value
        return Decimal('0')
    
    async def _calculate_sharpe_ratio(self) -> float:
        """Calculate Sharpe ratio."""
        # This would calculate actual Sharpe ratio based on historical returns
        # For now, return a mock value
        return 1.2
    
    async def _calculate_max_drawdown(self) -> float:
        """Calculate maximum drawdown."""
        # This would calculate actual max drawdown based on historical data
        # For now, return a mock value
        return 0.15
    
    async def _calculate_volatility(self) -> float:
        """Calculate portfolio volatility."""
        # This would calculate actual volatility based on historical returns
        # For now, return a mock value
        return 0.18
    
    async def _calculate_beta(self) -> float:
        """Calculate portfolio beta."""
        # This would calculate actual beta against a benchmark
        # For now, return a mock value
        return 1.1
    
    async def _find_tax_loss_harvesting_opportunities(self, 
                                                    positions: List[Position]) -> List[Dict[str, Any]]:
        """Find tax loss harvesting opportunities."""
        opportunities = []
        
        for position in positions:
            if position.unrealized_pnl < 0:  # Position at a loss
                # Check if it's been held for more than 30 days (wash sale rule)
                # This is a simplified check - would need actual transaction history
                opportunities.append({
                    'symbol': position.symbol,
                    'unrealized_loss': float(position.unrealized_pnl),
                    'quantity': float(position.quantity),
                    'current_price': float(position.current_price),
                    'suggested_action': 'Consider selling for tax loss harvesting',
                    'estimated_tax_savings': float(abs(position.unrealized_pnl) * self.tax_settings['short_term_rate'])
                })
        
        return opportunities 