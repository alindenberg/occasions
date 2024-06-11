from sqlalchemy import Column, Integer, String

from db.database import Base


class Occasion(Base):
    __tablename__ = "occasions"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(String, index=True)
    email = Column(String, index=True)
    date = Column(String, index=True)
    custom_input = Column(String, index=True)
