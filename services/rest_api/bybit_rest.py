import logging
import aiohttp

from config import PROXY
from models.models import RestOrderBook, RestCandle

logger = logging.getLogger(__name__)

class BybitRest:
    """Данный класс отвечает за REST запросы на Bybit API"""
    
    REST_URL_DEPTH = "https://api.bybit.com/v5/market/orderbook"
    REST_URL_KLINES = "https://api.bybit.com/v5/market/kline"

    def __init__(self, session: aiohttp.ClientSession):
        self._session = session
        self.__proxy = {
            "http": PROXY
        }

    async def get_spot_order_book(self, symbol: str, limit: int = 100) -> RestOrderBook | None:
        """
            Получает стакан для указанной пары на Bybit \n
            Формат пары слитный (BTCUSDT) \n
            limit: кол-во уровней стакана (по умолчанию 50)
        """
        url = self.REST_URL_DEPTH
        
        params = {
            "category": "spot",
            "symbol": symbol.upper(),
            "limit": limit
        }

        try:
            async with self._session.get(url=url, params=params, proxy=self.__proxy["http"]) as response:
                if response.status == 200:
                    res = await response.json()
                    
                    if res.get("retCode") == 0:
                        data = res.get("result", {})
                        logger.info(f"Успешно получен стакан (Bybit) по {symbol}; limit: {limit}")
                        
                        return RestOrderBook(
                            bids=data.get("b", []),
                            asks=data.get("a", [])
                        )
                    else:
                        logger.error(f"Ошибка API Bybit (стакан): {res.get('retMsg')}")
                        return None
                else:
                    error_msg = await response.text()
                    logger.error(f"HTTP Ошибка Bybit (стакан): {response.status} - {error_msg}")
                    return None
        except Exception as e:
            logger.error(f"Ошибка соединения с Bybit (стакан): {e}")
            return None

    async def get_spot_candles(self, symbol: str, interval: str = "5m", limit: int = 24) -> list[RestCandle] | None:
        """
            Получает свечи для указанной пары на Bybit \n
            limit: кол-во свечек
        """
        url = self.REST_URL_KLINES
        
        interval_map = {
            "1m": "1", "5m": "5", "15m": "15", 
            "30m": "30", "1h": "60", "4h": "240", "1d": "D"
        }
        bybit_interval = interval_map.get(interval, "5")

        params = {
            "category": "spot", 
            "symbol": symbol.upper(),
            "interval": bybit_interval,
            "limit": limit
        }

        try:
            async with self._session.get(url=url, params=params, proxy=self.__proxy["http"]) as response:
                if response.status == 200:
                    res = await response.json()
                    
                    if res.get("retCode") == 0:
                        data = res.get("result", {}).get("list", [])
                        logger.info(f"Успешно получены свечи (Bybit) по {symbol}; interval: {interval}; limit: {limit}")
                        
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
                        logger.error(f"Ошибка API Bybit (свечи): {res.get('retMsg')}")
                        return None
                else:
                    error_msg = await response.text()
                    logger.error(f"HTTP Ошибка Bybit (свечи): {response.status} - {error_msg}")
                    return None
        except Exception as e:
            logger.error(f"Ошибка соединения с Bybit (свечи): {e}")
            return None
        