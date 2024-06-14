from datetime import date
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from db.database import get_db
from occasions.services import OccasionService
from occasions.types import OccasionIn, OccasionOut
from users.models import User
from users.utils import get_current_user

router = APIRouter()


@router.post("/occasions/")
async def create_occasion(occasion: OccasionIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    OccasionService().create_occasion(db, user=user, **occasion.model_dump())
    return {"message": "Occasion created successfully"}


@router.get("/occasions/", response_model=List[OccasionOut])
async def get_occasions(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return OccasionService().get_occasions_for_user(user.id, db)


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
