import asyncio
import aiohttp
import logging
import json
from models.models import WsCandle


logger = logging.getLogger(__name__)

class BinanceWS:
    """Данный класс отвечает за Websocket Streams, подключенные к Binance Websocket API"""

    BASE_URL = "wss://stream.binance.com:9443/ws"

    def __init__(self, session: aiohttp.ClientSession):
        self._session = session
        
        self.__proxy = {
            'http': 'http://n6KPSuii:FtigEyZZ@138.249.96.10:64698',
            'https': 'http://n6KPSuii:FtigEyZZ@138.249.96.10:64698',
        }

    async def listen_klines(self, symbol: str, interval: str, average_volume: float, move_threshold: float):
        """Слушает Websocket Streams Binance и отправляет алерты при нахождении аномалии"""
        stream_name = f"{symbol.lower()}@kline_{interval}"
        url = f"{self.BASE_URL}/{stream_name}"
        
        current_candle_start_time = None
        volume_alert_sent_for_current_candle = False
        move_alert_sent_for_current_candle = False
        
        volume_threshold = average_volume * 4.0 
        
        while True:
            try:
                logger.info(f"Подключаемся к BinanceWS {interval} для {symbol.upper()} (klines)")
                async with self._session.ws_connect(url=url, heartbeat=30, proxy=self.__proxy["http"]) as ws:
                    async for msg in ws:
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            data = json.loads(msg.data)['k']
                            kline = WsCandle(
                                start_time=int(data["t"]),
                                volume=float(data["v"]),
                                close_price=float(data["c"]),
                                open_price=float(data["o"])
                            )
                            
                            kline_start_time = kline.start_time
                            current_volume = kline.volume

                            current_move = (abs(kline.close_price - kline.open_price) / kline.open_price) * 100
                            
                            if current_candle_start_time != kline_start_time:
                                current_candle_start_time = kline_start_time
                                volume_alert_sent_for_current_candle = False
                                move_alert_sent_for_current_candle = False
                                logger.info(f"Новая свеча {interval} началась. Предохранитель по объему и движению сброшен (klines)")

                            if current_volume >= volume_threshold and not volume_alert_sent_for_current_candle:
                                logger.warning(
                                    f"АНОМАЛЬНЫЙ ОБЪЕМ! | {symbol.upper()} | "
                                    f"Объем: {current_volume} превысил порог {volume_threshold}!"
                                )
                                
                                # Здесь вызываем функцию отправки сообщения в Telegram
                                
                                volume_alert_sent_for_current_candle = True

                            if current_move >= move_threshold and not move_alert_sent_for_current_candle:
                                logger.warning(
                                    f"РЕЗКОЕ ДВИЖЕНИЕ! | {symbol.upper()} | "
                                    f"Движение: {current_move} превысило порог {move_threshold}!"
                                )

                                # Здесь вызываем функцию отправки сообщения в Telegram

                                move_alert_sent_for_current_candle = True
                            
                                
                        elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR):
                            logger.error("WS соединение закрыто биржей (klines)... Переподключение")
                            break
                            
            except Exception as e:
                logger.error(f"Обрыв соединения с WS (klines): {e}. Реконнект через 5 сек...")
                await asyncio.sleep(5)
