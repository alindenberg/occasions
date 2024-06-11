from fastapi import FastAPI

from db.database import engine
from occasions import models as occasion_models
from occasions import routes as occasion_routes

# Create tables
occasion_models.Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(occasion_routes.router)


@app.get("/")
async def root():
    return {"message": "Hello World"}
