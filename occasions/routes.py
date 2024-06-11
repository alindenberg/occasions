from datetime import date
from fastapi import APIRouter, Depends
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from typing import List, Optional

from db.database import get_db
from occasions.service import OccasionService

router = APIRouter()


class OccasionIn(BaseModel):
    type: str
    email: EmailStr
    date: date
    custom_input: Optional[str]


class OccasionOut(OccasionIn):
    id: int


@router.post("/occasions/")
async def create_occasion(occasion: OccasionIn, db: Session = Depends(get_db)):
    OccasionService().create_occasion(db, **occasion.model_dump())
    return {"message": "Occasion created successfully"}


@router.get("/occasions/", response_model=List[OccasionOut])
async def get_occasions(db: Session = Depends(get_db)):
    return OccasionService().get_occasions(db)


@router.get("/occasions/{occasion_id}", response_model=OccasionOut)
async def get_occasion(occasion_id: int, db: Session = Depends(get_db)):
    return OccasionService().get_occasion(db, occasion_id)


@router.put("/occasions/{occasion_id}")
async def update_occasion(occasion_id: int, occasion: OccasionIn, db: Session = Depends(get_db)):
    OccasionService().update_occasion(db, occasion_id, **occasion.model_dump())
    return {"message": "Occasion updated successfully"}


@router.delete("/occasions/{occasion_id}")
async def delete_occasion(occasion_id: int, db: Session = Depends(get_db)):
    OccasionService().delete_occasion(db, occasion_id)
    return {"message": "Occasion deleted successfully"}
