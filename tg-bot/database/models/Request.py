from sqlalchemy import Column, Integer, BigInteger, String, Text, ForeignKey, Date, Float, Boolean
from sqlalchemy.orm import relationship
from datetime import date
from ..db_utils import Base


class Request(Base):
    __tablename__ = "request"

    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("user.chat_id"), nullable=False)
    photo_url = Column(String)
    response = Column(Text)

    execution_time = Column(Float)
    success = Column(Boolean)

    timestamp = Column(Date, default=date.today)

    user = relationship("User", back_populates="requests")
    ratings = relationship("Rating", back_populates="request")
