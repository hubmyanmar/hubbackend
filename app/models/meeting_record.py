from sqlalchemy import BigInteger, Column, ForeignKey, JSON, String, Text, TIMESTAMP, func
from sqlalchemy.orm import backref, relationship

from app.core.database import Base


class MeetingRecord(Base):
    __tablename__ = "meeting_records"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    meeting_id = Column(BigInteger, ForeignKey("meetings.id", ondelete="CASCADE"), unique=True, nullable=False)
    audio_url = Column(String(255), nullable=True)
    audio_object_key = Column(String(1024), nullable=True)
    ai_summary_en = Column(Text, nullable=True)
    ai_summary_my = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    transcript = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    decisions = Column(JSON, nullable=False, default=list)
    task_id = Column(String(36), nullable=True, index=True)
    status = Column(String(16), nullable=False, default="idle", server_default="idle")
    processing_error = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    meeting = relationship(
        "Meeting",
        backref=backref("record", uselist=False, cascade="all, delete-orphan"),
        foreign_keys=[meeting_id],
    )

    # Flattened display fields exposed by the meeting-record API.
    @property
    def title(self):
        return self.meeting.title if self.meeting else None

    @property
    def room_name(self):
        return self.meeting.room.name if self.meeting and self.meeting.room else None

    @property
    def organizer_name(self):
        return self.meeting.creator.name if self.meeting and self.meeting.creator else None

    @property
    def action_items(self):
        if not self.meeting:
            return []
        return [
            {
                "task": item.task,
                "assignee": item.owner_name,
                "deadline": item.due_date.isoformat() if item.due_date else None,
            }
            for item in self.meeting.action_items
        ]

