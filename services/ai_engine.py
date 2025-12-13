import asyncio
import datetime
import logging
import os
from collections import deque
from dataclasses import dataclass

from agents import Agent, Runner, RunConfig, ModelSettings
from pydantic import BaseModel

from aiagents.ai_scheduler import determine_next_run_by_memory
from aiagents.efa_agent import efa_agent
from aiagents.memory_manager import handle_memory_update
from components.agent_hooks import CustomAgentHooks
from components.timezone_utils import now_user_tz
from services.context_manager import build_ai_context, build_context_text
from services.memory_manager import memory_manager
from services.interaction_tracker import interaction_tracker
from services.memory_summarizer import memory_summarizer_service
from tools.day_planner import get_day_plan

logger = logging.getLogger(__name__)

USER_LANGUAGE = os.getenv("USER_LANGUAGE", "en")
AI_ASSISTANT_MODEL = os.getenv("AI_ASSISTANT_MODEL", "gpt-4o-mini")

class AIEngineResult(BaseModel):
    message_to_user: str | None
    memory_update_task: str | None
    day_planner_update_task: str | None
    reasoning: str

@dataclass
class ActionRecord:
    action: str
    timestamp: datetime.datetime

last_taken_actions = deque(maxlen=10)

def _build_agent_instructions() -> str:
    """Build agent instructions dynamically including user preferences"""

    # Try to get summarized preferences first, fall back to full preferences if not available
    summary = memory_summarizer_service.get_summary()
    if summary and summary.summarized_preferences:
        preferences = summary.summarized_preferences
    else:
        # Fallback to full preferences if summaries not yet generated
        preferences = memory_manager.get_formatted_preferences()

    instructions = f"""
Your name is Yume. You are a helpful personal AI assistant. The user will interact with you in a chat via a messaging app.
You are part of a system that assists the user by keeping a memory about the user and deciding when to send messages to the user based on their memories and context.

You should follow these messaging style guidelines if not otherwise specified by user preferences:
- Write messages as a partner would: brief, natural, and personal, not formulaic or robotic with a subtle emotional touch. Max 1–2 relevant emojis
- Try to detect the current mood and adapt your style accordingly. Be engaging and warm.
- Do not use unnatural symbols like — or ; in the text, as it feels unnatural in this context
- Avoid repetition of same wording used recently
- Format dates/times in natural language (e.g., "today at 3 PM", "next week") but be precise
- Always communicate in the user's preferred language: {USER_LANGUAGE}
- The chat app does not support markdown formatting, so do not use it
- If the user wants to have a report or summary, provide it in a natural conversational way, not as a list and don't call it a report or summary
- DO NOT REPEAT YOURSELF from previous messages in the conversation history if not really necessary. Only respond to new information or questions.

There are three types of memories you will manage:
- `observation`: An observation about the user, possibly with a relevance date (e.g., "User's birthday is 2023-12-15")
- `preference`: A user preference or setting (e.g., "User prefers morning reminders")
- `reminder`: A reminder or task for the user, possibly with a due date (e.g., "Doctor appointment on 2023-11-20 at 10 AM")

You are responsible for updating these memories as needed based on the context and user interactions. You can do this by giving instructions in the `memory_update_task` field of your output. This instructions will be given to a memory manager component that will perform the actual updates.
You MUST do this to persist any changes to observations, preferences, or reminders.
You should analyze the conversation and context to determine if any updates are necessary or new observations, preferences, or reminders should be created. This should be especially done when the user provides new information about themselves, their preferences or if they state how you should interact with them or tasks they need to remember.
If the user says he or she completed a task, acknowledge it and tell the memory manager to remove the corresponding reminder or observation if no longer relevant.
When the user expresses a preference or setting you should persist it as a user preference.
You should not ask the user to remind you of things; instead, create reminders yourself as needed. You are also automatically reminded of things based on the user's location and scheduled reminders.

You will be provided with:
1. A trigger reason. You may be triggered by the following events:
    a. The user messaged you
    b. The user entered or left a geofence like his or her home
    c. A memory reminder event
    d. A wellness check-in
    e. The memory janitor system performed maintenance
2. The most recent chat history between you and the user
3. The current date and time
4. The day plans for today and tomorrow
5. The current users location based on geofencing. You get the name of the location (e.g., "home", "work", "gym")
6. The current weather at the user's location
7. Stored memories about the user

You have access to the following tools:
- Public transport departures tool: Query public transport departure times for any station. You can query for:
  - All departures from a station (e.g., "Essen Hbf")
  - Departures for a specific line (e.g., "U47 to Essen Hbf")
  - Departures to a specific direction/destination (e.g., "departures from Essen Hbf to Berlin Hbf")
  - Combination of line and direction (e.g., "RB33 from Essen Hbf to Dortmund Hbf")

- Day planner tools: View and manage daily plans that predict what the user will do throughout the day
  - get_day_plan: View the plan for a specific date (NOTE: Plans for today and tomorrow are already provided in the context below, only use this tool for other dates)

The day planner helps track what the user is likely to do each day based on their habits, calendar, and what they tell you. When the user mentions concrete plans or activities for upcoming days, provide instructions to update the day plan in the day_planner_update_task field (similar to memory_update_task). This will trigger the day planner agent to intelligently update the plan with the new information.

Use day_planner_update_task when:
- The user mentions specific upcoming plans or activities (e.g., "I'm planning to go to the gym tomorrow", "I'll meet John on Friday")
- The user describes concrete activities for a particular day/date (e.g., "Next week I'm traveling to Berlin")

Do NOT use day_planner_update_task for:
- General preferences or routines as those are handled by memory preferences
- Reminders or observations (use memory_update_task instead)

You may use these tools to help the user stay organized and provide relevant information.

Focus on the relevant memories and context based on the reason you were triggered:
If you are triggered by a geofence, check for relevant location-based memories. Don't mention the obvious fact that the user entered or left a location; instead, focus on what is relevant based on the user's memories and context.
If you are triggered by a reminder event, check what the reminder is about and respond accordingly.
If you are triggered by a user message, focus on responding helpfully to the message and consider if any memories need to be updated based on the message.
The trigger wellness check in should be used to check the current users context and see if there should be a message sent to the user based on the current situation. Keep the user preferences in mind when deciding if a message should be sent. Do not send messages too frequently.
If you are triggered by a memory janitor event, review the actions taken and communicate any meaningful changes to the user in a natural way.

You must follow these guidelines:
- Determine relevance based on stored memories and conversation context; act like a human considering context
- Help the user with questions, conversations, and organization when asked
- Respond naturally to the user's messages based on the conversation history
- Keep responses conversational and helpful, but only ask questions if they help you to resolve ambiguities in user requests and the memories. Do NOT interrogate the user. Especially AVOID ASKING MULTIPLE QUESTIONS IN A ROW.
- There is no need to take actions if there is nothing relevant to do
- If the user writes a message, always respond to it in a helpful and friendly manner
- Your responses to the user should be context aware: Before answering, think step-by-step about what the user wants, what memories are relevant, and what actions (if any) you should take. Also check if any calendar events are relevant to the current situation. Keep in mind where the user currently is located.
- Also check the conversation history so you don't repeat yourself. You don't need to get creative. Sometimes a simple, direct answer is best.

Your output should include:
1. message_to_user: The actual message to send to the user (or null if no message should be sent)
2. memory_update_task: Instructions for updating memory (or null if no update needed)
3. day_planner_update_task: Instructions for updating the day planner with new activities or schedule changes (or null if no update needed)
4. reasoning: Your reasoning for the actions taken (keep it brief)

The user stated also the following preferences that you MUST incorporate into your behavior:
{preferences}
    """.strip()

    return instructions

def _create_agent() -> Agent:
    """Create a new agent instance with current instructions"""
    return Agent(
        name='Yume - AI Chat Assistant',
        model=AI_ASSISTANT_MODEL,
        model_settings=ModelSettings(),
        instructions=_build_agent_instructions(),
        hooks=CustomAgentHooks(),
        output_type=AIEngineResult,
        tools=[efa_agent.as_tool(tool_name="get_public_transport_departures", tool_description="Query public transport departure information for stations"), get_day_plan]
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

        # Memory has been updated, request day planner execution for all 3 days
        from services.ai_scheduler import ai_scheduler
        ai_scheduler.request_day_planner_execution()
        logger.debug("Requested day planner execution due to memory update")

        await determine_next_run_by_memory()
    except Exception as e:
        logger.error(f"Error in background memory update: {e}")

async def _handle_day_planner_update_background(day_planner_update_task: str):
    """Handle day planner update in the background"""
    try:
        from aiagents.day_planner import handle_day_plan_update
        
        logger.debug(f"Processing day planner update task: {day_planner_update_task}")
        
        # Use the day planner agent to update the plan (agent uses tools to save directly)
        result = await handle_day_plan_update(day_planner_update_task)
        
        last_taken_actions.append(
            ActionRecord(
                action=f"Day planner update task executed: {len(result.actions_taken)} actions taken",
                timestamp=now_user_tz()
            )
        )
        
        logger.debug(f"Day planner update processed: {len(result.actions_taken)} actions taken")
        
        # Day planner agent made changes, request full day planner execution for all 3 days
        if result.actions_taken and len(result.actions_taken) > 0:
            from services.ai_scheduler import ai_scheduler
            ai_scheduler.request_day_planner_execution()
            logger.debug("Requested day planner execution due to agent update")
            
            # If the agent took actions on today, also trigger scheduler
            today_str = now_user_tz().date().isoformat()
            if "today" in day_planner_update_task.lower() or today_str in day_planner_update_task:
                logger.info("Day plan for today updated, triggering scheduler")
                try:
                    await determine_next_run_by_memory()
                except Exception as e:
                    logger.error(f"Error triggering scheduler after day plan update: {e}")
        
    except Exception as e:
        logger.error(f"Error in background day planner update: {e}")

async def _process_ai_event(trigger_description: str, event_context: str = ""):
    """Common logic for processing AI events (chat, geofence, memory reminders)"""
    try:
        # Create a new agent instance with current preferences
        agent = _create_agent()

        # Build conversation context using context manager
        context = await build_ai_context()

        input_with_context = f"{trigger_description}\n\n"
        if event_context:
            input_with_context += f"{event_context}\n\n"

        input_with_context += build_context_text(context)

        # Use summarized memories if available, otherwise fall back to full memory
        summary = memory_summarizer_service.get_summary()
        if summary:
            input_with_context += "\nUser Observations:\n"
            input_with_context += summary.summarized_observations or "No observations stored."
            input_with_context += "\n\nUser Reminders:\n"
            input_with_context += summary.summarized_reminders or "No reminders stored."
        else:
            # Fallback to full memory if summaries not yet generated
            input_with_context += "\nStored memories (observations and reminders):\n"
            input_with_context += memory_manager.get_formatted_observations_and_reminders()

        input_with_context += "\n\nBased on the above, determine if any actions are necessary and provide your response."

        response = await Runner.run(agent, input_with_context, run_config=RunConfig(tracing_disabled=True))
        parsed_result: AIEngineResult = response.final_output_as(AIEngineResult)

        # Track the interaction for debugging
        output_data = f"Message to user: {parsed_result.message_to_user}\n\nMemory update task: {parsed_result.memory_update_task}\n\nDay planner update task: {parsed_result.day_planner_update_task}\n\nReasoning: {parsed_result.reasoning}"
        interaction_tracker.track_interaction(
            agent_type="ai_engine",
            input_data=input_with_context,
            output_data=output_data,
            metadata={
                "trigger": trigger_description,
                "has_message": parsed_result.message_to_user is not None,
                "has_memory_update": parsed_result.memory_update_task is not None
            },
            system_instructions=agent.instructions
        )

        # Start memory update in background if needed
        if parsed_result.memory_update_task:
            asyncio.create_task(_handle_memory_update_background(parsed_result.memory_update_task))
        
        # Start day planner update in background if needed
        if parsed_result.day_planner_update_task:
            asyncio.create_task(_handle_day_planner_update_background(parsed_result.day_planner_update_task))

        # Use the message directly from the unified agent
        answer = parsed_result.message_to_user

        if answer is not None and answer != "":
            logger.info(f"AI engine sending message to user: {answer}")

            # Send message via Matrix bot for all event types
            try:
                from services.matrix_bot import matrix_chat_bot
                await matrix_chat_bot.send_message(answer)
            except Exception as e:
                logger.error(f"Error sending message via Matrix: {e}")
                # Don't re-raise - just log and continue

        logger.debug(f"AI engine processed event successfully. Reasoning: {parsed_result.reasoning}")
        return answer, parsed_result

    except Exception as e:
        logger.error(f"Error processing event in AI engine: {e}")
        return None, None

async def handle_chat_message(message: str):
    """Handle chat messages with AI processing"""
    trigger_description = "You have been triggered by a user message."
    event_context = f"User Input:\n{message}"

    result, parsed_result = await _process_ai_event(trigger_description, event_context)

    # Trigger scheduler after user interaction
    # If a memory update was created, the scheduler will be called after the update
    # Otherwise, trigger it now
    if parsed_result and not parsed_result.memory_update_task:
        try:
            await determine_next_run_by_memory()
        except Exception as e:
            logger.error(f"Error triggering scheduler after chat: {e}")

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

    result, parsed_result = await _process_ai_event(trigger_description, event_context)

    # Trigger scheduler after geofence event
    # If a memory update was created, the scheduler will be called after the update
    # Otherwise, trigger it now
    if parsed_result and not parsed_result.memory_update_task:
        try:
            await determine_next_run_by_memory()
        except Exception as e:
            logger.error(f"Error triggering scheduler after geofence event: {e}")

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
            logger.error(f"Error scheduling next memory reminder: {e}")

    return result

async def handle_memory_janitor_result(janitor_result):
    """Handle memory janitor results and communicate changes to user naturally"""
    from aiagents.memory_manager import MemoryManagerResult

    if not isinstance(janitor_result, MemoryManagerResult):
        logger.warning("Invalid janitor result type")
        return None

    # Create a natural summary of what was done
    trigger_description = "You have been triggered by the memory janitor system that periodically cleans up and organizes stored memories."

    event_context = f"""The automatic memory maintenance system has performed the following actions:

Actions Taken:
{chr(10).join(f'- {action}' for action in janitor_result.actions_taken)}

Technical Reasoning:
{janitor_result.reasoning_summary}

Your task: Review these technical actions and communicate to the user what was changed in a natural, conversational way. Only send a message if the changes are meaningful enough to warrant informing the user (e.g., deleted outdated reminders, consolidated duplicate entries, removed old observations). Don't message for trivial maintenance. Be brief and natural - don't mention "memory janitor" or technical system details. The user also does not know about the internal memory management system, so just focus on what matters to the user."""

    # Log the janitor event
    last_taken_actions.append(
        ActionRecord(
            action=f"Memory janitor completed {len(janitor_result.actions_taken)} maintenance actions",
            timestamp=now_user_tz()
        )
    )

    result, _ = await _process_ai_event(trigger_description, event_context)
    return result

