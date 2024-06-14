
from sqlalchemy.orm import Session

from occasions.models import Occasion


class OccasionService:
    def create_occasion(self, db: Session, **kwargs):
        print(kwargs)
        occasion = Occasion(**kwargs)
        db.add(occasion)
        db.commit()
        db.refresh(occasion)
        return occasion

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
