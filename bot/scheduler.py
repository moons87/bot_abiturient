# bot/scheduler.py
import os
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()

async def _auto_update():
    url = os.getenv("COLLEGE_SITE_URL")
    if url:
        from scraper.site_parser import parse_site
        await parse_site(url)

def setup_scheduler():
    scheduler.add_job(_auto_update, "cron", day_of_week="mon", hour=3, minute=0)
    scheduler.start()
