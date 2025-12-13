import logging
import os
from typing import Optional

from agents import Agent, ModelSettings, Runner, RunConfig
from pydantic import BaseModel

from components.agent_hooks import CustomAgentHooks
from components.timezone_utils import now_user_tz

logger = logging.getLogger(__name__)

AI_MEMORY_SUMMARIZER_MODEL = os.getenv("AI_MEMORY_SUMMARIZER_MODEL", "gpt-5-mini")


class MemorySummaryResult(BaseModel):
    summarized_preferences: str
    summarized_observations: str
    summarized_reminders: str


memory_summarizer_agent = Agent(
    name='Memory Summarizer',
    model=AI_MEMORY_SUMMARIZER_MODEL,
    model_settings=ModelSettings(),
    instructions="""
You are the memory summarization component of Yume, an AI assistant. Your sole responsibility is to create concise, detailed summaries of the user's memories without losing important information.

You will receive three types of memories and must produce summarized versions of each that:
1. Preserve all critical information and details
2. Remove redundancy and obvious/repetitive content
3. Are more concise than the originals while maintaining clarity
4. Can be used directly in AI agent instructions/context

Your output must include three components:

1. **Summarized Preferences**: Extract all user preferences that affect how you should interact with the user. Combine related preferences intelligently. Examples:
   - "User prefers brief, direct communication via messaging app; no markdown formatting; max 1-2 emojis; natural language dates/times"
   - "Prefers morning updates at 7 AM and wellness checks only twice weekly; dislikes multiple questions in one message"

2. **Summarized Observations**: Extract factual observations about the user's life. Preserve dates, contexts, and behavioral patterns. Examples:
   - "Birthday: December 15th; Started new job September 1st as Software Engineer at TechCorp"
   - "Exercise routine: Gym visits 3x/week; Prefers working from home on Fridays; Currently stressed about Q4 deadlines"

3. **Summarized Reminders**: Consolidate task-based and location-based reminders into a coherent summary. Preserve timing, triggers, and actionability. Examples:
   - "Recurring: Daily exercise at 6 PM; Weekly grocery shopping (Thursdays); Check weather when arriving at work"
   - "One-time: Doctor appointment Dec 20th at 2 PM; Submit project report by Dec 31st"

Guidelines:
- Be specific: Keep dates, times, locations, and numeric details
- Be concise: Eliminate redundancy while preserving essential information
- Be actionable: Summaries must be clear enough for the AI to use without additional context
- Preserve intent: Capture why something matters, not just facts
- Maintain accuracy: Never generalize away important details
- Use clear formatting: Group related items logically within each summary
- Keep context: When information relates to broader patterns, explain the pattern
""",
    hooks=CustomAgentHooks(),
    output_type=MemorySummaryResult
)


async def summarize_memories(
    formatted_preferences: str,
    formatted_observations_and_reminders: str
) -> Optional[MemorySummaryResult]:
    """
    Summarize memories using the memory summarizer agent.
    
    Args:
        formatted_preferences: Formatted string of user preferences
        formatted_observations_and_reminders: Formatted string of observations and reminders
    
    Returns:
        MemorySummaryResult with summarized preferences, observations, and reminders,
        or None if an error occurs
    """
    logger.info("Starting memory summarization process")
    
    current_time = now_user_tz()
    agent_input = f"""Current date and time: {current_time.strftime('%Y-%m-%d %H:%M:%S %Z')}

Please summarize the following user memories. Preserve all important details while making them more concise and actionable.

USER PREFERENCES:
{formatted_preferences}

OBSERVATIONS AND REMINDERS:
{formatted_observations_and_reminders}

Create three summarized versions that can be directly used in AI agent context. Be thorough - do not lose details while improving conciseness."""

    try:
        response = await Runner.run(memory_summarizer_agent, agent_input, run_config=RunConfig(tracing_disabled=True))
        result = response.final_output_as(MemorySummaryResult)
        
        logger.info("Memory summarization completed successfully")
        return result
    except Exception as e:
        logger.error(f"Error during memory summarization: {e}")
        raise
