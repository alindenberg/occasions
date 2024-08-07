import stripe

from db.database import Base
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from stripe_utils.services import StripeService


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    created = Column(DateTime, index=True, nullable=False)
    email = Column(String, index=True)
    password = Column(String)
    occasions = relationship("Occasion", back_populates="user")
    credits = relationship("Credits", uselist=False, back_populates="user")
    stripe_customer = relationship("StripeCustomer", uselist=False, back_populates="user")
    password_resets = relationship("PasswordReset", back_populates="user")
    is_superuser = Column(Boolean, default=False)

    def get_stripe_customer(self):
        if self.stripe_customer:
            return self.stripe_customer
        return StripeService().create_customer_for_user(self)

    def add_credits(self, quantity):
        if not self.credits:
            self.credits = Credits(user_id=self.id, credits=quantity)
        else:
            self.credits.credits += quantity


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


class PasswordReset(Base):
    __tablename__ = "password_resets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    reset_hash = Column(String, unique=True, index=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)

    user = relationship("User", back_populates="password_resets")
