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

def convert_utc_to_user_tz(dt_utc: datetime.datetime) -> datetime.datetime:
    """Convert a UTC datetime to user's timezone.

    Properly converts UTC (or other timezone-aware) datetimes to the user's timezone
    by adjusting the time values using astimezone().

    Args:
        dt_utc: UTC or timezone-aware datetime object

    Returns:
        datetime object in user's timezone with adjusted time values
    """
    return dt_utc.astimezone(USER_TZ)

def from_isoformat_user_tz(iso_string: str) -> datetime.datetime:
    """Parse ISO format string and ensure it's in user's timezone"""
    dt = datetime.datetime.fromisoformat(iso_string)
    return to_user_tz(dt)
