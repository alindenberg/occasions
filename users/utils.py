import os
import jwt

from db.database import get_db
from jwt import InvalidTokenError
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from typing import Annotated
from sqlalchemy.orm import Session

from users.services import UserService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        jwt_salt = os.getenv("JWT_SALT")
        jwt_algo = os.getenv("JWT_ALGORITHM")
        payload = jwt.decode(token, jwt_salt, algorithms=[jwt_algo])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except InvalidTokenError:
        raise credentials_exception
    user = await UserService().get_user_by_email(db, email)
    if user is None:
        raise credentials_exception
    return user
