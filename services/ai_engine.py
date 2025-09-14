import datetime
from collections import deque
from dataclasses import dataclass

from agents import Agent, Runner, RunConfig, ModelSettings
from pydantic import BaseModel

from aiagents.answer_machine import generate_answer
from aiagents.memory_manager import handle_memory_update
from components.agent_hooks import CustomAgentHooks
from components.logging_manager import logging_manager
from services.context_manager import build_ai_context, build_context_text

logger = logging_manager

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
    name='Matrix Chat Bot',
    model="gpt-4o-mini",
    model_settings=ModelSettings(
    ),
    instructions=f"""
Your name is Yume. You are a helpful AI assistant in a chat room.

You are part of a system that assists the user by keeping a memory about the user and deciding when to send messages to the user based on their memories and context.

You will be provided with:
1. A user input message (if triggered by a user message)
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

You should plan actions to be taken that are being forwarded to a subsystem. Possible actions include:
- Sending a message to the user in the chat (tell the subsystem what to say)
- Incorporate new or updated information into the memory (tell the memory subsystem what to do)

Provide a reasoning summary of why you want to take the actions.

You must follow these guidelines:
- Determine relevance based on stored memories and conversation context; act like a human considering context
- Help the user with questions, conversations, and organization when asked
- Respond naturally to the user's messages based on the conversation history
- Keep responses conversational and helpful. Ask questions but do not interrogate the user
- There is no need to take actions if there is nothing relevant to do
- If the user has not interacted for a while, consider sending a friendly check-in message
- If the user wrotes a message, always respond to it in a helpful and friendly manner
                """.strip(),
    hooks=CustomAgentHooks(),
    output_type=AIEngineResult,
)

async def handle_chat_message(message: str):
    """Handle chat messages with AI processing"""
    try:
        # Build conversation context using context manager

        context = await build_ai_context()

        input_with_context = "You have been triggered by a user message.\n\n"
        input_with_context += f"User Input:\n{message}\n\n"
        input_with_context += build_context_text(context)

        input_with_context += "\nThese are the last actions taken by the AI:\n"

        if len(last_taken_actions) > 0:
            for action in last_taken_actions:
                input_with_context += f"- {action.action} at {action.timestamp.isoformat()}\n"
        else:
            input_with_context += "No previous actions taken.\n"

        input_with_context += "\nBased on the above, determine if any actions are necessary."

        response = await Runner.run(agent, input_with_context, run_config=RunConfig(tracing_disabled=True))
        parsed_result: AIEngineResult = response.final_output_as(AIEngineResult)

        if parsed_result.memory_update_task:
            await handle_memory_update(parsed_result.memory_update_task)
            last_taken_actions.append(
                ActionRecord(
                    action=f"Memory update task executed: {parsed_result.memory_update_task}",
                    timestamp=datetime.datetime.now()
                )
            )

        answer = None

        if parsed_result.message_to_user is not None and parsed_result.message_to_user != "":
            logger.log(f"AI engine decided to send a message to the user based on {parsed_result.message_to_user}")
            answer = await generate_answer(context, parsed_result.message_to_user)
            last_taken_actions.append(
                ActionRecord(
                    action=f"Sent message to user: {answer}",
                    timestamp=datetime.datetime.now()
                )
            )

        logger.log("AI engine processed message successfully. Reasoning: " + parsed_result.reasoning)
        return answer

    except Exception as e:
        logger.log(f"Error processing message in AI engine: {e}")
        return None


def handle_geofence_event(event):
    # Placeholder for handling geofence events
    return f"Geofence event handled: {event}"

def handle_memory_reminder(event):
    # Placeholder for handling other types of events
    return f"Other event handled: {event}"