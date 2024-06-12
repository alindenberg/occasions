import jwt

from datetime import datetime, timedelta, timezone
from jwt.exceptions import InvalidTokenError
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import Annotated
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr


from db.database import engine, get_db
from occasions import models as occasion_models
from occasions import routes as occasion_routes
from users import models as user_models
from users.services import UserService as user_service

# Create tables
occasion_models.Base.metadata.create_all(bind=engine)
user_models.Base.metadata.create_all(bind=engine)

SECRET_KEY = "randomsecretkey"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

app = FastAPI()

app.include_router(occasion_routes.router)
# app.include_router(user_routes.router)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


async def authenticate_user(db, username: str, password: str):
    user = await user_service().get_user_by_username(db, username)
    print("user is", user)
    print("password is", password)
    if not user:
        return False
    if not verify_password(password, user.password):
        return False
    return user


class TokenData(BaseModel):
    username: str


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except InvalidTokenError:
        raise credentials_exception
    user = user_service().get_user_by_username(token_data.username)
    if user is None:
        raise credentials_exception
    return user


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/users/me")
async def read_users_me(current_user: Annotated[user_models.User, Depends(get_current_user)]):
    return current_user


class UserInDB(BaseModel):
    password: str


@app.post("/token")
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: Session = Depends(get_db)):
    user = await authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.username}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}


class UserSignupForm(BaseModel):
    username: str
    email: EmailStr
    password: str


@app.post("/signup")
async def signup(user: UserSignupForm, db: Session = Depends(get_db)):
    user.password = get_password_hash(user.password)
    user = await user_service().create_user(db, user)
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.username}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}