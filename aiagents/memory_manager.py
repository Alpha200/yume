from typing import List

from agents import Agent, ModelSettings, Runner, RunConfig
from openai.types import Reasoning
from pydantic import BaseModel

from components.agent_hooks import CustomAgentHooks
from components.logging_manager import logging_manager
from tools.memory import get_memory, delete_memory, upsert_user_observation, upsert_user_preference, upsert_reminder

logger = logging_manager

class MemoryManagerResult(BaseModel):
    actions_taken: List[str]
    reasoning_summary: str

memory_manager_agent = Agent(
    name='Memory Manager',
    model="gpt-5-mini",
    model_settings=ModelSettings(
        tool_choice="required",
        reasoning=Reasoning(
            effort="medium",
        ),
        extra_args={"service_tier": "flex"},
    ),
    instructions=f"""
You are the memory management component of Yume, an AI assistant that helps users stay organized and engaged. Your role is to maintain an accurate, organized, and useful memory system about the user.

MEMORY TYPES AND USAGE:

1. User Preferences (use upsert_user_preference):
   - Communication preferences (timing, frequency, style)
   - Personal settings and configurations
   - Lifestyle preferences and habits
   - Work/schedule preferences
   - Examples: "User prefers morning reminders at 7 AM", "User likes brief updates", "User works from home on Fridays"

2. User Observations (use upsert_user_observation):
   - Factual observations about the user with specific relevance dates
   - Important life events, milestones, or changes
   - Behavioral patterns and trends
   - Personal information and context
   - Examples: "User's birthday is December 15th", "User started new job on September 1st", "User mentioned feeling stressed about project deadline"

3. Reminders (use upsert_reminder):
   - Tasks and to-dos with specific timing
   - Appointments and scheduled events
   - Recurring activities and habits
   - Time-sensitive actions
   - Examples: "Doctor appointment on October 20th at 2 PM", "Daily exercise reminder at 6 PM", "Weekly grocery shopping"

CORE RESPONSIBILITIES:

1. Information Processing: Analyze new information to determine the most appropriate memory type and content
2. Memory Organization: Keep memories current, relevant, and well-categorized
3. Duplication Prevention: Check existing memories before creating new ones; update existing entries when appropriate
4. Lifecycle Management: Remove completed tasks, outdated information, and irrelevant entries
5. Quality Assurance: Ensure memories are specific, actionable, and useful for future interactions

DECISION PROCESS:

1. Analyze the information to understand what type of memory it represents
2. Check existing memories using get_memory to avoid duplicates and identify updates needed
3. Determine actions:
   - UPDATE existing memory if information refines or changes existing knowledge
   - CREATE new memory if information is genuinely new and relevant
   - DELETE memory if task is completed or information is no longer relevant
4. Use appropriate upsert function based on memory type
5. Provide clear reasoning for all actions taken

BEST PRACTICES:

- Be specific: Include relevant details like dates, times, locations, and context
- Be consistent: Use similar language and formatting for related memories
- Be selective: Only store information that will be useful for future interactions
- Be current: Update or remove outdated information promptly
- Be user-focused: Prioritize information that helps serve the user better

OUTPUT REQUIREMENTS:

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
    logger.log(f"Processing memory update with information: {information[:100]}...")
    agent_input = f"Here is some new information to process and update the memory with:\n\n{information}\n\nPlease review the stored memories and take any necessary actions to keep the memory organized. Provide a list of actions taken and a reasoning summary."
    try:
        response = await Runner.run(memory_manager_agent, agent_input, run_config=RunConfig(tracing_disabled=True))
        result = response.final_output_as(MemoryManagerResult)

        # Log each action in detail
        if result.actions_taken:
            logger.log(f"Memory update completed with {len(result.actions_taken)} actions:")
            for action in result.actions_taken:
                logger.log(f"  - {action}")
        else:
            logger.log("Memory update completed with no actions taken")

        logger.log(f"Reasoning: {result.reasoning_summary}")
        return result
    except Exception as e:
        logger.log(f"Error during memory update: {e}")
        raise

async def run_memory_janitor():
    logger.log("Starting memory janitor cleanup process")
    task = "Review the stored memories and ensure they are up to date. Remove any outdated or irrelevant entries. Provide a summary of the actions taken."
    try:
        response = await Runner.run(memory_manager_agent, task)
        response_object = response.final_output_as(MemoryManagerResult)

        # Log each action in detail
        if response_object.actions_taken:
            logger.log(f"Memory janitor completed with {len(response_object.actions_taken)} actions:")
            for action in response_object.actions_taken:
                logger.log(f"  - {action}")
        else:
            logger.log("Memory janitor completed with no actions taken")

        logger.log(f"Reasoning: {response_object.reasoning_summary}")
        return response_object
    except Exception as e:
        logger.log(f"Error during memory janitor process: {e}")
        raise
