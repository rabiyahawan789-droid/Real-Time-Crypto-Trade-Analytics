SELECT 
    date_trunc('minute', trade_time) AS minute, 
    COUNT(*) AS trades_per_minute
FROM trade_data 
GROUP BY minute 
ORDER BY minute DESC 
LIMIT 5;