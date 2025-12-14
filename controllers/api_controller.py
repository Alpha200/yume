import logging
from typing import List, Dict, Any
from litestar import Controller, get
from litestar.exceptions import NotFoundException
from msgspec import Struct

from services.ai_engine import last_taken_actions
from services.memory_manager import memory_manager
from services.ai_scheduler import ai_scheduler
from services.interaction_tracker import interaction_tracker
from services.day_planner import day_planner_service
import datetime

logger = logging.getLogger(__name__)

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

class ScheduledTaskResponse(Struct):
    id: str
    name: str
    description: str
    next_run_time: str | None = None
    topic: str | None = None

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
    tool_usage: List[Dict[str, Any]] | None = None
    llm_calls: List[Dict[str, Any]] | None = None

class DayPlanItemResponse(Struct):
    id: str
    title: str
    source: str
    confidence: str  # "low", "medium", or "high"
    tags: List[str]
    description: str | None = None
    start_time: str | None = None
    end_time: str | None = None
    location: str | None = None

class DayPlanResponse(Struct):
    id: str
    date: str
    items: List[DayPlanItemResponse]
    created_at: str
    updated_at: str
    summary: str | None = None


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
            system_instructions=interaction.system_instructions,
            tool_usage=interaction.tool_usage,
            llm_calls=interaction.llm_calls
        )


    # Day plan endpoints
    @get("/day-plans/{date:str}")
    async def get_day_plan(self, date: str) -> DayPlanResponse:
        """Get the day plan for a specific date (YYYY-MM-DD)"""
        try:
            plan_date = datetime.date.fromisoformat(date)
        except ValueError:
            raise NotFoundException(detail=f"Invalid date format: {date}")
        
        plan = day_planner_service.get_plan_for_date(plan_date)
        
        if not plan:
            raise NotFoundException(detail=f"No plan found for {date}")
        
        items = [
            DayPlanItemResponse(
                id=item.id,
                title=item.title,
                description=item.description,
                start_time=item.start_time.isoformat() if item.start_time else None,
                end_time=item.end_time.isoformat() if item.end_time else None,
                source=item.source,
                confidence=item.confidence,
                location=item.location,
                tags=item.tags
            )
            for item in plan.items
        ]
        
        return DayPlanResponse(
            id=plan.id,
            date=plan.date.isoformat(),
            items=items,
            created_at=plan.created_at.isoformat(),
            updated_at=plan.updated_at.isoformat(),
            summary=plan.summary
        )

