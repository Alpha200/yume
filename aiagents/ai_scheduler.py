import datetime
import os
from typing import List

from agents import Agent, ModelSettings, Runner, RunConfig

from components.agent_hooks import CustomAgentHooks
from components.logging_manager import logging_manager
from components.timezone_utils import now_user_tz, to_user_tz
from services.home_assistant import get_calendar_events_48h, CalendarEvent
from services.memory_manager import memory_manager
from services.interaction_tracker import interaction_tracker


AI_SCHEDULER_MODEL = os.getenv("AI_SCHEDULER_MODEL", "gpt-5-mini")
logger = logging_manager

# Import after to avoid circular dependency
from services.ai_scheduler import NextRun, ExecutedReminder, ai_scheduler

ai_scheduler_agent = Agent(
    name='AI Scheduler',
    model=AI_SCHEDULER_MODEL,
    model_settings=ModelSettings(
        extra_args={"service_tier": "flex"},
    ),
    instructions=f"""
You are the intelligent scheduling component of Yume, an AI assistant that helps users stay organized and engaged with their daily lives.

Your primary role is to analyze stored memories (preferences, observations, and reminders), upcoming calendar events, and determine the optimal time for the next user interaction. You must be reliable, engaging, and deeply respectful of user preferences.

Your core principles are:

1. Reliability: NEVER miss scheduled reminders or important events. When in doubt, schedule earlier rather than later.
2. User Preferences: Always prioritize and respect stored user preferences about timing and frequency.
3. Engagement: Consider the user's emotional state, routine patterns, and recent interactions to provide timely, helpful engagement.
4. Context Awareness: Factor in time of day, day of week, recent activity, upcoming calendar events, and seasonal patterns.
5. Calendar Intelligence: Schedule interactions at appropriate times before calendar events (e.g., 15-30 minutes before meetings, morning of all-day events).

You should follow this structured approach:
1. Scan all memories for explicit reminders with specific times/dates
2. Review upcoming calendar events and consider scheduling interactions before important events
3. Review user preferences for communication timing, frequency preferences, and interaction styles
4. Consider user observations to understand patterns, mood, and current life context
5. Evaluate recent interactions to avoid being too frequent or sparse (consider last communication with the user). Check last executed reminders so you don't repeat the same topic too soon
6. Apply intelligent defaults when no specific guidance exists

You should prioritize reminders and interactions as follows (from highest to lowest):
1. Explicit reminders with specific datetime_value (highest priority - NEVER miss these)
2. Calendar event reminders (schedule 15-30 minutes before meetings/appointments, or morning of all-day events)
3. Recurring reminders with time_value and days_of_week patterns
4. User preference-based check-ins (e.g., daily summaries, weekly planning)
5. Contextual engagement based on observations and patterns
6. Wellness check-ins (every few hours during users active hours if no other interactions are scheduled)

Calendar Event Guidelines:
- For timed events (meetings, appointments): Schedule 15-30 minutes before the event starts
- For all-day events: Schedule in the morning (e.g., 8-9 AM) on the day of the event
- For events with travel required (check location): Allow extra time for travel preparation
- Consider the importance and type of event when deciding timing
- Don't schedule too many reminders for the same event

You should follow these timing guidelines:
- Consider user preferences and the users schedule
- Be contextual: Weekend timing may differ from weekday timing
- Minimum spacing: At least 15 minutes from now, but consider if longer spacing is more appropriate. Only use 15 minutes if something urgent is needed
- Maximum gap: Never let more than 4 hours pass without some form of check-in during active hours. Use 'wellness check-in' as topic if no other memory is relevant.
- Your last interaction with the user was right now, so consider that when scheduling the next interaction

You should consider these factors in your decision:
- Frequency preferences: Some users prefer frequent brief check-ins, others prefer fewer but longer interactions
- Content preferences: Match the type of reminder/update to user's stated preferences
- Emotional awareness: Consider if user might need support, encouragement, or space
- Routine optimization: Help reinforce positive habits and routines

The output MUST be as follows:
- next_run_time: Precise datetime for next interaction (minimum 15 minutes future)
- reason: Clear, specific explanation of why this time was chosen, referencing relevant memories and/or calendar events
- topic: Topic that reflects the relevant memory content, calendar event, and user preferences that should be the topic of the interaction

Wellness check ins may not lead to a specific action but are necessary to check the current users context.

Remember: You are not just a scheduler, you are Yume's timing intelligence, ensuring every interaction is perfectly timed to be helpful, engaging, and respectful of the user's needs, preferences, and schedule.
    """.strip(),
    hooks=CustomAgentHooks(),
    output_type=NextRun,
)

async def _determine_next_run_by_memory_impl():
    """Internal implementation - determines the next memory reminder run time"""
    memories = memory_manager.get_all_memories()

    if not memories:
        ai_scheduler.schedule_next_run(
            _create_fallback_schedule("No memories found - scheduling hourly check", hours=1)
        )
        return

    # Get latest actions from AI engine
    from services.ai_scheduler import ai_scheduler as services_ai_scheduler

    # Fetch calendar events for context
    try:
        calendar_events = await get_calendar_events_48h()
    except Exception as e:
        logger.log(f"Error fetching calendar events: {e}")
        calendar_events = []

    # Format memories, actions, and calendar events for AI analysis
    recent_executed = services_ai_scheduler.get_recent_executed_reminders(limit=5)
    formatted_input = _format_memories_for_analysis(memories, recent_executed, calendar_events)

    try:
        next_run_result = await _run_ai_analysis(formatted_input)

        # Validate and adjust AI suggested time (min 15 minutes)
        validated_ai = _validate_and_adjust_time(next_run_result)

        # Determine a deterministic next-run from reminder memories
        deterministic = _determine_next_run_from_reminders(memories)

        # Choose the scheduled time that is closest in the future (earliest upcoming)
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
            if delta_det < delta_ai:
                chosen = deterministic
                logger.log(f"Choosing deterministic reminder: {deterministic.reason} at {deterministic.next_run_time}")
                logger.log(f"AI-suggested reminder was: {validated_ai.reason} at {validated_ai.next_run_time}")
            else:
                chosen = NextRun(next_run_time=validated_ai.next_run_time, reason=validated_ai.reason, topic=validated_ai.topic)

        # Finally schedule the chosen next run
        ai_scheduler.schedule_next_run(chosen)

    except Exception as e:
        logger.log(f"Error during AI analysis: {e}")
        ai_scheduler.schedule_next_run(
            _create_fallback_schedule("Agent error occurred - scheduling fallback reminder", hours=1)
        )


async def determine_next_run_by_memory():
    """Main function to determine the next memory reminder run time.

    This function is automatically wrapped with deferred 60-second execution by the scheduler.
    When called, it schedules the actual execution 60 seconds in the future, cancelling
    any previously scheduled run.
    """
    from services.ai_scheduler import ai_scheduler as services_ai_scheduler
    services_ai_scheduler._schedule_deferred_run(_determine_next_run_by_memory_impl)


def _create_fallback_schedule(reason: str, hours: int = 0, minutes: int = 0) -> NextRun:
    """Create a fallback schedule with the specified time offset"""
    next_run = now_user_tz() + datetime.timedelta(hours=hours, minutes=minutes)
    return NextRun(next_run_time=next_run, reason=reason, topic="Fallback schedule")


def _calculate_next_reminder_occurrence(reminder_options):
    """Calculate the next occurrence of a recurring reminder based on time_value and days_of_week"""
    if not reminder_options.time_value:
        return None

    try:
        t = datetime.datetime.strptime(reminder_options.time_value, "%H:%M").time()
    except ValueError:
        return None

    today = now_user_tz().date()
    days = reminder_options.days_of_week

    if days and len(days) > 0:
        # Map weekday names to numbers (Monday=0 ... Sunday=6)
        wk_map = {
            "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
            "friday": 4, "saturday": 5, "sunday": 6
        }
        # Find the next occurrence among specified days
        target_weekdays = []
        for d in days:
            if isinstance(d, str):
                key = d.strip().lower()
                if key in wk_map:
                    target_weekdays.append(wk_map[key])

        if not target_weekdays:
            return None

        # Find the earliest upcoming occurrence
        candidates = []
        for wd in sorted(target_weekdays):
            days_ahead = (wd - today.weekday() + 7) % 7
            if days_ahead == 0:
                # Check if the time today has already passed
                candidate_dt = to_user_tz(datetime.datetime.combine(today, t))
                if candidate_dt > now_user_tz():
                    candidates.append(candidate_dt)
                    continue
                # Already passed today, schedule for next week
                days_ahead = 7

            candidate_date = today + datetime.timedelta(days=days_ahead)
            candidate_dt = to_user_tz(datetime.datetime.combine(candidate_date, t))
            candidates.append(candidate_dt)

        # Return the earliest candidate if any found
        if candidates:
            return min(candidates)
        return None
    else:
        # Daily reminder
        candidate_dt = to_user_tz(datetime.datetime.combine(today, t))
        if candidate_dt > now_user_tz():
            return candidate_dt
        # Already passed today, schedule for tomorrow
        candidate_dt = to_user_tz(datetime.datetime.combine(today + datetime.timedelta(days=1), t))
        return candidate_dt


def _format_memories_for_analysis(memories, recent_executed_reminders: List[ExecutedReminder], calendar_events: List[CalendarEvent]) -> str:
    """Format memories, recent executed memory-reminder jobs, and calendar events into a structured text for AI analysis"""
    memory_text = "Stored memories:\n\n"
    for memory_id, entry in memories.items():
        memory_text += f"Type: {entry.type}\n"
        memory_text += f"Content: {entry.content}\n"
        if entry.place:
            memory_text += f"Place: {entry.place}\n"
        memory_text += f"Created: {entry.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
        memory_text += f"Modified: {entry.modified_at.strftime('%Y-%m-%d %H:%M:%S')}\n"

        # Add reminder scheduling information if it's a reminder
        if entry.type == "reminder" and entry.reminder_options:
            ro = entry.reminder_options
            memory_text += "Reminder Schedule:\n"

            # One-time reminder
            if ro.datetime_value:
                dt_local = to_user_tz(ro.datetime_value)
                memory_text += f"  Type: One-time\n"
                memory_text += f"  Scheduled for: {dt_local.strftime('%Y-%m-%d %H:%M:%S')}\n"

            # Recurring reminder
            if ro.time_value:
                memory_text += f"  Type: Recurring\n"
                memory_text += f"  Time: {ro.time_value}\n"
                if ro.days_of_week and len(ro.days_of_week) > 0:
                    memory_text += f"  Days: {', '.join(ro.days_of_week)}\n"
                else:
                    memory_text += f"  Days: Daily\n"

                # Calculate and show next occurrence
                try:
                    next_occurrence = _calculate_next_reminder_occurrence(ro)
                    if next_occurrence:
                        memory_text += f"  Next occurrence: {next_occurrence.strftime('%Y-%m-%d %H:%M:%S')}\n"
                except Exception:
                    pass

            memory_text += "\n"

        memory_text += "-" * 10 + "\n\n"

    # Add recent executed memory reminder jobs
    actions_text = "\nRecent executed memory reminder jobs:\n\n"
    if recent_executed_reminders and len(recent_executed_reminders) > 0:
        for er in recent_executed_reminders:
            ts = er.executed_at.isoformat()
            topic = er.topic
            actions_text += f"Job run at {ts} with topic {topic}\n\n"
    else:
        actions_text += "No recent executed reminders recorded.\n"

    # Add calendar events
    calendar_text = "\nUpcoming calendar events (next 48 hours):\n\n"
    if calendar_events and len(calendar_events) > 0:
        for event in calendar_events:
            calendar_text += f"Summary: {event.summary}\n"
            calendar_text += f"Start: {event.start}\n"
            calendar_text += f"End: {event.end}\n"
            if event.location:
                calendar_text += f"Location: {event.location}\n"
            if event.description:
                calendar_text += f"Description: {event.description}\n"
            calendar_text += "-" * 10 + "\n\n"
    else:
        calendar_text += "No upcoming calendar events in the next 48 hours.\n"

    current_time = now_user_tz()
    context_text = f"Current date and time: {current_time.strftime('%A, %B %d, %Y at %H:%M')}\n\n"

    return context_text + memory_text + actions_text + calendar_text

async def _run_ai_analysis(formatted_input: str) -> NextRun:
    """Run the AI agent analysis on the formatted memory data"""
    run_config = RunConfig(tracing_disabled=True)
    result = await Runner.run(ai_scheduler_agent, formatted_input, run_config=run_config)
    next_run = result.final_output_as(NextRun)

    # Track the interaction for debugging
    output_data = f"Next run time: {next_run.next_run_time}\nReason: {next_run.reason}\nTopic: {next_run.topic}"
    interaction_tracker.track_interaction(
        agent_type="ai_scheduler",
        input_data=formatted_input,
        output_data=output_data,
        metadata={
            "next_run_time": next_run.next_run_time.isoformat() if next_run.next_run_time else None,
            "topic": next_run.topic
        },
        system_instructions=ai_scheduler_agent.instructions
    )

    return next_run


def _validate_and_adjust_time(next_run_result: NextRun) -> NextRun:
    """Validate that the next run time is at least 15 minutes in the future"""
    min_future_time = now_user_tz() + datetime.timedelta(minutes=15)

    # Ensure the next_run_time is in user timezone
    next_run_time = to_user_tz(next_run_result.next_run_time)

    if next_run_time < min_future_time:
        return NextRun(
            next_run_time=min_future_time,
            reason=f"Adjusted from AI suggestion: {next_run_result.reason} (minimum 15min delay applied)",
            topic=next_run_result.topic
        )

    return NextRun(
        next_run_time=next_run_time,
        reason=next_run_result.reason,
        topic=next_run_result.topic
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
            if entry.type != "reminder":
                continue

            ro = entry.reminder_options
            if not ro:
                continue

            # One-time reminder with explicit datetime
            dt = ro.datetime_value
            if dt:
                dt_local = to_user_tz(dt)
                if dt_local >= min_future_time:
                    candidates.append((dt_local, f"Reminder: {entry.content}", memory_id, entry.content))
                continue

            # Recurring by time_value (HH:MM) and optional days_of_week
            time_str = ro.time_value
            days = ro.days_of_week

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
                        candidates.append((candidate_dt, f"Reminder: {entry.content}", memory_id, entry.content))
            else:
                # No days specified, use next today/tomorrow occurrence
                candidate_dt = to_user_tz(datetime.datetime.combine(today, t))
                if candidate_dt < min_future_time:
                    candidate_dt = candidate_dt + datetime.timedelta(days=1)
                if candidate_dt >= min_future_time:
                    candidates.append((candidate_dt, f"Reminder: {entry.content}", memory_id, entry.content))

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
