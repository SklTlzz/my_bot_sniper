import logging
import aiohttp

from config import PROXY
from models.models import RestOrderBook, RestCandle


logger = logging.getLogger(__name__)

class GateRest:
    REST_URL_DEPTH = "https://api.gateio.ws/api/v4/spot/order_book"
    REST_URL_KLINES = "https://api.gateio.ws/api/v4/spot/candlesticks"

    def __init__(self, session: aiohttp.ClientSession):
        self._session = session

        self.__proxy = {
            "http": PROXY
        }

    async def get_spot_order_book(self, symbol: str, limit: int = 100) -> RestOrderBook | None:
        """
            Получает стакан для указанной пары на Gate \n
            Gate ожидает формат пары через подчеркивание (BTC_USDT) \n
            limit: кол-во уровней стакана
        """

        url = self.REST_URL_DEPTH

        formatted_symbol = symbol.upper()[:-4] + "_" + symbol.upper()[-4:]
        
        params = {
            "currency_pair": formatted_symbol,
            "limit": limit
        }

        try:
            async with self._session.get(url=url, params=params, proxy=self.__proxy["http"]) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"Успешно получен стакан (Gate) по {symbol}; limit: {limit}")
                    return RestOrderBook(
                        bids=data.get("bids", []),
                        asks=data.get("asks", [])
                    )
                else:
                    error_msg = await response.text()
                    logger.error(f"Ошибка API Gate (стакан): HTTP {response.status} - {error_msg}")
                    return None
        except Exception as e:
            logger.error(f"Ошибка соединения с Gate (стакан): {e}")
            return None

    async def get_spot_candles(self, symbol: str, interval: str = "5m", limit: int = 24) -> list[RestCandle] | None:
        """
            Получает свечи для указанной пары на Gate \n
            Тикер должен быть с нижним подчеркиванием (BTC_USDT) \n
            interval: интервал свечи \n
            limit: кол-во свечек
        """
        url = self.REST_URL_KLINES

        params = {
            "currency_pair": symbol.upper(),
            "interval": interval,
            "limit": limit
        }

        try:
            async with self._session.get(url=url, params=params, proxy=self.__proxy["http"]) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"Успешно получены свечи (Gate) по {symbol}; interval: {interval}; limit: {limit}")
                    return [
                        RestCandle(
                            open_price=float(item[5]),
                            high_price=float(item[3]),
                            low_price=float(item[4]),
                            close_price=float(item[2]),
                            volume=float(item[1])
                        ) for item in data
                    ]
                else:
                    error_msg = await response.text()
                    logger.error(f"Ошибка API Gate (свечи): HTTP {response.status} - {error_msg}")
                    return None
        except Exception as e:
            logger.error(f"Ошибка соединения с Gate (свечи): {e}")
            return None
