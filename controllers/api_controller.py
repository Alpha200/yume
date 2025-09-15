from typing import List, Dict, Any
from fastapi import APIRouter
from pydantic import BaseModel

from services.ai_engine import last_taken_actions, handle_geofence_event
from services.memory_manager import memory_manager
from services.ai_scheduler import ai_scheduler
from components.logging_manager import logging_manager

router = APIRouter(prefix="/api", tags=["api"])

class ActionResponse(BaseModel):
    action: str
    timestamp: str

class MemoryResponse(BaseModel):
    id: str
    type: str
    content: str
    place: str | None
    created_at: str
    modified_at: str
    observation_date: str | None = None
    reminder_options: Dict[str, Any] | None = None

class LogResponse(BaseModel):
    message: str
    timestamp: str
    level: str

class ScheduledTaskResponse(BaseModel):
    id: str
    name: str
    next_run_time: str | None
    topic: str | None = None
    description: str

class GeofenceEventRequest(BaseModel):
    geofence_name: str
    event_type: str  # "enter" or "leave"

class GeofenceEventResponse(BaseModel):
    success: bool
    message: str | None


@router.get("/actions", response_model=List[ActionResponse])
async def get_latest_actions():
    """Get the latest actions taken by the AI"""
    actions = []
    for action_record in last_taken_actions:
        actions.append(ActionResponse(
            action=action_record.action,
            timestamp=action_record.timestamp.isoformat()
        ))
    return actions

@router.get("/memories", response_model=List[MemoryResponse])
async def get_memories():
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

@router.get("/scheduled-tasks", response_model=List[ScheduledTaskResponse])
async def get_scheduled_tasks():
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

@router.get("/logs", response_model=List[LogResponse])
async def get_logs():
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

@router.post("/geofence-event", response_model=GeofenceEventResponse)
async def trigger_geofence_event(request: GeofenceEventRequest):
    """Trigger a geofence event (enter/leave location)"""
    try:
        # Validate event type
        if request.event_type not in ["enter", "leave"]:
            return GeofenceEventResponse(
                success=False,
                message="Invalid event_type. Must be 'enter' or 'leave'"
            )

        # Handle the geofence event
        result = await handle_geofence_event(request.geofence_name, request.event_type)

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
