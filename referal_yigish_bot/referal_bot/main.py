import asyncio
import logging
import os
import threading

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN
import database as db
from handlers import user, admin

logging.basicConfig(level=logging.INFO)


def run_webapp_thread():
    """
    Flask Mini App serverini alohida thread'da ishga tushiradi.
    Render.com kabi hostinglarda PORT environment variable orqali
    bitta jarayonda ham bot, ham webapp ishlaydi (asosiy talab).
    """
    port = int(os.getenv("PORT", 0))
    if not port:
        logging.info("PORT berilmagan, Mini App webserveri ishga tushmaydi (lokal rejim).")
        return

    from webapp.server import app as flask_app

    def _run():
        flask_app.run(host="0.0.0.0", port=port, use_reloader=False)

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
    logging.info(f"Mini App webserveri {port}-portda ishga tushdi")


async def main():
    db.init_db()

    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(admin.router)
    dp.include_router(user.router)

    run_webapp_thread()

    await bot.delete_webhook(drop_pending_updates=True)
    logging.info("Bot ishga tushdi...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
