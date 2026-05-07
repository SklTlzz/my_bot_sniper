import logging
import aiohttp
import asyncio
import aiosqlite
from aiogram import Bot, Dispatcher
from datetime import datetime, timezone, timedelta
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from services.rest_api.binance_rest import BinanceRest
from analyser.orderbook import Analyser
from config import BOT_TOKEN, PROXY, BOSS_ID
from handlers.commands import router as cmds_router
from db.database import Database
from db.alerts_db import AlertsDatabase


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

        await alerts_db.create_table()

        tg_session = AiohttpSession(proxy=PROXY)

        bot = Bot(token=BOT_TOKEN, session=tg_session, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
        dp = Dispatcher()

        dp.include_router(cmds_router)

        # async with aiohttp.ClientSession() as session:
        #     binance = BinanceRest(session=session)
        #     order_book = await binance.get_spot_order_book("TAOUSDT", limit=100)

        #     if order_book:
        #         logger.info(f"Стакан получен!")
        #         analyser = Analyser(data=order_book)
        #         logger.info("Анализатор успешно инициализирован!")

        #         result = analyser.prepare_data(volume_threshold=5.0)

        #         if result["asks"]:
        #             logger.info(f"Нашли плотности на продажу: {result['asks']}")
        #         if result["bids"]:
        #             logger.info(f"Нашли плотности на покупку: {result['bids']}")

        await dp.start_polling(bot, db=database, alerts_db=alerts_db)

if __name__ == "__main__":
    asyncio.run(main())
