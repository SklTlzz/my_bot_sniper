import aiohttp
import logging
import asyncio
from datetime import datetime, timezone, timedelta

from models.models import RestOrderBook, RestCandle
from config import PROXY


def msk_time_converter(*args):
    msk_tz = timezone(timedelta(hours=3))
    return datetime.now(msk_tz).timetuple()

logging.Formatter.converter = msk_time_converter
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


class BinanceRest:
    """Данный класс отвечает за REST запросы на Binance REST API"""

    REST_URL_DEPTH = "https://api.binance.com/api/v3/depth"
    REST_URL_KLINES = "https://api.binance.com/api/v3/klines"

    def __init__(self, session: aiohttp.ClientSession):
        self._session = session
        
        self.__proxy = {
            'http': PROXY,
        }

    async def get_spot_order_book(self, symbol: str, limit: int = 1000) -> RestOrderBook:
        """
            Получает стакан для указанной пары \n
            limit: количество уровней стакана. Допустимые значения: 5, 10, 20, 50, 100, 500, 1000, 5000
        """
        url = self.REST_URL_DEPTH
        
        params = {
            "symbol": symbol.upper(),
            "limit": limit
        }

        try:
            async with self._session.get(url=url, params=params, proxy=self.__proxy["http"]) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"Успешно получен стакан по {symbol}; limit: {limit}")
                    return RestOrderBook(
                        bids=data["bids"],
                        asks=data["asks"]
                    )
                else:
                    error_msg = await response.text()
                    logger.error(f"Ошибка API Binance (стакан): HTTP {response.status} - {error_msg}")
                    return None
        except Exception as e:
            logger.error(f"Ошибка соединения с Binance (стакан): {e}")
            return None

    async def get_spot_candles(self, symbol: str, interval: str, limit: int = 100) -> list[RestCandle]:
        """
            Получает свечи для указанной пары \n
                interval: '1m', '3m', '5m', '15m', '30m', '1h' и тд \n
                limit: количество свечей (максимум 1000)
        """
        url = self.REST_URL_KLINES

        params = {
            "symbol": symbol.upper(),
            "interval": interval,
            "limit": limit
        }

        try:
            async with self._session.get(url=url, params=params, proxy=self.__proxy["http"]) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"Успешно получены свечи по {symbol}; interval: {interval}; limit: {limit}")
                    return [
                        RestCandle(
                            openPrice=float(item[1]),
                            highPrice=float(item[2]),
                            lowPrice=float(item[3]),
                            closePrice=float(item[4]),
                            volume=float(item[7])
                        ) for item in data
                    ]
                else:
                    error_msg = await response.text()
                    logger.error(f"Ошибка API Binance (свечи): HTTP {response.status} - {error_msg}")
                    return None
        except Exception as e:
            logger.error(f"Ошибка соединения с Binance (свечи): {e}")
            return None
