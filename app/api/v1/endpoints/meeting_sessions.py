# app/api/v1/endpoints/meeting_sessions.py
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime
from app.db.session import get_db

router = APIRouter(prefix="/meeting-sessions", tags=["meeting-sessions"])

@router.get("/", response_model=Dict[str, Any])
def get_all_meeting_sessions(db: Session = Depends(get_db)):
    try:
        sessions_result = db.execute(
            text("SELECT id, status, actual_started_at, actual_ended_at, actual_duration FROM meetings")
        ).fetchall()
        
        sessions_dict = {}
        for row in sessions_result:
            sessions_dict[str(row.id)] = {
                "status": getattr(row, "status", "idle") or "idle",
                "actual_started_at": str(getattr(row, "actual_started_at", "")) if getattr(row, "actual_started_at", None) else None,
                "actual_ended_at": str(getattr(row, "actual_ended_at", "")) if getattr(row, "actual_ended_at", None) else None,
                "actual_duration": getattr(row, "actual_duration", 0) or 0
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
    
    now = datetime.now()
    
    try:
        existing = db.execute(
            text("SELECT id, actual_started_at FROM meetings WHERE id = :meeting_id OR CAST(id AS CHAR) = :meeting_id_str"),
            {"meeting_id": meeting_id, "meeting_id_str": str(meeting_id)}
        ).fetchone()

        if not existing:
            db.execute(
                text("INSERT INTO meetings (id, status, actual_started_at) VALUES (:meeting_id, :status, :now) ON DUPLICATE KEY UPDATE status = :status"),
                {"meeting_id": meeting_id, "status": new_status, "now": now}
            )
            db.commit()
            return {"message": "Meeting created and status updated", "meeting_id": meeting_id, "status": new_status}

        if new_status == "running":
            db.execute(
                text("UPDATE meetings SET status = :status, actual_started_at = :now WHERE id = :meeting_id OR CAST(id AS CHAR) = :meeting_id_str"),
                {"status": new_status, "now": now, "meeting_id": meeting_id, "meeting_id_str": str(meeting_id)}
            )
        elif new_status == "stopped":
            start_dt = existing.actual_started_at
            actual_duration = 0
            if start_dt:
                if start_dt.tzinfo is not None:
                    start_dt = start_dt.replace(tzinfo=None)
                
                if now.tzinfo is not None:
                    now = now.replace(tzinfo=None)

                diff = now - start_dt
                actual_duration = round(diff.total_seconds() / 60, 2)

            db.execute(
                text("""
                    UPDATE meetings 
                    SET status = :status, 
                        actual_ended_at = :now, 
                        actual_duration = :actual_duration 
                    WHERE id = :meeting_id OR CAST(id AS CHAR) = :meeting_id_str
                """),
                {
                    "status": new_status, 
                    "now": now, 
                    "actual_duration": actual_duration, 
                    "meeting_id": meeting_id, 
                    "meeting_id_str": str(meeting_id)
                }
            )
        else:
            db.execute(
                text("UPDATE meetings SET status = :status WHERE id = :meeting_id OR CAST(id AS CHAR) = :meeting_id_str"),
                {"meeting_id": meeting_id, "meeting_id_str": str(meeting_id), "status": new_status}
            )

        db.commit()
        return {"message": "Meeting status updated successfully", "meeting_id": meeting_id, "status": new_status}
    except Exception as exc:
        db.rollback()
        print(f"❌ Failed to update status for ID {meeting_id}: {str(exc)}")
        raise HTTPException(status_code=500, detail=f"Failed to update meeting status: {str(exc)}")