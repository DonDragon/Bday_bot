from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta
from database import get_birthdays
from config import ADMIN_IDS

scheduler = AsyncIOScheduler()

async def scheduler_start(bot):
    async def send_daily_reminders():
        now = datetime.now().strftime('%d.%m')
        bdays = get_birthdays()
        for b in bdays:
            if b['date'] == now:
                await bot.send_message(ADMIN_IDS[0], f"Сегодня день рождения у {b['name']}!")

    scheduler.add_job(send_daily_reminders, 'cron', hour=9)
    scheduler.start()

async def set_reminder(name, date):
    try:
        day, month = map(int, date.split('.'))
        now = datetime.now()
        target = datetime(year=now.year, month=month, day=day)
        if target < now:
            target = target.replace(year=now.year + 1)
        reminder_time = target - timedelta(days=1)

        async def reminder():
            print(f"Напоминание: Завтра день рождения у {name} ({date})")

        scheduler.add_job(reminder, trigger='date', run_date=reminder_time)
    except Exception as e:
        print(f"Ошибка при установке напоминания для {name}: {e}")
