"""
Settings Manager - Manages application settings stored in MongoDB
"""
import os
import uuid
from typing import Dict, Optional, List

from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError

from components.logging_manager import logging_manager

logger = logging_manager


class SettingsManager:
    """Settings manager using MongoDB for persistence"""
    
    def __init__(self, 
                 mongo_uri: str = None,
                 db_name: str = "yume",
                 collection_name: str = "train_station_mappings"):
        """
        Initialize MongoDB settings manager.
        
        Args:
            mongo_uri: MongoDB connection string (default: env var MONGODB_URI or local)
            db_name: Database name
            collection_name: Collection name for train station mappings
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
            logger.log("Settings Manager connected to MongoDB successfully")
        except ServerSelectionTimeoutError:
            logger.log(f"Settings Manager failed to connect to MongoDB at {self.mongo_uri}")
            raise
    
    def get_train_station_mappings(self) -> List[Dict]:
        """
        Get all train station to Home Assistant entity ID mappings.
        
        Returns:
            List of mapping dictionaries with id, station_name, and entity_id
        """
        try:
            documents = self.collection.find()
            mappings = []
            for doc in documents:
                mappings.append({
                    "id": doc["_id"],
                    "station_name": doc["station_name"],
                    "entity_id": doc["entity_id"]
                })
            return mappings
        except Exception as e:
            logger.log(f"Error fetching train station mappings: {e}")
            return []
    
    def add_train_station_mapping(self, station_name: str, entity_id: str) -> Optional[str]:
        """
        Add a new train station mapping.
        
        Args:
            station_name: Name of the train station
            entity_id: Home Assistant entity ID
            
        Returns:
            UUID of the created mapping, or None if failed
        """
        try:
            mapping_id = str(uuid.uuid4())
            self.collection.insert_one({
                "_id": mapping_id,
                "station_name": station_name,
                "entity_id": entity_id
            })
            logger.log(f"Added train station mapping: {station_name} -> {entity_id}")
            return mapping_id
        except Exception as e:
            logger.log(f"Error adding train station mapping: {e}")
            return None
    
    def update_train_station_mapping(self, mapping_id: str, station_name: str, entity_id: str) -> bool:
        """
        Update an existing train station mapping.
        
        Args:
            mapping_id: UUID of the mapping to update
            station_name: Name of the train station
            entity_id: Home Assistant entity ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            result = self.collection.update_one(
                {"_id": mapping_id},
                {"$set": {
                    "station_name": station_name,
                    "entity_id": entity_id
                }}
            )
            if result.modified_count > 0:
                logger.log(f"Updated train station mapping {mapping_id}")
                return True
            return False
        except Exception as e:
            logger.log(f"Error updating train station mapping: {e}")
            return False
    
    def delete_train_station_mapping(self, mapping_id: str) -> bool:
        """
        Delete a train station mapping.
        
        Args:
            mapping_id: UUID of the mapping to remove
            
        Returns:
            True if successful, False otherwise
        """
        try:
            result = self.collection.delete_one({"_id": mapping_id})
            if result.deleted_count > 0:
                logger.log(f"Deleted train station mapping {mapping_id}")
                return True
            return False
        except Exception as e:
            logger.log(f"Error deleting train station mapping: {e}")
            return False
    
    def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()


settings_manager = SettingsManager()
