-- Populate sample stock tick data for dashboard testing
-- This script adds recent tick data for major stocks

INSERT INTO market_data.tick_data (asset_id, asset_type, timestamp, price, volume, aggressor_side) VALUES
-- AAPL (assuming ID 1)
(1, 'stock', NOW() - INTERVAL '5 minutes', 175.50, 1000, 'BUY'),
(1, 'stock', NOW() - INTERVAL '4 minutes', 175.75, 850, 'BUY'),
(1, 'stock', NOW() - INTERVAL '3 minutes', 175.25, 1200, 'SELL'),
(1, 'stock', NOW() - INTERVAL '2 minutes', 175.80, 950, 'BUY'),
(1, 'stock', NOW() - INTERVAL '1 minute', 176.00, 750, 'BUY'),

-- MSFT (assuming ID 2)  
(2, 'stock', NOW() - INTERVAL '5 minutes', 380.25, 800, 'SELL'),
(2, 'stock', NOW() - INTERVAL '4 minutes', 379.50, 1100, 'SELL'),
(2, 'stock', NOW() - INTERVAL '3 minutes', 380.75, 900, 'BUY'),
(2, 'stock', NOW() - INTERVAL '2 minutes', 381.00, 1050, 'BUY'),
(2, 'stock', NOW() - INTERVAL '1 minute', 380.85, 650, 'SELL'),

-- GOOGL (assuming ID 3)
(3, 'stock', NOW() - INTERVAL '5 minutes', 2750.00, 300, 'BUY'),
(3, 'stock', NOW() - INTERVAL '4 minutes', 2748.50, 450, 'SELL'),
(3, 'stock', NOW() - INTERVAL '3 minutes', 2752.25, 200, 'BUY'),
(3, 'stock', NOW() - INTERVAL '2 minutes', 2751.75, 350, 'SELL'),
(3, 'stock', NOW() - INTERVAL '1 minute', 2753.00, 280, 'BUY'),

-- AMZN (assuming ID 5)
(5, 'stock', NOW() - INTERVAL '5 minutes', 155.50, 2000, 'SELL'),
(5, 'stock', NOW() - INTERVAL '4 minutes', 154.75, 1800, 'SELL'),
(5, 'stock', NOW() - INTERVAL '3 minutes', 155.25, 2200, 'BUY'),
(5, 'stock', NOW() - INTERVAL '2 minutes', 155.80, 1900, 'BUY'),
(5, 'stock', NOW() - INTERVAL '1 minute', 155.95, 1750, 'BUY'),

-- TSLA (assuming ID 6)
(6, 'stock', NOW() - INTERVAL '5 minutes', 185.25, 3000, 'BUY'),
(6, 'stock', NOW() - INTERVAL '4 minutes', 184.50, 2800, 'SELL'),
(6, 'stock', NOW() - INTERVAL '3 minutes', 185.75, 3200, 'BUY'),
(6, 'stock', NOW() - INTERVAL '2 minutes', 186.00, 2950, 'BUY'),
(6, 'stock', NOW() - INTERVAL '1 minute', 185.80, 2600, 'SELL'),

-- META (assuming ID 7)
(7, 'stock', NOW() - INTERVAL '5 minutes', 320.50, 1500, 'SELL'),
(7, 'stock', NOW() - INTERVAL '4 minutes', 319.75, 1400, 'SELL'),
(7, 'stock', NOW() - INTERVAL '3 minutes', 321.25, 1600, 'BUY'),
(7, 'stock', NOW() - INTERVAL '2 minutes', 321.50, 1450, 'BUY'),
(7, 'stock', NOW() - INTERVAL '1 minute', 321.00, 1300, 'SELL'),

-- NVDA (assuming ID 8)
(8, 'stock', NOW() - INTERVAL '5 minutes', 875.00, 500, 'BUY'),
(8, 'stock', NOW() - INTERVAL '4 minutes', 873.50, 600, 'SELL'),
(8, 'stock', NOW() - INTERVAL '3 minutes', 876.25, 450, 'BUY'),
(8, 'stock', NOW() - INTERVAL '2 minutes', 877.00, 550, 'BUY'),
(8, 'stock', NOW() - INTERVAL '1 minute', 876.75, 400, 'SELL'),

-- NFLX (assuming ID 9)
(9, 'stock', NOW() - INTERVAL '5 minutes', 485.00, 800, 'SELL'),
(9, 'stock', NOW() - INTERVAL '4 minutes', 484.25, 900, 'SELL'),
(9, 'stock', NOW() - INTERVAL '3 minutes', 485.75, 750, 'BUY'),
(9, 'stock', NOW() - INTERVAL '2 minutes', 486.00, 850, 'BUY'),
(9, 'stock', NOW() - INTERVAL '1 minute', 485.50, 700, 'SELL');

-- Add some historical data (last 24 hours) for trending
INSERT INTO market_data.tick_data (asset_id, asset_type, timestamp, price, volume, aggressor_side)
SELECT 
    (ARRAY[1,2,3,5,6,7,8,9])[ceil(random()*8)], -- Random stock ID
    'stock',
    generate_series(
        NOW() - INTERVAL '24 hours',
        NOW() - INTERVAL '10 minutes', 
        INTERVAL '30 minutes'
    ),
    -- Generate realistic price movements
    100 + (RANDOM() * 200) + SIN(EXTRACT(EPOCH FROM generate_series(NOW() - INTERVAL '24 hours', NOW() - INTERVAL '10 minutes', INTERVAL '30 minutes')) / 3600) * 10,
    (RANDOM() * 2000 + 100)::numeric(10,2),
    CASE WHEN RANDOM() > 0.5 THEN 'BUY' ELSE 'SELL' END;