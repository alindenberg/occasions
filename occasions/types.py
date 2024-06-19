from datetime import date, datetime
from pydantic import BaseModel, EmailStr
from typing import Optional


class OccasionIn(BaseModel):
    type: str
    # email: EmailStr
    date: date
    custom_input: Optional[str]


class OccasionOut(OccasionIn):
    id: int
    user_id: int
    email: EmailStr
    date_processed: Optional[datetime]
    summary: Optional[str]