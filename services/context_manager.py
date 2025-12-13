import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List

from components.calendar import CalendarEvent
from components.conversation import ConversationEntry
from components.timezone_utils import now_user_tz
from components.weather import WeatherForecast
from services.chat_message_manager import chat_message_manager
from services.home_assistant import get_weather_forecast_24h, get_current_geofence_for_user, get_calendar_events_48h
from services.day_planner import day_planner_service

logger = logging.getLogger(__name__)

@dataclass
class AIContext:
    forecast: List[WeatherForecast]
    user_location: str
    calendar_entries: List[CalendarEvent]
    chat_history: List[ConversationEntry]


async def build_ai_context(max_chat_messages: int = 10) -> AIContext:
    """Build AIContext by collecting data from matrix_bot and home_assistant services"""
    logger.info("Building AIContext from external services")

    # Initialize empty lists/defaults
    forecast = []
    user_location = "unknown"
    calendar_entries = []
    chat_history = []

    # Get weather forecast from home assistant
    try:
        forecast = await get_weather_forecast_24h()
        logger.debug(f"Retrieved {len(forecast)} weather forecast entries")
    except Exception as e:
        logger.error(f"Failed to get weather forecast: {e}")

    try:
        user_location = await get_current_geofence_for_user()
        logger.debug(f"User location: {user_location}")
    except Exception as e:
        logger.error(f"Failed to get user location: {e}")

    try:
        calendar_entries = await get_calendar_events_48h()
        logger.debug(f"Retrieved {len(calendar_entries)} calendar events")
    except Exception as e:
        logger.error(f"Failed to get calendar events: {e}")

    try:
        # Get recent messages from MongoDB chat history
        recent_messages = chat_message_manager.get_recent_messages(limit=max_chat_messages)
        chat_history = [ConversationEntry(sender=msg.sender, message=msg.message, timestamp=msg.timestamp) for msg in recent_messages]
        logger.debug(f"Retrieved {len(chat_history)} chat history entries")
    except Exception as e:
        logger.error(f"Failed to get chat history: {e}")

    # Create and store the AIContext
    current_context = AIContext(
        forecast=forecast,
        user_location=user_location,
        calendar_entries=calendar_entries,
        chat_history=chat_history
    )

    logger.info("AIContext built successfully")
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
            f"The user is currently at the following location: {context.user_location}",
            ""
        ])

    # Weather forecast
    if context.forecast:
        text_parts.append("Weather forecast (next 12 hours):")
        for i, weather in enumerate(context.forecast[:12]):  # Show first 12 hours for brevity
            weather_time = datetime.fromisoformat(weather.datetime.replace('Z', '+00:00')).strftime('%H:%M')
            text_parts.append(f"{weather_time}: {weather.condition}, {weather.temperature}°C, wind speed: {weather.wind_speed} km/h")
        text_parts.append("")

    # Day plans for today and tomorrow
    try:
        today = now_user_tz().date()
        tomorrow = today + timedelta(days=1)
        
        today_plan = day_planner_service.get_formatted_plan(today)
        tomorrow_plan = day_planner_service.get_formatted_plan(tomorrow)
        
        text_parts.append("Day Plan for Today:")
        text_parts.append(today_plan)
        text_parts.append("")
        
        text_parts.append("Day Plan for Tomorrow:")
        text_parts.append(tomorrow_plan)
        text_parts.append("")
    except Exception as e:
        logger.error(f"Failed to get day plans: {e}")

    # Chat history
    if include_chat_history and context.chat_history:
        text_parts.append("Recent conversation history:")
        recent_messages = context.chat_history[-max_chat_messages:] if len(context.chat_history) > max_chat_messages else context.chat_history

        for msg in recent_messages:
            sender_name = msg.sender.split(":")[0].replace("@", "")

            # Parse and format the timestamp with date, time, and seconds
            try:
                msg_time = datetime.fromisoformat(msg.timestamp).strftime("%m/%d %H:%M:%S")
                text_parts.append(f"[{msg_time}] {sender_name}: {msg.message}")
            except:
                # Fallback if timestamp parsing fails
                text_parts.append(f"{sender_name}: {msg.message}")
        text_parts.append("")

    result = "\n".join(text_parts)
    return result