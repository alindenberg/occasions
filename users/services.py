import jwt
import hashlib
import logging

from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from passlib.context import CryptContext
from pydantic import EmailStr
from sqlalchemy.orm import Session

from config import get_settings
from mail.services import MailService
from users.exceptions import UserNotFoundException
from users.models import User, Credits, PasswordReset
from users.types import UserIn

logger = logging.getLogger(__name__)
settings = get_settings()


class UserService:
    async def create_user(self, db, user):
        await self._validate_unique_email(db, user.email)
        db_user = User(
            created=datetime.now(timezone.utc),
            email=user.email,
            google_id=user.google_id
        )
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


class UserAuthenticationService(UserService):
    async def login(self, db, user: UserIn):
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
