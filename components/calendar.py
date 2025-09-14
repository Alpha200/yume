from dataclasses import dataclass
from typing import Optional


@dataclass
class CalendarEvent:
    """A single calendar event entry."""
    start: str
    end: str
    summary: str
    description: Optional[str] = None
    location: Optional[str] = None
