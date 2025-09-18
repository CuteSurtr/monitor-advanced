# PostgreSQL Grafana Dashboard Queries

Comprehensive SQL queries for building Grafana dashboards using your PostgreSQL database with 349 assets and HFT monitoring capabilities.

## Dashboard 1: Executive Portfolio Overview

### 1. Real-Time Portfolio Value (Stat Panel)
```sql
SELECT 
    SUM(market_value) as "Total Portfolio Value",
    SUM(unrealized_pnl) as "Unrealized P&L",
    SUM(realized_pnl) as "Realized P&L",
    COUNT(*) as "Position Count"
FROM portfolio.positions 
WHERE portfolio_id = '00000000-0000-0000-0000-000000000001';
```

### 2. Top Gainers/Losers Today (Table)
```sql
SELECT 
    s.symbol,
    s.company_name,
    p.unrealized_pnl as "P&L",
    ROUND((p.unrealized_pnl / (p.quantity * p.average_cost) * 100)::numeric, 2) as "P&L %",
    p.market_value as "Market Value",
    p.quantity as "Shares"
FROM portfolio.positions p
JOIN market_data.stocks s ON p.stock_id = s.id
WHERE p.portfolio_id = '00000000-0000-0000-0000-000000000001'
ORDER BY p.unrealized_pnl DESC
LIMIT 10;
```

### 3. Portfolio Allocation by Sector (Pie Chart)
```sql
SELECT 
    s.sector as "metric",
    SUM(p.market_value) as "value"
FROM portfolio.positions p
JOIN market_data.stocks s ON p.stock_id = s.id
WHERE p.portfolio_id = '00000000-0000-0000-0000-000000000001'
GROUP BY s.sector
ORDER BY SUM(p.market_value) DESC;
```

### 4. Daily Trading Activity (Time Series)
```sql
SELECT 
    DATE_TRUNC('day', transaction_date) as "time",
    SUM(CASE WHEN transaction_type = 'BUY' THEN total_amount ELSE 0 END) as "Purchases",
    SUM(CASE WHEN transaction_type = 'SELL' THEN total_amount ELSE 0 END) as "Sales",
    COUNT(*) as "Trade Count"
FROM portfolio.transactions 
WHERE portfolio_id = '00000000-0000-0000-0000-000000000001'
  AND transaction_date >= NOW() - INTERVAL '30 days'
GROUP BY DATE_TRUNC('day', transaction_date)
ORDER BY "time";
```

## Dashboard 2: Multi-Asset Market Overview

### 5. Asset Class Performance (Multi-Line Time Series)
```sql
-- Stocks Performance
SELECT 
    sp.timestamp as "time",
    'Stocks' as "metric",
    AVG(sp.close_price) as "value"
FROM market_data.stock_prices sp
JOIN market_data.stocks s ON sp.stock_id = s.id
WHERE sp.timestamp >= NOW() - INTERVAL '7 days'
  AND s.symbol IN ('AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA')
GROUP BY sp.timestamp, 'Stocks'

UNION ALL

-- Crypto Performance (from tick data)
SELECT 
    td.timestamp as "time",
    'Crypto' as "metric",
    AVG(td.price) as "value"
FROM market_data.tick_data td
JOIN market_data.cryptocurrencies c ON td.asset_id = c.id
WHERE td.asset_type = 'crypto'
  AND td.timestamp >= NOW() - INTERVAL '7 days'
  AND c.symbol IN ('BTC', 'ETH', 'ADA', 'SOL')
GROUP BY td.timestamp, 'Crypto'

UNION ALL

-- Commodities Performance
SELECT 
    td.timestamp as "time",
    'Commodities' as "metric",
    AVG(td.price) as "value"
FROM market_data.tick_data td
JOIN market_data.commodities cm ON td.asset_id = cm.id
WHERE td.asset_type = 'commodity'
  AND td.timestamp >= NOW() - INTERVAL '7 days'
  AND cm.symbol IN ('XAU/USD', 'XAG/USD', 'WTI', 'BRENT')
GROUP BY td.timestamp, 'Commodities'

ORDER BY "time";
```

### 6. Cross-Asset Volume Analysis (Bar Chart)
```sql
SELECT 
    'Stocks' as "Asset Class",
    SUM(sp.volume) as "Total Volume"
FROM market_data.stock_prices sp
WHERE sp.timestamp >= CURRENT_DATE

UNION ALL

SELECT 
    'Crypto' as "Asset Class",
    SUM(td.volume::bigint) as "Total Volume"
FROM market_data.tick_data td
WHERE td.asset_type = 'crypto'
  AND td.timestamp >= CURRENT_DATE

UNION ALL

SELECT 
    'Forex' as "Asset Class",
    SUM(td.volume::bigint) as "Total Volume"
FROM market_data.tick_data td
WHERE td.asset_type = 'forex'
  AND td.timestamp >= CURRENT_DATE

UNION ALL

SELECT 
    'Commodities' as "Asset Class",
    SUM(td.volume::bigint) as "Total Volume"
FROM market_data.tick_data td
WHERE td.asset_type = 'commodity'
  AND td.timestamp >= CURRENT_DATE;
```

### 7. Top Movers Across All Asset Classes (Table)
```sql
-- Top Stock Movers
SELECT 
    s.symbol,
    s.company_name as "Name",
    'Stock' as "Type",
    sp_current.close_price as "Current Price",
    sp_prev.close_price as "Previous Close",
    ROUND(((sp_current.close_price - sp_prev.close_price) / sp_prev.close_price * 100)::numeric, 2) as "Change %"
FROM market_data.stocks s
JOIN LATERAL (
    SELECT close_price 
    FROM market_data.stock_prices 
    WHERE stock_id = s.id 
    ORDER BY timestamp DESC 
    LIMIT 1
) sp_current ON true
JOIN LATERAL (
    SELECT close_price 
    FROM market_data.stock_prices 
    WHERE stock_id = s.id 
      AND timestamp < CURRENT_DATE
    ORDER BY timestamp DESC 
    LIMIT 1
) sp_prev ON true
WHERE s.is_active = true

UNION ALL

-- Top Crypto Movers
SELECT 
    c.symbol,
    c.name as "Name",
    'Crypto' as "Type",
    td_current.price as "Current Price",
    td_prev.price as "Previous Close",
    ROUND(((td_current.price - td_prev.price) / td_prev.price * 100)::numeric, 2) as "Change %"
FROM market_data.cryptocurrencies c
JOIN LATERAL (
    SELECT price 
    FROM market_data.tick_data 
    WHERE asset_id = c.id AND asset_type = 'crypto'
    ORDER BY timestamp DESC 
    LIMIT 1
) td_current ON true
JOIN LATERAL (
    SELECT price 
    FROM market_data.tick_data 
    WHERE asset_id = c.id AND asset_type = 'crypto'
      AND timestamp < CURRENT_DATE
    ORDER BY timestamp DESC 
    LIMIT 1
) td_prev ON true
WHERE c.is_active = true

ORDER BY "Change %" DESC
LIMIT 20;
```

## Dashboard 3: High-Frequency Trading Analytics

### 8. Real-Time Bid-Ask Spreads (Time Series)
```sql
SELECT 
    mf.timestamp as "time",
    CASE 
        WHEN mf.asset_type = 'stock' THEN s.symbol
        WHEN mf.asset_type = 'crypto' THEN c.symbol
        WHEN mf.asset_type = 'forex' THEN f.symbol
        WHEN mf.asset_type = 'commodity' THEN cm.symbol
    END as "metric",
    mf.bid_ask_spread_bps as "value"
FROM analytics.microstructure_features mf
LEFT JOIN market_data.stocks s ON mf.asset_id = s.id AND mf.asset_type = 'stock'
LEFT JOIN market_data.cryptocurrencies c ON mf.asset_id = c.id AND mf.asset_type = 'crypto'
LEFT JOIN market_data.forex_pairs f ON mf.asset_id = f.id AND mf.asset_type = 'forex'
LEFT JOIN market_data.commodities cm ON mf.asset_id = cm.id AND mf.asset_type = 'commodity'
WHERE mf.timestamp >= NOW() - INTERVAL '4 hours'
  AND mf.bid_ask_spread_bps IS NOT NULL
ORDER BY mf.timestamp;
```

### 9. Order Flow Imbalance (Heatmap/Time Series)
```sql
SELECT 
    mf.timestamp as "time",
    CASE 
        WHEN mf.asset_type = 'stock' THEN s.symbol
        WHEN mf.asset_type = 'crypto' THEN c.symbol
        WHEN mf.asset_type = 'forex' THEN f.symbol
        WHEN mf.asset_type = 'commodity' THEN cm.symbol
    END as "symbol",
    mf.order_flow_imbalance as "Order Flow Imbalance",
    mf.trade_intensity as "Trade Intensity"
FROM analytics.microstructure_features mf
LEFT JOIN market_data.stocks s ON mf.asset_id = s.id AND mf.asset_type = 'stock'
LEFT JOIN market_data.cryptocurrencies c ON mf.asset_id = c.id AND mf.asset_type = 'crypto'
LEFT JOIN market_data.forex_pairs f ON mf.asset_id = f.id AND mf.asset_type = 'forex'
LEFT JOIN market_data.commodities cm ON mf.asset_id = cm.id AND mf.asset_type = 'commodity'
WHERE mf.timestamp >= NOW() - INTERVAL '2 hours'
ORDER BY mf.timestamp;
```

### 10. Trade Intensity by Asset Type (Multi-Line Time Series)
```sql
SELECT 
    DATE_TRUNC('minute', mf.timestamp) as "time",
    mf.asset_type as "metric",
    AVG(mf.trade_intensity) as "value"
FROM analytics.microstructure_features mf
WHERE mf.timestamp >= NOW() - INTERVAL '6 hours'
  AND mf.trade_intensity IS NOT NULL
GROUP BY DATE_TRUNC('minute', mf.timestamp), mf.asset_type
ORDER BY "time";
```

## Dashboard 4: Risk Management & Alerts

### 11. Active Risk Alerts (Table)
```sql
SELECT 
    ai.title as "Alert",
    ai.severity as "Severity",
    ai.message as "Description",
    ai.triggered_at as "Time",
    ai.status as "Status",
    CASE 
        WHEN ai.stock_id IS NOT NULL THEN (SELECT symbol FROM market_data.stocks WHERE id = ai.stock_id)
        ELSE 'Portfolio'
    END as "Asset"
FROM alerts.alert_instances ai
WHERE ai.status = 'ACTIVE'
  AND ai.triggered_at >= NOW() - INTERVAL '24 hours'
ORDER BY ai.triggered_at DESC;
```

### 12. Portfolio Risk Metrics Over Time (Time Series)
```sql
-- This would require calculated metrics - simplified example
SELECT 
    DATE_TRUNC('hour', NOW()) as "time",
    'VaR 95%' as "metric",
    SUM(p.market_value) * 0.025 as "value"  -- Simplified VaR calculation
FROM portfolio.positions p
WHERE p.portfolio_id = '00000000-0000-0000-0000-000000000001'
GROUP BY DATE_TRUNC('hour', NOW())

UNION ALL

SELECT 
    DATE_TRUNC('hour', NOW()) as "time",
    'Portfolio Volatility' as "metric",
    STDDEV(p.unrealized_pnl) as "value"
FROM portfolio.positions p
WHERE p.portfolio_id = '00000000-0000-0000-0000-000000000001'
GROUP BY DATE_TRUNC('hour', NOW());
```

### 13. Concentration Risk by Position (Bar Chart)
```sql
SELECT 
    s.symbol as "Symbol",
    p.market_value as "Position Value",
    ROUND((p.market_value / portfolio_total.total_value * 100)::numeric, 2) as "Portfolio %"
FROM portfolio.positions p
JOIN market_data.stocks s ON p.stock_id = s.id
CROSS JOIN (
    SELECT SUM(market_value) as total_value 
    FROM portfolio.positions 
    WHERE portfolio_id = '00000000-0000-0000-0000-000000000001'
) portfolio_total
WHERE p.portfolio_id = '00000000-0000-0000-0000-000000000001'
ORDER BY p.market_value DESC
LIMIT 15;
```

## Dashboard 5: Global Market Sessions

### 14. Trading Sessions Activity (Time Series)
```sql
SELECT 
    td.timestamp as "time",
    CASE 
        WHEN EXTRACT(HOUR FROM td.timestamp AT TIME ZONE 'UTC') BETWEEN 14 AND 21 THEN 'US Session'
        WHEN EXTRACT(HOUR FROM td.timestamp AT TIME ZONE 'UTC') BETWEEN 8 AND 16 THEN 'European Session'
        WHEN EXTRACT(HOUR FROM td.timestamp AT TIME ZONE 'UTC') BETWEEN 0 AND 6 THEN 'Asian Session'
        ELSE 'Off Hours'
    END as "metric",
    COUNT(*) as "value"
FROM market_data.tick_data td
WHERE td.timestamp >= NOW() - INTERVAL '24 hours'
GROUP BY td.timestamp, 
    CASE 
        WHEN EXTRACT(HOUR FROM td.timestamp AT TIME ZONE 'UTC') BETWEEN 14 AND 21 THEN 'US Session'
        WHEN EXTRACT(HOUR FROM td.timestamp AT TIME ZONE 'UTC') BETWEEN 8 AND 16 THEN 'European Session'
        WHEN EXTRACT(HOUR FROM td.timestamp AT TIME ZONE 'UTC') BETWEEN 0 AND 6 THEN 'Asian Session'
        ELSE 'Off Hours'
    END
ORDER BY td.timestamp;
```

### 15. Exchange Volume Leaders (Bar Chart)
```sql
SELECT 
    e.name as "Exchange",
    COUNT(DISTINCT s.id) as "Listed Assets",
    SUM(COALESCE(sp.volume, 0)) as "Total Volume"
FROM market_data.exchanges e
LEFT JOIN market_data.stocks s ON e.id = s.exchange_id
LEFT JOIN market_data.stock_prices sp ON s.id = sp.stock_id 
    AND sp.timestamp >= CURRENT_DATE
WHERE e.id IS NOT NULL
GROUP BY e.name, e.code
ORDER BY SUM(COALESCE(sp.volume, 0)) DESC;
```

## Dashboard 6: Asset-Specific Deep Dive

### 16. Individual Asset Performance (Time Series with Template Variable)
```sql
-- Use $symbol as Grafana template variable
SELECT 
    sp.timestamp as "time",
    sp.close_price as "Price",
    sp.volume as "Volume"
FROM market_data.stock_prices sp
JOIN market_data.stocks s ON sp.stock_id = s.id
WHERE s.symbol = '$symbol'
  AND sp.timestamp >= NOW() - INTERVAL '30 days'
ORDER BY sp.timestamp;
```

### 17. Technical Indicators (Multi-Line Time Series)
```sql
-- Use $symbol as template variable
SELECT 
    ti.timestamp as "time",
    ti.indicator_name as "metric",
    ti.value as "value"
FROM market_data.technical_indicators ti
JOIN market_data.stocks s ON ti.stock_id = s.id
WHERE s.symbol = '$symbol'
  AND ti.timestamp >= NOW() - INTERVAL '30 days'
  AND ti.indicator_name IN ('SMA_20', 'SMA_50', 'RSI', 'MACD')
ORDER BY ti.timestamp;
```

### 18. Order Book Depth (Current State)
```sql
-- Use $symbol and $asset_type as template variables
SELECT 
    ob.side as "Side",
    ob.price_level as "Price",
    ob.size as "Size",
    ob.order_count as "Orders"
FROM market_data.order_book_level2 ob
WHERE ob.asset_id = (
    CASE 
        WHEN '$asset_type' = 'stock' THEN (SELECT id FROM market_data.stocks WHERE symbol = '$symbol')
        WHEN '$asset_type' = 'crypto' THEN (SELECT id FROM market_data.cryptocurrencies WHERE symbol = '$symbol')
        WHEN '$asset_type' = 'forex' THEN (SELECT id FROM market_data.forex_pairs WHERE symbol = '$symbol')
        WHEN '$asset_type' = 'commodity' THEN (SELECT id FROM market_data.commodities WHERE symbol = '$symbol')
    END
)
  AND ob.asset_type = '$asset_type'
  AND ob.timestamp >= NOW() - INTERVAL '5 minutes'
ORDER BY ob.price_level DESC;
```

## Template Variables for Grafana

### Symbol Selector (All Assets)
```sql
-- Query for symbol dropdown
SELECT DISTINCT symbol as __text, symbol as __value
FROM (
    SELECT symbol FROM market_data.stocks WHERE is_active = true
    UNION ALL
    SELECT symbol FROM market_data.cryptocurrencies WHERE is_active = true
    UNION ALL
    SELECT symbol FROM market_data.forex_pairs WHERE is_active = true
    UNION ALL
    SELECT symbol FROM market_data.commodities WHERE is_active = true
) all_symbols
ORDER BY symbol;
```

### Asset Type Selector
```sql
SELECT 'stock' as __text, 'stock' as __value
UNION ALL
SELECT 'crypto' as __text, 'crypto' as __value
UNION ALL
SELECT 'forex' as __text, 'forex' as __value
UNION ALL
SELECT 'commodity' as __text, 'commodity' as __value;
```

### Exchange Selector
```sql
SELECT name as __text, code as __value
FROM market_data.exchanges
ORDER BY name;
```

### Portfolio Selector
```sql
SELECT name as __text, id as __value
FROM portfolio.portfolios
WHERE is_active = true
ORDER BY name;
```

## Advanced Queries for Multi-Line Time Series

### 19. Multi-Symbol Price Comparison (Template Variable Multi-Select)
```sql
-- Use $symbols as multi-select template variable
SELECT 
    sp.timestamp as "time",
    s.symbol as "metric",
    sp.close_price as "value"
FROM market_data.stock_prices sp
JOIN market_data.stocks s ON sp.stock_id = s.id
WHERE s.symbol = ANY(string_to_array('$symbols', ','))
  AND sp.timestamp >= NOW() - INTERVAL '7 days'
ORDER BY sp.timestamp;
```

### 20. Normalized Performance Comparison (Multiple Assets)
```sql
-- Normalized to 100 at start date for comparison
WITH base_prices AS (
    SELECT 
        s.symbol,
        FIRST_VALUE(sp.close_price) OVER (PARTITION BY s.symbol ORDER BY sp.timestamp) as base_price
    FROM market_data.stock_prices sp
    JOIN market_data.stocks s ON sp.stock_id = s.id
    WHERE s.symbol = ANY(string_to_array('$symbols', ','))
      AND sp.timestamp >= NOW() - INTERVAL '30 days'
)
SELECT 
    sp.timestamp as "time",
    s.symbol as "metric",
    (sp.close_price / bp.base_price * 100) as "value"
FROM market_data.stock_prices sp
JOIN market_data.stocks s ON sp.stock_id = s.id
JOIN base_prices bp ON s.symbol = bp.symbol
WHERE s.symbol = ANY(string_to_array('$symbols', ','))
  AND sp.timestamp >= NOW() - INTERVAL '30 days'
ORDER BY sp.timestamp;
```

## Dashboard Configuration Tips

### Panel Settings:
- **Time Series**: Use "Connected nulls: true" for clean lines
- **Stat Panels**: Enable "Color background" for threshold alerts
- **Tables**: Sort by value columns for most relevant data first
- **Bar Charts**: Use horizontal bars for better label readability

### Refresh Intervals:
- **Real-time panels**: 30s-1m refresh
- **Historical analysis**: 5m-15m refresh
- **Static reference**: Manual refresh only

### Alert Thresholds:
- **P&L alerts**: Set based on portfolio size
- **Risk metrics**: Industry standard thresholds (VaR, drawdown)
- **Volume alerts**: Relative to historical averages

These queries leverage your complete 349-asset database with HFT capabilities and provide comprehensive monitoring across all asset classes!














