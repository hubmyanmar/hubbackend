from pydantic import BaseModel, constr, Field
from datetime import date, time, datetime
from typing import Optional


class MeetingBase(BaseModel):
    title: constr(max_length=255)
    agenda: Optional[str] = None
    meeting_date: date
    start_time: time
    end_time: time
    meeting_type: constr(max_length=32)
    platform: Optional[constr(max_length=100)] = None
    meeting_link: Optional[constr(max_length=255)] = None
    room_id: Optional[int] = None
    company_name: constr(max_length=255)


class MeetingCreate(MeetingBase):
    created_by: int


class MeetingUpdate(BaseModel):
    title: Optional[constr(max_length=255)] = None
    agenda: Optional[str] = None
    meeting_date: Optional[date] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    meeting_type: Optional[constr(max_length=32)] = None
    platform: Optional[constr(max_length=100)] = None
    meeting_link: Optional[constr(max_length=255)] = None
    room_id: Optional[int] = None
    company_name: Optional[constr(max_length=255)] = None


class MeetingOut(MeetingBase):
    id: int
    created_by: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
