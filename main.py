from datetime import date
from fastapi import FastAPI, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

import models
from db.database import get_db, engine
from services.occasion_service import OccasionService

# Create tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI()


class OccasionIn(BaseModel):
    type: str
    email: str
    date: date
    custom_input: str = None


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.post("/occasions/")
async def create_occasion(occasion: OccasionIn, db: Session = Depends(get_db)):
    OccasionService().create_occasion(db, **occasion.model_dump())
    return {"message": "Occasion created successfully"}


@app.get("/occasions/")
async def get_occasions(db: Session = Depends(get_db)):
    return OccasionService().get_occasions(db)
