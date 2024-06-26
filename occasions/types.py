from datetime import datetime
from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class OccasionIn(BaseModel):
    type: str
    label: str
    date: datetime
    custom_input: Optional[str]


class OccasionOut(OccasionIn):
    id: int
    user_id: int
    email: EmailStr
    label: str
    date: datetime
    custom_input: Optional[str]
    date_processed: Optional[datetime]
    summary: Optional[str]
    created: datetime