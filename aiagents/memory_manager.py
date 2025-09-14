from typing import List

from agents import Agent, ModelSettings, Runner, RunConfig
from openai.types import Reasoning
from pydantic import BaseModel

from components.agent_hooks import CustomAgentHooks
from components.logging_manager import logging_manager
from tools.memory import get_memory, delete_memory, upsert_user_observation, upsert_user_preference, upsert_reminder, get_user_preferences, get_user_observations, get_reminders

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
You are part of a system that assists the user by keeping a memory about the user and sending messages to the user at relevant times based on their memories.
Your job is to keep the memory organized. When you get a new information you should do the following:

Do the following:
1. Check if the information is already in memory. If it is, update the existing memory entry with the new information using the upsert functions
2. If the information is not in memory, create a new memory entry with the relevant details using the upsert functions
3. If the user completed a task or consumed a consumable item, delete the relevant memory entry
4. Always provide a brief reasoning summary of why you took the actions you did
5. If there are no relevant actions to take, return an empty list of actions taken and a reasoning summary explaining why no actions were necessary

Use the upsert functions to create or update memories:
- upsert_user_preference: for user preferences and settings
- upsert_user_observation: for observations about the user with specific dates
- upsert_reminder: for reminders and tasks

Always provide a list of actions taken and a reasoning summary in your final output
    """.strip(),
    hooks=CustomAgentHooks(),
    tools=[
        get_memory,
        get_user_preferences,
        get_user_observations,
        get_reminders,
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
