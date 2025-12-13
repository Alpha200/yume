import pytest
from unittest.mock import MagicMock
from datetime import datetime
from services.chat_message_manager import ChatMessageManager


@pytest.fixture
def chat_manager():
    """Create a ChatMessageManager instance with mocked MongoDB"""
    manager = ChatMessageManager(db_name="yume_test", collection_name="chat_messages_test")
    return manager


def test_save_message(chat_manager):
    """Test saving a message to MongoDB"""
    msg_id = "$test_event_1"
    sender = "@user:matrix.org"
    message = "Hello, world!"
    timestamp = datetime.now().isoformat()
    
    # Mock the update_one return value
    chat_manager.collection.update_one.return_value = MagicMock(upserted_id="test_id")
    
    result = chat_manager.save_message(msg_id, sender, message, timestamp)
    assert result is True
    chat_manager.collection.update_one.assert_called_once()


def test_duplicate_message(chat_manager):
    """Test that duplicate messages are not saved again"""
    msg_id = "$test_event_2"
    sender = "@user:matrix.org"
    message = "Duplicate test"
    timestamp = datetime.now().isoformat()
    
    # First save returns upserted_id
    chat_manager.collection.update_one.side_effect = [
        MagicMock(upserted_id="test_id"),
        MagicMock(upserted_id=None)
    ]
    
    result1 = chat_manager.save_message(msg_id, sender, message, timestamp)
    assert result1 is True
    
    result2 = chat_manager.save_message(msg_id, sender, message, timestamp)
    assert result2 is False


def test_get_recent_messages(chat_manager):
    """Test retrieving recent messages"""
    # Mock MongoDB find/sort/limit chain
    mock_docs = [
        {"message_id": f"$msg_{i}", "sender": "@user:matrix.org", "message": f"Message {i}", 
         "timestamp": datetime.now().isoformat(), "created_at": datetime.now(), "modified_at": datetime.now()}
        for i in range(5)
    ]
    
    mock_cursor = MagicMock()
    mock_cursor.sort.return_value.limit.return_value = mock_docs[::-1]
    chat_manager.collection.find.return_value = mock_cursor
    
    messages = chat_manager.get_recent_messages(limit=10)
    assert len(messages) == 5


def test_message_exists(chat_manager):
    """Test checking if a message exists"""
    msg_id = "$test_event_exists"
    
    # Message should not exist initially
    chat_manager.collection.find_one.return_value = None
    assert chat_manager.message_exists(msg_id) is False
    
    # Message should exist now
    chat_manager.collection.find_one.return_value = {"message_id": msg_id}
    assert chat_manager.message_exists(msg_id) is True


def test_get_messages_by_sender(chat_manager):
    """Test retrieving messages from a specific sender"""
    sender = "@alice:matrix.org"
    
    mock_docs = [
        {"message_id": f"$alice_msg_{i}", "sender": sender, "message": f"Alice's message {i}", 
         "timestamp": datetime.now().isoformat(), "created_at": datetime.now(), "modified_at": datetime.now()}
        for i in range(3)
    ]
    
    mock_cursor = MagicMock()
    mock_cursor.sort.return_value.limit.return_value = mock_docs[::-1]
    chat_manager.collection.find.return_value = mock_cursor
    
    messages = chat_manager.get_messages_by_sender(sender, limit=10)
    assert len(messages) == 3
    assert all(msg.sender == sender for msg in messages)


def test_get_message_count(chat_manager):
    """Test getting total message count"""
    chat_manager.collection.count_documents.return_value = 10
    
    count = chat_manager.get_message_count()
    assert count == 10


def test_get_conversation_context(chat_manager):
    """Test building conversation context from recent messages"""
    mock_docs = [
        {"message_id": "$msg_1", "sender": "@alice:matrix.org", "message": "Hello", 
         "timestamp": datetime.now().isoformat(), "created_at": datetime.now(), "modified_at": datetime.now()},
        {"message_id": "$msg_2", "sender": "@yume:matrix.org", "message": "Hi there!", 
         "timestamp": datetime.now().isoformat(), "created_at": datetime.now(), "modified_at": datetime.now()},
    ]
    
    mock_cursor = MagicMock()
    mock_cursor.sort.return_value.limit.return_value = mock_docs
    chat_manager.collection.find.return_value = mock_cursor
    
    context = chat_manager.get_conversation_context(max_messages=10, system_username="yume")
    assert context is not None
    assert "Recent conversation history:" in context
    assert "alice" in context
    assert "system" in context  # yume is replaced with "system" when system_username="yume"


if __name__ == "__main__":
    pytest.main([__file__])
