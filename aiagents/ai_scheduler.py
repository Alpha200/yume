import datetime

from agents import Agent, ModelSettings, Runner, RunConfig
from openai.types import Reasoning

from components.agent_hooks import CustomAgentHooks
from components.logging_manager import logging_manager
from components.timezone_utils import now_user_tz, to_user_tz
from services.ai_scheduler import ai_scheduler, NextRun
from services.memory_manager import memory_manager


logger = logging_manager

ai_scheduler_agent = Agent(
    name='AI Scheduler',
    model="gpt-5-mini",
    model_settings=ModelSettings(
        reasoning=Reasoning(
            effort="medium",
        ),
        extra_args={"service_tier": "flex"},
    ),
    instructions=f"""
You are part of a system that assists the user by keeping a memory about the user and sending messages to the user at relevant times based on their memories.
Your job is to analyze the stored memories and determine when the next memory reminder should be sent to the user.

Do the following:
1. Analyze the stored memories to determine the time and date for the next run. It is most important that you don't miss any relevant reminders.
2. Provide a brief reason for the chosen next run time that will be given as input to the reminder sending function. 
3. If there are multiple relevant memories, choose the one with the closest upcoming date and include all relevant memories in the reason.
4. There may be memories without specific dates. Use your judgment to determine if they are relevant for scheduling a reminder.

The minimum time for the next run must be at least 15 minutes in the future. If no relevant memories are found, schedule a fallback reminder in 1 hour.
    """.strip(),
    hooks=CustomAgentHooks(),
    output_type=NextRun,
)

async def determine_next_run_by_memory():
    """Main function to determine the next memory reminder run time"""
    memories = memory_manager.get_all_memories()

    if not memories:
        ai_scheduler.schedule_next_run(
            _create_fallback_schedule("No memories found - scheduling hourly check", hours=1)
        )

    # Format memories and run AI analysis
    formatted_input = _format_memories_for_analysis(memories)

    try:
        next_run_result = await _run_ai_analysis(formatted_input)
        ai_scheduler.schedule_next_run(
            _validate_and_adjust_time(next_run_result)
        )
    except Exception as e:
        logger.log(f"Error during AI analysis: {e}")
        ai_scheduler.schedule_next_run(
            _create_fallback_schedule("Agent error occurred - scheduling fallback reminder", hours=1)
        )

def _create_fallback_schedule(reason: str, hours: int = 0, minutes: int = 0) -> NextRun:
    """Create a fallback schedule with the specified time offset"""
    next_run = now_user_tz() + datetime.timedelta(hours=hours, minutes=minutes)
    return NextRun(next_run_time=next_run, reason=reason)

def _format_memories_for_analysis(memories) -> str:
    """Format memories into a structured text for AI analysis"""
    memory_text = "Stored memories:\n\n"
    for memory_id, entry in memories.items():
        memory_text += f"ID: {memory_id}\n"
        memory_text += f"Type: {entry.type}\n"
        memory_text += f"Content: {entry.content}\n"
        if entry.place:
            memory_text += f"Place: {entry.place}\n"
        memory_text += f"Created: {entry.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
        memory_text += f"Modified: {entry.modified_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
        memory_text += "-" * 50 + "\n"

    current_time = now_user_tz()
    context_text = f"\nCurrent date and time: {current_time.strftime('%A, %B %d, %Y at %H:%M')}\n\n"

    return context_text + memory_text

async def _run_ai_analysis(formatted_input: str) -> NextRun:
    """Run the AI agent analysis on the formatted memory data"""
    run_config = RunConfig(tracing_disabled=True)
    result = await Runner.run(ai_scheduler_agent, formatted_input, run_config=run_config)
    return result.final_output_as(NextRun)

def _validate_and_adjust_time(next_run_result: NextRun) -> NextRun:
    """Validate that the next run time is at least 15 minutes in the future"""
    min_future_time = now_user_tz() + datetime.timedelta(minutes=15)

    # Ensure the next_run_time is in user timezone
    next_run_time = to_user_tz(next_run_result.next_run_time)

    if next_run_time < min_future_time:
        return NextRun(
            next_run_time=min_future_time,
            reason=f"Adjusted from AI suggestion: {next_run_result.reason} (minimum 15min delay applied)"
        )

    return NextRun(
        next_run_time=next_run_time,
        reason=next_run_result.reason
    )
