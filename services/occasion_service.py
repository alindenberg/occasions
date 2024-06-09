
from db.database import SessionLocal
from sqlalchemy.orm import Session

from models import Occasion


class OccasionService:
    def create_occasion(self, db: Session, **kwargs):
        print(kwargs)
        occasion = Occasion(**kwargs)
        db.add(occasion)
        db.commit()
        db.refresh(occasion)
        return occasion

    def get_occasions(self, db: Session):
        return db.query(Occasion).all()
