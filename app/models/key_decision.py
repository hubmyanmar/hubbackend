from sqlalchemy import BigInteger, Column, ForeignKey, Text, TIMESTAMP, func
from sqlalchemy.orm import backref, relationship

from app.core.database import Base


class KeyDecision(Base):
    __tablename__ = "key_decisions"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    meeting_id = Column(BigInteger, ForeignKey("meetings.id", ondelete="CASCADE"), nullable=False)
    decision_text = Column(Text, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)

    meeting = relationship(
        "Meeting",
        backref=backref("key_decisions", cascade="all, delete-orphan"),
        foreign_keys=[meeting_id],
    )
