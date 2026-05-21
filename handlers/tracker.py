import logging
from aiogram import Bot
import asyncio
import time

from db.alerts_db import AlertsDatabase
from analyser.orderbook import Analyser
from models.models import RestCandle, RestOrderBook
from config import MOVE_THRESHOLD, INTERVAL, COUNT_CANDLES, ORDERBOOK_VOLUME_THRESHOLD, TIME_TO_NEXT_ORDERBOOK_ALERT


logger = logging.getLogger(__name__)

class Tracker:
    def __init__(self, bot: Bot, alerts_db: AlertsDatabase, clients: dict):
        self.bot = bot
        self.alerts_db = alerts_db
        self.clients = clients

        self.tasks = dict()

    async def send_message(self, text: str, tg_id: int):
        await self.bot.send_message(chat_id=tg_id, text=text)
    
    async def wait_for_alert(self):
        while True:
            all_alerts = await self.alerts_db.get_all_alerts()

            if all_alerts:
                for cur_alert in all_alerts:
                    if cur_alert not in self.tasks.keys():
                        tg_id, exchange, token = cur_alert
                        exchange_name = exchange.lower()

                        if exchange_name in self.clients:
                            current_rest = self.clients[exchange_name]["rest"]
                            current_ws = self.clients[exchange_name]["ws"]

                            candles = await current_rest.get_spot_candles(symbol=token, interval=INTERVAL, limit=COUNT_CANDLES)

                            if candles is None:
                                await asyncio.sleep(5)
                                continue
                            
                            sum_volume = 0

                            for candle in candles:
                                candle: RestCandle
                                sum_volume += candle.volume

                            average_volume = sum_volume / COUNT_CANDLES

                            klines_task = asyncio.create_task(current_ws.listen_klines(symbol=token, interval=INTERVAL, average_volume=average_volume, move_threshold=MOVE_THRESHOLD, tg_id=tg_id))

                            orderbook = await current_rest.get_spot_order_book(symbol=token)
                            orderbook_task = asyncio.create_task(self.prepare_orderbooks(orderbook=orderbook, rest_client=current_rest, tg_id=tg_id, token=token, exchange=exchange_name))

                            self.tasks[(tg_id, exchange, token)] = (klines_task, orderbook_task)

            current_tasks = list(self.tasks.keys())
            for alert in current_tasks:
                if alert not in all_alerts:
                    klines_task, orderbook_task = self.tasks[alert]
                    klines_task.cancel()
                    orderbook_task.cancel()

                    self.tasks.pop(alert, None)

            await asyncio.sleep(1)

    async def prepare_orderbooks(self, orderbook: RestOrderBook, rest_client, tg_id: int, token: str, exchange: str):
        current_anomals = []
        last_alert_time = 0

        while True:
            if orderbook is None:
                await asyncio.sleep(5)
                orderbook: RestOrderBook = await rest_client.get_spot_order_book(symbol=token)
                continue

            analyser = Analyser(data=orderbook)
            data = analyser.prepare_data(volume_threshold=ORDERBOOK_VOLUME_THRESHOLD)
            buy_tuple = (tg_id, exchange, token, "покупка")
            sell_tuple = (tg_id, exchange, token, "продажа")

            if data["asks"] and sell_tuple not in current_anomals and (time.time() - last_alert_time > TIME_TO_NEXT_ORDERBOOK_ALERT):
                text = (
                    f"==============================================\n"
                    f"🔽 Найдена плотность на ПРОДАЖУ! Токен: {token} | Биржа: {exchange}\n\n"
                    f"📈 Цена: {data['asks'][0][0]}\n"
                    f"ℹ️ Объем: {round(data['asks'][0][1], 2)}\n"
                    f"=============================================="
                )

                logger.warning((f"Найдена плотность на ПРОДАЖУ! Токен: {token} | Биржа: {exchange}\n"
                    f"Цена: {data['asks'][0][0]} | "
                    f"Объем: {round(data['asks'][0][1], 2)}"))
                
                await self.send_message(text=text, tg_id=tg_id)

                current_anomals.append(sell_tuple)
                last_alert_time = time.time()
            if data["bids"] and buy_tuple not in current_anomals and (time.time() - last_alert_time > TIME_TO_NEXT_ORDERBOOK_ALERT):
                text = (
                    f"==============================================\n"
                    f"🔼 Найдена плотность на ПОКУПКУ! Токен: {token} | Биржа: {exchange}\n\n"
                    f"📈 Цена: {data['bids'][0][0]}\n"
                    f"ℹ️ Объем: {round(data['bids'][0][1], 2)}\n"
                    f"=============================================="
                )

                logger.warning((f"Найдена плотность на ПОКУПКУ! Токен: {token} | Биржа: {exchange}\n"
                    f"Цена: {data['bids'][0][0]} | "
                    f"Объем: {round(data['bids'][0][1], 2)}"))
                
                await self.send_message(text=text, tg_id=tg_id)

                current_anomals.append(buy_tuple)
                last_alert_time = time.time()

            if data["asks"] and not data["bids"]:
                if buy_tuple in current_anomals:
                    current_anomals.remove(buy_tuple)
                    logger.info(f"Из кеша удалена плотность {buy_tuple}")

            if data["bids"] and not data["asks"]:
                if sell_tuple in current_anomals:
                    current_anomals.remove(sell_tuple)
                    logger.info(f"Из кеша удалена плотность {sell_tuple}")
                    
            if not data["asks"] and not data["bids"]:
                current_anomals.clear()
                logger.info("Из кеша удалены все плотности")

            orderbook: RestOrderBook = await rest_client.get_spot_order_book(symbol=token)
            await asyncio.sleep(8)
