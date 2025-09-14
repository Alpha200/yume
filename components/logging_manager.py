from collections import deque
import datetime
from typing import List, Dict, Any
from dataclasses import dataclass
from components.timezone_utils import now_user_tz


@dataclass
class LogEntry:
    message: str
    timestamp: datetime.datetime
    level: str = "INFO"

class LoggingManager:
    """
    A logging manager that wraps the standard logger and keeps track of the
    100 latest logged actions for monitoring and debugging purposes.
    """

    def __init__(self, max_entries: int = 100):
        self.max_entries = max_entries
        self._log_history = deque(maxlen=max_entries)

    def _add_to_history(self, message: str, **kwargs):
        """Add a log entry to the history."""
        entry = LogEntry(
            message=message,
            timestamp=now_user_tz(),
            level="INFO",
        )
        self._log_history.append(entry)

    def log(self, message: str, level: str = "INFO"):
        """Add a log entry with current timestamp"""
        entry = LogEntry(
            message=message,
            level=level,
            timestamp=now_user_tz(),
        )
        self._log_history.append(entry)

        # Also print to console for immediate visibility
        print(f"{now_user_tz().isoformat(timespec='milliseconds')} - {message}")

    def get_recent_logs(self, count: int = None) -> List[LogEntry]:
        """Get the most recent log entries."""
        if count is None:
            return list(self._log_history)
        return list(self._log_history)[-count:]

    def clear_history(self):
        """Clear the log history."""
        self._log_history.clear()

logging_manager = LoggingManager()
