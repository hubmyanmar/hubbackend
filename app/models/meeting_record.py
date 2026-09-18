from sqlalchemy import BigInteger, Column, ForeignKey, String, Text, TIMESTAMP, func
from sqlalchemy.orm import backref, relationship

from app.core.database import Base


class MeetingRecord(Base):
    __tablename__ = "meeting_records"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    meeting_id = Column(BigInteger, ForeignKey("meetings.id", ondelete="CASCADE"), unique=True, nullable=False)
    audio_url = Column(String(255), nullable=True)
    ai_summary_en = Column(Text, nullable=True)
    ai_summary_my = Column(Text, nullable=True)
    transcript = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    meeting = relationship(
        "Meeting",
        backref=backref("record", uselist=False, cascade="all, delete-orphan"),
        foreign_keys=[meeting_id],
    )
