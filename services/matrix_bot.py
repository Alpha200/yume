from nio import AsyncClient, MatrixRoom, RoomMessageText, LoginResponse, SyncResponse
from datetime import datetime
from collections import deque
import os
from components.conversation import ConversationEntry
from components.logging_manager import logging_manager

logger = logging_manager

class MatrixChatBot:
    def __init__(self):
        # Load configuration from environment variables
        self.homeserver = os.getenv("MATRIX_HOMESERVER_URL")
        self.username = os.getenv("MATRIX_USERNAME")
        self.password = os.getenv("MATRIX_PASSWORD")
        self.room_id = os.getenv("MATRIX_ROOM_ID")
        self.system_username = os.getenv("MATRIX_SYSTEM_USERNAME")

        # Validate required environment variables
        if not self.homeserver:
            raise ValueError("MATRIX_HOMESERVER_URL environment variable is required")
        if not self.username:
            raise ValueError("MATRIX_USERNAME environment variable is required")
        if not self.password:
            raise ValueError("MATRIX_PASSWORD environment variable is required")
        if not self.room_id:
            raise ValueError("MATRIX_ROOM_ID environment variable is required")

        logger.log(f"Initializing MatrixChatBot with homeserver: {self.homeserver}, user: {self.username}, room: {self.room_id}")

        self.client = AsyncClient(self.homeserver, self.username)

        # Store the start time to filter out old messages
        self.start_time = datetime.now()

        # Store conversation history (last 20 messages)
        self.conversation_history = deque(maxlen=20)

    async def message_callback(self, room: MatrixRoom, event: RoomMessageText):
        """Handle incoming messages asynchronously"""
        await self._handle_message(room, event)

    async def _handle_message(self, room: MatrixRoom, event: RoomMessageText) -> None:
        try:
            # Only process messages from the specified room
            if room.room_id != self.room_id:
                return

            # Filter out messages that were sent before the bot started
            if event.server_timestamp < self.start_time.timestamp() * 1000:
                return

            logger.log(f"Received message from {event.sender} in {room.room_id}: {event.body}")

            # Add message to history (including our own messages from other apps)
            self.conversation_history.append(ConversationEntry(
                sender=event.sender,
                message=event.body,
                timestamp=datetime.now().isoformat()
            ))

            # Only respond if message is not from us
            if event.sender == self.client.user_id:
                return

            try:
                from services.ai_engine import handle_chat_message
                await handle_chat_message(message=event.body)

            except Exception as e:
                logger.log(f"Error processing message: {e}")
                return  # Do nothing on error


        except Exception as e:
            logger.log(f"Unhandled error in _handle_message: {e}")
            # Send a simple error message to the room
            try:
                await self.client.room_send(
                    room_id=room.room_id,
                    message_type="m.room.message",
                    content={
                        "msgtype": "m.text",
                        "body": "Sorry, I encountered an unexpected error."
                    }
                )
            except Exception as send_error:
                logger.log(f"Failed to send error message: {send_error}")

    async def send_message(self, message: str):
        """Send a message to the configured Matrix room"""
        try:
            await self.client.room_send(
                room_id=self.room_id,
                message_type="m.room.message",
                content={
                    "msgtype": "m.text",
                    "body": message
                }
            )

            # Add our own message to conversation history
            self.conversation_history.append(ConversationEntry(
                sender=self.client.user_id,
                message=message,
                timestamp=datetime.now().isoformat()
            ))

            logger.log(f"Sent message to {self.room_id}: {message}")

        except Exception as e:
            logger.log(f"Failed to send message: {e}")
            # Don't re-raise the exception to prevent crashing the calling function
            return

    def get_conversation_context(self, max_messages: int = 10, include_timestamps: bool = False) -> str | None:
        """Build conversation context from recent messages

        Args:
            max_messages: Maximum number of recent messages to include
            include_timestamps: Whether to include timestamps in the format [YYYY-MM-DD HH:MM]

        Returns:
            Conversation context string or None if no history available
        """
        if not self.conversation_history:
            return None

        # Build conversation context (last N messages)
        recent_messages = list(self.conversation_history)[-max_messages:] if len(self.conversation_history) > max_messages else list(self.conversation_history)
        context_lines = ["Recent conversation history:"]

        for msg in recent_messages:
            sender_name = msg.sender.split(":")[0].replace("@", "")

            # Determine if sender is system or use real username
            if self.system_username and sender_name == self.system_username:
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

    async def login_callback(self, response: LoginResponse):
        if isinstance(response, LoginResponse):
            logger.log(f"Logged in as {response.user_id}")
        else:
            logger.log(f"Login failed: {response}")

    async def sync_callback(self, response: SyncResponse) -> None:
        logger.log(f"Sync completed")

    async def start(self):
        # Login
        response = await self.client.login(self.password)
        if not isinstance(response, LoginResponse):
            logger.log(f"Failed to login: {response}")
            return

        # Add callbacks
        self.client.add_event_callback(self.message_callback, RoomMessageText)

        logger.log("Starting Matrix bot...")

        # Start syncing
        await self.client.sync_forever(timeout=30000)

    async def stop(self):
        await self.client.close()

matrix_chat_bot = MatrixChatBot()