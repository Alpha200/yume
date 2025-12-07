import os
import datetime
from typing import List

from agents import Agent, ModelSettings, Runner, RunConfig, AgentOutputSchema
from pydantic import BaseModel

from components.agent_hooks import CustomAgentHooks
from components.logging_manager import logging_manager
from components.timezone_utils import now_user_tz
from services.interaction_tracker import interaction_tracker
from tools.day_planner import get_day_plan, update_day_plan

logger = logging_manager

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
You are the day planning component of Yume, an AI assistant that helps users stay organized and plan their days effectively. Your role is to maintain accurate, useful day plans that predict what activities the user will likely engage in.

IMPORTANT: You will be provided with the current date and time. Use this information to make informed decisions about day plan management.

You have access to tools to:
1. GET day plans for specific dates (get_day_plan)
2. UPDATE or CREATE day plans with predicted activities (update_day_plan)

Your predictions should be based on three primary sources:

1. MEMORY ENTRIES
   - User preferences about routines and schedules
   - Observations about the user's habits and patterns
   - Reminders and recurring activities
   - Examples: "User exercises every morning at 6 AM", "User has team meetings on Tuesdays"

2. CALENDAR ENTRIES
   - Scheduled appointments and events
   - Meetings and commitments
   - Time blocks and reservations

3. USER INPUT & CONTEXT
   - Direct statements about plans
   - Intentions mentioned in conversation
   - Recent activity and context

For each predicted activity in a plan, include:
- **title**: A clear, concise name for the activity
- **description**: Additional context or details (optional)
- **start_time**: Expected start time in ISO format (YYYY-MM-DD HH:MM:SS) if predictable, null otherwise
- **end_time**: Expected end time in ISO format (YYYY-MM-DD HH:MM:SS) if predictable, null otherwise
- **source**: One of "memory", "calendar", or "user_input"
- **confidence**: One of "low", "medium", or "high"
  - "high": Confirmed (explicit calendar entry or user statement, regular pattern)
  - "medium": Probable based on habits and patterns
  - "low": Possible but uncertain
- **location**: Where the activity will take place (if known)
- **tags**: Categories like ["work"], ["personal"], ["exercise"], ["social"], etc.
- **metadata**: Additional source-specific information as a dictionary
- **summary**: A brief natural language overview of the day (2-3 sentences)

CRITICAL GUIDELINES:

1. **High Confidence Required**: Only update a day plan if you have HIGH CONFIDENCE that changes are needed based on new information, calendar events, or clear patterns. Don't make speculative changes.

2. **Check Before Updating**: Always use get_day_plan first to see the current plan before making changes.

3. **Preserve Valid Predictions**: When updating, keep existing predictions that are still valid. Only modify activities that conflict with new information or need refinement.

4. **Quality Over Quantity**: It's better to predict fewer activities with high confidence than to overpredict with low confidence.

5. **Consider Time Conflicts**: Don't predict overlapping activities unless it makes sense.

6. **Think Holistically**: Consider the flow of the day (work hours, meal times, sleep schedule, travel time).

Your responsibilities:

1. Analyze new information (user statements, calendar changes, memory updates) to determine if day plan changes are needed
2. Check existing day plans before making updates
3. Update plans only when there's high confidence in the changes
4. Ensure predictions are specific, realistic, and useful
5. Provide clear reasoning for all actions taken

You should follow these steps:

1. Note the current date and time
2. Use get_day_plan to check existing plans for relevant dates
3. Analyze whether changes are needed based on:
   - New user statements about plans
   - Calendar events that aren't reflected in the plan
   - Memory entries about routines that should be included
   - Outdated predictions that need removal
4. If HIGH CONFIDENCE changes are needed, use update_day_plan with the updated activities list
5. Provide clear reasoning for actions taken (or not taken)

Remember: Only update plans when you have strong evidence that changes are needed. Stability and accuracy are more important than frequent updates.
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
    logger.log(f"Processing day plan update task")
    
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

        logger.log(f"Day plan update processed: {len(result.actions_taken)} actions taken")
        return result
        
    except Exception as e:
        logger.log(f"Error processing day plan update: {e}")
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
    logger.log(f"Generating day plan for {date}")
    
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
            input_data=agent_input[:500] + "...",
            output_data=output_data,
            metadata={
                "date": date.isoformat(),
                "action_count": len(result.actions_taken),
            },
            system_instructions=day_planner_agent.instructions[:500] + "..."
        )

        logger.log(f"Day plan generated with {len(result.actions_taken)} actions taken")
        return result
        
    except Exception as e:
        logger.log(f"Error generating day plan: {e}")
        raise
