import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timezone

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
        raise HTTPException(status_code=500, detail=f"An error occurred while creating the occasion: {str(e)}")


@router.get("/occasions/", response_model=List[OccasionOut])
async def get_occasions(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        return OccasionService().get_occasions_for_user(db, user.id)
    except Exception as e:
        logger.error(f"An error occurred while getting the occasions - {e}")
        raise HTTPException(status_code=500, detail="An error occurred while getting the occasions")


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
async def update_occasion(
    occasion_id: int,
    occasion: OccasionIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    try:
        # Get the occasion to check if it's a draft or has a future date
        existing_occasion = OccasionService().get_occasion(db, occasion_id, user.id)

        # Check if the occasion is a draft or has a future date
        if not existing_occasion.is_draft and datetime.fromisoformat(existing_occasion.date) <= datetime.now(timezone.utc):
            raise HTTPException(
                status_code=403,
                detail="Cannot modify processed occasions"
            )

        # If it's a draft or has a future date, proceed with modification
        OccasionService().update_occasion(db, existing_occasion, **occasion.model_dump())
        return {"message": "Occasion updated successfully"}
    except ValueError as e:
        logger.error(f"Value error raised while updating the occasion - {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException as e:
        # Re-raise HTTP exceptions
        raise e
    except Exception as e:
        logger.error(f"An error occurred while updating the occasion - {e}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while updating the occasion"
        )


@router.delete("/occasions/{occasion_id}")
async def delete_occasion(
    occasion_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    try:
        # Get the occasion to check if it's a draft or has a future date
        existing_occasion = OccasionService().get_occasion(db, occasion_id, user.id)

        # Check if the occasion is a draft or has a future date
        if not existing_occasion.is_draft and datetime.fromisoformat(existing_occasion.date) <= datetime.now(timezone.utc):
            raise HTTPException(
                status_code=403,
                detail="Cannot delete processed occasions"
            )

        # If it's a draft or has a future date, proceed with deletion
        OccasionService().delete_occasion(db, occasion_id)
        return {"message": "Occasion deleted successfully"}
    except ValueError as e:
        logger.error(f"Value error raised while deleting the occasion - {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException as e:
        # Re-raise HTTP exceptions
        raise e
    except Exception as e:
        logger.error(f"An error occurred while deleting the occasion - {e}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while deleting the occasion"
        )


@router.post("/occasions/{occasion_id}/activate")
async def activate_draft_occasion(
    occasion_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        activated_occasion = OccasionService().activate_draft_occasion(db, occasion_id, user)
        return {"message": "Draft occasion activated successfully", "occasion": activated_occasion}
    except ValueError as e:
        logger.error(f"Value error raised while activating draft occasion - {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"An error occurred while activating draft occasion - {e}")
        raise HTTPException(status_code=500, detail="An error occurred while activating draft occasion")
