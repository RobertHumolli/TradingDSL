import yfinance as yf
import sqlite3  
from datetime import datetime


symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA"]


def get_db_connection():
    conn = sqlite3.connect("stocks.db")
    cursor = conn.cursor()
    return conn, cursor

conn, cursor = get_db_connection()


cursor.execute("""
    CREATE TABLE IF NOT EXISTS stocks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        symbol TEXT NOT NULL,
        price REAL,
        volume INTEGER,
        timestamp TEXT NOT NULL
    )
""")
conn.commit()


def get_latest_stock_price(symbol):
    with sqlite3.connect("stocks.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT price, timestamp FROM stocks WHERE symbol = ? ORDER BY timestamp DESC LIMIT 1", (symbol,))
        result = cursor.fetchone()
        return result[0] if result else None


def insert_stock_data(data):
    cursor.execute("""
        INSERT INTO stocks (symbol, price, volume, timestamp)
        VALUES (?, ?, ?, ?)
    """, (data["symbol"], data["price"], data["volume"], data["timestamp"]))
    conn.commit()


def fetch_stock_data(symbol):
    stock = yf.Ticker(symbol)
    data = stock.history(period="5d")

    if data.empty:
        return None

    latest = data.tail(1)
    if latest.empty:
        return None

    latest_row = latest.iloc[0]

    return {
        "symbol": symbol,
        "price": latest_row["Close"],
        "volume": latest_row["Volume"],
        "timestamp": latest_row.name.isoformat()
    }


for symbol in symbols:
    latest_price = get_latest_stock_price(symbol)

    if latest_price is None:
        stock_data = fetch_stock_data(symbol)
        if stock_data:
            insert_stock_data(stock_data)

conn.close()  
