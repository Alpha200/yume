"""
Tools for EFA (Elektronisches Fahrplanauskun ftssystem) public transport queries.
Provides functions to query departure times and information for public transport stations.
"""

from agents import function_tool
from services.efa import get_departures_json
from components.logging_manager import logging_manager

logger = logging_manager


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
        logger.log(f"[TOOL] ERROR - Exception fetching departures: {type(e).__name__}: {e}")
        return f"Error fetching departures for {station_name}: {str(e)}"
