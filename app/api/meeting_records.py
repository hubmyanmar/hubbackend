from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.crud import meeting_record as record_crud
from app.db.session import get_db
from app.core.security import get_current_user
from app.models.meeting import Meeting
from app.models.meeting_record import MeetingRecord
from app.models.user import User
from app.schemas import meeting_record as record_schemas
from app.schemas.translation import ProcessingStatusResponse

router = APIRouter(prefix="/meeting-records", tags=["meeting_records"])


@router.post("/", response_model=record_schemas.MeetingRecordOut, status_code=status.HTTP_201_CREATED)
def create_meeting_record(payload: record_schemas.MeetingRecordCreate, db: Session = Depends(get_db)):
    meeting = db.execute(text("SELECT 1 FROM meetings WHERE id = :id"), {"id": payload.meeting_id}).first()
    if meeting is None:
        raise HTTPException(status_code=400, detail="meeting_id not found")

    existing = record_crud.get_by_meeting_id(db=db, meeting_id=payload.meeting_id)
    if existing is not None:
        raise HTTPException(status_code=400, detail="A meeting record already exists for this meeting")

    return record_crud.create_meeting_record(db=db, payload=payload)


@router.get("/", response_model=List[record_schemas.MeetingRecordOut])
def read_meeting_records(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return record_crud.list_meeting_records(db=db, skip=skip, limit=limit)


@router.get("/{meeting_id}/status", response_model=ProcessingStatusResponse)
def read_meeting_processing_status(
    meeting_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if meeting is None:
        raise HTTPException(status_code=404, detail="Meeting not found")
    if meeting.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="You do not have access to this meeting")
    record = db.query(MeetingRecord).filter(MeetingRecord.meeting_id == meeting_id).first()
    if record is None:
        raise HTTPException(status_code=404, detail="Meeting recording not found")
    return ProcessingStatusResponse(
        task_id=record.task_id,
        meeting_id=meeting_id,
        status=record.status,
        error=record.processing_error,
    )


@router.get("/{meeting_id}", response_model=record_schemas.MeetingRecordOut)
def read_meeting_record(meeting_id: int, db: Session = Depends(get_db)):
    obj = record_crud.get_by_meeting_id(db=db, meeting_id=meeting_id)
    if obj is None:
        raise HTTPException(status_code=404, detail="Meeting record not found")
    return obj


@router.put("/{meeting_id}", response_model=record_schemas.MeetingRecordOut)
@router.patch("/{meeting_id}", response_model=record_schemas.MeetingRecordOut)
def update_meeting_record(
    meeting_id: int,
    updates: record_schemas.MeetingRecordUpdate,
    db: Session = Depends(get_db),
):
    obj = record_crud.get_by_meeting_id(db=db, meeting_id=meeting_id)
    if obj is None:
        raise HTTPException(status_code=404, detail="Meeting record not found")
    return record_crud.update_meeting_record(db=db, db_obj=obj, updates=updates)


@router.delete("/{meeting_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_meeting_record(meeting_id: int, db: Session = Depends(get_db)):
    obj = record_crud.get_by_meeting_id(db=db, meeting_id=meeting_id)
    if obj is None:
        raise HTTPException(status_code=404, detail="Meeting record not found")
    record_crud.delete_meeting_record(db=db, db_obj=obj)
    return None
