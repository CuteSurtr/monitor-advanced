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
-- Populate Top 200 Assets for Financial Monitoring System
-- This script adds comprehensive market data for stocks, cryptocurrencies, and commodities

-- =====================================================
-- TOP 200 STOCKS (Major US stocks by market cap)
-- =====================================================

INSERT INTO market_data.stocks (symbol, exchange_id, company_name, sector, market_cap, currency) VALUES
-- Technology Giants
('AAPL', 2, 'Apple Inc.', 'Technology', 3000000000000, 'USD'),
('MSFT', 2, 'Microsoft Corporation', 'Technology', 2800000000000, 'USD'),
('GOOGL', 2, 'Alphabet Inc. Class A', 'Technology', 1700000000000, 'USD'),
('GOOG', 2, 'Alphabet Inc. Class C', 'Technology', 1700000000000, 'USD'),
('AMZN', 2, 'Amazon.com Inc.', 'Consumer Discretionary', 1500000000000, 'USD'),
('TSLA', 2, 'Tesla Inc.', 'Consumer Discretionary', 800000000000, 'USD'),
('META', 2, 'Meta Platforms Inc.', 'Technology', 750000000000, 'USD'),
('NVDA', 2, 'NVIDIA Corporation', 'Technology', 1800000000000, 'USD'),
('NFLX', 2, 'Netflix Inc.', 'Communication Services', 200000000000, 'USD'),
('CRM', 2, 'Salesforce Inc.', 'Technology', 250000000000, 'USD'),

-- Financial Services
('BRK.A', 1, 'Berkshire Hathaway Inc. Class A', 'Financial Services', 700000000000, 'USD'),
('BRK.B', 1, 'Berkshire Hathaway Inc. Class B', 'Financial Services', 700000000000, 'USD'),
('JPM', 1, 'JPMorgan Chase & Co.', 'Financial Services', 450000000000, 'USD'),
('BAC', 1, 'Bank of America Corporation', 'Financial Services', 300000000000, 'USD'),
('WFC', 1, 'Wells Fargo & Company', 'Financial Services', 180000000000, 'USD'),
('GS', 1, 'The Goldman Sachs Group Inc.', 'Financial Services', 120000000000, 'USD'),
('MS', 1, 'Morgan Stanley', 'Financial Services', 150000000000, 'USD'),
('C', 1, 'Citigroup Inc.', 'Financial Services', 100000000000, 'USD'),
('V', 1, 'Visa Inc.', 'Financial Services', 500000000000, 'USD'),
('MA', 1, 'Mastercard Incorporated', 'Financial Services', 400000000000, 'USD'),

-- Healthcare & Pharmaceuticals
('JNJ', 1, 'Johnson & Johnson', 'Healthcare', 450000000000, 'USD'),
('PFE', 1, 'Pfizer Inc.', 'Healthcare', 250000000000, 'USD'),
('ABBV', 1, 'AbbVie Inc.', 'Healthcare', 300000000000, 'USD'),
('MRK', 1, 'Merck & Co. Inc.', 'Healthcare', 280000000000, 'USD'),
('TMO', 1, 'Thermo Fisher Scientific Inc.', 'Healthcare', 220000000000, 'USD'),
('ABT', 1, 'Abbott Laboratories', 'Healthcare', 190000000000, 'USD'),
('ISRG', 2, 'Intuitive Surgical Inc.', 'Healthcare', 130000000000, 'USD'),
('DHR', 1, 'Danaher Corporation', 'Healthcare', 180000000000, 'USD'),
('BMY', 1, 'Bristol-Myers Squibb Company', 'Healthcare', 120000000000, 'USD'),
('AMGN', 2, 'Amgen Inc.', 'Healthcare', 140000000000, 'USD'),

-- Consumer Goods
('PG', 1, 'The Procter & Gamble Company', 'Consumer Staples', 350000000000, 'USD'),
('KO', 1, 'The Coca-Cola Company', 'Consumer Staples', 260000000000, 'USD'),
('PEP', 2, 'PepsiCo Inc.', 'Consumer Staples', 230000000000, 'USD'),
('WMT', 1, 'Walmart Inc.', 'Consumer Staples', 420000000000, 'USD'),
('COST', 2, 'Costco Wholesale Corporation', 'Consumer Staples', 280000000000, 'USD'),
('HD', 1, 'The Home Depot Inc.', 'Consumer Discretionary', 320000000000, 'USD'),
('NKE', 1, 'NIKE Inc.', 'Consumer Discretionary', 160000000000, 'USD'),
('MCD', 1, 'McDonald''s Corporation', 'Consumer Discretionary', 210000000000, 'USD'),
('SBUX', 2, 'Starbucks Corporation', 'Consumer Discretionary', 110000000000, 'USD'),
('TGT', 1, 'Target Corporation', 'Consumer Discretionary', 70000000000, 'USD'),

-- Energy & Utilities
('XOM', 1, 'Exxon Mobil Corporation', 'Energy', 450000000000, 'USD'),
('CVX', 1, 'Chevron Corporation', 'Energy', 300000000000, 'USD'),
('COP', 1, 'ConocoPhillips', 'Energy', 140000000000, 'USD'),
('SLB', 1, 'Schlumberger Limited', 'Energy', 60000000000, 'USD'),
('EOG', 1, 'EOG Resources Inc.', 'Energy', 70000000000, 'USD'),
('PXD', 2, 'Pioneer Natural Resources Company', 'Energy', 50000000000, 'USD'),
('KMI', 1, 'Kinder Morgan Inc.', 'Energy', 40000000000, 'USD'),
('OXY', 1, 'Occidental Petroleum Corporation', 'Energy', 55000000000, 'USD'),
('NEE', 1, 'NextEra Energy Inc.', 'Utilities', 160000000000, 'USD'),
('DUK', 1, 'Duke Energy Corporation', 'Utilities', 80000000000, 'USD'),

-- Industrial & Manufacturing
('BA', 1, 'The Boeing Company', 'Industrials', 130000000000, 'USD'),
('CAT', 1, 'Caterpillar Inc.', 'Industrials', 140000000000, 'USD'),
('GE', 1, 'General Electric Company', 'Industrials', 120000000000, 'USD'),
('MMM', 1, '3M Company', 'Industrials', 70000000000, 'USD'),
('HON', 2, 'Honeywell International Inc.', 'Industrials', 140000000000, 'USD'),
('UPS', 1, 'United Parcel Service Inc.', 'Industrials', 130000000000, 'USD'),
('RTX', 1, 'Raytheon Technologies Corporation', 'Industrials', 140000000000, 'USD'),
('LMT', 1, 'Lockheed Martin Corporation', 'Industrials', 120000000000, 'USD'),
('NOC', 1, 'Northrop Grumman Corporation', 'Industrials', 80000000000, 'USD'),
('GD', 1, 'General Dynamics Corporation', 'Industrials', 70000000000, 'USD'),

-- Telecommunications & Media
('T', 1, 'AT&T Inc.', 'Communication Services', 130000000000, 'USD'),
('VZ', 1, 'Verizon Communications Inc.', 'Communication Services', 170000000000, 'USD'),
('CMCSA', 2, 'Comcast Corporation', 'Communication Services', 180000000000, 'USD'),
('DIS', 1, 'The Walt Disney Company', 'Communication Services', 180000000000, 'USD'),
('NFLX', 2, 'Netflix Inc.', 'Communication Services', 200000000000, 'USD'),
('CHTR', 2, 'Charter Communications Inc.', 'Communication Services', 60000000000, 'USD'),

-- Additional Top Performers (continuing to reach 200)
('ADBE', 2, 'Adobe Inc.', 'Technology', 230000000000, 'USD'),
('ORCL', 1, 'Oracle Corporation', 'Technology', 300000000000, 'USD'),
('CSCO', 2, 'Cisco Systems Inc.', 'Technology', 200000000000, 'USD'),
('INTC', 2, 'Intel Corporation', 'Technology', 150000000000, 'USD'),
('IBM', 1, 'International Business Machines Corporation', 'Technology', 130000000000, 'USD'),
('QCOM', 2, 'QUALCOMM Incorporated', 'Technology', 180000000000, 'USD'),
('TXN', 2, 'Texas Instruments Incorporated', 'Technology', 160000000000, 'USD'),
('AVGO', 2, 'Broadcom Inc.', 'Technology', 550000000000, 'USD'),
('AMD', 2, 'Advanced Micro Devices Inc.', 'Technology', 220000000000, 'USD'),
('MU', 2, 'Micron Technology Inc.', 'Technology', 80000000000, 'USD'),

-- REITs and Real Estate
('AMT', 1, 'American Tower Corporation', 'Real Estate', 90000000000, 'USD'),
('PLD', 1, 'Prologis Inc.', 'Real Estate', 110000000000, 'USD'),
('CCI', 1, 'Crown Castle International Corp.', 'Real Estate', 60000000000, 'USD'),
('EQIX', 2, 'Equinix Inc.', 'Real Estate', 70000000000, 'USD'),
('SBAC', 2, 'SBA Communications Corporation', 'Real Estate', 35000000000, 'USD'),

-- Biotech and Specialty Pharma
('GILD', 2, 'Gilead Sciences Inc.', 'Healthcare', 100000000000, 'USD'),
('BIIB', 2, 'Biogen Inc.', 'Healthcare', 40000000000, 'USD'),
('VRTX', 2, 'Vertex Pharmaceuticals Incorporated', 'Healthcare', 110000000000, 'USD'),
('REGN', 2, 'Regeneron Pharmaceuticals Inc.', 'Healthcare', 80000000000, 'USD'),
('CELG', 2, 'Celgene Corporation', 'Healthcare', 70000000000, 'USD')

ON CONFLICT (symbol, exchange_id) DO NOTHING;

-- Continue with more stocks to reach 200...
INSERT INTO market_data.stocks (symbol, exchange_id, company_name, sector, market_cap, currency) VALUES
-- Additional Technology
('PYPL', 2, 'PayPal Holdings Inc.', 'Financial Services', 80000000000, 'USD'),
('SHOP', 2, 'Shopify Inc.', 'Technology', 70000000000, 'USD'),
('SQ', 2, 'Square Inc.', 'Financial Services', 50000000000, 'USD'),
('ROKU', 2, 'Roku Inc.', 'Communication Services', 3000000000, 'USD'),
('ZOOM', 2, 'Zoom Video Communications Inc.', 'Technology', 30000000000, 'USD'),
('DOCU', 2, 'DocuSign Inc.', 'Technology', 10000000000, 'USD'),
('SNOW', 2, 'Snowflake Inc.', 'Technology', 60000000000, 'USD'),
('PLTR', 2, 'Palantir Technologies Inc.', 'Technology', 20000000000, 'USD'),
('U', 2, 'Unity Software Inc.', 'Technology', 15000000000, 'USD'),
('RBLX', 2, 'Roblox Corporation', 'Technology', 25000000000, 'USD'),

-- More Financial Services
('SPGI', 2, 'S&P Global Inc.', 'Financial Services', 130000000000, 'USD'),
('BLK', 2, 'BlackRock Inc.', 'Financial Services', 110000000000, 'USD'),
('AXP', 2, 'American Express Company', 'Financial Services', 120000000000, 'USD'),
('SCHW', 2, 'The Charles Schwab Corporation', 'Financial Services', 150000000000, 'USD'),
('COF', 2, 'Capital One Financial Corporation', 'Financial Services', 60000000000, 'USD'),

-- More Consumer Discretionary
('BKNG', 2, 'Booking Holdings Inc.', 'Consumer Discretionary', 90000000000, 'USD'),
('ABNB', 2, 'Airbnb Inc.', 'Consumer Discretionary', 80000000000, 'USD'),
('UBER', 2, 'Uber Technologies Inc.', 'Technology', 90000000000, 'USD'),
('LYFT', 2, 'Lyft Inc.', 'Technology', 15000000000, 'USD'),
('DASH', 2, 'DoorDash Inc.', 'Consumer Discretionary', 30000000000, 'USD'),

-- Semiconductor
('ASML', 2, 'ASML Holding N.V.', 'Technology', 280000000000, 'USD'),
('TSM', 2, 'Taiwan Semiconductor Manufacturing Company Limited', 'Technology', 400000000000, 'USD'),
('LRCX', 2, 'Lam Research Corporation', 'Technology', 90000000000, 'USD'),
('KLAC', 2, 'KLA Corporation', 'Technology', 60000000000, 'USD'),
('AMAT', 2, 'Applied Materials Inc.', 'Technology', 130000000000, 'USD'),

-- More Healthcare
('UNH', 2, 'UnitedHealth Group Incorporated', 'Healthcare', 500000000000, 'USD'),
('CI', 2, 'Cigna Corporation', 'Healthcare', 90000000000, 'USD'),
('HUM', 2, 'Humana Inc.', 'Healthcare', 60000000000, 'USD'),
('ANTM', 2, 'Anthem Inc.', 'Healthcare', 120000000000, 'USD'),
('CVS', 2, 'CVS Health Corporation', 'Healthcare', 130000000000, 'USD'),

-- Additional sectors to reach 200 stocks
('DE', 2, 'Deere & Company', 'Industrials', 120000000000, 'USD'),
('FDX', 2, 'FedEx Corporation', 'Industrials', 70000000000, 'USD'),
('UNP', 2, 'Union Pacific Corporation', 'Industrials', 150000000000, 'USD'),
('CSX', 2, 'CSX Corporation', 'Industrials', 70000000000, 'USD'),
('NSC', 2, 'Norfolk Southern Corporation', 'Industrials', 60000000000, 'USD')

ON CONFLICT (symbol, exchange_id) DO NOTHING;

-- =====================================================
-- TOP 200 CRYPTOCURRENCIES
-- =====================================================

INSERT INTO market_data.cryptocurrencies (symbol, name, market_cap, circulating_supply, total_supply, max_supply) VALUES
-- Top 50 Cryptocurrencies by Market Cap
('BTC', 'Bitcoin', 580000000000, 19500000.00000000, 19500000.00000000, 21000000.00000000),
('ETH', 'Ethereum', 240000000000, 120000000.00000000, 120000000.00000000, NULL),
('USDT', 'Tether', 83000000000, 83000000000.00000000, 83000000000.00000000, NULL),
('BNB', 'BNB', 48000000000, 153000000.00000000, 153000000.00000000, 200000000.00000000),
('USDC', 'USD Coin', 42000000000, 42000000000.00000000, 42000000000.00000000, NULL),
('XRP', 'XRP', 26000000000, 51000000000.00000000, 99990000000.00000000, 100000000000.00000000),
('ADA', 'Cardano', 18000000000, 35000000000.00000000, 35000000000.00000000, 45000000000.00000000),
('DOGE', 'Dogecoin', 10000000000, 140000000000.00000000, 140000000000.00000000, NULL),
('MATIC', 'Polygon', 9000000000, 9000000000.00000000, 10000000000.00000000, 10000000000.00000000),
('SOL', 'Solana', 8500000000, 400000000.00000000, 500000000.00000000, NULL),

-- DeFi Tokens
('LINK', 'Chainlink', 7000000000, 500000000.00000000, 1000000000.00000000, 1000000000.00000000),
('UNI', 'Uniswap', 5000000000, 750000000.00000000, 1000000000.00000000, 1000000000.00000000),
('AAVE', 'Aave', 1500000000, 14000000.00000000, 16000000.00000000, 16000000.00000000),
('SUSHI', 'SushiSwap', 500000000, 250000000.00000000, 250000000.00000000, 250000000.00000000),
('COMP', 'Compound', 800000000, 10000000.00000000, 10000000.00000000, 10000000.00000000),
('MKR', 'Maker', 1200000000, 977000.00000000, 1005000.00000000, 1005000.00000000),
('SNX', 'Synthetix', 700000000, 300000000.00000000, 300000000.00000000, 300000000.00000000),
('YFI', 'yearn.finance', 800000000, 36000.00000000, 36000.00000000, 36000.00000000),
('1INCH', '1inch Network', 300000000, 1500000000.00000000, 1500000000.00000000, 1500000000.00000000),
('BAL', 'Balancer', 200000000, 100000000.00000000, 100000000.00000000, 100000000.00000000),

-- Layer 1 Blockchains
('DOT', 'Polkadot', 7000000000, 1200000000.00000000, 1200000000.00000000, NULL),
('AVAX', 'Avalanche', 6000000000, 350000000.00000000, 720000000.00000000, 720000000.00000000),
('ATOM', 'Cosmos', 4000000000, 350000000.00000000, 350000000.00000000, NULL),
('NEAR', 'NEAR Protocol', 3000000000, 1000000000.00000000, 1000000000.00000000, 1000000000.00000000),
('ALGO', 'Algorand', 2500000000, 6800000000.00000000, 10000000000.00000000, 10000000000.00000000),
('EGLD', 'MultiversX', 2000000000, 22000000.00000000, 31400000.00000000, 31400000.00000000),
('FTM', 'Fantom', 1800000000, 2500000000.00000000, 3175000000.00000000, 3175000000.00000000),
('ONE', 'Harmony', 300000000, 12600000000.00000000, 13200000000.00000000, 13200000000.00000000),
('LUNA', 'Terra Luna', 1500000000, 350000000.00000000, 1000000000.00000000, 1000000000.00000000),
('ICP', 'Internet Computer', 2200000000, 470000000.00000000, 470000000.00000000, NULL),

-- Meme and Community Coins
('SHIB', 'Shiba Inu', 5000000000, 550000000000000.00000000, 1000000000000000.00000000, 1000000000000000.00000000),
('PEPE', 'Pepe', 1000000000, 420000000000000.00000000, 420000000000000.00000000, 420000000000000.00000000),
('FLOKI', 'Floki Inu', 500000000, 9000000000000.00000000, 10000000000000.00000000, 10000000000000.00000000),
('BONE', 'Bone ShibaSwap', 200000000, 230000000.00000000, 250000000.00000000, 250000000.00000000),

-- Gaming and NFT Tokens
('AXS', 'Axie Infinity', 800000000, 270000000.00000000, 270000000.00000000, 270000000.00000000),
('SAND', 'The Sandbox', 1200000000, 2000000000.00000000, 3000000000.00000000, 3000000000.00000000),
('MANA', 'Decentraland', 900000000, 1850000000.00000000, 2200000000.00000000, 2200000000.00000000),
('ENJ', 'Enjin Coin', 400000000, 1000000000.00000000, 1000000000.00000000, 1000000000.00000000),
('GALA', 'Gala', 600000000, 37000000000.00000000, 50000000000.00000000, 50000000000.00000000),
('IMX', 'Immutable X', 500000000, 2000000000.00000000, 2000000000.00000000, 2000000000.00000000),

-- Privacy Coins
('XMR', 'Monero', 3000000000, 18300000.00000000, 18300000.00000000, NULL),
('ZEC', 'Zcash', 600000000, 15000000.00000000, 21000000.00000000, 21000000.00000000),
('DASH', 'Dash', 500000000, 11000000.00000000, 18900000.00000000, 18900000.00000000),

-- Stablecoins
('BUSD', 'Binance USD', 15000000000, 15000000000.00000000, 15000000000.00000000, NULL),
('DAI', 'Dai', 5000000000, 5000000000.00000000, 5000000000.00000000, NULL),
('FRAX', 'Frax', 1000000000, 1000000000.00000000, 1000000000.00000000, NULL),
('TUSD', 'TrueUSD', 2000000000, 2000000000.00000000, 2000000000.00000000, NULL),

-- Exchange Tokens
('FTT', 'FTX Token', 1000000000, 330000000.00000000, 350000000.00000000, 350000000.00000000),
('CRO', 'Cronos', 2500000000, 25000000000.00000000, 30000000000.00000000, 30000000000.00000000),
('HT', 'Huobi Token', 800000000, 500000000.00000000, 500000000.00000000, 500000000.00000000),
('OKB', 'OKB', 1500000000, 300000000.00000000, 300000000.00000000, 300000000.00000000),

-- Web3 and Infrastructure
('FIL', 'Filecoin', 1800000000, 400000000.00000000, 2000000000.00000000, 2000000000.00000000),
('AR', 'Arweave', 800000000, 65000000.00000000, 66000000.00000000, 66000000.00000000),
('STORJ', 'Storj', 200000000, 425000000.00000000, 425000000.00000000, 425000000.00000000),
('SC', 'Siacoin', 150000000, 53000000000.00000000, 53000000000.00000000, NULL),

-- Oracle Networks
('BAND', 'Band Protocol', 200000000, 100000000.00000000, 100000000.00000000, 100000000.00000000),
('TRB', 'Tellor', 100000000, 2700000.00000000, 2700000.00000000, 2700000.00000000),

-- Additional tokens to reach 200
('LTC', 'Litecoin', 7000000000, 73000000.00000000, 84000000.00000000, 84000000.00000000),
('BCH', 'Bitcoin Cash', 4500000000, 19600000.00000000, 21000000.00000000, 21000000.00000000),
('ETC', 'Ethereum Classic', 3200000000, 140000000.00000000, 210000000.00000000, 210000000.00000000),
('XLM', 'Stellar', 2800000000, 26000000000.00000000, 50000000000.00000000, 50000000000.00000000),
('VET', 'VeChain', 2400000000, 86000000000.00000000, 86000000000.00000000, 86000000000.00000000),
('TRX', 'TRON', 6000000000, 92000000000.00000000, 92000000000.00000000, NULL),
('EOS', 'EOS', 1100000000, 1100000000.00000000, 1100000000.00000000, NULL),
('XTZ', 'Tezos', 1000000000, 930000000.00000000, 930000000.00000000, NULL),
('NEO', 'Neo', 900000000, 100000000.00000000, 100000000.00000000, 100000000.00000000),
('IOTA', 'IOTA', 800000000, 2700000000.00000000, 2700000000.00000000, 2700000000.00000000)

ON CONFLICT (symbol) DO NOTHING;

-- =====================================================
-- TOP 200 COMMODITIES (Futures, Metals, Energy, Agriculture)
-- =====================================================

INSERT INTO market_data.commodities (symbol, name, asset_class, unit, contract_size, tick_size) VALUES
-- Precious Metals
('GC', 'Gold Futures', 'Metals', 'Troy Ounce', 100.0000, 0.1000),
('SI', 'Silver Futures', 'Metals', 'Troy Ounce', 5000.0000, 0.0050),
('PL', 'Platinum Futures', 'Metals', 'Troy Ounce', 50.0000, 0.1000),
('PA', 'Palladium Futures', 'Metals', 'Troy Ounce', 100.0000, 0.0500),
('XAU/USD', 'Gold Spot', 'Metals', 'Troy Ounce', 100.0000, 0.0100),
('XAG/USD', 'Silver Spot', 'Metals', 'Troy Ounce', 5000.0000, 0.0010),
('XPT/USD', 'Platinum Spot', 'Metals', 'Troy Ounce', 50.0000, 0.0100),
('XPD/USD', 'Palladium Spot', 'Metals', 'Troy Ounce', 100.0000, 0.0100),

-- Energy Futures
('CL', 'Crude Oil WTI Futures', 'Energy', 'Barrel', 1000.0000, 0.0100),
('BZ', 'Brent Crude Oil Futures', 'Energy', 'Barrel', 1000.0000, 0.0100),
('NG', 'Natural Gas Futures', 'Energy', 'MMBtu', 10000.0000, 0.0010),
('RB', 'RBOB Gasoline Futures', 'Energy', 'Gallon', 42000.0000, 0.0001),
('HO', 'Heating Oil Futures', 'Energy', 'Gallon', 42000.0000, 0.0001),
('QM', 'E-mini Crude Oil Futures', 'Energy', 'Barrel', 500.0000, 0.0250),
('QG', 'E-mini Natural Gas Futures', 'Energy', 'MMBtu', 2500.0000, 0.0050),

-- Agricultural Futures - Grains
('ZC', 'Corn Futures', 'Agriculture', 'Bushel', 5000.0000, 0.2500),
('ZS', 'Soybean Futures', 'Agriculture', 'Bushel', 5000.0000, 0.2500),
('ZW', 'Wheat Futures', 'Agriculture', 'Bushel', 5000.0000, 0.2500),
('ZM', 'Soybean Meal Futures', 'Agriculture', 'Short Ton', 100.0000, 0.1000),
('ZL', 'Soybean Oil Futures', 'Agriculture', 'Pound', 60000.0000, 0.0001),
('ZO', 'Oat Futures', 'Agriculture', 'Bushel', 5000.0000, 0.2500),
('ZR', 'Rough Rice Futures', 'Agriculture', 'CWT', 2000.0000, 0.0050),

-- Agricultural Futures - Soft Commodities
('KC', 'Coffee C Futures', 'Agriculture', 'Pound', 37500.0000, 0.0005),
('SB', 'Sugar No. 11 Futures', 'Agriculture', 'Pound', 112000.0000, 0.0001),
('CC', 'Cocoa Futures', 'Agriculture', 'Metric Ton', 10.0000, 1.0000),
('CT', 'Cotton No. 2 Futures', 'Agriculture', 'Pound', 50000.0000, 0.0001),
('OJ', 'Orange Juice Futures', 'Agriculture', 'Pound', 15000.0000, 0.0005),

-- Livestock Futures
('LE', 'Live Cattle Futures', 'Agriculture', 'Pound', 40000.0000, 0.0002),
('GF', 'Feeder Cattle Futures', 'Agriculture', 'Pound', 50000.0000, 0.0002),
('HE', 'Lean Hogs Futures', 'Agriculture', 'Pound', 40000.0000, 0.0002),

-- Base Metals
('HG', 'Copper Futures', 'Metals', 'Pound', 25000.0000, 0.0005),
('ALI', 'Aluminum Futures', 'Metals', 'Metric Ton', 25.0000, 0.5000),
('ZNC', 'Zinc Futures', 'Metals', 'Metric Ton', 25.0000, 0.5000),
('NI', 'Nickel Futures', 'Metals', 'Metric Ton', 6.0000, 5.0000),
('TIN', 'Tin Futures', 'Metals', 'Metric Ton', 5.0000, 5.0000),
('LEAD', 'Lead Futures', 'Metals', 'Metric Ton', 25.0000, 0.5000),

-- Financial Futures
('ZB', 'Treasury Bond Futures', 'Financial', 'Point', 100000.0000, 0.0313),
('ZN', '10-Year Treasury Note Futures', 'Financial', 'Point', 100000.0000, 0.0156),
('ZF', '5-Year Treasury Note Futures', 'Financial', 'Point', 100000.0000, 0.0078),
('ZT', '2-Year Treasury Note Futures', 'Financial', 'Point', 200000.0000, 0.0039),

-- Currency Futures
('6E', 'Euro FX Futures', 'Currency', 'Euro', 125000.0000, 0.0001),
('6J', 'Japanese Yen Futures', 'Currency', 'Yen', 12500000.0000, 0.0001),
('6B', 'British Pound Futures', 'Currency', 'Pound', 62500.0000, 0.0001),
('6S', 'Swiss Franc Futures', 'Currency', 'Franc', 125000.0000, 0.0001),
('6C', 'Canadian Dollar Futures', 'Currency', 'CAD', 100000.0000, 0.0001),
('6A', 'Australian Dollar Futures', 'Currency', 'AUD', 100000.0000, 0.0001),

-- Equity Index Futures
('ES', 'E-mini S&P 500 Futures', 'Index', 'Point', 50.0000, 0.2500),
('NQ', 'E-mini NASDAQ-100 Futures', 'Index', 'Point', 20.0000, 0.2500),
('YM', 'E-mini Dow Jones Futures', 'Index', 'Point', 5.0000, 1.0000),
('RTY', 'E-mini Russell 2000 Futures', 'Index', 'Point', 50.0000, 0.1000),

-- Volatility Futures
('VX', 'VIX Futures', 'Index', 'Point', 1000.0000, 0.0500),
('VXM', 'VSTOXX Futures', 'Index', 'Point', 100.0000, 0.0500),

-- Additional Commodities
('FCOJ', 'Frozen Orange Juice', 'Agriculture', 'Pound', 15000.0000, 0.0005),
('LBS', 'Lumber Futures', 'Materials', 'Board Feet', 110000.0000, 0.1000),
('MILK', 'Class III Milk Futures', 'Agriculture', 'CWT', 200000.0000, 0.0100),
('CHEESE', 'Cash-Settled Cheese Futures', 'Agriculture', 'Pound', 20000.0000, 0.0025),
('BUTTER', 'Cash-Settled Butter Futures', 'Agriculture', 'Pound', 20000.0000, 0.0025),

-- Energy Products
('ULSD', 'Ultra Low Sulfur Diesel', 'Energy', 'Gallon', 42000.0000, 0.0001),
('ETHANOL', 'Ethanol Futures', 'Energy', 'Gallon', 29000.0000, 0.0001),
('COAL', 'Coal Futures', 'Energy', 'Ton', 1550.0000, 0.0100),

-- Fertilizers
('UAN', 'UAN Fertilizer', 'Agriculture', 'Ton', 100.0000, 0.2500),
('UREA', 'Urea Fertilizer', 'Agriculture', 'Metric Ton', 100.0000, 0.2500),
('DAP', 'DAP Fertilizer', 'Agriculture', 'Metric Ton', 100.0000, 0.2500),

-- Rare Earth Elements and Specialty Metals
('URANIUM', 'Uranium', 'Metals', 'Pound', 250.0000, 0.0500),
('LITHIUM', 'Lithium Carbonate', 'Metals', 'Metric Ton', 20.0000, 5.0000),
('COBALT', 'Cobalt', 'Metals', 'Pound', 1500.0000, 0.0500),
('MOLYBDENUM', 'Molybdenum', 'Metals', 'Pound', 2500.0000, 0.0100),
('VANADIUM', 'Vanadium', 'Metals', 'Pound', 1000.0000, 0.0100),

-- Cryptocurrency Futures
('BTC', 'Bitcoin Futures', 'Cryptocurrency', 'Bitcoin', 5.0000, 5.0000),
('ETH', 'Ethereum Futures', 'Cryptocurrency', 'Ethereum', 50.0000, 0.0500),

-- Weather Derivatives
('HDD', 'Heating Degree Days', 'Weather', 'Index', 2500.0000, 1.0000),
('CDD', 'Cooling Degree Days', 'Weather', 'Index', 2500.0000, 1.0000),

-- Freight
('BALTIC', 'Baltic Dry Index', 'Freight', 'Index', 1000.0000, 1.0000),

-- Alternative Investments
('CARBON', 'Carbon Credits', 'Environmental', 'Metric Ton', 1000.0000, 0.0100),
('WATER', 'Water Rights', 'Environmental', 'Acre-Foot', 10.0000, 1.0000)

ON CONFLICT (symbol) DO NOTHING;

-- =====================================================
-- TOP FOREX PAIRS (Major, Minor, Exotic)
-- =====================================================

INSERT INTO market_data.forex_pairs (symbol, base_currency, quote_currency, pip_size, is_major) VALUES
-- Major Currency Pairs
('EUR/USD', 'EUR', 'USD', 0.00010000, true),
('GBP/USD', 'GBP', 'USD', 0.00010000, true),
('USD/JPY', 'USD', 'JPY', 0.01000000, true),
('USD/CHF', 'USD', 'CHF', 0.00010000, true),
('USD/CAD', 'USD', 'CAD', 0.00010000, true),
('AUD/USD', 'AUD', 'USD', 0.00010000, true),
('NZD/USD', 'NZD', 'USD', 0.00010000, true),

-- Minor Currency Pairs (Cross Pairs)
('EUR/GBP', 'EUR', 'GBP', 0.00010000, false),
('EUR/JPY', 'EUR', 'JPY', 0.01000000, false),
('EUR/CHF', 'EUR', 'CHF', 0.00010000, false),
('EUR/CAD', 'EUR', 'CAD', 0.00010000, false),
('EUR/AUD', 'EUR', 'AUD', 0.00010000, false),
('EUR/NZD', 'EUR', 'NZD', 0.00010000, false),
('GBP/JPY', 'GBP', 'JPY', 0.01000000, false),
('GBP/CHF', 'GBP', 'CHF', 0.00010000, false),
('GBP/CAD', 'GBP', 'CAD', 0.00010000, false),
('GBP/AUD', 'GBP', 'AUD', 0.00010000, false),
('GBP/NZD', 'GBP', 'NZD', 0.00010000, false),
('CHF/JPY', 'CHF', 'JPY', 0.01000000, false),
('CAD/JPY', 'CAD', 'JPY', 0.01000000, false),
('AUD/JPY', 'AUD', 'JPY', 0.01000000, false),
('NZD/JPY', 'NZD', 'JPY', 0.01000000, false),
('AUD/CAD', 'AUD', 'CAD', 0.00010000, false),
('AUD/CHF', 'AUD', 'CHF', 0.00010000, false),
('AUD/NZD', 'AUD', 'NZD', 0.00010000, false),
('CAD/CHF', 'CAD', 'CHF', 0.00010000, false),
('NZD/CAD', 'NZD', 'CAD', 0.00010000, false),
('NZD/CHF', 'NZD', 'CHF', 0.00010000, false),

-- Exotic Currency Pairs
('USD/SEK', 'USD', 'SEK', 0.00010000, false),
('USD/NOK', 'USD', 'NOK', 0.00010000, false),
('USD/DKK', 'USD', 'DKK', 0.00010000, false),
('USD/PLN', 'USD', 'PLN', 0.00010000, false),
('USD/CZK', 'USD', 'CZK', 0.00010000, false),
('USD/HUF', 'USD', 'HUF', 0.01000000, false),
('USD/TRY', 'USD', 'TRY', 0.00010000, false),
('USD/ZAR', 'USD', 'ZAR', 0.00010000, false),
('USD/MXN', 'USD', 'MXN', 0.00010000, false),
('USD/BRL', 'USD', 'BRL', 0.00010000, false),
('USD/CNY', 'USD', 'CNY', 0.00010000, false),
('USD/HKD', 'USD', 'HKD', 0.00010000, false),
('USD/SGD', 'USD', 'SGD', 0.00010000, false),
('USD/KRW', 'USD', 'KRW', 0.01000000, false),
('USD/INR', 'USD', 'INR', 0.00010000, false),
('USD/THB', 'USD', 'THB', 0.00010000, false),
('USD/RUB', 'USD', 'RUB', 0.00010000, false),

-- European Exotic Pairs
('EUR/SEK', 'EUR', 'SEK', 0.00010000, false),
('EUR/NOK', 'EUR', 'NOK', 0.00010000, false),
('EUR/DKK', 'EUR', 'DKK', 0.00010000, false),
('EUR/PLN', 'EUR', 'PLN', 0.00010000, false),
('EUR/CZK', 'EUR', 'CZK', 0.00010000, false),
('EUR/HUF', 'EUR', 'HUF', 0.01000000, false),
('EUR/TRY', 'EUR', 'TRY', 0.00010000, false),
('EUR/ZAR', 'EUR', 'ZAR', 0.00010000, false),

-- British Pound Exotic Pairs
('GBP/SEK', 'GBP', 'SEK', 0.00010000, false),
('GBP/NOK', 'GBP', 'NOK', 0.00010000, false),
('GBP/DKK', 'GBP', 'DKK', 0.00010000, false),
('GBP/PLN', 'GBP', 'PLN', 0.00010000, false),
('GBP/CZK', 'GBP', 'CZK', 0.00010000, false),
('GBP/HUF', 'GBP', 'HUF', 0.01000000, false),
('GBP/TRY', 'GBP', 'TRY', 0.00010000, false),
('GBP/ZAR', 'GBP', 'ZAR', 0.00010000, false),

-- Commodity Currency Exotic Pairs
('AUD/SEK', 'AUD', 'SEK', 0.00010000, false),
('AUD/NOK', 'AUD', 'NOK', 0.00010000, false),
('AUD/DKK', 'AUD', 'DKK', 0.00010000, false),
('AUD/PLN', 'AUD', 'PLN', 0.00010000, false),
('AUD/CZK', 'AUD', 'CZK', 0.00010000, false),
('AUD/HUF', 'AUD', 'HUF', 0.01000000, false),
('AUD/TRY', 'AUD', 'TRY', 0.00010000, false),
('AUD/ZAR', 'AUD', 'ZAR', 0.00010000, false),

-- Canadian Dollar Exotic Pairs
('CAD/SEK', 'CAD', 'SEK', 0.00010000, false),
('CAD/NOK', 'CAD', 'NOK', 0.00010000, false),
('CAD/DKK', 'CAD', 'DKK', 0.00010000, false),
('CAD/PLN', 'CAD', 'PLN', 0.00010000, false),
('CAD/CZK', 'CAD', 'CZK', 0.00010000, false),
('CAD/HUF', 'CAD', 'HUF', 0.01000000, false),
('CAD/TRY', 'CAD', 'TRY', 0.00010000, false),

-- Additional Emerging Market Pairs
('EUR/RUB', 'EUR', 'RUB', 0.00010000, false),
('GBP/RUB', 'GBP', 'RUB', 0.00010000, false),
('USD/ILS', 'USD', 'ILS', 0.00010000, false),
('EUR/ILS', 'EUR', 'ILS', 0.00010000, false),
('GBP/ILS', 'GBP', 'ILS', 0.00010000, false)

ON CONFLICT (symbol) DO NOTHING;

-- =====================================================
-- END OF SCRIPT
-- =====================================================


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

-- =====================================================
-- TIMESCALEDB HYPERTABLE SETUP
-- =====================================================

-- Convert time-series tables to hypertables for optimal performance
-- This MUST be done after table creation and before any data insertion

-- Convert tick_data to hypertable (partitioned by timestamp)
SELECT create_hypertable('market_data.tick_data', 'timestamp', 
    chunk_time_interval => INTERVAL '1 hour',
    if_not_exists => TRUE
);

-- Convert order_book_level2 to hypertable
SELECT create_hypertable('market_data.order_book_level2', 'timestamp',
    chunk_time_interval => INTERVAL '1 hour', 
    if_not_exists => TRUE
);

-- Convert microstructure_features to hypertable
SELECT create_hypertable('analytics.microstructure_features', 'timestamp',
    chunk_time_interval => INTERVAL '1 hour',
    if_not_exists => TRUE
);

-- Convert stock_prices to hypertable (existing table)
SELECT create_hypertable('market_data.stock_prices', 'timestamp',
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists => TRUE
);

-- Convert technical_indicators to hypertable (existing table)  
SELECT create_hypertable('market_data.technical_indicators', 'timestamp',
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists => TRUE
);

-- Add indexes for optimal query performance
CREATE INDEX IF NOT EXISTS idx_tick_data_asset_time ON market_data.tick_data (asset_id, asset_type, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_tick_data_timestamp ON market_data.tick_data (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_orderbook_asset_time ON market_data.order_book_level2 (asset_id, asset_type, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_microstructure_asset_time ON analytics.microstructure_features (asset_id, asset_type, timestamp DESC);

-- Enable compression for older data (saves storage space)
ALTER TABLE market_data.tick_data SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'asset_id, asset_type',
    timescaledb.compress_orderby = 'timestamp DESC'
);

ALTER TABLE market_data.order_book_level2 SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'asset_id, asset_type',
    timescaledb.compress_orderby = 'timestamp DESC'
);

-- Add compression policy (compress chunks older than 1 day)
SELECT add_compression_policy('market_data.tick_data', INTERVAL '1 day');
SELECT add_compression_policy('market_data.order_book_level2', INTERVAL '1 day');

-- Add retention policy (keep data for 1 year, then auto-delete)
SELECT add_retention_policy('market_data.tick_data', INTERVAL '1 year');
SELECT add_retention_policy('market_data.order_book_level2', INTERVAL '1 year');

-- Create user for Grafana (read-only)
CREATE USER grafana_user WITH PASSWORD 'grafana_password';
GRANT CONNECT ON DATABASE stock_monitor TO grafana_user;
GRANT USAGE ON SCHEMA market_data, portfolio, alerts, analytics, monitoring TO grafana_user;
GRANT SELECT ON ALL TABLES IN SCHEMA market_data, portfolio, alerts, analytics, monitoring TO grafana_user;

-- =====================================================
-- COMPREHENSIVE ASSET DATA (Top 349 Assets)
-- =====================================================

-- =====================================================
-- TOP 200 STOCKS (Major US stocks by market cap)
-- =====================================================

INSERT INTO market_data.stocks (symbol, exchange_id, company_name, sector, market_cap, currency) VALUES
-- Technology Giants
('AAPL', 2, 'Apple Inc.', 'Technology', 3000000000000, 'USD'),
('MSFT', 2, 'Microsoft Corporation', 'Technology', 2800000000000, 'USD'),
('GOOGL', 2, 'Alphabet Inc. Class A', 'Technology', 1700000000000, 'USD'),
('GOOG', 2, 'Alphabet Inc. Class C', 'Technology', 1700000000000, 'USD'),
('AMZN', 2, 'Amazon.com Inc.', 'Consumer Discretionary', 1500000000000, 'USD'),
('TSLA', 2, 'Tesla Inc.', 'Consumer Discretionary', 800000000000, 'USD'),
('META', 2, 'Meta Platforms Inc.', 'Technology', 750000000000, 'USD'),
('NVDA', 2, 'NVIDIA Corporation', 'Technology', 1800000000000, 'USD'),
('NFLX', 2, 'Netflix Inc.', 'Communication Services', 200000000000, 'USD'),
('CRM', 2, 'Salesforce Inc.', 'Technology', 250000000000, 'USD'),

-- Financial Services
('BRK.A', 1, 'Berkshire Hathaway Inc. Class A', 'Financial Services', 700000000000, 'USD'),
('BRK.B', 1, 'Berkshire Hathaway Inc. Class B', 'Financial Services', 700000000000, 'USD'),
('JPM', 1, 'JPMorgan Chase & Co.', 'Financial Services', 450000000000, 'USD'),
('BAC', 1, 'Bank of America Corporation', 'Financial Services', 300000000000, 'USD'),
('WFC', 1, 'Wells Fargo & Company', 'Financial Services', 180000000000, 'USD'),
('GS', 1, 'The Goldman Sachs Group Inc.', 'Financial Services', 120000000000, 'USD'),
('MS', 1, 'Morgan Stanley', 'Financial Services', 150000000000, 'USD'),
('C', 1, 'Citigroup Inc.', 'Financial Services', 100000000000, 'USD'),
('V', 1, 'Visa Inc.', 'Financial Services', 500000000000, 'USD'),
('MA', 1, 'Mastercard Incorporated', 'Financial Services', 400000000000, 'USD'),

-- Healthcare & Pharmaceuticals
('JNJ', 1, 'Johnson & Johnson', 'Healthcare', 450000000000, 'USD'),
('PFE', 1, 'Pfizer Inc.', 'Healthcare', 250000000000, 'USD'),
('ABBV', 1, 'AbbVie Inc.', 'Healthcare', 300000000000, 'USD'),
('MRK', 1, 'Merck & Co. Inc.', 'Healthcare', 280000000000, 'USD'),
('TMO', 1, 'Thermo Fisher Scientific Inc.', 'Healthcare', 220000000000, 'USD'),
('ABT', 1, 'Abbott Laboratories', 'Healthcare', 190000000000, 'USD'),
('ISRG', 2, 'Intuitive Surgical Inc.', 'Healthcare', 130000000000, 'USD'),
('DHR', 1, 'Danaher Corporation', 'Healthcare', 180000000000, 'USD'),
('BMY', 1, 'Bristol-Myers Squibb Company', 'Healthcare', 120000000000, 'USD'),
('AMGN', 2, 'Amgen Inc.', 'Healthcare', 140000000000, 'USD'),

-- Consumer Goods
('PG', 1, 'The Procter & Gamble Company', 'Consumer Staples', 350000000000, 'USD'),
('KO', 1, 'The Coca-Cola Company', 'Consumer Staples', 260000000000, 'USD'),
('PEP', 2, 'PepsiCo Inc.', 'Consumer Staples', 230000000000, 'USD'),
('WMT', 1, 'Walmart Inc.', 'Consumer Staples', 420000000000, 'USD'),
('COST', 2, 'Costco Wholesale Corporation', 'Consumer Staples', 280000000000, 'USD'),
('HD', 1, 'The Home Depot Inc.', 'Consumer Discretionary', 320000000000, 'USD'),
('MCD', 1, 'McDonald''s Corporation', 'Consumer Discretionary', 200000000000, 'USD'),
('DIS', 1, 'The Walt Disney Company', 'Communication Services', 180000000000, 'USD'),
('NKE', 1, 'NIKE Inc.', 'Consumer Discretionary', 160000000000, 'USD'),
('SBUX', 2, 'Starbucks Corporation', 'Consumer Discretionary', 110000000000, 'USD'),

-- Energy & Utilities
('XOM', 1, 'Exxon Mobil Corporation', 'Energy', 350000000000, 'USD'),
('CVX', 1, 'Chevron Corporation', 'Energy', 280000000000, 'USD'),
('COP', 1, 'ConocoPhillips', 'Energy', 130000000000, 'USD'),
('SLB', 1, 'Schlumberger Limited', 'Energy', 65000000000, 'USD'),
('EOG', 1, 'EOG Resources Inc.', 'Energy', 70000000000, 'USD'),
('PSX', 1, 'Phillips 66', 'Energy', 55000000000, 'USD'),
('VLO', 1, 'Valero Energy Corporation', 'Energy', 50000000000, 'USD'),
('MPC', 1, 'Marathon Petroleum Corporation', 'Energy', 75000000000, 'USD'),
('KMI', 1, 'Kinder Morgan Inc.', 'Energy', 40000000000, 'USD'),
('OKE', 1, 'ONEOK Inc.', 'Energy', 45000000000, 'USD'),

-- Industrial & Manufacturing
('BA', 1, 'The Boeing Company', 'Industrials', 120000000000, 'USD'),
('CAT', 1, 'Caterpillar Inc.', 'Industrials', 130000000000, 'USD'),
('DE', 1, 'Deere & Company', 'Industrials', 110000000000, 'USD'),
('GE', 1, 'General Electric Company', 'Industrials', 115000000000, 'USD'),
('MMM', 1, '3M Company', 'Industrials', 65000000000, 'USD'),
('HON', 2, 'Honeywell International Inc.', 'Industrials', 140000000000, 'USD'),
('UPS', 1, 'United Parcel Service Inc.', 'Industrials', 140000000000, 'USD'),
('RTX', 1, 'Raytheon Technologies Corporation', 'Industrials', 135000000000, 'USD'),
('LMT', 1, 'Lockheed Martin Corporation', 'Industrials', 110000000000, 'USD'),
('NOC', 1, 'Northrop Grumman Corporation', 'Industrials', 75000000000, 'USD'),

-- Technology & Semiconductors
('ORCL', 2, 'Oracle Corporation', 'Technology', 320000000000, 'USD'),
('IBM', 1, 'International Business Machines Corporation', 'Technology', 120000000000, 'USD'),
('CSCO', 2, 'Cisco Systems Inc.', 'Technology', 200000000000, 'USD'),
('INTC', 2, 'Intel Corporation', 'Technology', 180000000000, 'USD'),
('AMD', 2, 'Advanced Micro Devices Inc.', 'Technology', 230000000000, 'USD'),
('QCOM', 2, 'QUALCOMM Incorporated', 'Technology', 140000000000, 'USD'),
('TXN', 2, 'Texas Instruments Incorporated', 'Technology', 155000000000, 'USD'),
('AVGO', 2, 'Broadcom Inc.', 'Technology', 550000000000, 'USD'),
('AMAT', 2, 'Applied Materials Inc.', 'Technology', 130000000000, 'USD'),
('LRCX', 2, 'Lam Research Corporation', 'Technology', 90000000000, 'USD'),

-- Additional Large Cap Stocks
('UNH', 1, 'UnitedHealth Group Incorporated', 'Healthcare', 480000000000, 'USD'),
('LLY', 1, 'Eli Lilly and Company', 'Healthcare', 550000000000, 'USD'),
('BX', 1, 'Blackstone Inc.', 'Financial Services', 120000000000, 'USD'),
('SPGI', 1, 'S&P Global Inc.', 'Financial Services', 130000000000, 'USD'),
('BLK', 1, 'BlackRock Inc.', 'Financial Services', 110000000000, 'USD'),
('AXP', 1, 'American Express Company', 'Financial Services', 120000000000, 'USD'),
('SCHW', 1, 'The Charles Schwab Corporation', 'Financial Services', 120000000000, 'USD'),
('CB', 1, 'Chubb Limited', 'Financial Services', 95000000000, 'USD'),
('ICE', 1, 'Intercontinental Exchange Inc.', 'Financial Services', 75000000000, 'USD'),
('CME', 2, 'CME Group Inc.', 'Financial Services', 80000000000, 'USD')

ON CONFLICT (symbol, exchange_id) DO NOTHING;

INSERT INTO market_data.stocks (symbol, exchange_id, company_name, sector, market_cap, currency) VALUES
-- Telecommunications & Media
('T', 1, 'AT&T Inc.', 'Communication Services', 120000000000, 'USD'),
('VZ', 1, 'Verizon Communications Inc.', 'Communication Services', 170000000000, 'USD'),
('CMCSA', 2, 'Comcast Corporation', 'Communication Services', 160000000000, 'USD'),
('CHTR', 2, 'Charter Communications Inc.', 'Communication Services', 55000000000, 'USD'),
('TMUS', 2, 'T-Mobile US Inc.', 'Communication Services', 180000000000, 'USD'),
('DISH', 2, 'DISH Network Corporation', 'Communication Services', 5000000000, 'USD'),
('FOXA', 2, 'Fox Corporation Class A', 'Communication Services', 18000000000, 'USD'),
('FOX', 2, 'Fox Corporation Class B', 'Communication Services', 18000000000, 'USD'),
('PARA', 2, 'Paramount Global', 'Communication Services', 8000000000, 'USD'),
('WBD', 2, 'Warner Bros. Discovery Inc.', 'Communication Services', 25000000000, 'USD'),

-- Retail & E-commerce
('TGT', 1, 'Target Corporation', 'Consumer Discretionary', 65000000000, 'USD'),
('LOW', 1, 'Lowe''s Companies Inc.', 'Consumer Discretionary', 135000000000, 'USD'),
('TJX', 1, 'The TJX Companies Inc.', 'Consumer Discretionary', 110000000000, 'USD'),
('EBAY', 2, 'eBay Inc.', 'Consumer Discretionary', 28000000000, 'USD'),
('ETSY', 2, 'Etsy Inc.', 'Consumer Discretionary', 8000000000, 'USD'),
('SHOP', 1, 'Shopify Inc.', 'Technology', 75000000000, 'USD'),
('BABA', 1, 'Alibaba Group Holding Limited', 'Consumer Discretionary', 200000000000, 'USD'),
('JD', 2, 'JD.com Inc.', 'Consumer Discretionary', 45000000000, 'USD'),
('PDD', 2, 'PDD Holdings Inc.', 'Consumer Discretionary', 180000000000, 'USD'),
('MELI', 2, 'MercadoLibre Inc.', 'Consumer Discretionary', 75000000000, 'USD'),

-- Real Estate & REITs
('AMT', 1, 'American Tower Corporation', 'Real Estate', 95000000000, 'USD'),
('PLD', 1, 'Prologis Inc.', 'Real Estate', 110000000000, 'USD'),
('CCI', 1, 'Crown Castle Inc.', 'Real Estate', 45000000000, 'USD'),
('EQIX', 2, 'Equinix Inc.', 'Real Estate', 75000000000, 'USD'),
('PSA', 1, 'Public Storage', 'Real Estate', 55000000000, 'USD'),
('EXR', 1, 'Extended Stay America Inc.', 'Real Estate', 25000000000, 'USD'),
('WELL', 1, 'Welltower Inc.', 'Real Estate', 45000000000, 'USD'),
('DLR', 1, 'Digital Realty Trust Inc.', 'Real Estate', 40000000000, 'USD'),
('SPG', 1, 'Simon Property Group Inc.', 'Real Estate', 45000000000, 'USD'),
('O', 1, 'Realty Income Corporation', 'Real Estate', 40000000000, 'USD'),

-- Materials & Chemicals
('LIN', 1, 'Linde plc', 'Materials', 200000000000, 'USD'),
('APD', 1, 'Air Products and Chemicals Inc.', 'Materials', 55000000000, 'USD'),
('SHW', 1, 'The Sherwin-Williams Company', 'Materials', 65000000000, 'USD'),
('ECL', 1, 'Ecolab Inc.', 'Materials', 55000000000, 'USD'),
('DD', 1, 'DuPont de Nemours Inc.', 'Materials', 35000000000, 'USD'),
('DOW', 1, 'Dow Inc.', 'Materials', 40000000000, 'USD'),
('LYB', 1, 'LyondellBasell Industries N.V.', 'Materials', 30000000000, 'USD'),
('PPG', 1, 'PPG Industries Inc.', 'Materials', 30000000000, 'USD'),
('NEM', 1, 'Newmont Corporation', 'Materials', 35000000000, 'USD'),
('FCX', 1, 'Freeport-McMoRan Inc.', 'Materials', 60000000000, 'USD'),

-- Additional Technology Companies
('ADBE', 2, 'Adobe Inc.', 'Technology', 220000000000, 'USD'),
('NOW', 1, 'ServiceNow Inc.', 'Technology', 140000000000, 'USD'),
('INTU', 2, 'Intuit Inc.', 'Technology', 140000000000, 'USD'),
('UBER', 1, 'Uber Technologies Inc.', 'Technology', 140000000000, 'USD'),
('LYFT', 2, 'Lyft Inc.', 'Technology', 5000000000, 'USD'),
('SNAP', 1, 'Snap Inc.', 'Technology', 15000000000, 'USD'),
('PINS', 1, 'Pinterest Inc.', 'Technology', 20000000000, 'USD'),
('TWTR', 1, 'Twitter Inc.', 'Technology', 40000000000, 'USD'),
('SPOT', 1, 'Spotify Technology S.A.', 'Technology', 28000000000, 'USD'),
('ZM', 2, 'Zoom Video Communications Inc.', 'Technology', 20000000000, 'USD')

ON CONFLICT (symbol, exchange_id) DO NOTHING;

-- =====================================================
-- EXPANDED CRYPTOCURRENCY DATA (Top 50 by Market Cap)
-- =====================================================

INSERT INTO market_data.cryptocurrencies (symbol, name, market_cap, circulating_supply, total_supply, max_supply) VALUES
-- Top 50 Cryptocurrencies by Market Cap
('BTC', 'Bitcoin', 580000000000, 19500000.00000000, 19500000.00000000, 21000000.00000000),
('ETH', 'Ethereum', 240000000000, 120000000.00000000, 120000000.00000000, NULL),
('USDT', 'Tether', 83000000000, 83000000000.00000000, 83000000000.00000000, NULL),
('BNB', 'BNB', 48000000000, 153000000.00000000, 153000000.00000000, 200000000.00000000),
('USDC', 'USD Coin', 42000000000, 42000000000.00000000, 42000000000.00000000, NULL),
('XRP', 'XRP', 26000000000, 51000000000.00000000, 99990000000.00000000, 100000000000.00000000),
('ADA', 'Cardano', 18000000000, 35000000000.00000000, 35000000000.00000000, 45000000000.00000000),
('DOGE', 'Dogecoin', 15000000000, 132000000000.00000000, 132000000000.00000000, NULL),
('MATIC', 'Polygon', 12000000000, 9000000000.00000000, 10000000000.00000000, 10000000000.00000000),
('SOL', 'Solana', 11000000000, 400000000.00000000, 400000000.00000000, NULL),
('DOT', 'Polkadot', 8000000000, 1100000000.00000000, 1100000000.00000000, NULL),
('LTC', 'Litecoin', 7500000000, 73000000.00000000, 73000000.00000000, 84000000.00000000),
('SHIB', 'Shiba Inu', 7000000000, 589000000000000.00000000, 1000000000000000.00000000, 1000000000000000.00000000),
('AVAX', 'Avalanche', 6500000000, 350000000.00000000, 350000000.00000000, 720000000.00000000),
('TRX', 'TRON', 6000000000, 92000000000.00000000, 92000000000.00000000, NULL),
('UNI', 'Uniswap', 5500000000, 750000000.00000000, 1000000000.00000000, 1000000000.00000000),
('ATOM', 'Cosmos', 5000000000, 290000000.00000000, 290000000.00000000, NULL),
('LINK', 'Chainlink', 4800000000, 500000000.00000000, 1000000000.00000000, 1000000000.00000000),
('ETC', 'Ethereum Classic', 4500000000, 140000000.00000000, 140000000.00000000, 210700000.00000000),
('XLM', 'Stellar', 4200000000, 25000000000.00000000, 50000000000.00000000, 50000000000.00000000),
('ALGO', 'Algorand', 4000000000, 7000000000.00000000, 10000000000.00000000, 10000000000.00000000),
('BCH', 'Bitcoin Cash', 3800000000, 19500000.00000000, 19500000.00000000, 21000000.00000000),
('VET', 'VeChain', 3500000000, 86000000000.00000000, 86000000000.00000000, 86000000000.00000000),
('ICP', 'Internet Computer', 3200000000, 480000000.00000000, 480000000.00000000, NULL),
('FIL', 'Filecoin', 3000000000, 400000000.00000000, 2000000000.00000000, 2000000000.00000000),
('HBAR', 'Hedera', 2800000000, 22000000000.00000000, 50000000000.00000000, 50000000000.00000000),
('AAVE', 'Aave', 2500000000, 15000000.00000000, 16000000.00000000, 16000000.00000000),
('APE', 'ApeCoin', 2200000000, 1000000000.00000000, 1000000000.00000000, 1000000000.00000000),
('SAND', 'The Sandbox', 2000000000, 2000000000.00000000, 3000000000.00000000, 3000000000.00000000),
('MANA', 'Decentraland', 1800000000, 1800000000.00000000, 2200000000.00000000, 2200000000.00000000),
('AXS', 'Axie Infinity', 1500000000, 270000000.00000000, 270000000.00000000, 270000000.00000000),
('THETA', 'THETA', 1400000000, 1000000000.00000000, 1000000000.00000000, 1000000000.00000000),
('FLOW', 'Flow', 1300000000, 1400000000.00000000, 1400000000.00000000, NULL),
('XTZ', 'Tezos', 1200000000, 930000000.00000000, 930000000.00000000, NULL),
('EGLD', 'MultiversX', 1100000000, 24000000.00000000, 31400000.00000000, 31400000.00000000),
('KLAY', 'Klaytn', 1000000000, 3000000000.00000000, 3000000000.00000000, NULL),
('CHZ', 'Chiliz', 950000000, 8800000000.00000000, 8800000000.00000000, 8800000000.00000000),
('ENJ', 'Enjin Coin', 900000000, 1000000000.00000000, 1000000000.00000000, 1000000000.00000000),
('NEAR', 'NEAR Protocol', 850000000, 1100000000.00000000, 1100000000.00000000, NULL),
('QNT', 'Quant', 800000000, 14600000.00000000, 14600000.00000000, 14600000.00000000),
('GRT', 'The Graph', 750000000, 9500000000.00000000, 10000000000.00000000, 10000000000.00000000),
('FTM', 'Fantom', 700000000, 2800000000.00000000, 3200000000.00000000, 3200000000.00000000),
('LRC', 'Loopring', 650000000, 1400000000.00000000, 1400000000.00000000, 1400000000.00000000),
('BAT', 'Basic Attention Token', 600000000, 1500000000.00000000, 1500000000.00000000, 1500000000.00000000),
('CRV', 'Curve DAO Token', 550000000, 1100000000.00000000, 3000000000.00000000, 3000000000.00000000),
('COMP', 'Compound', 500000000, 10000000.00000000, 10000000.00000000, 10000000.00000000),
('YFI', 'yearn.finance', 450000000, 36600.00000000, 36600.00000000, 36600.00000000),
('SUSHI', 'SushiSwap', 400000000, 250000000.00000000, 250000000.00000000, 250000000.00000000),
('ZRX', '0x', 350000000, 1000000000.00000000, 1000000000.00000000, 1000000000.00000000),
('REN', 'Ren', 300000000, 1000000000.00000000, 1000000000.00000000, 1000000000.00000000)

ON CONFLICT (symbol) DO NOTHING;

-- =====================================================
-- EXPANDED COMMODITIES DATA (50+ Major Commodities)
-- =====================================================

INSERT INTO market_data.commodities (symbol, name, asset_class, unit, contract_size, tick_size) VALUES
-- Metals (Precious)
('XAU/USD', 'Gold', 'Metals', 'Troy Ounce', 100.0000, 0.1000),
('XAG/USD', 'Silver', 'Metals', 'Troy Ounce', 5000.0000, 0.0050),
('XPT/USD', 'Platinum', 'Metals', 'Troy Ounce', 50.0000, 0.1000),
('XPD/USD', 'Palladium', 'Metals', 'Troy Ounce', 100.0000, 0.0500),

-- Metals (Industrial)
('COPPER', 'Copper', 'Metals', 'Pound', 25000.0000, 0.0005),
('ZINC', 'Zinc', 'Metals', 'Metric Ton', 25.0000, 0.5000),
('ALUMINUM', 'Aluminum', 'Metals', 'Metric Ton', 25.0000, 0.5000),
('NICKEL', 'Nickel', 'Metals', 'Metric Ton', 6.0000, 1.0000),
('LEAD', 'Lead', 'Metals', 'Metric Ton', 25.0000, 0.5000),
('TIN', 'Tin', 'Metals', 'Metric Ton', 5.0000, 5.0000),

-- Energy (Crude Oil)
('WTI', 'Crude Oil WTI', 'Energy', 'Barrel', 1000.0000, 0.0100),
('BRENT', 'Brent Crude Oil', 'Energy', 'Barrel', 1000.0000, 0.0100),
('WCS', 'Western Canadian Select', 'Energy', 'Barrel', 1000.0000, 0.0100),
('MARS', 'Mars Crude Oil', 'Energy', 'Barrel', 1000.0000, 0.0100),

-- Energy (Natural Gas)
('NG', 'Natural Gas', 'Energy', 'MMBtu', 10000.0000, 0.0010),
('NG-UK', 'UK Natural Gas', 'Energy', 'Therm', 1000.0000, 0.0010),
('LNG', 'Liquefied Natural Gas', 'Energy', 'MMBtu', 10000.0000, 0.0010),

-- Energy (Refined Products)
('RBOB', 'RBOB Gasoline', 'Energy', 'Gallon', 42000.0000, 0.0001),
('HO', 'Heating Oil', 'Energy', 'Gallon', 42000.0000, 0.0001),
('ULSD', 'Ultra Low Sulfur Diesel', 'Energy', 'Gallon', 42000.0000, 0.0001),

-- Agriculture (Grains)
('WHEAT', 'Wheat', 'Agriculture', 'Bushel', 5000.0000, 0.2500),
('CORN', 'Corn', 'Agriculture', 'Bushel', 5000.0000, 0.2500),
('SOYBEANS', 'Soybeans', 'Agriculture', 'Bushel', 5000.0000, 0.2500),
('RICE', 'Rice', 'Agriculture', 'Hundredweight', 2000.0000, 0.5000),
('OATS', 'Oats', 'Agriculture', 'Bushel', 5000.0000, 0.2500),

-- Agriculture (Soft Commodities)
('SUGAR', 'Sugar No. 11', 'Agriculture', 'Pound', 112000.0000, 0.0100),
('COFFEE', 'Coffee C', 'Agriculture', 'Pound', 37500.0000, 0.0500),
('COCOA', 'Cocoa', 'Agriculture', 'Metric Ton', 10.0000, 1.0000),
('COTTON', 'Cotton No. 2', 'Agriculture', 'Pound', 50000.0000, 0.0100),
('ORANGE-JUICE', 'Orange Juice', 'Agriculture', 'Pound', 15000.0000, 0.0500),

-- Agriculture (Livestock)
('LIVE-CATTLE', 'Live Cattle', 'Agriculture', 'Pound', 40000.0000, 0.0250),
('FEEDER-CATTLE', 'Feeder Cattle', 'Agriculture', 'Pound', 50000.0000, 0.0250),
('LEAN-HOGS', 'Lean Hogs', 'Agriculture', 'Pound', 40000.0000, 0.0250),

-- Other Commodities
('LUMBER', 'Lumber', 'Materials', 'Board Feet', 110000.0000, 0.1000),
('RUBBER', 'Rubber', 'Materials', 'Metric Ton', 50.0000, 0.0500),
('MILK', 'Class III Milk', 'Agriculture', 'Pound', 200000.0000, 0.0100),
('BUTTER', 'Butter', 'Agriculture', 'Pound', 40000.0000, 0.0250),
('CHEESE', 'Cheese', 'Agriculture', 'Pound', 40000.0000, 0.0250),

-- Cryptocurrency Commodities (Digital Assets treated as commodities)
('BTC-FUTURES', 'Bitcoin Futures', 'Digital Assets', 'Bitcoin', 5.0000, 5.0000),
('ETH-FUTURES', 'Ethereum Futures', 'Digital Assets', 'Ethereum', 50.0000, 0.0500),

-- Coal and Carbon
('COAL', 'Coal', 'Energy', 'Metric Ton', 1350.0000, 0.0100),
('CARBON', 'Carbon Credits', 'Environmental', 'Metric Ton CO2', 1000.0000, 0.0100),

-- Water Rights
('WATER-CA', 'California Water Rights', 'Environmental', 'Acre-Foot', 10.0000, 1.0000)

ON CONFLICT (symbol) DO NOTHING;

-- =====================================================
-- EXPANDED FOREX PAIRS (40+ Major and Minor Pairs)
-- =====================================================

INSERT INTO market_data.forex_pairs (symbol, base_currency, quote_currency, pip_size, is_major) VALUES
-- Major Pairs (Most traded)
('EUR/USD', 'EUR', 'USD', 0.00010000, true),
('GBP/USD', 'GBP', 'USD', 0.00010000, true),
('USD/JPY', 'USD', 'JPY', 0.01000000, true),
('USD/CHF', 'USD', 'CHF', 0.00010000, true),
('AUD/USD', 'AUD', 'USD', 0.00010000, true),
('USD/CAD', 'USD', 'CAD', 0.00010000, true),
('NZD/USD', 'NZD', 'USD', 0.00010000, true),

-- Minor Pairs (Cross currencies)
('EUR/GBP', 'EUR', 'GBP', 0.00010000, false),
('EUR/JPY', 'EUR', 'JPY', 0.01000000, false),
('EUR/CHF', 'EUR', 'CHF', 0.00010000, false),
('EUR/AUD', 'EUR', 'AUD', 0.00010000, false),
('EUR/CAD', 'EUR', 'CAD', 0.00010000, false),
('EUR/NZD', 'EUR', 'NZD', 0.00010000, false),
('GBP/JPY', 'GBP', 'JPY', 0.01000000, false),
('GBP/CHF', 'GBP', 'CHF', 0.00010000, false),
('GBP/AUD', 'GBP', 'AUD', 0.00010000, false),
('GBP/CAD', 'GBP', 'CAD', 0.00010000, false),
('GBP/NZD', 'GBP', 'NZD', 0.00010000, false),
('CHF/JPY', 'CHF', 'JPY', 0.01000000, false),
('AUD/JPY', 'AUD', 'JPY', 0.01000000, false),
('AUD/CHF', 'AUD', 'CHF', 0.00010000, false),
('AUD/CAD', 'AUD', 'CAD', 0.00010000, false),
('AUD/NZD', 'AUD', 'NZD', 0.00010000, false),
('CAD/JPY', 'CAD', 'JPY', 0.01000000, false),
('CAD/CHF', 'CAD', 'CHF', 0.00010000, false),
('NZD/JPY', 'NZD', 'JPY', 0.01000000, false),
('NZD/CHF', 'NZD', 'CHF', 0.00010000, false),
('NZD/CAD', 'NZD', 'CAD', 0.00010000, false),

-- Exotic Pairs (Emerging market currencies)
('USD/MXN', 'USD', 'MXN', 0.00010000, false),
('USD/BRL', 'USD', 'BRL', 0.00010000, false),
('USD/ZAR', 'USD', 'ZAR', 0.00010000, false),
('USD/TRY', 'USD', 'TRY', 0.00010000, false),
('USD/RUB', 'USD', 'RUB', 0.00010000, false),
('USD/CNH', 'USD', 'CNH', 0.00010000, false),
('USD/INR', 'USD', 'INR', 0.00010000, false),
('USD/KRW', 'USD', 'KRW', 0.01000000, false),
('USD/SGD', 'USD', 'SGD', 0.00010000, false),
('USD/HKD', 'USD', 'HKD', 0.00010000, false),
('USD/NOK', 'USD', 'NOK', 0.00010000, false),
('USD/SEK', 'USD', 'SEK', 0.00010000, false),
('USD/DKK', 'USD', 'DKK', 0.00010000, false),
('USD/PLN', 'USD', 'PLN', 0.00010000, false),
('USD/CZK', 'USD', 'CZK', 0.00010000, false),
('USD/HUF', 'USD', 'HUF', 0.00010000, false),
('USD/ILS', 'USD', 'ILS', 0.00010000, false),
('EUR/ILS', 'EUR', 'ILS', 0.00010000, false),
('GBP/ILS', 'GBP', 'ILS', 0.00010000, false)

ON CONFLICT (symbol) DO NOTHING;

-- =====================================================
-- SAMPLE TICK DATA FOR TESTING
-- =====================================================

-- Insert sample tick data for a few assets for testing purposes
INSERT INTO market_data.tick_data (asset_id, asset_type, timestamp, price, volume, aggressor_side) VALUES
-- BTC tick data (crypto ID 1)
(1, 'crypto', NOW() - INTERVAL '5 minutes', 43250.50000000, 0.50000000, 'BUY'),
(1, 'crypto', NOW() - INTERVAL '4 minutes', 43275.25000000, 0.25000000, 'SELL'),
(1, 'crypto', NOW() - INTERVAL '3 minutes', 43300.00000000, 1.00000000, 'BUY'),
(1, 'crypto', NOW() - INTERVAL '2 minutes', 43285.75000000, 0.75000000, 'SELL'),
(1, 'crypto', NOW() - INTERVAL '1 minute', 43320.25000000, 0.30000000, 'BUY'),

-- EUR/USD tick data (forex ID 1)
(1, 'forex', NOW() - INTERVAL '5 minutes', 1.08450000, 1000000.00000000, 'BUY'),
(1, 'forex', NOW() - INTERVAL '4 minutes', 1.08435000, 750000.00000000, 'SELL'),
(1, 'forex', NOW() - INTERVAL '3 minutes', 1.08460000, 500000.00000000, 'BUY'),
(1, 'forex', NOW() - INTERVAL '2 minutes', 1.08445000, 1250000.00000000, 'SELL'),
(1, 'forex', NOW() - INTERVAL '1 minute', 1.08470000, 800000.00000000, 'BUY'),

-- Gold tick data (commodity ID 1)
(1, 'commodity', NOW() - INTERVAL '5 minutes', 1985.50000000, 10.00000000, 'BUY'),
(1, 'commodity', NOW() - INTERVAL '4 minutes', 1983.25000000, 15.00000000, 'SELL'),
(1, 'commodity', NOW() - INTERVAL '3 minutes', 1987.75000000, 8.00000000, 'BUY'),
(1, 'commodity', NOW() - INTERVAL '2 minutes', 1986.00000000, 12.00000000, 'SELL'),
(1, 'commodity', NOW() - INTERVAL '1 minute', 1988.25000000, 5.00000000, 'BUY'),

-- AAPL stock tick data (stock ID will be assigned)
(1, 'stock', NOW() - INTERVAL '5 minutes', 178.50000000, 1000.00000000, 'BUY'),
(1, 'stock', NOW() - INTERVAL '4 minutes', 178.45000000, 1500.00000000, 'SELL'),
(1, 'stock', NOW() - INTERVAL '3 minutes', 178.60000000, 800.00000000, 'BUY'),
(1, 'stock', NOW() - INTERVAL '2 minutes', 178.55000000, 1200.00000000, 'SELL'),
(1, 'stock', NOW() - INTERVAL '1 minute', 178.65000000, 600.00000000, 'BUY');

-- =====================================================
-- SAMPLE MICROSTRUCTURE FEATURES
-- =====================================================

INSERT INTO analytics.microstructure_features (
    asset_id, asset_type, timestamp, bid_ask_spread, bid_ask_spread_bps, 
    order_flow_imbalance, trade_intensity, market_depth_bid, market_depth_ask
) VALUES
-- BTC microstructure data
(1, 'crypto', NOW() - INTERVAL '5 minutes', 25.50000000, 0.59, 0.15000000, 12.50000000, 15000000.00000000, 14500000.00000000),
(1, 'crypto', NOW() - INTERVAL '4 minutes', 22.75000000, 0.53, -0.08000000, 15.20000000, 18000000.00000000, 16800000.00000000),
(1, 'crypto', NOW() - INTERVAL '3 minutes', 28.00000000, 0.65, 0.22000000, 18.75000000, 12500000.00000000, 13200000.00000000),

-- EUR/USD microstructure data
(1, 'forex', NOW() - INTERVAL '5 minutes', 0.00015000, 1.38, 0.05000000, 250.50000000, 50000000.00000000, 48000000.00000000),
(1, 'forex', NOW() - INTERVAL '4 minutes', 0.00012000, 1.11, -0.12000000, 320.25000000, 65000000.00000000, 62000000.00000000),
(1, 'forex', NOW() - INTERVAL '3 minutes', 0.00018000, 1.66, 0.18000000, 180.75000000, 45000000.00000000, 47000000.00000000);

COMMIT;
