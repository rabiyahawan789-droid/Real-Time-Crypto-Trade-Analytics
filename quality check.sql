SELECT trade_id, COUNT(*) 
FROM trade_data 
GROUP BY trade_id 
HAVING COUNT(*) > 1;