from db.database import get_db
from jose import jwt, JWTError
from jwt import InvalidTokenError
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from typing import Annotated
from users.services import UserService
from users.google_auth import verify_google_token
from users.models import User
from config import get_settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
settings = get_settings()


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, settings.JWT_SALT, algorithms=[settings.JWT_ALGORITHM])
        email = payload.get("sub")
        if email:
            user = await UserService().get_user_by_email(db, email)
            if user:
                return user
    except JWTError:
        # If JWT decoding fails, try Google token verification
        try:
            user_dict = verify_google_token(token)
            if user_dict:
                email = user_dict.get('email')
                if email:
                    user = await UserService().get_user_by_email(db, email)
                    if user:
                        return user
        except InvalidTokenError:
            pass

    raise credentials_exception


anon_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)


async def get_current_user_or_none(
    token: str | None = Depends(anon_oauth2_scheme),
    db: Session = Depends(get_db)
):
    if not token:
        return None
    return await get_current_user(token, db)


async def email_verified(current_user: Annotated[User, Depends(get_current_user)]):
    if not current_user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified. Please verify your email before creating occasions."
        )
    return current_user
