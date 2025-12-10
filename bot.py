import asyncio
import logging
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from handlers import user, admin, ordering
import database

async def main():
    # Логування
    logging.basicConfig(level=logging.INFO)
    
    # Ініціалізація БД
    await database.create_tables()

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    # Підключення роутерів
    dp.include_router(admin.admin_router) # Адмін повинен бути першим
    dp.include_router(ordering.order_router)
    dp.include_router(user.user_router)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Exit")