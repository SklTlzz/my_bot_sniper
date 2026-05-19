import asyncio
import aiohttp
import logging
import json
from aiogram import Bot

from config import PROXY, COEFFICIENT_VOLUME_THRESHOLD
from models.models import WsCandle

logger = logging.getLogger(__name__)

class MexcWS:
    """Данный класс отвечает за Websockets на MEXC"""

    BASE_URL = "wss://wbs.mexc.com/ws"

    def __init__(self, session: aiohttp.ClientSession, bot: Bot):
        self._session = session
        self.bot = bot
        self.__proxy = {
            'http': PROXY,
        }

    async def send_message(self, text: str, tg_id: int):
        await self.bot.send_message(chat_id=tg_id, text=text)

    async def listen_klines(self, symbol: str, interval: str, average_volume: float, move_threshold: float, tg_id: int):
        """Слушает Websocket MEXC и отправляет алерты при нахождении аномалии"""
        url = self.BASE_URL
        formatted_symbol = symbol.upper()
        
        interval_map = {
            "1m": "Min1", "5m": "Min5", "15m": "Min15", 
            "30m": "Min30", "1h": "Min60", "4h": "Hour4", "1d": "Day1"
        }
        mexc_interval = interval_map.get(interval, "Min5")
        
        current_candle_start_time = None
        volume_alert_sent_for_current_candle = False
        move_alert_sent_for_current_candle = False
        volume_threshold = average_volume * COEFFICIENT_VOLUME_THRESHOLD 
        
        subscribe_payload = {
            "method": "SUBSCRIPTION",
            "params": [
                f"spot@public.kline.v3.api.pb@{formatted_symbol}@{mexc_interval}"
            ]
        }

        while True:
            try:
                logger.info(f"Подключаемся к MexcWS {interval} ({mexc_interval}) для {formatted_symbol}")
                async with self._session.ws_connect(url=url, heartbeat=30, proxy=self.__proxy["http"]) as ws:
                    
                    await ws.send_json(subscribe_payload)

                    async for msg in ws:
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            response = json.loads(msg.data)
                            
                            if "publicspotkline" in response:
                                data = response["publicspotkline"]
                                
                                kline = WsCandle(
                                    start_time=int(data["windowstart"]),
                                    volume=float(data["amount"]),
                                    close_price=float(data["closingprice"]),
                                    open_price=float(data["openingprice"])
                                )
                                
                                kline_start_time = kline.start_time
                                current_volume = kline.volume
                                current_move = ((kline.close_price - kline.open_price) / kline.open_price) * 100
                                
                                if current_candle_start_time != kline_start_time:
                                    current_candle_start_time = kline_start_time
                                    volume_alert_sent_for_current_candle = False
                                    move_alert_sent_for_current_candle = False
                                    logger.info(f"Новая свеча {interval} началась (MEXC). Предохранитель по объему и движению сброшен (klines)")

                                if current_volume >= volume_threshold and not volume_alert_sent_for_current_candle:
                                    text = (
                                        f"==============================================\n"
                                        f"🚨 АНОМАЛЬНЫЙ ОБЪЕМ! | {formatted_symbol} | MEXC\n"
                                        f"ℹ️ Объем: {round(current_volume, 2)} превысил порог {round(volume_threshold, 2)}!\n"
                                        f"=============================================="
                                    )
                                    logger.warning((f"АНОМАЛЬНЫЙ ОБЪЕМ! | {formatted_symbol} | MEXC | "
                                        f"Объем: {round(current_volume, 2)} превысил порог {round(volume_threshold, 2)}!"))
                                    await self.send_message(text=text, tg_id=tg_id)
                                    volume_alert_sent_for_current_candle = True

                                if abs(current_move) >= move_threshold and not move_alert_sent_for_current_candle:
                                    text = (
                                        f"==============================================\n"
                                        f"🚨 РЕЗКОЕ ДВИЖЕНИЕ! | {formatted_symbol} | MEXC\n"
                                        f"ℹ️ Движение: {round(current_move, 2)}% превысило порог {move_threshold}%!\n"
                                        f"=============================================="
                                    )
                                    logger.warning((f"РЕЗКОЕ ДВИЖЕНИЕ! | {formatted_symbol} | MEXC | "
                                        f"Движение: {round(current_move, 2)}% превысило порог {move_threshold}%!"))
                                    await self.send_message(text=text, tg_id=tg_id)
                                    move_alert_sent_for_current_candle = True
                                
                        elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR):
                            logger.error("WS соединение закрыто биржей MEXC... Переподключение")
                            break
                            
            except Exception as e:
                logger.error(f"Обрыв соединения с WS MEXC: {e}. Реконнект через 5 сек...")
                await asyncio.sleep(5)
