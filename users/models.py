from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship

from db.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    created = Column(DateTime, index=True, nullable=False)
    username = Column(String, index=True)
    email = Column(String, index=True)
    password = Column(String)
    occasions = relationship("Occasion", back_populates="user")
