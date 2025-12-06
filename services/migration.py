"""
Migration utility to migrate memories from JSON file to MongoDB
"""
import json
import os
from pathlib import Path

from components.logging_manager import logging_manager
from services.memory_manager import MemoryManager

logger = logging_manager


def migrate_json_to_mongodb(json_file_path: str = "./data/memories.json",
                            mongo_uri: str = None) -> bool:
    """
    Migrate memories from JSON file to MongoDB.
    
    Args:
        json_file_path: Path to the JSON memories file
        mongo_uri: MongoDB connection string
    
    Returns:
        True if migration successful, False otherwise
    """
    if not os.path.exists(json_file_path):
        logger.log(f"JSON memories file not found: {json_file_path}")
        return False
    
    try:
        # Initialize MongoDB memory manager
        mongo_manager = MemoryManager(mongo_uri=mongo_uri)
        
        # Check if MongoDB already has data
        existing_count = mongo_manager.collection.count_documents({})
        if existing_count > 0:
            logger.log(f"MongoDB already contains {existing_count} memories. Skipping migration.")
            return True
        
        # Load JSON data
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        memories_data = data.get("memories", {})
        
        if not memories_data:
            logger.log("No memories found in JSON file to migrate")
            return True
        
        # Migrate each memory entry
        migrated_count = 0
        for memory_id, entry_data in memories_data.items():
            try:
                doc = {
                    "_id": memory_id,
                    "content": entry_data["content"],
                    "place": entry_data.get("place"),
                    "type": entry_data.get("type", "user_preference"),
                    "created_at": entry_data.get("created_at"),
                    "modified_at": entry_data.get("modified_at")
                }
                
                # Add optional fields
                if "observation_date" in entry_data:
                    doc["observation_date"] = entry_data["observation_date"]
                
                if "reminder_options" in entry_data:
                    doc["reminder_options"] = entry_data["reminder_options"]
                
                mongo_manager.collection.insert_one(doc)
                migrated_count += 1
            except Exception as e:
                logger.log(f"Error migrating memory {memory_id}: {e}")
        
        logger.log(f"Successfully migrated {migrated_count} memories from JSON to MongoDB")
        
        # Delete the JSON file after successful migration
        try:
            os.remove(json_file_path)
            logger.log(f"Deleted JSON memories file: {json_file_path}")
        except Exception as e:
            logger.log(f"Warning: Could not delete JSON file: {e}")
        
        return True
    
    except Exception as e:
        logger.log(f"Migration failed: {e}")
        return False
