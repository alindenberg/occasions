import asyncio
import logging

from datetime import datetime, timezone
from fastapi import FastAPI
from sqlalchemy.orm import Session

from db.database import SessionLocal
from occasions.models import Occasion

app = FastAPI()
logger = logging.getLogger(__name__)


async def repeat_func(seconds: int, func):
    while True:
        await func()
        await asyncio.sleep(seconds)


async def send_occasion_notifications():
    db: Session = SessionLocal()
    occasions = db.query(Occasion).all()
    for occasion in occasions:
        asyncio.create_task(occasion.send_notification(db))


class OccasionTasks():
    def init(self):
        logger.info("Creating occasion tasks")
        # Start the background task
        asyncio.create_task(self.schedule_task(send_occasion_notifications))

    async def schedule_task(self, func):
        # Ensure top of hour run
        now = datetime.now(timezone.utc)
        if now.minute != 0 or now.second != 0:
            wait_seconds = 60*(60 - now.minute) - now.second
            await asyncio.sleep(wait_seconds)
        await repeat_func(60*60, func)
