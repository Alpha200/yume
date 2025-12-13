import os
import logging
from typing import Optional
from dataclasses import dataclass

from pymongo import MongoClient

from components.timezone_utils import now_user_tz
from aiagents.memory_summarizer import summarize_memories

logger = logging.getLogger(__name__)


@dataclass
class MemorySummary:
    """Typed dataclass for memory summary results"""
    summarized_preferences: str
    summarized_observations: str
    summarized_reminders: str
    updated_at: Optional[str] = None


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
        
        # Create client with connection pooling enabled (default behavior)
        # PyMongo handles reconnection and pooling automatically
        self.client = MongoClient(self.mongo_uri, serverSelectionTimeoutMS=5000)
        self.db = self.client[self.db_name]
        self.collection = self.db[self.collection_name]
        
        logger.info(f"Initialized MongoDB client for memory summarizer service")
    
    def save_summary(self, summarized_preferences: str, summarized_observations: str, summarized_reminders: str) -> None:
        """
        Save memory summaries to MongoDB.
        
        Args:
            summarized_preferences: Summarized user preferences
            summarized_observations: Summarized observations
            summarized_reminders: Summarized reminders
            
        Raises:
            Exception: If MongoDB operation fails
        """
        summary_doc = {
            "_id": "current",  # Use a fixed ID for the current summary
            "summarized_preferences": summarized_preferences,
            "summarized_observations": summarized_observations,
            "summarized_reminders": summarized_reminders,
            "created_at": now_user_tz().isoformat(),
            "updated_at": now_user_tz().isoformat()
        }
        
        # Upsert the summary (update if exists, insert if not)
        # PyMongo will handle reconnection and retries automatically
        self.collection.update_one(
            {"_id": "current"},
            {"$set": summary_doc},
            upsert=True
        )
        logger.debug("Memory summaries saved to MongoDB")
    
    def get_summary(self) -> Optional[MemorySummary]:
        """
        Retrieve the current memory summary from MongoDB.
        
        Returns:
            MemorySummary object with summarized preferences, observations, and reminders
            or None if no summary exists
            
        Raises:
            Exception: If MongoDB operation fails
        """
        # PyMongo will handle reconnection and retries automatically
        summary = self.collection.find_one({"_id": "current"})
        if summary:
            return MemorySummary(
                summarized_preferences=summary.get("summarized_preferences", ""),
                summarized_observations=summary.get("summarized_observations", ""),
                summarized_reminders=summary.get("summarized_reminders", ""),
                updated_at=summary.get("updated_at")
            )
        return None


# Global instance
memory_summarizer_service = MemorySummarizerService()


async def update_memory_summaries(
    formatted_preferences: str,
    formatted_observations_and_reminders: str
) -> Optional[MemorySummary]:
    """
    Update memory summaries: run the summarizer agent and save results to MongoDB.
    
    Args:
        formatted_preferences: Formatted string of user preferences
        formatted_observations_and_reminders: Formatted string of observations and reminders
    
    Returns:
        MemorySummary object with summarized memories or None if an error occurs
    """
    try:
        logger.info("Updating memory summaries")
        
        # Run the summarizer agent
        summary_result = await summarize_memories(
            formatted_preferences,
            formatted_observations_and_reminders
        )
        
        if summary_result:
            try:
                # Save to MongoDB
                memory_summarizer_service.save_summary(
                    summary_result.summarized_preferences,
                    summary_result.summarized_observations,
                    summary_result.summarized_reminders
                )
            except RuntimeError as e:
                logger.warning(f"Memory summaries generated but failed to persist: {e}")
                # Still return the result so it's available in memory, but caller should know it failed
            
            return MemorySummary(
                summarized_preferences=summary_result.summarized_preferences,
                summarized_observations=summary_result.summarized_observations,
                summarized_reminders=summary_result.summarized_reminders
            )
        
        return None
    except Exception as e:
        logger.error(f"Error updating memory summaries: {e}")
        raise
