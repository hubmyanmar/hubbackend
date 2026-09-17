# models package
from .meeting_room import MeetingRoom  # existing import

# Add Meeting model export
try:
    from .meeting import Meeting  # noqa: F401
except Exception:
    # Meeting model will be available once created
    pass

try:
    from .meeting_record import MeetingRecord  # noqa: F401
except Exception:
    # MeetingRecord model will be available once created
    pass

try:
    from .key_decision import KeyDecision  # noqa: F401
except Exception:
    # KeyDecision model will be available once created
    pass

try:
    from .action_item import ActionItem  # noqa: F401
except Exception:
    # ActionItem model will be available once created
    pass
