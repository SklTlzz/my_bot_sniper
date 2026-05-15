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
from services.websockets.binance_ws import BinanceWS


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
            binance_ws = BinanceWS(session=session, bot=bot)

            tracker = Tracker(bot=bot, alerts_db=alerts_db, binance_ws=binance_ws, binance_rest=binance_rest)
            asyncio.create_task(tracker.wait_for_alert())

            await dp.start_polling(bot, db=database, alerts_db=alerts_db)

if __name__ == "__main__":
    asyncio.run(main())
