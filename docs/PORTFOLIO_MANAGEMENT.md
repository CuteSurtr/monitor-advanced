# Enhanced Portfolio Management System

## Overview

The Enhanced Portfolio Management System provides comprehensive portfolio tracking, P&L calculation, performance analysis, rebalancing suggestions, and tax optimization capabilities. It's designed to handle real-world portfolio management needs with advanced features for professional and individual investors.

## Features

### Core Features

1. **Transaction Tracking**
   - Buy/sell transaction recording
   - Dividend and corporate action tracking
   - Commission and fee management
   - Tax lot identification and management

2. **Position Management**
   - Real-time position calculation
   - Average cost basis tracking
   - Unrealized and realized P&L calculation
   - Market value and cost basis tracking

3. **Performance Analysis**
   - Total return calculation
   - Period-based performance metrics (daily, weekly, monthly)
   - Risk metrics (Sharpe ratio, volatility, beta, max drawdown)
   - Performance attribution analysis

4. **Portfolio Rebalancing**
   - Target allocation management
   - Rebalancing suggestions with priority levels
   - Tolerance-based rebalancing triggers
   - Buy/sell recommendations

5. **Tax Optimization**
   - Short-term vs long-term gain/loss tracking
   - Tax liability calculation
   - Tax loss harvesting opportunities
   - Wash sale rule compliance

6. **Interactive Dashboard**
   - Real-time portfolio visualization
   - Interactive charts and graphs
   - Performance tracking
   - Rebalancing and tax optimization views

## Architecture

### Components

```
Portfolio Management System
├── PortfolioManager (Core Business Logic)
├── PortfolioAPI (FastAPI Endpoints)
├── PortfolioDashboard (Dash Web Interface)
└── Database Layer (PostgreSQL + Redis Cache)
```

### Data Models

#### Transaction
```python
@dataclass
class Transaction:
    id: Optional[int]
    symbol: str
    transaction_type: TransactionType  # BUY, SELL, DIVIDEND, SPLIT, MERGE
    quantity: Decimal
    price: Decimal
    commission: Decimal
    timestamp: datetime
    tax_lot_id: Optional[str]
    notes: str
```

#### Position
```python
@dataclass
class Position:
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
```

#### PerformanceMetrics
```python
@dataclass
class PerformanceMetrics:
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
```

## API Reference

### Base URL
```
/api/portfolio
```

### Transaction Endpoints

#### Create Transaction
```http
POST /api/portfolio/transactions
```

**Request Body:**
```json
{
    "symbol": "AAPL",
    "transaction_type": "buy",
    "quantity": 100.0,
    "price": 150.00,
    "commission": 9.99,
    "timestamp": "2024-01-15T10:30:00Z",
    "tax_lot_id": "AAPL_20240115_103000",
    "notes": "Initial purchase"
}
```

**Response:**
```json
{
    "message": "Transaction created successfully",
    "transaction_id": 123,
    "transaction": {
        "id": 123,
        "symbol": "AAPL",
        "transaction_type": "buy",
        "quantity": 100.0,
        "price": 150.00,
        "commission": 9.99,
        "timestamp": "2024-01-15T10:30:00Z",
        "tax_lot_id": "AAPL_20240115_103000",
        "notes": "Initial purchase"
    }
}
```

#### Get Transactions
```http
GET /api/portfolio/transactions?symbol=AAPL&limit=100
```

**Query Parameters:**
- `symbol` (optional): Filter by symbol
- `start_date` (optional): Filter by start date
- `end_date` (optional): Filter by end date
- `limit` (optional): Maximum number of transactions (default: 100, max: 1000)

### Position Endpoints

#### Get All Positions
```http
GET /api/portfolio/positions
```

**Response:**
```json
[
    {
        "symbol": "AAPL",
        "quantity": 150.0,
        "average_cost": 152.50,
        "current_price": 155.00,
        "market_value": 23250.00,
        "unrealized_pnl": 375.00,
        "realized_pnl": 0.00,
        "total_pnl": 375.00,
        "cost_basis": 22875.00,
        "last_updated": "2024-01-15T15:30:00Z"
    }
]
```

#### Get Specific Position
```http
GET /api/portfolio/positions/{symbol}
```

### Performance Endpoints

#### Get Performance Metrics
```http
GET /api/portfolio/performance?period=all
```

**Query Parameters:**
- `period` (optional): Performance period ("all", "1d", "1w", "1m", "3m", "6m", "1y")

**Response:**
```json
{
    "total_value": 150000.00,
    "total_cost": 145000.00,
    "total_pnl": 5000.00,
    "total_return_percent": 3.45,
    "daily_pnl": 250.00,
    "daily_return_percent": 0.17,
    "weekly_pnl": 1200.00,
    "weekly_return_percent": 0.80,
    "monthly_pnl": 3500.00,
    "monthly_return_percent": 2.41,
    "sharpe_ratio": 1.25,
    "max_drawdown": 8.50,
    "volatility": 0.18,
    "beta": 1.10
}
```

### Rebalancing Endpoints

#### Get Rebalancing Suggestions
```http
GET /api/portfolio/rebalancing?tolerance=0.05
```

**Query Parameters:**
- `tolerance` (optional): Rebalancing tolerance (default: 0.05, range: 0.01-0.20)

**Response:**
```json
[
    {
        "symbol": "AAPL",
        "current_allocation": 0.18,
        "target_allocation": 0.15,
        "suggested_action": "sell",
        "suggested_quantity": 20.0,
        "suggested_value": 3100.00,
        "priority": "medium"
    }
]
```

### Tax Optimization Endpoints

#### Get Tax Optimization Data
```http
GET /api/portfolio/tax-optimization
```

**Response:**
```json
{
    "short_term_gains": 2500.00,
    "long_term_gains": 1500.00,
    "short_term_losses": 500.00,
    "long_term_losses": 0.00,
    "net_capital_gains": 3500.00,
    "tax_liability": 550.00,
    "tax_rate": 0.157,
    "harvesting_opportunities": [
        {
            "symbol": "TSLA",
            "unrealized_loss": 1200.00,
            "quantity": 25.0,
            "current_price": 800.00,
            "suggested_action": "Consider selling for tax loss harvesting",
            "estimated_tax_savings": 264.00
        }
    ]
}
```

### Portfolio Summary Endpoint

#### Get Portfolio Summary
```http
GET /api/portfolio/summary
```

**Response:**
```json
{
    "total_positions": 8,
    "total_value": 150000.00,
    "total_pnl": 5000.00,
    "total_return_percent": 3.45,
    "top_gainers": [
        {
            "symbol": "AAPL",
            "pnl": 375.00,
            "return_percent": 1.64
        }
    ],
    "top_losers": [
        {
            "symbol": "TSLA",
            "pnl": -1200.00,
            "return_percent": -6.00
        }
    ],
    "recent_transactions": [...]
}
```

### Configuration Endpoints

#### Get Target Allocations
```http
GET /api/portfolio/target-allocations
```

#### Update Target Allocations
```http
PUT /api/portfolio/target-allocations
```

**Request Body:**
```json
{
    "AAPL": 0.15,
    "GOOGL": 0.12,
    "MSFT": 0.12,
    "TSLA": 0.10,
    "AMZN": 0.10,
    "META": 0.08,
    "NVDA": 0.08,
    "NFLX": 0.05,
    "PYPL": 0.05,
    "ADBE": 0.05,
    "CRM": 0.03,
    "ORCL": 0.02
}
```

#### Get Tax Settings
```http
GET /api/portfolio/tax-settings
```

#### Update Tax Settings
```http
PUT /api/portfolio/tax-settings?short_term_rate=0.22&long_term_rate=0.15&tax_lot_method=fifo&wash_sale_window=30
```

## Usage Examples

### Python API Usage

```python
import asyncio
from decimal import Decimal
from datetime import datetime
from src.portfolio.portfolio_manager import PortfolioManager, Transaction, TransactionType

async def portfolio_example():
    # Initialize portfolio manager
    portfolio_manager = PortfolioManager(db_manager, cache_manager, analytics_engine)
    
    # Add a transaction
    transaction = Transaction(
        symbol="AAPL",
        transaction_type=TransactionType.BUY,
        quantity=Decimal('100'),
        price=Decimal('150.00'),
        commission=Decimal('9.99'),
        notes="Initial purchase"
    )
    
    transaction_id = await portfolio_manager.add_transaction(transaction)
    print(f"Added transaction {transaction_id}")
    
    # Get positions
    positions = await portfolio_manager.get_positions()
    for position in positions:
        print(f"{position.symbol}: {position.quantity} shares, P&L: ${position.total_pnl}")
    
    # Get performance metrics
    performance = await portfolio_manager.get_performance_metrics()
    print(f"Total return: {performance.total_return_percent:.2f}%")
    
    # Get rebalancing suggestions
    suggestions = await portfolio_manager.get_rebalancing_suggestions()
    for suggestion in suggestions:
        print(f"Rebalance {suggestion.symbol}: {suggestion.suggested_action} {suggestion.suggested_quantity}")

# Run the example
asyncio.run(portfolio_example())
```

### REST API Usage

```bash
# Add a transaction
curl -X POST "http://localhost:8000/api/portfolio/transactions" \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "AAPL",
    "transaction_type": "buy",
    "quantity": 100.0,
    "price": 150.00,
    "commission": 9.99,
    "notes": "Initial purchase"
  }'

# Get positions
curl "http://localhost:8000/api/portfolio/positions"

# Get performance metrics
curl "http://localhost:8000/api/portfolio/performance"

# Get rebalancing suggestions
curl "http://localhost:8000/api/portfolio/rebalancing?tolerance=0.05"
```

## Configuration

### Target Allocations

Configure target portfolio allocations for rebalancing:

```python
target_allocations = {
    'AAPL': 0.15,    # 15% allocation
    'GOOGL': 0.12,   # 12% allocation
    'MSFT': 0.12,    # 12% allocation
    'TSLA': 0.10,    # 10% allocation
    'AMZN': 0.10,    # 10% allocation
    'META': 0.08,    # 8% allocation
    'NVDA': 0.08,    # 8% allocation
    'NFLX': 0.05,    # 5% allocation
    'PYPL': 0.05,    # 5% allocation
    'ADBE': 0.05,    # 5% allocation
    'CRM': 0.03,     # 3% allocation
    'ORCL': 0.02     # 2% allocation
}
```

### Tax Settings

Configure tax optimization parameters:

```python
tax_settings = {
    'short_term_rate': 0.22,      # 22% short-term capital gains rate
    'long_term_rate': 0.15,       # 15% long-term capital gains rate
    'tax_lot_method': 'fifo',     # FIFO tax lot identification
    'wash_sale_window': 30        # 30-day wash sale window
}
```

## Dashboard Features

### Overview Section
- Portfolio summary with key metrics
- Total value, P&L, and return percentages
- Daily, weekly, and monthly performance
- Risk metrics (Sharpe ratio, max drawdown)

### Positions Section
- Interactive pie chart showing portfolio allocation
- Detailed positions table with P&L information
- Top performers chart
- P&L distribution histogram

### Performance Section
- Performance metrics visualization
- Risk metrics charts
- Return analysis graphs

### Rebalancing Section
- Current vs target allocation comparison
- Rebalancing suggestions table
- Priority-based recommendations
- Interactive allocation charts

### Tax Optimization Section
- Tax summary with gains/losses breakdown
- Tax liability calculation
- Tax loss harvesting opportunities
- Interactive tax breakdown charts

### Transactions Section
- Recent transactions table
- Transaction history with filtering
- Transaction details and notes

## Performance Optimization

### Caching Strategy
- Redis caching for frequently accessed data
- Cache invalidation on data updates
- Configurable cache expiration times

### Database Optimization
- Efficient queries with proper indexing
- Connection pooling
- Asynchronous database operations

### Memory Management
- Decimal precision for financial calculations
- Efficient data structures
- Garbage collection optimization

## Security Considerations

### Data Validation
- Input validation for all API endpoints
- Decimal precision handling
- Date/time validation
- Symbol validation

### Access Control
- API authentication and authorization
- Rate limiting
- Input sanitization

### Data Integrity
- Transaction atomicity
- Database constraints
- Error handling and rollback

## Monitoring and Logging

### Logging
- Structured logging with different levels
- Performance metrics logging
- Error tracking and debugging

### Metrics
- API response times
- Database query performance
- Cache hit rates
- Error rates

### Health Checks
- Database connectivity
- Cache connectivity
- API endpoint availability

## Troubleshooting

### Common Issues

1. **Transaction Not Found**
   - Check transaction ID validity
   - Verify database connectivity
   - Check transaction filters

2. **Position Calculation Errors**
   - Verify transaction data integrity
   - Check for missing transactions
   - Validate price data

3. **Performance Calculation Issues**
   - Check historical data availability
   - Verify date ranges
   - Check for data gaps

4. **Rebalancing Suggestions Not Appearing**
   - Verify target allocations are set
   - Check tolerance settings
   - Ensure positions exist

### Debug Mode

Enable debug logging for troubleshooting:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Database Queries

Use database query logging to debug issues:

```python
# Enable SQL query logging
import logging
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
```

## Best Practices

### Transaction Management
- Always include commission/fees in transactions
- Use descriptive notes for transaction tracking
- Maintain consistent tax lot identification
- Regular transaction reconciliation

### Performance Monitoring
- Monitor portfolio performance regularly
- Set up alerts for significant changes
- Track rebalancing frequency
- Monitor tax optimization opportunities

### Data Management
- Regular data backups
- Validate data integrity
- Monitor storage usage
- Archive old transactions

### Security
- Use secure API authentication
- Implement rate limiting
- Regular security audits
- Keep dependencies updated

## Future Enhancements

### Planned Features
- Advanced portfolio optimization algorithms
- Machine learning-based rebalancing
- Integration with external brokers
- Real-time market data integration
- Advanced tax optimization strategies
- Portfolio backtesting capabilities
- Risk management tools
- Multi-currency support

### Performance Improvements
- Real-time data streaming
- Advanced caching strategies
- Database optimization
- Parallel processing for large portfolios

## Support and Documentation

### Additional Resources
- API documentation: `/docs` (Swagger UI)
- Example scripts: `examples/portfolio_example.py`
- Configuration guide: `docs/CONFIGURATION.md`
- Deployment guide: `docs/DEPLOYMENT.md`

### Getting Help
- Check the troubleshooting section
- Review example code
- Enable debug logging
- Contact support team

---

This documentation provides a comprehensive guide to the Enhanced Portfolio Management System. For specific implementation details, refer to the source code and API documentation. 