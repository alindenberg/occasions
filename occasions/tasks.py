import asyncio
import logging
import sqlalchemy as sa

from datetime import datetime, timezone
from fastapi import FastAPI
from sqlalchemy.orm import Session

from db.database import get_db
from occasions.models import Occasion
from occasions.services import OccasionService

app = FastAPI()
logger = logging.getLogger(__name__)


async def repeat_func(seconds: int, func):
    while True:
        await func()
        await asyncio.sleep(seconds)


async def process_ocassions(db: Session):
    service = OccasionService()
    occasions = db.query(Occasion).filter(
        sa.and_(
            sa.or_(Occasion.is_draft.is_(False), Occasion.is_draft.is_(None)),
            Occasion.date_processed.is_(None),
            Occasion.is_processing.is_(False),
            Occasion.date < datetime.now(timezone.utc).isoformat()
        )
    ).all()

    # Mark occasions as processing
    for occasion in occasions:
        occasion.is_processing = True
    db.commit()

    # Process occasions
    for occasion in occasions:
        try:
            await service.process_occasion(db, occasion)
        except Exception as e:
            logger.error(f"Error processing occasion {occasion.id}: {str(e)}")
        finally:
            occasion.is_processing = False
            db.commit()


class OccasionTasks():
    def init(self):
        logger.info("Creating occasion tasks")
        # Start the background task
        asyncio.create_task(self.schedule_task(process_ocassions))

    async def schedule_task(self, func):
        db = next(get_db())
        await repeat_func(60, lambda: func(db))
