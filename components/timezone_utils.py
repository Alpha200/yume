import datetime
import os
import zoneinfo

# Get user timezone from environment variable, default to Europe/Berlin
USER_TIMEZONE = os.getenv("USER_TIMEZONE", "Europe/Berlin")
USER_TZ = zoneinfo.ZoneInfo(USER_TIMEZONE)

def now_user_tz() -> datetime.datetime:
    """Get current datetime in user's timezone"""
    return datetime.datetime.now(USER_TZ)

def to_user_tz(dt: datetime.datetime) -> datetime.datetime:
    """Convert datetime to user's timezone"""
    return dt.replace(tzinfo=USER_TZ)

def from_isoformat_user_tz(iso_string: str) -> datetime.datetime:
    """Parse ISO format string and ensure it's in user's timezone"""
    dt = datetime.datetime.fromisoformat(iso_string)
    return to_user_tz(dt)