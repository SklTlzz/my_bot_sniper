import logging
import aiohttp

from config import PROXY
from models.models import RestOrderBook, RestCandle

logger = logging.getLogger(__name__)

class KucoinRest:
    """Данный класс отвечает за REST запросы на KuCoin API"""
    
    REST_URL_DEPTH = "https://api.kucoin.com/api/v1/market/orderbook/level2_100"
    REST_URL_KLINES = "https://api.kucoin.com/api/v1/market/candles"

    def __init__(self, session: aiohttp.ClientSession):
        self._session = session
        self.__proxy = {
            "http": PROXY
        }

    async def get_spot_order_book(self, symbol: str, limit: int = 100) -> RestOrderBook | None:
        """
            Получает стакан для указанной пары на KuCoin \n
            Формат пары через дефис (BTC-USDT)
        """
        url = self.REST_URL_DEPTH
        
        formatted_symbol = symbol.upper()[:-4] + "-" + symbol.upper()[-4:]

        params = {
            "symbol": formatted_symbol
        }

        try:
            async with self._session.get(url=url, params=params, proxy=self.__proxy["http"]) as response:
                if response.status == 200:
                    res = await response.json()
                    
                    if res.get("code") == "200000":
                        data = res.get("data", {})
                        logger.info(f"Успешно получен стакан (KuCoin) по {symbol}; limit: 100")
                        
                        return RestOrderBook(
                            bids=data.get("bids", []),
                            asks=data.get("asks", [])
                        )
                    else:
                        logger.error(f"Ошибка API KuCoin (стакан): {res.get('msg')}")
                        return None
                else:
                    error_msg = await response.text()
                    logger.error(f"HTTP Ошибка KuCoin (стакан): {response.status} - {error_msg}")
                    return None
        except Exception as e:
            logger.error(f"Ошибка соединения с KuCoin (стакан): {e}")
            return None

    async def get_spot_candles(self, symbol: str, interval: str = "5m", limit: int = 24) -> list[RestCandle] | None:
        """
            Получает свечи для указанной пары на KuCoin \n
            limit: кол-во свечек
        """
        url = self.REST_URL_KLINES
        formatted_symbol = symbol.upper()[:-4] + "-" + symbol.upper()[-4:]
        
        interval_map = {
            "1m": "1min", "5m": "5min", "15m": "15min", 
            "30m": "30min", "1h": "1hour", "4h": "4hour", "1d": "1day"
        }
        kucoin_interval = interval_map.get(interval, "5min")

        params = {
            "symbol": formatted_symbol,
            "type": kucoin_interval
        }

        try:
            async with self._session.get(url=url, params=params, proxy=self.__proxy["http"]) as response:
                if response.status == 200:
                    res = await response.json()
                    
                    if res.get("code") == "200000":
                        data = res.get("data", [])
                        logger.info(f"Успешно получены свечи (KuCoin) по {symbol}; interval: {interval}; limit: {limit}")
                        
                        candles = [
                            RestCandle(
                                open_price=float(item[1]),
                                high_price=float(item[3]),
                                low_price=float(item[4]),
                                close_price=float(item[2]),
                                volume=float(item[6])
                            ) for item in data[:limit]
                        ]
                        
                        return candles[::-1]
                    else:
                        logger.error(f"Ошибка API KuCoin (свечи): {res.get('msg')}")
                        return None
                else:
                    error_msg = await response.text()
                    logger.error(f"HTTP Ошибка KuCoin (свечи): {response.status} - {error_msg}")
                    return None
        except Exception as e:
            logger.error(f"Ошибка соединения с KuCoin (свечи): {e}")
            return None
