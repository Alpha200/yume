import os
import datetime
from typing import List, Optional
from dataclasses import dataclass

import aiohttp

from components.calendar import CalendarEvent
from components.logging_manager import logging_manager
from components.timezone_utils import now_user_tz, from_isoformat_user_tz, to_user_tz
from components.weather import WeatherForecast

logger = logging_manager

HA_URL = os.getenv("HA_URL", "http://localhost:8123")
HA_TOKEN = os.getenv("HA_TOKEN")
HA_DEVICE_TRACKER_ENTITY = os.getenv("HA_DEVICE_TRACKER_ENTITY", "device_tracker.phone")
HA_WEATHER_ENTITY = os.getenv("HA_WEATHER_ENTITY", "weather.forecast_home")
HA_CALENDAR_ENTITY = os.getenv("HA_CALENDAR_ENTITY", "calendar.personal")
HA_PROXIMITY_ENTITY = os.getenv("HA_PROXIMITY_ENTITY", "sensor.proximity_home_distance")
HA_HOME_GEOFENCE = os.getenv("HA_HOME_GEOFENCE", "home")


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

async def get_proximity_distance() -> str:
    """Fetch the proximity distance from Home Assistant proximity entity.

    Returns the distance as a string (e.g., "42 km", "150 m", etc.)
    or an empty string if the entity is not available.
    """
    entity_id = HA_PROXIMITY_ENTITY
    logger.log(f"Fetching proximity distance for entity: {entity_id}")

    result = await ha_request("GET", f"/api/states/{entity_id}")
    if result["status"] == 200:
        data = result["data"]
        state = data.get("state", None)

        # The state of a proximity entity is the distance value
        if state is not None and state != "unknown":
            logger.log(f"Proximity distance: {state}")
            return str(state)
        else:
            logger.log("Proximity state is unknown")
            return ""
    elif result["status"] == 404:
        logger.log(f"Proximity entity '{entity_id}' not found in Home Assistant")
        return ""
    else:
        logger.log(f"Failed to fetch proximity: {result['status']} - {result['data']}")
        return ""


async def get_current_geofence_for_user() -> str:
    """Fetch the current geofence (zone) of the user from Home Assistant via the device tracker entity.

    If not in the home geofence, appends the proximity distance to provide context.
    """
    entity_id = HA_DEVICE_TRACKER_ENTITY
    logger.log(f"Fetching geofence for entity: {entity_id}")

    result = await ha_request("GET", f"/api/states/{entity_id}")
    if result["status"] == 200:
        geofence = result["data"].get("state", None)
        if geofence is not None:
            # If user is not at home, fetch proximity distance
            if geofence.lower() != HA_HOME_GEOFENCE.lower():
                proximity_distance = await get_proximity_distance()
                if proximity_distance:
                    geofence_with_distance = f"{geofence} ({proximity_distance} away)"
                    logger.log(f"Current geofence: {geofence_with_distance}")
                    return geofence_with_distance

            logger.log(f"Current geofence: {geofence}")
            return geofence
        else:
            logger.log("No geofence state found, user is on the way")
            # Fetch proximity distance when on the way
            proximity_distance = await get_proximity_distance()
            if proximity_distance:
                on_the_way_with_distance = f"on the way ({proximity_distance} away)"
                logger.log(f"Current status: {on_the_way_with_distance}")
                return on_the_way_with_distance
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
                # Detect if this is an all-day event (start/end are dates without time component)
                start_str = event.get("start", "")
                is_all_day = len(start_str) == 10  # Format: YYYY-MM-DD for all-day events

                calendar_event = CalendarEvent(
                    start=start_str,
                    end=event.get("end"),
                    summary=event.get("summary"),
                    description=event.get("description"),
                    location=event.get("location"),
                    is_all_day=is_all_day
                )
                events_data.append(calendar_event)

                # Log each event in detail
                event_info = f"Event: {calendar_event.summary} ({calendar_event.start} - {calendar_event.end})"
                if calendar_event.location:
                    event_info += f" at {calendar_event.location}"
                logger.log(f"  - {event_info}")

    logger.log(f"Retrieved {len(events_data)} calendar events")
    return events_data


async def get_calendar_events_for_day(date: datetime.date) -> List[CalendarEvent]:
    """Fetch calendar events for a specific day.
    
    Args:
        date: The date to fetch events for
        
    Returns:
        List of calendar events for that day
    """
    entity_id = HA_CALENDAR_ENTITY
    logger.log(f"Fetching calendar events for {date} for entity: {entity_id}")

    # Set start time to beginning of the day
    start_time = datetime.datetime.combine(date, datetime.time.min)
    start_time = to_user_tz(start_time)
    
    # Set end time to end of the day
    end_time = datetime.datetime.combine(date, datetime.time.max)
    end_time = to_user_tz(end_time)

    start_time_iso = start_time.isoformat()
    end_time_iso = end_time.isoformat()

    calendar_payload = {
        "entity_id": entity_id,
        "start_date_time": start_time_iso,
        "end_date_time": end_time_iso
    }
    calendar_result = await ha_request("POST", "/api/services/calendar/get_events?return_response", calendar_payload)

    if calendar_result["status"] != 200:
        logger.log(f"Failed to fetch calendar events: {calendar_result['status']} - {calendar_result['data']}")
        return []  # Return empty list on error instead of raising

    events_data = []
    service_data = calendar_result["data"]

    if "service_response" in service_data and entity_id in service_data["service_response"]:
        entity_data = service_data["service_response"][entity_id]
        if "events" in entity_data:
            events = entity_data["events"]

            for event in events:
                # Detect if this is an all-day event
                start_str = event.get("start", "")
                is_all_day = len(start_str) == 10

                calendar_event = CalendarEvent(
                    start=start_str,
                    end=event.get("end"),
                    summary=event.get("summary"),
                    description=event.get("description"),
                    location=event.get("location"),
                    is_all_day=is_all_day
                )
                events_data.append(calendar_event)

    logger.log(f"Retrieved {len(events_data)} calendar events for {date}")
    return events_data
