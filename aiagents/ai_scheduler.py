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

Return values:
- next_run_time: The date and time for the next run
- reason: A brief reason for the chosen next run time
- topic: The topic of the next reminder (should include the memory content of the relevant memory entries)
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
        return

    # Format memories and run AI analysis
    formatted_input = _format_memories_for_analysis(memories)

    try:
        next_run_result = await _run_ai_analysis(formatted_input)

        # Validate and adjust AI suggested time (min 15 minutes)
        validated_ai = _validate_and_adjust_time(next_run_result)

        # Determine a deterministic next-run from reminder memories
        deterministic = _determine_next_run_from_reminders(memories)

        # Choose the scheduled time that is closest in the future (earliest upcoming)
        chosen = None

        if deterministic is None:
            # Ensure topic propagation from agent result if available
            chosen = NextRun(next_run_time=validated_ai.next_run_time, reason=validated_ai.reason, topic=validated_ai.topic)
        elif validated_ai is None:
            chosen = deterministic
        else:
            now = now_user_tz()
            delta_ai = (validated_ai.next_run_time - now).total_seconds()
            delta_det = (deterministic.next_run_time - now).total_seconds()

            # Pick the one that is sooner (smaller positive delta)
            if delta_det <= delta_ai:
                chosen = deterministic
            else:
                chosen = NextRun(next_run_time=validated_ai.next_run_time, reason=validated_ai.reason, topic=validated_ai.topic)

        # Finally schedule the chosen next run
        ai_scheduler.schedule_next_run(chosen)

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


def _determine_next_run_from_reminders(memories) -> NextRun | None:
    """Deterministic next-run calculation: find the closest upcoming reminder from stored reminders.

    This will consider one-time reminders (datetime_value) and simple recurring reminders with a time_value
    and optional days_of_week. Returns None if no suitable upcoming reminder is found.
    """
    min_future_time = now_user_tz() + datetime.timedelta(minutes=15)
    candidates = []

    for memory_id, entry in memories.items():
        try:
            if getattr(entry, "type", None) != "reminder":
                continue

            ro = getattr(entry, "reminder_options", None)
            if not ro:
                continue

            # One-time reminder with explicit datetime
            dt = getattr(ro, "datetime_value", None)
            if dt:
                dt_local = to_user_tz(dt)
                if dt_local >= min_future_time:
                    candidates.append((dt_local, f"Reminder {memory_id}: {entry.content}", memory_id, entry.content))
                continue

            # Recurring by time_value (HH:MM) and optional days_of_week
            time_str = getattr(ro, "time_value", None)
            days = getattr(ro, "days_of_week", None)

            if not time_str:
                # No usable scheduling info
                continue

            # Parse time
            try:
                t = datetime.datetime.strptime(time_str, "%H:%M").time()
            except ValueError:
                # If parsing fails, skip this reminder
                continue

            today = now_user_tz().date()

            if days and len(days) > 0:
                # Map weekday names to numbers (Monday=0 ... Sunday=6)
                wk_map = {
                    "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
                    "friday": 4, "saturday": 5, "sunday": 6
                }
                # Normalize day names
                target_weekdays = []
                for d in days:
                    if not isinstance(d, str):
                        continue
                    key = d.strip().lower()
                    if key in wk_map:
                        target_weekdays.append(wk_map[key])

                # For each target weekday determine the next date
                for wd in target_weekdays:
                    days_ahead = (wd - today.weekday() + 7) % 7
                    candidate_date = today + datetime.timedelta(days=days_ahead)
                    candidate_dt = to_user_tz(datetime.datetime.combine(candidate_date, t))
                    if candidate_dt < min_future_time:
                        # If this week's occurrence already passed, schedule for next week
                        candidate_date = candidate_date + datetime.timedelta(days=7)
                        candidate_dt = to_user_tz(datetime.datetime.combine(candidate_date, t))

                    if candidate_dt >= min_future_time:
                        candidates.append((candidate_dt, f"Reminder {memory_id}: {entry.content}", memory_id, entry.content))
            else:
                # No days specified, use next today/tomorrow occurrence
                candidate_dt = to_user_tz(datetime.datetime.combine(today, t))
                if candidate_dt < min_future_time:
                    candidate_dt = candidate_dt + datetime.timedelta(days=1)
                if candidate_dt >= min_future_time:
                    candidates.append((candidate_dt, f"Reminder {memory_id}: {entry.content}", memory_id, entry.content))

        except Exception:
            # Skip problematic entries
            continue

    if not candidates:
        return None

    # Pick the earliest candidate
    candidates.sort(key=lambda x: x[0])
    chosen_dt, reason, chosen_id, chosen_content = candidates[0]

    # Include other reminders that are within 15 minutes of the chosen one
    nearby_threshold = datetime.timedelta(minutes=15)
    nearby = [ (dt, desc, mid, content) for dt, desc, mid, content in candidates if abs((dt - chosen_dt).total_seconds()) <= nearby_threshold.total_seconds() ]

    if len(nearby) > 1:
        # Format list of reminders/time for the reason
        parts = []
        topics = []
        for dt, desc, mid, content in nearby:
            parts.append(f"{desc} at {dt.strftime('%Y-%m-%d %H:%M')}")
            topics.append(content)
        combined_reason = f"Deterministic reminder chosen: {parts[0]} (includes nearby reminders: {', '.join(parts[1:])})"
        topic_str = "; ".join(topics)
    else:
        combined_reason = f"Deterministic reminder chosen: {reason}"
        topic_str = chosen_content

    return NextRun(next_run_time=chosen_dt, reason=combined_reason, topic=topic_str)
