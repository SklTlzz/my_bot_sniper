import asyncio
import aiohttp
import logging
import json
from aiogram import Bot

from config import PROXY, COEFFICIENT_VOLUME_THRESHOLD
from models.models import WsCandle

logger = logging.getLogger(__name__)

class KrakenWS:
    """Данный класс отвечает за Websockets на Kraken"""

    BASE_URL = "wss://ws.kraken.com/v2"

    def __init__(self, session: aiohttp.ClientSession, bot: Bot):
        self._session = session
        self.bot = bot
        self.__proxy = {
            'http': PROXY,
        }

    async def send_message(self, text: str, tg_id: int):
        await self.bot.send_message(chat_id=tg_id, text=text)

    async def listen_klines(self, symbol: str, interval: str, average_volume: float, move_threshold: float, tg_id: int):
        """Слушает Websocket Kraken и отправляет алерты при нахождении аномалии"""
        url = self.BASE_URL
        
        formatted_symbol = symbol.upper()[:-4] + "/" + symbol.upper()[-4:]
        
        ws_interval_map = {
            "1m": 1, "5m": 5, "15m": 15, 
            "30m": 30, "1h": 60, "4h": 240, "1d": 1440
        }
        kraken_interval = ws_interval_map.get(interval, 5)
        
        current_candle_start_time = None
        volume_alert_sent_for_current_candle = False
        move_alert_sent_for_current_candle = False
        volume_threshold = average_volume * COEFFICIENT_VOLUME_THRESHOLD 
        
        subscribe_payload = {
            "method": "subscribe",
            "params": {
                "channel": "ohlc",
                "symbol": [formatted_symbol],
                "interval": kraken_interval
            }
        }

        while True:
            try:
                logger.info(f"Подключаемся к KrakenWS {interval} для {formatted_symbol}")
                async with self._session.ws_connect(url=url, heartbeat=25, proxy=self.__proxy["http"]) as ws:
                    
                    await ws.send_json(subscribe_payload)

                    async for msg in ws:
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            response = json.loads(msg.data)
                            
                            if response.get("channel") != "ohlc" or response.get("type") != "update":
                                continue

                            if "data" in response and len(response["data"]) > 0:
                                data = response["data"][0]
                                
                                close_price = float(data.get("close", 0))
                                base_volume = float(data.get("volume", 0))
                                quote_volume = base_volume * close_price
                                
                                kline_start_time = data.get("timestamp")
                                
                                kline = WsCandle(
                                    start_time=0,
                                    volume=quote_volume, 
                                    close_price=close_price,
                                    open_price=float(data.get("open", 0))
                                )
                                
                                current_volume = kline.volume
                                current_move = ((kline.close_price - kline.open_price) / kline.open_price) * 100
                                
                                if current_candle_start_time != kline_start_time:
                                    current_candle_start_time = kline_start_time
                                    volume_alert_sent_for_current_candle = False
                                    move_alert_sent_for_current_candle = False
                                    logger.info(f"Новая свеча {interval} началась (Kraken). Предохранитель по объему и движению сброшен (klines)")

                                if current_volume >= volume_threshold and not volume_alert_sent_for_current_candle:
                                    text = (
                                        f"==============================================\n"
                                        f"🚨 АНОМАЛЬНЫЙ ОБЪЕМ! | {formatted_symbol} | Kraken\n"
                                        f"ℹ️ Объем: {round(current_volume, 2)} превысил порог {round(volume_threshold, 2)}!\n"
                                        f"=============================================="
                                    )
                                    logger.warning((f"АНОМАЛЬНЫЙ ОБЪЕМ! | {formatted_symbol} | Kraken | "
                                        f"Объем: {round(current_volume, 2)} превысил порог {round(volume_threshold, 2)}!"))
                                    await self.send_message(text=text, tg_id=tg_id)
                                    volume_alert_sent_for_current_candle = True

                                if abs(current_move) >= move_threshold and not move_alert_sent_for_current_candle:
                                    text = (
                                        f"==============================================\n"
                                        f"🚨 РЕЗКОЕ ДВИЖЕНИЕ! | {formatted_symbol} | Kraken\n"
                                        f"ℹ️ Движение: {round(current_move, 2)}% превысило порог {move_threshold}%!\n"
                                        f"=============================================="
                                    )
                                    logger.warning((f"РЕЗКОЕ ДВИЖЕНИЕ! | {formatted_symbol} | Kraken | "
                                        f"Движение: {round(current_move, 2)}% превысило порог {move_threshold}%!"))
                                    await self.send_message(text=text, tg_id=tg_id)
                                    move_alert_sent_for_current_candle = True
                                
                        elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR):
                            logger.error("WS соединение закрыто биржей Kraken... Переподключение")
                            break
                            
            except Exception as e:
                logger.error(f"Обрыв соединения с WS Kraken: {e}. Реконнект через 5 сек...")
                await asyncio.sleep(5)
