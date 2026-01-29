import websocket
import json
import psycopg2
from datetime import datetime
import time


DB_HOST = "localhost"
DB_NAME = "trade-db"
DB_USER = "postgres"
DB_PASS = "Rabiya123"  
SYMBOL = "btcusdt"
WS_URL = f"wss://stream.binance.com:9443/ws/{SYMBOL}@trade"

def get_db_connection():
    conn = psycopg2.connect(
        host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASS
    )
    return conn

def on_message(ws, message):
    """
    Callback when a message is received from Binance.
    Parses JSON and inserts into Postgres.
    """
    try:
        data = json.loads(message)
        
        
        trade_id = data['t']
        price = float(data['p'])
        qty = float(data['q'])
        
        trade_time = datetime.fromtimestamp(data['T'] / 1000.0)
        
        
        cursor.execute(
            """
            INSERT INTO trade_data (trade_id, symbol, price, quantity, trade_time)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (trade_id) DO NOTHING;
            """,
            (trade_id, SYMBOL.upper(), price, qty, trade_time)
        )
        conn.commit()
        print(f"Stored Trade: {price} | {qty}")

    except Exception as e:
        print(f"Error processing message: {e}")
        

def on_error(ws, error):
    print(f"WebSocket Error: {error}")

def on_close(ws, close_status_code, close_msg):
    print("### WebSocket Closed ###")

def start_stream():
    """
    Main loop with reconnection logic.
    """
    global conn, cursor
    while True:
        try:
            print("Connecting to DB...")
            conn = get_db_connection()
            cursor = conn.cursor()
            
            print(f"Connecting to Binance Stream: {WS_URL}...")
            ws = websocket.WebSocketApp(
                WS_URL,
                on_message=on_message,
                on_error=on_error,
                on_close=on_close
            )
            
            
            ws.run_forever()
            
        except Exception as e:
            print(f"Connection failed: {e}. Retrying in 5s...")
            time.sleep(5)
        finally:
            if conn:
                cursor.close()
                conn.close()

if __name__ == "__main__":
    start_stream()