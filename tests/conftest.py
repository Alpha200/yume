import pytest
from unittest.mock import MagicMock, patch
import sys


def pytest_configure(config):
    """Patch MongoDB before any test modules are imported"""
    patcher = patch('pymongo.MongoClient')
    mock_client_class = patcher.start()
    
    # Setup the mock instance
    mock_client_instance = MagicMock()
    mock_client_instance.admin.command.return_value = None
    mock_client_class.return_value = mock_client_instance
    
    mock_db = MagicMock()
    mock_collection = MagicMock()
    
    mock_client_instance.__getitem__.return_value = mock_db
    mock_db.__getitem__.return_value = mock_collection
    
    # Mock default collection methods
    mock_collection.create_index.return_value = None
    mock_collection.count_documents.return_value = 0
    mock_collection.find_one.return_value = None
    
    # Store patcher for cleanup
    config._mongo_patcher = patcher


def pytest_unconfigure(config):
    """Stop patching MongoDB after tests are done"""
    if hasattr(config, '_mongo_patcher'):
        config._mongo_patcher.stop()
