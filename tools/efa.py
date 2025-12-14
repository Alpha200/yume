"""
Tools for EFA (Elektronisches Fahrplanauskun ftssystem) public transport queries.
Provides functions to query departure times and information for public transport stations.
"""

import logging
from typing import Optional

from agents import function_tool
from services.efa import (
    get_departures_json,
    get_journeys,
    get_station_id,
)

logger = logging.getLogger(__name__)


async def _resolve_station_identifier(name_or_id: str) -> str:
    """Resolve human-readable station name to EFA station ID when possible."""
    if not name_or_id:
        return name_or_id

    lowered = name_or_id.lower()
    if lowered.startswith("de:") or lowered.startswith("coord:"):
        return name_or_id

    station_id = await get_station_id(name_or_id)
    return station_id or name_or_id


def _infer_station_type(identifier: str) -> str:
    """Infer station type parameter for EFA trip requests."""
    if not identifier:
        return "any"
    lowered = identifier.lower()
    if lowered.startswith("de:"):
        return "stop"
    if lowered.startswith("coord:"):
        return "coord"
    return "any"


@function_tool
async def get_station_departures(
    station_name: str,
    limit: int = 10,
    line_query: str = None,
    direction_query: str = None
) -> str:
    """
    Get upcoming departures for a public transport station.
    Supports filtering by line number/name and destination direction.
    
    Args:
        station_name: The name of the station (e.g., "Essen Hauptbahnhof")
        limit: Maximum number of departures to return (default: 10)
        line_query: Optional filter by line (e.g., "U47", "RB33", "ICE"). Substring match.
        direction_query: Optional filter by destination (e.g., "Berlin", "Köln"). Substring match.
        
    Returns:
        Formatted string with departure information
    """
    try:
        result = await get_departures_json(
            station_name=station_name,
            limit=limit,
            line_query=line_query,
            direction_query=direction_query
        )
        
        if result["status"] == "no_departures":
            filters = []
            if line_query:
                filters.append(f"line '{line_query}'")
            if direction_query:
                filters.append(f"direction '{direction_query}'")
            
            if filters:
                return f"No departures found for {station_name} with {' and '.join(filters)}"
            else:
                return f"No upcoming departures found for {station_name}"
        
        # Format the departures
        formatted = f"📍 Departures from {station_name}:\n"
        
        if line_query or direction_query:
            filters = []
            if line_query:
                filters.append(f"line {line_query}")
            if direction_query:
                filters.append(f"to {direction_query}")
            if filters:
                formatted = f"📍 Departures from {station_name} ({', '.join(filters)}):\n"
        
        for i, dep in enumerate(result["departures"], 1):
            line = dep.get("line", "N/A")
            destination = dep.get("destination", "Unknown")
            planned_time = dep.get("planned_time", "N/A")
            estimated_time = dep.get("estimated_time")
            delay = dep.get("delay_minutes", 0)
            platform = dep.get("platform", "—")
            realtime = "🔄" if dep.get("realtime") else "ℹ️"
            transport_type = dep.get("transport_type", "")
            
            # Build the departure line
            time_str = planned_time
            if estimated_time and estimated_time != planned_time:
                delay_str = f"+{delay} min" if delay > 0 else f"{delay} min"
                time_str = f"{planned_time} ({estimated_time}, {delay_str})"
            
            formatted += f"{i}. {line} {transport_type} to {destination} at {time_str} | Platform {platform} {realtime}\n"
        
        return formatted
        
    except Exception as e:
        logger.error(f"Exception fetching departures: {type(e).__name__}: {e}")
        return f"Error fetching departures for {station_name}: {str(e)}"


@function_tool
async def get_journey_options(
    origin: str,
    destination: str,
    limit: int = 3,
    via: Optional[str] = None
) -> str:
    """Fetch journey plans with detailed steps between two public transport stations.

    Args:
        origin: The starting station name or identifier (e.g., "Essen Hauptbahnhof"
            or "de:2892" for station ID). Supports human-readable station names which
            are automatically resolved to station IDs.
        destination: The destination station name or identifier. Same format as origin.
        limit: Maximum number of journey options to return (default: 3). Minimum is 1.
        via: Optional intermediate station to route through. Uses same format as origin
            and destination. If provided, all journeys will pass through this station.

    Returns:
        A formatted string containing journey options with the following details for
        each journey:
        - Total duration in minutes
        - Each leg (step) of the journey with:
          * Transport mode and line number (e.g., "U-Bahn U47", "S-Bahn S6")
          * Origin and destination stations with platform information
          * Planned and estimated departure/arrival times
          * Delay information in minutes (if applicable)
          * Duration of the leg in minutes

        Returns a message if no journeys are found or an error occurs.
    """
    if not origin or not destination:
        return "Origin and destination are both required to search for journeys."

    try:
        resolved_origin = await _resolve_station_identifier(origin)
        resolved_destination = await _resolve_station_identifier(destination)
        resolved_via = await _resolve_station_identifier(via) if via else None

        journeys = await get_journeys(
            origin=resolved_origin,
            destination=resolved_destination,
            origin_type=_infer_station_type(resolved_origin),
            destination_type=_infer_station_type(resolved_destination),
            via=resolved_via,
            via_type=_infer_station_type(resolved_via) if resolved_via else "any",
            limit=max(limit, 1)
        )

        if not journeys:
            via_str = f" via {via}" if via else ""
            return f"No journeys found from {origin} to {destination}{via_str}."

        formatted = f"Journeys from {origin} to {destination}"
        if via:
            formatted += f" via {via}"
        formatted += ":\n"

        for idx, journey in enumerate(journeys, 1):
            length = journey.length_minutes
            formatted += f"\nOPTION {idx}: Total duration {length} minutes\n"

            for step_idx, step in enumerate(journey.steps, 1):
                mode = step.mode
                line = step.line
                origin_name = step.origin
                destination_name = step.destination
                dep = step.departure_planned
                dep_est = step.departure_estimated
                arr = step.arrival_planned
                arr_est = step.arrival_estimated
                dep_delay = step.departure_delay_minutes
                arr_delay = step.arrival_delay_minutes
                platform_dep = step.platform_origin
                platform_arr = step.platform_destination
                duration = step.duration_minutes

                formatted += f"\nStep {step_idx}:\n"

                # Transport line information
                if line:
                    formatted += f"  Line: {mode} {line}\n"
                else:
                    formatted += f"  Mode: {mode}\n"

                # Check if origin and destination are the same (walk within station)
                if origin_name == destination_name:
                    formatted += f"  Location: {origin_name}\n"
                    formatted += f"  Action: Walk to another platform or transfer point in {origin_name}\n"
                else:
                    formatted += f"  From: {origin_name}"
                    if platform_dep:
                        formatted += f" (Platform {platform_dep})"
                    formatted += "\n"
                    formatted += f"  To: {destination_name}"
                    if platform_arr:
                        formatted += f" (Platform {platform_arr})"
                    formatted += "\n"

                # Departure time
                if dep:
                    formatted += f"  Depart: {dep}"
                    if dep_est and dep_est != dep:
                        delay_str = f"+{dep_delay}" if dep_delay and dep_delay > 0 else f"{dep_delay}"
                        formatted += f" → Estimated: {dep_est} ({delay_str} min delay)"
                    formatted += "\n"

                # Arrival time
                if arr:
                    formatted += f"  Arrive: {arr}"
                    if arr_est and arr_est != arr:
                        delay_str = f"+{arr_delay}" if arr_delay and arr_delay > 0 else f"{arr_delay}"
                        formatted += f" → Estimated: {arr_est} ({delay_str} min delay)"
                    formatted += "\n"

                # Duration
                if duration:
                    formatted += f"  Duration: {duration} minutes\n"

        return formatted.strip()

    except Exception as e:
        logger.error(f"Exception fetching journeys: {type(e).__name__}: {e}")
        return f"Error fetching journeys from {origin} to {destination}: {str(e)}"
