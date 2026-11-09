from datetime import date, datetime, time, timezone
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app import models
from app.crud import meeting as meeting_crud
from app.core.security import get_current_user
from app.db.session import get_db
from app.models.booking_rule import BookingRule
from app.models.user import User
from app.schemas import meeting as meeting_schemas
from app.api.settings import DEFAULTS
# from app.utils.zoho_utils import send_meeting_webhook_notification
from app.utils.zoho_sync import send_zoho_notification

router = APIRouter(prefix="/meetings", tags=["meetings"])


def _booking_rule_values(db):
    rule = db.query(BookingRule).filter(BookingRule.id == 1).first()
    if rule is None:
        return DEFAULTS
    return {
        "approval_required": rule.approval_required,
        "work_start": rule.work_start,
        "work_end": rule.work_end,
        "notify_email": rule.notify_email,
        "notify_in_app": rule.notify_in_app,
        "notify_zoho_cliq": rule.notify_zoho_cliq,
        "approver_admin": rule.approver_admin,
        "approver_approver": rule.approver_approver,
    }


def _require_approver(db, current_user: User):
    rules = _booking_rule_values(db)
    allowed = (
        current_user.role == "admin" and rules["approver_admin"]
    ) or (
        current_user.role == "approver" and rules["approver_approver"]
    )
    if not allowed:
        raise HTTPException(status_code=403, detail="Approver access required")


def _enforce_working_hours(db, start_time, end_time):
    rule = db.query(BookingRule).filter(BookingRule.id == 1).first()
    work_start = rule.work_start if rule else time(9, 0)
    work_end = rule.work_end if rule else time(18, 0)
    if start_time < work_start or end_time > work_end:
        raise HTTPException(
            status_code=400,
            detail=f"Meetings can only be booked between "
                   f"{work_start.strftime('%H:%M')} and "
                   f"{work_end.strftime('%H:%M')}",
        )


@router.post("/", response_model=meeting_schemas.MeetingOut, status_code=status.HTTP_201_CREATED)
def create_meeting(
    meeting_in: meeting_schemas.MeetingCreate, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    meeting_in.created_by = current_user.id

    booking_rules = _booking_rule_values(db)
    approval_required = booking_rules["approval_required"]
    if approval_required:
        meeting_in.status = "pending"

    if meeting_in.end_time <= meeting_in.start_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="end_time must be after start_time"
        )

    _enforce_working_hours(db, meeting_in.start_time, meeting_in.end_time)

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
    db_obj = meeting_crud.create_meeting(db=db, meeting_in=meeting_in)

    # Zoho Cliq Notification Trigger
    should_invite = getattr(meeting_in, "inviteCliq", False) or getattr(meeting_in, "invite_cliq", False)

    if should_invite and not approval_required:
        participants = getattr(meeting_in, "participants", []) or getattr(db_obj, "participants", [])
        
        meeting_date = getattr(db_obj, "meeting_date", "")
        start_time_val = getattr(db_obj, "start_time", "")
        end_time_val = getattr(db_obj, "end_time", "")
        time_str = f"{meeting_date} {start_time_val}".strip()

        background_tasks.add_task(
            send_zoho_notification,
            meeting_title=getattr(db_obj, "title", "Meeting"),
            start_time=time_str or str(start_time_val),
            end_time=str(end_time_val),
            participants=participants,
            meeting_room=getattr(db_obj, "room", getattr(db_obj, "meeting_room", "")),
            meeting_id=str(getattr(db_obj, "id", ""))
        )

    return db_obj


@router.get("/pending-approvals", response_model=List[meeting_schemas.PendingApprovalOut])
def read_pending_approvals(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_approver(db, current_user)
    rows = (
        db.query(models.Meeting, User.name)
        .join(User, models.Meeting.created_by == User.id)
        .filter(models.Meeting.status == "pending")
        .order_by(models.Meeting.meeting_date, models.Meeting.start_time)
        .all()
    )
    return [
        {
            **meeting_schemas.MeetingOut.model_validate(meeting).model_dump(),
            "created_by_name": booker_name,
        }
        for meeting, booker_name in rows
    ]


@router.post("/{meeting_id}/approve", response_model=meeting_schemas.MeetingOut)
def approve_meeting(
    meeting_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_approver(db, current_user)
    db_obj = meeting_crud.get_meeting(db=db, meeting_id=meeting_id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Meeting not found")
    if db_obj.status != "pending":
        raise HTTPException(status_code=400, detail="This booking is not waiting for approval")

    if db_obj.room_id is not None and meeting_crud.check_room_conflict(
        db=db,
        room_id=db_obj.room_id,
        meeting_date=db_obj.meeting_date,
        start_time=db_obj.start_time,
        end_time=db_obj.end_time,
        exclude_meeting_id=meeting_id,
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The selected room is already booked for this date and time range.",
        )

    db_obj.status = "approved"
    db_obj.decided_by = current_user.id
    db_obj.decided_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(db_obj)

    if db_obj.invite_cliq:
        meeting_date = getattr(db_obj, "meeting_date", "")
        start_time_val = getattr(db_obj, "start_time", "")
        end_time_val = getattr(db_obj, "end_time", "")
        time_str = f"{meeting_date} {start_time_val}".strip()
        background_tasks.add_task(
            send_zoho_notification,
            meeting_title=getattr(db_obj, "title", "Meeting"),
            start_time=time_str or str(start_time_val),
            end_time=str(end_time_val),
            participants=getattr(db_obj, "participants", []),
            meeting_room=getattr(db_obj, "room", getattr(db_obj, "meeting_room", "")),
            meeting_id=str(getattr(db_obj, "id", "")),
        )
    return db_obj


@router.post("/{meeting_id}/reject", response_model=meeting_schemas.MeetingOut)
def reject_meeting(
    meeting_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_approver(db, current_user)
    db_obj = meeting_crud.get_meeting(db=db, meeting_id=meeting_id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Meeting not found")
    if db_obj.status != "pending":
        raise HTTPException(status_code=400, detail="This booking is not waiting for approval")
    db_obj.status = "rejected"
    db_obj.decided_by = current_user.id
    db_obj.decided_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(db_obj)
    return db_obj


@router.get("/", response_model=List[meeting_schemas.MeetingOut])
def read_meetings(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    date: Optional[date] = Query(None, alias="date", description="Filter meetings by date (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return meeting_crud.list_meetings(
            db=db, skip=skip, limit=limit, date_filter=date
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch meetings: {str(exc)}"
        )


@router.get("/{meeting_id}", response_model=meeting_schemas.MeetingOut)
def read_meeting(
    meeting_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db_obj = meeting_crud.get_meeting(db=db, meeting_id=meeting_id)
    if not db_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meeting not found")
    return db_obj


@router.put("/{meeting_id}", response_model=meeting_schemas.MeetingOut)
@router.patch("/{meeting_id}", response_model=meeting_schemas.MeetingOut)
def update_meeting(
    meeting_id: int,
    updates: meeting_schemas.MeetingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
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
def delete_meeting(
    meeting_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db_obj = meeting_crud.get_meeting(db=db, meeting_id=meeting_id)
    if not db_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meeting not found")
    meeting_crud.delete_meeting(db=db, db_obj=db_obj)
    return None
