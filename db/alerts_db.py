import aiosqlite
import logging


logger = logging.getLogger(__name__)


class AlertsDatabase:
    """Класс для работы c таблицей users_alerts"""
    def __init__(self, db_connection: aiosqlite.Connection):
        self.db = db_connection

    async def create_table(self):
        """Создает таблицу users_alerts для хранения алертов пользователей"""
        await self.db.execute("""
            CREATE TABLE IF NOT EXISTS users_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tg_id INTEGER,
                exchange VARCHAR(7),
                token VARCHAR(12),
                              
                UNIQUE(tg_id, exchange, token)
            )
        """)
        await self.db.commit()

        logger.info("Таблица users_alerts (если её еще не было) успешно создана")


    async def add_alert(self, tg_id: int, exchange: str, token: str):
        """Добавляет алерт в таблицу users_alerts"""
        await self.db.execute("""INSERT OR IGNORE INTO users_alerts (tg_id, exchange, token) VALUES (?, ?, ?)""", (tg_id, exchange, token))
        await self.db.commit()

        logger.info(f"В users_alerts добавилось новое отслеживание. Информация: tg_id: {tg_id}; exchange: {exchange}; token: {token}")

    async def delete_alert(self, tg_id: int, exchange: str, token: str):
        """Удаляет алерт из таблицы users_alerts"""
        await self.db.execute("""DELETE FROM users_alerts WHERE tg_id = ? AND exchange = ? AND token = ?""", (tg_id, exchange, token))
        await self.db.commit()
        
        logger.info(f"Из users_alerts удалено отслеживание. Информация: tg_id: {tg_id}; exchange: {exchange}; token: {token}")

    async def delete_all_user_alerts(self, tg_id: int):
        """Удаляет все алерты определенного пользователя из таблицы users_alerts"""
        await self.db.execute("""DELETE FROM users_alerts WHERE tg_id = ?""", (tg_id, ))
        await self.db.commit()
        
        logger.info(f"Из users_alerts успешно удалены все алерты пользователя c tg_id: {tg_id}")

    async def delete_all_alerts(self):
        """Удаляет все алерты из таблицы users_alerts"""
        await self.db.execute("""DELETE FROM users_alerts""")
        await self.db.commit()
        
        logger.info(f"Из users_alerts успешно удалены все алерты")

    async def get_all_user_alerts(self, tg_id: int) -> list:
        """Получает все алерты пользователя из таблицы users_alerts"""
        async with self.db.execute("""SELECT exchange, token FROM users_alerts WHERE tg_id = ?""", (tg_id, )) as cursor:
            alerts_list = await cursor.fetchall()
            
            # logger.info(f"Получили все отслеживания пользователя {tg_id} из таблицы users_alerts. Всего отслеживаний: {len(alerts_list)}")

            return alerts_list

    async def get_all_alerts(self) -> list:
        """Получает алерты всех пользователей из таблицы users_alerts"""
        async with self.db.execute("""SELECT tg_id, exchange, token FROM users_alerts""") as cursor:
            alerts_list = await cursor.fetchall()
            
            # logger.info(f"Получили все отслеживания из таблицы users_alerts. Всего отслеживаний: {len(alerts_list)}")

            return alerts_list

