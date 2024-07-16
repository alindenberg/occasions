import logging
from fastapi import FastAPI

from occasions import routes as occasion_routes
from occasions.tasks import OccasionTasks as occasion_tasks

from users import routes as user_routes

app = FastAPI()

app.include_router(occasion_routes.router)
app.include_router(user_routes.router)

logging.basicConfig(level=logging.INFO)


@app.on_event("startup")
async def startup_event():
    occasion_tasks().init()
