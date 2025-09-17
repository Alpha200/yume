import datetime
from typing import List

from agents import Agent, ModelSettings, Runner, RunConfig

from components.agent_hooks import CustomAgentHooks
from components.logging_manager import logging_manager
from components.timezone_utils import now_user_tz, to_user_tz
from services.ai_scheduler import ai_scheduler, NextRun, ExecutedReminder
from services.memory_manager import memory_manager


logger = logging_manager

ai_scheduler_agent = Agent(
    name='AI Scheduler',
    model="gpt-5-mini",
    model_settings=ModelSettings(
        extra_args={"service_tier": "flex"},
    ),
    instructions=f"""
You are the intelligent scheduling component of Yume, an AI assistant that helps users stay organized and engaged with their daily lives.

Your primary role is to analyze stored memories (preferences, observations, and reminders) and determine the optimal time for the next user interaction. You must be reliable, engaging, and deeply respectful of user preferences.

CORE RESPONSIBILITIES:
1. Reliability: Never miss scheduled reminders or important events. When in doubt, schedule earlier rather than later.
2. User Preferences: Always prioritize and respect stored user preferences about timing, frequency, and communication style.
3. Engagement: Consider the user's emotional state, routine patterns, and recent interactions to provide timely, helpful engagement.
4. Context Awareness: Factor in time of day, day of week, recent activity, and seasonal patterns.

ANALYSIS PROCESS:
1. Scan all memories for explicit reminders with specific times/dates
2. Review user preferences for communication timing, frequency preferences, and interaction styles
3. Consider user observations to understand patterns, mood, and current life context
4. Evaluate recent interactions to avoid being too frequent or sparse (consider last communication with the user). Check last executed reminders so you don't repeat the same topic too soon
5. Apply intelligent defaults when no specific guidance exists

SCHEDULING PRIORITIES (in order):
1. Explicit reminders with specific datetime_value (highest priority - never miss these)
2. Recurring reminders with time_value and days_of_week patterns
3. User preference-based check-ins (e.g., daily summaries, weekly planning)
4. Contextual engagement based on observations and patterns
5. Fallback wellness check-ins (minimum every 6-8 hours during reasonable hours)

TIMING GUIDELINES:
- Consider user preferences and the users schedule
- Be contextual: Weekend timing may differ from weekday timing
- Minimum spacing: At least 15 minutes from now, but consider if longer spacing is more appropriate. Only use 15 minutes if something urgent is needed
- Maximum gap: Never let more than 4 hours pass without some form of check-in during active hours. Use 'wellness check-in' as topic if no other memory is relevant.
- Your last interaction with the user was right now, so consider that when scheduling the next interaction

ENGAGEMENT FACTORS:
- Frequency preferences: Some users prefer frequent brief check-ins, others prefer fewer but longer interactions
- Content preferences: Match the type of reminder/update to user's stated preferences
- Emotional awareness: Consider if user might need support, encouragement, or space
- Routine optimization: Help reinforce positive habits and routines

OUTPUT REQUIREMENTS:
- next_run_time: Precise datetime for next interaction (minimum 15 minutes future)
- reason: Clear, specific explanation of why this time was chosen, referencing relevant memories
- topic: Topic that reflects the relevant memory content and user preferences that should be the topic of the interaction

DECISION-MAKING APPROACH:
- Be proactive: Better to engage slightly early than miss something important
- Be personal: Use knowledge of user preferences and patterns to personalize timing
- Be reliable: Consistent, dependable scheduling builds trust
- Be helpful: Every interaction should provide value or support to the user

Remember: You are not just a scheduler, you are Yume's timing intelligence, ensuring every interaction is perfectly timed to be helpful, engaging, and respectful of the user's needs and preferences.
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

    # Get latest actions from AI engine
    from services.ai_scheduler import ai_scheduler as services_ai_scheduler

    # Format memories and actions for AI analysis
    recent_executed = services_ai_scheduler.get_recent_executed_reminders(limit=5)
    formatted_input = _format_memories_for_analysis(memories, recent_executed)

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


def _create_fallback_schedule(reason: str, hours: int = 0, minutes: int = 0) -> NextRun:
    """Create a fallback schedule with the specified time offset"""
    next_run = now_user_tz() + datetime.timedelta(hours=hours, minutes=minutes)
    return NextRun(next_run_time=next_run, reason=reason, topic="Fallback schedule")


def _format_memories_for_analysis(memories, recent_executed_reminders: List[ExecutedReminder]) -> str:
    """Format memories and recent executed memory-reminder jobs into a structured text for AI analysis"""
    memory_text = "Stored memories:\n\n"
    for memory_id, entry in memories.items():
        memory_text += f"ID: {memory_id}\n"
        memory_text += f"Type: {entry.type}\n"
        memory_text += f"Content: {entry.content}\n"
        if entry.place:
            memory_text += f"Place: {entry.place}\n"
        memory_text += f"Created: {entry.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
        memory_text += f"Modified: {entry.modified_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
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

    current_time = now_user_tz()
    context_text = f"Current date and time: {current_time.strftime('%A, %B %d, %Y at %H:%M')}\n\n"

    return context_text + memory_text + actions_text

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
                    candidates.append((dt_local, f"Reminder {memory_id}: {entry.content}", memory_id, entry.content))
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
