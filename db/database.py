import aiosqlite


class Database:
    def __init__(self, db_connection: aiosqlite.Connection):
        self.db = db_connection

    async def create_table(self):
        await self.db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                tg_id INTEGER UNIQUE
            )
        """)
        await self.db.commit()


    async def add_user(self, user_id: int):
        await self.db.execute("""INSERT OR IGNORE INTO users (tg_id) VALUES (?)""", (user_id, ))
        await self.db.commit()

    async def delete_user(self, user_id: int):
        await self.db.execute("""DELETE FROM users WHERE tg_id = ?""", (user_id, ))
        await self.db.commit()

    async def get_all_users(self) -> list:
        async with self.db.execute("""SELECT tg_id FROM users""") as cursor:
            raw_users_list = await cursor.fetchall()
            result_users_list = [i[0] for i in raw_users_list]
            
            return result_users_list
