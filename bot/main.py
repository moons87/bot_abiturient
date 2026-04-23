# bot/main.py
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from knowledge.db import init_db
from bot.handlers import menu, faq, profitest, excursions, admin, free_text
from bot.scheduler import setup_scheduler

async def main():
    await init_db()
    if not os.getenv("BOT_TOKEN"):
        raise ValueError("BOT_TOKEN is required")
    if not os.getenv("ADMIN_TELEGRAM_ID"):
        print("WARNING: ADMIN_TELEGRAM_ID не задан — команды администратора отключены")
    bot = Bot(token=os.getenv("BOT_TOKEN"))
    dp = Dispatcher(storage=MemoryStorage())

    # Router order matters — FSM and specific handlers before catch-all free_text
    dp.include_router(menu.router)
    dp.include_router(faq.router)
    dp.include_router(profitest.router)
    dp.include_router(excursions.router)
    dp.include_router(admin.router)
    dp.include_router(free_text.router)  # last — catches all remaining messages

    setup_scheduler()
    print("Бот запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
