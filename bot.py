import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties

from handlers import register_handlers
from reminder import scheduler_start
from database import init_db
from i18n import setup_i18n
from config import API_TOKEN
import os

logging.basicConfig(level=logging.INFO)

async def main():
    from aiogram.client.default import DefaultBotProperties

    bot = Bot(
        token=API_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    await bot.delete_webhook(drop_pending_updates=True)
    dp = Dispatcher(storage=MemoryStorage())

    setup_i18n(dp)
    register_handlers(dp)

    db_path = os.path.abspath("birthdays.db")
    print(f"Используется база: {db_path}")

    init_db()

    db_path = os.path.abspath("birthdays.db")
    print(f"Используется база: {db_path}")
    logging.info(f"Используется база: {db_path}")

    # Запуск планировщика
    await scheduler_start(bot)

    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
