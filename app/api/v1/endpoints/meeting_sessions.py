from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db.session import get_db

router = APIRouter(prefix="/meeting-sessions", tags=["meeting-sessions"])

@router.get("/", response_model=Dict[str, Any])
def get_all_meeting_sessions(db: Session = Depends(get_db)):
    """
    meetings table ထဲမှ meeting တစ်ခုချင်းစီ၏ status များကို ယူသုံးရန်
    """
    try:
        sessions_result = db.execute(text("SELECT id, status FROM meetings")).fetchall()
        
        sessions_dict = {}
        for row in sessions_result:
            sessions_dict[str(row.id)] = {
                "status": getattr(row, "status", "idle") or "idle"
            }
        return sessions_dict
    except Exception as exc:
        return {}


@router.post("/{meeting_id}/status", status_code=status.HTTP_200_OK)
def update_meeting_session_status(
    meeting_id: str, 
    payload: dict, 
    db: Session = Depends(get_db)
):
    """
    meetings table ထဲရှိ သက်ဆိုင်ရာ meeting ၏ status ကို Update လုပ်ရန်
    """
    new_status = payload.get("status")
    if new_status not in ["running", "stopped", "idle"]:
        raise HTTPException(status_code=400, detail="Invalid status value")
    
    try:
        db.execute(
            text("UPDATE meetings SET status = :status WHERE id = :meeting_id"),
            {"meeting_id": meeting_id, "status": new_status}
        )
        db.commit()
        return {"message": "Meeting status updated successfully", "meeting_id": meeting_id, "status": new_status}
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update meeting status: {str(exc)}")