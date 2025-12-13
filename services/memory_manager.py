import logging
import datetime
import os
import uuid
from typing import Dict, Literal, Optional, List, Union
from abc import ABC
from dataclasses import dataclass

from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError

from components.timezone_utils import now_user_tz, to_user_tz, from_isoformat_user_tz

logger = logging.getLogger(__name__)


@dataclass
class ReminderOptions:
    """Options for reminder memory entries - supports time-based and location-based reminders"""
    datetime_value: Optional[datetime.datetime] = None  # For one-time reminders
    time_value: Optional[str] = None  # Time in HH:MM format for recurring reminders
    days_of_week: Optional[List[str]] = None  # List of weekday names for recurring reminders
    location: Optional[str] = None  # Location-based trigger (geofence name)
    trigger_type: Optional[Literal["enter", "leave"]] = None  # Trigger on enter or leave for location-based


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
    """Memory manager using MongoDB for persistence"""
    
    def __init__(self, 
                 mongo_uri: str = None,
                 db_name: str = "yume",
                 collection_name: str = "memories"):
        """
        Initialize MongoDB memory manager.
        
        Args:
            mongo_uri: MongoDB connection string (default: env var MONGODB_URI or local)
            db_name: Database name
            collection_name: Collection name
        """
        self.mongo_uri = mongo_uri or os.getenv("MONGODB_URI", "mongodb://mongodb:27017")
        self.db_name = db_name
        self.collection_name = collection_name
        self.client = None
        self.db = None
        self.collection = None
        
        self._connect()
    
    def _connect(self):
        """Establish connection to MongoDB"""
        try:
            self.client = MongoClient(self.mongo_uri, serverSelectionTimeoutMS=5000)
            # Verify connection
            self.client.admin.command('ping')
            self.db = self.client[self.db_name]
            self.collection = self.db[self.collection_name]
            logger.info("Connected to MongoDB successfully")
        except ServerSelectionTimeoutError:
            logger.error(f"Failed to connect to MongoDB at {self.mongo_uri}")
            raise
    
    def _entry_to_document(self, entry: MemoryEntry) -> dict:
        """Convert memory entry to MongoDB document"""
        doc = {
            "_id": entry.id,
            "content": entry.content,
            "place": entry.place,
            "type": entry.type,
            "created_at": entry.created_at.isoformat(),
            "modified_at": entry.modified_at.isoformat()
        }
        
        if isinstance(entry, UserObservationEntry):
            doc["observation_date"] = entry.observation_date.isoformat()
        elif isinstance(entry, ReminderEntry):
            reminder_data = {}
            if entry.reminder_options.datetime_value:
                reminder_data["datetime_value"] = entry.reminder_options.datetime_value.isoformat()
            if entry.reminder_options.time_value:
                reminder_data["time_value"] = entry.reminder_options.time_value
            if entry.reminder_options.days_of_week:
                reminder_data["days_of_week"] = entry.reminder_options.days_of_week
            if entry.reminder_options.location:
                reminder_data["location"] = entry.reminder_options.location
            if entry.reminder_options.trigger_type:
                reminder_data["trigger_type"] = entry.reminder_options.trigger_type
            
            if reminder_data:
                doc["reminder_options"] = reminder_data
        
        return doc
    
    def _document_to_entry(self, doc: dict) -> MemoryEntry:
        """Convert MongoDB document to memory entry"""
        memory_id = doc["_id"]
        created_at = from_isoformat_user_tz(doc["created_at"])
        modified_at = from_isoformat_user_tz(doc["modified_at"])
        memory_type = doc.get("type", "user_preference")
        
        if memory_type == "user_preference":
            return UserPreferenceEntry(
                id=memory_id,
                content=doc["content"],
                place=doc.get("place"),
                created_at=created_at,
                modified_at=modified_at
            )
        elif memory_type == "user_observation":
            observation_date = now_user_tz()
            if doc.get("observation_date"):
                observation_date = from_isoformat_user_tz(doc["observation_date"])
            
            return UserObservationEntry(
                id=memory_id,
                content=doc["content"],
                place=doc.get("place"),
                created_at=created_at,
                modified_at=modified_at,
                observation_date=observation_date
            )
        elif memory_type == "reminder":
            reminder_options = ReminderOptions()
            if doc.get("reminder_options"):
                reminder_data = doc["reminder_options"]
                if reminder_data.get("datetime_value"):
                    reminder_options.datetime_value = from_isoformat_user_tz(reminder_data["datetime_value"])
                reminder_options.time_value = reminder_data.get("time_value")
                reminder_options.days_of_week = reminder_data.get("days_of_week")
                reminder_options.location = reminder_data.get("location")
                reminder_options.trigger_type = reminder_data.get("trigger_type")
            
            return ReminderEntry(
                id=memory_id,
                content=doc["content"],
                place=doc.get("place"),
                created_at=created_at,
                modified_at=modified_at,
                reminder_options=reminder_options
            )
        else:
            # Default to user preference for unknown types
            return UserPreferenceEntry(
                id=memory_id,
                content=doc["content"],
                place=doc.get("place"),
                created_at=created_at,
                modified_at=modified_at
            )
    
    def save_memory(self, entry: MemoryEntry):
        """Save or update a single memory entry in MongoDB"""
        try:
            doc = self._entry_to_document(entry)
            self.collection.replace_one({"_id": entry.id}, doc, upsert=True)
        except Exception as e:
            logger.error(f"Error saving memory to MongoDB: {e}")
            raise
    
    def create_user_preference(
        self,
        content: str,
        memory_id: str = None,
        place: str = None
    ) -> str:
        """Create or update a user preference entry"""
        if memory_id is None:
            memory_id = str(uuid.uuid4())
            created_at = now_user_tz()
        else:
            # Try to get existing entry's creation time from DB
            existing_doc = self.collection.find_one({"_id": memory_id})
            if existing_doc and "created_at" in existing_doc:
                created_at = from_isoformat_user_tz(existing_doc["created_at"])
            else:
                created_at = now_user_tz()
        
        entry = UserPreferenceEntry(
            id=memory_id,
            content=content,
            place=place,
            created_at=created_at,
            modified_at=now_user_tz()
        )
        
        self.save_memory(entry)
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
            created_at = now_user_tz()
        else:
            # Try to get existing entry's creation time from DB
            existing_doc = self.collection.find_one({"_id": memory_id})
            if existing_doc and "created_at" in existing_doc:
                created_at = from_isoformat_user_tz(existing_doc["created_at"])
            else:
                created_at = now_user_tz()
        
        observation_date = to_user_tz(observation_date)
        
        entry = UserObservationEntry(
            id=memory_id,
            content=content,
            place=place,
            created_at=created_at,
            modified_at=now_user_tz(),
            observation_date=observation_date
        )
        
        self.save_memory(entry)
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
            created_at = now_user_tz()
        else:
            # Try to get existing entry's creation time from DB
            existing_doc = self.collection.find_one({"_id": memory_id})
            if existing_doc and "created_at" in existing_doc:
                created_at = from_isoformat_user_tz(existing_doc["created_at"])
            else:
                created_at = now_user_tz()
        
        if reminder_options.datetime_value:
            reminder_options.datetime_value = to_user_tz(reminder_options.datetime_value)
        
        entry = ReminderEntry(
            id=memory_id,
            content=content,
            place=place,
            created_at=created_at,
            modified_at=now_user_tz(),
            reminder_options=reminder_options
        )
        
        self.save_memory(entry)
        return memory_id
    
    def get_all_memories(self) -> Dict[str, MemoryEntry]:
        """Get all memory entries from MongoDB"""
        try:
            documents = self.collection.find()
            memories = {}
            for doc in documents:
                entry = self._document_to_entry(doc)
                memories[entry.id] = entry
            return memories
        except Exception as e:
            logger.error(f"Error fetching memories from MongoDB: {e}")
            return {}
    
    def get_user_preferences(self) -> Dict[str, UserPreferenceEntry]:
        """Get all user preference entries from MongoDB"""
        try:
            documents = self.collection.find({"type": "user_preference"})
            preferences = {}
            for doc in documents:
                entry = self._document_to_entry(doc)
                if isinstance(entry, UserPreferenceEntry):
                    preferences[entry.id] = entry
            return preferences
        except Exception as e:
            logger.error(f"Error fetching preferences from MongoDB: {e}")
            return {}
    
    def get_user_observations(self) -> Dict[str, UserObservationEntry]:
        """Get all user observation entries from MongoDB"""
        try:
            documents = self.collection.find({"type": "user_observation"})
            observations = {}
            for doc in documents:
                entry = self._document_to_entry(doc)
                if isinstance(entry, UserObservationEntry):
                    observations[entry.id] = entry
            return observations
        except Exception as e:
            logger.error(f"Error fetching observations from MongoDB: {e}")
            return {}
    
    def get_reminders(self) -> Dict[str, ReminderEntry]:
        """Get all reminder entries from MongoDB"""
        try:
            documents = self.collection.find({"type": "reminder"})
            reminders = {}
            for doc in documents:
                entry = self._document_to_entry(doc)
                if isinstance(entry, ReminderEntry):
                    reminders[entry.id] = entry
            return reminders
        except Exception as e:
            logger.error(f"Error fetching reminders from MongoDB: {e}")
            return {}
    
    def get_memories_by_type(self, memory_type: Literal["user_preference", "user_observation", "reminder"]) -> Dict[str, MemoryEntry]:
        """Get all memories of a specific type from MongoDB"""
        try:
            documents = self.collection.find({"type": memory_type})
            memories = {}
            for doc in documents:
                entry = self._document_to_entry(doc)
                memories[entry.id] = entry
            return memories
        except Exception as e:
            logger.error(f"Error fetching memories by type from MongoDB: {e}")
            return {}
    
    def _format_reminder_schedule(self, reminder_entry: ReminderEntry) -> str:
        """Format reminder schedule information for display"""
        ro = reminder_entry.reminder_options
        schedule_info = "Reminder Schedule:\n"
        if ro.datetime_value:
            schedule_info += f"  Type: One-time\n"
            schedule_info += f"  Scheduled for: {ro.datetime_value.strftime('%Y-%m-%d %H:%M:%S')}\n"
        elif ro.time_value:
            schedule_info += f"  Type: Recurring\n"
            schedule_info += f"  Time: {ro.time_value}\n"
            if ro.days_of_week and len(ro.days_of_week) > 0:
                schedule_info += f"  Days: {', '.join(ro.days_of_week)}\n"
            else:
                schedule_info += f"  Days: Daily\n"
        elif ro.location:
            schedule_info += f"  Type: Location-based\n"
            schedule_info += f"  Location: {ro.location}\n"
            if ro.trigger_type:
                trigger_text = "enter" if ro.trigger_type == "enter" else "leave"
                schedule_info += f"  Trigger: On {trigger_text}\n"
        return schedule_info
    
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
            
            if isinstance(entry, UserObservationEntry):
                memory_info += f"Observation Date: {entry.observation_date.strftime('%Y-%m-%d %H:%M:%S')}\n"
            elif isinstance(entry, ReminderEntry):
                memory_info += self._format_reminder_schedule(entry)
            
            memory_list.append(memory_info.rstrip())
        
        return "\n\n".join(memory_list)
    
    def get_formatted_preferences(self) -> str:
        """Get user preferences as a formatted string for agent instructions"""
        preferences = self.get_user_preferences()
        
        if not preferences:
            return "No user preferences stored."
        
        pref_list = []
        for memory_id, entry in preferences.items():
            pref_info = f"- {entry.content}"
            if entry.place:
                pref_info += f" (Place: {entry.place})"
            pref_list.append(pref_info)
        
        return "\n".join(pref_list)
    
    def get_formatted_observations_and_reminders(self) -> str:
        """Get observations and reminders as a formatted string (excludes preferences)"""
        observations = self.get_user_observations()
        reminders = self.get_reminders()
        
        memory_list = []
        
        for memory_id, entry in observations.items():
            memory_info = f"Type: {entry.type}\n"
            memory_info += f"Content: {entry.content}\n"
            if entry.place:
                memory_info += f"Place: {entry.place}\n"
            memory_info += f"Observation Date: {entry.observation_date.strftime('%Y-%m-%d %H:%M:%S')}\n"
            memory_list.append(memory_info.rstrip())
        
        for memory_id, entry in reminders.items():
            memory_info = f"Type: {entry.type}\n"
            memory_info += f"Content: {entry.content}\n"
            if entry.place:
                memory_info += f"Place: {entry.place}\n"
            memory_info += self._format_reminder_schedule(entry)
            memory_list.append(memory_info.rstrip())
        
        if not memory_list:
            return "No observations or reminders stored."
        
        return "\n\n".join(memory_list)
    
    def get_location_reminders(self, location: str) -> Dict[str, ReminderEntry]:
        """Get all location-based reminders for a specific location"""
        reminders = self.get_reminders()
        location_reminders = {}
        for memory_id, reminder in reminders.items():
            if reminder.reminder_options.location and reminder.reminder_options.location.lower() == location.lower():
                location_reminders[memory_id] = reminder
        return location_reminders
    
    def get_location_reminders_by_trigger(self, location: str, trigger_type: Literal["enter", "leave"]) -> Dict[str, ReminderEntry]:
        """Get location-based reminders for a specific location and trigger type"""
        reminders = self.get_reminders()
        matching_reminders = {}
        for memory_id, reminder in reminders.items():
            if (reminder.reminder_options.location and 
                reminder.reminder_options.location.lower() == location.lower() and
                reminder.reminder_options.trigger_type == trigger_type):
                matching_reminders[memory_id] = reminder
        return matching_reminders
    
    def delete_memory(self, memory_id: str) -> bool:
        """Delete a memory entry by ID from MongoDB. Returns True if deleted, False if not found"""
        try:
            result = self.collection.delete_one({"_id": memory_id})
            if result.deleted_count > 0:
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting memory from MongoDB: {e}")
            raise
    
    def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()


memory_manager = MemoryManager()
