from sqlalchemy import Column, BigInteger, String, TIMESTAMP, ForeignKey, func
from sqlalchemy.orm import relationship, backref
from app.db.session import Base


class MeetingParticipant(Base):
    __tablename__ = "meeting_participants"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    meeting_id = Column(BigInteger, ForeignKey("meetings.id", ondelete="CASCADE"), nullable=False)
    zoho_user_id = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)

    meeting = relationship("Meeting", backref=backref("participants", cascade="all, delete-orphan"), foreign_keys=[meeting_id])
