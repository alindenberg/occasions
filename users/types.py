from pydantic import BaseModel, EmailStr
from datetime import datetime


class BaseUser(BaseModel):
    email: EmailStr


class UserIn(BaseUser):
    password: str


class UserOut(BaseUser):
    id: int
    created: datetime
