import asyncio
import logging
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, status
from jose import jwt
from sqlalchemy.orm import Session
from config import get_settings
from mail.services import MailService
from passlib.context import CryptContext
from users.models import User, Credits, Feedback, EmailVerification
from users.types import GoogleUserIn, UserIn
import secrets

logger = logging.getLogger(__name__)
settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserService:
    async def create_user(self, db, user):
        await self._validate_unique_email(db, user.email)
        db_user = User(
            created=datetime.now(timezone.utc),
            email=user.email,
            google_id=user.google_id if hasattr(user, 'google_id') else None,
            hashed_password=pwd_context.hash(user.password) if hasattr(user, 'password') else None
        )
        db.add(db_user)
        db.commit()

        # Credits module
        credits = Credits(user_id=db_user.id, credits=2)
        db.add(credits)
        db.commit()

        db.refresh(db_user)

        asyncio.create_task(self.create_email_verification(db, db_user))

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

    async def create_email_verification(self, db: Session, user: User) -> str:
        token = secrets.token_urlsafe(32)
        verification = EmailVerification(user_id=user.id, token=token)
        db.add(verification)
        db.commit()

        asyncio.create_task(self.send_verification_email(db, token, user))

        return token

    async def send_verification_email(self, db: Session, token: str, user: User):
        verification_url = f"{settings.NEXT_PUBLIC_URL}/verify-email/{token}"
        MailService().send_verification_email(user.email, verification_url)
        return verification_url

    async def verify_email(self, db: Session, token: str) -> bool:
        verification = db.query(EmailVerification).filter(
            EmailVerification.token == token,
            EmailVerification.expires_at > datetime.now(timezone.utc)
        ).first()

        if verification:
            user = verification.user
            user.email_verified = True
            db.delete(verification)
            db.commit()
            return True
        return False


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

    async def login(self, db, email, password):
        db_user = db.query(User).filter(User.email == email).first()
        if not db_user:
            raise ValueError("User not found")
        if not db_user.check_password(password):
            raise ValueError("Invalid password")

        access_token, expires_at, refresh_token = self.create_auth_tokens(db, db_user, data={"sub": email})
        return {
            "id": db_user.id,
            "access_token": access_token,
            "expires_at": expires_at,
            "refresh_token": refresh_token,
        }

    async def signup(self, db, user: UserIn):
        db_user = await self.create_user(db, user)

        access_token, expires_at, refresh_token = self.create_auth_tokens(db, db_user, data={"sub": db_user.email})
        return {
            "id": db_user.id,
            "access_token": access_token,
            "expires_at": expires_at,
            "refresh_token": refresh_token
        }

    def create_auth_tokens(self, db, user, data: dict):
        access_token, expires_at = self._create_access_token(data)
        refresh_token = self._create_refresh_token(data)
        user.refresh_token = refresh_token
        db.commit()
        return access_token, expires_at, refresh_token

    def _create_access_token(self, data: dict):
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + timedelta(minutes=int(settings.JWT_EXP_MINUTES))
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.JWT_SALT, algorithm=settings.JWT_ALGORITHM)
        return encoded_jwt, int(expire.timestamp())

    def _create_refresh_token(self, data: dict):
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + timedelta(days=30)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.REFRESH_TOKEN_SALT, algorithm=settings.JWT_ALGORITHM)
        return encoded_jwt

    async def refresh_token(self, db: Session, refresh_token: str):
        try:
            payload = jwt.decode(refresh_token, settings.REFRESH_TOKEN_SALT, algorithms=[settings.JWT_ALGORITHM])
            email: str = payload.get("sub")
        except jwt.JWTError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

        user = db.query(User).filter(User.email == email).first()
        if not user or user.refresh_token != refresh_token:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

        new_access_token, expires_at = self._create_access_token({"sub": user.email})
        return {"access_token": new_access_token, "expires_at": expires_at}