from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.crud import meeting_record as record_crud
from app.db.session import get_db
from app.schemas import meeting_record as record_schemas

router = APIRouter(prefix="/meeting-records", tags=["meeting_records"])


@router.post("/", response_model=record_schemas.MeetingRecordOut, status_code=status.HTTP_201_CREATED)
def create_meeting_record(payload: record_schemas.MeetingRecordCreate, db: Session = Depends(get_db)):
    meeting = db.execute("SELECT 1 FROM meetings WHERE id = :id", {"id": payload.meeting_id}).first()
    if meeting is None:
        raise HTTPException(status_code=400, detail="meeting_id not found")

    existing = record_crud.get_by_meeting_id(db=db, meeting_id=payload.meeting_id)
    if existing is not None:
        raise HTTPException(status_code=400, detail="A meeting record already exists for this meeting")

    return record_crud.create_meeting_record(db=db, payload=payload)


@router.get("/", response_model=List[record_schemas.MeetingRecordOut])
def read_meeting_records(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return record_crud.list_meeting_records(db=db, skip=skip, limit=limit)


@router.get("/{meeting_id}", response_model=record_schemas.MeetingRecordOut)
def read_meeting_record(meeting_id: int, db: Session = Depends(get_db)):
    obj = record_crud.get_by_meeting_id(db=db, meeting_id=meeting_id)
    if obj is None:
        raise HTTPException(status_code=404, detail="Meeting record not found")
    return obj


@router.put("/{meeting_id}", response_model=record_schemas.MeetingRecordOut)
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
