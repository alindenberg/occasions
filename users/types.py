from datetime import datetime
from pydantic import BaseModel, EmailStr
from typing import Optional


class BaseUser(BaseModel):
    email: EmailStr


class UserIn(BaseUser):
    password: str


class UserOut(BaseUser):
    id: int
    created: datetime
    is_superuser: Optional[bool] = None
