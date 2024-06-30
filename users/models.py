from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.orm import relationship

from db.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    created = Column(DateTime, index=True, nullable=False)
    email = Column(String, index=True)
    password = Column(String)
    occasions = relationship("Occasion", back_populates="user")
    is_superuser = Column(Boolean, default=False)
