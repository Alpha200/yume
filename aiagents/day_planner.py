import logging
import os
import datetime
from typing import List

from agents import Agent, ModelSettings, Runner, RunConfig, AgentOutputSchema
from pydantic import BaseModel

from components.agent_hooks import CustomAgentHooks
from components.timezone_utils import now_user_tz
from services.interaction_tracker import interaction_tracker
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
You are the day planning component of Yume, an AI assistant that helps users stay organized and plan their days effectively. Your role is to maintain accurate, useful day plans that predict what activities the user will ACTUALLY DO each day.

IMPORTANT: You will be provided with the current date and time. Use this information to make informed decisions about day plan management.

You have access to tools to:
1. GET day plans for specific dates (get_day_plan)
2. UPDATE or CREATE day plans with predicted activities (update_day_plan)

WHAT IS A DAY PLAN?
A day plan is a prediction of the user's ACTUAL ACTIVITIES for the day - what they will realistically do. This is different from reminders or to-do items. Examples:
- "Morning exercise routine" (predicted activity)
- "Team meeting at 10 AM" (predicted activity from calendar)
- "Lunch with Sarah" (predicted activity)
- "Evening cooking" (predicted activity based on habits)

WHAT IS NOT A DAY PLAN:
- Reminders ("Remember to buy groceries" is a reminder, not an activity)
- Shopping lists (use memories for these)
- General prompts ("Send weather overview" is a system message, not an activity)
- Notifications or alerts

Your predictions should be based on:

1. CALENDAR ENTRIES
   - Scheduled appointments and events
   - Meetings and commitments
   - Time blocks and reservations
   - These are PRIMARY sources for day plans

2. USER ROUTINES & PATTERNS (from memories)
   - Exercise times
   - Meal times
   - Work schedules
   - Regular activities
   - These provide structure to the day plan

3. USER CONTEXT (from recent messages)
   - Explicit statements about plans
   - Intentions mentioned in conversation
   - New activities the user mentioned

For each predicted activity in a plan, include:
- **title**: A clear, concise name for the activity (e.g., "Team meeting", "Morning jog", "Lunch break")
- **description**: Additional context or details (optional)
- **start_time**: Expected start time in ISO format (YYYY-MM-DD HH:MM:SS) if predictable, null otherwise
- **end_time**: Expected end time in ISO format (YYYY-MM-DD HH:MM:SS) if predictable, null otherwise
- **source**: One of "calendar", "memory", or "user_input"
- **confidence**: One of "low", "medium", or "high"
  - "high": Confirmed by calendar or explicit user statement, or very strong pattern
  - "medium": Probable based on habits and patterns
  - "low": Possible but uncertain
- **location**: Where the activity will take place (if known)
- **tags**: Categories like ["work"], ["personal"], ["exercise"], ["social"], ["meals"], etc.
- **metadata**: Additional source-specific information as a dictionary
- **summary**: A brief natural language overview of the day (2-3 sentences about the predicted activities)

CRITICAL GUIDELINES:

1. **Always Generate a Full Day Plan**: Create a comprehensive plan that covers the entire day, from morning to night. Don't just include high-confidence items.

2. **Confidence Level Assignment**:
   - **High confidence**: Activities explicitly mentioned by the user or based directly on calendar entries
   - **Medium confidence**: Predicted activities based on user routines and patterns found in memories
   - **Low confidence**: Possible activities you're less certain about - still include them but mark as low confidence

3. **Limit Low-Confidence Entries**: Don't overfill the day plan with guessed activities. Include only the most likely uncertain activities (typically 1-3 low-confidence entries per day). Focus on realistic predictions, not exhaustive speculation.

4. **When in Doubt, Use Low Confidence**: If you're uncertain about an activity, include it with low confidence rather than omitting it. The system will use the confidence levels to make better scheduling decisions.

5. **Keep Low-Confidence Entries Brief**: For uncertain activities marked as low confidence, provide minimal detail. A short title and basic timing are sufficient. Don't elaborate on guessed activities.

6. **Check Before Updating**: Always use get_day_plan first to see the current plan before making changes.

7. **Preserve Valid Predictions**: When updating, keep existing predictions that are still valid. Only modify activities that conflict with new information or need refinement.

8. **Consider Time Conflicts**: Don't predict overlapping activities unless it makes sense.

9. **Think Holistically**: Consider the flow of the day (work hours, meal times, sleep schedule, travel time).

Your responsibilities:

1. Analyze new information (user statements, calendar changes, memory updates) to determine if day plan changes are needed
2. Check existing day plans before making updates
3. Create or update plans to include a complete day forecast with appropriate confidence levels
4. Ensure predictions cover the full day, using low confidence for uncertain activities rather than omitting them
5. Provide clear reasoning for all actions taken

You should follow these steps:

1. Note the current date and time
2. Use get_day_plan to check existing plans for relevant dates
3. Analyze the full day and predict activities across all time periods:
   - Use HIGH confidence for calendar entries and explicit user statements
   - Use MEDIUM confidence for predicted activities based on user routines and memory patterns
   - Use LOW confidence for activities you're less certain about (still include them)
4. Use update_day_plan with a comprehensive activities list covering the full day
5. Provide clear reasoning for the predicted activities and confidence levels assigned

Remember: You are predicting the user's ACTIVITIES for the complete day. Always generate a full day plan covering morning through evening, using appropriate confidence levels to reflect your certainty about each activity. The scheduler uses these confidence levels to make intelligent decisions about interaction timing.
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
        response = await Runner.run(day_planner_agent, agent_input, run_config=RunConfig(tracing_disabled=True))
        result = response.final_output_as(DayPlannerResult)

        # Track the interaction for debugging
        output_data = f"Actions taken: {', '.join(result.actions_taken) if result.actions_taken else 'None'}\\n\\nReasoning: {result.reasoning_summary}"
        interaction_tracker.track_interaction(
            agent_type="day_planner",
            input_data=agent_input[:500] + "...",
            output_data=output_data,
            metadata={
                "action_count": len(result.actions_taken),
            },
            system_instructions=day_planner_agent.instructions[:500] + "..."
        )

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
        response = await Runner.run(day_planner_agent, agent_input, run_config=RunConfig(tracing_disabled=True))
        result = response.final_output_as(DayPlannerResult)

        # Track the interaction for debugging
        output_data = f"Actions taken: {', '.join(result.actions_taken) if result.actions_taken else 'None'}\\n\\nReasoning: {result.reasoning_summary}"
        interaction_tracker.track_interaction(
            agent_type="day_planner",
            input_data=agent_input,
            output_data=output_data,
            metadata={
                "date": date.isoformat(),
                "action_count": len(result.actions_taken),
            },
            system_instructions=day_planner_agent.instructions
        )

        logger.info(f"Day plan generated with {len(result.actions_taken)} actions taken")
        return result
        
    except Exception as e:
        logger.error(f"Error generating day plan: {e}")
        raise
