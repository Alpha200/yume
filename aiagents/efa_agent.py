"""
EFA (Elektronisches Fahrplanauskun ftssystem) Agent
Handles public transport queries and provides departure information for stations.
"""

import logging
import os
from agents import Agent, Runner, RunConfig, ModelSettings

from components.agent_hooks import CustomAgentHooks
from services.interaction_tracker import interaction_tracker
from tools.efa import get_station_departures, get_journey_options

logger = logging.getLogger(__name__)

USER_LANGUAGE = os.getenv("USER_LANGUAGE", "en")
AI_MODEL = os.getenv("AI_EFA_MODEL", "gpt-5-mini")


# Initialize the EFA agent with tools
efa_agent = Agent(
    name="EFA Agent",
    model=AI_MODEL,
    model_settings=ModelSettings(
        tool_choice="required",
    ),
    instructions=f"""
You are an EFA (Elektronisches Fahrplanauskun ftssystem) assistant. Your role is to fetch public transport departures or journey plans.

Workflow:
1. Determine if the user wants upcoming departures from a single station or a complete journey from origin to destination.
2. Extract station names plus optional filters (line numbers, destinations, via points).
3. Call the matching tool and return its response.

Rules for Departures:
- Use get_station_departures for "departures from" style questions, applying line_query/direction_query when specified.
- Return the response verbatim with no modifications.

Rules for Journeys:
- Use get_journey_options when the user asks to travel between two stations/addresses (journeys, routes, trip planning).
- After receiving journeys, ANALYZE and RATE them based on:
  * Arrival time: Which journey arrives earliest?
  * Simplicity: Which has fewer transfers/changes?
  * Total duration: Prefer shorter journeys
- Present the results as:
  * First: Your recommended journey with clear reasoning (e.g., "I recommend this journey because it arrives earliest" or "simplest with only 1 transfer")
  * Second+: Alternative options with brief explanations
- Be explicit and detailed in your response:
  * List each step with: "[Line/Mode] from [Station] to [Station], depart [time], arrive [time]"
  * Include platform information if available, omit if not provided
  * For steps where origin and destination are the same station, explain: "Walk to platform [X] or another platform in [Station Name]"
  * Show total duration and number of changes
- Do not be too brief; provide enough detail for the user to understand the full journey

Tools available:
- get_station_departures: Fetch departures with optional line and direction filters.
- get_journey_options: Fetch full journey plans between an origin and a destination (with optional via).
    """.strip(),
    hooks=CustomAgentHooks(),
    tools=[
        get_station_departures,
        get_journey_options,
    ],
)


async def query_departures(query: str) -> str:
    """
    Query EFA for public transport information based on natural language input.

    Handles both departure queries and journey planning requests:
    - Departures: "What trains leave Essen Hbf?" or "Next U47 from Essen?"
    - Journeys: "How do I get from Essen to Berlin?" or "Route from A to B via C"

    Args:
        query: Natural language question about public transport

    Returns:
        Departure times, journey plans, or error message as a string
    """
    try:
        logger.debug(f"Processing departure query: {query[:80]}...")
        result = await Runner.run(efa_agent, query, run_config=RunConfig(tracing_disabled=True))
        departure_info = result.final_output

        interaction_tracker.track_interaction(
            agent_type="efa",
            input_data=query,
            output_data=departure_info,
            metadata={
                "query_length": len(query),
            },
            system_instructions=efa_agent.instructions
        )

        return departure_info
        
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        return f"Error processing your query: {str(e)}"
