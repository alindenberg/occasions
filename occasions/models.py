import logging
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship

from db.database import Base


logger = logging.getLogger(__name__)


class Occasion(Base):
    __tablename__ = "occasions"

    id = Column(Integer, primary_key=True, index=True)
    created = Column(String, nullable=False)
    label = Column(String, index=True)
    type = Column(String, index=True)
    email = Column(String, index=True)
    date = Column(String, index=True)
    custom_input = Column(String, index=True)
    summary = Column(Text, nullable=True)
    date_processed = Column(String, nullable=True)
    user_id = Column(Integer, ForeignKey('users.id'), index=True, nullable=False)
    user = relationship("User", back_populates="occasions")

    async def send_notification(self, db):
        if self.date_processed:
            logger.info(f"Occasion {self.id} has already been processed")
            return

        summary = await self.generate_summary()

        await self._send_email(summary)

        self.summary = summary
        self.date_processed = datetime.now(timezone.utc)
        db.commit()

    async def generate_summary(self):
        return f"Occasion {self.id} is coming up on {datetime.utcnow()}"

    async def _send_email(self, summary):
        pass
        # self.custom_input = summary
        # db.commit()