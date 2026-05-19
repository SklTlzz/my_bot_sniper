import asyncio
import aiohttp
import logging
import json
from aiogram import Bot

from config import PROXY, COEFFICIENT_VOLUME_THRESHOLD
from models.models import WsCandle

logger = logging.getLogger(__name__)

class BingXWS:
    """Данный класс отвечает за Websockets на BingX Spot"""

    BASE_URL = "wss://open-api-ws.bingx.com/market"

    def __init__(self, session: aiohttp.ClientSession, bot: Bot):
        self._session = session
        self.bot = bot
        self.__proxy = {
            'http': PROXY,
        }

    async def send_message(self, text: str, tg_id: int):
        await self.bot.send_message(chat_id=tg_id, text=text)

    async def listen_klines(self, symbol: str, interval: str, average_volume: float, move_threshold: float, tg_id: int):
        """Слушает Websocket BingX и отправляет алерты при нахождении аномалии"""
        url = self.BASE_URL
        
        formatted_symbol = symbol.upper()[:-4] + "-" + symbol.upper()[-4:]
        
        current_candle_start_time = None
        volume_alert_sent_for_current_candle = False
        move_alert_sent_for_current_candle = False
        volume_threshold = average_volume * COEFFICIENT_VOLUME_THRESHOLD 
        
        subscribe_payload = {
            "id": "1",
            "reqType": "sub",
            "dataType": f"{formatted_symbol}@kline_{interval}"
        }

        while True:
            try:
                logger.info(f"Подключаемся к BingXWS {interval} для {formatted_symbol}")
                async with self._session.ws_connect(url=url, heartbeat=25, proxy=self.__proxy["http"]) as ws:
                    
                    await ws.send_json(subscribe_payload)

                    async for msg in ws:
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            if msg.data.lower() == "ping":
                                await ws.send_str("Pong")
                                continue
                            
                            if msg.data.lower() == "pong":
                                continue

                            response = json.loads(msg.data)

                            if response.get("code") == 0 and "data" in response and "dataType" in response:
                                data = response["data"]
                                
                                if isinstance(data, list) and len(data) > 0:
                                    kline_data = data[0]
                                elif isinstance(data, dict):
                                    kline_data = data.get("K", data)
                                else:
                                    continue
                                
                                kline = WsCandle(
                                    start_time=int(kline_data.get("t", 0)),
                                    volume=float(kline_data.get("q", 0)),
                                    close_price=float(kline_data.get("c", 0)),
                                    open_price=float(kline_data.get("o", 0))
                                )
                                
                                kline_start_time = kline.start_time
                                current_volume = kline.volume
                                current_move = ((kline.close_price - kline.open_price) / kline.open_price) * 100
                                
                                if current_candle_start_time != kline_start_time:
                                    current_candle_start_time = kline_start_time
                                    volume_alert_sent_for_current_candle = False
                                    move_alert_sent_for_current_candle = False
                                    logger.info(f"Новая свеча {interval} началась (BingX). Предохранитель по объему и движению сброшен (klines)")

                                if current_volume >= volume_threshold and not volume_alert_sent_for_current_candle:
                                    text = (
                                        f"==============================================\n"
                                        f"🚨 АНОМАЛЬНЫЙ ОБЪЕМ! | {formatted_symbol} | BingX\n"
                                        f"ℹ️ Объем: {round(current_volume, 2)} превысил порог {round(volume_threshold, 2)}!\n"
                                        f"=============================================="
                                    )
                                    logger.warning((f"АНОМАЛЬНЫЙ ОБЪЕМ! | {formatted_symbol} | BingX | "
                                        f"Объем: {round(current_volume, 2)} превысил порог {round(volume_threshold, 2)}!"))
                                    await self.send_message(text=text, tg_id=tg_id)
                                    volume_alert_sent_for_current_candle = True

                                if abs(current_move) >= move_threshold and not move_alert_sent_for_current_candle:
                                    text = (
                                        f"==============================================\n"
                                        f"🚨 РЕЗКОЕ ДВИЖЕНИЕ! | {formatted_symbol} | BingX\n"
                                        f"ℹ️ Движение: {round(current_move, 2)}% превысило порог {move_threshold}%!\n"
                                        f"=============================================="
                                    )
                                    logger.warning((f"РЕЗКОЕ ДВИЖЕНИЕ! | {formatted_symbol} | BingX | "
                                        f"Движение: {round(current_move, 2)}% превысило порог {move_threshold}%!"))
                                    await self.send_message(text=text, tg_id=tg_id)
                                    move_alert_sent_for_current_candle = True
                                
                        elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR):
                            logger.error("WS соединение закрыто биржей BingX... Переподключение")
                            break
                            
            except Exception as e:
                logger.error(f"Обрыв соединения с WS BingX: {e}. Реконнект через 5 сек...")
                await asyncio.sleep(5)
