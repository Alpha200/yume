from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List

from components.calendar import CalendarEvent
from components.conversation import ConversationEntry
from components.logging_manager import logging_manager
from components.timezone_utils import now_user_tz
from components.weather import WeatherForecast
from services.matrix_bot import matrix_chat_bot
from services.home_assistant import get_weather_forecast_24h, get_current_geofence_for_user, get_calendar_events_48h

logger = logging_manager

@dataclass
class AIContext:
    forecast: List[WeatherForecast]
    user_location: str
    calendar_entries: List[CalendarEvent]
    chat_history: List[ConversationEntry]


async def build_ai_context(max_chat_messages: int = 10) -> AIContext:
    """Build AIContext by collecting data from matrix_bot and home_assistant services"""
    logger.log("Building AIContext from external services")

    # Initialize empty lists/defaults
    forecast = []
    user_location = "unknown"
    calendar_entries = []
    chat_history = []

    # Get weather forecast from home assistant
    try:
        forecast = await get_weather_forecast_24h()
        logger.log(f"Retrieved {len(forecast)} weather forecast entries")
    except Exception as e:
        logger.log(f"Failed to get weather forecast: {e}")

    try:
        user_location = await get_current_geofence_for_user()
        logger.log(f"User location: {user_location}")
    except Exception as e:
        logger.log(f"Failed to get user location: {e}")

    try:
        calendar_entries = await get_calendar_events_48h()
        logger.log(f"Retrieved {len(calendar_entries)} calendar events")
    except Exception as e:
        logger.log(f"Failed to get calendar events: {e}")

    try:
        # Get recent messages from the bot's conversation history
        recent_messages = list(matrix_chat_bot.conversation_history)[-max_chat_messages:] if len(matrix_chat_bot.conversation_history) > max_chat_messages else list(matrix_chat_bot.conversation_history)
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
        text_parts.append("Weather forecast (next 12 hours):")
        for i, weather in enumerate(context.forecast[:12]):  # Show first 12 hours for brevity
            weather_time = datetime.fromisoformat(weather.datetime.replace('Z', '+00:00')).strftime('%H:%M')
            text_parts.append(f"{weather_time}: {weather.condition}, {weather.temperature}°C, wind speed: {weather.wind_speed} km/h")
        text_parts.append("")

    # Calendar events
    if context.calendar_entries:
        text_parts.append("Upcoming calendar events (next 48 hours):")
        now = now_user_tz()
        today = now.date()
        tomorrow = (now + timedelta(days=1)).date()

        for event in context.calendar_entries:
            event_text = f"  {event.summary}"
            if event.start and event.end:
                # Handle all-day events differently from timed events
                if event.is_all_day:
                    try:
                        start_date = datetime.fromisoformat(event.start).date()
                        if start_date == today:
                            event_text += f" (all day today)"
                        elif start_date == tomorrow:
                            event_text += f" (all day tomorrow)"
                        else:
                            event_text += f" (all day on {start_date.strftime('%m/%d')})"
                    except:
                        event_text += f" (all day)"
                else:
                    # Parse datetime strings and format them for timed events
                    try:
                        start_dt = datetime.fromisoformat(event.start.replace('Z', '+00:00'))
                        end_dt = datetime.fromisoformat(event.end.replace('Z', '+00:00'))
                        start_date = start_dt.date()

                        if start_date == today:
                            day_str = "today"
                        elif start_date == tomorrow:
                            day_str = "tomorrow"
                        else:
                            day_str = start_dt.strftime('%m/%d')

                        event_text += f" ({day_str} {start_dt.strftime('%H:%M')} - {end_dt.strftime('%H:%M')})"
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

    result = "\n".join(text_parts)
    return result