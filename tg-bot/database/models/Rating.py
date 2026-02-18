from sqlalchemy import Column, BigInteger, Integer, ForeignKey
from sqlalchemy.orm import relationship
from datetime import date

from ..db_utils import Base


class Rating(Base):
    __tablename__ = "rating"

    id = Column(Integer, primary_key=True)
    request_id = Column(Integer, ForeignKey("request.id"), nullable=False)
    user_id = Column(BigInteger, ForeignKey("user.chat_id"), nullable=False)
    rating = Column(Integer)

    request = relationship("Request", back_populates="ratings")
    user = relationship("User", back_populates="ratings")
