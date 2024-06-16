import logging
from fastapi import FastAPI

from db.database import engine
from occasions import models as occasion_models
from occasions import routes as occasion_routes
from occasions.tasks import OccasionTasks as occasion_tasks

from users import models as user_models
from users import routes as user_routes

# Create tables
occasion_models.Base.metadata.create_all(bind=engine)
user_models.Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(occasion_routes.router)
app.include_router(user_routes.router)

logging.basicConfig(level=logging.INFO)


@app.on_event("startup")
async def startup_event():
    occasion_tasks().init()
