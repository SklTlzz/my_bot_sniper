import logging
import aiohttp

from models.models import RestOrderBook, RestCandle

logger = logging.getLogger(__name__)

class BingXRest:
    """Данный класс отвечает за REST запросы на BingX Spot API"""
    
    REST_URL_DEPTH = "https://open-api.bingx.com/openApi/spot/v1/market/depth"
    REST_URL_KLINES = "https://open-api.bingx.com/openApi/spot/v2/market/kline"

    def __init__(self, session: aiohttp.ClientSession):
        self._session = session

    async def get_spot_order_book(self, symbol: str, limit: int = 100) -> RestOrderBook | None:
        """
            Получает стакан для указанной пары на BingX \n
            Формат пары через дефис (BTC-USDT)
        """
        url = self.REST_URL_DEPTH
        formatted_symbol = symbol.upper()[:-4] + "-" + symbol.upper()[-4:]

        params = {
            "symbol": formatted_symbol,
            "limit": limit
        }

        try:
            async with self._session.get(url=url, params=params) as response:
                if response.status == 200:
                    res = await response.json()
                    
                    if res.get("code") == 0:
                        data = res.get("data", {})
                        logger.info(f"Успешно получен стакан (BingX) по {symbol}; limit: {limit}")
                        
                        return RestOrderBook(
                            bids=data.get("bids", []),
                            asks=data.get("asks", [])
                        )
                    else:
                        logger.error(f"Ошибка API BingX (стакан): {res.get('msg')}")
                        return None
                else:
                    error_msg = await response.text()
                    logger.error(f"HTTP Ошибка BingX (стакан): {response.status} - {error_msg}")
                    return None
        except Exception as e:
            logger.error(f"Ошибка соединения с BingX (стакан): {e}")
            return None

    async def get_spot_candles(self, symbol: str, interval: str = "5m", limit: int = 24) -> list[RestCandle] | None:
        """
            Получает свечи для указанной пары на BingX \n
            Формат пары через дефис (BTC-USDT)
            limit: кол-во свечек
        """
        url = self.REST_URL_KLINES
        formatted_symbol = symbol.upper()[:-4] + "-" + symbol.upper()[-4:]

        params = {
            "symbol": formatted_symbol,
            "interval": interval,
            "limit": limit
        }

        try:
            async with self._session.get(url=url, params=params) as response:
                if response.status == 200:
                    res = await response.json()
                    
                    if res.get("code") == 0:
                        data = res.get("data", [])
                        logger.info(f"Успешно получены свечи (BingX) по {symbol}; interval: {interval}; limit: {limit}")
                        
                        candles = [
                            RestCandle(
                                open_price=float(item[1]),
                                high_price=float(item[2]),
                                low_price=float(item[3]),
                                close_price=float(item[4]),
                                volume=float(item[7])
                            ) for item in data
                        ]
                        return candles
                    else:
                        logger.error(f"Ошибка API BingX (свечи): {res.get('msg')}")
                        return None
                else:
                    error_msg = await response.text()
                    logger.error(f"HTTP Ошибка BingX (свечи): {response.status} - {error_msg}")
                    return None
        except Exception as e:
            logger.error(f"Ошибка соединения с BingX (свечи): {e}")
            return None
