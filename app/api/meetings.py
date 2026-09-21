from datetime import date
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app import models
from app.crud import meeting as meeting_crud
from app.db.session import get_db
from app.schemas import meeting as meeting_schemas
from app.utils.zoho_utils import send_meeting_webhook_notification

router = APIRouter(prefix="/meetings", tags=["meetings"])


@router.post("/", response_model=meeting_schemas.MeetingOut, status_code=status.HTTP_201_CREATED)
def create_meeting(
    meeting_in: meeting_schemas.MeetingCreate, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
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

    # Zoho Cliq Notification Trigger
    should_invite = getattr(meeting_in, "inviteCliq", False) or getattr(meeting_in, "invite_cliq", False)

    if should_invite:
        participants = getattr(meeting_in, "participants", []) or getattr(db_obj, "participants", [])
        
        meeting_date = getattr(db_obj, "meeting_date", "")
        start_time_val = getattr(db_obj, "start_time", "")
        time_str = f"{meeting_date} {start_time_val}".strip()

        background_tasks.add_task(
            send_meeting_webhook_notification,
            meeting_title=getattr(db_obj, "title", "Meeting"),
            start_time=time_str or str(start_time_val),
            participants=participants,
            meeting_room=getattr(db_obj, "room", getattr(db_obj, "meeting_room", "")),
            meeting_id=str(getattr(db_obj, "id", ""))
        )

    return db_obj


@router.get("/", response_model=List[meeting_schemas.MeetingOut])
def read_meetings(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    date: Optional[str] = Query(None, alias="date", description="Filter meetings by date (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    try:
        return meeting_crud.list_meetings(db=db, skip=skip, limit=limit, date=date)
    except TypeError:
        return meeting_crud.list_meetings(db=db, skip=skip, limit=limit)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch meetings: {str(exc)}"
        )


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
    new_date = updates.meeting_date if updates.meeting_date is not None else db_obj.meeting_date
    target_room_id = updates.room_id if updates.room_id is not None else db_obj.room_id

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

    # Room Conflict Check For Update Case
    if target_room_id is not None:
        has_conflict = meeting_crud.check_room_conflict(
            db=db,
            room_id=target_room_id,
            meeting_date=new_date,
            start_time=new_start,
            end_time=new_end,
            exclude_meeting_id=meeting_id
        )
        if has_conflict:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The selected room is already booked for this date and time range."
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