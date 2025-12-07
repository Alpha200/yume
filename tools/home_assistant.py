from agents import function_tool
from services.home_assistant import get_public_transport_departures
from services.settings_manager import settings_manager
from components.logging_manager import logging_manager
import asyncio

logger = logging_manager

@function_tool
def get_public_transport_departures(station_name: str) -> str:
    """
    Get upcoming public transport departures for a given station name.
    
    Args:
        station_name: The name of the transit station (e.g., "Central Station")
        
    Returns:
        Formatted string with departure times and delays
    """
    logger.log(f"[TOOL] Getting departures for station: {station_name}")
    
    # Get the entity ID from settings based on station name
    mappings = settings_manager.get_train_station_mappings()
    logger.log(f"[TOOL] Found {len(mappings)} configured stations")
    
    entity_id = None
    for mapping in mappings:
        if mapping["station_name"].lower() == station_name.lower():
            entity_id = mapping["entity_id"]
            logger.log(f"[TOOL] Matched station '{station_name}' to entity '{entity_id}'")
            break
    
    if not entity_id:
        logger.log(f"[TOOL] ERROR - Station '{station_name}' not found in settings")
        return f"Station '{station_name}' not found in settings. Please configure it in the transit station mappings."
    
    # Fetch departures asynchronously
    try:
        logger.log(f"[TOOL] Fetching departures for entity: {entity_id}")
        departures = asyncio.run(get_public_transport_departures(entity_id))
        
        logger.log(f"[TOOL] Received {len(departures)} departures")
        
        if not departures:
            logger.log(f"[TOOL] No departures found for {station_name}")
            return f"No upcoming departures found for {station_name}"
        
        # Format the departures
        result = f"Upcoming departures from {station_name}:\n"
        for i, dep in enumerate(departures, 1):
            result += f"{i}. {dep}\n"
        
        logger.log(f"[TOOL] Successfully formatted {len(departures)} departures")
        return result
    except Exception as e:
        logger.log(f"[TOOL] ERROR - Exception fetching departures: {type(e).__name__}: {e}")
        return f"Error fetching departures for {station_name}: {str(e)}"
