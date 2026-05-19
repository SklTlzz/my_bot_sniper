import logging
import aiohttp

from config import PROXY
from models.models import RestOrderBook, RestCandle

logger = logging.getLogger(__name__)

class MexcRest:
    """Данный класс отвечает за REST запросы на MEXC API"""
    
    REST_URL_DEPTH = "https://api.mexc.com/api/v3/depth"
    REST_URL_KLINES = "https://api.mexc.com/api/v3/klines"

    def __init__(self, session: aiohttp.ClientSession):
        self._session = session
        self.__proxy = {
            "http": PROXY
        }

    async def get_spot_order_book(self, symbol: str, limit: int = 100) -> RestOrderBook | None:
        """
            Получает стакан для указанной пары на MEXC \n
            Формат пары слитный (BTCUSDT) \n
            limit: кол-во уровней стакана
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
                    logger.info(f"Успешно получен стакан (MEXC) по {symbol}; limit: {limit}")
                    return RestOrderBook(
                        bids=data.get("bids", []),
                        asks=data.get("asks", [])
                    )
                else:
                    error_msg = await response.text()
                    logger.error(f"Ошибка API MEXC (стакан): HTTP {response.status} - {error_msg}")
                    return None
        except Exception as e:
            logger.error(f"Ошибка соединения с MEXC (стакан): {e}")
            return None

    async def get_spot_candles(self, symbol: str, interval: str = "5m", limit: int = 24) -> list[RestCandle] | None:
        """
            Получает свечи для указанной пары на MEXC \n
            limit: кол-во свечек
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
                    logger.info(f"Успешно получены свечи (MEXC) по {symbol}; interval: {interval}; limit: {limit}")
                    return [
                        RestCandle(
                            open_price=float(item[1]),
                            high_price=float(item[2]),
                            low_price=float(item[3]),
                            close_price=float(item[4]),
                            volume=float(item[7])
                        ) for item in data
                    ]
                else:
                    error_msg = await response.text()
                    logger.error(f"Ошибка API MEXC (свечи): HTTP {response.status} - {error_msg}")
                    return None
        except Exception as e:
            logger.error(f"Ошибка соединения с MEXC (свечи): {e}")
            return None
