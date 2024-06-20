import jwt
import logging

from datetime import datetime, timedelta, timezone
from fastapi.security import OAuth2PasswordRequestForm
from passlib.context import CryptContext

from users.constants import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from users.exceptions import UserNotFoundException
from users.models import User
from users.types import UserIn

logger = logging.getLogger(__name__)


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
        db.refresh(db_user)
        return db_user

    async def get_user(self, db, user_id):
        return db.query(User).get(user_id)

    async def get_user_by_email(self, db, email):
        return db.query(User).filter(User.email == email).first()

    async def get_all_users(self, db):
        return db.query(User).all()

    async def _validate_unique_email(self, db, email):
        user = db.query(User).filter(User.email == email).count()
        print("user ", user)
        if user:
            raise ValueError("Email already registered")


class UserAuthenticationService(UserService):
    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    async def login(self, db, form_data: OAuth2PasswordRequestForm):
        try:
            user = await self.authenticate_user(db, form_data.username, form_data.password)
            if not user:
                raise UserNotFoundException("Invalid username of password")
            access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
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
                expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
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
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    def verify_password(self, plain_password, hashed_password):
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password):
        return self.pwd_context.hash(password)