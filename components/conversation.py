from dataclasses import dataclass


@dataclass
class ConversationEntry:
    """A single entry in the conversation history."""
    sender: str
    message: str
    timestamp: str
