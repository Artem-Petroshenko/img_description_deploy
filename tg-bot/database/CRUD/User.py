import datetime
from sqlalchemy.orm import Session
from ..models.User import User


def create_user(db: Session, chat_id: int, first_name: str, last_name: str, link: str,
                username: str, registered_at: datetime.datetime) -> User:

    existing = is_user_exist(db, chat_id)
    if existing:
        return existing
    db_user = User(chat_id=chat_id, first_name=first_name, last_name=last_name,
                   link=link, username=username, registered_at=registered_at)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user


def is_user_exist(db: Session, chat_id: int) -> User:
    return db.query(User).filter(User.chat_id == chat_id).first()
