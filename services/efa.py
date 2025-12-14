import logging
import os
import aiohttp
from typing import Optional, List, Dict, Any
from datetime import datetime
from dataclasses import dataclass

from components.timezone_utils import convert_utc_to_user_tz

logger = logging.getLogger(__name__)

# EFA API configuration
EFA_API_URL = os.getenv("EFA_API_URL", "https://efa.vrr.de/standard")
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


@dataclass
class JourneyStep:
    """Single leg of a journey, including walking segments."""
    mode: str
    line: Optional[str]
    origin: str
    destination: str
    departure_planned: Optional[str]
    departure_estimated: Optional[str]
    arrival_planned: Optional[str]
    arrival_estimated: Optional[str]
    platform_origin: Optional[str]
    platform_destination: Optional[str]
    departure_delay_minutes: Optional[int]
    arrival_delay_minutes: Optional[int]
    duration_minutes: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mode": self.mode,
            "line": self.line,
            "origin": self.origin,
            "destination": self.destination,
            "departure_planned": self.departure_planned,
            "departure_estimated": self.departure_estimated,
            "arrival_planned": self.arrival_planned,
            "arrival_estimated": self.arrival_estimated,
            "platform_origin": self.platform_origin,
            "platform_destination": self.platform_destination,
            "departure_delay_minutes": self.departure_delay_minutes,
            "arrival_delay_minutes": self.arrival_delay_minutes,
            "duration_minutes": self.duration_minutes
        }


@dataclass
class JourneyPlan:
    """Aggregated journey containing multiple steps."""
    length_minutes: int
    steps: List[JourneyStep]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "length_minutes": self.length_minutes,
            "steps": [step.to_dict() for step in self.steps]
        }


async def efa_request(endpoint: str, params: dict = None) -> dict:
    """Make a request to the EFA API."""
    if not EFA_API_URL or EFA_API_URL == "http://api.example.com":
        logger.warning("EFA_API_URL environment variable is required")
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
                    logger.error(f"EFA API error {response.status}: {error_text}")
                    return {"status": response.status, "data": error_text}
    except Exception as e:
        logger.error(f"Error making EFA request to {url}: {e}")
        return {"status": 500, "data": str(e)}


async def get_station_id(station_name: str) -> Optional[str]:
    """
    Get the station ID from a station name using EFA stopfinder.
    
    Args:
        station_name: Name of the station (e.g., "Central Station")
    
    Returns:
        Station ID or None if not found
    """
    logger.debug(f"Searching for station: {station_name}")
    
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
                logger.debug(f"Found station ID for '{station_name}': {station_id}")
                return station_id
            else:
                # If no stops found, try any location
                locations.sort(key=lambda x: x.get("matchQuality", 0), reverse=True)
                station_id = locations[0].get("id")
                logger.debug(f"Found location ID for '{station_name}': {station_id}")
                return station_id
        else:
            logger.debug(f"Station '{station_name}' not found")
            return None
    else:
        logger.error(f"Failed to search station: {result['status']}")
        return None


async def get_serving_lines(station_id: str) -> List[Dict[str, Any]]:
    """
    Get all serving lines for a station.
    
    Args:
        station_id: EFA station ID
    
    Returns:
        List of line dictionaries with id, name, number, and destination
    """
    logger.debug(f"Fetching serving lines for station: {station_id}")
    
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
        logger.debug(f"Found {len(lines)} serving lines")
        return lines
    else:
        logger.error(f"Failed to fetch serving lines: {result['status']}")
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
            logger.debug(f"Found line ID for '{line_query}' (matched {matched_field}): {line_id}")
            return line_id
    
    logger.debug(f"Line matching '{line_query}' not found at station {station_id}")
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
    """Parse ISO timestamp to HH:MM format in user's timezone.

    Converts UTC timestamps (e.g., '2025-12-11T18:54:00Z') to user's local timezone
    and extracts the time component as HH:MM.

    Args:
        time_str: ISO format timestamp string (e.g., '2025-12-11T18:54:00Z')

    Returns:
        Time string in HH:MM format in user's timezone, or None if invalid
    """
    if not time_str:
        return None
    try:
        # Parse ISO format timestamp (which is in UTC)
        dt_utc = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
        # Convert to user's timezone
        dt_user = convert_utc_to_user_tz(dt_utc)
        return dt_user.strftime("%H:%M")
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


def _seconds_to_minutes(seconds: Optional[int]) -> int:
    """Convert seconds to rounded minutes, ensuring short legs do not become zero."""
    if seconds is None:
        return 0
    if seconds <= 0:
        return 0
    minutes = seconds / 60
    if minutes < 1:
        return 1
    return int(round(minutes))


def _extract_platform(location: Dict[str, Any]) -> Optional[str]:
    """Safely extract platform information from a leg location node."""
    if not location:
        return None
    properties = location.get("properties", {}) or {}
    platform = properties.get("platform")
    if platform:
        return platform
    parent_props = (location.get("parent") or {}).get("properties", {}) or {}
    return parent_props.get("platform")


def _parse_location_time(location: Dict[str, Any], preferred_key: str, fallback_key: Optional[str] = None) -> Optional[str]:
    """Parse a timestamp from a location dict, trying preferred key first."""
    if not location:
        return None
    time_value = location.get(preferred_key)
    if not time_value and fallback_key:
        time_value = location.get(fallback_key)
    return _parse_departure_time_iso(time_value)


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
            logger.debug(f"Could not find station: {station_name}")
            return []
    
    if not station_id:
        logger.warning("No station ID provided and could not resolve station name")
        return []
    
    logger.debug(f"Fetching departures for station ID: {station_id}")
    
    # Get line ID if line_query is specified
    line_id = None
    if line_query:
        line_id = await find_line_id(station_id, line_query)
        if not line_id:
            logger.debug(f"Could not find line matching '{line_query}' at station {station_id}")
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
                logger.error(f"Error parsing departure: {e}")
                continue
        
        logger.debug(f"Found {len(departures)} departures")
        return departures
    else:
        logger.error(f"Failed to fetch departures: {result['status']}")
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


async def get_journeys(
    origin: str,
    destination: str,
    search_for_arrival: bool = False,
    origin_type: str = "any",
    destination_type: str = "any",
    limit: int = 3,
    via: Optional[str] = None,
    via_type: str = "any",
    language: str = "de"
) -> List[JourneyPlan]:
    """Search for full journeys between two points using the EFA trip endpoint."""
    if not origin or not destination:
        logger.warning("Origin and destination are required for journey search")
        return []

    params = {
        "accessProfile": "0",
        "allInterchangesAsLegs": "1",
        "calcOneDirection": "1",
        "changeSpeed": "fast",
        "coordOutputDistance": "1",
        "coordOutputFormat": "WGS84[dd.ddddd]",
        "descWithCoordPedestrian": "1",
        "genC": "1",
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
        "includedMeans": "checkbox",
        "itOptionsActive": "1",
        "itdTripDateTimeDepArr": "arr" if search_for_arrival else "dep",
        "language": language,
        "lineRestriction": "400",
        "locationServerActive": "1",
        "name_destination": destination,
        "name_origin": origin,
        "ptOptionsActive": "1",
        "routeType": "LEASTTIME",
        "serverInfo": "1",
        "sl3plusTripMacro": "1",
        "trITMOTvalue100": "15",
        "type_destination": destination_type,
        "type_origin": origin_type,
        "useProxFootSearchDestination": "true",
        "useProxFootSearchOrigin": "true",
        "useRealtime": "1",
        "useUT": "1",
        "version": "11.0.6.72"
    }

    if via:
        params["name_via"] = via
        params["type_via"] = via_type

    result = await efa_request("/XML_TRIP_REQUEST2", params=params)

    if result["status"] != 200:
        logger.error(f"Failed to fetch journeys: {result['status']}")
        return []

    data = result.get("data", {})
    raw_journeys = data.get("journeys", [])

    if not isinstance(limit, int):
        limit = len(raw_journeys)

    if limit <= 0:
        logger.debug("Journey limit <= 0, returning no results")
        return []

    journeys: List[JourneyPlan] = []
    for raw_journey in raw_journeys[:limit]:
        legs = raw_journey.get("legs", [])
        steps: List[JourneyStep] = []
        for leg in legs:
            transportation = leg.get("transportation", {}) or {}
            product = transportation.get("product", {}) or {}
            product_name = (product.get("name") or "").lower()
            product_class = product.get("class")

            if product_name == "footpath" or product_class == 100:
                mode = "walk"
                line = None
            else:
                mode = transportation.get("name") or product.get("name") or "Unknown"
                line = transportation.get("number") or transportation.get("name")

            origin_node = leg.get("origin", {}) or {}
            destination_node = leg.get("destination", {}) or {}

            departure_planned = _parse_location_time(origin_node, "departureTimePlanned", "departureTimeBaseTimetable")
            departure_estimated = _parse_location_time(origin_node, "departureTimeEstimated")
            arrival_planned = _parse_location_time(destination_node, "arrivalTimePlanned", "arrivalTimeBaseTimetable")
            arrival_estimated = _parse_location_time(destination_node, "arrivalTimeEstimated")

            step = JourneyStep(
                mode=mode,
                line=line,
                origin=origin_node.get("name") or origin_node.get("disassembledName") or "Unknown",
                destination=destination_node.get("name") or destination_node.get("disassembledName") or "Unknown",
                departure_planned=departure_planned,
                departure_estimated=departure_estimated,
                arrival_planned=arrival_planned,
                arrival_estimated=arrival_estimated,
                platform_origin=_extract_platform(origin_node),
                platform_destination=_extract_platform(destination_node),
                departure_delay_minutes=_calculate_delay(departure_planned, departure_estimated),
                arrival_delay_minutes=_calculate_delay(arrival_planned, arrival_estimated),
                duration_minutes=_seconds_to_minutes(leg.get("duration"))
            )
            steps.append(step)

        if not steps:
            continue

        total_duration_seconds = sum(leg.get("duration", 0) or 0 for leg in legs)
        journey_plan = JourneyPlan(
            length_minutes=_seconds_to_minutes(total_duration_seconds),
            steps=steps
        )
        journeys.append(journey_plan)

    logger.debug(f"Found {len(journeys)} journeys between '{origin}' and '{destination}'")
    return journeys

