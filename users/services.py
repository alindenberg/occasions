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
            password=user.password
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
        user = db.query(User).filter(User.email == email).count()
        if user:
            raise ValueError("Email already registered")


class UserAuthenticationService(UserService):
    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    async def login(self, db, form_data: OAuth2PasswordRequestForm):
        try:
            user = await self.authenticate_user(db, form_data.username, form_data.password)
            if not user:
                raise UserNotFoundException("Invalid username or password")
            access_token_expires = timedelta(minutes=settings.JWT_EXP_MINUTES)
            access_token = self.create_access_token(data={"sub": user.email}, expires_delta=access_token_expires)
            return access_token
        except Exception as e:
            logger.error(f"An error occurred while logging in: {e}")
            raise e

    async def signup(self, db, user: UserIn):
        try:
            user.password = self.get_password_hash(user.password)
            user = await self.create_user(db, user)
            access_token = self.create_access_token(
                data={"sub": user.email},
                expires_delta=timedelta(minutes=settings.JWT_EXP_MINUTES)
            )
            return access_token
        except Exception as e:
            logger.error(f"An error occurred while signing up: {e}")
            raise e

    async def authenticate_user(self, db, email: str, password: str):
        user = await self.get_user_by_email(db, email)
        if not user:
            return False
        if not self.verify_password(password, user.password):
            return False
        return user

    def create_access_token(self, data: dict, expires_delta: timedelta | None = None):
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=15)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.JWT_SALT, algorithm=settings.JWT_ALGORITHM)
        return encoded_jwt

    def verify_password(self, plain_password, hashed_password):
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password):
        return self.pwd_context.hash(password)

    def generate_reset_hash(self, db: Session, user: User):
        # Generate a unique hash
        reset_hash = hashlib.sha256(f"{user.email}{datetime.utcnow().isoformat()}".encode()).hexdigest()
        expiration_time = datetime.utcnow() + timedelta(minutes=15)

        # Store the hash and expiration time in the database
        password_reset = PasswordReset(user_id=user.id, reset_hash=reset_hash, expires_at=expiration_time)
        db.add(password_reset)
        db.commit()

        # Send email with the reset link
        reset_link = f"{settings.NEXT_PUBLIC_URL}/account/reset-password?hash={reset_hash}"
        self.send_reset_email(user.email, reset_link)

        logger.info(f"Password reset hash generated and email sent to: {user.email}")
        return {"msg": "Password reset email sent"}

    def send_reset_email(self, email: EmailStr, reset_link: str):
        subject = "Password Reset"
        body = f"Reset your password using the following link. The link will expire in 15 minutes. Link: {reset_link}"
        MailService().send_email(email, subject, body)

    def verify_password_reset_hash(self, db, reset_hash: str):
        from users.models import PasswordReset

        # Retrieve the hash from the database
        password_reset = db \
            .query(PasswordReset) \
            .filter(PasswordReset.reset_hash == reset_hash) \
            .first()
        if not password_reset or password_reset.expires_at < datetime.utcnow():
            logger.error("Invalid or expired password reset hash")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired password reset hash")

        return password_reset.user_id

    def reset_password(self, db: Session, reset_hash: str, new_password: str, confirm_new_password: str):
        if new_password != confirm_new_password:
            logger.error("Passwords do not match")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Passwords do not match")

        user_id = self.verify_password_reset_hash(db, reset_hash)

        # Hash the new password
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        hashed_password = pwd_context.hash(new_password)

        # Update the user's password in the database
        user = db.query(User).filter(User.id == user_id).first()
        setattr(user, "password", hashed_password)
        db.commit()
        db.refresh(user)

        db.query(PasswordReset).filter(PasswordReset.reset_hash == reset_hash).delete()
        db.commit()

        logger.info(f"Password reset successfully for user: {user.id}")
        return {"msg": "Password reset successfully"}
