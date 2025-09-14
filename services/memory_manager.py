import datetime
from dataclasses import dataclass
import json
import os
import uuid
from typing import Dict, Literal, Optional, List, Union
from abc import ABC

@dataclass
class ReminderOptions:
    """Options for reminder memory entries"""
    datetime_value: Optional[datetime.datetime] = None  # For one-time reminders
    time_value: Optional[str] = None  # Time in HH:MM format for recurring reminders
    days_of_week: Optional[List[str]] = None  # List of weekday names for recurring reminders

@dataclass
class BaseMemoryEntry(ABC):
    """Base class for all memory entries"""
    id: str
    content: str
    place: Optional[str]
    created_at: datetime.datetime
    modified_at: datetime.datetime

@dataclass
class UserPreferenceEntry(BaseMemoryEntry):
    """Memory entry for user preferences"""
    type: Literal["user_preference"] = "user_preference"

@dataclass
class UserObservationEntry(BaseMemoryEntry):
    """Memory entry for user observations with observation date"""
    observation_date: datetime.datetime
    type: Literal["user_observation"] = "user_observation"

@dataclass
class ReminderEntry(BaseMemoryEntry):
    """Memory entry for reminders with reminder options"""
    reminder_options: ReminderOptions
    type: Literal["reminder"] = "reminder"

# Union type for all memory entry types
MemoryEntry = Union[UserPreferenceEntry, UserObservationEntry, ReminderEntry]

class MemoryManager:
    def __init__(self, data_dir: str = "./data"):
        self.data_dir = data_dir
        self.memories_file = os.path.join(data_dir, "memories.json")
        self.memory_entries: Dict[str, MemoryEntry] = {}

        # Ensure data directory exists
        os.makedirs(data_dir, exist_ok=True)

    def save_memories(self):
        """Save memories to disk"""
        data = {
            "version": 3,  # Updated version for new structure
            "memories": {}
        }

        for memory_id, entry in self.memory_entries.items():
            entry_data = {
                "content": entry.content,
                "place": entry.place,
                "type": entry.type,
                "created_at": entry.created_at.isoformat(),
                "modified_at": entry.modified_at.isoformat()
            }

            # Add observation_date for user_observation entries
            if isinstance(entry, UserObservationEntry):
                entry_data["observation_date"] = entry.observation_date.isoformat()

            # Add reminder_options for reminder entries
            elif isinstance(entry, ReminderEntry):
                reminder_data = {}
                if entry.reminder_options.datetime_value:
                    reminder_data["datetime_value"] = entry.reminder_options.datetime_value.isoformat()
                if entry.reminder_options.time_value:
                    reminder_data["time_value"] = entry.reminder_options.time_value
                if entry.reminder_options.days_of_week:
                    reminder_data["days_of_week"] = entry.reminder_options.days_of_week

                # Only add reminder_options if we have actual data
                if reminder_data:
                    entry_data["reminder_options"] = reminder_data

            data["memories"][memory_id] = entry_data

        with open(self.memories_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def load_memories(self):
        """Load memories from disk"""
        if not os.path.exists(self.memories_file):
            return

        try:
            with open(self.memories_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Check if this is an empty file
            if not data:
                return

            memories_data = data.get("memories", {})

            for memory_id, entry_data in memories_data.items():
                created_at = datetime.datetime.now(datetime.UTC)
                if entry_data.get("created_at"):
                    created_at = datetime.datetime.fromisoformat(entry_data["created_at"])

                modified_at = datetime.datetime.now(datetime.UTC)
                if entry_data.get("modified_at"):
                    modified_at = datetime.datetime.fromisoformat(entry_data["modified_at"])

                # Handle legacy memory types - convert old types to new ones
                memory_type = entry_data.get("type", "user_preference")
                if memory_type == "user":
                    memory_type = "user_preference"
                elif memory_type in ["system", "instructions"]:
                    # Skip loading old system and instructions entries
                    continue

                # Create appropriate memory entry subclass based on type
                if memory_type == "user_preference":
                    entry = UserPreferenceEntry(
                        id=memory_id,
                        content=entry_data["content"],
                        place=entry_data.get("place"),
                        created_at=created_at,
                        modified_at=modified_at
                    )
                elif memory_type == "user_observation":
                    observation_date = datetime.datetime.now(datetime.UTC)
                    if entry_data.get("observation_date"):
                        observation_date = datetime.datetime.fromisoformat(entry_data["observation_date"])

                    entry = UserObservationEntry(
                        id=memory_id,
                        content=entry_data["content"],
                        place=entry_data.get("place"),
                        created_at=created_at,
                        modified_at=modified_at,
                        observation_date=observation_date
                    )
                elif memory_type == "reminder":
                    reminder_options = ReminderOptions()
                    if entry_data.get("reminder_options"):
                        reminder_data = entry_data["reminder_options"]
                        if reminder_data.get("datetime_value"):
                            reminder_options.datetime_value = datetime.datetime.fromisoformat(reminder_data["datetime_value"])
                        reminder_options.time_value = reminder_data.get("time_value")
                        reminder_options.days_of_week = reminder_data.get("days_of_week")

                    entry = ReminderEntry(
                        id=memory_id,
                        content=entry_data["content"],
                        place=entry_data.get("place"),
                        created_at=created_at,
                        modified_at=modified_at,
                        reminder_options=reminder_options
                    )
                else:
                    # Default to user preference for unknown types
                    entry = UserPreferenceEntry(
                        id=memory_id,
                        content=entry_data["content"],
                        place=entry_data.get("place"),
                        created_at=created_at,
                        modified_at=modified_at
                    )

                self.memory_entries[memory_id] = entry
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            print(f"Error loading memories: {e}")

    def create_user_preference(
        self,
        content: str,
        memory_id: str = None,
        place: str = None
    ) -> str:
        """Create or update a user preference entry"""
        if memory_id is None:
            memory_id = str(uuid.uuid4())
            created_at = datetime.datetime.now(datetime.UTC)
        else:
            created_at = self.memory_entries[memory_id].created_at if memory_id in self.memory_entries else datetime.datetime.now(datetime.UTC)

        entry = UserPreferenceEntry(
            id=memory_id,
            content=content,
            place=place,
            created_at=created_at,
            modified_at=datetime.datetime.now(datetime.UTC)
        )

        self.memory_entries[memory_id] = entry
        self.save_memories()
        return memory_id

    def create_user_observation(
        self,
        content: str,
        observation_date: datetime.datetime,
        memory_id: str = None,
        place: str = None
    ) -> str:
        """Create or update a user observation entry"""
        if memory_id is None:
            memory_id = str(uuid.uuid4())
            created_at = datetime.datetime.now(datetime.UTC)
        else:
            created_at = self.memory_entries[memory_id].created_at if memory_id in self.memory_entries else datetime.datetime.now(datetime.UTC)

        entry = UserObservationEntry(
            id=memory_id,
            content=content,
            place=place,
            created_at=created_at,
            modified_at=datetime.datetime.now(datetime.UTC),
            observation_date=observation_date
        )

        self.memory_entries[memory_id] = entry
        self.save_memories()
        return memory_id

    def create_reminder(
        self,
        content: str,
        reminder_options: ReminderOptions,
        memory_id: str = None,
        place: str = None
    ) -> str:
        """Create or update a reminder entry"""
        if memory_id is None:
            memory_id = str(uuid.uuid4())
            created_at = datetime.datetime.now(datetime.UTC)
        else:
            created_at = self.memory_entries[memory_id].created_at if memory_id in self.memory_entries else datetime.datetime.now(datetime.UTC)

        entry = ReminderEntry(
            id=memory_id,
            content=content,
            place=place,
            created_at=created_at,
            modified_at=datetime.datetime.now(datetime.UTC),
            reminder_options=reminder_options
        )

        self.memory_entries[memory_id] = entry
        self.save_memories()
        return memory_id

    def get_all_memories(self) -> Dict[str, MemoryEntry]:
        """Get all memory entries"""
        return self.memory_entries.copy()

    def get_user_preferences(self) -> Dict[str, UserPreferenceEntry]:
        """Get all user preference entries"""
        return {
            memory_id: entry
            for memory_id, entry in self.memory_entries.items()
            if isinstance(entry, UserPreferenceEntry)
        }

    def get_user_observations(self) -> Dict[str, UserObservationEntry]:
        """Get all user observation entries"""
        return {
            memory_id: entry
            for memory_id, entry in self.memory_entries.items()
            if isinstance(entry, UserObservationEntry)
        }

    def get_reminders(self) -> Dict[str, ReminderEntry]:
        """Get all reminder entries"""
        return {
            memory_id: entry
            for memory_id, entry in self.memory_entries.items()
            if isinstance(entry, ReminderEntry)
        }

    def get_memories_by_type(self, memory_type: Literal["user_preference", "user_observation", "reminder"]) -> Dict[str, MemoryEntry]:
        """Get all memories of a specific type"""
        return {
            memory_id: entry
            for memory_id, entry in self.memory_entries.items()
            if entry.type == memory_type
        }

    def get_formatted_memories(self) -> str:
        """Get all stored memories as a formatted string"""
        memories = self.get_all_memories()

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

    def delete_memory(self, memory_id: str) -> bool:
        """Delete a memory entry by ID. Returns True if deleted, False if not found"""
        if memory_id in self.memory_entries:
            del self.memory_entries[memory_id]
            self.save_memories()
            return True
        return False

memory_manager = MemoryManager()
memory_manager.load_memories()
