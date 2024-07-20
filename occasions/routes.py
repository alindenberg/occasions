import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from db.database import get_db
from occasions.services import OccasionService
from occasions.types import OccasionIn, OccasionOut
from users.models import User
from users.utils import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/occasions/")
async def create_occasion(occasion: OccasionIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        OccasionService().create_occasion(db, user=user, **occasion.model_dump())
        return {"message": "Occasion created successfully"}
    except ValueError as e:
        logger.error(f"Value error raised while creating the occasion - {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"An error occurred while creating the occasion - {e}")
        raise HTTPException(status_code=500, detail="An error occurred while creating the occasion")


@router.get("/occasions/", response_model=List[OccasionOut])
async def get_occasions(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return OccasionService().get_occasions_for_user(db, user.id)


@router.get("/occasions/{occasion_id}", response_model=OccasionOut)
async def get_occasion(occasion_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    try:
        return OccasionService().get_occasion(db, occasion_id, user.id)
    except ValueError as e:
        logger.error(f"Value error raised while getting the occasion - {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"An error occurred while getting the occasion - {e}")
        raise HTTPException(status_code=500, detail="An error occurred while getting the occasion")


@router.put("/occasions/{occasion_id}")
async def update_occasion(occasion_id: int, occasion: OccasionIn, db: Session = Depends(get_db)):
    OccasionService().update_occasion(db, occasion_id, **occasion.model_dump())
    return {"message": "Occasion updated successfully"}


@router.delete("/occasions/{occasion_id}")
async def delete_occasion(occasion_id: int, db: Session = Depends(get_db)):
    OccasionService().delete_occasion(db, occasion_id)
    return {"message": "Occasion deleted successfully"}
