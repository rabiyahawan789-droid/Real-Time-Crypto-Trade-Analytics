CREATE TABLE IF NOT EXISTS trades (
    trade_id BIGINT PRIMARY KEY, 
    symbol VARCHAR(12) NOT NULL,
    price NUMERIC(20, 8) NOT NULL, 
    quantity NUMERIC(20, 8) NOT NULL,
    trade_time TIMESTAMP WITH TIME ZONE NOT NULL,
    is_buyer_maker BOOLEAN NOT NULL,
    ingested_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_trade_time ON trade_data(trade_time DESC);