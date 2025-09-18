# Web Dashboard Documentation

## Overview

The Web Dashboard is a comprehensive, real-time interface for the 24/7 Global Stock Market Monitoring System. It provides interactive visualization of market data, portfolio performance, technical analysis, alerts, and analytics through a modern web interface.

## Features

### 🏠 **Dashboard Overview**
- **Market Overview**: Real-time market statistics and performance metrics
- **Key Metrics**: Total symbols, gainers/losers count, active alerts
- **Market Performance Chart**: Interactive time-series chart of market performance
- **Top Movers**: Real-time list of stocks with highest price movements

### 💼 **Portfolio Management**
- **Portfolio Summary**: Total value, P&L, and position counts
- **Portfolio Allocation**: Interactive pie chart showing asset allocation
- **Performance Tracking**: Historical portfolio performance over time
- **Real-time Updates**: Live portfolio value updates

### 📊 **Technical Analysis**
- **Interactive Charts**: Plotly-powered technical indicator charts
- **Multiple Indicators**: RSI, MACD, Bollinger Bands, Moving Averages
- **Symbol Selection**: Dropdown to select any available stock symbol
- **Period Selection**: Customizable analysis periods (1-365 days)

### 🔔 **Alerts Management**
- **Recent Alerts**: Real-time list of triggered alerts
- **Alert Statistics**: Total, active, and daily alert counts
- **Alert Details**: Symbol, message, timestamp, and severity
- **Alert Acknowledgment**: Mark alerts as read/acknowledged

### 🗺️ **Market Data**
- **Market Heatmap**: Visual representation of market performance
- **Sector Analysis**: Performance across different market sectors
- **Real-time Data**: Live price, volume, and change data
- **Historical Data**: Historical price and volume information

## Architecture

### Components

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Web Browser   │◄──►│  FastAPI Server  │◄──►│ Dashboard Mgr   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
                       ┌──────────────────┐    ┌─────────────────┐
                       │   API Routes     │    │ System Components│
                       └──────────────────┘    └─────────────────┘
                                                        │
                                ┌───────────────────────┼───────────────────────┐
                                ▼                       ▼                       ▼
                       ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
                       │ Database Mgr    │    │ Analytics Engine│    │ Alert Manager   │
                       └─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Key Components

1. **Dashboard API** (`src/dashboard/api.py`)
   - FastAPI routes for dashboard endpoints
   - HTML response serving for main dashboard page
   - RESTful API for data retrieval

2. **Dashboard Manager** (`src/dashboard/dashboard_manager.py`)
   - Core business logic for dashboard data
   - Integration with all system components
   - Caching and data aggregation

3. **Frontend Interface**
   - Bootstrap 5 for responsive design
   - Plotly.js for interactive charts
   - Vanilla JavaScript for dynamic updates

## API Endpoints

### Dashboard Routes

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/dashboard/` | GET | Main dashboard HTML page |
| `/api/dashboard/overview` | GET | Market overview data |
| `/api/dashboard/portfolio` | GET | Portfolio data |
| `/api/dashboard/symbols` | GET | Available stock symbols |
| `/api/dashboard/analytics/{symbol}` | GET | Technical analysis for symbol |
| `/api/dashboard/alerts` | GET | Alerts data |
| `/api/dashboard/market-heatmap` | GET | Market heatmap data |
| `/api/dashboard/real-time/{symbol}` | GET | Real-time data for symbol |

### Response Formats

#### Market Overview
```json
{
  "total_symbols": 150,
  "gainers": 85,
  "losers": 45,
  "unchanged": 20,
  "active_alerts": 12,
  "market_data": {
    "timestamps": ["2024-01-01T10:00:00", ...],
    "prices": [100.5, 101.2, ...]
  },
  "top_movers": [
    {
      "symbol": "AAPL",
      "change_percent": 5.2
    }
  ]
}
```

#### Portfolio Data
```json
{
  "summary": {
    "total_value": 125000.50,
    "total_pnl": 8750.25,
    "total_pnl_percent": 7.5,
    "positions_count": 8
  },
  "allocations": {
    "labels": ["AAPL", "GOOGL", "MSFT"],
    "values": [30, 25, 20]
  },
  "performance": {
    "timestamps": ["2024-01-01", ...],
    "values": [116250, 117000, ...]
  }
}
```

#### Technical Analysis
```json
{
  "symbol": "AAPL",
  "indicator": "rsi",
  "timestamps": ["2024-01-01", ...],
  "values": [65.2, 67.8, ...],
  "signals": {
    "current": "NEUTRAL",
    "trend": "SIDEWAYS"
  }
}
```

## Usage

### Starting the Dashboard

1. **Start the main application**:
   ```bash
   python src/main.py
   ```

2. **Access the dashboard**:
   ```
   http://localhost:8000/api/dashboard/
   ```

3. **Navigate through sections**:
   - Click on sidebar navigation items
   - Use the interactive charts and controls
   - Monitor real-time updates

### Dashboard Sections

#### Overview Section
- **Market Performance Chart**: Shows market index performance over time
- **Key Metrics Cards**: Displays total symbols, gainers, losers, and active alerts
- **Top Movers List**: Real-time list of stocks with highest price movements

#### Portfolio Section
- **Portfolio Summary**: Total value, P&L, and position information
- **Allocation Pie Chart**: Visual representation of portfolio allocation
- **Performance Chart**: Historical portfolio value over time

#### Analytics Section
- **Symbol Selector**: Choose from available stock symbols
- **Indicator Selector**: Select technical indicators (RSI, MACD, etc.)
- **Analysis Period**: Set custom analysis periods
- **Technical Chart**: Interactive chart showing selected indicator

#### Alerts Section
- **Recent Alerts**: List of recently triggered alerts
- **Alert Statistics**: Summary of alert counts and status
- **Alert Details**: Full alert information with timestamps

#### Market Section
- **Market Heatmap**: Visual heatmap of market performance
- **Sector Performance**: Performance across different sectors
- **Real-time Data**: Live market data updates

## Configuration

### Dashboard Settings

The dashboard can be configured through the main configuration file:

```yaml
dashboard:
  # Cache settings for dashboard data
  cache_duration:
    market_overview: 300  # 5 minutes
    portfolio_summary: 120  # 2 minutes
    alert_summary: 60  # 1 minute
    market_heatmap: 300  # 5 minutes
  
  # Default symbols for monitoring
  default_symbols:
    - AAPL
    - GOOGL
    - MSFT
    - TSLA
    - AMZN
  
  # Chart settings
  charts:
    default_period: 30  # days
    max_data_points: 1000
    update_interval: 30  # seconds
```

### Customization

#### Adding New Charts
1. Create new API endpoint in `src/dashboard/api.py`
2. Add corresponding method in `src/dashboard/dashboard_manager.py`
3. Update frontend JavaScript to handle new data
4. Add chart rendering logic

#### Modifying Layout
1. Edit the HTML template in the dashboard API
2. Update CSS styles for custom appearance
3. Modify JavaScript for new interactions

#### Adding New Data Sources
1. Extend `DashboardManager` with new data methods
2. Update API endpoints to expose new data
3. Modify frontend to display new information

## Performance Optimization

### Caching Strategy
- **Market Overview**: 5-minute cache (frequently accessed)
- **Portfolio Data**: 2-minute cache (moderate updates)
- **Alert Data**: 1-minute cache (real-time critical)
- **Technical Analysis**: No cache (user-specific requests)

### Data Aggregation
- **Batch Processing**: Aggregate data at regular intervals
- **Lazy Loading**: Load data only when requested
- **Pagination**: Limit data points for large datasets

### Frontend Optimization
- **Chart Optimization**: Limit data points for smooth rendering
- **Auto-refresh**: 30-second intervals for real-time updates
- **Responsive Design**: Optimized for different screen sizes

## Security

### Access Control
- **Authentication**: Integrate with user authentication system
- **Authorization**: Role-based access to different dashboard sections
- **API Security**: Rate limiting and input validation

### Data Protection
- **Input Sanitization**: Validate all user inputs
- **SQL Injection Prevention**: Use parameterized queries
- **XSS Protection**: Sanitize data before rendering

## Monitoring and Logging

### Dashboard Metrics
- **Response Times**: Monitor API endpoint performance
- **Error Rates**: Track failed requests and errors
- **User Activity**: Monitor dashboard usage patterns

### Logging
```python
# Dashboard-specific logging
logger.info(f"Dashboard accessed by user {user_id}")
logger.warning(f"Slow response time for market overview: {response_time}ms")
logger.error(f"Failed to load portfolio data: {error}")
```

## Troubleshooting

### Common Issues

#### Dashboard Not Loading
1. **Check Application Status**:
   ```bash
   curl http://localhost:8000/health
   ```

2. **Verify Database Connection**:
   ```bash
   python -c "from src.utils.database import DatabaseManager; print('DB OK')"
   ```

3. **Check Cache Status**:
   ```bash
   redis-cli ping
   ```

#### Charts Not Displaying
1. **Check JavaScript Console**: Look for JavaScript errors
2. **Verify API Endpoints**: Test endpoints directly
3. **Check Data Format**: Ensure API returns expected JSON structure

#### Slow Performance
1. **Check Cache Hit Rates**: Monitor cache effectiveness
2. **Optimize Queries**: Review database query performance
3. **Reduce Data Points**: Limit chart data for better rendering

### Debug Mode

Enable debug mode for detailed logging:

```python
# In configuration
logging:
  level: DEBUG
  dashboard_debug: true
```

## Development

### Running Tests
```bash
# Test dashboard functionality
pytest tests/test_dashboard.py

# Test API endpoints
pytest tests/test_dashboard_api.py
```

### Adding New Features
1. **Create Feature Branch**: `git checkout -b feature/new-dashboard-feature`
2. **Implement Changes**: Add new functionality
3. **Update Tests**: Add corresponding test cases
4. **Update Documentation**: Document new features
5. **Submit PR**: Create pull request for review

### Code Style
- Follow PEP 8 for Python code
- Use TypeScript for complex JavaScript
- Maintain consistent naming conventions
- Add comprehensive docstrings

## Integration

### External Systems
- **Grafana**: Export dashboard metrics to Grafana
- **Prometheus**: Monitor dashboard performance metrics
- **Slack/Teams**: Send dashboard alerts to messaging platforms

### APIs
- **REST API**: Full RESTful API for programmatic access
- **WebSocket**: Real-time data streaming (future enhancement)
- **GraphQL**: Alternative API interface (future enhancement)

## Future Enhancements

### Planned Features
- **Real-time WebSocket Updates**: Live data streaming
- **Mobile App**: Native mobile dashboard application
- **Advanced Analytics**: Machine learning insights
- **Custom Dashboards**: User-configurable layouts
- **Export Functionality**: PDF/Excel report generation

### Performance Improvements
- **Server-Side Rendering**: Improved initial load times
- **Progressive Web App**: Offline functionality
- **CDN Integration**: Faster static asset delivery
- **Database Optimization**: Improved query performance

## Support

### Getting Help
1. **Documentation**: Check this documentation first
2. **Issues**: Report bugs on GitHub issues
3. **Discussions**: Use GitHub discussions for questions
4. **Email**: Contact support team for urgent issues

### Contributing
1. **Fork Repository**: Create your own fork
2. **Make Changes**: Implement your improvements
3. **Test Thoroughly**: Ensure all tests pass
4. **Submit PR**: Create pull request with description

---

*This documentation covers the comprehensive web dashboard system for the 24/7 Global Stock Market Monitoring System. For additional information, refer to the main project documentation.* 