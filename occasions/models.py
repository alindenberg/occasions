import logging
from sqlalchemy import Column, Integer, String, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship

from db.database import Base
from occasions.types import OccasionTone, OccasionType

logger = logging.getLogger(__name__)


class Occasion(Base):
    __tablename__ = "occasions"

    id = Column(Integer, primary_key=True, index=True)
    created = Column(String, nullable=False)
    label = Column(String)
    type = Column(String, index=True)
    tone = Column(String)
    email = Column(String)
    date = Column(String)
    custom_input = Column(String)
    summary = Column(Text, nullable=True)
    date_processed = Column(String, nullable=True)
    user_id = Column(Integer, ForeignKey('users.id'), index=True, nullable=False)
    user = relationship("User", back_populates="occasions")