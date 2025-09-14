import os
import datetime
from typing import List

import aiohttp

from components.calendar import CalendarEvent
from components.logging_manager import logging_manager
from components.timezone_utils import now_user_tz
from components.weather import WeatherForecast

logger = logging_manager

HA_URL = os.getenv("HA_URL", "http://localhost:8123")
HA_TOKEN = os.getenv("HA_TOKEN")
HA_DEVICE_TRACKER_ENTITY = os.getenv("HA_DEVICE_TRACKER_ENTITY", "device_tracker.phone")
HA_WEATHER_ENTITY = os.getenv("HA_WEATHER_ENTITY", "weather.forecast_home")
HA_CALENDAR_ENTITY = os.getenv("HA_CALENDAR_ENTITY", "calendar.personal")


async def ha_request(method: str, endpoint: str, payload: dict = None) -> dict:
    """Generalized async request to Home Assistant API."""
    if not HA_TOKEN:
        logger.log("HA_TOKEN environment variable is required")
        raise ValueError("HA_TOKEN environment variable is required")

    url = f"{HA_URL}{endpoint}"
    headers = {
        "Authorization": f"Bearer {HA_TOKEN}",
        "Content-Type": "application/json"
    }

    async with aiohttp.ClientSession() as session:
        try:
            if method.upper() == "GET":
                async with session.get(url, headers=headers) as response:
                    data = await response.json(content_type=None)
                    return {"status": response.status, "data": data}
            elif method.upper() == "POST":
                async with session.post(url, json=payload, headers=headers) as response:
                    data = await response.json(content_type=None)
                    return {"status": response.status, "data": data}
            else:
                logger.log(f"Method {method} not allowed")
                return {"status": 405, "data": f"Method {method} not allowed"}
        except Exception as e:
            logger.log(f"Error making request to {endpoint}: {e}")
            return {"status": 500, "data": str(e)}

async def get_current_geofence_for_user() -> str:
    """Fetch the current geofence (zone) of the user from Home Assistant via the device tracker entity."""
    entity_id = HA_DEVICE_TRACKER_ENTITY
    logger.log(f"Fetching geofence for entity: {entity_id}")

    result = await ha_request("GET", f"/api/states/{entity_id}")
    if result["status"] == 200:
        geofence = result["data"].get("state", None)
        if geofence is not None:
            logger.log(f"Current geofence: {geofence}")
            return geofence
        else:
            logger.log("No geofence state found, user is on the way")
            return "on the way"
    elif result["status"] == 404:
        logger.log(f"Entity '{entity_id}' not found in Home Assistant")
        return f"Entity '{entity_id}' not found in Home Assistant."
    else:
        logger.log(f"Failed to fetch geofence: {result['status']} - {result['data']}")
        return f"Failed to fetch geofence: {result['status']} - {result['data']}"


async def get_weather_forecast_24h() -> List[WeatherForecast]:
    """Fetch the weather forecast for the next 24 hours.

    Returns hourly forecast data with:
    - datetime: ISO timestamp for each forecast hour
    - condition: weather condition (sunny, partlycloudy, cloudy, rainy, etc.)
    - temperature: temperature in Celsius (°C)
    - wind_speed: wind speed in km/h
    """
    entity_id = HA_WEATHER_ENTITY
    logger.log(f"Fetching 24h weather forecast for entity: {entity_id}")

    # Get forecast data using the weather.get_forecasts service with return_response parameter
    forecast_payload = {
        "entity_id": entity_id,
        "type": "hourly"
    }
    forecast_result = await ha_request("POST", "/api/services/weather/get_forecasts?return_response", forecast_payload)

    if forecast_result["status"] != 200:
        logger.log(f"Failed to fetch weather forecast: {forecast_result['status']} - {forecast_result['data']}")
        raise Exception(f"Failed to fetch weather forecast: {forecast_result['status']} - {forecast_result['data']}")

    forecast_data = []
    service_data = forecast_result["data"]

    if "service_response" in service_data and entity_id in service_data["service_response"]:
        entity_data = service_data["service_response"][entity_id]
        if "forecast" in entity_data:
            all_forecasts = entity_data["forecast"]
            limited_forecasts = all_forecasts[:24] if len(all_forecasts) >= 24 else all_forecasts

            for forecast in limited_forecasts:
                weather_forecast = WeatherForecast(
                    datetime=forecast.get("datetime"),
                    condition=forecast.get("condition"),
                    temperature=forecast.get("temperature"),
                    wind_speed=forecast.get("wind_speed")
                )
                forecast_data.append(weather_forecast)

                # Log each forecast entry in detail
                logger.log(f"  - {weather_forecast.datetime}: {weather_forecast.condition}, {weather_forecast.temperature}°C, wind {weather_forecast.wind_speed} km/h")

    logger.log(f"Retrieved {len(forecast_data)} weather forecast entries")
    return forecast_data


async def get_calendar_events_48h() -> List[CalendarEvent]:
    """Fetch users calendar events for the next 48 hours.
    If the time component of a calendar entry is missing, it is an all-day event.

    Returns calendar events with:
    - start: Event start datetime
    - end: Event end datetime
    - summary: Event title/summary
    - description: Event description (if available)
    - location: Event location (if available)
    """
    entity_id = HA_CALENDAR_ENTITY
    logger.log(f"Fetching 48h calendar events for entity: {entity_id}")

    now = now_user_tz()
    end_time = now + datetime.timedelta(hours=48)

    start_time_iso = now.isoformat()
    end_time_iso = end_time.isoformat()

    calendar_payload = {
        "entity_id": entity_id,
        "start_date_time": start_time_iso,
        "end_date_time": end_time_iso
    }
    calendar_result = await ha_request("POST", "/api/services/calendar/get_events?return_response", calendar_payload)

    if calendar_result["status"] != 200:
        logger.log(f"Failed to fetch calendar events: {calendar_result['status']} - {calendar_result['data']}")
        raise Exception(f"Failed to fetch calendar events: {calendar_result['status']} - {calendar_result['data']}")

    events_data = []
    service_data = calendar_result["data"]

    if "service_response" in service_data and entity_id in service_data["service_response"]:
        entity_data = service_data["service_response"][entity_id]
        if "events" in entity_data:
            events = entity_data["events"]

            for event in events:
                calendar_event = CalendarEvent(
                    start=event.get("start"),
                    end=event.get("end"),
                    summary=event.get("summary"),
                    description=event.get("description"),
                    location=event.get("location")
                )
                events_data.append(calendar_event)

                # Log each event in detail
                event_info = f"Event: {calendar_event.summary} ({calendar_event.start} - {calendar_event.end})"
                if calendar_event.location:
                    event_info += f" at {calendar_event.location}"
                logger.log(f"  - {event_info}")

    logger.log(f"Retrieved {len(events_data)} calendar events")
    return events_data
