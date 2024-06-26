from datetime import datetime, timezone
from sqlalchemy import and_
from sqlalchemy.orm import Session

from occasions.models import Occasion
from users.models import User


class OccasionService:
    def create_occasion(self, db: Session, user: User, **kwargs):
        try:
            kwargs["date"] = kwargs["date"].isoformat() if kwargs.get("date") else None
            kwargs["created"] = datetime.now(timezone.utc).isoformat()
            kwargs["user_id"] = user.id
            kwargs["email"] = user.email
            occasion = Occasion(**kwargs)
            self._validate_occasion(db, occasion)
            db.add(occasion)
            db.commit()
            db.refresh(occasion)
            return occasion
        except (ValueError, Exception):
            db.rollback()
            raise

    def get_occasions_for_user(self, user_id: int, db: Session):
        return db.query(Occasion).filter(Occasion.user_id == user_id).all()

    def get_occasion(self, db: Session, occasion_id: int):
        return db.query(Occasion).get(occasion_id)

    def update_occasion(self, db: Session, occasion_id: int, **kwargs):
        occasion = db.query(Occasion).get(occasion_id)
        for key, value in kwargs.items():
            setattr(occasion, key, value)
        db.commit()
        db.refresh(occasion)
        return occasion

    def delete_occasion(self, db: Session, occasion_id: int):
        db.query(Occasion).filter(Occasion.id == occasion_id).delete()
        db.commit()
        return {"message": "Occasion deleted successfully"}

    def _validate_occasion(self, db: Session, occasion: Occasion):
        current_time = datetime.now(timezone.utc)
        existing_occasions = db.query(Occasion).filter(
            and_(
                Occasion.user_id == occasion.user_id,
                Occasion.id != occasion.id,
                Occasion.date >= current_time.isoformat()
            )
        ).count()
        if existing_occasions >= 3:
            raise ValueError("User can only have 3 upcoming occasions")
