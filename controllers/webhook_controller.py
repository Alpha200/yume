from litestar import Controller, post
from msgspec import Struct

from services.ai_engine import handle_geofence_event
from components.logging_manager import logging_manager


class GeofenceEventRequest(Struct):
    geofence_name: str
    event_type: str  # "enter" or "leave"


class GeofenceEventResponse(Struct):
    success: bool
    message: str | None = None


class WebhookController(Controller):
    """Controller for webhook endpoints (Home Assistant, external integrations)"""
    path = "/webhook"

    @post("/geofence-event")
    async def trigger_geofence_event(self, data: GeofenceEventRequest) -> GeofenceEventResponse:
        """Trigger a geofence event (enter/leave location)
        
        This endpoint uses Basic Auth for Home Assistant webhook integration.
        Configure BASIC_AUTH_USERNAME and BASIC_AUTH_PASSWORD environment variables.
        """
        try:
            # Validate event type
            if data.event_type not in ["enter", "leave"]:
                return GeofenceEventResponse(
                    success=False,
                    message="Invalid event_type. Must be 'enter' or 'leave'"
                )

            # Handle the geofence event
            result = await handle_geofence_event(data.geofence_name, data.event_type)

            return GeofenceEventResponse(
                success=True,
                message=result
            )
        except Exception as e:
            logging_manager.log(f"Error handling geofence event: {e}")
            return GeofenceEventResponse(
                success=False,
                message=f"Error processing geofence event: {str(e)}"
            )
