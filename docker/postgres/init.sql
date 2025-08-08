-- Database initialization script for Stock Market Monitor
-- This script creates the necessary tables and initial data

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create schemas
CREATE SCHEMA IF NOT EXISTS market_data;
CREATE SCHEMA IF NOT EXISTS portfolio;
CREATE SCHEMA IF NOT EXISTS alerts;
CREATE SCHEMA IF NOT EXISTS analytics;
CREATE SCHEMA IF NOT EXISTS monitoring;

-- Set default schema
SET search_path TO public, market_data, portfolio, alerts, analytics, monitoring;

-- Market Data Tables
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

CREATE TABLE IF NOT EXISTS market_data.technical_indicators (
    id BIGSERIAL PRIMARY KEY,
    stock_id INTEGER REFERENCES market_data.stocks(id),
    timestamp TIMESTAMP NOT NULL,
    indicator_name VARCHAR(50) NOT NULL,
    value DECIMAL(15,6),
    parameters JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Portfolio Tables
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

-- Alert Tables
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

-- Analytics Tables
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

-- Monitoring Tables
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

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_stock_prices_stock_timestamp ON market_data.stock_prices(stock_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_stock_prices_timestamp ON market_data.stock_prices(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_technical_indicators_stock_timestamp ON market_data.technical_indicators(stock_id, timestamp DESC, indicator_name);
CREATE INDEX IF NOT EXISTS idx_positions_portfolio ON portfolio.positions(portfolio_id);
CREATE INDEX IF NOT EXISTS idx_transactions_portfolio_date ON portfolio.transactions(portfolio_id, transaction_date DESC);
CREATE INDEX IF NOT EXISTS idx_alert_instances_status_triggered ON alerts.alert_instances(status, triggered_at DESC);
CREATE INDEX IF NOT EXISTS idx_predictions_stock_date ON analytics.predictions(stock_id, prediction_date DESC);
CREATE INDEX IF NOT EXISTS idx_anomalies_stock_detected ON analytics.anomalies(stock_id, detected_at DESC);
CREATE INDEX IF NOT EXISTS idx_system_metrics_name_timestamp ON monitoring.system_metrics(metric_name, timestamp DESC);

-- Create partial indexes for active records
CREATE INDEX IF NOT EXISTS idx_stocks_active ON market_data.stocks(symbol, exchange_id) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_portfolios_active ON portfolio.portfolios(name) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_alert_rules_active ON alerts.alert_rules(alert_type) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_alert_instances_active ON alerts.alert_instances(triggered_at DESC) WHERE status = 'ACTIVE';

-- Insert default data
INSERT INTO market_data.exchanges (code, name, timezone, market_open, market_close, currency) VALUES
    ('NYSE', 'New York Stock Exchange', 'America/New_York', '09:30:00', '16:00:00', 'USD'),
    ('NASDAQ', 'NASDAQ', 'America/New_York', '09:30:00', '16:00:00', 'USD'),
    ('LSE', 'London Stock Exchange', 'Europe/London', '08:00:00', '16:30:00', 'GBP'),
    ('TSE', 'Tokyo Stock Exchange', 'Asia/Tokyo', '09:00:00', '15:00:00', 'JPY'),
    ('FRA', 'Frankfurt Stock Exchange', 'Europe/Berlin', '09:00:00', '17:30:00', 'EUR')
ON CONFLICT (code) DO NOTHING;

-- Create default portfolio
INSERT INTO portfolio.portfolios (id, name, description, initial_value) VALUES
    ('00000000-0000-0000-0000-000000000001', 'Default Portfolio', 'Default portfolio for testing', 100000.00)
ON CONFLICT (id) DO NOTHING;

-- Create some default alert rules
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
    )
ON CONFLICT (id) DO NOTHING;

-- Create functions for common operations

-- Function to update timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_exchanges_updated_at BEFORE UPDATE ON market_data.exchanges 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_stocks_updated_at BEFORE UPDATE ON market_data.stocks 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_portfolios_updated_at BEFORE UPDATE ON portfolio.portfolios 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_alert_rules_updated_at BEFORE UPDATE ON alerts.alert_rules 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to calculate portfolio metrics
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

-- Function to get latest stock price
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

-- Create views for common queries
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

-- Grant permissions
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