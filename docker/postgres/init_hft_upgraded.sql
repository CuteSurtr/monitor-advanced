-- Database initialization script for Stock Market Monitor - HFT Multi-Asset Upgraded
-- This script creates the necessary tables and initial data for high-frequency trading monitoring
-- Supports stocks, forex, cryptocurrencies, and commodities

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "timescaledb";  -- For time-series optimization

-- Create schemas
CREATE SCHEMA IF NOT EXISTS market_data;
CREATE SCHEMA IF NOT EXISTS portfolio;
CREATE SCHEMA IF NOT EXISTS alerts;
CREATE SCHEMA IF NOT EXISTS analytics;
CREATE SCHEMA IF NOT EXISTS monitoring;

-- Set default schema
SET search_path TO public, market_data, portfolio, alerts, analytics, monitoring;

-- =====================================================
-- PART 1: Asset-Specific Master Tables
-- =====================================================

-- Existing exchanges table (keeping original)
CREATE TABLE IF NOT EXISTS market_data.exchanges (
    id SERIAL PRIMARY KEY,
    code VARCHAR(10) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    timezone VARCHAR(50) NOT NULL,
    market_open TIME NOT NULL,
    market_close TIME NOT NULL,
    currency VARCHAR(3) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Enhanced stocks table (keeping original but adding market_cap)
CREATE TABLE IF NOT EXISTS market_data.stocks (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    exchange_id INTEGER REFERENCES market_data.exchanges(id),
    company_name VARCHAR(200),
    sector VARCHAR(100),
    industry VARCHAR(100),
    market_cap BIGINT,
    currency VARCHAR(3) DEFAULT 'USD',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, exchange_id)
);

-- NEW: Cryptocurrencies master table
CREATE TABLE IF NOT EXISTS market_data.cryptocurrencies (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) UNIQUE NOT NULL,  -- e.g., 'BTC', 'ETH'
    name VARCHAR(100) NOT NULL,          -- e.g., 'Bitcoin', 'Ethereum'
    market_cap BIGINT,
    circulating_supply DECIMAL(30,8),
    total_supply DECIMAL(30,8),
    max_supply DECIMAL(30,8),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- NEW: Forex pairs master table
CREATE TABLE IF NOT EXISTS market_data.forex_pairs (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) UNIQUE NOT NULL,  -- e.g., 'EUR/USD', 'GBP/JPY'
    base_currency VARCHAR(3) NOT NULL,   -- e.g., 'EUR' in EUR/USD
    quote_currency VARCHAR(3) NOT NULL,  -- e.g., 'USD' in EUR/USD
    pip_size DECIMAL(10,8) DEFAULT 0.0001,
    is_major BOOLEAN DEFAULT false,      -- Major pairs like EUR/USD, GBP/USD
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- NEW: Commodities master table
CREATE TABLE IF NOT EXISTS market_data.commodities (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) UNIQUE NOT NULL,  -- e.g., 'XAU/USD', 'WTI', 'BRENT'
    name VARCHAR(100) NOT NULL,          -- e.g., 'Gold', 'Crude Oil WTI'
    asset_class VARCHAR(50) NOT NULL,    -- e.g., 'Metals', 'Energy', 'Agriculture'
    unit VARCHAR(20),                    -- e.g., 'Troy Ounce', 'Barrel', 'Bushel'
    contract_size DECIMAL(15,4),
    tick_size DECIMAL(10,8),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- PART 2: Universal High-Frequency Data Tables
-- =====================================================

-- NEW: Tick data table for HFT monitoring (most crucial table)
CREATE TABLE IF NOT EXISTS market_data.tick_data (
    id BIGSERIAL PRIMARY KEY,
    asset_id INTEGER NOT NULL,                    -- References one of the master tables
    asset_type VARCHAR(20) NOT NULL,              -- 'stock', 'crypto', 'forex', 'commodity'
    timestamp TIMESTAMPTZ(6) NOT NULL,            -- Microsecond precision for HFT
    price DECIMAL(20,8) NOT NULL,
    volume DECIMAL(20,8) NOT NULL,
    aggressor_side VARCHAR(4),                    -- 'BUY' or 'SELL'
    trade_id VARCHAR(50),                         -- Exchange-specific trade ID
    exchange_timestamp TIMESTAMPTZ(6),            -- Original exchange timestamp
    latency_us INTEGER,                           -- Latency in microseconds from exchange
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT valid_asset_type CHECK (asset_type IN ('stock', 'crypto', 'forex', 'commodity')),
    CONSTRAINT valid_aggressor_side CHECK (aggressor_side IN ('BUY', 'SELL', NULL))
);

-- NEW: Level 2 Order Book data for market depth monitoring
CREATE TABLE IF NOT EXISTS market_data.order_book_level2 (
    id BIGSERIAL PRIMARY KEY,
    asset_id INTEGER NOT NULL,
    asset_type VARCHAR(20) NOT NULL,
    timestamp TIMESTAMPTZ(6) NOT NULL,
    side VARCHAR(4) NOT NULL,                     -- 'BID' or 'ASK'
    price_level DECIMAL(20,8) NOT NULL,
    size DECIMAL(20,8) NOT NULL,
    order_count INTEGER,                          -- Number of orders at this level
    exchange_timestamp TIMESTAMPTZ(6),
    sequence_number BIGINT,                       -- For maintaining order book integrity
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT valid_asset_type_ob CHECK (asset_type IN ('stock', 'crypto', 'forex', 'commodity')),
    CONSTRAINT valid_side CHECK (side IN ('BID', 'ASK'))
);

-- Enhanced stock prices table (keeping original for backward compatibility)
CREATE TABLE IF NOT EXISTS market_data.stock_prices (
    id BIGSERIAL PRIMARY KEY,
    stock_id INTEGER REFERENCES market_data.stocks(id),
    timestamp TIMESTAMP NOT NULL,
    open_price DECIMAL(15,4),
    high_price DECIMAL(15,4),
    low_price DECIMAL(15,4),
    close_price DECIMAL(15,4),
    volume BIGINT,
    adjusted_close DECIMAL(15,4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Technical indicators (keeping original)
CREATE TABLE IF NOT EXISTS market_data.technical_indicators (
    id BIGSERIAL PRIMARY KEY,
    stock_id INTEGER REFERENCES market_data.stocks(id),
    timestamp TIMESTAMP NOT NULL,
    indicator_name VARCHAR(50) NOT NULL,
    value DECIMAL(15,6),
    parameters JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- PART 3: HFT Analytics Table
-- =====================================================

-- NEW: Microstructure features for advanced HFT analytics
CREATE TABLE IF NOT EXISTS analytics.microstructure_features (
    id BIGSERIAL PRIMARY KEY,
    asset_id INTEGER NOT NULL,
    asset_type VARCHAR(20) NOT NULL,
    timestamp TIMESTAMPTZ(6) NOT NULL,
    
    -- Spread and liquidity metrics
    bid_ask_spread DECIMAL(15,6),                 -- Absolute spread
    bid_ask_spread_bps DECIMAL(10,4),             -- Spread in basis points
    bid_ask_spread_percent DECIMAL(10,6),         -- Spread as percentage of mid-price
    mid_price DECIMAL(20,8),                      -- (best_bid + best_ask) / 2
    
    -- Order flow metrics
    order_flow_imbalance DECIMAL(15,6),           -- (bid_volume - ask_volume) / (bid_volume + ask_volume)
    buy_volume_ratio DECIMAL(6,4),                -- Buy volume / Total volume
    sell_volume_ratio DECIMAL(6,4),               -- Sell volume / Total volume
    
    -- Trading intensity metrics
    trade_intensity DECIMAL(15,6),                -- Trades per second over time window
    volume_intensity DECIMAL(15,6),               -- Volume per second over time window
    price_volatility DECIMAL(15,6),               -- Price volatility over time window
    
    -- Market impact measures
    realized_spread DECIMAL(15,6),                -- Post-trade price impact
    effective_spread DECIMAL(15,6),               -- Immediate price impact
    price_improvement DECIMAL(15,6),              -- Price improvement vs. quoted spread
    
    -- Liquidity metrics
    market_depth_bid DECIMAL(20,8),               -- Total volume in top 5 bid levels
    market_depth_ask DECIMAL(20,8),               -- Total volume in top 5 ask levels
    book_pressure DECIMAL(10,6),                  -- Pressure from order book imbalance
    
    -- High-frequency patterns
    momentum_5s DECIMAL(10,6),                    -- 5-second momentum
    momentum_30s DECIMAL(10,6),                   -- 30-second momentum
    volume_weighted_price DECIMAL(20,8),          -- VWAP over time window
    
    -- Timing metrics
    time_since_last_trade INTEGER,                -- Milliseconds since last trade
    trade_duration_avg INTEGER,                   -- Average time between trades (ms)
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT valid_asset_type_features CHECK (asset_type IN ('stock', 'crypto', 'forex', 'commodity'))
);

-- =====================================================
-- EXISTING TABLES (Portfolio, Alerts, etc.)
-- =====================================================

-- Portfolio Tables (keeping original)
CREATE TABLE IF NOT EXISTS portfolio.portfolios (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    currency VARCHAR(3) DEFAULT 'USD',
    initial_value DECIMAL(20,4),
    risk_tolerance VARCHAR(20) DEFAULT 'moderate',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS portfolio.positions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    portfolio_id UUID REFERENCES portfolio.portfolios(id),
    stock_id INTEGER REFERENCES market_data.stocks(id),
    quantity DECIMAL(15,6) NOT NULL,
    average_cost DECIMAL(15,4) NOT NULL,
    current_price DECIMAL(15,4),
    market_value DECIMAL(20,4),
    unrealized_pnl DECIMAL(20,4),
    realized_pnl DECIMAL(20,4) DEFAULT 0,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS portfolio.transactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    portfolio_id UUID REFERENCES portfolio.portfolios(id),
    stock_id INTEGER REFERENCES market_data.stocks(id),
    transaction_type VARCHAR(10) NOT NULL CHECK (transaction_type IN ('BUY', 'SELL')),
    quantity DECIMAL(15,6) NOT NULL,
    price DECIMAL(15,4) NOT NULL,
    total_amount DECIMAL(20,4) NOT NULL,
    commission DECIMAL(10,4) DEFAULT 0,
    transaction_date TIMESTAMP NOT NULL,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Alert Tables (keeping original)
CREATE TABLE IF NOT EXISTS alerts.alert_rules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    alert_type VARCHAR(50) NOT NULL,
    conditions JSONB NOT NULL,
    thresholds JSONB NOT NULL,
    notification_channels JSONB,
    is_active BOOLEAN DEFAULT true,
    created_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS alerts.alert_instances (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    rule_id UUID REFERENCES alerts.alert_rules(id),
    stock_id INTEGER REFERENCES market_data.stocks(id),
    portfolio_id UUID REFERENCES portfolio.portfolios(id),
    severity VARCHAR(20) NOT NULL,
    title VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    data JSONB,
    status VARCHAR(20) DEFAULT 'ACTIVE',
    triggered_at TIMESTAMP NOT NULL,
    resolved_at TIMESTAMP,
    acknowledged_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Analytics Tables (keeping existing + new ones)
CREATE TABLE IF NOT EXISTS analytics.predictions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    stock_id INTEGER REFERENCES market_data.stocks(id),
    model_name VARCHAR(100) NOT NULL,
    model_version VARCHAR(50),
    prediction_type VARCHAR(50) NOT NULL,
    predicted_value DECIMAL(15,6),
    confidence_score DECIMAL(3,2),
    prediction_horizon INTEGER, -- in minutes
    features_used JSONB,
    prediction_date TIMESTAMP NOT NULL,
    target_date TIMESTAMP NOT NULL,
    actual_value DECIMAL(15,6),
    accuracy_score DECIMAL(3,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS analytics.anomalies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    stock_id INTEGER REFERENCES market_data.stocks(id),
    detection_method VARCHAR(100) NOT NULL,
    anomaly_type VARCHAR(50) NOT NULL,
    anomaly_score DECIMAL(5,4) NOT NULL,
    data_point JSONB NOT NULL,
    context JSONB,
    severity VARCHAR(20) DEFAULT 'LOW',
    detected_at TIMESTAMP NOT NULL,
    investigated BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Monitoring Tables (keeping original)
CREATE TABLE IF NOT EXISTS monitoring.system_metrics (
    id BIGSERIAL PRIMARY KEY,
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(15,6) NOT NULL,
    labels JSONB,
    timestamp TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS monitoring.health_checks (
    id BIGSERIAL PRIMARY KEY,
    component_name VARCHAR(100) NOT NULL,
    check_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL,
    response_time_ms INTEGER,
    message TEXT,
    details JSONB,
    checked_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- INDEXES FOR HFT PERFORMANCE
-- =====================================================

-- Existing indexes (keeping all original ones)
CREATE INDEX IF NOT EXISTS idx_stock_prices_stock_timestamp ON market_data.stock_prices(stock_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_stock_prices_timestamp ON market_data.stock_prices(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_technical_indicators_stock_timestamp ON market_data.technical_indicators(stock_id, timestamp DESC, indicator_name);
CREATE INDEX IF NOT EXISTS idx_positions_portfolio ON portfolio.positions(portfolio_id);
CREATE INDEX IF NOT EXISTS idx_transactions_portfolio_date ON portfolio.transactions(portfolio_id, transaction_date DESC);
CREATE INDEX IF NOT EXISTS idx_alert_instances_status_triggered ON alerts.alert_instances(status, triggered_at DESC);
CREATE INDEX IF NOT EXISTS idx_predictions_stock_date ON analytics.predictions(stock_id, prediction_date DESC);
CREATE INDEX IF NOT EXISTS idx_anomalies_stock_detected ON analytics.anomalies(stock_id, detected_at DESC);
CREATE INDEX IF NOT EXISTS idx_system_metrics_name_timestamp ON monitoring.system_metrics(metric_name, timestamp DESC);

-- NEW: HFT-optimized indexes for tick data
CREATE INDEX IF NOT EXISTS idx_tick_data_asset_timestamp ON market_data.tick_data(asset_id, asset_type, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_tick_data_timestamp ON market_data.tick_data(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_tick_data_asset_type_timestamp ON market_data.tick_data(asset_type, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_tick_data_aggressor_timestamp ON market_data.tick_data(aggressor_side, timestamp DESC) WHERE aggressor_side IS NOT NULL;

-- NEW: Order book indexes for fast level 2 queries
CREATE INDEX IF NOT EXISTS idx_order_book_asset_timestamp ON market_data.order_book_level2(asset_id, asset_type, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_order_book_timestamp ON market_data.order_book_level2(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_order_book_side_price ON market_data.order_book_level2(asset_id, side, price_level) WHERE timestamp > (NOW() - INTERVAL '1 hour');

-- NEW: Microstructure features indexes
CREATE INDEX IF NOT EXISTS idx_microstructure_asset_timestamp ON analytics.microstructure_features(asset_id, asset_type, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_microstructure_timestamp ON analytics.microstructure_features(timestamp DESC);

-- NEW: Master table indexes
CREATE INDEX IF NOT EXISTS idx_cryptocurrencies_symbol ON market_data.cryptocurrencies(symbol) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_forex_pairs_symbol ON market_data.forex_pairs(symbol) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_commodities_symbol ON market_data.commodities(symbol) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_commodities_asset_class ON market_data.commodities(asset_class) WHERE is_active = true;

-- Partial indexes for active records (keeping original + new ones)
CREATE INDEX IF NOT EXISTS idx_stocks_active ON market_data.stocks(symbol, exchange_id) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_portfolios_active ON portfolio.portfolios(name) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_alert_rules_active ON alerts.alert_rules(alert_type) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_alert_instances_active ON alerts.alert_instances(triggered_at DESC) WHERE status = 'ACTIVE';

-- =====================================================
-- TIME-SERIES OPTIMIZATIONS (if TimescaleDB available)
-- =====================================================

-- Convert tick_data to hypertable for better performance (optional - requires TimescaleDB)
-- SELECT create_hypertable('market_data.tick_data', 'timestamp', if_not_exists => TRUE);
-- SELECT create_hypertable('market_data.order_book_level2', 'timestamp', if_not_exists => TRUE);
-- SELECT create_hypertable('analytics.microstructure_features', 'timestamp', if_not_exists => TRUE);

-- =====================================================
-- SAMPLE DATA FOR TESTING
-- =====================================================

-- Insert default exchanges (keeping original)
INSERT INTO market_data.exchanges (code, name, timezone, market_open, market_close, currency) VALUES
    ('NYSE', 'New York Stock Exchange', 'America/New_York', '09:30:00', '16:00:00', 'USD'),
    ('NASDAQ', 'NASDAQ', 'America/New_York', '09:30:00', '16:00:00', 'USD'),
    ('LSE', 'London Stock Exchange', 'Europe/London', '08:00:00', '16:30:00', 'GBP'),
    ('TSE', 'Tokyo Stock Exchange', 'Asia/Tokyo', '09:00:00', '15:00:00', 'JPY'),
    ('FRA', 'Frankfurt Stock Exchange', 'Europe/Berlin', '09:00:00', '17:30:00', 'EUR')
ON CONFLICT (code) DO NOTHING;

-- Insert sample cryptocurrencies
INSERT INTO market_data.cryptocurrencies (symbol, name, market_cap, circulating_supply) VALUES
    ('BTC', 'Bitcoin', 500000000000, 19500000.00000000),
    ('ETH', 'Ethereum', 200000000000, 120000000.00000000),
    ('ADA', 'Cardano', 15000000000, 35000000000.00000000),
    ('SOL', 'Solana', 8000000000, 400000000.00000000),
    ('AVAX', 'Avalanche', 6000000000, 350000000.00000000)
ON CONFLICT (symbol) DO NOTHING;

-- Insert sample forex pairs
INSERT INTO market_data.forex_pairs (symbol, base_currency, quote_currency, is_major) VALUES
    ('EUR/USD', 'EUR', 'USD', true),
    ('GBP/USD', 'GBP', 'USD', true),
    ('USD/JPY', 'USD', 'JPY', true),
    ('USD/CHF', 'USD', 'CHF', true),
    ('AUD/USD', 'AUD', 'USD', true),
    ('USD/CAD', 'USD', 'CAD', true),
    ('NZD/USD', 'NZD', 'USD', true),
    ('EUR/GBP', 'EUR', 'GBP', false),
    ('EUR/JPY', 'EUR', 'JPY', false),
    ('GBP/JPY', 'GBP', 'JPY', false)
ON CONFLICT (symbol) DO NOTHING;

-- Insert sample commodities
INSERT INTO market_data.commodities (symbol, name, asset_class, unit, contract_size) VALUES
    ('XAU/USD', 'Gold', 'Metals', 'Troy Ounce', 100.0000),
    ('XAG/USD', 'Silver', 'Metals', 'Troy Ounce', 5000.0000),
    ('WTI', 'Crude Oil WTI', 'Energy', 'Barrel', 1000.0000),
    ('BRENT', 'Brent Crude Oil', 'Energy', 'Barrel', 1000.0000),
    ('NG', 'Natural Gas', 'Energy', 'MMBtu', 10000.0000),
    ('WHEAT', 'Wheat', 'Agriculture', 'Bushel', 5000.0000),
    ('CORN', 'Corn', 'Agriculture', 'Bushel', 5000.0000),
    ('COPPER', 'Copper', 'Metals', 'Pound', 25000.0000)
ON CONFLICT (symbol) DO NOTHING;

-- Create default portfolio (keeping original)
INSERT INTO portfolio.portfolios (id, name, description, initial_value) VALUES
    ('00000000-0000-0000-0000-000000000001', 'Default Portfolio', 'Default portfolio for testing', 100000.00)
ON CONFLICT (id) DO NOTHING;

-- Create some default alert rules (keeping original)
INSERT INTO alerts.alert_rules (id, name, alert_type, conditions, thresholds, notification_channels) VALUES
    (
        '00000000-0000-0000-0000-000000000001',
        'Price Drop Alert',
        'price_change',
        '{"field": "price_change_percent", "operator": "less_than"}',
        '{"value": -5.0, "timeframe": "5m"}',
        '["email", "dashboard"]'
    ),
    (
        '00000000-0000-0000-0000-000000000002',
        'High Volume Alert',
        'volume_spike',
        '{"field": "volume_change_percent", "operator": "greater_than"}',
        '{"value": 200.0, "timeframe": "15m"}',
        '["dashboard"]'
    ),
    (
        '00000000-0000-0000-0000-000000000003',
        'HFT Spread Alert',
        'spread_widening',
        '{"field": "bid_ask_spread_bps", "operator": "greater_than"}',
        '{"value": 50.0, "timeframe": "1m"}',
        '["dashboard", "sms"]'
    )
ON CONFLICT (id) DO NOTHING;

-- =====================================================
-- FUNCTIONS AND TRIGGERS
-- =====================================================

-- Function to update timestamps (keeping original)
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at (keeping original + new ones)
CREATE TRIGGER update_exchanges_updated_at BEFORE UPDATE ON market_data.exchanges 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_stocks_updated_at BEFORE UPDATE ON market_data.stocks 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_cryptocurrencies_updated_at BEFORE UPDATE ON market_data.cryptocurrencies 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_forex_pairs_updated_at BEFORE UPDATE ON market_data.forex_pairs 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_commodities_updated_at BEFORE UPDATE ON market_data.commodities 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_portfolios_updated_at BEFORE UPDATE ON portfolio.portfolios 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_alert_rules_updated_at BEFORE UPDATE ON alerts.alert_rules 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- NEW: Function to get latest tick price for any asset
CREATE OR REPLACE FUNCTION get_latest_tick_price(p_asset_id INTEGER, p_asset_type VARCHAR(20))
RETURNS DECIMAL(20,8) AS $$
DECLARE
    latest_price DECIMAL(20,8);
BEGIN
    SELECT price INTO latest_price
    FROM market_data.tick_data
    WHERE asset_id = p_asset_id AND asset_type = p_asset_type
    ORDER BY timestamp DESC
    LIMIT 1;
    
    RETURN COALESCE(latest_price, 0);
END;
$$ LANGUAGE plpgsql;

-- NEW: Function to calculate spread statistics
CREATE OR REPLACE FUNCTION calculate_spread_stats(p_asset_id INTEGER, p_asset_type VARCHAR(20), p_minutes INTEGER DEFAULT 5)
RETURNS TABLE(
    avg_spread_bps DECIMAL(10,4),
    max_spread_bps DECIMAL(10,4),
    min_spread_bps DECIMAL(10,4),
    spread_volatility DECIMAL(10,4)
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        AVG(mf.bid_ask_spread_bps) as avg_spread_bps,
        MAX(mf.bid_ask_spread_bps) as max_spread_bps,
        MIN(mf.bid_ask_spread_bps) as min_spread_bps,
        STDDEV(mf.bid_ask_spread_bps) as spread_volatility
    FROM analytics.microstructure_features mf
    WHERE mf.asset_id = p_asset_id 
      AND mf.asset_type = p_asset_type
      AND mf.timestamp >= (NOW() - (p_minutes || ' minutes')::INTERVAL);
END;
$$ LANGUAGE plpgsql;

-- Function to calculate portfolio metrics (keeping original)
CREATE OR REPLACE FUNCTION calculate_portfolio_value(p_portfolio_id UUID)
RETURNS TABLE(
    total_value DECIMAL(20,4),
    total_cost DECIMAL(20,4),
    unrealized_pnl DECIMAL(20,4),
    realized_pnl DECIMAL(20,4)
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COALESCE(SUM(pos.market_value), 0) as total_value,
        COALESCE(SUM(pos.quantity * pos.average_cost), 0) as total_cost,
        COALESCE(SUM(pos.unrealized_pnl), 0) as unrealized_pnl,
        COALESCE(SUM(pos.realized_pnl), 0) as realized_pnl
    FROM portfolio.positions pos
    WHERE pos.portfolio_id = p_portfolio_id;
END;
$$ LANGUAGE plpgsql;

-- Function to get latest stock price (keeping original)
CREATE OR REPLACE FUNCTION get_latest_stock_price(p_stock_id INTEGER)
RETURNS DECIMAL(15,4) AS $$
DECLARE
    latest_price DECIMAL(15,4);
BEGIN
    SELECT close_price INTO latest_price
    FROM market_data.stock_prices
    WHERE stock_id = p_stock_id
    ORDER BY timestamp DESC
    LIMIT 1;
    
    RETURN COALESCE(latest_price, 0);
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- VIEWS FOR COMMON QUERIES
-- =====================================================

-- Portfolio summary view (keeping original)
CREATE OR REPLACE VIEW portfolio.portfolio_summary AS
SELECT 
    p.id,
    p.name,
    p.currency,
    p.initial_value,
    (calculate_portfolio_value(p.id)).total_value as current_value,
    (calculate_portfolio_value(p.id)).unrealized_pnl as unrealized_pnl,
    (calculate_portfolio_value(p.id)).realized_pnl as realized_pnl,
    ((calculate_portfolio_value(p.id)).total_value - p.initial_value) / p.initial_value * 100 as total_return_percent,
    COUNT(pos.id) as position_count,
    p.created_at,
    p.updated_at
FROM portfolio.portfolios p
LEFT JOIN portfolio.positions pos ON p.id = pos.portfolio_id
WHERE p.is_active = true
GROUP BY p.id, p.name, p.currency, p.initial_value, p.created_at, p.updated_at;

-- Latest prices view (keeping original)
CREATE OR REPLACE VIEW market_data.latest_prices AS
SELECT DISTINCT ON (sp.stock_id)
    sp.stock_id,
    s.symbol,
    e.code as exchange,
    sp.close_price,
    sp.volume,
    sp.timestamp,
    LAG(sp.close_price) OVER (PARTITION BY sp.stock_id ORDER BY sp.timestamp) as previous_price
FROM market_data.stock_prices sp
JOIN market_data.stocks s ON sp.stock_id = s.id
JOIN market_data.exchanges e ON s.exchange_id = e.id
WHERE s.is_active = true
ORDER BY sp.stock_id, sp.timestamp DESC;

-- NEW: Latest tick prices view for all assets
CREATE OR REPLACE VIEW market_data.latest_tick_prices AS
SELECT DISTINCT ON (td.asset_id, td.asset_type)
    td.asset_id,
    td.asset_type,
    CASE 
        WHEN td.asset_type = 'stock' THEN s.symbol
        WHEN td.asset_type = 'crypto' THEN c.symbol
        WHEN td.asset_type = 'forex' THEN f.symbol
        WHEN td.asset_type = 'commodity' THEN cm.symbol
    END as symbol,
    td.price as latest_price,
    td.volume,
    td.aggressor_side,
    td.timestamp as last_trade_time,
    LAG(td.price) OVER (PARTITION BY td.asset_id, td.asset_type ORDER BY td.timestamp) as previous_price
FROM market_data.tick_data td
LEFT JOIN market_data.stocks s ON td.asset_id = s.id AND td.asset_type = 'stock'
LEFT JOIN market_data.cryptocurrencies c ON td.asset_id = c.id AND td.asset_type = 'crypto'
LEFT JOIN market_data.forex_pairs f ON td.asset_id = f.id AND td.asset_type = 'forex'
LEFT JOIN market_data.commodities cm ON td.asset_id = cm.id AND td.asset_type = 'commodity'
ORDER BY td.asset_id, td.asset_type, td.timestamp DESC;

-- NEW: Real-time spread monitoring view
CREATE OR REPLACE VIEW analytics.current_spreads AS
SELECT DISTINCT ON (mf.asset_id, mf.asset_type)
    mf.asset_id,
    mf.asset_type,
    CASE 
        WHEN mf.asset_type = 'stock' THEN s.symbol
        WHEN mf.asset_type = 'crypto' THEN c.symbol
        WHEN mf.asset_type = 'forex' THEN f.symbol
        WHEN mf.asset_type = 'commodity' THEN cm.symbol
    END as symbol,
    mf.bid_ask_spread,
    mf.bid_ask_spread_bps,
    mf.bid_ask_spread_percent,
    mf.mid_price,
    mf.order_flow_imbalance,
    mf.trade_intensity,
    mf.timestamp as last_update
FROM analytics.microstructure_features mf
LEFT JOIN market_data.stocks s ON mf.asset_id = s.id AND mf.asset_type = 'stock'
LEFT JOIN market_data.cryptocurrencies c ON mf.asset_id = c.id AND mf.asset_type = 'crypto'
LEFT JOIN market_data.forex_pairs f ON mf.asset_id = f.id AND mf.asset_type = 'forex'
LEFT JOIN market_data.commodities cm ON mf.asset_id = cm.id AND mf.asset_type = 'commodity'
WHERE mf.timestamp >= (NOW() - INTERVAL '5 minutes')
ORDER BY mf.asset_id, mf.asset_type, mf.timestamp DESC;

-- =====================================================
-- PERMISSIONS
-- =====================================================

-- Grant permissions to stock_user
GRANT USAGE ON SCHEMA market_data TO stock_user;
GRANT USAGE ON SCHEMA portfolio TO stock_user;
GRANT USAGE ON SCHEMA alerts TO stock_user;
GRANT USAGE ON SCHEMA analytics TO stock_user;
GRANT USAGE ON SCHEMA monitoring TO stock_user;

GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA market_data TO stock_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA portfolio TO stock_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA alerts TO stock_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA analytics TO stock_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA monitoring TO stock_user;

GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA market_data TO stock_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA portfolio TO stock_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA alerts TO stock_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA analytics TO stock_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA monitoring TO stock_user;

-- Create user for Grafana (read-only)
CREATE USER grafana_user WITH PASSWORD 'grafana_password';
GRANT CONNECT ON DATABASE stock_monitor TO grafana_user;
GRANT USAGE ON SCHEMA market_data, portfolio, alerts, analytics, monitoring TO grafana_user;
GRANT SELECT ON ALL TABLES IN SCHEMA market_data, portfolio, alerts, analytics, monitoring TO grafana_user;

COMMIT;
















