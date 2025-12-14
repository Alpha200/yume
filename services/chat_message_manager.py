import logging
import os
from typing import List, Optional
from datetime import datetime, UTC, timedelta
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError
from dataclasses import dataclass, field, asdict

logger = logging.getLogger(__name__)


@dataclass
class ChatMessage:
    """Represents a chat message stored in MongoDB"""
    message_id: str  # Unique identifier to prevent duplicates
    sender: str
    message: str
    timestamp: str
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    modified_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class ChatMessageManager:
    """Manages chat message persistence to MongoDB"""

    def __init__(
        self,
        mongo_uri: str = None,
        db_name: str = "yume",
        collection_name: str = "chat_messages"
    ):
        """
        Initialize MongoDB chat message manager.

        Args:
            mongo_uri: MongoDB connection string (default: env var MONGODB_URI or local)
            db_name: Database name
            collection_name: Collection name for chat messages
        """
        self.mongo_uri = mongo_uri or os.getenv("MONGODB_URI", "mongodb://mongodb:27017")
        self.db_name = db_name
        self.collection_name = collection_name
        self.client = None
        self.db = None
        self.collection = None

        self._connect()
        self._ensure_indexes()

    def _connect(self):
        """Establish connection to MongoDB"""
        try:
            self.client = MongoClient(self.mongo_uri, serverSelectionTimeoutMS=5000)
            # Verify connection
            self.client.admin.command('ping')
            self.db = self.client[self.db_name]
            self.collection = self.db[self.collection_name]
            logger.info(f"Connected to MongoDB successfully for chat messages")
        except ServerSelectionTimeoutError:
            logger.error(f"Failed to connect to MongoDB at {self.mongo_uri}")
            raise

    def _ensure_indexes(self):
        """Create necessary indexes for chat messages"""
        try:
            # Create unique index on message_id to prevent duplicates
            self.collection.create_index("message_id", unique=True)
            # Create index on timestamp for efficient querying
            self.collection.create_index("timestamp")
            # Create index on created_at for sorting
            self.collection.create_index("created_at")
            logger.info("Chat message indexes created")
        except Exception as e:
            logger.error(f"Failed to create indexes: {e}")

    def _message_to_document(self, msg: ChatMessage) -> dict:
        """Convert ChatMessage to MongoDB document"""
        doc = asdict(msg)
        # Ensure timestamp is stored as a string for consistency
        doc['timestamp'] = msg.timestamp
        return doc

    def save_message(self, message_id: str, sender: str, message: str, timestamp: str) -> bool:
        """
        Save a chat message to MongoDB.

        Args:
            message_id: Unique identifier for the message (e.g., Matrix event ID)
            sender: The sender of the message
            message: The message content
            timestamp: ISO format timestamp of the message

        Returns:
            True if saved successfully, False if duplicate
        """
        try:
            chat_msg = ChatMessage(
                message_id=message_id,
                sender=sender,
                message=message,
                timestamp=timestamp
            )
            
            # Upsert to handle duplicates gracefully
            result = self.collection.update_one(
                {"message_id": message_id},
                {
                    "$setOnInsert": self._message_to_document(chat_msg)
                },
                upsert=True
            )
            
            if result.upserted_id:
                logger.debug(f"Saved new chat message: {message_id}")
                return True
            else:
                logger.debug(f"Message already exists: {message_id}")
                return False
        except Exception as e:
            logger.error(f"Failed to save chat message: {e}")
            return False

    def get_recent_messages(self, limit: int = 20) -> List[ChatMessage]:
        """
        Retrieve recent chat messages from MongoDB.

        Args:
            limit: Maximum number of recent messages to retrieve (default: 20)

        Returns:
            List of ChatMessage objects in chronological order
        """
        try:
            # Sort by timestamp (actual message timestamp) in ascending order (oldest to newest)
            # This ensures messages are returned in the correct chronological order based on when they were actually sent
            docs = list(
                self.collection.find()
                .sort("timestamp", 1)
                .limit(limit)
            )
            
            messages = []
            for doc in docs:
                # Remove MongoDB's _id field
                doc.pop("_id", None)
                msg = ChatMessage(**doc)
                messages.append(msg)
            
            return messages
        except Exception as e:
            logger.error(f"Failed to retrieve chat messages: {e}")
            return []

    def get_messages_by_sender(self, sender: str, limit: int = 20) -> List[ChatMessage]:
        """
        Retrieve recent messages from a specific sender.

        Args:
            sender: The sender to filter by
            limit: Maximum number of messages to retrieve

        Returns:
            List of ChatMessage objects
        """
        try:
            docs = list(
                self.collection.find({"sender": sender})
                .sort("timestamp", 1)
                .limit(limit)
            )
            
            messages = []
            for doc in docs:
                doc.pop("_id", None)
                msg = ChatMessage(**doc)
                messages.append(msg)
            
            return messages
        except Exception as e:
            logger.error(f"Failed to retrieve messages from sender {sender}: {e}")
            return []

    def message_exists(self, message_id: str) -> bool:
        """
        Check if a message already exists in the database.

        Args:
            message_id: The message ID to check

        Returns:
            True if message exists, False otherwise
        """
        try:
            return self.collection.find_one({"message_id": message_id}) is not None
        except Exception as e:
            logger.error(f"Failed to check if message exists: {e}")
            return False

    def delete_old_messages(self, keep_days: int = 30) -> int:
        """
        Delete chat messages older than specified days.

        Args:
            keep_days: Number of days to keep (delete older messages)

        Returns:
            Number of messages deleted
        """
        try:
            cutoff_date = datetime.now(UTC) - timedelta(days=keep_days)
            result = self.collection.delete_many({
                "created_at": {"$lt": cutoff_date}
            })
            
            logger.info(f"Deleted {result.deleted_count} messages older than {keep_days} days")
            return result.deleted_count
        except Exception as e:
            logger.error(f"Failed to delete old messages: {e}")
            return 0

    def get_message_count(self) -> int:
        """Get total count of stored messages"""
        try:
            return self.collection.count_documents({})
        except Exception as e:
            logger.error(f"Failed to count messages: {e}")
            return 0

    def get_conversation_context(self, max_messages: int = 10, include_timestamps: bool = False, system_username: Optional[str] = None) -> Optional[str]:
        """Build conversation context from recent messages stored in MongoDB

        Args:
            max_messages: Maximum number of recent messages to include
            include_timestamps: Whether to include timestamps in the format [YYYY-MM-DD HH:MM]
            system_username: Optional system username to identify system messages

        Returns:
            Conversation context string or None if no history available
        """
        # Fetch recent messages from MongoDB
        recent_messages = self.get_recent_messages(limit=max_messages)
        
        if not recent_messages:
            return None

        context_lines = ["Recent conversation history:"]

        for msg in recent_messages:
            sender_name = msg.sender.split(":")[0].replace("@", "")

            # Determine if sender is system or use real username
            if system_username and sender_name == system_username:
                role = "system"
            else:
                role = sender_name

            if include_timestamps:
                # Parse timestamp and format as date
                msg_time = datetime.fromisoformat(msg.timestamp).strftime("%Y-%m-%d %H:%M")
                context_lines.append(f"[{msg_time}] {role}: {msg.message}")
            else:
                context_lines.append(f"{role}: {msg.message}")

        return "\n".join(context_lines)


# Initialize the manager
chat_message_manager = ChatMessageManager()
