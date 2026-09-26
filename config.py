from dotenv import load_dotenv
import os


load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
MOVE_THRESHOLD = 2.5
INTERVAL = "15m"
COUNT_CANDLES = 8
ORDERBOOK_VOLUME_THRESHOLD = 12
COEFFICIENT_VOLUME_THRESHOLD = 5
DIST_TO_DENSITY = 2.0
TIME_TO_NEXT_ORDERBOOK_ALERT = 900

AVAILABLE_EXCHANGES = ["bingx", "bitget", "binance", "mexc", "okx", "gate", "bybit", "kucoin", "kraken"]

