from typing import List, Optional

from sqlalchemy.orm import Session, joinedload

from app import models, schemas


def get_meeting_record(db: Session, record_id: int) -> Optional[models.MeetingRecord]:
    return db.query(models.MeetingRecord).filter(models.MeetingRecord.id == record_id).first()


def get_by_meeting_id(db: Session, meeting_id: int) -> Optional[models.MeetingRecord]:
    return (
        db.query(models.MeetingRecord)
        .options(
            joinedload(models.MeetingRecord.meeting).joinedload(models.Meeting.room),
            joinedload(models.MeetingRecord.meeting).joinedload(models.Meeting.creator),
            joinedload(models.MeetingRecord.meeting).selectinload(models.Meeting.action_items),
        )
        .filter(models.MeetingRecord.meeting_id == meeting_id)
        .first()
    )


def list_meeting_records(db: Session, skip: int = 0, limit: int = 100) -> List[models.MeetingRecord]:
    return (
        db.query(models.MeetingRecord)
        .options(
            joinedload(models.MeetingRecord.meeting).joinedload(models.Meeting.room),
            joinedload(models.MeetingRecord.meeting).joinedload(models.Meeting.creator),
            joinedload(models.MeetingRecord.meeting).selectinload(models.Meeting.action_items),
        )
        .offset(skip)
        .limit(limit)
        .all()
    )


def create_meeting_record(db: Session, *, payload: schemas.MeetingRecordCreate) -> models.MeetingRecord:
    db_obj = models.MeetingRecord(**payload.dict(exclude_unset=True))
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def update_meeting_record(
    db: Session,
    *,
    db_obj: models.MeetingRecord,
    updates: schemas.MeetingRecordUpdate,
) -> models.MeetingRecord:
    data = updates.dict(exclude_unset=True)
    action_items = data.pop("action_items", None)
    for field, value in data.items():
        setattr(db_obj, field, value)

    if action_items is not None:
        for item in action_items:
            item["meeting_id"] = db_obj.meeting_id
            db.add(models.ActionItem(**item))

    try:
        db.add(db_obj)
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(db_obj)
    return db_obj


def delete_meeting_record(db: Session, *, db_obj: models.MeetingRecord) -> None:
    db.delete(db_obj)
    db.commit()
