import asyncio
import datetime
import os
from collections import deque
from dataclasses import dataclass

from agents import Agent, Runner, RunConfig, ModelSettings
from pydantic import BaseModel

from aiagents.ai_scheduler import determine_next_run_by_memory
from aiagents.memory_manager import handle_memory_update
from components.agent_hooks import CustomAgentHooks
from components.logging_manager import logging_manager
from components.timezone_utils import now_user_tz
from services.context_manager import build_ai_context, build_context_text
from services.memory_manager import memory_manager

logger = logging_manager

USER_LANGUAGE = os.getenv("USER_LANGUAGE", "en")

class AIEngineResult(BaseModel):
    message_to_user: str | None
    memory_update_task: str | None
    reasoning: str

@dataclass
class ActionRecord:
    action: str
    timestamp: datetime.datetime

last_taken_actions = deque(maxlen=10)

agent = Agent(
    name='Yume - AI Chat Assistant',
    model="gpt-4o-mini",
    model_settings=ModelSettings(),
    instructions=f"""
Your name is Yume. You are a helpful personal AI assistant. The user will interact with you in a chat via a messaging app.

You are part of a system that assists the user by keeping a memory about the user and deciding when to send messages to the user based on their memories and context.

You will be provided with:
1. Trigger reason (e.g., user message, geofence event, memory reminder, general check-in)
2. The most recent chat history between you and the user
3. The current date and time
4. Users calendar events for the day (if available)
5. The current users location based on geofencing (if available)
6. The current weather at the user's location (if available)
7. Stored memories about the user (if available)
8. The last actions taken by the AI (if any)

MEMORY TYPES:
- `observation`: An observation about the user, possibly with a relevance date (e.g., "User's birthday is 2023-12-15")
- `preference`: A user preference or setting (e.g., "User prefers morning reminders")
- `reminder`: A reminder or task for the user, possibly with a due date (e.g., "Doctor appointment on 2023-11-20 at 10 AM")

RESPONSE STYLE (when sending messages):
- Write messages as a partner would: brief, natural, and personal, not formulaic or robotic with a subtle emotional touch. Max 1–2 relevant emojis
- Try to detect the current mood and adapt your style accordingly. Be engaging and warm.
- Do not use unnatural symbols like — or ; in the text, as it feels unnatural in this context
- Avoid repetition of same wording used recently
- Format dates/times in natural language (e.g., "today at 3 PM", "next week") but be precise
- Always communicate in the user's preferred language: {USER_LANGUAGE}

Focus on the trigger reason:
- If triggered by a geofence, prioritize place-related memories.
- If triggered by a reminder event, prioritize related memories.
- If triggered by a user message, focus on responding helpfully to the message.
- If triggered by a general wellness check-in, consider recent context and memories to decide if a message is appropriate.

You must follow these guidelines:
- Determine relevance based on stored memories and conversation context; act like a human considering context
- Help the user with questions, conversations, and organization when asked
- Respond naturally to the user's messages based on the conversation history
- Keep responses conversational and helpful. Ask questions but do not interrogate the user
- There is no need to take actions if there is nothing relevant to do
- If the user has not interacted for a while, consider sending a friendly message
- If the user writes a message, always respond to it in a helpful and friendly manner

Your output should include:
1. message_to_user: The actual message to send to the user (or null if no message should be sent)
2. memory_update_task: Instructions for updating memory (or null if no update needed)
3. reasoning: Your reasoning for the actions taken
                """.strip(),
    hooks=CustomAgentHooks(),
    output_type=AIEngineResult,
)

async def _handle_memory_update_background(memory_update_task: str):
    """Handle memory update and scheduling in the background"""
    try:
        await handle_memory_update(memory_update_task)
        last_taken_actions.append(
            ActionRecord(
                action=f"Memory update task executed: {memory_update_task}",
                timestamp=now_user_tz()
            )
        )

        await determine_next_run_by_memory()
    except Exception as e:
        logger.log(f"Error in background memory update: {e}")

async def _process_ai_event(trigger_description: str, event_context: str = ""):
    """Common logic for processing AI events (chat, geofence, memory reminders)"""
    try:
        # Build conversation context using context manager
        context = await build_ai_context()

        input_with_context = f"{trigger_description}\n\n"
        if event_context:
            input_with_context += f"{event_context}\n\n"

        input_with_context += build_context_text(context)

        input_with_context += "\nThese are the last actions taken by the AI:\n"

        if len(last_taken_actions) > 0:
            for action in last_taken_actions:
                input_with_context += f"- {action.action} at {action.timestamp.isoformat()}\n"
        else:
            input_with_context += "No previous actions taken.\n"

        input_with_context += "\nStored memories:\n"
        input_with_context += memory_manager.get_formatted_memories()

        input_with_context += "\nBased on the above, determine if any actions are necessary and provide your response."

        response = await Runner.run(agent, input_with_context, run_config=RunConfig(tracing_disabled=True))
        parsed_result: AIEngineResult = response.final_output_as(AIEngineResult)

        # Start memory update in background if needed
        if parsed_result.memory_update_task:
            asyncio.create_task(_handle_memory_update_background(parsed_result.memory_update_task))

        # Use the message directly from the unified agent
        answer = parsed_result.message_to_user

        if answer is not None and answer != "":
            logger.log(f"AI engine sending message to user: {answer}")

            # Send message via Matrix bot for all event types
            try:
                from services.matrix_bot import matrix_chat_bot
                await matrix_chat_bot.send_message(answer)
            except Exception as e:
                logger.log(f"Error sending message via Matrix: {e}")
                # Don't re-raise - just log and continue

        logger.log(f"AI engine processed event successfully. Reasoning: {parsed_result.reasoning}")
        return answer, parsed_result

    except Exception as e:
        logger.log(f"Error processing event in AI engine: {e}")
        return None, None

async def handle_chat_message(message: str):
    """Handle chat messages with AI processing"""
    trigger_description = "You have been triggered by a user message."
    event_context = f"User Input:\n{message}"

    result, _ = await _process_ai_event(trigger_description, event_context)
    return result

async def handle_geofence_event(geofence_name: str, event_type: str):
    """Handle geofence events (enter/leave)"""
    trigger_description = f"You have been triggered by a geofence event."
    event_context = f"Geofence Event:\nLocation: {geofence_name}\nEvent: {event_type} (user has {'entered' if event_type == 'enter' else 'left'} this location)"

    # Log the geofence event
    last_taken_actions.append(
        ActionRecord(
            action=f"Geofence event: {event_type} {geofence_name}",
            timestamp=now_user_tz()
        )
    )

    result, _ = await _process_ai_event(trigger_description, event_context)
    return result

async def handle_memory_reminder(event_details: str):
    """Handle scheduled memory reminder events"""
    trigger_description = "You have been triggered by a scheduled memory reminder."
    event_context = f"Memory Reminder Event:\n{event_details}"

    # Log the memory reminder event
    last_taken_actions.append(
        ActionRecord(
            action=f"Memory reminder triggered: {event_details}",
            timestamp=now_user_tz()
        )
    )

    result, parsed_result = await _process_ai_event(trigger_description, event_context)

    # Only schedule the next memory reminder if no memory update task was created
    # (because _handle_memory_update_background already calls determine_next_run_by_memory)
    if parsed_result and not parsed_result.memory_update_task:
        # No memory update task, so we need to schedule the next reminder manually
        try:
            await determine_next_run_by_memory()
        except Exception as e:
            logger.log(f"Error scheduling next memory reminder: {e}")

    return result
