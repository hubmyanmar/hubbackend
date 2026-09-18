from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List

from app.schemas import meeting as meeting_schemas
from app.crud import meeting as meeting_crud
from app.db.session import get_db
from app import models

router = APIRouter(prefix="/meetings", tags=["meetings"])


@router.post("/", response_model=meeting_schemas.MeetingOut, status_code=status.HTTP_201_CREATED)
def create_meeting(meeting_in: meeting_schemas.MeetingCreate, db: Session = Depends(get_db)):
    if meeting_in.end_time <= meeting_in.start_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="end_time must be after start_time"
        )

    if meeting_in.room_id is not None:
        room = db.execute(
            text("SELECT 1 FROM meeting_rooms WHERE id = :id"), 
            {"id": meeting_in.room_id}
        ).first()
        if room is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="room_id not found"
            )

        has_conflict = meeting_crud.check_room_conflict(
            db=db,
            room_id=meeting_in.room_id,
            meeting_date=meeting_in.meeting_date,
            start_time=meeting_in.start_time,
            end_time=meeting_in.end_time
        )
        if has_conflict:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The selected room is already booked for this date and time range."
            )

    user = db.execute(
        text("SELECT 1 FROM users WHERE id = :id"), 
        {"id": meeting_in.created_by}
    ).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="created_by user not found"
        )

    db_obj = meeting_crud.create_meeting(db=db, meeting_in=meeting_in)
    return db_obj


@router.get("/", response_model=List[meeting_schemas.MeetingOut])
def read_meetings(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return meeting_crud.list_meetings(db=db, skip=skip, limit=limit)


@router.get("/{meeting_id}", response_model=meeting_schemas.MeetingOut)
def read_meeting(meeting_id: int, db: Session = Depends(get_db)):
    db_obj = meeting_crud.get_meeting(db=db, meeting_id=meeting_id)
    if not db_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meeting not found")
    return db_obj


@router.put("/{meeting_id}", response_model=meeting_schemas.MeetingOut)
def update_meeting(meeting_id: int, updates: meeting_schemas.MeetingUpdate, db: Session = Depends(get_db)):
    db_obj = meeting_crud.get_meeting(db=db, meeting_id=meeting_id)
    if not db_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meeting not found")

    new_start = updates.start_time if updates.start_time is not None else db_obj.start_time
    new_end = updates.end_time if updates.end_time is not None else db_obj.end_time

    if new_end <= new_start:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="end_time must be after start_time"
        )

    if updates.room_id is not None:
        room = db.execute(
            text("SELECT 1 FROM meeting_rooms WHERE id = :id"), 
            {"id": updates.room_id}
        ).first()
        if room is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="room_id not found"
            )

    updated = meeting_crud.update_meeting(db=db, db_obj=db_obj, updates=updates)
    return updated


@router.delete("/{meeting_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_meeting(meeting_id: int, db: Session = Depends(get_db)):
    db_obj = meeting_crud.get_meeting(db=db, meeting_id=meeting_id)
    if not db_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meeting not found")
    meeting_crud.delete_meeting(db=db, db_obj=db_obj)
    return None