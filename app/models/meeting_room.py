# app/models/meeting_room.py
from sqlalchemy import Column, BigInteger, String, Integer, DateTime, func, CheckConstraint
from sqlalchemy.dialects.postgresql import JSONB
from app.core.database import Base # သင့် project ၏ Base class နေရာလိုက်ပြောင်းပါ

class MeetingRoom(Base):
    __tablename__ = "meeting_rooms"

    id = Column(BigInteger, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    capacity = Column(Integer, nullable=False)
    status = Column(String(20), server_default="active", nullable=False)
    devices = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        CheckConstraint("status IN ('active', 'maintenance')", name="check_status_values"),
    )