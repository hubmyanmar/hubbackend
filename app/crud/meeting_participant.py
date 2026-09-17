from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from app import models, schemas


def get_participant(db: Session, participant_id: int) -> Optional[models.MeetingParticipant]:
    return db.query(models.MeetingParticipant).filter(models.MeetingParticipant.id == participant_id).first()


def list_participants_by_meeting(db: Session, meeting_id: int) -> List[models.MeetingParticipant]:
    return db.query(models.MeetingParticipant).filter(models.MeetingParticipant.meeting_id == meeting_id).all()


def get_by_meeting_and_zoho(db: Session, meeting_id: int, zoho_user_id: str) -> Optional[models.MeetingParticipant]:
    return db.query(models.MeetingParticipant).filter(
        models.MeetingParticipant.meeting_id == meeting_id,
        models.MeetingParticipant.zoho_user_id == zoho_user_id,
    ).first()


def create_participant(db: Session, payload: schemas.MeetingParticipantCreate) -> models.MeetingParticipant:
    obj = models.MeetingParticipant(**payload.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def upsert_by_zoho(db: Session, meeting_id: int, zoho_user_id: str, name: str, email: str) -> models.MeetingParticipant:
    existing = get_by_meeting_and_zoho(db, meeting_id, zoho_user_id)
    if existing:
        existing.name = name
        existing.email = email
        db.add(existing)
        db.commit()
        db.refresh(existing)
        return existing

    payload = schemas.MeetingParticipantCreate(
        meeting_id=meeting_id,
        zoho_user_id=zoho_user_id,
        name=name,
        email=email,
    )
    return create_participant(db, payload)


def delete_participant(db: Session, participant: models.MeetingParticipant) -> None:
    db.delete(participant)
    db.commit()


def bulk_sync_from_zoho(db: Session, meeting_id: int, users: List[Dict[str, str]]) -> List[models.MeetingParticipant]:
    """Given a list of user dicts with keys zoho_user_id, name, email, upsert them for the meeting."""
    results: List[models.MeetingParticipant] = []
    for u in users:
        if not u.get("zoho_user_id") or not u.get("email"):
            continue
        obj = upsert_by_zoho(db, meeting_id, u["zoho_user_id"], u.get("name") or "", u.get("email"))
        results.append(obj)
    return results
