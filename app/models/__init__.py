# app/models/__init__.py
# models package

from app.core.database import Base

# Concrete models များကို တိုက်ရိုက် import လုပ်၍ Metadata ကို တိုင်ပင် သတ်မှတ်ခြင်း
from .meeting_room import MeetingRoom  # noqa: F401
from .user import User  # noqa: F401
from .meeting import Meeting  # noqa: F401

# အခြား Related Models များရှိပါက တိုက်ရိုက် import လုပ်ပါ
try:
    from .meeting_participant import MeetingParticipant  # noqa: F401
    from .meeting_record import MeetingRecord  # noqa: F401
    from .key_decision import KeyDecision  # noqa: F401
    from .action_item import ActionItem  # noqa: F401
except ImportError:
    pass

__all__ = ["Base", "User", "MeetingRoom", "Meeting"]