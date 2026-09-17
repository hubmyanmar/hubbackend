from typing import List, Optional

from sqlalchemy.orm import Session

from app import models, schemas


def get_action_item(db: Session, action_item_id: int) -> Optional[models.ActionItem]:
    return db.query(models.ActionItem).filter(models.ActionItem.id == action_item_id).first()


def list_action_items_by_meeting(db: Session, meeting_id: int) -> List[models.ActionItem]:
    return db.query(models.ActionItem).filter(models.ActionItem.meeting_id == meeting_id).all()


def list_action_items(db: Session, skip: int = 0, limit: int = 100) -> List[models.ActionItem]:
    return db.query(models.ActionItem).offset(skip).limit(limit).all()


def create_action_item(db: Session, *, payload: schemas.ActionItemCreate) -> models.ActionItem:
    db_obj = models.ActionItem(**payload.dict(exclude_unset=True))
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def update_action_item(
    db: Session,
    *,
    db_obj: models.ActionItem,
    updates: schemas.ActionItemUpdate,
) -> models.ActionItem:
    data = updates.dict(exclude_unset=True)
    for field, value in data.items():
        setattr(db_obj, field, value)
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def delete_action_item(db: Session, *, db_obj: models.ActionItem) -> None:
    db.delete(db_obj)
    db.commit()
