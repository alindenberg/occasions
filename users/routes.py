import logging
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import Annotated
from db.database import get_db

from users.exceptions import UserNotFoundException
from users.models import User
from users.services import UserService, UserAuthenticationService
from users.types import UserIn, UserOut
from users.utils import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/users/me", response_model=UserOut)
async def read_users_me(current_user: Annotated[User, Depends(get_current_user)]):
    return current_user


@router.get("/users", response_model=list[UserOut])
async def users(db: Session = Depends(get_db)):
    return await UserService().get_all_users(db)


@router.post("/login")
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: Session = Depends(get_db)):
    try:
        token = await UserAuthenticationService().login(db, form_data)
        return {"access_token": token, "token_type": "bearer"}
    except UserNotFoundException:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
    except Exception as e:
        logger.error(f"An error occurred while logging in: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An error occurred while logging in")


@router.post("/signup")
async def signup(user: UserIn, db: Session = Depends(get_db)):
    try:
        token = await UserAuthenticationService().signup(db, user)
        return {"access_token": token, "token_type": "bearer"}
    except Exception as e:
        logger.error(f"An error occurred while signing up - {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An error occurred while signing up")
