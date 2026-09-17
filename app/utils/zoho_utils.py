import re
from typing import Tuple, Optional


def split_name_and_position(full_name: Optional[str]) -> Tuple[str, Optional[str]]:
    """Split a display name that may include a trailing ' - position' or similar separator.

    Returns a tuple (name, position) where position is None if not found.
    Separators considered: hyphen variants, pipe, slash. Splitting is limited to the first separator.
    """
    if not full_name:
        return "", None

    raw = full_name.strip()
    # Split on common separators with optional surrounding whitespace
    parts = re.split(r"\s*[-–—|/]\s*", raw, maxsplit=1)
    if len(parts) >= 2:
        name = parts[0].strip()
        position = parts[1].strip()
        return name, position

    return raw, None
