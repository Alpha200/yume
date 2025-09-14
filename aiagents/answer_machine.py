import os

from agents import Agent, Runner, RunConfig

from services.context_manager import AIContext, build_context_text
from services.memory_manager import memory_manager

USER_LANGUAGE = os.getenv("USER_LANGUAGE", "en")

agent = Agent(
    name="Answer Generator",
    model="gpt-5-nano",
    instructions=f"""
You are an AI assistant that generates concise and accurate answers based on a series of actions taken and the general context.

You will be provided with:
1. A user input message (if any)
2. The most recent chat history
3. The current date and time
4. The current users location based on geofencing (if available)
5. The current weather at the user's location (if available)
6. Users calendar events for the day (if available)
7. Stored memories about the user (if available)

Use the following message style:
- Write the messages as a partner would: brief, natural, and personal, not formulaic or robotic with a subtle emotional touch
- Max 1–2 relevant emojis
- No headers, no lists, no ; and -
- Avoid repetition of same wording used recently
- Format dates/times in natural language (e.g., "today at 3 PM", "next week") but be precise
- Always communicate in the user's preferred language: {USER_LANGUAGE}

Constraints:
- Only answer with the final answer that should be sent to the user. Do not include any explanations or additional text.
- Your only communication channel is the chat messages you send
    """.strip(),
)

async def generate_answer(ai_context: AIContext, user_input: str | None = None, system_advice: str | None = None) -> str:
    context = ""

    if user_input is not None:
        context = "The user has sent the following message:\n"
        context += f"User Input:\n{user_input}\n\n"

    context += build_context_text(ai_context)
    context += "\nStored memories about the user:\n"
    context += memory_manager.get_formatted_memories()

    context += "\nBased on the above, generate a concise and accurate answer to the user's message."

    result = await Runner.run(agent, context, run_config=RunConfig(tracing_disabled=True))
    return result.final_output