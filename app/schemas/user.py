from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    position: Optional[str] = Field(default=None, max_length=100)
    image: Optional[str] = None

    # ⚠️ မှားနေပုံ ( `:` သုံးထားခြင်း )
    # model_config: ConfigDict(from_attributes=True)

    # ✅ မှန်ကန်သောပုံ ( `=` ကို သုံးရပါမည် )
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
    created_at: datetime
    updated_at: datetime

    # ⚠️ ဤနေရာတွင်လည်း `:` ကို `=` သို့ ပြောင်းပေးပါ
    model_config = ConfigDict(from_attributes=True)