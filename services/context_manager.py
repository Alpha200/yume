from dataclasses import dataclass
from datetime import datetime
from typing import List

from components.calendar import CalendarEvent
from components.conversation import ConversationEntry
from components.logging_manager import logging_manager
from components.timezone_utils import now_user_tz
from components.weather import WeatherForecast

logger = logging_manager

@dataclass
class AIContext:
    forecast: List[WeatherForecast]
    user_location: str
    calendar_entries: List[CalendarEvent]
    chat_history: List[ConversationEntry]


async def build_ai_context(matrix_bot=None, home_assistant_module=None, max_chat_messages: int = 10) -> AIContext:
    """Build AIContext by collecting data from matrix_bot and home_assistant services"""
    logger.log("Building AIContext from external services")

    # Initialize empty lists/defaults
    forecast = []
    user_location = "unknown"
    calendar_entries = []
    chat_history = []

    # Get weather forecast from home assistant
    if home_assistant_module:
        try:
            forecast = await home_assistant_module.get_weather_forecast_24h()
            logger.log(f"Retrieved {len(forecast)} weather forecast entries")
        except Exception as e:
            logger.log(f"Failed to get weather forecast: {e}")

        try:
            user_location = await home_assistant_module.get_current_geofence_for_user()
            logger.log(f"User location: {user_location}")
        except Exception as e:
            logger.log(f"Failed to get user location: {e}")

        try:
            calendar_entries = await home_assistant_module.get_calendar_events_48h()
            logger.log(f"Retrieved {len(calendar_entries)} calendar events")
        except Exception as e:
            logger.log(f"Failed to get calendar events: {e}")

    # Get chat history from matrix bot
    if matrix_bot and hasattr(matrix_bot, 'conversation_history'):
        try:
            # Get recent messages from the bot's conversation history
            recent_messages = list(matrix_bot.conversation_history)[-max_chat_messages:] if len(matrix_bot.conversation_history) > max_chat_messages else list(matrix_bot.conversation_history)
            chat_history = recent_messages
            logger.log(f"Retrieved {len(chat_history)} chat history entries")
        except Exception as e:
            logger.log(f"Failed to get chat history: {e}")

    # Create and store the AIContext
    current_context = AIContext(
        forecast=forecast,
        user_location=user_location,
        calendar_entries=calendar_entries,
        chat_history=chat_history
    )

    logger.log("AIContext built successfully")
    return current_context

def build_context_text(context: AIContext, include_chat_history: bool = True, max_chat_messages: int = 10) -> str:
    """Build a text representation of the AIContext for use in prompts or other text-based systems"""

    # Build datetime context
    now = now_user_tz()
    text_parts = [
        f"Current date and time: {now.strftime('%A, %B %d, %Y at %H:%M')} ({now.tzinfo})",
        ""
    ]

    # User location
    if context.user_location and context.user_location != "unknown":
        text_parts.extend([
            f"User location: {context.user_location}",
            ""
        ])

    # Weather forecast
    if context.forecast:
        text_parts.append("Weather forecast (next 24 hours):")
        for i, weather in enumerate(context.forecast[:8]):  # Show first 8 hours for brevity
            weather_time = datetime.fromisoformat(weather.datetime.replace('Z', '+00:00')).strftime('%H:%M')
            text_parts.append(f"  {weather_time}: {weather.condition}, {weather.temperature}°C, wind {weather.wind_speed} km/h")
        if len(context.forecast) > 8:
            text_parts.append(f"  ... and {len(context.forecast) - 8} more forecast entries")
        text_parts.append("")

    # Calendar events
    if context.calendar_entries:
        text_parts.append("Upcoming calendar events (next 48 hours):")
        for event in context.calendar_entries:
            event_text = f"  {event.summary}"
            if event.start and event.end:
                # Parse datetime strings and format them
                try:
                    start_dt = datetime.fromisoformat(event.start.replace('Z', '+00:00'))
                    end_dt = datetime.fromisoformat(event.end.replace('Z', '+00:00'))
                    event_text += f" ({start_dt.strftime('%m/%d %H:%M')} - {end_dt.strftime('%H:%M')})"
                except:
                    event_text += f" ({event.start} - {event.end})"
            if event.location:
                event_text += f" at {event.location}"
            text_parts.append(event_text)
        text_parts.append("")

    # Chat history
    if include_chat_history and context.chat_history:
        text_parts.append("Recent conversation history:")
        recent_messages = context.chat_history[-max_chat_messages:] if len(context.chat_history) > max_chat_messages else context.chat_history

        for msg in recent_messages:
            sender_name = msg.sender.split(":")[0].replace("@", "")

            text_parts.append(f"{sender_name}: {msg.message}")
        text_parts.append("")

    # Add instruction for AI
    if include_chat_history and context.chat_history:
        text_parts.append("Please respond to the most recent message considering this full context.")
    else:
        text_parts.append("Please provide assistance based on the available context.")

    result = "\n".join(text_parts)
    return result