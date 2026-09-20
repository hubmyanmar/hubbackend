from pydantic import BaseModel, EmailStr, field_validator
from datetime import date, time
from typing import Optional, List, Dict, Any

class MeetingParticipantSchema(BaseModel):
    zoho_user_id: str
    name: Optional[str] = None
    email: EmailStr

class MeetingBase(BaseModel):
    title: str
    agenda: Optional[str] = None
    meeting_date: date
    start_time: time
    end_time: time
    meeting_type: str
    platform: Optional[str] = None
    meeting_link: Optional[str] = None
    room_id: Optional[int] = None
    company_name: str

    @field_validator('meeting_type', mode='before')
    def normalize_meeting_type(cls, v: str) -> str:
        if isinstance(v, str):
            return v.strip().lower()
        return v

class MeetingCreate(MeetingBase):
    created_by: Optional[int] = None
    participant_emails: Optional[List[str]] = []
    participants: Optional[List[MeetingParticipantSchema]] = []

class MeetingUpdate(BaseModel):
    title: Optional[str] = None
    agenda: Optional[str] = None
    meeting_date: Optional[date] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    meeting_type: Optional[str] = None
    platform: Optional[str] = None
    meeting_link: Optional[str] = None
    room_id: Optional[int] = None
    company_name: Optional[str] = None
    participant_emails: Optional[List[str]] = None
    participants: Optional[List[Dict[str, Any]]] = None

class MeetingOut(MeetingBase):
    id: int
    created_by: int

    class Config:
        from_attributes = True