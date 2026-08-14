from aiogram import Router, Bot
from aiogram.types import Message
from aiogram.filters import CommandStart, Command, CommandObject
import logging

from db.database import Database
from config import AVAILABLE_EXCHANGES
from db.alerts_db import AlertsDatabase


logger = logging.getLogger(__name__)
router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message, db: Database):
    """Обработчик команды /start"""
    user_id = message.from_user.id
    await db.add_user(user_id)

    await message.answer("Приветствую! Жми /help, чтобы узнать, что я могу")

@router.message(Command("help"))
async def cmd_help(message: Message, db: Database):
    """Обработчик команды /help"""
    user_id = message.from_user.id
    await db.add_user(user_id)
    
    help_text = (
        "<b>Доступные команды:</b>\n\n"
        "/start - приветствие\n"
        "/help - показывает доступные команды\n"
        "/add - добавить монету для отслеживания. Пример заполнения:\n"
        "       <code>/add binance - WIFUSDT</code>\n"
        "       <code>/add binance-WIFUSDT</code>\n\n"
        "/del - удалить монету из отслеживания. Пример заполнения (аналогично <code>/add</code>):\n"
        "       <code>/del binance - WIFUSDT</code>\n\n"
        "/stopall - отключить все уведомления разом\n"
        "/myalerts - показывает все ваши алерты\n\n\n\n"
        "<b>Доступные биржи:</b>\n\n"
        "bingx, bitget, binance, mexc, okx, gate, bybit, kucoin, kraken"
    )

    await message.answer(help_text)

@router.message(Command("add"))
async def cmd_add(message: Message, db: Database, command: CommandObject, alerts_db: AlertsDatabase):
    """Обработчик команды /add"""
    user_id = message.from_user.id
    await db.add_user(user_id)
    
    if command.args:
        params = [i.strip().lower() for i in command.args.split("-")]

        if len(params) == 2:
            exchange, token = params
        
            if exchange in AVAILABLE_EXCHANGES:
                if token.endswith("usdt"):
                    await alerts_db.add_alert(tg_id=user_id, exchange=exchange, token=token)
                    await message.answer(f"Добавил в отслеживание: {params}")
                    logger.info(f"{user_id} добавил в отслеживание токен {token} на бирже {exchange}")
                else:
                    await message.answer(f"Добавьте usdt в любом регистре в конец токена: {token}usdt")                    
            else:
                await message.answer(f"Такой биржи в базе нет: {exchange}")
    
        else:
            await message.answer("Вы недописали параметры. Пример: <code>/add binance - WIFUSDT</code>")
    else:
        await message.answer("Вы недописали параметры. Пример: <code>/add binance - WIFUSDT</code>")

@router.message(Command("del"))
async def cmd_del(message: Message, db: Database, command: CommandObject, alerts_db: AlertsDatabase):
    """Обработчик команды /del"""
    user_id = message.from_user.id
    await db.add_user(user_id)
        
    if command.args:
        params = [i.strip().lower() for i in command.args.split("-")]
        if len(params) == 2:
            exchange, token = params
        
            if exchange in AVAILABLE_EXCHANGES:
                await alerts_db.delete_alert(tg_id=user_id, exchange=exchange, token=token)
                await message.answer(f"Удалил из отслеживания: {params}")
                logger.info(f"{user_id} удалил из отслеживания токен {token} на бирже {exchange}")
            else:
                await message.answer(f"Такой биржи в базе нет: {exchange}")
    
        else:
            await message.answer("Вы недописали параметры. Пример: <code>/del binance - WIFUSDT</code>")
    else:
        await message.answer("Вы недописали параметры. Пример: <code>/del binance - WIFUSDT</code>")


@router.message(Command("stopall"))
async def cmd_stopall(message: Message, db: Database, alerts_db: AlertsDatabase):
    """Обработчик команды /stopall"""
    user_id = message.from_user.id
    await db.add_user(user_id)

    alerts = await alerts_db.get_all_user_alerts(tg_id=user_id)

    if alerts:
        await alerts_db.delete_all_user_alerts(tg_id=user_id)
        await message.answer("Все ваши алерты удалены")
    else:
        await message.answer("У вас нет алертов")

@router.message(Command("myalerts"))
async def cmd_myalerts(message: Message, db: Database, alerts_db: AlertsDatabase):
    """Обработчик команды /myalerts"""
    user_id = message.from_user.id
    await db.add_user(user_id)
    
    alerts = await alerts_db.get_all_user_alerts(tg_id=user_id)

    if alerts:
        alerts_text = "\n".join([f'     {exchange} - {token}' for exchange, token in alerts])
        await message.answer(f"Ваши алерты:\n\n{alerts_text}")
    else:
        await message.answer("У вас сейчас нет алертов")
