from sqlalchemy.orm import Session
from ..models.Rating import Rating


def create_rating(db: Session, user_id: int, request_id: int, rating: int) -> Rating:
    db_request = Rating(user_id=user_id, request_id=request_id, rating=rating)
    db.add(db_request)
    db.commit()
    db.refresh(db_request)

    return db_request
