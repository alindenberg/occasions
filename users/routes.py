from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from typing import Annotated
from pydantic import BaseModel
from db.database import get_db

from users.models import User
from users.constants import ACCESS_TOKEN_EXPIRE_MINUTES
from users.services import UserService, UserAuthenticationService
from users.utils import get_current_user

router = APIRouter()


class UserIn(BaseModel):
    username: str
    email: EmailStr
    password: str


class UserOut(UserIn):
    id: int


class UserSignupForm(BaseModel):
    username: str
    email: EmailStr
    password: str


class TokenData(BaseModel):
    username: str


class UserInDB(BaseModel):
    password: str


@router.get("/users/me")
async def read_users_me(current_user: Annotated[User, Depends(get_current_user)]):
    return current_user


@router.get("/users")
async def users(db: Session = Depends(get_db)):
    return await UserService().get_all_users(db)


@router.post("/token")
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: Session = Depends(get_db)):
    token = await UserAuthenticationService().login(db, form_data)
    return {"access_token": token, "token_type": "bearer"}


@router.post("/signup")
async def signup(user: UserSignupForm, db: Session = Depends(get_db)):
    token = await UserAuthenticationService().signup(db, user)
    return {"access_token": token, "token_type": "bearer"}