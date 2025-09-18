-- Comprehensive data population for all asset types
-- Generate tick data for all stocks (top 30 by market cap)
WITH stock_data AS (
  SELECT id, symbol, market_cap FROM market_data.stocks ORDER BY market_cap DESC LIMIT 30
)
INSERT INTO market_data.tick_data (asset_id, asset_type, timestamp, last_price, volume)
SELECT 
  s.id,
  'stock',
  generate_series(
    NOW() - INTERVAL '24 hours',
    NOW(),
    INTERVAL '1 hour'
  ),
  -- Generate realistic stock prices based on market cap
  CASE 
    WHEN s.market_cap > 1000000000000 THEN 150 + (RANDOM() * 200) + SIN(EXTRACT(EPOCH FROM generate_series(NOW() - INTERVAL '24 hours', NOW(), INTERVAL '1 hour')) / 3600) * 20
    WHEN s.market_cap > 500000000000 THEN 80 + (RANDOM() * 120) + SIN(EXTRACT(EPOCH FROM generate_series(NOW() - INTERVAL '24 hours', NOW(), INTERVAL '1 hour')) / 3600) * 15
    ELSE 40 + (RANDOM() * 80) + SIN(EXTRACT(EPOCH FROM generate_series(NOW() - INTERVAL '24 hours', NOW(), INTERVAL '1 hour')) / 3600) * 10
  END,
  (RANDOM() * 5000 + 500)::numeric(20,8)
FROM stock_data s;

-- Generate tick data for all cryptocurrencies (top 30 by market cap)
WITH crypto_data AS (
  SELECT id, symbol, market_cap FROM market_data.cryptocurrencies ORDER BY market_cap DESC LIMIT 30
)
INSERT INTO market_data.tick_data (asset_id, asset_type, timestamp, last_price, volume)
SELECT 
  c.id,
  'crypto',
  generate_series(
    NOW() - INTERVAL '24 hours',
    NOW(),
    INTERVAL '1 hour'
  ),
  -- Generate realistic crypto prices
  CASE 
    WHEN c.symbol = 'BTC' THEN 40000 + (RANDOM() * 10000) + SIN(EXTRACT(EPOCH FROM generate_series(NOW() - INTERVAL '24 hours', NOW(), INTERVAL '1 hour')) / 3600) * 2000
    WHEN c.symbol = 'ETH' THEN 2500 + (RANDOM() * 800) + SIN(EXTRACT(EPOCH FROM generate_series(NOW() - INTERVAL '24 hours', NOW(), INTERVAL '1 hour')) / 3600) * 200
    WHEN c.market_cap > 50000000000 THEN 100 + (RANDOM() * 200) + SIN(EXTRACT(EPOCH FROM generate_series(NOW() - INTERVAL '24 hours', NOW(), INTERVAL '1 hour')) / 3600) * 20
    WHEN c.market_cap > 10000000000 THEN 10 + (RANDOM() * 50) + SIN(EXTRACT(EPOCH FROM generate_series(NOW() - INTERVAL '24 hours', NOW(), INTERVAL '1 hour')) / 3600) * 5
    ELSE 1 + (RANDOM() * 10) + SIN(EXTRACT(EPOCH FROM generate_series(NOW() - INTERVAL '24 hours', NOW(), INTERVAL '1 hour')) / 3600) * 1
  END,
  (RANDOM() * 10000 + 100)::numeric(20,8)
FROM crypto_data c;

-- Generate tick data for all forex pairs (top 30)
WITH forex_data AS (
  SELECT id, symbol FROM market_data.forex_pairs ORDER BY is_major DESC, id LIMIT 30
)
INSERT INTO market_data.tick_data (asset_id, asset_type, timestamp, last_price, volume)
SELECT 
  f.id,
  'forex',
  generate_series(
    NOW() - INTERVAL '24 hours',
    NOW(),
    INTERVAL '1 hour'
  ),
  -- Generate realistic forex rates
  CASE 
    WHEN f.symbol LIKE '%JPY' THEN 100 + (RANDOM() * 50) + SIN(EXTRACT(EPOCH FROM generate_series(NOW() - INTERVAL '24 hours', NOW(), INTERVAL '1 hour')) / 3600) * 5
    WHEN f.symbol LIKE 'USD%' AND f.symbol NOT LIKE '%JPY' THEN 0.5 + (RANDOM() * 2) + SIN(EXTRACT(EPOCH FROM generate_series(NOW() - INTERVAL '24 hours', NOW(), INTERVAL '1 hour')) / 3600) * 0.1
    ELSE 1 + (RANDOM() * 0.5) + SIN(EXTRACT(EPOCH FROM generate_series(NOW() - INTERVAL '24 hours', NOW(), INTERVAL '1 hour')) / 3600) * 0.05
  END,
  (RANDOM() * 1000000 + 50000)::numeric(20,8)
FROM forex_data f;

-- Generate tick data for all commodities (top 30)
WITH commodity_data AS (
  SELECT id, symbol, asset_class FROM market_data.commodities ORDER BY id LIMIT 30
)
INSERT INTO market_data.tick_data (asset_id, asset_type, timestamp, last_price, volume)
SELECT 
  cm.id,
  'commodity',
  generate_series(
    NOW() - INTERVAL '24 hours',
    NOW(),
    INTERVAL '1 hour'
  ),
  -- Generate realistic commodity prices
  CASE 
    WHEN cm.asset_class = 'Precious Metals' AND cm.symbol = 'GOLD' THEN 1800 + (RANDOM() * 400) + SIN(EXTRACT(EPOCH FROM generate_series(NOW() - INTERVAL '24 hours', NOW(), INTERVAL '1 hour')) / 3600) * 50
    WHEN cm.asset_class = 'Precious Metals' AND cm.symbol = 'SILVER' THEN 20 + (RANDOM() * 10) + SIN(EXTRACT(EPOCH FROM generate_series(NOW() - INTERVAL '24 hours', NOW(), INTERVAL '1 hour')) / 3600) * 2
    WHEN cm.asset_class = 'Energy' AND cm.symbol IN ('WTI', 'BRENT') THEN 60 + (RANDOM() * 30) + SIN(EXTRACT(EPOCH FROM generate_series(NOW() - INTERVAL '24 hours', NOW(), INTERVAL '1 hour')) / 3600) * 5
    WHEN cm.asset_class = 'Energy' THEN 3 + (RANDOM() * 5) + SIN(EXTRACT(EPOCH FROM generate_series(NOW() - INTERVAL '24 hours', NOW(), INTERVAL '1 hour')) / 3600) * 0.5
    WHEN cm.asset_class = 'Industrial Metals' THEN 5000 + (RANDOM() * 2000) + SIN(EXTRACT(EPOCH FROM generate_series(NOW() - INTERVAL '24 hours', NOW(), INTERVAL '1 hour')) / 3600) * 300
    WHEN cm.asset_class = 'Agriculture' THEN 5 + (RANDOM() * 10) + SIN(EXTRACT(EPOCH FROM generate_series(NOW() - INTERVAL '24 hours', NOW(), INTERVAL '1 hour')) / 3600) * 1
    ELSE 100 + (RANDOM() * 200) + SIN(EXTRACT(EPOCH FROM generate_series(NOW() - INTERVAL '24 hours', NOW(), INTERVAL '1 hour')) / 3600) * 20
  END,
  (RANDOM() * 2000 + 100)::numeric(20,8)
FROM commodity_data cm;