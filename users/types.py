import logging
from datetime import datetime
from pydantic import BaseModel, EmailStr, field_serializer
from typing import Optional, Any

logger = logging.getLogger(__name__)


class BaseUser(BaseModel):
    email: EmailStr


class UserIn(BaseUser):
    password: str


# class CreditOut(BaseModel):
#     credits: int


class UserOut(BaseUser):
    id: int
    created: datetime
    is_superuser: Optional[bool] = None
    credits: Any

    @field_serializer('credits')
    def credits_serializer(self, credits, _info):
        try:
            return credits.credits if credits else 0
        except Exception as exc:
            logger.error(f"An error occurred while serializing credits: {exc}")
            return 0


class CheckoutRequest(BaseModel):
    quantity: int


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordReset(BaseModel):
    new_password: str
    confirm_new_password: str
    reset_hash: str