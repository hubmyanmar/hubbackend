from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=255)
    position: Optional[str] = Field(default=None, max_length=100)
    image: Optional[str] = Field(default=None, max_length=255)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=255)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
