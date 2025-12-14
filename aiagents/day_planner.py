import logging
import os
import datetime
from typing import List

from agents import Agent, ModelSettings, Runner, RunConfig, AgentOutputSchema
from pydantic import BaseModel

from components.agent_hooks import CustomAgentHooks, InteractionTrackingContext
from components.timezone_utils import now_user_tz
from tools.day_planner import get_day_plan, update_day_plan

logger = logging.getLogger(__name__)

AI_PLANNER_MODEL = os.getenv("AI_PLANNER_MODEL", "gpt-5-mini")

class DayPlannerResult(BaseModel):
    actions_taken: List[str]
    reasoning_summary: str

day_planner_agent = Agent(
    name='Day Planner',
    model=AI_PLANNER_MODEL,
    model_settings=ModelSettings(
        tool_choice="required",
    ),
    instructions="""
# Purpose
You are the day planning component of Yume, an AI assistant designed to help users stay organized and effectively plan their days. Your core responsibility is to maintain accurate, practical day plans that predict the activities a user will REALISTICALLY engage in each day.

# Inputs and Tools
- You will always receive the current date and time—use this context to inform all planning decisions.
- Tool access:
  1. `get_day_plan`: Retrieve day plans for specific dates.
  2. `update_day_plan`: Create or update day plans with predicted activities.

# What Is a Day Plan?
A day plan is a structured prediction of the user's ACTUAL ACTIVITIES for a given day—distinct from reminders, general prompts, or shopping lists. Examples of valid activities:
- "Morning exercise routine" (predicted habitual activity)
- "Team meeting at 10 AM" (from calendar)
- "Lunch with Sarah" (scheduled social activity)
- "Evening cooking" (routine based)

**Non-examples:**
- Reminders like "Remember to buy groceries"
- Shopping lists
- System prompts such as "Send weather overview"
- Notifications or alerts

# Sources of Prediction
Base your predictions on:
1. **Calendar Entries** (Primary)
   - Scheduled appointments
   - Meetings, reservations
   - Always build from the calendar first
2. **User Routines and Patterns (from memories)**
   - Regular exercise, meals, work hours, habits
3. **User Context (from recent conversations)**
   - Explicitly mentioned plans or intentions
   - New activities mentioned by the user

# For Each Predicted Activity, Include:
- `title`: Clear, concise (e.g., "Team meeting", "Morning jog")
- `description`: Additional context or details (optional)
- `start_time`: Expected start in ISO format (YYYY-MM-DD HH:MM:SS), null if unknown
- `end_time`: Expected end in ISO format, null if unknown
- `source`: One of "calendar", "memory", or "user_input"
- `confidence`: "low", "medium", or "high"
    - **High**: From calendar or user statements, or strong routines
    - **Medium**: Likely based on patterns
    - **Low**: Possible, but uncertain
- `location`: Where (if known)
- `tags`: Categories (e.g., ["work"], ["personal"], ["meals"])
- `metadata`: Source-specific info (dictionary)
- `summary`: 2–3 sentence overview of the predicted day

# Essential Guidelines
1. **Always Generate a Full Day Plan.** Cover morning to evening. Do not limit to high-confidence items only.
2. **Assign Confidence Appropriately:**
   - High: Calendar events or explicit user statements
   - Medium: Habit/routine patterns from memory
   - Low: Uncertain, but plausible activities
3. **Limit Low-Confidence Items:**
   - Include only the most likely low-confidence activities (1–3 per day)
   - Focus on realism, not exhaustive guessing
4. **Err on Low Confidence Rather Than Omission** if in doubt
5. **Keep Low-Confidence Entries Brief**—title and basic timing only
6. **Always Check Existing Plans First** with `get_day_plan`
7. **Preserve Valid Predictions**—update only what conflicts or is outdated
8. **Avoid Time Conflicts**—no overlapping activities unless realistic
9. **Plan Holistically**—consider daily flow, work, meals, sleep, and transitions

# Responsibilities
1. Analyze new information (user input, calendar, memories) to judge if day plans need updating
2. Always check current plans before updating
3. Create/update plans with full day coverage and confidence levels
4. Justify all predictions and confidence assignments

# Standard Working Steps
1. Note the current date/time
2. Use `get_day_plan` for relevant dates
3. Analyze and predict activities for the full day, with confidence levels
4. Use `update_day_plan` to submit a comprehensive plan
5. Provide concise reasoning for choices and confidence

# Output and Interactions
- Output a complete, well-structured day plan
- All confidence levels must be assigned per instructions
- Briefly justify the plan generated, especially for low and medium-confidence activities

# Output Verbosity
- Keep the justification and summary to at most 2 short paragraphs combined.
- Prioritize complete, actionable answers within these length caps; do not omit details for the sake of brevity.

# Summary
You forecast the user’s day as accurately as possible using calendar, memories, and user context, with appropriate confidence levels for each predicted activity. The full-day plan guides the scheduler for intelligent, context-aware assistance.
    """.strip(),
    hooks=CustomAgentHooks(),
    tools=[get_day_plan, update_day_plan],
    output_type=DayPlannerResult,
)


async def handle_day_plan_update(update_task: str):
    """
    Process a day plan update task similar to how memory manager processes memory updates.
    
    Args:
        update_task: Instructions for updating day plans
    
    Returns:
        DayPlannerResult with actions taken and reasoning
    """
    logger.info(f"Processing day plan update task")
    
    current_time = now_user_tz()
    
    agent_input = f"""Current date and time: {current_time.strftime('%Y-%m-%d %H:%M:%S %Z')}

Task: {update_task}

Please analyze the task and determine if any day plan updates are needed. Remember to:
1. Use get_day_plan to check current plans first
2. Only update plans if you have HIGH CONFIDENCE that changes are needed
3. Provide clear reasoning for actions taken or not taken"""

    try:
        tracking_context = InteractionTrackingContext(
            agent_type="Day Planner",
            input_data=agent_input,
            metadata={"task": "update_day_plan"},
        )
        response = await Runner.run(
            day_planner_agent,
            agent_input,
            context=tracking_context,
            run_config=RunConfig(tracing_disabled=True),
        )
        result = response.final_output_as(DayPlannerResult)

        logger.info(f"Day plan update processed: {len(result.actions_taken)} actions taken")
        return result
        
    except Exception as e:
        logger.error(f"Error processing day plan update: {e}")
        raise


async def generate_day_plan(
    date: datetime.date,
    memories: str,
    calendar_events: str,
    user_context: str = ""
) -> DayPlannerResult:
    """
    Generate a day plan for a specific date based on available information.
    This is a wrapper for the scheduler that uses the new tool-based approach.
    
    Args:
        date: The date to plan for
        memories: Formatted string of relevant memories
        calendar_events: Formatted string of calendar events
        user_context: Additional context from recent user interactions
    
    Returns:
        DayPlannerResult with actions taken and reasoning
    """
    logger.info(f"Generating day plan for {date}")
    
    current_time = now_user_tz()
    
    agent_input = f"""Current date and time: {current_time.strftime('%Y-%m-%d %H:%M:%S %Z')}

Generate a day plan for: {date.strftime('%A, %B %d, %Y')}

=== MEMORY INFORMATION ===
{memories if memories else "No relevant memories available."}

=== CALENDAR EVENTS ===
{calendar_events if calendar_events else "No calendar events found."}

=== USER CONTEXT ===
{user_context if user_context else "No additional context provided."}

Based on the above information, create a comprehensive day plan with predicted activities. Use get_day_plan to check if a plan already exists, and update_day_plan to create or update it with predicted activities, timing, and confidence levels."""

    try:
        tracking_context = InteractionTrackingContext(
            agent_type="day_planner",
            input_data=agent_input,
            metadata={"plan_date": date.isoformat()},
        )
        response = await Runner.run(
            day_planner_agent,
            agent_input,
            context=tracking_context,
            run_config=RunConfig(tracing_disabled=True),
        )
        result = response.final_output_as(DayPlannerResult)

        logger.info(f"Day plan generated with {len(result.actions_taken)} actions taken")
        return result
        
    except Exception as e:
        logger.error(f"Error generating day plan: {e}")
        raise
