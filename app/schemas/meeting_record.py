from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, Field, constr, validator

from app.schemas.action_item import ActionItemStatus
from app.schemas.translation import ActionItemResult


class MeetingRecordCreate(BaseModel):
    meeting_id: int
    audio_url: constr(max_length=255)


class ActionItemExtracted(BaseModel):
    task: constr(max_length=255)
    owner_name: constr(max_length=255)
    due_date: Optional[date] = None
    status: ActionItemStatus = ActionItemStatus.to_do


class MeetingRecordUpdate(BaseModel):
    summary: Optional[str] = None
    transcript: Optional[str] = None
    notes: Optional[str] = None
    action_items: Optional[List[ActionItemExtracted]] = None


class MeetingRecordBase(BaseModel):
    audio_url: Optional[constr(max_length=255)] = None
    summary: Optional[str] = None
    transcript: Optional[str] = None
    notes: Optional[str] = None


class MeetingRecordOut(MeetingRecordBase):
    id: int
    meeting_id: int
    title: Optional[str] = None
    room_name: Optional[str] = None
    organizer_name: Optional[str] = None
    decisions: List[str] = Field(default_factory=list)
    action_items: List[ActionItemResult] = Field(default_factory=list)
    task_id: Optional[str] = None
    status: str = "idle"
    processing_error: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    @validator("decisions", pre=True, always=True)
    def none_decisions_as_empty_list(cls, value):
        return [] if value is None else value

    class Config:
        orm_mode = True
