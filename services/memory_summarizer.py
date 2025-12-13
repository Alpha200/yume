import os
from typing import Optional
from datetime import datetime

from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError

from components.logging_manager import logging_manager
from components.timezone_utils import now_user_tz
from aiagents.memory_summarizer import summarize_memories

logger = logging_manager


class MemorySummarizerService:
    """Service for managing memory summaries in MongoDB"""
    
    def __init__(self, 
                 mongo_uri: str = None,
                 db_name: str = "yume",
                 collection_name: str = "memory_summaries"):
        """
        Initialize memory summarizer service.
        
        Args:
            mongo_uri: MongoDB connection string (default: env var MONGODB_URI or local)
            db_name: Database name
            collection_name: Collection name for storing summaries
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
            logger.log(f"Connected to MongoDB successfully for memory summarizer service")
        except ServerSelectionTimeoutError:
            logger.log(f"Failed to connect to MongoDB at {self.mongo_uri}")
            raise
    
    def save_summary(self, summarized_preferences: str, summarized_observations: str, summarized_reminders: str) -> None:
        """
        Save memory summaries to MongoDB.
        
        Args:
            summarized_preferences: Summarized user preferences
            summarized_observations: Summarized observations
            summarized_reminders: Summarized reminders
        """
        if self.collection is None:
            logger.log("Warning: MongoDB collection not initialized")
            return
        
        summary_doc = {
            "_id": "current",  # Use a fixed ID for the current summary
            "summarized_preferences": summarized_preferences,
            "summarized_observations": summarized_observations,
            "summarized_reminders": summarized_reminders,
            "created_at": now_user_tz().isoformat(),
            "updated_at": now_user_tz().isoformat()
        }
        
        try:
            # Upsert the summary (update if exists, insert if not)
            self.collection.update_one(
                {"_id": "current"},
                {"$set": summary_doc},
                upsert=True
            )
            logger.log("Memory summaries saved to MongoDB")
        except Exception as e:
            logger.log(f"Error saving memory summaries to MongoDB: {e}")
            raise
    
    def get_summary(self) -> Optional[dict]:
        """
        Retrieve the current memory summary from MongoDB.
        
        Returns:
            Dictionary with summarized_preferences, summarized_observations, summarized_reminders
            or None if no summary exists
        """
        if self.collection is None:
            logger.log("Warning: MongoDB collection not initialized")
            return None
        
        try:
            summary = self.collection.find_one({"_id": "current"})
            if summary:
                return {
                    "summarized_preferences": summary.get("summarized_preferences", ""),
                    "summarized_observations": summary.get("summarized_observations", ""),
                    "summarized_reminders": summary.get("summarized_reminders", ""),
                    "updated_at": summary.get("updated_at")
                }
            return None
        except Exception as e:
            logger.log(f"Error retrieving memory summary from MongoDB: {e}")
            return None


# Global instance
memory_summarizer_service = MemorySummarizerService()


async def update_memory_summaries(
    formatted_preferences: str,
    formatted_observations_and_reminders: str
) -> Optional[dict]:
    """
    Update memory summaries: run the summarizer agent and save results to MongoDB.
    
    Args:
        formatted_preferences: Formatted string of user preferences
        formatted_observations_and_reminders: Formatted string of observations and reminders
    
    Returns:
        Dictionary with summarized memories or None if an error occurs
    """
    try:
        logger.log("Updating memory summaries")
        
        # Run the summarizer agent
        summary_result = await summarize_memories(
            formatted_preferences,
            formatted_observations_and_reminders
        )
        
        if summary_result:
            # Save to MongoDB
            memory_summarizer_service.save_summary(
                summary_result.summarized_preferences,
                summary_result.summarized_observations,
                summary_result.summarized_reminders
            )
            
            return {
                "summarized_preferences": summary_result.summarized_preferences,
                "summarized_observations": summary_result.summarized_observations,
                "summarized_reminders": summary_result.summarized_reminders
            }
        
        return None
    except Exception as e:
        logger.log(f"Error updating memory summaries: {e}")
        raise
