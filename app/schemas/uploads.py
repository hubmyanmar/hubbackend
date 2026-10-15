from typing import List, Optional

from pydantic import BaseModel, Field, constr, validator

from app.schemas.translation import ActionItemResult


class MultipartInitiateRequest(BaseModel):
    meeting_id: int = Field(..., gt=0)
    filename: constr(min_length=1, max_length=255)
    content_type: constr(min_length=1, max_length=255) = "audio/mpeg"


class MultipartInitiateResponse(BaseModel):
    meeting_id: int
    object_key: str
    upload_id: str


class MultipartPresignRequest(BaseModel):
    meeting_id: int = Field(..., gt=0)
    object_key: str
    upload_id: str
    part_number: int = Field(..., alias="partNumber", ge=1, le=10000)

    class Config:
        allow_population_by_field_name = True


class MultipartPresignResponse(BaseModel):
    url: str
    part_number: int = Field(..., alias="partNumber")
    expires_in: int

    class Config:
        allow_population_by_field_name = True


class MultipartGetPresignResponse(BaseModel):
    url: str
    expires_in: int


class MultipartPart(BaseModel):
    etag: constr(min_length=1) = Field(..., alias="ETag")
    part_number: int = Field(..., alias="PartNumber", ge=1, le=10000)

    class Config:
        allow_population_by_field_name = True


class MultipartCompleteRequest(BaseModel):
    meeting_id: int = Field(..., gt=0)
    object_key: str
    upload_id: str
    parts: List[MultipartPart] = Field(..., min_items=1)


class MultipartCompleteResponse(BaseModel):
    meeting_id: int
    object_key: str
    audio_url: str
    summary: Optional[str] = None
    transcript: Optional[str] = None
    decisions: List[str] = Field(default_factory=list)
    action_items: List[ActionItemResult] = Field(default_factory=list)
    task_id: Optional[str] = None
    status: str = "idle"
    message: str = "Multipart upload completed"

    @validator("decisions", pre=True, always=True)
    def none_decisions_as_empty_list(cls, value):
        return [] if value is None else value


class MeetingUploadResponse(BaseModel):
    meeting_id: int
    audio_url: Optional[str] = None
    summary: Optional[str] = None
    transcript: Optional[str] = None
    decisions: List[str] = Field(default_factory=list)
    action_items: List[ActionItemResult] = Field(default_factory=list)
    task_id: Optional[str] = None
    status: str = "idle"

    @validator("decisions", pre=True, always=True)
    def none_decisions_as_empty_list(cls, value):
        return [] if value is None else value


class MultipartAbortRequest(BaseModel):
    meeting_id: int = Field(..., gt=0)
    object_key: str
    upload_id: str


class MultipartAbortResponse(BaseModel):
    message: str = "Multipart upload aborted"
