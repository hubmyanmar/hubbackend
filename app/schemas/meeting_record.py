from datetime import datetime
from typing import Optional

from pydantic import BaseModel, constr


class MeetingRecordBase(BaseModel):
    audio_url: Optional[constr(max_length=255)] = None
    ai_summary_en: Optional[str] = None
    ai_summary_my: Optional[str] = None
    transcript: Optional[str] = None
    notes: Optional[str] = None


class MeetingRecordCreate(MeetingRecordBase):
    meeting_id: int


class MeetingRecordUpdate(BaseModel):
    audio_url: Optional[constr(max_length=255)] = None
    ai_summary_en: Optional[str] = None
    ai_summary_my: Optional[str] = None
    transcript: Optional[str] = None
    notes: Optional[str] = None


class MeetingRecordOut(MeetingRecordBase):
    id: int
    meeting_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
