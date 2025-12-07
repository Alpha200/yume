from typing import List, Dict, Any
from litestar import Controller, get, post, put, delete
from litestar.exceptions import NotFoundException
from litestar.datastructures import ResponseHeader
from litestar.dto import DTOData
from msgspec import Struct

from services.ai_engine import last_taken_actions, handle_geofence_event
from services.memory_manager import memory_manager
from services.ai_scheduler import ai_scheduler
from components.logging_manager import logging_manager
from services.interaction_tracker import interaction_tracker
from services.settings_manager import settings_manager

class ActionResponse(Struct):
    action: str
    timestamp: str

class MemoryResponse(Struct):
    id: str
    type: str
    content: str
    created_at: str
    modified_at: str
    place: str | None = None
    observation_date: str | None = None
    reminder_options: Dict[str, Any] | None = None

class LogResponse(Struct):
    message: str
    timestamp: str
    level: str

class ScheduledTaskResponse(Struct):
    id: str
    name: str
    description: str
    next_run_time: str | None = None
    topic: str | None = None

class GeofenceEventRequest(Struct):
    geofence_name: str
    event_type: str  # "enter" or "leave"

class GeofenceEventResponse(Struct):
    success: bool
    message: str | None = None

class InteractionSummaryResponse(Struct):
    id: str
    agent_type: str
    timestamp: str

class InteractionDetailResponse(Struct):
    id: str
    agent_type: str
    timestamp: str
    input_data: str
    output_data: str
    metadata: Dict[str, Any] | None = None
    system_instructions: str | None = None

class TrainStationMappingsResponse(Struct):
    mappings: List[Dict[str, str]]

class TrainStationMappingRequest(Struct):
    station_name: str
    entity_id: str

class TrainStationMappingResponse(Struct):
    id: str
    station_name: str
    entity_id: str


class APIController(Controller):
    path = "/api"

    @get("/actions")
    async def get_latest_actions(self) -> List[ActionResponse]:
        """Get the latest actions taken by the AI"""
        actions = []
        for action_record in last_taken_actions:
            actions.append(ActionResponse(
                action=action_record.action,
                timestamp=action_record.timestamp.isoformat()
            ))
        return actions

    @get("/memories")
    async def get_memories(self) -> List[MemoryResponse]:
        """Get all stored memories"""
        memories = []
        all_memories = memory_manager.get_all_memories()

        for memory_id, entry in all_memories.items():
            memory_data = MemoryResponse(
                id=memory_id,
                type=entry.type,
                content=entry.content,
                place=entry.place,
                created_at=entry.created_at.isoformat(),
                modified_at=entry.modified_at.isoformat()
            )

            # Add specific fields based on memory type
            if hasattr(entry, 'observation_date'):
                memory_data.observation_date = entry.observation_date.isoformat()

            if hasattr(entry, 'reminder_options') and entry.reminder_options:
                reminder_options = {}
                if entry.reminder_options.datetime_value:
                    reminder_options['datetime_value'] = entry.reminder_options.datetime_value.isoformat()
                if entry.reminder_options.time_value:
                    reminder_options['time_value'] = entry.reminder_options.time_value
                if entry.reminder_options.days_of_week:
                    reminder_options['days_of_week'] = entry.reminder_options.days_of_week
                memory_data.reminder_options = reminder_options if reminder_options else None

            memories.append(memory_data)

        return memories

    @get("/scheduled-tasks")
    async def get_scheduled_tasks(self) -> List[ScheduledTaskResponse]:
        """Get the next scheduled tasks"""
        tasks = []

        try:
            # Get next memory reminder
            next_reminder = ai_scheduler.get_next_memory_reminder()
            if next_reminder is not None:
                nr_time = next_reminder.next_run_time
                nr_topic = next_reminder.topic

                tasks.append(ScheduledTaskResponse(
                    id="memory_reminder",
                    name="Memory Reminder",
                    next_run_time=nr_time.isoformat() if nr_time else None,
                    topic=nr_topic,
                    description="Scheduled memory reminder task"
                ))

            janitor_job = ai_scheduler.scheduler.get_job("memory_janitor_job")
            if janitor_job and janitor_job.next_run_time:
                tasks.append(ScheduledTaskResponse(
                    id="memory_janitor",
                    name="Memory Janitor",
                    next_run_time=janitor_job.next_run_time.isoformat(),
                    description="Recurring memory cleanup task (every 12 hours)"
                ))
        except Exception as e:
            # If there's an error, just return empty list
            pass

        return tasks

    @get("/logs")
    async def get_logs(self) -> List[LogResponse]:
        """Get recent log entries from the logging manager"""
        logs = []
        recent_logs = logging_manager.get_recent_logs()

        for log_entry in reversed(recent_logs):  # Show newest first
            logs.append(LogResponse(
                message=log_entry.message,
                timestamp=log_entry.timestamp.isoformat(),
                level=log_entry.level
            ))

        return logs

    @post("/geofence-event")
    async def trigger_geofence_event(self, data: GeofenceEventRequest) -> GeofenceEventResponse:
        """Trigger a geofence event (enter/leave location)"""
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

    @get("/interactions")
    async def get_interactions(self) -> List[InteractionSummaryResponse]:
        """Get all agent interactions (summary view)"""
        interactions = interaction_tracker.get_all_interactions()
        return [
            InteractionSummaryResponse(
                id=interaction.id,
                agent_type=interaction.agent_type,
                timestamp=interaction.timestamp.isoformat()
            )
            for interaction in interactions
        ]

    @get("/interactions/{interaction_id:str}")
    async def get_interaction_detail(self, interaction_id: str) -> InteractionDetailResponse:
        """Get detailed view of a specific interaction"""
        interaction = interaction_tracker.get_interaction_by_id(interaction_id)
        if not interaction:
            raise NotFoundException(detail="Interaction not found")

        return InteractionDetailResponse(
            id=interaction.id,
            agent_type=interaction.agent_type,
            timestamp=interaction.timestamp.isoformat(),
            input_data=interaction.input_data,
            output_data=interaction.output_data,
            metadata=interaction.metadata,
            system_instructions=interaction.system_instructions
        )


    # Settings endpoints
    @get("/settings/train-station-mappings")
    async def get_train_station_mappings(self) -> TrainStationMappingsResponse:
        """Get all train station to Home Assistant entity ID mappings"""
        mappings = settings_manager.get_train_station_mappings()
        return TrainStationMappingsResponse(mappings=mappings)

    @post("/settings/train-station-mappings", status_code=201)
    async def add_train_station_mapping(self, data: TrainStationMappingRequest) -> TrainStationMappingResponse:
        """Add a new train station mapping"""
        mapping_id = settings_manager.add_train_station_mapping(
            data.station_name,
            data.entity_id
        )
        
        if not mapping_id:
            raise NotFoundException(detail="Failed to create mapping")
        
        return TrainStationMappingResponse(
            id=mapping_id,
            station_name=data.station_name,
            entity_id=data.entity_id
        )

    @put("/settings/train-station-mappings/{mapping_id:str}")
    async def update_train_station_mapping(self, mapping_id: str, data: TrainStationMappingRequest) -> TrainStationMappingResponse:
        """Update an existing train station mapping"""
        success = settings_manager.update_train_station_mapping(
            mapping_id,
            data.station_name,
            data.entity_id
        )
        
        if not success:
            raise NotFoundException(detail="Mapping not found")
        
        return TrainStationMappingResponse(
            id=mapping_id,
            station_name=data.station_name,
            entity_id=data.entity_id
        )

    @delete("/settings/train-station-mappings/{mapping_id:str}", status_code=204)
    async def delete_train_station_mapping(self, mapping_id: str) -> None:
        """Delete a train station mapping"""
        success = settings_manager.delete_train_station_mapping(mapping_id)
        
        if not success:
            raise NotFoundException(detail="Mapping not found")
        
        return None
