from aiogram import Router, Bot
from aiogram.types import Message
from aiogram.filters import CommandStart, Command, CommandObject
import logging
import aiosqlite

from db.database import Database
from config import BOSS_ID
from db.alerts_db import AlertsDatabase


logger = logging.getLogger(__name__)
router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message, db: Database):
    """Обработчик команды /start"""
    users_list = await db.get_all_users()
    user_id = message.from_user.id
    
    if str(user_id) == BOSS_ID:
        await message.answer("Здраве, надёже государь! За чем соизволите следить сегодня? 🤓")
    elif user_id in users_list:
        await message.answer("Ты в списках, кайф, за чем следить будем? 🧐")
    else:
        await message.answer("Вам не выдан доступ 🫠")

@router.message(Command("help"))
async def cmd_help(message: Message, db: Database):
    """Обработчик команды /help"""
    users_list = await db.get_all_users()
    user_id = message.from_user.id
    
    if user_id in users_list:
        help_text = (
            "<b>Доступные команды:</b>\n\n"
            "/start - просто приветствие\n"
            "/help - показывает доступные команды. Ну ты уже понял))\n"
            "/add - добавить монету для отслеживания. Пример заполнения:\n"
            "       <code>/add binance - WIF</code>\n"
            "       <code>/add binance-WIF</code>\n\n"
            "/del - удалить монету из отслеживания. Пример заполнения (аналогично <code>/add</code>):\n"
            "       <code>/del binance - WIF</code>\n\n"
            "/stopall - вырубить все уведы разом"
        )

        await message.answer(help_text)
    else:
        await message.answer("Вам не выдан доступ 🫠")

@router.message(Command("add"))
async def cmd_add(message: Message, db: Database, command: CommandObject, alerts_db: AlertsDatabase):
    """Обработчик команды /add"""
    users_list = await db.get_all_users()
    user_id = message.from_user.id
    
    if user_id in users_list:
        available_exchanges = ["bingx", "bitget", "binance", "mexc", "okx", "gate", "bybit"]
        
        if command.args:
            params = [i.strip().lower() for i in command.args.split("-")]

            if len(params) == 2:
                exchange, token = params
            
                if exchange in available_exchanges:
                    await alerts_db.add_alert(tg_id=user_id, exchange=exchange, token=token)

                    await message.answer(f"Добавил в отслеживание: {params}")
                    logger.info(f"{user_id} добавил в отслеживание токен {token} на бирже {exchange}")
                else:
                    await message.answer(f"Я впервые вижу такую биржу: {exchange}")
        
            else:
                await message.answer("Ты недописал параметры, бро. Пример напомню: <code>/add binance - WIF</code>")
        else:
            await message.answer("Ты не вписал параметры, бро. Пример напомню: <code>/add binance - WIF</code>")
    else:
        await message.answer("Вам не выдан доступ 🫠")

@router.message(Command("del"))
async def cmd_del(message: Message, db: Database, command: CommandObject, alerts_db: AlertsDatabase):
    """Обработчик команды /del"""
    users_list = await db.get_all_users()
    user_id = message.from_user.id
    
    if user_id in users_list:
        available_exchanges = ["bingx", "bitget", "binance", "mexc", "okx", "gate", "bybit"]
        
        if command.args:
            params = [i.strip().lower() for i in command.args.split("-")]

            if len(params) == 2:
                exchange, token = params
            
                if exchange in available_exchanges:
                    await alerts_db.delete_alert(tg_id=user_id, exchange=exchange, token=token)

                    await message.answer(f"Удалил из отслеживания: {params}")
                    logger.info(f"{user_id} удалил из отслеживания токен {token} на бирже {exchange}")
                else:
                    await message.answer(f"Я впервые вижу такую биржу: {exchange}")
        
            else:
                await message.answer("Ты недописал параметры, бро. Пример напомню: <code>/del binance - WIF</code>")
        else:
            await message.answer("Ты не вписал параметры, бро. Пример напомню: <code>/del binance - WIF</code>")
    else:
        await message.answer("Вам не выдан доступ 🫠")

@router.message(Command("stopall"))
async def cmd_stopall(message: Message, db: Database, alerts_db: AlertsDatabase):
    """Обработчик команды /stopall"""
    users_list = await db.get_all_users()
    user_id = message.from_user.id
    
    if user_id in users_list:
        alerts = await alerts_db.get_all_user_alerts(tg_id=user_id)

        if alerts:
            await alerts_db.delete_all_user_alerts(tg_id=user_id)
            await message.answer("Удалил все ваши алерты")
        else:
            await message.answer("У вас нет алертов")
    else:
        await message.answer("Вам не выдан доступ 🫠")

@router.message(Command("myalerts"))
async def cmd_myalerts(message: Message, db: Database, alerts_db: AlertsDatabase):
    """Обработчик команды /myalerts"""
    users_list = await db.get_all_users()
    user_id = message.from_user.id
    
    if user_id in users_list:
        alerts = await alerts_db.get_all_user_alerts(tg_id=user_id)

        if alerts:
            await message.answer(f"Ваши алерты:\n\n{"\n".join([f"       {exchange} - {token}" for exchange, token in alerts])}")
        else:
            await message.answer("У вас сейчас нет алертов")
    else:
        await message.answer("Вам не выдан доступ 🫠")
