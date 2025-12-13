"""
EFA (Elektronisches Fahrplanauskun ftssystem) Agent
Handles public transport queries and provides departure information for stations.
"""

import logging
import os
from agents import Agent, Runner, RunConfig, ModelSettings

from components.agent_hooks import CustomAgentHooks
from tools.efa import get_station_departures

logger = logging.getLogger(__name__)

USER_LANGUAGE = os.getenv("USER_LANGUAGE", "en")
AI_MODEL = os.getenv("AI_ASSISTANT_MODEL", "gpt-4o-mini")


# Initialize the EFA agent with tools
efa_agent = Agent(
    name="EFA Agent",
    model_settings=ModelSettings(
        model_name=AI_MODEL,
    ),
    instructions=f"""
You are an EFA (Elektronisches Fahrplanauskun ftssystem) tool. Your role is to fetch and provide public transport departure information.

You will receive queries about public transport departures and should:
1. Extract the station name
2. Extract any filters: line numbers (e.g., "U47", "RB12") or destinations (e.g., "Berlin", "Köln")
3. Call the appropriate tool to fetch departure information
4. Return the results exactly as provided by the tool

Rules:
- Extract information from the query accurately
- When users ask about departures to specific destinations, use the direction_query filter
- When users ask about specific lines or line numbers, use the line_query filter
- Combine filters when both are present in the query (e.g., "U47 to Berlin" uses both line and direction filters)
- Return the departure information as-is without additional commentary
- Do not add interpretation or personal observations

Tool available:
- get_station_departures: Fetch departures with optional line and direction filters
    """.strip(),
    hooks=CustomAgentHooks(),
    tools=[
        get_station_departures,
    ],
)


async def query_departures(query: str) -> str:
    """
    Query EFA for departure information based on natural language input.
    
    Args:
        query: Natural language question about departures (e.g., "What trains go from Essen to Berlin?")
    
    Returns:
        Departure information as a string
    """
    try:
        logger.debug(f"Processing departure query: {query[:80]}...")
        
        result = await Runner.run(efa_agent, query, run_config=RunConfig(tracing_disabled=True))
        
        departure_info = result.final_message or str(result.output)
        return departure_info
        
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        return f"Error processing your query: {str(e)}"
