import asyncio
import logging

from datetime import datetime, timezone
from fastapi import FastAPI
from sqlalchemy.orm import Session

from db.database import SessionLocal
from occasions.models import Occasion
from occasions.services import OccasionService

app = FastAPI()
logger = logging.getLogger(__name__)


async def repeat_func(seconds: int, func):
    while True:
        await func()
        await asyncio.sleep(seconds)


async def process_ocassions():
    db: Session = SessionLocal()
    service = OccasionService()
    occasions = db.query(Occasion).filter(
        Occasion.date_processed.is_(None),
        Occasion.date < datetime.now(timezone.utc).isoformat()
    ).all()
    for occasion in occasions:
        asyncio.create_task(service.process_occasion(db, occasion))


class OccasionTasks():
    def init(self):
        logger.info("Creating occasion tasks")
        # Start the background task
        asyncio.create_task(self.schedule_task(process_ocassions))

    async def schedule_task(self, func):
        # Ensure top of hour run
        # now = datetime.now(timezone.utc)
        # if now.minute != 0 or now.second != 0:
            # wait_seconds = 60*(60 - now.minute) - now.second
            # await asyncio.sleep(wait_seconds)
        # await repeat_func(60*60, func)
        await repeat_func(60, func)
