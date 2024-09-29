import logging

from sqlalchemy.orm import Session
from datetime import datetime, timezone
from config import get_settings
from users.models import User, Credits, Feedback
from users.types import GoogleUserIn, UserIn
from passlib.context import CryptContext

logger = logging.getLogger(__name__)
settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserService:
    async def create_user(self, db, user):
        await self._validate_unique_email(db, user.email)
        db_user = User(
            created=datetime.now(timezone.utc),
            email=user.email,
            google_id=user.google_id
        )
        if isinstance(user, UserIn) and user.password:
            db_user.set_password(user.password)
        db.add(db_user)
        db.commit()

        # Credits module
        credits = Credits(user_id=db_user.id, credits=2)
        db.add(credits)
        db.commit()

        db.refresh(db_user)
        return db_user

    async def get_user_by_email(self, db, email):
        return db.query(User).filter(User.email == email).first()

    async def get_all_users(self, db):
        return db.query(User).all()

    async def _validate_unique_email(self, db, email):
        # Normalize the email by removing any part after a '+' sign before the '@' symbol
        local_part, domain_part = email.split('@')
        cleaned_email = local_part.split('+')[0] + '@' + domain_part

        user = db.query(User).filter(User.email == cleaned_email).count()
        if user:
            raise ValueError("Email already registered")

    async def create_feedback(self, db: Session, feedback: str, user: User = None):
        db_feedback = Feedback(feedback=feedback, user_id=user.id if user else None)
        db.add(db_feedback)
        db.commit()
        db.refresh(db_feedback)
        return db_feedback


class UserAuthenticationService(UserService):
    async def google_login(self, db, user: GoogleUserIn):
        db_user = db.query(User).filter(
            (User.google_id == user.google_id) | (User.email == user.email)
        ).first()
        if not db_user:
            logger.info('creating user')
            db_user = await self.create_user(db, user)
        elif not db_user.google_id and user.google_id:
            db_user.google_id = user.google_id
            db.commit()
        return db_user

    async def login(self, db, user: UserIn):
        db_user = db.query(User).filter(User.email == user.email).first()
        if not db_user:
            raise ValueError("User not found")
        if not db_user.check_password(user.password):
            raise ValueError("Invalid password")
        return db_user

    async def signup(self, db, user: UserIn):
        await self._validate_unique_email(db, user.email)
        db_user = User(
            created=datetime.now(timezone.utc),
            email=user.email,
            hashed_password=pwd_context.hash(user.password)
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
