from datetime import datetime

from sqlalchemy.orm import Session
from ..models.Request import Request


def create_request(db: Session, id: int, user_id: int, photo_url: str, response: str,
                   timestamp: datetime, success: bool, execution_time: float = None) -> Request:
    db_request = Request(id=id, user_id=user_id, photo_url=photo_url, response=response, timestamp=timestamp,
                         execution_time=execution_time, success=success)
    db.add(db_request)
    db.commit()
    db.refresh(db_request)

    return db_request.id
