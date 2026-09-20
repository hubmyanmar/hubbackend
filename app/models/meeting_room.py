from sqlalchemy import JSON, CheckConstraint, Column, DateTime, Integer, String, func
from sqlalchemy.orm import relationship

from app.core.database import Base


class MeetingRoom(Base):
    __tablename__ = "meeting_rooms"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    name = Column(String(100), nullable=False)
    capacity = Column(Integer, nullable=False)
    status = Column(String(20), server_default="active", nullable=False)
    devices = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    meetings = relationship("Meeting", back_populates="room", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("status IN ('active', 'maintenance')", name="check_status_values"),
    )