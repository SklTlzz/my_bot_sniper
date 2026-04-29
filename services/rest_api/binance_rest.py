import aiohttp
from config import STAKAN_DEPTH, MIN_TOKEN_VOLUME, EXCEEDING_AVG_PCT
import asyncio


class Binance:
    REST_URL_24HR = "https://fapi.binance.com/fapi/v1/ticker/24hr"
    REST_URL_DEPTH = "https://fapi.binance.com/fapi/v1/depth"

    def __init__(self, session: aiohttp.ClientSession):
        self._session = session
        
        self.__proxy = {
            'http': 'http://n6KPSuii:FtigEyZZ@45.199.240.33:62870',
            'https': 'http://n6KPSuii:FtigEyZZ@45.199.240.33:62870',
        }

    async def get_liquid_tickers(self):
        """Метод для получения ликвидных монет"""
        url = self.REST_URL_24HR
        print("Отправляем запрос к Binance REST API...")

        async with self._session.get(url, proxy=self.__proxy['http']) as response:
            data = await response.json()
            liquid_coins = []
            
            for item in data:
                symbol = item['symbol']
                volume = round(float(item['quoteVolume']), 2)

                if symbol.endswith('USDT'):
                    if volume >= MIN_TOKEN_VOLUME:
                        liquid_coins.append(symbol)

            return liquid_coins

    async def fetch_single_snapshot(self, symbol: str, semaphore: asyncio.Semaphore, local_books: dict):
        """Асинхронно скачивает один глубокий стакан с учетом лимитов"""
        
        url = self.REST_URL_DEPTH
        params = {
            "symbol": symbol,
            "limit": 1000
        }

        async with semaphore:
            try:
                async with self._session.get(url, params=params, proxy=self.__proxy['http']) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        
                        local_books[symbol] = {
                            "lastUpdateId": data['lastUpdateId'],
                            "bids": {float(price): float(qty) for price, qty in data['bids']},
                            "asks": {float(price): float(qty) for price, qty in data['asks']}
                        }
                        print(f"✅ [{symbol}] Снапшот загружен (id: {data['lastUpdateId']})")
                    
                    elif response.status == 429:
                        print(f"❌ [{symbol}] Лимит")
                    else:
                        print(f"⚠️ [{symbol}] Ошибка скачивания: {response.status}")
                        
            except Exception as e:
                print(f"[{symbol}] Ошибка соединения: {e}")

    async def initialize_all_order_books(self, tickers: list) -> dict:
        """Менеджер загрузки всех 400 стаканов"""
        
        print(f"Начинаем загрузку {len(tickers)} глубоких стаканов")
        
        local_books = {}
        
        # Разрешаем не более 2 одновременных запросов (чтобы укладываться в лимиты)
        semaphore = asyncio.Semaphore(2)
        
        # Разбиваем монеты на пачки по 10 штук
        chunk_size = 10
        for i in range(0, len(tickers), chunk_size):
            chunk = tickers[i:i + chunk_size]
            
            # Создаем задачи для скачивания пачки
            tasks = [self.fetch_single_snapshot(ticker, semaphore, local_books) for ticker in chunk]
            
            # Запускаем пачку параллельно и ждем выполнения
            await asyncio.gather(*tasks)
            
            # СПИМ 5 СЕКУНД после каждых 10 монет! 
            # 10 монет * 50 весов = 500 весов. За 1 минуту мы скачаем 120 монет (6000 весов).
            # Идеально укладываемся в лимит биржи.
            print(f"💤 Пачка загружена. Спим 5 сек")
            await asyncio.sleep(5)
            
        print(f"🎉 Все {len(local_books)} стаканов успешно инициализированы!")
        return local_books

