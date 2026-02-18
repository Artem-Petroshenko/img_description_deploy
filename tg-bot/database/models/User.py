from sqlalchemy import Column, BigInteger, String, Date
from sqlalchemy.orm import relationship
from datetime import date

from ..db_utils import Base


class User(Base):
    __tablename__ = "user"

    chat_id = Column(BigInteger, primary_key=True, unique=True)
    first_name = Column(String)
    last_name = Column(String)
    link = Column(String)
    username = Column(String)
    registered_at = Column(Date, default=date.today)

    requests = relationship("Request", back_populates="user")
    ratings = relationship("Rating", back_populates="user")
