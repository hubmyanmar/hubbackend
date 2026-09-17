import enum
from sqlalchemy import (
    Column,
    BigInteger,
    String,
    Text,
    Date,
    Time,
    Enum as SAEnum,
    ForeignKey,
    TIMESTAMP,
    func,
)
from sqlalchemy.orm import relationship
from app.db.session import Base


class MeetingType(enum.Enum):
    online = "online"
    face_to_face = "face to face"


class Meeting(Base):
    __tablename__ = "meetings"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    agenda = Column(Text, nullable=True)
    meeting_date = Column(Date, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    meeting_type = Column(SAEnum(MeetingType, name="meeting_type_enum"), nullable=False)
    platform = Column(String(100), nullable=True)
    meeting_link = Column(String(255), nullable=True)
    room_id = Column(BigInteger, ForeignKey("meeting_rooms.id", ondelete="SET NULL"), nullable=True)
    company_name = Column(String(255), nullable=False)
    created_by = Column(BigInteger, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)

    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Optional relationship placeholders — rely on existing meeting_rooms and users models
    room = relationship("MeetingRoom", back_populates="meetings", passive_deletes=True, foreign_keys=[room_id])
    creator = relationship("User", back_populates="meetings_created", foreign_keys=[created_by])
