import os
import aiohttp
from typing import Optional, List, Dict, Any
from datetime import datetime
from dataclasses import dataclass

from components.logging_manager import logging_manager

logger = logging_manager

# EFA API configuration
EFA_API_URL = os.getenv("EFA_API_URL", "http://api.example.com")
EFA_CLIENT_ID = os.getenv("EFA_CLIENT_ID", "CLIENTID")
EFA_CLIENT_NAME = os.getenv("EFA_CLIENT_NAME", "yume")


@dataclass
class PublicTransportDeparture:
    """Information about a public transport departure"""
    line: str  # Line number/name (e.g., "U6", "S1")
    destination: str  # Destination station
    planned_time: str  # Planned departure time (HH:MM)
    estimated_time: Optional[str]  # Estimated departure time (HH:MM)
    delay_minutes: Optional[int]  # Delay in minutes
    transport_type: str  # Type of transport (U-Bahn, S-Bahn, Tram, Bus)
    platform: Optional[str]  # Platform number
    realtime: bool  # Whether realtime data is available
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "line": self.line,
            "destination": self.destination,
            "planned_time": self.planned_time,
            "estimated_time": self.estimated_time,
            "delay_minutes": self.delay_minutes,
            "transport_type": self.transport_type,
            "platform": self.platform,
            "realtime": self.realtime
        }


async def efa_request(endpoint: str, params: dict = None) -> dict:
    """Make a request to the EFA API."""
    if not EFA_API_URL or EFA_API_URL == "http://api.example.com":
        logger.log("EFA_API_URL environment variable is required")
        raise ValueError("EFA_API_URL environment variable is required")

    url = f"{EFA_API_URL}{endpoint}"
    
    # Add default EFA parameters
    if params is None:
        params = {}
    
    params.setdefault("clientID", EFA_CLIENT_ID)
    params.setdefault("clientName", EFA_CLIENT_NAME)
    params.setdefault("outputFormat", "rapidJSON")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json(content_type=None)
                    return {"status": response.status, "data": data}
                else:
                    error_text = await response.text()
                    logger.log(f"EFA API error {response.status}: {error_text}")
                    return {"status": response.status, "data": error_text}
    except Exception as e:
        logger.log(f"Error making EFA request to {url}: {e}")
        return {"status": 500, "data": str(e)}


async def get_station_id(station_name: str) -> Optional[str]:
    """
    Get the station ID from a station name using EFA stopfinder.
    
    Args:
        station_name: Name of the station (e.g., "Central Station")
    
    Returns:
        Station ID or None if not found
    """
    logger.log(f"Searching for station: {station_name}")
    
    result = await efa_request(
        "/XML_STOPFINDER_REQUEST",
        params={
            "name_sf": station_name,
            "type_sf": "any"
        }
    )
    
    if result["status"] == 200:
        data = result["data"]
        
        # EFA rapidJSON returns locations array
        locations = data.get("locations", [])
        
        if locations:
            # Filter for actual stops (type="stop"), prefer best matches
            stops = [loc for loc in locations if loc.get("type") == "stop"]
            
            if stops:
                # Sort by matchQuality (descending) and get the best match
                stops.sort(key=lambda x: x.get("matchQuality", 0), reverse=True)
                best_stop = stops[0]
                station_id = best_stop.get("id")
                logger.log(f"Found station ID for '{station_name}': {station_id}")
                return station_id
            else:
                # If no stops found, try any location
                locations.sort(key=lambda x: x.get("matchQuality", 0), reverse=True)
                station_id = locations[0].get("id")
                logger.log(f"Found location ID for '{station_name}': {station_id}")
                return station_id
        else:
            logger.log(f"Station '{station_name}' not found")
            return None
    else:
        logger.log(f"Failed to search station: {result['status']}")
        return None


async def get_serving_lines(station_id: str) -> List[Dict[str, Any]]:
    """
    Get all serving lines for a station.
    
    Args:
        station_id: EFA station ID
    
    Returns:
        List of line dictionaries with id, name, number, and destination
    """
    logger.log(f"Fetching serving lines for station: {station_id}")
    
    result = await efa_request(
        "/XML_SERVINGLINES_REQUEST",
        params={
            "name_sl": station_id,
            "type_sl": "stop",
            "deleteAssignedStops_sl": "1",
            "lineReqType": "1",
            "lsShowTrainsExplicit": "1",
            "mergeDir": "false",
            "mode": "odv",
            "sl3plusServingLinesMacro": "1",
            "withoutTrains": "0",
            "language": "de",
            "version": "11.0.6.72"
        }
    )
    
    if result["status"] == 200:
        data = result["data"]
        lines = data.get("lines", [])
        logger.log(f"Found {len(lines)} serving lines")
        return lines
    else:
        logger.log(f"Failed to fetch serving lines: {result['status']}")
        return []


async def find_line_id(station_id: str, line_query: str) -> Optional[str]:
    """
    Find a line ID by searching for line number or name.
    Performs case-insensitive substring matching for flexibility.
    
    Args:
        station_id: EFA station ID
        line_query: Search string (e.g., "U47", "RB33", "ICE")
    
    Returns:
        Line ID or None if not found
    """
    lines = await get_serving_lines(station_id)
    query_lower = line_query.lower()
    
    for line in lines:
        # Check if query matches any line identifier fields (case-insensitive substring match)
        number = (line.get("number") or "").lower()
        disassembled = (line.get("disassembledName") or "").lower()
        name = (line.get("name") or "").lower()
        product_name = (line.get("product", {}).get("name") or "").lower()
        
        # Check if query is contained in any of these fields
        if (query_lower in number or
            query_lower in disassembled or
            query_lower in name or
            query_lower in product_name):
            line_id = line.get("id")
            matched_field = ""
            if query_lower in number:
                matched_field = f"number '{number}'"
            elif query_lower in disassembled:
                matched_field = f"disassembled name '{disassembled}'"
            else:
                matched_field = "line info"
            logger.log(f"Found line ID for '{line_query}' (matched {matched_field}): {line_id}")
            return line_id
    
    logger.log(f"Line matching '{line_query}' not found at station {station_id}")
    return None


def _get_line_identifier(line: Dict[str, Any]) -> str:
    """Extract the best identifier for a line (number, disassembledName, or name)."""
    return (line.get("number") or 
            line.get("disassembledName") or 
            line.get("name") or 
            "Unknown")


def _parse_departure_time(time_str: Optional[str]) -> Optional[str]:
    """Parse time string to HH:MM format."""
    if not time_str:
        return None
    # EFA typically returns time as HHMM (4 digits)
    if len(time_str) == 4:
        return f"{time_str[:2]}:{time_str[2:]}"
    return time_str


def _parse_departure_time_iso(time_str: Optional[str]) -> Optional[str]:
    """Parse ISO timestamp to HH:MM format (e.g., '2025-12-11T18:54:00Z' -> '18:54')."""
    if not time_str:
        return None
    try:
        # Parse ISO format timestamp
        dt = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
        return dt.strftime("%H:%M")
    except (ValueError, AttributeError):
        return None


def _calculate_delay(planned_time: Optional[str], estimated_time: Optional[str]) -> Optional[int]:
    """Calculate delay in minutes from planned and estimated times."""
    if not planned_time or not estimated_time:
        return None
    
    try:
        planned = datetime.strptime(planned_time, "%H:%M")
        estimated = datetime.strptime(estimated_time, "%H:%M")
        delay = int((estimated - planned).total_seconds() / 60)
        return max(0, delay)  # Return 0 if no delay
    except (ValueError, TypeError):
        return None


async def get_departures(
    station_id: Optional[str] = None,
    station_name: Optional[str] = None,
    limit: int = 10,
    line_query: Optional[str] = None,
    direction_query: Optional[str] = None
) -> List[PublicTransportDeparture]:
    """
    Get departures for a station, optionally filtered by line and/or direction.
    
    Args:
        station_id: EFA station ID (if known)
        station_name: Station name (will be looked up if station_id not provided)
        limit: Maximum number of departures to return
        line_query: Optional line search query (e.g., "U47", "RB33", "ICE")
                   Substring match against line number, name, etc.
        direction_query: Optional direction search query (e.g., "Berlin", "Hamburg")
                        Substring match against destination name
    
    Returns:
        List of PublicTransportDeparture objects
    """
    # Resolve station ID if not provided
    if not station_id and station_name:
        station_id = await get_station_id(station_name)
        if not station_id:
            logger.log(f"Could not find station: {station_name}")
            return []
    
    if not station_id:
        logger.log("No station ID provided and could not resolve station name")
        return []
    
    logger.log(f"Fetching departures for station ID: {station_id}")
    
    # Get line ID if line_query is specified
    line_id = None
    if line_query:
        line_id = await find_line_id(station_id, line_query)
        if not line_id:
            logger.log(f"Could not find line matching '{line_query}' at station {station_id}")
            return []
    
    params = {
        "name_dm": station_id,
        "type_dm": "any",
        "depType": "stopEvents",
        "useRealtime": "1",
        "canChangeMOT": "0",
        "coordOutputFormat": "WGS84[dd.ddddd]",
        "deleteAssignedStops_dm": "1",
        "depSequence": limit,
        "doNotSearchForStops": "1",
        "genMaps": "0",
        "imparedOptionsActive": "1",
        "inclMOT_1": "true",
        "inclMOT_2": "true",
        "inclMOT_3": "true",
        "inclMOT_4": "true",
        "inclMOT_5": "true",
        "inclMOT_6": "true",
        "inclMOT_7": "true",
        "inclMOT_8": "true",
        "inclMOT_9": "true",
        "inclMOT_10": "true",
        "inclMOT_11": "true",
        "inclMOT_13": "true",
        "inclMOT_14": "true",
        "inclMOT_15": "true",
        "inclMOT_16": "true",
        "inclMOT_17": "true",
        "inclMOT_18": "true",
        "inclMOT_19": "true",
        "includeCompleteStopSeq": "1",
        "includedMeans": "checkbox",
        "itOptionsActive": "1",
        "itdDateTimeDepArr": "dep",
        "language": "de",
        "locationServerActive": "1",
        "maxTimeLoop": "1",
        "mergeDep": "1",
        "mode": "direct",
        "ptOptionsActive": "1",
        "serverInfo": "1",
        "sl3plusDMMacro": "1",
        "useAllStops": "1",
        "useProxFootSearchDestination": "true",
        "useProxFootSearchOrigin": "true",
        "version": "11.0.6.72"
    }
    
    # Add line filter if specified
    if line_id:
        params["line"] = line_id
    
    result = await efa_request(
        "/XML_DM_REQUEST",
        params=params
    )
    
    departures = []
    
    if result["status"] == 200:
        data = result["data"]
        stop_events = data.get("stopEvents", [])
        
        for event in stop_events:
            try:
                transportation = event.get("transportation", {})
                location = event.get("location", {})
                location_props = location.get("properties", {})
                
                # Parse ISO timestamps (e.g., "2025-12-11T18:54:00Z")
                planned_time_iso = event.get("departureTimePlanned")
                estimated_time_iso = event.get("departureTimeEstimated")
                
                planned_time = _parse_departure_time_iso(planned_time_iso)
                estimated_time = _parse_departure_time_iso(estimated_time_iso)
                delay = _calculate_delay(planned_time, estimated_time)
                
                destination_name = transportation.get("destination", {}).get("name", "Unknown")
                
                # Filter by direction if specified
                if direction_query:
                    if direction_query.lower() not in destination_name.lower():
                        continue
                
                departure = PublicTransportDeparture(
                    line=transportation.get("number", "N/A"),
                    destination=destination_name,
                    planned_time=planned_time or "N/A",
                    estimated_time=estimated_time,
                    delay_minutes=delay,
                    transport_type=transportation.get("product", {}).get("name", "Unknown"),
                    platform=location_props.get("platform"),
                    realtime=event.get("isRealtimeControlled", False)
                )
                departures.append(departure)
            except Exception as e:
                logger.log(f"Error parsing departure: {e}")
                continue
        
        logger.log(f"Found {len(departures)} departures")
        return departures
    else:
        logger.log(f"Failed to fetch departures: {result['status']}")
        return []


async def get_departures_json(
    station_id: Optional[str] = None,
    station_name: Optional[str] = None,
    limit: int = 10,
    line_query: Optional[str] = None,
    direction_query: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get departures in JSON format.
    
    Args:
        station_id: EFA station ID
        station_name: Station name
        limit: Maximum number of departures
        line_query: Optional line search query (e.g., "U47", "RB33", "ICE")
                   Substring match against line number, name, etc.
        direction_query: Optional direction search query (e.g., "Berlin", "Hamburg")
                        Substring match against destination name
    
    Returns:
        JSON-serializable dictionary with departure information
    """
    departures = await get_departures(
        station_id=station_id,
        station_name=station_name,
        limit=limit,
        line_query=line_query,
        direction_query=direction_query
    )
    
    return {
        "status": "success" if departures else "no_departures",
        "departures": [dep.to_dict() for dep in departures],
        "count": len(departures)
    }
