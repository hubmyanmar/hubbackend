# app/models/__init__.py
# models package

from app.core.database import Base

# Import every mapped model so Base.metadata.create_all sees the full schema.
from .meeting_room import MeetingRoom  # noqa: F401
from .user import User  # noqa: F401
from .meeting import Meeting  # noqa: F401
from .meeting_participant import MeetingParticipant  # noqa: F401
from .meeting_record import MeetingRecord  # noqa: F401
from .action_item import ActionItem  # noqa: F401

__all__ = [
    "Base", "User", "MeetingRoom", "Meeting", "MeetingParticipant",
    "MeetingRecord", "ActionItem",
]
