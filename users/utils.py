from db.database import get_db
from jwt import InvalidTokenError
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from typing import Annotated
from sqlalchemy.orm import Session

from config import get_settings
from users.services import UserService
from users.google_auth import verify_google_token

settings = get_settings()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        user_dict = verify_google_token(token)
        if user_dict is None:
            raise credentials_exception
        email = user_dict.get('email')
        if not email:
            raise credentials_exception

    except InvalidTokenError:
        raise credentials_exception
    user = await UserService().get_user_by_email(db, email)
    if user is None:
        raise credentials_exception
    return user
