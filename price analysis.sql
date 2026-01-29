SELECT 
    MIN(price) as lowest_price,
    MAX(price) as highest_price,
    AVG(price) as avg_price,
    SUM(quantity) as total_volume_btc
FROM trade_data;