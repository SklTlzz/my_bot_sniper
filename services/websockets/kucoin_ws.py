import asyncio
import aiohttp
import logging
import json
import time
from aiogram import Bot

from config import PROXY, COEFFICIENT_VOLUME_THRESHOLD
from models.models import WsCandle

logger = logging.getLogger(__name__)

class KucoinWS:
    """Данный класс отвечает за Websockets на KuCoin"""

    TOKEN_URL = "https://api.kucoin.com/api/v1/bullet-public"

    def __init__(self, session: aiohttp.ClientSession, bot: Bot):
        self._session = session
        self.bot = bot
        self.__proxy = {
            'http': PROXY,
        }

    async def send_message(self, text: str, tg_id: int):
        await self.bot.send_message(chat_id=tg_id, text=text)

    async def get_ws_endpoint(self) -> str | None:
        """Получает динамический токен и endpoint для подключения к WS KuCoin"""
        try:
            async with self._session.post(self.TOKEN_URL, proxy=self.__proxy["http"]) as resp:
                res = await resp.json()
                if res.get("code") == "200000":
                    token = res["data"]["token"]
                    endpoint = res["data"]["instanceServers"][0]["endpoint"]
                    return f"{endpoint}?token={token}"
                return None
        except Exception as e:
            logger.error(f"Ошибка получения WS токена KuCoin: {e}")
            return None

    async def listen_klines(self, symbol: str, interval: str, average_volume: float, move_threshold: float, tg_id: int):
        """Слушает Websocket KuCoin и отправляет алерты при нахождении аномалии"""
        formatted_symbol = symbol.upper()[:-4] + "-" + symbol.upper()[-4:]
        
        ws_interval_map = {
            "1m": "1min", "5m": "5min", "15m": "15min", 
            "30m": "30min", "1h": "1hour", "4h": "4hour", "1d": "1day"
        }
        kucoin_interval = ws_interval_map.get(interval, "5min")
        
        topic = f"/market/candles:{formatted_symbol}_{kucoin_interval}"
        
        current_candle_start_time = None
        volume_alert_sent_for_current_candle = False
        move_alert_sent_for_current_candle = False
        volume_threshold = average_volume * COEFFICIENT_VOLUME_THRESHOLD 
        
        subscribe_payload = {
            "id": int(time.time() * 1000),
            "type": "subscribe",
            "topic": topic,
            "response": True
        }

        while True:
            try:
                url = await self.get_ws_endpoint()
                if not url:
                    logger.error("Не удалось получить WS URL KuCoin. Ретрай через 5 сек...")
                    await asyncio.sleep(5)
                    continue

                logger.info(f"Подключаемся к KucoinWS {interval} для {formatted_symbol}")
                
                async with self._session.ws_connect(url=url, heartbeat=25, proxy=self.__proxy["http"]) as ws:
                    
                    await ws.send_json(subscribe_payload)

                    async for msg in ws:
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            response = json.loads(msg.data)
                            
                            if response.get("type") != "message" or response.get("subject") != "trade.candles.update":
                                continue

                            if "data" in response and "candles" in response["data"]:
                                data = response["data"]["candles"]
                                
                                kline = WsCandle(
                                    start_time=int(data[0]),
                                    volume=float(data[6]), 
                                    close_price=float(data[2]),
                                    open_price=float(data[1])
                                )
                                
                                kline_start_time = kline.start_time
                                current_volume = kline.volume
                                current_move = ((kline.close_price - kline.open_price) / kline.open_price) * 100
                                
                                if current_candle_start_time != kline_start_time:
                                    current_candle_start_time = kline_start_time
                                    volume_alert_sent_for_current_candle = False
                                    move_alert_sent_for_current_candle = False
                                    logger.info(f"Новая свеча {interval} началась (KuCoin). Предохранитель по объему и движению сброшен (klines)")

                                if current_volume >= volume_threshold and not volume_alert_sent_for_current_candle:
                                    text = (
                                        f"==============================================\n"
                                        f"🚨 АНОМАЛЬНЫЙ ОБЪЕМ! | {formatted_symbol} | KuCoin\n"
                                        f"ℹ️ Объем: {round(current_volume, 2)} превысил порог {round(volume_threshold, 2)}!\n"
                                        f"=============================================="
                                    )
                                    logger.warning((f"АНОМАЛЬНЫЙ ОБЪЕМ! | {formatted_symbol} | KuCoin | "
                                        f"Объем: {round(current_volume, 2)} превысил порог {round(volume_threshold, 2)}!"))
                                    await self.send_message(text=text, tg_id=tg_id)
                                    volume_alert_sent_for_current_candle = True

                                if abs(current_move) >= move_threshold and not move_alert_sent_for_current_candle:
                                    text = (
                                        f"==============================================\n"
                                        f"🚨 РЕЗКОЕ ДВИЖЕНИЕ! | {formatted_symbol} | KuCoin\n"
                                        f"ℹ️ Движение: {round(current_move, 2)}% превысило порог {move_threshold}%!\n"
                                        f"=============================================="
                                    )
                                    logger.warning((f"РЕЗКОЕ ДВИЖЕНИЕ! | {formatted_symbol} | KuCoin | "
                                        f"Движение: {round(current_move, 2)}% превысило порог {move_threshold}%!"))
                                    await self.send_message(text=text, tg_id=tg_id)
                                    move_alert_sent_for_current_candle = True
                                
                        elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR):
                            logger.error("WS соединение закрыто биржей KuCoin... Переподключение")
                            break
                            
            except Exception as e:
                logger.error(f"Обрыв соединения с WS KuCoin: {e}. Реконнект через 5 сек...")
                await asyncio.sleep(5)
