#!/usr/bin/env python3
"""
Enhanced Portfolio Management Example

Demonstrates comprehensive portfolio management features including:
- Transaction tracking and management
- P&L calculation and performance analysis
- Portfolio rebalancing suggestions
- Tax optimization calculations
- Interactive dashboard

This example shows how to use the enhanced portfolio management system
for real-world portfolio tracking and optimization.
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
from decimal import Decimal
import json

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.utils.config import Config
from src.utils.database import DatabaseManager
from src.utils.cache import CacheManager
from src.analytics.analytics_engine import AnalyticsEngine
from src.portfolio.portfolio_manager import (
    PortfolioManager, Transaction, TransactionType, Position, 
    PerformanceMetrics, RebalancingSuggestion, TaxOptimization
)
from src.portfolio.portfolio_api import set_portfolio_manager
from src.portfolio.portfolio_dashboard import PortfolioDashboard
from src.utils.logger import get_logger

logger = get_logger(__name__)


class PortfolioExample:
    """Example class demonstrating portfolio management features."""
    
    def __init__(self):
        self.config = None
        self.db_manager = None
        self.cache_manager = None
        self.analytics_engine = None
        self.portfolio_manager = None
        self.dashboard = None
    
    async def initialize(self):
        """Initialize all components."""
        try:
            logger.info("Initializing portfolio management example...")
            
            # Load configuration
            self.config = Config()
            
            # Initialize database manager
            self.db_manager = DatabaseManager(self.config.database_url)
            await self.db_manager.initialize()
            
            # Initialize cache manager
            self.cache_manager = CacheManager(self.config.redis_url)
            await self.cache_manager.initialize()
            
            # Initialize analytics engine
            self.analytics_engine = AnalyticsEngine(self.db_manager, self.cache_manager)
            
            # Initialize portfolio manager
            self.portfolio_manager = PortfolioManager(
                self.db_manager,
                self.cache_manager,
                self.analytics_engine
            )
            
            # Set portfolio manager for API
            set_portfolio_manager(self.portfolio_manager)
            
            # Initialize dashboard
            self.dashboard = PortfolioDashboard(self.portfolio_manager)
            
            logger.info("Portfolio management example initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing portfolio example: {e}")
            raise
    
    async def create_sample_transactions(self):
        """Create sample transactions for demonstration."""
        try:
            logger.info("Creating sample transactions...")
            
            # Sample transaction data
            sample_transactions = [
                {
                    "symbol": "AAPL",
                    "transaction_type": TransactionType.BUY,
                    "quantity": Decimal('100'),
                    "price": Decimal('150.00'),
                    "commission": Decimal('9.99'),
                    "timestamp": datetime.now() - timedelta(days=30),
                    "notes": "Initial purchase"
                },
                {
                    "symbol": "GOOGL",
                    "transaction_type": TransactionType.BUY,
                    "quantity": Decimal('50'),
                    "price": Decimal('2800.00'),
                    "commission": Decimal('9.99'),
                    "timestamp": datetime.now() - timedelta(days=25),
                    "notes": "Initial purchase"
                },
                {
                    "symbol": "MSFT",
                    "transaction_type": TransactionType.BUY,
                    "quantity": Decimal('75'),
                    "price": Decimal('300.00'),
                    "commission": Decimal('9.99'),
                    "timestamp": datetime.now() - timedelta(days=20),
                    "notes": "Initial purchase"
                },
                {
                    "symbol": "TSLA",
                    "transaction_type": TransactionType.BUY,
                    "quantity": Decimal('25'),
                    "price": Decimal('800.00'),
                    "commission": Decimal('9.99'),
                    "timestamp": datetime.now() - timedelta(days=15),
                    "notes": "Initial purchase"
                },
                {
                    "symbol": "AMZN",
                    "transaction_type": TransactionType.BUY,
                    "quantity": Decimal('30'),
                    "price": Decimal('3300.00'),
                    "commission": Decimal('9.99'),
                    "timestamp": datetime.now() - timedelta(days=10),
                    "notes": "Initial purchase"
                },
                {
                    "symbol": "AAPL",
                    "transaction_type": TransactionType.BUY,
                    "quantity": Decimal('50'),
                    "price": Decimal('155.00'),
                    "commission": Decimal('9.99'),
                    "timestamp": datetime.now() - timedelta(days=5),
                    "notes": "Additional purchase"
                },
                {
                    "symbol": "GOOGL",
                    "transaction_type": TransactionType.SELL,
                    "quantity": Decimal('10'),
                    "price": Decimal('2850.00'),
                    "commission": Decimal('9.99'),
                    "timestamp": datetime.now() - timedelta(days=2),
                    "notes": "Partial sale for profit taking"
                }
            ]
            
            # Add transactions
            for tx_data in sample_transactions:
                transaction = Transaction(**tx_data)
                transaction_id = await self.portfolio_manager.add_transaction(transaction)
                logger.info(f"Added transaction {transaction_id} for {transaction.symbol}")
            
            logger.info(f"Created {len(sample_transactions)} sample transactions")
            
        except Exception as e:
            logger.error(f"Error creating sample transactions: {e}")
            raise
    
    async def demonstrate_transaction_management(self):
        """Demonstrate transaction management features."""
        try:
            logger.info("\n=== Transaction Management Demo ===")
            
            # Get all transactions
            transactions = await self.portfolio_manager.get_transactions()
            logger.info(f"Total transactions: {len(transactions)}")
            
            # Get transactions for specific symbol
            aapl_transactions = await self.portfolio_manager.get_transactions(symbol="AAPL")
            logger.info(f"AAPL transactions: {len(aapl_transactions)}")
            
            # Get recent transactions
            recent_transactions = await self.portfolio_manager.get_transactions(limit=5)
            logger.info("Recent transactions:")
            for tx in recent_transactions:
                logger.info(f"  {tx.timestamp.strftime('%Y-%m-%d')}: {tx.symbol} {tx.transaction_type.value} {tx.quantity} @ ${tx.price}")
            
            # Add a new transaction
            new_transaction = Transaction(
                symbol="NVDA",
                transaction_type=TransactionType.BUY,
                quantity=Decimal('40'),
                price=Decimal('200.00'),
                commission=Decimal('9.99'),
                notes="New position in NVIDIA"
            )
            transaction_id = await self.portfolio_manager.add_transaction(new_transaction)
            logger.info(f"Added new transaction {transaction_id} for NVDA")
            
        except Exception as e:
            logger.error(f"Error in transaction management demo: {e}")
    
    async def demonstrate_position_tracking(self):
        """Demonstrate position tracking features."""
        try:
            logger.info("\n=== Position Tracking Demo ===")
            
            # Get current positions
            positions = await self.portfolio_manager.get_positions()
            logger.info(f"Current positions: {len(positions)}")
            
            # Display position details
            total_value = Decimal('0')
            total_pnl = Decimal('0')
            
            for position in positions:
                logger.info(f"\n{position.symbol}:")
                logger.info(f"  Quantity: {position.quantity:,.0f}")
                logger.info(f"  Average Cost: ${position.average_cost:,.2f}")
                logger.info(f"  Current Price: ${position.current_price:,.2f}")
                logger.info(f"  Market Value: ${position.market_value:,.2f}")
                logger.info(f"  Unrealized P&L: ${position.unrealized_pnl:,.2f}")
                logger.info(f"  Realized P&L: ${position.realized_pnl:,.2f}")
                logger.info(f"  Total P&L: ${position.total_pnl:,.2f}")
                
                total_value += position.market_value
                total_pnl += position.total_pnl
            
            logger.info(f"\nPortfolio Summary:")
            logger.info(f"  Total Market Value: ${total_value:,.2f}")
            logger.info(f"  Total P&L: ${total_pnl:,.2f}")
            
        except Exception as e:
            logger.error(f"Error in position tracking demo: {e}")
    
    async def demonstrate_performance_analysis(self):
        """Demonstrate performance analysis features."""
        try:
            logger.info("\n=== Performance Analysis Demo ===")
            
            # Get performance metrics
            performance = await self.portfolio_manager.get_performance_metrics()
            
            logger.info("Performance Metrics:")
            logger.info(f"  Total Value: ${performance.total_value:,.2f}")
            logger.info(f"  Total Cost: ${performance.total_cost:,.2f}")
            logger.info(f"  Total P&L: ${performance.total_pnl:,.2f}")
            logger.info(f"  Total Return: {performance.total_return_percent:+.2f}%")
            logger.info(f"  Daily P&L: ${performance.daily_pnl:,.2f} ({performance.daily_return_percent:+.2f}%)")
            logger.info(f"  Weekly P&L: ${performance.weekly_pnl:,.2f} ({performance.weekly_return_percent:+.2f}%)")
            logger.info(f"  Monthly P&L: ${performance.monthly_pnl:,.2f} ({performance.monthly_return_percent:+.2f}%)")
            logger.info(f"  Sharpe Ratio: {performance.sharpe_ratio:.2f}")
            logger.info(f"  Max Drawdown: {performance.max_drawdown:.2f}%")
            logger.info(f"  Volatility: {performance.volatility:.2f}")
            logger.info(f"  Beta: {performance.beta:.2f}")
            
        except Exception as e:
            logger.error(f"Error in performance analysis demo: {e}")
    
    async def demonstrate_rebalancing_suggestions(self):
        """Demonstrate rebalancing suggestions."""
        try:
            logger.info("\n=== Rebalancing Suggestions Demo ===")
            
            # Get rebalancing suggestions
            suggestions = await self.portfolio_manager.get_rebalancing_suggestions(tolerance=0.05)
            
            if not suggestions:
                logger.info("No rebalancing suggestions - portfolio is well balanced")
            else:
                logger.info(f"Found {len(suggestions)} rebalancing suggestions:")
                
                for suggestion in suggestions:
                    logger.info(f"\n{suggestion.symbol}:")
                    logger.info(f"  Current Allocation: {suggestion.current_allocation:.1%}")
                    logger.info(f"  Target Allocation: {suggestion.target_allocation:.1%}")
                    logger.info(f"  Suggested Action: {suggestion.suggested_action}")
                    logger.info(f"  Suggested Quantity: {suggestion.suggested_quantity:,.0f}")
                    logger.info(f"  Suggested Value: ${suggestion.suggested_value:,.2f}")
                    logger.info(f"  Priority: {suggestion.priority}")
            
            # Update target allocations
            logger.info("\nUpdating target allocations...")
            new_allocations = {
                'AAPL': 0.20,
                'GOOGL': 0.15,
                'MSFT': 0.15,
                'TSLA': 0.10,
                'AMZN': 0.10,
                'NVDA': 0.10,
                'META': 0.08,
                'NFLX': 0.05,
                'PYPL': 0.04,
                'ADBE': 0.03
            }
            
            # This would normally be done via API, but for demo we'll update directly
            self.portfolio_manager.target_allocations = new_allocations
            logger.info("Target allocations updated")
            
            # Get new suggestions
            new_suggestions = await self.portfolio_manager.get_rebalancing_suggestions(tolerance=0.05)
            logger.info(f"New rebalancing suggestions: {len(new_suggestions)}")
            
        except Exception as e:
            logger.error(f"Error in rebalancing suggestions demo: {e}")
    
    async def demonstrate_tax_optimization(self):
        """Demonstrate tax optimization features."""
        try:
            logger.info("\n=== Tax Optimization Demo ===")
            
            # Get tax optimization data
            tax_opt = await self.portfolio_manager.get_tax_optimization()
            
            logger.info("Tax Summary:")
            logger.info(f"  Short-term Gains: ${tax_opt.short_term_gains:,.2f}")
            logger.info(f"  Long-term Gains: ${tax_opt.long_term_gains:,.2f}")
            logger.info(f"  Short-term Losses: ${tax_opt.short_term_losses:,.2f}")
            logger.info(f"  Long-term Losses: ${tax_opt.long_term_losses:,.2f}")
            logger.info(f"  Net Capital Gains: ${tax_opt.net_capital_gains:,.2f}")
            logger.info(f"  Estimated Tax Liability: ${tax_opt.tax_liability:,.2f}")
            logger.info(f"  Effective Tax Rate: {tax_opt.tax_rate:.2%}")
            
            # Tax loss harvesting opportunities
            if tax_opt.harvesting_opportunities:
                logger.info(f"\nTax Loss Harvesting Opportunities ({len(tax_opt.harvesting_opportunities)}):")
                for opp in tax_opt.harvesting_opportunities:
                    logger.info(f"  {opp['symbol']}: ${opp['unrealized_loss']:,.2f} loss, "
                              f"${opp['estimated_tax_savings']:,.2f} potential savings")
            else:
                logger.info("No tax loss harvesting opportunities available")
            
            # Update tax settings
            logger.info("\nUpdating tax settings...")
            self.portfolio_manager.tax_settings.update({
                'short_term_rate': 0.24,  # Updated rate
                'long_term_rate': 0.15,   # Same rate
                'wash_sale_window': 30    # Same window
            })
            logger.info("Tax settings updated")
            
        except Exception as e:
            logger.error(f"Error in tax optimization demo: {e}")
    
    async def demonstrate_portfolio_summary(self):
        """Demonstrate portfolio summary features."""
        try:
            logger.info("\n=== Portfolio Summary Demo ===")
            
            # Get portfolio summary (this would normally come from API)
            positions = await self.portfolio_manager.get_positions()
            transactions = await self.portfolio_manager.get_transactions(limit=10)
            performance = await self.portfolio_manager.get_performance_metrics()
            
            # Calculate summary metrics
            total_positions = len(positions)
            total_value = performance.total_value
            total_pnl = performance.total_pnl
            total_return_percent = performance.total_return_percent
            
            # Get top gainers and losers
            sorted_positions = sorted(positions, key=lambda p: p.total_pnl, reverse=True)
            top_gainers = [pos for pos in sorted_positions[:3] if pos.total_pnl > 0]
            top_losers = [pos for pos in sorted_positions[-3:] if pos.total_pnl < 0]
            
            logger.info("Portfolio Summary:")
            logger.info(f"  Total Positions: {total_positions}")
            logger.info(f"  Total Value: ${total_value:,.2f}")
            logger.info(f"  Total P&L: ${total_pnl:,.2f} ({total_return_percent:+.2f}%)")
            
            if top_gainers:
                logger.info("  Top Gainers:")
                for pos in top_gainers:
                    return_pct = (pos.total_pnl / pos.cost_basis * 100) if pos.cost_basis > 0 else 0
                    logger.info(f"    {pos.symbol}: ${pos.total_pnl:,.2f} ({return_pct:+.2f}%)")
            
            if top_losers:
                logger.info("  Top Losers:")
                for pos in top_losers:
                    return_pct = (pos.total_pnl / pos.cost_basis * 100) if pos.cost_basis > 0 else 0
                    logger.info(f"    {pos.symbol}: ${pos.total_pnl:,.2f} ({return_pct:+.2f}%)")
            
            logger.info(f"  Recent Transactions: {len(transactions)}")
            
        except Exception as e:
            logger.error(f"Error in portfolio summary demo: {e}")
    
    async def run_dashboard(self):
        """Run the portfolio dashboard."""
        try:
            logger.info("\n=== Starting Portfolio Dashboard ===")
            logger.info("Dashboard will be available at: http://localhost:8050")
            logger.info("Press Ctrl+C to stop the dashboard")
            
            # Run dashboard
            self.dashboard.run(host="0.0.0.0", port=8050, debug=False)
            
        except KeyboardInterrupt:
            logger.info("Dashboard stopped by user")
        except Exception as e:
            logger.error(f"Error running dashboard: {e}")
    
    async def run_comprehensive_demo(self):
        """Run a comprehensive demonstration of all features."""
        try:
            logger.info("Starting comprehensive portfolio management demo...")
            
            # Initialize components
            await self.initialize()
            
            # Create sample data
            await self.create_sample_transactions()
            
            # Run demonstrations
            await self.demonstrate_transaction_management()
            await self.demonstrate_position_tracking()
            await self.demonstrate_performance_analysis()
            await self.demonstrate_rebalancing_suggestions()
            await self.demonstrate_tax_optimization()
            await self.demonstrate_portfolio_summary()
            
            logger.info("\n=== Demo Complete ===")
            logger.info("All portfolio management features demonstrated successfully!")
            
            # Ask user if they want to run the dashboard
            response = input("\nWould you like to start the portfolio dashboard? (y/n): ")
            if response.lower() in ['y', 'yes']:
                await self.run_dashboard()
            
        except Exception as e:
            logger.error(f"Error in comprehensive demo: {e}")
            raise
        finally:
            # Cleanup
            if self.cache_manager:
                await self.cache_manager.close()
            if self.db_manager:
                await self.db_manager.close()


async def main():
    """Main function to run the portfolio example."""
    try:
        example = PortfolioExample()
        await example.run_comprehensive_demo()
        
    except KeyboardInterrupt:
        logger.info("Demo interrupted by user")
    except Exception as e:
        logger.error(f"Error running portfolio example: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Run the example
    asyncio.run(main()) 