from sqlalchemy.orm import Session
from typing import List, Optional
from app import models, schemas


def get_meeting(db: Session, meeting_id: int) -> Optional[models.Meeting]:
    return db.query(models.Meeting).filter(models.Meeting.id == meeting_id).first()


def list_meetings(db: Session, skip: int = 0, limit: int = 100) -> List[models.Meeting]:
    return db.query(models.Meeting).offset(skip).limit(limit).all()


def create_meeting(db: Session, *, meeting_in: schemas.MeetingCreate) -> models.Meeting:
    db_obj = models.Meeting(**meeting_in.dict(exclude_unset=True))
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def update_meeting(db: Session, *, db_obj: models.Meeting, updates: schemas.MeetingUpdate) -> models.Meeting:
    data = updates.dict(exclude_unset=True)
    for field, value in data.items():
        setattr(db_obj, field, value)
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def delete_meeting(db: Session, *, db_obj: models.Meeting) -> None:
    db.delete(db_obj)
    db.commit()
