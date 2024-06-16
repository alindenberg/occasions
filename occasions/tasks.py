import asyncio
import logging
from fastapi import FastAPI

app = FastAPI()
logger = logging.getLogger(__name__)


async def repeat_func(seconds: int, func):
    while True:
        await func()
        await asyncio.sleep(seconds)


async def send_occasion_notifications():
    logger.info("Sending occasion notifications")


class OccasionTasks():
    def __init__(self):
        self.tasks = []

    def add_task(self, task):
        self.tasks.append(task)

    def init(self):
        logger.info("Creating tasks")
        # Start the background task
        asyncio.create_task(repeat_func(60, send_occasion_notifications))
