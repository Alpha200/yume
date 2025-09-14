from agents import function_tool
from services.memory_manager import (
    ReminderOptions, memory_manager
)
from typing import Optional, List
import datetime
from components.timezone_utils import from_isoformat_user_tz, to_user_tz, now_user_tz

@function_tool
def get_memory() -> str:
    """Get all stored memories as a formatted string"""
    return memory_manager.get_formatted_memories()

@function_tool
def upsert_user_preference(content: str, memory_id: Optional[str] = None, place: Optional[str] = None) -> str:
    """Create a new user preference or update an existing one by ID"""
    result_id = memory_manager.create_user_preference(
        content=content,
        memory_id=memory_id,
        place=place
    )
    action = "updated" if memory_id else "created"
    return f"User preference {action} with ID: {result_id}"

@function_tool
def upsert_user_observation(content: str, observation_date: str, memory_id: Optional[str] = None, place: Optional[str] = None) -> str:
    """Create a new user observation or update an existing one by ID with an observation date (format: YYYY-MM-DD HH:MM:SS or YYYY-MM-DD)"""
    try:
        # Try to parse with time first, then date only
        try:
            obs_date = from_isoformat_user_tz(observation_date)
        except ValueError:
            # If that fails, try date only and set time to current time
            date_part = datetime.datetime.strptime(observation_date, '%Y-%m-%d').date()
            obs_date = datetime.datetime.combine(date_part, now_user_tz().time())
            obs_date = to_user_tz(obs_date)

        result_id = memory_manager.create_user_observation(
            content=content,
            observation_date=obs_date,
            memory_id=memory_id,
            place=place
        )
        action = "updated" if memory_id else "created"
        return f"User observation {action} with ID: {result_id}"
    except ValueError as e:
        return f"Error parsing observation date '{observation_date}': {e}. Please use format YYYY-MM-DD or YYYY-MM-DD HH:MM:SS"

@function_tool
def upsert_reminder(content: str, reminder_datetime: Optional[str] = None, reminder_time: Optional[str] = None, days_of_week: Optional[List[str]] = None, memory_id: Optional[str] = None, place: Optional[str] = None) -> str:
    """Create a new reminder or update an existing one by ID. For one-time reminders use reminder_datetime (YYYY-MM-DD HH:MM:SS). For recurring reminders use reminder_time (HH:MM) and days_of_week (list of weekday names)"""
    try:
        reminder_options = ReminderOptions()

        if reminder_datetime:
            reminder_options.datetime_value = from_isoformat_user_tz(reminder_datetime)

        if reminder_time:
            reminder_options.time_value = reminder_time

        if days_of_week:
            reminder_options.days_of_week = days_of_week

        # Validate that we have either datetime or time+days
        if not reminder_options.datetime_value and not (reminder_options.time_value and reminder_options.days_of_week):
            return "Error: Either provide reminder_datetime for one-time reminders, or both reminder_time and days_of_week for recurring reminders"

        result_id = memory_manager.create_reminder(
            content=content,
            reminder_options=reminder_options,
            memory_id=memory_id,
            place=place
        )
        action = "updated" if memory_id else "created"
        return f"Reminder {action} with ID: {result_id}"
    except ValueError as e:
        return f"Error creating/updating reminder: {e}"

@function_tool
def delete_memory(memory_id: str) -> str:
    """Delete a memory by its ID"""
    success = memory_manager.delete_memory(memory_id)
    if success:
        return f"Memory with ID {memory_id} has been deleted."
    else:
        return f"Memory with ID {memory_id} not found."
