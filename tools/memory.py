from agents import function_tool
from services.memory_manager import (
    get_memory_manager,
    ReminderOptions,
    UserObservationEntry,
    ReminderEntry
)
from typing import Optional, List
import datetime

memory_manager = get_memory_manager()

@function_tool
def get_memory() -> str:
    """Get all stored memories as a formatted string"""
    memories = memory_manager.get_all_memories()

    if not memories:
        return "No memories stored."

    memory_list = []
    for memory_id, entry in memories.items():
        memory_info = f"ID: {memory_id}\n"
        memory_info += f"Type: {entry.type}\n"
        memory_info += f"Content: {entry.content}\n"
        if entry.place:
            memory_info += f"Place: {entry.place}\n"
        memory_info += f"Created: {entry.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
        memory_info += f"Modified: {entry.modified_at.strftime('%Y-%m-%d %H:%M:%S')}\n"

        # Add observation date for user_observation entries
        if isinstance(entry, UserObservationEntry):
            memory_info += f"Observation Date: {entry.observation_date.strftime('%Y-%m-%d %H:%M:%S')}\n"

        # Add reminder options for reminder entries
        elif isinstance(entry, ReminderEntry):
            memory_info += "Reminder Options:\n"
            if entry.reminder_options.datetime_value:
                memory_info += f"  One-time reminder: {entry.reminder_options.datetime_value.strftime('%Y-%m-%d %H:%M:%S')}\n"
            if entry.reminder_options.time_value:
                memory_info += f"  Recurring time: {entry.reminder_options.time_value}\n"
            if entry.reminder_options.days_of_week:
                memory_info += f"  Days of week: {', '.join(entry.reminder_options.days_of_week)}\n"

        memory_list.append(memory_info.rstrip())

    return "\n\n".join(memory_list)

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
            obs_date = datetime.datetime.fromisoformat(observation_date)
        except ValueError:
            # If that fails, try date only and set time to current time
            date_part = datetime.datetime.strptime(observation_date, '%Y-%m-%d').date()
            obs_date = datetime.datetime.combine(date_part, datetime.datetime.now().time())
            obs_date = obs_date.replace(tzinfo=datetime.timezone.utc)

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
            reminder_options.datetime_value = datetime.datetime.fromisoformat(reminder_datetime)

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

@function_tool
def search_memories(search_term: str) -> str:
    """Search for memories containing the given term"""
    memories = memory_manager.get_all_memories()
    matching_memories = []

    for memory_id, entry in memories.items():
        if search_term.lower() in entry.content.lower():
            memory_info = f"ID: {memory_id}\n"
            memory_info += f"Type: {entry.type}\n"
            memory_info += f"Content: {entry.content}\n"
            if entry.place:
                memory_info += f"Place: {entry.place}\n"
            memory_info += f"Created: {entry.created_at.strftime('%Y-%m-%d %H:%M:%S')}"

            # Add observation date for user_observation entries
            if isinstance(entry, UserObservationEntry):
                memory_info += f"\nObservation Date: {entry.observation_date.strftime('%Y-%m-%d %H:%M:%S')}"

            # Add reminder options for reminder entries
            elif isinstance(entry, ReminderEntry):
                memory_info += "\nReminder Options:"
                if entry.reminder_options.datetime_value:
                    memory_info += f"\n  One-time reminder: {entry.reminder_options.datetime_value.strftime('%Y-%m-%d %H:%M:%S')}"
                if entry.reminder_options.time_value:
                    memory_info += f"\n  Recurring time: {entry.reminder_options.time_value}"
                if entry.reminder_options.days_of_week:
                    memory_info += f"\n  Days of week: {', '.join(entry.reminder_options.days_of_week)}"

            matching_memories.append(memory_info)

    if not matching_memories:
        return f"No memories found containing '{search_term}'."

    return f"Found {len(matching_memories)} memory(ies) containing '{search_term}':\n\n" + "\n\n".join(matching_memories)
