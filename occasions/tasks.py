import asyncio
import logging

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
        logger.error("Creating tasks")
        # Start the background task
        asyncio.create_task(repeat_func(5, send_occasion_notifications))
