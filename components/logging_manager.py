from collections import deque
import datetime
from typing import List, Dict, Any
from dataclasses import dataclass


@dataclass
class LogEntry:
    timestamp: datetime.datetime
    message: str
    extra_data: Dict[str, Any] = None

    def __post_init__(self):
        if self.extra_data is None:
            self.extra_data = {}

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
            timestamp=datetime.datetime.now(datetime.UTC),
            message=message,
            extra_data=kwargs
        )
        self._log_history.append(entry)

    def log(self, message: str):
        """Log an info message."""
        print(f"{datetime.datetime.now(datetime.UTC).isoformat(timespec="milliseconds")} - {message}")
        self._add_to_history(message)

    def get_recent_logs(self, count: int = None) -> List[LogEntry]:
        """Get the most recent log entries."""
        if count is None:
            return list(self._log_history)
        return list(self._log_history)[-count:]

    def clear_history(self):
        """Clear the log history."""
        self._log_history.clear()

logging_manager = LoggingManager()
