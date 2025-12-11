"""
Settings Manager - Manages application settings stored in MongoDB
"""
import os

from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError

from components.logging_manager import logging_manager

logger = logging_manager


class SettingsManager:
    """Settings manager using MongoDB for persistence"""
    
    def __init__(self, 
                 mongo_uri: str = None,
                 db_name: str = "yume"):
        """
        Initialize MongoDB settings manager.
        
        Args:
            mongo_uri: MongoDB connection string (default: env var MONGODB_URI or local)
            db_name: Database name
        """
        self.mongo_uri = mongo_uri or os.getenv("MONGODB_URI", "mongodb://mongodb:27017")
        self.db_name = db_name
        self.client = None
        self.db = None
        
        self._connect()
    
    def _connect(self):
        """Establish connection to MongoDB"""
        try:
            self.client = MongoClient(self.mongo_uri, serverSelectionTimeoutMS=5000)
            # Verify connection
            self.client.admin.command('ping')
            self.db = self.client[self.db_name]
            logger.log("Settings Manager connected to MongoDB successfully")
        except ServerSelectionTimeoutError:
            logger.log(f"Settings Manager failed to connect to MongoDB at {self.mongo_uri}")
            raise

    def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()


settings_manager = SettingsManager()
