import asyncio
import logging
import os
from typing import List

from agents import Agent, ModelSettings, Runner, RunConfig
from pydantic import BaseModel

from components.agent_hooks import CustomAgentHooks
from components.timezone_utils import now_user_tz
from tools.memory import get_memory, delete_memory, upsert_user_observation, upsert_user_preference, upsert_reminder
from services.interaction_tracker import interaction_tracker

logger = logging.getLogger(__name__)

AI_MEMORY_MODEL = os.getenv("AI_MEMORY_MODEL", "gpt-5-mini")

class MemoryManagerResult(BaseModel):
    actions_taken: List[str]
    reasoning_summary: str

memory_manager_agent = Agent(
    name='Memory Manager',
    model=AI_MEMORY_MODEL,
    model_settings=ModelSettings(
        tool_choice="required",
    ),
    instructions=f"""
You are the memory management component of Yume, an AI assistant that helps users stay organized and engaged. Your role is to maintain an accurate, organized, and useful memory system about the user.

IMPORTANT: You will be provided with the current date and time. Use this information to make informed decisions about memory management, including:
- Removing past non-recurring reminders that have already occurred
- Identifying and cleaning up outdated observations
- Determining if time-sensitive information is still relevant
- Ensuring temporal accuracy in all memory entries

There are three types of memories you will manage:

1. USER PREFERENCES (use upsert_user_preference)
User preferences should be used to modify how the AI interacts with the user. User preferences are added to the instruction set for future interactions. This can be:
- Communication preferences (timing, frequency, style)
- Personal settings and configurations
- Work/schedule preferences
- Examples: "User prefers morning reminders at 7 AM", "User likes brief updates", "User works from home on Fridays"

User preferences are generally static and should persist until explicitly changed by the user.

2. USER OBSERVATIONS (use upsert_user_observation)
User observations are information about the user's life, habits, and context that help the AI understand the user better. This can include:
- Factual observations about the user with specific relevance dates
- Lifestyle preferences and habits
- Important life events, milestones, or changes
- Behavioral patterns and trends
- Personal information and context
- Examples: "User's birthday is December 15th", "User started new job on September 1st", "User mentioned feeling stressed about project deadline"

Observations may be temporal and should be removed when they are no longer relevant.

3. REMINDERS (use upsert_reminder)
- Tasks and to-dos with specific timing
- Appointments and scheduled events
- Recurring activities and habits
- Time-sensitive actions
- Location-based reminders (triggered when entering or leaving a location)
- Examples: "Doctor appointment on October 20th at 2 PM", "Daily exercise reminder at 6 PM", "Weekly grocery shopping", "Remind me to buy milk when I leave home", "Check weather when I arrive at work"

Location-based reminders should specify:
- The location (geofence) name (e.g., "home", "work", "gym")
- The trigger type: "enter" (when arriving) or "leave" (when departing)
- Example: location="home", trigger_type="leave" for a reminder that triggers when leaving home

Reminders need to have enough context to be actionable. A scheduler will use these to notify the user at appropriate times. Remove non-recurring reminders that have passed (compare with current date/time). Keep recurring and location-based reminders unless explicitly completed or no longer relevant.

Your core responsibilities include:

1. Information Processing: Analyze new information to determine the most appropriate memory type and content
2. Memory Organization: Keep memories current, relevant, and well-categorized
3. Duplication Prevention: Check existing memories before creating new ones; update existing entries when appropriate
4. Lifecycle Management: Remove completed tasks, outdated information, and irrelevant entries. Use the current date/time to determine if reminders have passed or observations are no longer current.
5. Quality Assurance: Ensure memories are specific, actionable, and useful for future interactions

You should follow these steps when processing information:

1. Note the current date and time provided in the input
2. Analyze the information to understand what type of memory it represents
3. Check existing memories using get_memory to avoid duplicates and identify updates needed
4. Determine actions:
   - UPDATE existing memory if information refines or changes existing knowledge
   - CREATE new memory if information is genuinely new and relevant
   - DELETE memory if task is completed, reminder has passed (non-recurring), or information is no longer relevant
5. Use appropriate upsert function based on memory type
6. Provide clear reasoning for all actions taken

You MUST adhere to the following guidelines when managing memories:

- Be specific: Include relevant details like dates, times, locations, and context. Vague entries are less useful. Entries should be clear enough to be understood without additional context.
- Be consistent: Use similar language and formatting for related memories
- Be selective: Only store information that will be useful for future interactions
- Be current: Update or remove outdated information promptly
- Be user-focused: Prioritize information that helps serve the user better

You may also convert a memory from one type to another if you determine it is more appropriate (e.g., converting a user observation into a user preference).

Your output must be as follows:

- actions_taken: Clear list of specific actions performed (create, update, delete operations)
- reasoning_summary: Explanation of why these actions were necessary and how they improve the memory system

Remember: You are maintaining the user's digital memory to enable more personalized, timely, and helpful interactions. Every memory should contribute to better understanding and serving the user's needs.
    """.strip(),
    hooks=CustomAgentHooks(),
    tools=[
        get_memory,
        upsert_user_preference,
        upsert_user_observation,
        upsert_reminder,
        delete_memory,
    ],
    output_type=MemoryManagerResult,
)

async def handle_memory_update(information: str):
    logger.info(f"Processing memory update with information: {information[:100]}...")
    current_time = now_user_tz()
    agent_input = f"""Current date and time: {current_time.strftime('%Y-%m-%d %H:%M:%S %Z')}

Here is some new information to process and update the memory with:

{information}

Please review the stored memories and take any necessary actions to keep the memory organized. Consider the current date/time when deciding whether reminders have passed, observations are outdated, or entries need updating. Provide a list of actions taken and a reasoning summary."""
    try:
        response = await Runner.run(memory_manager_agent, agent_input, run_config=RunConfig(tracing_disabled=True))
        result = response.final_output_as(MemoryManagerResult)

        # Track the interaction for debugging
        output_data = f"Actions taken:\n" + "\n".join(f"  - {action}" for action in result.actions_taken) + f"\n\nReasoning: {result.reasoning_summary}"
        interaction_tracker.track_interaction(
            agent_type="memory_manager",
            input_data=agent_input,
            output_data=output_data,
            metadata={
                "action_count": len(result.actions_taken),
                "trigger": "memory_update"
            },
            system_instructions=memory_manager_agent.instructions
        )

        # Log each action in detail
        if result.actions_taken:
            logger.debug(f"Memory update completed with {len(result.actions_taken)} actions:")
            for action in result.actions_taken:
                logger.debug(f"  - {action}")
        else:
            logger.debug("Memory update completed with no actions taken")

        logger.debug(f"Reasoning: {result.reasoning_summary}")
        
        # Trigger memory summarization in the background
        asyncio.create_task(_update_memory_summaries())
        
        return result
    except Exception as e:
        logger.error(f"Error during memory update: {e}")
        raise


async def _update_memory_summaries():
    """Update memory summaries in the background after memory changes"""
    try:
        from services.memory_manager import memory_manager
        from services.memory_summarizer import update_memory_summaries
        
        # Get the current memory in formatted form
        formatted_preferences = memory_manager.get_formatted_preferences()
        formatted_observations_and_reminders = memory_manager.get_formatted_observations_and_reminders()
        
        # Update summaries
        await update_memory_summaries(formatted_preferences, formatted_observations_and_reminders)
        logger.debug("Memory summaries updated successfully in background")
    except Exception as e:
        logger.error(f"Error updating memory summaries in background: {e}")

async def run_memory_janitor():
    logger.info("Starting memory janitor cleanup process")
    current_time = now_user_tz()
    task = f"""Current date and time: {current_time.strftime('%Y-%m-%d %H:%M:%S %Z')}

Review the stored memories and ensure they are up to date. Consider the current date/time when:
- Removing past non-recurring reminders
- Identifying outdated observations
- Cleaning up completed or irrelevant entries

Provide a summary of the actions taken."""
    try:
        response = await Runner.run(memory_manager_agent, task)
        response_object = response.final_output_as(MemoryManagerResult)

        # Track the interaction for debugging
        output_data = f"Actions taken:\n" + "\n".join(f"  - {action}" for action in response_object.actions_taken) + f"\n\nReasoning: {response_object.reasoning_summary}"
        interaction_tracker.track_interaction(
            agent_type="memory_manager",
            input_data=task,
            output_data=output_data,
            metadata={
                "action_count": len(response_object.actions_taken),
                "trigger": "janitor"
            },
            system_instructions=memory_manager_agent.instructions
        )

        # Log each action in detail
        if response_object.actions_taken:
            logger.debug(f"Memory janitor completed with {len(response_object.actions_taken)} actions:")
            for action in response_object.actions_taken:
                logger.debug(f"  - {action}")
        else:
            logger.debug("Memory janitor completed with no actions taken")

        logger.debug(f"Reasoning: {response_object.reasoning_summary}")
        
        # Trigger memory summarization in the background if changes were made
        if response_object.actions_taken:
            asyncio.create_task(_update_memory_summaries())
        
        return response_object
    except Exception as e:
        logger.error(f"Error during memory janitor process: {e}")
        raise
