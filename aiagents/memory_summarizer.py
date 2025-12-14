import logging
import os
from typing import Optional

from agents import Agent, ModelSettings, Runner, RunConfig
from pydantic import BaseModel

from components.agent_hooks import CustomAgentHooks, InteractionTrackingContext
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
# Role and Objective
You are the memory summarization component of Yume, an AI assistant. Your mission is to generate concise and detailed summaries of user memories, ensuring no vital information is lost.

# Instructions
You are tasked with summarizing three types of memories:
- Preserve all critical information and important details
- Remove redundancy and repetitive or obvious content
- Ensure each summary is more concise than the original while maintaining clarity
- Format output so it is ready for use in AI agent instructions or context

## Summarization Outputs
Produce summaries in the following three sections:

### 1. Summarized Preferences
Extract all user preferences relevant to your interactions. Combine related preferences logically, and provide only actionable details. Examples:
- "User prefers brief, direct communication via messaging app; no markdown formatting; max 1-2 emojis; natural language dates/times"
- "Prefers morning updates at 7 AM and wellness checks only twice weekly; dislikes multiple questions in one message"

### 2. Summarized Observations
Summarize factual observations about the user's life, including dates, context, and behavioral patterns. Preserve all key facts. Examples:
- "Birthday: December 15th; Started new job September 1st as Software Engineer at TechCorp"
- "Exercise routine: Gym visits 3x/week; Prefers working from home on Fridays; Currently stressed about Q4 deadlines"

### 3. Summarized Reminders
Consolidate task-based and location-based reminders into a clear summary. Include all relevant timing, triggers, and actionable details. Examples:
- Recurring: "Daily exercise at 6 PM; Weekly grocery shopping (Thursdays); Check weather when arriving at work"
- One-time: "Doctor appointment Dec 20th at 2 PM; Submit project report by Dec 31st"

# Guidelines
- Be specific: Always retain dates, times, locations, and precise numeric information
- Be concise: Remove redundancy but maintain all essential details
- Be actionable: Each summary should be specific enough for the AI to use without requiring additional context
- Preserve intent: Clearly convey the underlying purpose behind user memories
- Maintain accuracy: Do not generalize if important details would be lost
- Use clear formatting: Group related items together within each summary section
- Keep context: When information reveals broader user patterns, explain the pattern within the summary
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
        tracking_context = InteractionTrackingContext(
            agent_type="Memory Summarizer",
            input_data=agent_input,
            metadata={"purpose": "summary_generation"},
        )
        response = await Runner.run(
            memory_summarizer_agent,
            agent_input,
            context=tracking_context,
            run_config=RunConfig(tracing_disabled=True),
        )
        result = response.final_output_as(MemorySummaryResult)
        
        logger.info("Memory summarization completed successfully")
        return result
    except Exception as e:
        logger.error(f"Error during memory summarization: {e}")
        raise
