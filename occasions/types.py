from datetime import datetime
from pydantic import BaseModel, EmailStr
from typing import Optional


from enum import Enum


class OccasionTone(str, Enum):
    NORMAL = 'normal'
    SYMPATHETIC = 'sympathetic'
    ENCOURAGING = 'encouraging'
    CELEBRATORY = 'celebratory'
    SARCASTIC = 'sarcastic'


class OccasionType(str, Enum):
    BIRTHDAY = 'birthday'
    ANNIVERSARY = 'anniversary'
    GRADUATION = 'graduation'
    OTHER = 'other'


class OccasionIn(BaseModel):
    label: str
    type: OccasionType
    tone: OccasionTone
    date: datetime
    custom_input: Optional[str]
    is_recurring: bool = False


class OccasionOut(OccasionIn):
    id: int
    user_id: int
    email: EmailStr
    date_processed: Optional[datetime]
    summary: Optional[str]
    created: datetime
    is_draft: bool
