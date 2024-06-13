import jwt

from datetime import datetime, timedelta, timezone
from fastapi.security import OAuth2PasswordRequestForm
from passlib.context import CryptContext
from pydantic import BaseModel

from users.constants import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from users.models import User


class UserCreate(BaseModel):
    username: str
    email: str
    password: str


class UserService:
    async def create_user(self, db, user):
        db_user = User(
            username=user.username,
            email=user.email,
            password=user.password
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user

    async def get_user(self, db, user_id):
        return db.query(User).get(user_id)

    async def get_user_by_username(self, db, username):
        return db.query(User).filter(User.username == username).first()

    async def get_all_users(self, db):
        return db.query(User).all()


class UserAuthenticationService(UserService):
    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    async def login(self, db, form_data: OAuth2PasswordRequestForm):
        user = await self.authenticate_user(db, form_data.username, form_data.password)
        if not user:
            return False
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = self.create_access_token(data={"sub": user.username}, expires_delta=access_token_expires)
        return access_token

    async def signup(self, db, user: UserCreate):
        user.password = self.get_password_hash(user.password)
        user = await self.create_user(db, user)
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = self.create_access_token(data={"sub": user.username}, expires_delta=access_token_expires)
        return access_token

    async def authenticate_user(self, db, username: str, password: str):
        user = await self.get_user_by_username(db, username)
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