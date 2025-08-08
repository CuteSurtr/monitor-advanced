# Stock Market Monitor - API Documentation

## Overview

This document provides comprehensive documentation for the Stock Market Monitor API. The API provides real-time access to market data, portfolio management, analytics, and alerting functionality.

## Base URL

```
http://localhost:8080/api/v1
```

## Authentication

The API uses JWT token-based authentication. Include the token in the Authorization header:

```
Authorization: Bearer <your_jwt_token>
```

## API Endpoints

### 1. Authentication

#### POST /auth/login
Login and obtain access token.

**Request Body:**
```json
{
  "username": "string",
  "password": "string"
}
```

**Response:**
```json
{
  "access_token": "string",
  "token_type": "bearer",
  "expires_in": 3600
}
```

#### POST /auth/refresh
Refresh access token.

**Request Body:**
```json
{
  "refresh_token": "string"
}
```

### 2. Market Data

#### GET /market/stocks
Get list of available stocks.

**Query Parameters:**
- `exchange` (optional): Filter by exchange (NYSE, NASDAQ, etc.)
- `sector` (optional): Filter by sector
- `limit` (optional): Number of results (default: 100)
- `offset` (optional): Pagination offset

**Response:**
```json
{
  "stocks": [
    {
      "id": 1,
      "symbol": "AAPL",
      "company_name": "Apple Inc.",
      "exchange": "NASDAQ",
      "sector": "Technology",
      "market_cap": 2800000000000,
      "currency": "USD"
    }
  ],
  "total": 1000,
  "limit": 100,
  "offset": 0
}
```

#### GET /market/stocks/{symbol}/price
Get current price for a specific stock.

**Path Parameters:**
- `symbol`: Stock symbol (e.g., AAPL)

**Response:**
```json
{
  "symbol": "AAPL",
  "current_price": 155.50,
  "change": 2.30,
  "change_percent": 1.50,
  "volume": 45000000,
  "timestamp": "2024-01-15T14:30:00Z"
}
```

#### GET /market/stocks/{symbol}/history
Get historical price data.

**Path Parameters:**
- `symbol`: Stock symbol

**Query Parameters:**
- `period`: Time period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, max)
- `interval`: Data interval (1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo)

**Response:**
```json
{
  "symbol": "AAPL",
  "history": [
    {
      "timestamp": "2024-01-15T09:30:00Z",
      "open": 153.20,
      "high": 156.80,
      "low": 152.90,
      "close": 155.50,
      "volume": 2500000
    }
  ]
}
```

#### GET /market/stocks/{symbol}/indicators
Get technical indicators for a stock.

**Path Parameters:**
- `symbol`: Stock symbol

**Query Parameters:**
- `indicators`: Comma-separated list (rsi,macd,bb,sma_20,ema_12)
- `period`: Time period for calculation

**Response:**
```json
{
  "symbol": "AAPL",
  "indicators": {
    "rsi": {
      "value": 65.5,
      "signal": "neutral",
      "timestamp": "2024-01-15T14:30:00Z"
    },
    "macd": {
      "macd": 1.25,
      "signal": 1.10,
      "histogram": 0.15,
      "timestamp": "2024-01-15T14:30:00Z"
    }
  }
}
```

### 3. Portfolio Management

#### GET /portfolio/portfolios
Get list of portfolios.

**Response:**
```json
{
  "portfolios": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "name": "Growth Portfolio",
      "description": "Long-term growth focused portfolio",
      "currency": "USD",
      "current_value": 155500.75,
      "total_return": 55500.75,
      "total_return_percent": 55.50,
      "created_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

#### POST /portfolio/portfolios
Create a new portfolio.

**Request Body:**
```json
{
  "name": "string",
  "description": "string",
  "currency": "USD",
  "initial_value": 100000.00,
  "risk_tolerance": "moderate"
}
```

**Response:**
```json
{
  "success": true,
  "portfolio": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "name": "string",
    "description": "string",
    "currency": "USD",
    "initial_value": 100000.00,
    "current_value": 100000.00,
    "created_at": "2024-01-15T14:30:00Z"
  }
}
```

#### GET /portfolio/portfolios/{portfolio_id}
Get specific portfolio details.

**Path Parameters:**
- `portfolio_id`: Portfolio UUID

**Response:**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "name": "Growth Portfolio",
  "description": "Long-term growth focused portfolio",
  "currency": "USD",
  "initial_value": 100000.00,
  "current_value": 155500.75,
  "cash_balance": 5500.75,
  "total_return": 55500.75,
  "total_return_percent": 55.50,
  "positions": [
    {
      "id": "position-uuid",
      "symbol": "AAPL",
      "quantity": 100,
      "average_cost": 150.00,
      "current_price": 155.50,
      "market_value": 15550.00,
      "unrealized_pnl": 550.00,
      "unrealized_pnl_percent": 3.67
    }
  ],
  "performance": {
    "daily_return": 125.50,
    "daily_return_percent": 0.81,
    "volatility": 18.5,
    "sharpe_ratio": 1.25,
    "max_drawdown": -8.2
  }
}
```

#### POST /portfolio/portfolios/{portfolio_id}/positions
Add position to portfolio.

**Path Parameters:**
- `portfolio_id`: Portfolio UUID

**Request Body:**
```json
{
  "symbol": "AAPL",
  "quantity": 100,
  "price": 155.50,
  "transaction_type": "BUY"
}
```

#### GET /portfolio/portfolios/{portfolio_id}/performance
Get portfolio performance metrics.

**Path Parameters:**
- `portfolio_id`: Portfolio UUID

**Query Parameters:**
- `period`: Performance period (1d, 1w, 1m, 3m, 6m, 1y, ytd, all)

**Response:**
```json
{
  "portfolio_id": "123e4567-e89b-12d3-a456-426614174000",
  "period": "1m",
  "performance": [
    {
      "date": "2024-01-15",
      "value": 155500.75,
      "return": 125.50,
      "return_percent": 0.81
    }
  ],
  "metrics": {
    "total_return": 55500.75,
    "total_return_percent": 55.50,
    "volatility": 18.5,
    "sharpe_ratio": 1.25,
    "max_drawdown": -8.2,
    "var_95": -2850.75,
    "beta": 1.05
  }
}
```

### 4. Analytics

#### GET /analytics/predictions/{symbol}
Get ML predictions for a stock.

**Path Parameters:**
- `symbol`: Stock symbol

**Query Parameters:**
- `models`: Comma-separated list of models (lstm,random_forest,xgboost)
- `horizon`: Prediction horizon in minutes (default: 60)

**Response:**
```json
{
  "symbol": "AAPL",
  "predictions": [
    {
      "model": "lstm",
      "predicted_price": 157.25,
      "confidence": 0.85,
      "horizon_minutes": 60,
      "prediction_date": "2024-01-15T14:30:00Z",
      "target_date": "2024-01-15T15:30:00Z"
    }
  ]
}
```

#### GET /analytics/anomalies
Get detected anomalies.

**Query Parameters:**
- `symbol` (optional): Filter by symbol
- `severity` (optional): Filter by severity (LOW, MEDIUM, HIGH)
- `hours_back` (optional): Hours to look back (default: 24)

**Response:**
```json
{
  "anomalies": [
    {
      "id": "anomaly-uuid",
      "symbol": "AAPL",
      "anomaly_type": "price_spike",
      "severity": "HIGH",
      "anomaly_score": 0.95,
      "detected_at": "2024-01-15T14:25:00Z",
      "description": "Unusual price movement detected"
    }
  ]
}
```

#### GET /analytics/sentiment/{symbol}
Get sentiment analysis for a stock.

**Path Parameters:**
- `symbol`: Stock symbol

**Response:**
```json
{
  "symbol": "AAPL",
  "sentiment": {
    "overall_score": 0.65,
    "sentiment_label": "positive",
    "confidence": 0.82,
    "sources": {
      "news": {
        "score": 0.70,
        "article_count": 25
      },
      "social_media": {
        "score": 0.60,
        "mention_count": 150
      }
    },
    "last_updated": "2024-01-15T14:30:00Z"
  }
}
```

### 5. Alerts

#### GET /alerts/rules
Get alert rules.

**Query Parameters:**
- `active_only` (optional): Filter active rules only (default: true)
- `alert_type` (optional): Filter by alert type

**Response:**
```json
{
  "alert_rules": [
    {
      "id": "rule-uuid",
      "name": "Price Drop Alert",
      "description": "Alert when stock drops more than 5%",
      "alert_type": "price_change",
      "conditions": {
        "field": "price_change_percent",
        "operator": "less_than",
        "value": -5.0
      },
      "is_active": true,
      "created_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

#### POST /alerts/rules
Create new alert rule.

**Request Body:**
```json
{
  "name": "string",
  "description": "string",
  "alert_type": "price_change|volume_spike|technical_indicator",
  "conditions": {
    "field": "string",
    "operator": "greater_than|less_than|equals",
    "value": 0.0
  },
  "thresholds": {
    "value": 0.0,
    "timeframe": "5m"
  },
  "notification_channels": ["email", "dashboard"]
}
```

#### GET /alerts/instances
Get alert instances.

**Query Parameters:**
- `status` (optional): Filter by status (ACTIVE, RESOLVED, ACKNOWLEDGED)
- `severity` (optional): Filter by severity
- `symbol` (optional): Filter by symbol
- `limit` (optional): Number of results
- `offset` (optional): Pagination offset

**Response:**
```json
{
  "alerts": [
    {
      "id": "alert-uuid",
      "rule_id": "rule-uuid",
      "symbol": "AAPL",
      "severity": "HIGH",
      "title": "AAPL Price Drop Alert",
      "message": "AAPL has dropped by 6.2%",
      "status": "ACTIVE",
      "triggered_at": "2024-01-15T14:25:00Z",
      "data": {
        "current_price": 145.50,
        "change_percent": -6.2
      }
    }
  ]
}
```

#### POST /alerts/instances/{alert_id}/acknowledge
Acknowledge an alert.

**Path Parameters:**
- `alert_id`: Alert UUID

**Request Body:**
```json
{
  "acknowledged_by": "string",
  "notes": "string"
}
```

### 6. Monitoring

#### GET /monitoring/health
Get system health status.

**Response:**
```json
{
  "overall_status": "healthy",
  "timestamp": "2024-01-15T14:30:00Z",
  "components": {
    "database": {
      "status": "healthy",
      "response_time_ms": 5.2
    },
    "cache": {
      "status": "healthy",
      "hit_rate": 95.5
    },
    "external_apis": {
      "status": "degraded",
      "available_providers": 3,
      "total_providers": 4
    }
  }
}
```

#### GET /monitoring/metrics
Get system metrics.

**Query Parameters:**
- `metric_names`: Comma-separated list of metrics
- `time_range`: Time range (1h, 6h, 24h, 7d)

**Response:**
```json
{
  "metrics": [
    {
      "name": "api_requests_per_second",
      "values": [
        {
          "timestamp": "2024-01-15T14:30:00Z",
          "value": 125.5
        }
      ]
    }
  ]
}
```

### 7. Reports

#### GET /reports/portfolio/{portfolio_id}/summary
Generate portfolio summary report.

**Path Parameters:**
- `portfolio_id`: Portfolio UUID

**Query Parameters:**
- `period`: Report period (daily, weekly, monthly, quarterly, yearly)
- `format`: Report format (json, pdf, excel)

**Response:**
```json
{
  "report_id": "report-uuid",
  "portfolio_id": "portfolio-uuid",
  "period": "monthly",
  "generated_at": "2024-01-15T14:30:00Z",
  "summary": {
    "starting_value": 100000.00,
    "ending_value": 155500.75,
    "total_return": 55500.75,
    "total_return_percent": 55.50,
    "best_performer": {
      "symbol": "AAPL",
      "return_percent": 25.5
    },
    "worst_performer": {
      "symbol": "GE",
      "return_percent": -8.2
    }
  }
}
```

## Error Responses

All API endpoints return consistent error responses:

```json
{
  "error": {
    "code": "INVALID_REQUEST",
    "message": "Detailed error message",
    "details": {
      "field": "specific field error"
    }
  },
  "timestamp": "2024-01-15T14:30:00Z",
  "request_id": "req-uuid"
}
```

### Common Error Codes

- `INVALID_REQUEST` (400): Invalid request parameters
- `UNAUTHORIZED` (401): Authentication required
- `FORBIDDEN` (403): Insufficient permissions
- `NOT_FOUND` (404): Resource not found
- `RATE_LIMITED` (429): Rate limit exceeded
- `INTERNAL_ERROR` (500): Internal server error

## Rate Limiting

API requests are rate limited:
- **Regular endpoints**: 100 requests per minute
- **Market data endpoints**: 200 requests per minute
- **Analytics endpoints**: 50 requests per minute

Rate limit headers are included in responses:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1642258800
```

## WebSocket API

For real-time data, use WebSocket connections:

### Connection
```
ws://localhost:8080/ws
```

### Subscribe to Stock Prices
```json
{
  "action": "subscribe",
  "channel": "stock_prices",
  "symbols": ["AAPL", "GOOGL", "MSFT"]
}
```

### Subscribe to Portfolio Updates
```json
{
  "action": "subscribe",
  "channel": "portfolio_updates",
  "portfolio_id": "portfolio-uuid"
}
```

### Subscribe to Alerts
```json
{
  "action": "subscribe",
  "channel": "alerts",
  "severity": ["HIGH", "CRITICAL"]
}
```

## SDK Examples

### Python SDK
```python
from stock_monitor_sdk import StockMonitorClient

client = StockMonitorClient(api_key="your_api_key")

# Get stock price
price = client.get_stock_price("AAPL")

# Create portfolio
portfolio = client.create_portfolio(
    name="My Portfolio",
    initial_value=100000
)

# Add position
client.add_position(
    portfolio_id=portfolio.id,
    symbol="AAPL",
    quantity=100,
    price=155.50
)
```

### JavaScript SDK
```javascript
import { StockMonitorClient } from 'stock-monitor-sdk';

const client = new StockMonitorClient({ apiKey: 'your_api_key' });

// Get stock price
const price = await client.getStockPrice('AAPL');

// Create portfolio
const portfolio = await client.createPortfolio({
  name: 'My Portfolio',
  initialValue: 100000
});
```

## Changelog

### v1.0.0 (2024-01-15)
- Initial API release
- Core market data endpoints
- Portfolio management
- Basic analytics
- Alert system

### v1.1.0 (TBD)
- Enhanced analytics endpoints
- Machine learning predictions
- Advanced portfolio metrics
- Real-time WebSocket feeds

## Support

For API support and questions:
- Email: api-support@stockmonitor.com
- Documentation: https://docs.stockmonitor.com
- Status Page: https://status.stockmonitor.com