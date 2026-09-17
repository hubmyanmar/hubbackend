# app/schemas/meeting_room.py
from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime

class MeetingRoomBase(BaseModel):
    name: str
    capacity: int
    status: Optional[str] = "active"
    devices: Optional[List[Any]] = None

class MeetingRoomCreate(MeetingRoomBase):
    pass

class MeetingRoomResponse(MeetingRoomBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class MeetingRoomUpdate(BaseModel):
    name: Optional[str] = None
    capacity: Optional[int] = None
    status: Optional[str] = None
    devices: Optional[List[Any]] = None