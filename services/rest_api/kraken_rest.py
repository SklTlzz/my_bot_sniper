import logging
import aiohttp

from config import PROXY
from models.models import RestOrderBook, RestCandle

logger = logging.getLogger(__name__)

class KrakenRest:
    """Данный класс отвечает за REST запросы на Kraken API V1"""
    
    REST_URL_DEPTH = "https://api.kraken.com/0/public/Depth"
    REST_URL_KLINES = "https://api.kraken.com/0/public/OHLC"

    def __init__(self, session: aiohttp.ClientSession):
        self._session = session
        self.__proxy = {
            "http": PROXY
        }

    async def get_spot_order_book(self, symbol: str, limit: int = 100) -> RestOrderBook | None:
        """
            Получает стакан для указанной пары на Kraken \n
            Формат пары слитный (BTCUSDT) \n
            limit: кол-во уровней
        """
        url = self.REST_URL_DEPTH
        
        params = {
            "pair": symbol.upper(),
            "count": limit
        }

        try:
            async with self._session.get(url=url, params=params, proxy=self.__proxy["http"]) as response:
                if response.status == 200:
                    res = await response.json()
                    
                    if not res.get("error"):
                        result_data = res.get("result", {})
                        if not result_data:
                            return None
                            
                        pair_key = list(result_data.keys())[0]
                        data = result_data[pair_key]
                        
                        logger.info(f"Успешно получен стакан (Kraken) по {symbol}; limit: {limit}")
                        
                        return RestOrderBook(
                            bids=data.get("bids", []),
                            asks=data.get("asks", [])
                        )
                    else:
                        logger.error(f"Ошибка API Kraken (стакан): {res.get('error')}")
                        return None
                else:
                    error_msg = await response.text()
                    logger.error(f"HTTP Ошибка Kraken (стакан): {response.status} - {error_msg}")
                    return None
        except Exception as e:
            logger.error(f"Ошибка соединения с Kraken (стакан): {e}")
            return None

    async def get_spot_candles(self, symbol: str, interval: str = "5m", limit: int = 24) -> list[RestCandle] | None:
        """
            Получает свечи для указанной пары на Kraken \n
            limit: кол-во свечек
        """
        url = self.REST_URL_KLINES
        
        interval_map = {
            "1m": 1, "5m": 5, "15m": 15, 
            "30m": 30, "1h": 60, "4h": 240, "1d": 1440
        }
        kraken_interval = interval_map.get(interval, 5)

        params = {
            "pair": symbol.upper(),
            "interval": kraken_interval
        }

        try:
            async with self._session.get(url=url, params=params, proxy=self.__proxy["http"]) as response:
                if response.status == 200:
                    res = await response.json()
                    
                    if not res.get("error"):
                        result_data = res.get("result", {})
                        result_data.pop("last", None)
                        
                        if not result_data:
                            return None
                            
                        pair_key = list(result_data.keys())[0]
                        data = result_data[pair_key]
                        
                        logger.info(f"Успешно получены свечи (Kraken) по {symbol}; interval: {interval}; limit: {limit}")
                        
                        candles = []
                        for item in data[-limit:]:
                            close_price = float(item[4])
                            base_volume = float(item[6])
                            
                            quote_volume = base_volume * close_price
                            
                            candles.append(RestCandle(
                                open_price=float(item[1]),
                                high_price=float(item[2]),
                                low_price=float(item[3]),
                                close_price=close_price,
                                volume=quote_volume 
                            ))
                        
                        return candles
                    else:
                        logger.error(f"Ошибка API Kraken (свечи): {res.get('error')}")
                        return None
                else:
                    error_msg = await response.text()
                    logger.error(f"HTTP Ошибка Kraken (свечи): {response.status} - {error_msg}")
                    return None
        except Exception as e:
            logger.error(f"Ошибка соединения с Kraken (свечи): {e}")
            return None
