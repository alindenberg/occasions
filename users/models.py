from db.database import Base
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from stripe_utils.services import StripeService


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    created = Column(DateTime, index=True, nullable=False)
    email = Column(String, unique=True, index=True)
    google_id = Column(String, unique=True, index=True)
    occasions = relationship("Occasion", back_populates="user")
    credits = relationship("Credits", uselist=False, back_populates="user")
    stripe_customer = relationship("StripeCustomer", uselist=False, back_populates="user")
    is_superuser = Column(Boolean, default=False)
    feedback = relationship("Feedback", back_populates="user")
    hashed_password = Column(String, nullable=True)
    is_email_verified = Column(Boolean, default=False)  # New field
    email_verifications = relationship("EmailVerification", back_populates="user")
    password_resets = relationship("PasswordReset", back_populates="user")
    refresh_token = Column(String, nullable=True)

    def get_stripe_customer(self):
        if self.stripe_customer:
            return self.stripe_customer
        return StripeService().create_customer_for_user(self)

    def add_credits(self, quantity):
        if not self.credits:
            self.credits = Credits(user_id=self.id, credits=quantity)
        else:
            self.credits.credits += quantity

    def check_password(self, password):
        return pwd_context.verify(password, self.hashed_password)


class StripeCustomer(Base):
    __tablename__ = "stripe_customers"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), index=True, nullable=False)
    user = relationship("User", back_populates="stripe_customer")
    stripe_customer_id = Column(String, unique=True, nullable=False)


class Credits(Base):
    __tablename__ = "credits"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), index=True, nullable=False)
    user = relationship("User", back_populates="credits")
    credits = Column(Integer, default=0)


class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, index=True)
    feedback = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    user = relationship("User", back_populates="feedback")


class EmailVerification(Base):
    __tablename__ = "email_verifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    token = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    expires_at = Column(DateTime, default=datetime.now(timezone.utc) + timedelta(days=1))

    user = relationship("User", back_populates="email_verifications")


class PasswordReset(Base):
    __tablename__ = "password_resets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    token = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    expires_at = Column(DateTime, default=datetime.now(timezone.utc) + timedelta(hours=1))

    user = relationship("User", back_populates="password_resets")
