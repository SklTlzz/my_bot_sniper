import aiosqlite
import logging


logger = logging.getLogger(__name__)


class Database:
    """Класс для работы c таблицей users"""
    def __init__(self, db_connection: aiosqlite.Connection):
        self.db = db_connection

    async def create_table(self):
        """Создает таблицу users"""
        await self.db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                tg_id INTEGER UNIQUE
            )
        """)
        await self.db.commit()

        logger.info("Таблица users (если её еще не было) успешно создана")


    async def add_user(self, tg_id: int):
        """Добавляет пользователя по его telegram_id в таблицу users"""
        await self.db.execute("""INSERT OR IGNORE INTO users (tg_id) VALUES (?)""", (tg_id, ))
        await self.db.commit()

        logger.info(f"В users добавлен пользователь c id: {tg_id} (если его ранее не было)")

    async def delete_user(self, tg_id: int):
        """Удаляет пользователя из таблицы users"""
        await self.db.execute("""DELETE FROM users WHERE tg_id = ?""", (tg_id, ))
        await self.db.commit()
        
        logger.info(f"Из users удален пользователь c id: {tg_id}")

    async def get_all_users(self) -> list:
        """Получает всех пользователей из таблицы users"""
        async with self.db.execute("""SELECT tg_id FROM users""") as cursor:
            raw_users_list = await cursor.fetchall()
            result_users_list = [i[0] for i in raw_users_list]
            
            logger.info(f"Получили всех пользователей из таблицы users. Всего пользователей: {len(result_users_list)}")

            return result_users_list
