import logging
import asyncio
from aiogram import Bot, Dispatcher
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import TOKEN
from core.handlers import common, mail, register_user, teacher, questions, buy_course
from core.handlers.reminder import send_reminder, ask_confirmation
from core.sheets.questions_sheet import update_table
from core.sheets.students_sheet import update_grades

logging.basicConfig(level=logging.INFO)


async def main():
    bot = Bot(token=TOKEN, parse_mode="html")
    dp = Dispatcher()
    scheduler = AsyncIOScheduler(timezone="Europe/Moscow")

    dp.include_router(common.router)
    dp.include_router(teacher.router)
    dp.include_router(mail.router)
    dp.include_router(register_user.router)
    dp.include_router(buy_course.router)
    dp.include_router(questions.router)

    scheduler.add_job(send_reminder, trigger='cron', hour=10, kwargs={'bot': bot})
    scheduler.add_job(ask_confirmation, trigger='cron', day_of_week=0, hour=7, kwargs={'bot': bot})
    scheduler.add_job(ask_confirmation, trigger='cron', day_of_week=3, hour=7, kwargs={'bot': bot})
    scheduler.add_job(update_table, trigger='cron', hour=23, minute=59)
    scheduler.add_job(update_grades, trigger='cron', month=9, day=1, hour=1)
    scheduler.start()

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
