# app/api/v1/endpoints/meeting_sessions.py
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db.session import get_db

router = APIRouter(prefix="/meeting-sessions", tags=["meeting-sessions"])

@router.get("/", response_model=Dict[str, Any])
def get_all_meeting_sessions(db: Session = Depends(get_db)):
    try:
        sessions_result = db.execute(
            text("SELECT id, status FROM meetings")
        ).fetchall()
        
        sessions_dict = {}
        for row in sessions_result:
            sessions_dict[str(row.id)] = {
                "status": getattr(row, "status", "idle") or "idle",
                "actual_started_at": None,
                "actual_ended_at": None,
                "actual_duration": 0
            }
        return sessions_dict
    except Exception as exc:
        print(f"❌ Database Error: {exc}")
        return {"error": str(exc)}


@router.post("/{meeting_id}/status", status_code=status.HTTP_200_OK)
def update_meeting_session_status(
    meeting_id: str, 
    payload: dict, 
    db: Session = Depends(get_db)
):
    new_status = payload.get("status")
    if new_status not in ["running", "stopped", "idle"]:
        raise HTTPException(status_code=400, detail="Invalid status value")
    
    try:
        existing = db.execute(
            text("SELECT id FROM meetings WHERE id = :meeting_id"),
            {"meeting_id": int(meeting_id)}
        ).fetchone()
    except Exception as exc:
        db.rollback()
        print(f"❌ Failed to update status for ID {meeting_id}: {str(exc)}")
        raise HTTPException(status_code=500, detail=f"Failed to update meeting status: {str(exc)}")

    if not existing:
        raise HTTPException(status_code=404, detail="Meeting not found")

    try:
        db.execute(
            text("UPDATE meetings SET status = :status WHERE id = :meeting_id"),
            {"meeting_id": int(meeting_id), "status": new_status}
        )

        db.commit()
        return {"message": "Meeting status updated successfully", "meeting_id": meeting_id, "status": new_status}
    except Exception as exc:
        db.rollback()
        print(f"❌ Failed to update status for ID {meeting_id}: {str(exc)}")
        raise HTTPException(status_code=500, detail=f"Failed to update meeting status: {str(exc)}")