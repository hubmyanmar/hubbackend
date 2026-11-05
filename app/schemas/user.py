from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    position: Optional[str] = Field(default=None, max_length=100)
    image: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class UserCreate(UserBase):
    password: Optional[str] = Field(default=None, max_length=255)


class UserUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(default=None, max_length=255)
    position: Optional[str] = Field(default=None, max_length=100)
    image: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class UserOut(UserBase):
    id: int
    role: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class RoleUpdate(BaseModel):
    role: Literal["admin", "approver", "member"]


class ActiveUpdate(BaseModel):
    is_active: bool