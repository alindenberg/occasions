import logging
from datetime import datetime
from pydantic import BaseModel, EmailStr, field_serializer
from typing import Optional, Any

logger = logging.getLogger(__name__)


class BaseUser(BaseModel):
    email: EmailStr


class GoogleUserIn(BaseUser):
    google_id: str
    email: EmailStr


class UserIn(BaseUser):
    password: str


class RefreshTokenReq(BaseModel):
    refresh_token: str


class UserOut(BaseUser):
    id: int
    created: datetime
    is_superuser: Optional[bool] = None
    is_email_verified: Optional[bool] = None
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


class FeedbackRequest(BaseModel):
    feedback: str


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordReset(BaseModel):
    reset_hash: str
    new_password: str
