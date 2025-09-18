# InfluxDB Grafana Dashboard Queries

This document contains pre-built Grafana queries for your comprehensive financial monitoring system using InfluxDB.

## Real-Time Market Data Queries

### 1. Multi-Asset Price Comparison (Time Series)
```flux
from(bucket: "market_data")
  |> range(start: -1h)
  |> filter(fn: (r) => r["_measurement"] == "market_data")
  |> filter(fn: (r) => r["_field"] == "price")
  |> filter(fn: (r) => contains(value: r["symbol"], set: ["SPY", "QQQ", "AAPL", "TSLA"]))
  |> aggregateWindow(every: 1m, fn: last, createEmpty: false)
  |> yield(name: "prices")
```

### 2. Volume Analysis by Asset Type (Bar Chart)
```flux
from(bucket: "market_data")
  |> range(start: -1d)
  |> filter(fn: (r) => r["_measurement"] == "market_data")
  |> filter(fn: (r) => r["_field"] == "volume")
  |> group(columns: ["asset_type"])
  |> sum()
  |> yield(name: "volume_by_type")
```

### 3. Bid-Ask Spread Monitoring (Time Series)
```flux
from(bucket: "market_data")
  |> range(start: -4h)
  |> filter(fn: (r) => r["_measurement"] == "market_data")
  |> filter(fn: (r) => r["_field"] == "spread_bps")
  |> filter(fn: (r) => r["symbol"] == "${symbol}")
  |> aggregateWindow(every: 5m, fn: mean, createEmpty: false)
  |> yield(name: "spread")
```

## Portfolio Analytics Queries

### 4. Real-Time P&L (Stat Panel)
```flux
from(bucket: "portfolio_metrics")
  |> range(start: -1h)
  |> filter(fn: (r) => r["_measurement"] == "portfolio_metrics")
  |> filter(fn: (r) => r["_field"] == "pnl_daily")
  |> last()
  |> yield(name: "daily_pnl")
```

### 5. Portfolio Value Over Time (Time Series)
```flux
from(bucket: "portfolio_metrics")
  |> range(start: -7d)
  |> filter(fn: (r) => r["_measurement"] == "portfolio_metrics")
  |> filter(fn: (r) => r["_field"] == "total_value")
  |> aggregateWindow(every: 1h, fn: last, createEmpty: false)
  |> yield(name: "portfolio_value")
```

### 6. VaR/CVaR Risk Metrics (Multi-Stat Panel)
```flux
// VaR 99%
from(bucket: "risk_analytics")
  |> range(start: -1h)
  |> filter(fn: (r) => r["_measurement"] == "risk_metrics")
  |> filter(fn: (r) => r["_field"] == "var")
  |> filter(fn: (r) => r["confidence_level"] == "0.99")
  |> last()
  |> yield(name: "var_99")

// CVaR 99%
from(bucket: "risk_analytics")
  |> range(start: -1h)
  |> filter(fn: (r) => r["_measurement"] == "risk_metrics")
  |> filter(fn: (r) => r["_field"] == "cvar")
  |> filter(fn: (r) => r["confidence_level"] == "0.99")
  |> last()
  |> yield(name: "cvar_99")
```

### 7. Maximum Drawdown (Gauge)
```flux
from(bucket: "risk_analytics")
  |> range(start: -1h)
  |> filter(fn: (r) => r["_measurement"] == "risk_metrics")
  |> filter(fn: (r) => r["_field"] == "max_drawdown")
  |> last()
  |> yield(name: "max_drawdown")
```

## VIX and Volatility Monitoring

### 8. VIX Index with Threshold Lines (Time Series)
```flux
from(bucket: "vix_data")
  |> range(start: -24h)
  |> filter(fn: (r) => r["_measurement"] == "vix_data")
  |> filter(fn: (r) => r["_field"] == "vix_spot")
  |> aggregateWindow(every: 5m, fn: last, createEmpty: false)
  |> yield(name: "vix")
```

### 9. Volatility Regime Indicator (Stat Panel)
```flux
from(bucket: "vix_data")
  |> range(start: -1h)
  |> filter(fn: (r) => r["_measurement"] == "vix_data")
  |> filter(fn: (r) => r["volatility_regime"] != "")
  |> last()
  |> keep(columns: ["volatility_regime"])
  |> yield(name: "vol_regime")
```

### 10. VIX Term Structure (Time Series)
```flux
from(bucket: "vix_data")
  |> range(start: -6h)
  |> filter(fn: (r) => r["_measurement"] == "vix_data")
  |> filter(fn: (r) => r["_field"] =~ /vix_.*/)
  |> aggregateWindow(every: 30m, fn: last, createEmpty: false)
  |> yield(name: "vix_curve")
```

## Options Chain Analysis

### 11. Call/Put Ratio by Symbol (Bar Chart)
```flux
from(bucket: "options_data")
  |> range(start: -4h)
  |> filter(fn: (r) => r["_measurement"] == "options_analysis")
  |> filter(fn: (r) => r["_field"] == "call_put_ratio")
  |> group(columns: ["symbol"])
  |> last()
  |> yield(name: "call_put_ratios")
```

### 12. Max Pain vs Current Price (Time Series)
```flux
// Max Pain
from(bucket: "options_data")
  |> range(start: -1d)
  |> filter(fn: (r) => r["_measurement"] == "options_analysis")
  |> filter(fn: (r) => r["_field"] == "max_pain")
  |> filter(fn: (r) => r["symbol"] == "${symbol}")
  |> aggregateWindow(every: 15m, fn: last, createEmpty: false)
  |> yield(name: "max_pain")

// Current Price
from(bucket: "options_data")
  |> range(start: -1d)
  |> filter(fn: (r) => r["_measurement"] == "options_analysis")
  |> filter(fn: (r) => r["_field"] == "underlying_price")
  |> filter(fn: (r) => r["symbol"] == "${symbol}")
  |> aggregateWindow(every: 15m, fn: last, createEmpty: false)
  |> yield(name: "current_price")
```

### 13. Gamma Exposure (Time Series)
```flux
from(bucket: "options_data")
  |> range(start: -2d)
  |> filter(fn: (r) => r["_measurement"] == "options_analysis")
  |> filter(fn: (r) => r["_field"] == "gamma_exposure")
  |> filter(fn: (r) => r["symbol"] == "${symbol}")
  |> aggregateWindow(every: 1h, fn: last, createEmpty: false)
  |> yield(name: "gamma_exposure")
```

## Global Market Monitoring

### 14. Multi-Exchange Trading Volume (Time Series)
```flux
from(bucket: "global_exchanges")
  |> range(start: -12h)
  |> filter(fn: (r) => r["_measurement"] == "global_market_data")
  |> filter(fn: (r) => r["_field"] == "volume")
  |> group(columns: ["exchange"])
  |> aggregateWindow(every: 1h, fn: sum, createEmpty: false)
  |> yield(name: "exchange_volume")
```

### 15. Cross-Asset Correlation Heatmap
```flux
// This would require custom processing in Grafana or a transformation
from(bucket: "market_data")
  |> range(start: -30d)
  |> filter(fn: (r) => r["_measurement"] == "market_data")
  |> filter(fn: (r) => r["_field"] == "price")
  |> filter(fn: (r) => contains(value: r["symbol"], set: ["SPY", "QQQ", "GLD", "TLT", "BTC-USD"]))
  |> aggregateWindow(every: 1d, fn: last, createEmpty: false)
  |> pivot(rowKey:["_time"], columnKey: ["symbol"], valueColumn: "_value")
```

## Risk Alerts and Monitoring

### 16. Active Risk Alerts (Table)
```flux
from(bucket: "risk_analytics")
  |> range(start: -24h)
  |> filter(fn: (r) => r["_measurement"] == "volatility_alerts")
  |> filter(fn: (r) => r["level"] == "high" or r["level"] == "critical")
  |> sort(columns: ["_time"], desc: true)
  |> limit(n: 10)
  |> yield(name: "risk_alerts")
```

### 17. Portfolio Concentration Risk (Pie Chart)
```flux
from(bucket: "portfolio_metrics")
  |> range(start: -1h)
  |> filter(fn: (r) => r["_measurement"] == "position_weights")
  |> filter(fn: (r) => r["_field"] == "weight")
  |> group(columns: ["symbol"])
  |> last()
  |> yield(name: "position_weights")
```

## Performance Analytics

### 18. Sharpe Ratio Trend (Time Series)
```flux
from(bucket: "portfolio_metrics")
  |> range(start: -30d)
  |> filter(fn: (r) => r["_measurement"] == "portfolio_metrics")
  |> filter(fn: (r) => r["_field"] == "sharpe_ratio")
  |> aggregateWindow(every: 1d, fn: last, createEmpty: false)
  |> yield(name: "sharpe_ratio")
```

### 19. Beta vs Benchmark (Stat Panel)
```flux
from(bucket: "portfolio_metrics")
  |> range(start: -1h)
  |> filter(fn: (r) => r["_measurement"] == "portfolio_metrics")
  |> filter(fn: (r) => r["_field"] == "beta")
  |> last()
  |> yield(name: "beta")
```

### 20. Returns Distribution (Histogram)
```flux
from(bucket: "portfolio_metrics")
  |> range(start: -252d)  // 1 year
  |> filter(fn: (r) => r["_measurement"] == "portfolio_metrics")
  |> filter(fn: (r) => r["_field"] == "daily_return_percent")
  |> yield(name: "daily_returns")
```

## Template Variables for Grafana

### Symbol Selection
```flux
// Query for symbol dropdown
from(bucket: "market_data")
  |> range(start: -1h)
  |> filter(fn: (r) => r["_measurement"] == "market_data")
  |> keep(columns: ["symbol"])
  |> distinct()
  |> yield(name: "symbols")
```

### Asset Type Selection
```flux
// Query for asset type dropdown
from(bucket: "market_data")
  |> range(start: -1h)
  |> filter(fn: (r) => r["_measurement"] == "market_data")
  |> keep(columns: ["asset_type"])
  |> distinct()
  |> yield(name: "asset_types")
```

### Exchange Selection
```flux
// Query for exchange dropdown
from(bucket: "global_exchanges")
  |> range(start: -1h)
  |> filter(fn: (r) => r["_measurement"] == "global_market_data")
  |> keep(columns: ["exchange"])
  |> distinct()
  |> yield(name: "exchanges")
```

## Dashboard Organization

### Recommended Dashboard Structure:

1. **Executive Summary Dashboard**
   - Real-time P&L (Query #4)
   - Portfolio Value (Query #5)
   - VaR/CVaR (Query #6)
   - Max Drawdown (Query #7)
   - Active Alerts (Query #16)

2. **Market Overview Dashboard**
   - Multi-asset prices (Query #1)
   - Volume by asset type (Query #2)
   - VIX with thresholds (Query #8)
   - Global exchange volume (Query #14)

3. **Risk Analytics Dashboard**
   - VaR/CVaR trends
   - Max drawdown history
   - Volatility regime indicators
   - Risk alerts table

4. **Options Analysis Dashboard**
   - Call/Put ratios (Query #11)
   - Max Pain vs Price (Query #12)
   - Gamma exposure (Query #13)
   - Volatility skew

5. **Performance Analytics Dashboard**
   - Sharpe ratio trend (Query #18)
   - Beta analysis (Query #19)
   - Returns distribution (Query #20)
   - Portfolio concentration (Query #17)

## Notes

- All queries use relative time ranges (e.g., `-1h`, `-7d`) for real-time updates
- Template variables allow dynamic filtering by symbol, asset type, and exchange
- Queries are optimized for performance with appropriate aggregateWindow functions
- Alert thresholds can be added to any visualization using Grafana's built-in alerting














