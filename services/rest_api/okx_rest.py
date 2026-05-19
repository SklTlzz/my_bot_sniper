import logging
import aiohttp

from config import PROXY
from models.models import RestOrderBook, RestCandle

logger = logging.getLogger(__name__)

class OkxRest:
    """Данный класс отвечает за REST запросы на OKX API"""
    
    REST_URL_DEPTH = "https://www.okx.com/api/v5/market/books"
    REST_URL_KLINES = "https://www.okx.com/api/v5/market/candles"

    def __init__(self, session: aiohttp.ClientSession):
        self._session = session
        self.__proxy = {
            "http": PROXY
        }

    async def get_spot_order_book(self, symbol: str, limit: int = 100) -> RestOrderBook | None:
        """
            Получает стакан для указанной пары на OKX \n
            Формат пары через дефис (BTC-USDT) \n
            limit (sz): кол-во уровней стакана (макс 400)
        """
        url = self.REST_URL_DEPTH
        
        formatted_symbol = symbol.upper()[:-4] + "-" + symbol.upper()[-4:]

        params = {
            "instId": formatted_symbol,
            "sz": limit
        }

        try:
            async with self._session.get(url=url, params=params, proxy=self.__proxy["http"]) as response:
                if response.status == 200:
                    res = await response.json()
                    
                    if res.get("code") == "0":
                        data = res.get("data", [{}])[0]
                        logger.info(f"Успешно получен стакан (OKX) по {symbol}; limit: {limit}")
                        
                        return RestOrderBook(
                            bids=data.get("bids", []),
                            asks=data.get("asks", [])
                        )
                    else:
                        logger.error(f"Ошибка API OKX (стакан): {res.get('msg')}")
                        return None
                else:
                    error_msg = await response.text()
                    logger.error(f"HTTP Ошибка OKX (стакан): {response.status} - {error_msg}")
                    return None
        except Exception as e:
            logger.error(f"Ошибка соединения с OKX (стакан): {e}")
            return None

    async def get_spot_candles(self, symbol: str, interval: str = "5m", limit: int = 24) -> list[RestCandle] | None:
        """
            Получает свечи для указанной пары на OKX \n
            limit: кол-во свечек
        """
        url = self.REST_URL_KLINES
        formatted_symbol = symbol.upper()[:-4] + "-" + symbol.upper()[-4:]
        
        interval_map = {
            "1m": "1m", "5m": "5m", "15m": "15m", 
            "30m": "30m", "1h": "1H", "4h": "4H", "1d": "1D"
        }
        okx_interval = interval_map.get(interval, "5m")

        params = {
            "instId": formatted_symbol,
            "bar": okx_interval,
            "limit": limit
        }

        try:
            async with self._session.get(url=url, params=params, proxy=self.__proxy["http"]) as response:
                if response.status == 200:
                    res = await response.json()
                    
                    if res.get("code") == "0":
                        data = res.get("data", [])
                        logger.info(f"Успешно получены свечи (OKX) по {symbol}; interval: {interval}; limit: {limit}")
                        
                        candles = [
                            RestCandle(
                                open_price=float(item[1]),
                                high_price=float(item[2]),
                                low_price=float(item[3]),
                                close_price=float(item[4]),
                                volume=float(item[6]) 
                            ) for item in data
                        ]
                        
                        return candles[::-1]
                    else:
                        logger.error(f"Ошибка API OKX (свечи): {res.get('msg')}")
                        return None
                else:
                    error_msg = await response.text()
                    logger.error(f"HTTP Ошибка OKX (свечи): {response.status} - {error_msg}")
                    return None
        except Exception as e:
            logger.error(f"Ошибка соединения с OKX (свечи): {e}")
            return None
