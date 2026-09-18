import enum

from sqlalchemy import BigInteger, Column, Date, Enum as SAEnum, ForeignKey, String, TIMESTAMP, func
from sqlalchemy.orm import backref, relationship

from app.core.database import Base


class ActionItemStatus(enum.Enum):
    to_do = "to_do"
    in_progress = "in_progress"
    complete = "complete"


class ActionItem(Base):
    __tablename__ = "action_items"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    meeting_id = Column(BigInteger, ForeignKey("meetings.id", ondelete="CASCADE"), nullable=False)
    task = Column(String(255), nullable=False)
    owner_name = Column(String(255), nullable=False)
    due_date = Column(Date, nullable=True)
    status = Column(SAEnum(ActionItemStatus, name="action_item_status"), nullable=False, default=ActionItemStatus.to_do)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    meeting = relationship(
        "Meeting",
        backref=backref("action_items", cascade="all, delete-orphan"),
        foreign_keys=[meeting_id],
    )
