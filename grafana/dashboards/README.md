# Comprehensive Multi-Asset Trading Dashboards

This directory contains comprehensive Grafana dashboards for multi-asset trading, risk management, and options analysis based on the PostgreSQL database structure from `init.sql`.

## Dashboard Files

### 1. `comprehensive-multi-asset-trading-dashboard.json`
**Main Dashboard** - Comprehensive overview of all asset classes with real-time monitoring.

**Features:**
- **Top 30 Assets by Category**: Stocks, Cryptocurrencies, Commodities, Forex
- **Real-Time Price Charts**: Time series visualization of major assets
- **Portfolio Risk Metrics**: VaR, CVaR, Maximum Drawdown
- **Real-Time P&L**: Live profit/loss monitoring
- **Correlation Analysis**: Portfolio and cross-asset correlations
- **Market News & Sentiment**: Real-time market updates
- **Bid-Ask Spread Analysis**: Market microstructure monitoring
- **Order Flow Imbalance**: Trading flow analysis
- **Market Depth Analysis**: Liquidity monitoring
- **Asset Performance Heatmap**: Visual performance comparison

### 2. `enhanced-options-trading-dashboard.json`
**Options Trading Dashboard** - Advanced options analysis and risk management.

**Features:**
- **Options Chain Overview**: Complete options data with expiration dates
- **Greeks Analysis**: Delta, Gamma, Theta, Vega monitoring
- **Implied Volatility Surface**: 3D volatility visualization
- **Options Volume & Open Interest**: Trading activity analysis
- **VIX Monitoring**: Real-time volatility index tracking
- **VIX Term Structure**: Contango/Backwardation analysis
- **VIX Put/Call Ratio**: Market sentiment indicators
- **Portfolio Greeks Risk**: Options portfolio risk exposure
- **Options Expiration Risk Calendar**: Expiration risk management
- **Volatility Skew Analysis**: Strike price volatility patterns
- **Options Flow & Unusual Activity**: Market flow monitoring
- **Risk-Adjusted Performance Metrics**: Advanced performance analysis

## Color Coding System

### Risk Level Indicators
- **🟢 Green**: Safe/Low Risk
- **🟡 Yellow**: Medium Risk/At Risk
- **🔴 Red**: High Risk/Negative

### Thresholds
- **Portfolio P&L**: 
  - Green: > $10,000
  - Yellow: $0 - $10,000
  - Red: < $0
- **VIX Levels**:
  - Green: < 20 (Low Volatility)
  - Yellow: 20-25 (Medium Volatility)
  - Orange: 25-30 (High Volatility)
  - Red: > 30 (Extreme Volatility)
- **Bid-Ask Spreads**:
  - Green: < 5 bps
  - Yellow: 5-10 bps
  - Red: > 10 bps

## Database Integration

### Required Tables
The dashboards are designed to work with the following database schema:

#### Market Data Tables
- `market_data.stocks` - Stock information
- `market_data.cryptocurrencies` - Cryptocurrency data
- `market_data.commodities` - Commodity information
- `market_data.forex_pairs` - Forex pair data
- `market_data.tick_data` - Real-time price data
- `market_data.stock_prices` - Historical stock prices
- `market_data.technical_indicators` - Technical analysis data

#### Portfolio Tables
- `portfolio.portfolios` - Portfolio definitions
- `portfolio.positions` - Current positions
- `portfolio.transactions` - Trading history

#### Analytics Tables
- `analytics.microstructure_features` - Market microstructure data
- `analytics.options_chain` - Options data (if available)
- `analytics.options_greeks` - Options Greeks (if available)
- `analytics.vix_metrics` - VIX-related metrics (if available)

#### Monitoring Tables
- `monitoring.system_metrics` - System performance data
- `monitoring.health_checks` - System health status

## Installation & Setup

### 1. Import Dashboards
1. Open Grafana in your browser
2. Navigate to **Dashboards** → **Import**
3. Upload the JSON files or paste the content
4. Configure the data source (PostgreSQL)
5. Save the dashboard

### 2. Data Source Configuration
```yaml
# Grafana Data Source Configuration
type: postgres
name: Stock Monitor Database
url: localhost:5432
database: stock_monitor
user: grafana_user
password: grafana_password
sslMode: disable
```

### 3. Database Permissions
Ensure the `grafana_user` has read access to all required schemas:
```sql
GRANT USAGE ON SCHEMA market_data, portfolio, analytics, monitoring TO grafana_user;
GRANT SELECT ON ALL TABLES IN SCHEMA market_data, portfolio, analytics, monitoring TO grafana_user;
```

## Dashboard Features

### Real-Time Updates
- **Refresh Intervals**: 5s, 10s, 30s, 1m, 5m, 15m, 30m, 1h, 2h, 1d
- **Live Data**: Real-time tick data and market updates
- **Auto-refresh**: Configurable automatic refresh rates

### Interactive Elements
- **Templating Variables**: Asset type, portfolio, time range selection
- **Dynamic Queries**: Real-time database queries
- **Responsive Layout**: Adaptive grid positioning

### Visualization Types
- **Time Series**: Price charts, risk metrics over time
- **Tables**: Asset performance, options chains, risk metrics
- **Heatmaps**: Correlation analysis, volatility surfaces
- **Stat Panels**: Key metrics, risk indicators
- **Text Panels**: News, sentiment, market updates

## Customization

### Adding New Assets
1. Update the database with new asset data
2. Modify dashboard queries to include new symbols
3. Add new panels for asset-specific metrics

### Modifying Risk Thresholds
1. Edit the `fieldConfig.thresholds` sections
2. Adjust color coding values
3. Update risk level calculations

### Adding New Metrics
1. Create new database views/functions
2. Add new dashboard panels
3. Configure appropriate visualizations

## Performance Optimization

### Database Indexes
Ensure proper indexing for dashboard queries:
```sql
-- Key indexes for dashboard performance
CREATE INDEX idx_tick_data_asset_timestamp ON market_data.tick_data(asset_id, asset_type, timestamp DESC);
CREATE INDEX idx_stock_prices_stock_timestamp ON market_data.stock_prices(stock_id, timestamp DESC);
CREATE INDEX idx_portfolio_positions_portfolio ON portfolio.positions(portfolio_id);
```

### Query Optimization
- Use appropriate time ranges
- Limit result sets with LIMIT clauses
- Implement materialized views for complex calculations

### Caching
- Enable Grafana query caching
- Use database query result caching
- Implement Redis caching for frequently accessed data

## Troubleshooting

### Common Issues
1. **Data Not Loading**: Check database connectivity and permissions
2. **Slow Performance**: Optimize database queries and add indexes
3. **Missing Data**: Verify data exists in the database
4. **Permission Errors**: Ensure proper user access rights

### Debug Mode
Enable Grafana debug logging:
```ini
[log]
level = debug
```

### Query Testing
Test dashboard queries directly in the database:
```sql
-- Example: Test options chain query
SELECT * FROM analytics.options_chain 
WHERE underlying = 'AAPL' 
AND expiration = '2024-01-19' 
LIMIT 10;
```

## Support & Maintenance

### Regular Updates
- Monitor dashboard performance
- Update asset lists and symbols
- Refresh risk thresholds based on market conditions
- Maintain database indexes and statistics

### Backup & Recovery
- Export dashboard configurations regularly
- Backup database schemas and data
- Document custom modifications

### Monitoring
- Track dashboard load times
- Monitor database query performance
- Alert on data quality issues

## License
These dashboards are provided as-is for educational and trading purposes. Please ensure compliance with your organization's data usage policies and trading regulations.
