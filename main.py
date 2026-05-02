import logging
import aiohttp
import asyncio
from datetime import datetime, timezone, timedelta

from services.rest_api.binance_rest import BinanceRest
from analyser.orderbook import Analyser


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
    async with aiohttp.ClientSession() as session:
        binance = BinanceRest(session=session)
        order_book = await binance.get_spot_order_book("TAOUSDT", limit=100)

        if order_book:
            logger.info(f"Стакан получен!")
            analyser = Analyser(data=order_book)
            logger.info("Анализатор успешно инициализирован!")

            result = analyser.prepare_data(volume_threshold=5.0)

            if result["asks"]:
                logger.info(f"Нашли плотности на продажу: {result['asks']}")
            if result["bids"]:
                logger.info(f"Нашли плотности на покупку: {result['bids']}")

if __name__ == "__main__":
    asyncio.run(main())
