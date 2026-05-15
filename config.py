from dotenv import load_dotenv
import os


load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
PROXY = os.getenv("PROXY")
BOSS_ID = os.getenv("BOSS_ID")
MOVE_THRESHOLD = 7
INTERVAL = "5m"
COUNT_CANDLES = 24
ORDERBOOK_VOLUME_THRESHOLD = 6
COEFFICIENT_VOLUME_THRESHOLD = 4
