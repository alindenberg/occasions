from datetime import date
from pydantic import BaseModel, EmailStr
from typing import Optional


class OccasionIn(BaseModel):
    type: str
    email: EmailStr
    date: date
    custom_input: Optional[str]


class OccasionOut(OccasionIn):
    id: int
    user_id: int