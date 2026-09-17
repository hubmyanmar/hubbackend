from datetime import date, datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, constr


class ActionItemStatus(str, Enum):
    to_do = "to_do"
    in_progress = "in_progress"
    complete = "complete"


class ActionItemBase(BaseModel):
    task: constr(max_length=255)
    owner_name: constr(max_length=255)
    due_date: Optional[date] = None
    status: ActionItemStatus = ActionItemStatus.to_do


class ActionItemCreate(ActionItemBase):
    meeting_id: int


class ActionItemUpdate(BaseModel):
    task: Optional[constr(max_length=255)] = None
    owner_name: Optional[constr(max_length=255)] = None
    due_date: Optional[date] = None
    status: Optional[ActionItemStatus] = None


class ActionItemOut(ActionItemBase):
    id: int
    meeting_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
