import logging
import aiohttp
import asyncio
import aiosqlite
from aiogram import Bot, Dispatcher
from datetime import datetime, timezone, timedelta
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import BOT_TOKEN, PROXY, BOSS_ID
from handlers.commands import router as cmds_router
from handlers.tracker import Tracker
from db.database import Database
from db.alerts_db import AlertsDatabase

from services.rest_api.binance_rest import BinanceRest
from services.rest_api.bingx_rest import BingXRest
from services.rest_api.bitget_rest import BitgetRest
from services.rest_api.bybit_rest import BybitRest
from services.rest_api.gate_rest import GateRest
from services.rest_api.kraken_rest import KrakenRest
from services.rest_api.kucoin_rest import KucoinRest
from services.rest_api.mexc_rest import MexcRest
from services.rest_api.okx_rest import OkxRest

from services.websockets.binance_ws import BinanceWS
from services.websockets.bingx_ws import BingXWS
from services.websockets.bitget_ws import BitgetWS
from services.websockets.bybit_ws import BybitWS
from services.websockets.gate_ws import GateWS
from services.websockets.kraken_ws import KrakenWS
from services.websockets.kucoin_ws import KucoinWS
from services.websockets.mexc_ws import MexcWS
from services.websockets.okx_ws import OkxWS


def msk_time_converter(*args):
    msk_tz = timezone(timedelta(hours=3))
    return datetime.now(msk_tz).timetuple()

logging.Formatter.converter = msk_time_converter
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


async def main():
    """Главная функция проекта. Структурирует, вызывает и запускает все файлы проекта"""
    async with aiosqlite.connect("ids_database.db") as db:
        database = Database(db_connection=db)
        alerts_db = AlertsDatabase(db_connection=db)

        await database.create_table()
        await database.add_user(tg_id=BOSS_ID)

        await alerts_db.delete_all_alerts()
        await alerts_db.create_table()

        tg_session = AiohttpSession(proxy=PROXY)

        bot = Bot(token=BOT_TOKEN, session=tg_session, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
        dp = Dispatcher()

        dp.include_router(cmds_router)

        async with aiohttp.ClientSession() as session:
            binance_rest = BinanceRest(session=session)
            bingx_rest = BingXRest(session=session)
            bitget_rest = BitgetRest(session=session)
            bybit_rest = BybitRest(session=session)
            gate_rest = GateRest(session=session)
            kraken_rest = KrakenRest(session=session)
            kucoin_rest = KucoinRest(session=session)
            mexc_rest = MexcRest(session=session)
            okx_rest = OkxRest(session=session)

            binance_ws = BinanceWS(session=session, bot=bot)
            bingx_ws = BingXWS(session=session, bot=bot)
            bitget_ws = BitgetWS(session=session, bot=bot)
            bybit_ws = BybitWS(session=session, bot=bot)
            gate_ws = GateWS(session=session, bot=bot)
            kraken_ws = KrakenWS(session=session, bot=bot)
            kucoin_ws = KucoinWS(session=session, bot=bot)
            mexc_ws = MexcWS(session=session, bot=bot)
            okx_ws = OkxWS(session=session, bot=bot)

            clients = {
                "binance": {"rest": binance_rest, "ws": binance_ws},
                "bingx": {"rest": bingx_rest, "ws": bingx_ws},
                "bitget": {"rest": bitget_rest, "ws": bitget_ws},
                "bybit": {"rest": bybit_rest, "ws": bybit_ws},
                "gate": {"rest": gate_rest, "ws": gate_ws},
                "kraken": {"rest": kraken_rest, "ws": kraken_ws},
                "kucoin": {"rest": kucoin_rest, "ws": kucoin_ws},
                "mexc": {"rest": mexc_rest, "ws": mexc_ws},
                "okx": {"rest": okx_rest, "ws": okx_ws},
            }

            tracker = Tracker(bot=bot, alerts_db=alerts_db, clients=clients)
            asyncio.create_task(tracker.wait_for_alert())

            await dp.start_polling(bot, db=database, alerts_db=alerts_db)

if __name__ == "__main__":
    asyncio.run(main())
