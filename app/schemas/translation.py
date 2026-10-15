from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class TranslationRequest(BaseModel):
    meeting_id: int = Field(..., gt=0)
    audio_url: Optional[str] = None


class ActionItemResult(BaseModel):
    task: str
    assignee: Optional[str] = None
    deadline: Optional[str] = None


class TranslationAccepted(BaseModel):
    task_id: str
    meeting_id: int
    status: Literal["processing"]


class ProcessingStatusResponse(BaseModel):
    task_id: Optional[str] = None
    meeting_id: int
    status: Literal["idle", "processing", "completed", "failed"]
    error: Optional[str] = None
