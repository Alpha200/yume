import logging
from nio import AsyncClient, MatrixRoom, RoomMessageText, LoginResponse, SyncResponse
from datetime import datetime
import os
from services.chat_message_manager import chat_message_manager

logger = logging.getLogger(__name__)

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

        logger.debug(f"Initializing MatrixChatBot with homeserver: {self.homeserver}, user: {self.username}, room: {self.room_id}")

        self.client = AsyncClient(self.homeserver, self.username)

        # Store the start time to filter out old messages
        self.start_time = datetime.now()

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

            logger.debug(f"Received message from {event.sender} in {room.room_id}: {event.body}")

            # Convert server timestamp (milliseconds) to ISO format
            msg_timestamp = datetime.fromtimestamp(event.server_timestamp / 1000).isoformat()

            # Only respond if message is not from us
            if event.sender == self.client.user_id:
                # Save our own message to MongoDB
                chat_message_manager.save_message(
                    message_id=event.event_id,
                    sender=event.sender,
                    message=event.body,
                    timestamp=msg_timestamp
                )
                return

            try:
                from services.ai_engine import handle_chat_message
                await handle_chat_message(message=event.body)
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                return  # Do nothing on error

            # Save user message to MongoDB AFTER AI processing so it's not included in AI context
            chat_message_manager.save_message(
                message_id=event.event_id,
                sender=event.sender,
                message=event.body,
                timestamp=msg_timestamp
            )

        except Exception as e:
            logger.error(f"Unhandled error in _handle_message: {e}")
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
                logger.error(f"Failed to send error message: {send_error}")

    async def send_message(self, message: str):
        """Send a message to the configured Matrix room"""
        try:
            response = await self.client.room_send(
                room_id=self.room_id,
                message_type="m.room.message",
                content={
                    "msgtype": "m.text",
                    "body": message
                }
            )

            # Save the message to MongoDB with the event ID from the response
            if hasattr(response, 'event_id'):
                chat_message_manager.save_message(
                    message_id=response.event_id,
                    sender=self.client.user_id,
                    message=message,
                    timestamp=datetime.now().isoformat()
                )

            # Don't add message to history here - it will be added when the message
            # comes back from the Matrix server in the _handle_message callback
            # This prevents duplicate messages in the conversation history

            logger.info(f"Sent message to {self.room_id}: {message}")

        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            # Don't re-raise the exception to prevent crashing the calling function
            return

    async def login_callback(self, response: LoginResponse):
        if isinstance(response, LoginResponse):
            logger.info(f"Logged in as {response.user_id}")
        else:
            logger.error(f"Login failed: {response}")

    async def sync_callback(self, response: SyncResponse) -> None:
        logger.debug(f"Sync completed")

    async def start(self):
        # Login
        response = await self.client.login(self.password)
        if not isinstance(response, LoginResponse):
            logger.error(f"Failed to login: {response}")
            return

        # Add callbacks
        self.client.add_event_callback(self.message_callback, RoomMessageText)

        logger.info("Starting Matrix bot...")

        # Start syncing
        await self.client.sync_forever(timeout=30000)

    async def stop(self):
        await self.client.close()

matrix_chat_bot = MatrixChatBot()