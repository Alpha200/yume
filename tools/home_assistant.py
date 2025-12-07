from agents import function_tool
from services.home_assistant import get_public_transport_departures
from services.settings_manager import settings_manager
import asyncio

@function_tool
def get_public_transport_departures(station_name: str) -> str:
    """
    Get upcoming public transport departures for a given station name.
    
    Args:
        station_name: The name of the transit station (e.g., "Central Station")
        
    Returns:
        Formatted string with departure times and delays
    """
    # Get the entity ID from settings based on station name
    mappings = settings_manager.get_train_station_mappings()
    
    entity_id = None
    for mapping in mappings:
        if mapping["station_name"].lower() == station_name.lower():
            entity_id = mapping["entity_id"]
            break
    
    if not entity_id:
        return f"Station '{station_name}' not found in settings. Please configure it in the transit station mappings."
    
    # Fetch departures asynchronously
    try:
        departures = asyncio.run(get_public_transport_departures(entity_id))
        
        if not departures:
            return f"No upcoming departures found for {station_name}"
        
        # Format the departures
        result = f"Upcoming departures from {station_name}:\n"
        for i, dep in enumerate(departures, 1):
            result += f"{i}. {dep}\n"
        
        return result
    except Exception as e:
        return f"Error fetching departures for {station_name}: {str(e)}"
