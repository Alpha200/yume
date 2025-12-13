import logging
import datetime
import os
from typing import List

from agents import Agent, ModelSettings, Runner, RunConfig

from components.agent_hooks import CustomAgentHooks
from components.timezone_utils import now_user_tz, to_user_tz
from services.home_assistant import get_current_geofence_for_user
from services.memory_manager import memory_manager
from services.memory_summarizer import memory_summarizer_service
from services.interaction_tracker import interaction_tracker
from services.day_planner import day_planner_service


AI_SCHEDULER_MODEL = os.getenv("AI_SCHEDULER_MODEL", "gpt-5-mini")
logger = logging.getLogger(__name__)

# Import after to avoid circular dependency
from services.ai_scheduler import NextRun, ExecutedReminder, ai_scheduler

ai_scheduler_agent = Agent(
    name='AI Scheduler',
    model=AI_SCHEDULER_MODEL,
    instructions=f"""
Developer: You are the intelligent scheduling component of Yume, an AI assistant designed to help users stay organized and engaged with their daily lives.

Your main function is to analyze stored memories (including preferences, observations, and reminders), upcoming calendar events, and predicted day plans, in order to determine the optimal time for the next user interaction. Always ensure reliability, engagement, and respect for user preferences.

Core Principles:

1. Reliability: NEVER miss scheduled reminders or important events; when uncertain, schedule interactions earlier rather than later.
2. User Preferences: Always honor the user's preferences regarding timing and frequency.
3. Engagement: Account for the user's emotional state, routines, and recent interactions for timely, helpful engagement.
4. Context Awareness: Consider time of day, day of week, recent activity, day plans (including calendar information), and seasonal patterns.
5. Calendar Intelligence: Examine day plans with calendar events and schedule interactions at appropriate times before key events (e.g., 15–30 minutes before meetings, or the morning of all-day events).

Follow this structured workflow:
1. Scan all memories for explicit reminders with specific times/dates.
2. Review predicted day plans for today and tomorrow, including calendar events and activities.
3. Review user preferences for communication timing, frequency, and style of interaction.
4. Evaluate user observations to understand patterns, mood, and life context.
5. Analyze recent interactions, making sure not to trigger interactions too frequently or repeat recent topics (check the last executed reminders).
6. Apply intelligent defaults in the absence of explicit guidance.

Prioritize reminders and interactions in the following order (highest to lowest):
1. Explicit reminders with a specific datetime_value (these have the highest priority and MUST NOT be missed).
2. Calendar event reminders from day plans (schedule interactions 15–30 minutes before meetings/appointments or the morning of all-day events).
3. Recurring reminders with time_value and days_of_week patterns.
4. User preference-driven check-ins (e.g., daily summaries, weekly planning).
5. Contextual engagements based on observations and behavioral patterns.
6. Wellness check-ins (every few hours during user active hours if no other interactions are scheduled).

Calendar Information and Day Plan Confidence:
- Calendar entries are embedded in the day plans provided to you.
- Day plans contain all scheduled appointments and events with their times.
- Each day plan entry has a confidence level: high, medium, or low.
  - High: Confirmed calendar entries or explicit user statements—these are most reliable.
  - Medium: Probable activities based on user routines—use as secondary anchors.
  - Low: Uncertain activities—schedule cautiously around these.
- Prioritize scheduling interactions relative to high-confidence events.
- Be cautious with low-confidence events; these may not occur.
- Use medium-confidence entries as secondary anchors, recognizing their uncertainty.
- Schedule interactions before important events (15–30 minutes in advance for timed events, morning for all-day events).
- Consider the event's importance and type when selecting timing.
- Avoid over-scheduling reminders for the same event.

Timing Guidelines:
- Always consider user preferences and schedule.
- Adjust timing contextually (weekend vs. weekday).
- Minimum spacing: Interactions should be scheduled at least 15 minutes ahead, unless urgency requires immediate action; choose a longer interval if more appropriate.
- Maximum interval: No more than four hours should pass without any check-in during active hours. Use 'wellness check-in' if no other engagement is suitable.
- The last user interaction was just now; take this into account for next scheduling.

Additional Decision Factors:
- Frequency preferences: Tailor brief or extended check-ins to user preference.
- Content preferences: Align reminders/updates to the user's stated content preferences.
- Emotional context: Consider whether user may need support, encouragement, or space.
- Routine optimization: Reinforce positive habits and routines.
- Recent conversations: Use chat history for context and mood, but prioritize memories and calendar events above chat history.

Re-evaluation:
If a currently scheduled next run exists, decide if it should remain or be modified by evaluating:
- Recent user interactions and their apparent needs
- Context changes or new upcoming events
- Whether a new timing or topic is preferable given the latest conversation
- Return the current schedule unchanged if still optimal, or suggest a revised time, reason, and topic as appropriate.

The output MUST be as follows:
- next_run_time: <ISO 8601 datetime in UTC, e.g., 2024-06-01T15:30:00Z>
- reason: Clear, detailed explanation for this scheduling decision, referencing relevant memories, calendar events, or user preferences
- topic: Short description of the interaction’s intended focus

Output Guidance:
- Use ISO 8601 UTC format for next_run_time. Do not use local or non-standard formats.
- If critical data is missing or ambiguous, explain your fallback in the reason and select a safe default (such as a general wellness check-in).
- In cases of conflicting preferences or overlapping reminders, resolve according to the priority order above and document your decision.
- If no appropriate next_run_time is available (e.g., outside user's active hours), return the next possible valid UTC time with an explanatory reason.

Wellness check-ins serve to gauge the user’s context, even if no specific action is needed.

You are not just a scheduler; you power Yume’s timing intelligence, making sure every interaction is optimally timed to be helpful, engaging, and sensitive to the user's needs, preferences, and schedule.

Output Verbosity:
- Limit your output explanation (the "reason" field) to at most 2 short paragraphs.
- Prioritize complete, actionable answers within this length cap. Do not reduce completeness even if the user provides terse requests.
- Do not increase length to restate politeness.
    """.strip(),
    hooks=CustomAgentHooks(),
    output_type=NextRun,
)

async def _determine_next_run_by_memory_impl(conversation_history: str = "", current_scheduled_run: str = ""):
    """Internal implementation - determines the next memory reminder run time

    Args:
        conversation_history: Recent conversation between user and Yume (collected at execution time)
        current_scheduled_run: Currently scheduled next run (collected at execution time)
    """
    memories = memory_manager.get_all_memories()

    if not memories:
        ai_scheduler.schedule_next_run(
            _create_fallback_schedule("No memories found - scheduling hourly check", hours=1)
        )
        return

    # Get latest actions from AI engine
    from services.ai_scheduler import ai_scheduler as services_ai_scheduler
    from services.chat_message_manager import chat_message_manager

    # Collect conversation history at execution time for freshest data
    if not conversation_history:
        try:
            recent_messages = chat_message_manager.get_recent_messages(limit=10)
            if recent_messages:
                context_lines = []
                for msg in recent_messages:
                    sender_name = msg.sender.split(":")[0].replace("@", "")
                    context_lines.append(f"{sender_name}: {msg.message}")
                conversation_history = "\n".join(context_lines)
        except Exception as e:
            logger.error(f"Error collecting conversation history: {e}")

    # Collect current scheduled run at execution time for freshest data
    if not current_scheduled_run:
        try:
            scheduled = services_ai_scheduler.get_next_memory_reminder()
            if scheduled:
                current_scheduled_run = f"Time: {scheduled.next_run_time}\nReason: {scheduled.reason}\nTopic: {scheduled.topic}"
        except Exception as e:
            logger.error(f"Error collecting current scheduled run: {e}")

    # Fetch current user location for context
    current_location = None
    try:
        current_location = await get_current_geofence_for_user()
    except Exception as e:
        logger.error(f"Error fetching current location: {e}")

    # Fetch day plans for today and tomorrow
    today_plan = None
    tomorrow_plan = None
    try:
        today = now_user_tz().date()
        tomorrow = today + datetime.timedelta(days=1)
        today_plan = day_planner_service.get_formatted_plan(today)
        tomorrow_plan = day_planner_service.get_formatted_plan(tomorrow)
    except Exception as e:
        logger.error(f"Error fetching day plans: {e}")

    # Format memories, actions, and day plans for AI analysis
    recent_executed = services_ai_scheduler.get_recent_executed_reminders(limit=5)
    formatted_input = _format_memories_for_analysis(memories, recent_executed, current_location, today_plan, tomorrow_plan)

    # Add conversation history if available
    if conversation_history:
        formatted_input += f"\n\nRecent conversation history with user:\n{conversation_history}"

    # Add current scheduled run for re-evaluation if available
    if current_scheduled_run:
        formatted_input += f"\n\nCurrently scheduled next run (please re-evaluate if this is still optimal):\n{current_scheduled_run}"

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
                logger.debug(f"Choosing deterministic reminder: {deterministic.reason} at {deterministic.next_run_time}")
                logger.debug(f"AI-suggested reminder was: {validated_ai.reason} at {validated_ai.next_run_time}")
            else:
                chosen = NextRun(next_run_time=validated_ai.next_run_time, reason=validated_ai.reason, topic=validated_ai.topic)

        # Finally schedule the chosen next run
        ai_scheduler.schedule_next_run(chosen)

    except Exception as e:
        logger.error(f"Error during AI analysis: {e}")
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

    services_ai_scheduler.schedule_deferred_run(
        _determine_next_run_by_memory_impl
    )


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


def _format_memories_for_analysis(memories, recent_executed_reminders: List[ExecutedReminder], current_location: str = None, today_plan: str = None, tomorrow_plan: str = None) -> str:
    """Format memories for AI analysis: uses summarizer for observations/preferences, detailed format for reminders"""
    
    # Separate reminders from observations and preferences
    reminders = {}
    for memory_id, entry in memories.items():
        if entry.type == "reminder":
            reminders[memory_id] = entry
    
    # Build memory text
    memory_text = ""
    
    # Add summarized observations and preferences from the summarizer service
    summary = memory_summarizer_service.get_summary()
    if summary:
        memory_text += "User Context (Observations & Preferences):\n\n"
        if summary.summarized_observations:
            memory_text += summary.summarized_observations + "\n\n"
        if summary.summarized_preferences:
            memory_text += summary.summarized_preferences + "\n\n"
    
    # Add detailed reminders
    if reminders:
        memory_text += "Stored Reminders:\n\n"
        for memory_id, entry in reminders.items():
            memory_text += f"Content: {entry.content}\n"
            if entry.place:
                memory_text += f"Place: {entry.place}\n"
            
            ro = entry.reminder_options
            if ro:
                # One-time reminder
                if ro.datetime_value:
                    dt_local = to_user_tz(ro.datetime_value)
                    memory_text += f"Type: One-time\n"
                    memory_text += f"Scheduled for: {dt_local.strftime('%Y-%m-%d %H:%M:%S')}\n"

                # Recurring reminder
                if ro.time_value:
                    memory_text += f"Type: Recurring\n"
                    memory_text += f"Time: {ro.time_value}\n"
                    if ro.days_of_week and len(ro.days_of_week) > 0:
                        memory_text += f"Days: {', '.join(ro.days_of_week)}\n"
                    else:
                        memory_text += f"Days: Daily\n"

                    # Calculate and show next occurrence
                    try:
                        next_occurrence = _calculate_next_reminder_occurrence(ro)
                        if next_occurrence:
                            memory_text += f"Next occurrence: {next_occurrence.strftime('%Y-%m-%d %H:%M:%S')}\n"
                    except Exception:
                        pass
            
            memory_text += "\n"

    # Add recent executed memory reminder jobs
    actions_text = "\nRecent executed memory reminder jobs:\n\n"
    if recent_executed_reminders and len(recent_executed_reminders) > 0:
        for er in recent_executed_reminders:
            ts = er.executed_at.isoformat()
            topic = er.topic
            actions_text += f"Job run at {ts} with topic {topic}\n\n"
    else:
        actions_text += "No recent executed reminders recorded.\n"

    # Add day plans
    day_plan_text = "\nPredicted Day Plans:\n\n"
    if today_plan:
        day_plan_text += "Today's Plan:\n"
        day_plan_text += today_plan + "\n"
    else:
        day_plan_text += "Today's Plan: Not available\n\n"
    
    if tomorrow_plan:
        day_plan_text += "\nTomorrow's Plan:\n"
        day_plan_text += tomorrow_plan + "\n"
    else:
        day_plan_text += "Tomorrow's Plan: Not available\n\n"

    current_time = now_user_tz()
    context_text = f"Current date and time: {current_time.strftime('%A, %B %d, %Y at %H:%M')}\n"

    # Add current user location if available
    if current_location:
        context_text += f"Current user location: {current_location}\n"

    context_text += "\n"

    return context_text + memory_text + actions_text + day_plan_text

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
