from pydantic import BaseModel, constr, EmailStr
from datetime import datetime
from typing import Optional


class MeetingParticipantBase(BaseModel):
    zoho_user_id: Optional[constr(max_length=255)] = None
    name: Optional[constr(max_length=255)] = None
    email: EmailStr
    meeting_id: int


class MeetingParticipantCreate(MeetingParticipantBase):
    pass


class MeetingParticipantOut(MeetingParticipantBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True